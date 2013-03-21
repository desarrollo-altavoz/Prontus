#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

package Update;
use strict;
use Carp qw(cluck carp);
use warnings;
no warnings 'uninitialized';

use DBI;

use glib_fildir_02;
use File::Copy;
use lib_prontus;
use prontus_varglb;
use glib_hrfec_02;
use Digest::MD5 qw(md5_hex);
use File::Compare;
use lib_prontus;
# use diagnostics;


# ---------------------------------------------------------------
# Errores orientados a que los pueda leer el usuario, sin info del ambiente.
# el texto completo del error se tira al STDERR
our $ERR;

# ---------------------------------------------------------------
sub new {
# Crea el objeto y retorna una referencia a el.
# Este metodo es el primer paso obligado

    my $clase = shift;
    my $upd_obj = {@_};
    bless $upd_obj, $clase;

    # Atributos recibidos.
    $upd_obj->{document_root}      ||= $ENV{'DOCUMENT_ROOT'}; # valor por omision
    $upd_obj->{prontus_id}         ||= '';
    $upd_obj->{version_prontus} ||= '';
    $upd_obj->{actualizaciones} ||= 'SI';
    $upd_obj->{path_conf} ||= ''; # se asume q lo valida la CGI que utiliza esta lib.
    $upd_obj->{just_status} ||='0';

    if ( ($upd_obj->{prontus_id} !~ /^[\w\d]+$/) || ($upd_obj->{version_prontus} eq '') || ($upd_obj->{path_conf} eq '') ) {
        $Update::ERR = "Update::new con params no validos:\n"
                    . "prontus_id[$upd_obj->{prontus_id}] \n"
                    . "path_conf[$upd_obj->{path_conf}] \n"
                    . "version_prontus[$upd_obj->{version_prontus}] \n";
        return 0;
    };

    $upd_obj->{update_server} = 'http://www.prontus.cl';

    # Establece y chequea dirs
    $upd_obj->{dir_updates} = $upd_obj->{document_root} . "/_prontus_update";

    if(! &glib_fildir_02::check_dir($upd_obj->{dir_updates}) ) {
        $Update::ERR = "No se pueden crear directorios de update";
        cluck $Update::ERR . "[$!]\n";
        return 0;
    }

    # Determina y disponibiliza version del update disponible, en caso de haberlo.
    $upd_obj->{rama_instalada} = '';
    $upd_obj->{nro_revision_instalada} = '';
    $upd_obj->{nom_file_vdescriptor} = '';
    $upd_obj->_set_info_release_instalada();

    use FindBin '$Bin';
    $upd_obj->{nom_cgicpn_current} = ''; # por ej 'cgi-cpn'
    $upd_obj->{nom_cgicpn_current} = &lib_prontus::remove_front_string($Bin, $upd_obj->{document_root} . '/');
    # $upd_obj->{nom_cgicpn_current} = 'cgi-cpn-test'; # DEBUG

    $upd_obj->{nom_cgibin_current} = $prontus_varglb::DIR_CGI_PUBLIC;
    # $upd_obj->{nom_cgibin_current} = 'cgi-bin-test'; # DEBUG

    $upd_obj->{buffer_last} = &glib_fildir_02::read_file($upd_obj->{dir_updates} . '/' . $upd_obj->{nom_file_vdescriptor}); # last.11.0.txt
    $upd_obj->{last_version_disponible} = $upd_obj->update_disponible();

    $upd_obj->{ts_actualizacion} = &glib_hrfec_02::get_dtime_pack4();

    $upd_obj->{core_dirs} = $upd_obj->get_core_dirs();
    if ($upd_obj->{core_dirs} eq '') {
        $Update::ERR = "No se detectaron instancias Prontus para actualizar core.\nEl proceso de actualización no realizó cambios.";
        return 0;
    };

    if ($upd_obj->{just_status} ne '1') {
        $upd_obj->{dir_backup} = $upd_obj->get_dir_backup();
        if($upd_obj->{dir_backup} eq '') {
            $Update::ERR = "No se pueden crear directorios de respaldo";
            cluck $Update::ERR . "[$!]\n";
            return 0;
        }

        $upd_obj->{dir_descarga} = $upd_obj->get_dir_descarga();
        if($upd_obj->{dir_descarga} eq '') {
            $Update::ERR = "No se pueden crear directorios de descarga";
            cluck $Update::ERR . "[$!]\n";
            return 0;
        }
    }

    return $upd_obj;
};


# ---------------------------------------------------------------
sub garbage_dirs {

    # Borrar dirs descargados del download actual, pero deja el .tgz y el .md5, por si las moscas.
    my ($this) = shift;
    &glib_fildir_02::borra_dir("$this->{dir_descarga}/cgi-cpn");
    &glib_fildir_02::borra_dir("$this->{dir_descarga}/cgi-bin");
    &glib_fildir_02::borra_dir("$this->{dir_descarga}/wizard_prontus");

    # Garbage de backups, deja solo los 3 respaldos mas recientes.
    $this->garbage_dirs_leave3($this->{dir_updates} . '/updated');

    # Garbage de downloads, deja solo los 3 downloads mas recientes.
    $this->garbage_dirs_leave3($this->{dir_updates} . '/downloads');

};
# ---------------------------------------------------------------
sub get_dir_backup {

    my ($this) = shift;
    my $dir_dst_bak = $this->{dir_updates}
                    . '/updated/'
                    . $this->{rama_instalada}
                    . '.' . $this->{nro_revision_instalada}
                    . $this->{beta_revision_instalada}
                    . '-' . $this->{ts_actualizacion};
    if(! -d $dir_dst_bak) {
        return '' if (! &glib_fildir_02::check_dir($dir_dst_bak));
    }
    return $dir_dst_bak;
}
# ---------------------------------------------------------------
sub get_dir_descarga {

    my ($this) = shift;
    my $dir_descarga = $this->{dir_updates}
                    . '/downloads/'
                    . $this->{last_version_disponible};
    if(! -d $dir_descarga) {
        return '' if (! &glib_fildir_02::check_dir($dir_descarga));
    }
    return $dir_descarga;
}
# ---------------------------------------------------------------
# Este método realiza todas las validaciones necesarias, antes
# de comenzar el proceso de update
sub check_before_update {

    my ($this) = shift;

    # Ver si estan las carpetas a respaldar (aunque se supone que estan!)
    if (! -d "$this->{document_root}/$this->{nom_cgicpn_current}") {
        $Update::ERR = "Error al respaldar version actual de las CGIs back-end de Prontus: el directorio de origen no existe o no es valido.";
        cluck $Update::ERR . " - dir cgis backend origen[$this->{document_root}/$this->{nom_cgicpn_current}]\n";
        return 0;
    };
    if (! -d "$this->{document_root}/$this->{nom_cgibin_current}") {
        $Update::ERR = "Error al respaldar version actual de las CGIs front-end de Prontus: el directorio de origen no existe o no es valido.";
        cluck $Update::ERR . " - dir cgis frontend origen[$this->{document_root}/$this->{nom_cgibin_current}]\n";
        return 0;
    };

    # Se revisa si se puede escribir en el directorio de las CGIs
    my $random = &glib_str_02::random_string(10);
    while(-f "$this->{document_root}/$this->{nom_cgicpn_current}/$random.txt") {
        $random = &glib_str_02::random_string(10);
    }
    &glib_fildir_02::write_file("$this->{document_root}/$this->{nom_cgicpn_current}/$random.txt", $random);
    if(! unlink("$this->{document_root}/$this->{nom_cgicpn_current}/$random.txt")) {
        $Update::ERR = "No se pudo escribir en el directorio: /$this->{nom_cgicpn_current}";
        cluck $Update::ERR . " - dir cgis frontend origen[$this->{document_root}/$this->{nom_cgicpn_current}]\n";
        return 0;
    }

    $random = &glib_str_02::random_string(10);
    while(-f "$this->{document_root}/$this->{nom_cgibin_current}/$random.txt") {
        $random = &glib_str_02::random_string(10);
    }
    &glib_fildir_02::write_file("$this->{document_root}/$this->{nom_cgibin_current}/$random.txt", $random);
    if(! unlink("$this->{document_root}/$this->{nom_cgibin_current}/$random.txt")) {
        $Update::ERR = "No se pudo escribir en el directorio: /$this->{nom_cgibin_current}";
        cluck $Update::ERR . " - dir cgis frontend origen[$this->{document_root}/$this->{nom_cgibin_current}]\n";
        return 0;
    }

    # Revisa si se pueden asignar permisos ejecucion a las cgis, recursivamente.
    my $permResult = $this->setExecPermisos("$this->{document_root}/$this->{nom_cgicpn_current}", 755);
    if ($permResult ne '') {
        $Update::ERR = "Error al cambiar permisos de las CGIs back-end de Prontus: no se pudo asignar permisos de ejecucion a las CGIs: [$permResult]";
        cluck $Update::ERR . " - dir de cgis backend[$this->{document_root}/$this->{nom_cgicpn_current}]\n";
        return 0;
    };
    $permResult = $this->setExecPermisos("$this->{document_root}/$this->{nom_cgibin_current}", 755);
    if ($permResult ne '') {
        $Update::ERR = "Error al cambiar permisos de las CGIs front-end de Prontus: no se pudo asignar permisos de ejecucion a las CGIs: [$permResult]";
        cluck $Update::ERR . " - dir de cgis frontend[$this->{document_root}/$this->{nom_cgibin_current}]\n";
        return 0;
    };

    return 1;
};

# ---------------------------------------------------------------
sub _set_info_release_instalada {
    my ($this) = shift;
    my $rama_instalada;
    if ($this->{version_prontus} =~ /([0-9]+\.[0-9]+)\.([0-9]+)(\.beta)?/) {
        $this->{rama_instalada} = $1;
        $this->{nro_revision_instalada} = $2;
        $this->{beta_revision_instalada} = $3;
        $this->{nom_file_vdescriptor} = 'last.' . $this->{rama_instalada} . '.txt';
    } else {
        cluck 'No se pudo determinar version base instalada, no es posible verificar actualizaciones disponibles.';
    };
};

# ---------------------------------------------------------------
sub update_disponible {
    # Determina y retorna version del update disponible, en caso de haberlo.
    # Lee el archivo ya descargado.
    my ($this) = shift;

    my $last_version_disponible;

    if ($this->{rama_instalada} ne '')  {

        my $buffer_last_v = $this->{buffer_last};
        my $rama_instalada = $this->{rama_instalada};
        if ($buffer_last_v =~ /$rama_instalada\.([0-9]+)(\.beta)?/) {
            my $nro_revision_last = $1;
            my $beta = $2;
            $last_version_disponible = $rama_instalada . '.' . $nro_revision_last . $beta;
            if ($nro_revision_last > $this->{nro_revision_instalada}) {
                return $last_version_disponible;
            };
        };
    };
    return '';
};
# ---------------------------------------------------------------
sub get_status_update {
    my ($this) = shift;
    my $status_upd;
    if ($this->{actualizaciones} eq 'SI') {
        if($this->{buffer_last}) {
            # Existe una actualizacion, ahora se compara para ver si es mas actual
            if($this->{last_version_disponible}) {
                $status_upd = $this->{last_version_disponible};
            } else {
                $status_upd = "no_updates";
            }
        } else {
            $status_upd = "notfound";
        };
    } else {
        $status_upd = "disabled";
    };
#    $status_upd = "11.2.6";
#    $status_upd = "no_updatesf";
    warn "status_upd[$status_upd]";
    return $status_upd;
};

# ---------------------------------------------------------------
sub descarga_upd_descriptor {
    my ($this) = shift;

    # http://www.prontus.cl/release/prontus.11.0/last.11.0.txt
    unlink $this->{dir_updates} . '/' . $this->{nom_file_vdescriptor};

    my $url = $this->{update_server} . '/release/prontus.' . $this->{rama_instalada} . '/last.' . $this->{rama_instalada} . '.txt';
    my ($last_version_available, $msg_err) = &lib_prontus::get_url($url, 10); # contiene: 11.0.2.beta - 27/10/2010

    my $download_ok = 1;

    if ($msg_err) {
        if ($msg_err =~ /^404 /) {
            warn "No hay actualizacion disponible, 404 - no se encuentra el archivo[$url]";
            $download_ok = 0;
        } else {
            my $err = "No se pudo descargar información de nuevas versiones disponibles: $msg_err";
            warn("$err - url[$url] - " . $msg_err . "\n");
            $download_ok = 0;
        };
    } else {
        if ($last_version_available !~ /[0-9]+\.[0-9]+\.[0-9]+(\.beta)?/) {
            warn "No hay actualizacion disponible, el archivo [$url] existe pero no contiene info valida, last_version_available[$last_version_available]";
            $download_ok = 0;
        };
    };

    if ($download_ok) {
        &glib_fildir_02::write_file($this->{dir_updates} . '/' . $this->{nom_file_vdescriptor}, $last_version_available);
    };

};

# ---------------------------------------------------------------
sub descarga_release {
# Descarga tgz, md5 y descomprime:
# http://www.prontus.cl/release/prontus.x.y/files.x.y.z.tgz ->     /_prontus_update/downloads/x.y.z/files.x.y.z.tgz
#                                          /files.x.y.z.tgz.md5 ->                                 /files.x.y.z.tgz.md5
    my ($this) = shift;

    # Descarga tgz
    # http://www.prontus.cl/release/prontus.11.0/files.11.0.13.tgz
    my $url = $this->{update_server} . '/release/prontus.' . $this->{rama_instalada} . '/files.' . $this->{last_version_disponible} . '.tgz';
    my ($tgz_content, $msg_err) = &lib_prontus::get_url($url, 30);

    if ($msg_err) {
        if ($msg_err =~ /^404 /) {
            $Update::ERR = "Error al descargar release .tgz, 404 - no se encuentra el archivo[$url]";
            cluck $Update::ERR . "\n";
        } else {
            $Update::ERR = "Error al descargar release .tgz [$url]: $msg_err";
            cluck $Update::ERR . "\n";
        };
        return 0;
    } else {

        # Si ok el tgz, descarga md5
        # http://www.prontus.cl/release/prontus.11.0/files.11.0.13.tgz.md5
        my $url_md5 = $url . ".md5";
        my ($md5_remoto, $msg_err_md5) = &lib_prontus::get_url($url_md5, 10);
        if ($msg_err_md5) {
            if ($msg_err_md5 =~ /^404 /) {
                $Update::ERR = "Error al descargar release md5, 404 - no se encuentra el archivo[$url_md5]";
                cluck $Update::ERR . "\n";
            } else {
                $Update::ERR = "Error al descargar release md5 [$url_md5]: $msg_err_md5";
                cluck $Update::ERR . "\n";
            };
            return 0;
        } else {
            if ($md5_remoto =~ /([a-z0-9]{32})/) {
                $md5_remoto = $1;
            } else {
                $Update::ERR = "Error al descargar release md5 [$url_md5]: No contiene un string md5 valido, contiene[$md5_remoto]";
                cluck $Update::ERR . "\n";
                return 0;
            };

            # Si descargo ok el md5, verificar el tgz con este
            my $md5_local = md5_hex($tgz_content);
            if ($md5_local ne $md5_remoto) {
                $Update::ERR = "Error al descargar release [$url]: md5 no coincide\nlocal [$md5_local]\nremoto[$md5_remoto]\nEl archivo no se pudo descargar correctamente.";
                cluck $Update::ERR . "\n";
                return 0;
            } else {
                # Si verificacion ok, guardar tgz y descomprimir en ubicacion de destino, por ej:
                # /_prontus_update/downloads/11.0.13/files.11.0.13.tgz
                return 0 if (! &glib_fildir_02::check_dir($this->{dir_descarga}));
                my $path_local_tgz = $this->{dir_descarga} . '/files.' . $this->{last_version_disponible} . '.tgz';
                &glib_fildir_02::write_file($path_local_tgz, $tgz_content);
                if ((-s $path_local_tgz) && (-f $path_local_tgz)) {
                    # guardar el .md5 tb, por siaca
                    &glib_fildir_02::write_file("$path_local_tgz.md5", $md5_remoto);
                    # descomprimir en el mismo dir, el .tgz
                    system("tar xzf $path_local_tgz -C $this->{dir_descarga}");
                    if ($? != 0) {
                        $Update::ERR = "Error al descomprimir release .tgz[$path_local_tgz] en dir[$this->{dir_descarga}]: Error[$!]";
                        cluck $Update::ERR . "\n";
                        return 0;
                    };

                    # Eliminar cgi-cpn/dir_cgi.pm  y cgi-bin/dir_cgi.pmde la release a instalar, NO SE DEBE PISAR!
                    unlink "$this->{dir_descarga}/cgi-cpn/dir_cgi.pm";
                    unlink "$this->{dir_descarga}/cgi-bin/dir_cgi.pm";
                    unlink "$this->{dir_descarga}/cgi-bin/posting_limit.cfg";

                } else {
                    $Update::ERR = "Error al descargar release .tgz [$url]: $msg_err";
                    cluck $Update::ERR . "\n";
                    return 0;
                };
            };
        };
    };

    # Finalmente se chequea que realmente vengan los cgi-cgi y cgi-bin
    my $dir_src_cgicpn = "$this->{dir_descarga}/cgi-cpn";
    if (! -d $dir_src_cgicpn) {
        $Update::ERR = "En la release a instalar no se encontro directorio cgi-cpn";
        cluck $Update::ERR . " - dir_src_cgicpn[$dir_src_cgicpn]\n";
        return 0;
    };
    my $dir_src_cgibin = "$this->{dir_descarga}/cgi-bin";
    if (! -d $dir_src_cgibin) {
        $Update::ERR = "En la release a instalar no se encontro directorio cgi-bin";
        cluck $Update::ERR . " - dir_src_cgicpn[$dir_src_cgibin]\n";
        return 0;
    };

    # Se chequea que venga el prontus_dir y el core del wizard
    my $dir_src_core = "$this->{dir_descarga}/wizard_prontus/prontus_dir/cpan/core";
    if (! -d $dir_src_core) {
        $Update::ERR = "En la release a instalar no se encontro directorio core";
        cluck $Update::ERR . " - dir_src[$dir_src_core]\n";
        return 0;
    };
    my $dir_src_core_wiz = "$this->{dir_descarga}/wizard_prontus/core";
    if (! -d $dir_src_core_wiz) {
        $Update::ERR = "En la release a instalar no se encontro directorio core";
        cluck $Update::ERR . " - dir_src[$dir_src_core_wiz]\n";
        return 0;
    };
    return 1;
};

# ---------------------------------------------------------------
sub garbage_dirs_leave3 {
# Deja solo los ultimos 3 respaldos generados por el update

    my ($this) = shift;
    my ($dir) = shift;

    return unless(-d $dir);
    my @entries = &glib_fildir_02::lee_dir($dir);

    @entries = grep !/^\./, @entries; # Elimina directorios . y ..

    # Ordena por fecha dejando primero los mas nuevos
    @entries = sort { (stat("$dir/$b"))[9] <=> (stat("$dir/$a"))[9] } @entries;

    # Elimina del 3r dir en adelante
    my $numdir = 0;
    foreach my $entry (@entries) {
        next if (!-d "$dir/$entry");
        $numdir++;
        # print STDERR "garbage: revisando [$dir/$entry]\n";
        if ($numdir > 3) {
            print STDERR "\tgarbage: borrando [$dir/$entry]\n";
            &glib_fildir_02::borra_dir("$dir/$entry");
        };

    };

};

# ---------------------------------------------------------------
sub crea_respaldos {

    my ($this) = shift;

    # Copiar /cgi-cpn --> a dir de respaldo
    &glib_fildir_02::copy_tree($this->{document_root}, $this->{nom_cgicpn_current},
                               $this->{dir_backup}, $this->{nom_cgicpn_current});

    # Copiar /cgi-bin --> a dir de respaldo
    &glib_fildir_02::copy_tree($this->{document_root}, $this->{nom_cgibin_current},
                               $this->{dir_backup}, $this->{nom_cgibin_current});

    # Chequear integridad de respaldo - cgi-cpn.
    if (! -d "$this->{dir_backup}/$this->{nom_cgicpn_current}") {
        $Update::ERR = "Error al respaldar version actual de las CGIs back-end de Prontus: no se creo el directorio destino.";
        cluck $Update::ERR . " - dir bak de cgis backend[$this->{dir_backup}/$this->{nom_cgicpn_current}]\n";
        return 0;
    };
    my $cmpResult = $this->compareDirs("$this->{dir_backup}/$this->{nom_cgicpn_current}", "$this->{document_root}/$this->{nom_cgicpn_current}");
    if ($cmpResult ne '') {
        $Update::ERR = "Error al respaldar version actual de las CGIs back-end de Prontus: el dir. origen y el de destino del backup presentan diferencias en sus archivos:\n$cmpResult";
        cluck $Update::ERR . " - dir bak de cgis backend[$this->{dir_backup}/$this->{nom_cgicpn_current}]\n";
        return 0;
    };

    # Chequear integridad de respaldo - cgi-bin.
    if (! -d "$this->{dir_backup}/$this->{nom_cgibin_current}") {
        $Update::ERR = "Error al respaldar version actual de las CGIs front-end de Prontus: no se creo el directorio destino.";
        cluck $Update::ERR . " - dir bak de cgis frontend[$this->{dir_backup}/$this->{nom_cgibin_current}]\n";
        return 0;
    };
    $cmpResult = $this->compareDirs("$this->{dir_backup}/$this->{nom_cgibin_current}", "$this->{document_root}/$this->{nom_cgibin_current}");
    if ($cmpResult ne '') {
        $Update::ERR = "Error al respaldar version actual de las CGIs front-end de Prontus: el dir. origen y el de destino del backup presentan diferencias en sus archivos:\n$cmpResult";
        cluck $Update::ERR . " - dir bak de cgis frontend[$this->{dir_backup}/$this->{nom_cgibin_current}]\n";
        return 0;
    };


    # Se respaldan los cores de los prontus
    my $core_dirs = $this->{core_dirs};
    my @prontus_dirs = split(/;/, $core_dirs);
    foreach my $prontus_dir (@prontus_dirs) {
        next if (!-d "$this->{document_root}/$prontus_dir");
        # respaldar core antes de pisarlo.
        &glib_fildir_02::check_dir("$this->{dir_backup}/$prontus_dir/cpan");
        &glib_fildir_02::copy_tree("$this->{document_root}/$prontus_dir/cpan", 'core',
                                   "$this->{dir_backup}/$prontus_dir/cpan", 'core');

        # Chequear integridad de respaldo de core.
        if (! -d "$this->{dir_backup}/$prontus_dir/cpan/core") {
            $Update::ERR = "Error al respaldar core de instancia Prontus [$prontus_dir/cpan/core]: no se creo el directorio destino.";
            cluck $Update::ERR . " - dir destino[$this->{dir_backup}/$prontus_dir/cpan/core]\n";
            return 0;
        };
        $cmpResult = $this->compareDirs("$this->{dir_backup}/$prontus_dir/cpan/core", "$this->{document_root}/$prontus_dir/cpan/core");
        if ($cmpResult ne '') {
            $Update::ERR = "Error al respaldar version actual de core de instancia Prontus [$prontus_dir/cpan/core]: el dir. origen y el de destino del backup presentan diferencias en sus archivos:\n$cmpResult";
            cluck $Update::ERR . " - dir destino[$this->{dir_backup}/$prontus_dir/cpan/core]\n";
            return 0;
        };
    };

    # Se respalda el wizard si es que existe
    if(-d "$this->{document_root}/wizard_prontus") {
        # Se respalda el core del prontus_dir
        &glib_fildir_02::check_dir("$this->{dir_backup}/wizard_prontus/prontus_dir/cpan");
        &glib_fildir_02::copy_tree("$this->{document_root}/wizard_prontus/prontus_dir/cpan", 'core',
                                   "$this->{dir_backup}/wizard_prontus/prontus_dir/cpan", 'core');
        $cmpResult = $this->compareDirs("$this->{document_root}/wizard_prontus/prontus_dir/cpan/core", "$this->{dir_backup}/wizard_prontus/prontus_dir/cpan/core");
        if ($cmpResult ne '') {
            $Update::ERR = "Error al respaldar el core Prontus dir del Wizard: el dir. origen (actual wizard) y el de destino presentan diferencias en sus archivos:\n$cmpResult";
            cluck $Update::ERR . " - dir de core target[$this->{document_root}/wizard_prontus/prontus_dir/cpan/core]\n";
            return 0;
        };

        # Se respalda el core del wizard
        &glib_fildir_02::copy_tree("$this->{document_root}/wizard_prontus", 'core',
                                   "$this->{dir_backup}/wizard_prontus", 'core');
        $cmpResult = $this->compareDirs("$this->{document_root}/wizard_prontus/core", "$this->{dir_backup}/wizard_prontus/core");
        if ($cmpResult ne '') {
            $Update::ERR = "Error al actualizar Core del Wizard: el dir. origen (nueva release) y el de destino presentan diferencias en sus archivos:\n$cmpResult";
            cluck $Update::ERR . " - dir target[$this->{document_root}/wizard_prontus/core]\n";
            return 0;
        };
    }

    # Si todo sale bien, se responde
    return 1;
}

# ---------------------------------------------------------------
sub install_cgis {
# Descarga tgz, md5 y descomprime:
# http://www.prontus.cl/release/prontus.x.y/files.x.y.z.tgz ->     /_prontus_update/downloads/x.y.z/files.x.y.z.tgz
#                                          /files.x.y.z.tgz.md5 ->                                 /files.x.y.z.tgz.md5
    my ($this) = shift;

    # Copiar /cgi-cpn de la nueva release --> a dir oficial
    &glib_fildir_02::copy_tree($this->{dir_descarga}, 'cgi-cpn',
                               $this->{document_root}, $this->{nom_cgicpn_current});

    # Copiar /cgi-bin de la nueva release --> a dir oficial
    &glib_fildir_02::copy_tree($this->{dir_descarga}, 'cgi-bin',
                               $this->{document_root}, $this->{nom_cgibin_current});

    # Chequear integridad de cgi-cpn current.
    my $cmpResult = $this->compareDirs("$this->{document_root}/$this->{nom_cgicpn_current}", "$this->{dir_descarga}/cgi-cpn");
    if ($cmpResult ne '') {
        $Update::ERR = "Error al instalar CGIs back-end de Prontus: el dir. origen (nueva release) y el de destino presentan diferencias en sus archivos:\n$cmpResult";
        cluck $Update::ERR . " - dir de cgis backend[$this->{document_root}/$this->{nom_cgicpn_current}]\n";
        # $this->rollback_update();
        return 0;
    };

    # Chequear integridad de  cgi-bin current.
    $cmpResult = $this->compareDirs("$this->{document_root}/$this->{nom_cgibin_current}", "$this->{dir_descarga}/cgi-bin");
    if ($cmpResult ne '') {
        $Update::ERR = "Error al instalar CGIs front-end de Prontus: el dir. origen (nueva release) y el de destino presentan diferencias en sus archivos:\n$cmpResult";
        cluck $Update::ERR . " - dir de cgis frontend[$this->{document_root}/$this->{nom_cgibin_current}]\n";
        # $this->rollback_update();
        return 0;
    };

    # Asignar permisos ejecucion a las cgis, recursivamente.
    my $permResult = $this->setExecPermisos("$this->{document_root}/$this->{nom_cgicpn_current}", 755);
    if ($permResult ne '') {
        $Update::ERR = "Error al instalar CGIs back-end de Prontus: no se pudo asignar permisos de ejecucion a las CGIs: [$permResult]";
        cluck $Update::ERR . " - dir de cgis backend[$this->{document_root}/$this->{nom_cgicpn_current}]\n";
        # $this->rollback_update();
        return 0;
    };
    $permResult = $this->setExecPermisos("$this->{document_root}/$this->{nom_cgibin_current}", 755);
    if ($permResult ne '') {
        $Update::ERR = "Error al instalar CGIs front-end de Prontus: no se pudo asignar permisos de ejecucion a las CGIs: [$permResult]";
        cluck $Update::ERR . " - dir de cgis frontend[$this->{document_root}/$this->{nom_cgibin_current}]\n";
        # $this->rollback_update();
        return 0;
    };

    return 1;

};

# ---------------------------------------------------------------
sub install_core {

    my ($this) = shift;

    my $core_dirs = $this->{core_dirs};
    my $doc_root = $this->{document_root};

    # Prontus dirs a actualizar el core
    my @prontus_dirs = split(/;/, $core_dirs);
    foreach my $prontus_dir (@prontus_dirs) {
        next if (!-d "$doc_root/$prontus_dir");

        # Copiar core de la nueva release a dir destino
        &glib_fildir_02::copy_tree("$this->{dir_descarga}/wizard_prontus/prontus_dir/cpan", 'core',
                                   "$this->{document_root}/$prontus_dir/cpan", 'core');

        # Chequear integridad de lo copiado
        my $cmpResult = $this->compareDirs("$this->{document_root}/$prontus_dir/cpan/core", "$this->{dir_descarga}/wizard_prontus/prontus_dir/cpan/core");
        if ($cmpResult ne '') {
            $Update::ERR = "Error al instalar nuevo core de Prontus: el dir. origen (nueva release) y el de destino presentan diferencias en sus archivos:\n$cmpResult";
            cluck $Update::ERR . " - dir de core target[$this->{document_root}/$prontus_dir/cpan/core]\n";
            return 0;
        };
    };

    # Actualizar el prontus core del wizard, en caso de que se encuentre instalado
    if (-d "$this->{document_root}/wizard_prontus/prontus_dir/cpan/core") {
        # Copiar core
        &glib_fildir_02::copy_tree("$this->{dir_descarga}/wizard_prontus/prontus_dir/cpan", 'core',
                                   "$this->{document_root}/wizard_prontus/prontus_dir/cpan", 'core');

        # Chequear integridad de lo copiado
        my $cmpResult = $this->compareDirs("$this->{document_root}/wizard_prontus/prontus_dir/cpan/core", "$this->{dir_descarga}/wizard_prontus/prontus_dir/cpan/core");
        if ($cmpResult ne '') {
            $Update::ERR = "Error al actualizar Wizard con nuevo core de Prontus: el dir. origen (nueva release) y el de destino presentan diferencias en sus archivos:\n$cmpResult";
            cluck $Update::ERR . " - dir de core target[$this->{document_root}/wizard_prontus/prontus_dir/cpan/core]\n";
            return 0;
        };
    };

    return 1;

};

# ---------------------------------------------------------------
sub install_core_wizard {
# Actualiza /wizard_prontus/core/

    my ($this) = shift;

    # Actualizar el core del wizard, en caso de que se encuentre instalado
    if (-d "$this->{document_root}/wizard_prontus/core") {
        # Copiar el core del wizard
        &glib_fildir_02::copy_tree("$this->{dir_descarga}/wizard_prontus", 'core',
                                   "$this->{document_root}/wizard_prontus", 'core');

        # Chequear integridad de lo copiado
        my $cmpResult = $this->compareDirs("$this->{document_root}/wizard_prontus/core", "$this->{dir_descarga}/wizard_prontus/core");
        if ($cmpResult ne '') {
            $Update::ERR = "Error al actualizar Core del Wizard: el dir. origen (nueva release) y el de destino presentan diferencias en sus archivos:\n$cmpResult";
            cluck $Update::ERR . " - dir target[$this->{document_root}/wizard_prontus/core]\n";
            return 0;
        };
    };

    return 1;

};


# ---------------------------------------------------------------
sub compareDirs {
    my $this = shift;
    my $errors;
    my $targetDir = shift;
    my $sourceDir = shift;

    unless (-d $targetDir) {
        $errors .= "'$targetDir' is not a valid target directory. Please pass the name of a valid target directory enclosed in quotes.\n";
        return $errors;
    }

    unless (-d $sourceDir) {
        $errors .= "'$sourceDir' is not a valid target directory. Please pass the name of a valid target directory enclosed in quotes.\n";
        return $errors;
    }

    opendir THISDIR, $sourceDir;
    my @allFiles = grep { $_ ne '.' and $_ ne '..' && -f $_}  readdir THISDIR;
    closedir THISDIR;

    foreach (@allFiles) {
        if (File::Compare::compare("$sourceDir/$_", "$targetDir/$_") == 1) {
            $errors .= "$_ in source dir. $sourceDir differs from that in target dir. $targetDir\n\n";
        };
        if (File::Compare::compare("$sourceDir/$_", "$targetDir/$_") < 0) {
            $errors .= "$_ found in source dir. $sourceDir but not in target dir. $targetDir\n\n";
        };
    };

    return $errors;

};

# ---------------------------------------------------------------
sub setExecPermisos {
    my ($this) = shift;
    my ($dir) = shift;

    my @entries = &glib_fildir_02::lee_dir($dir);
    my $errors;

    # Recorre recursivamente, asignando permisos
    foreach my $entry (@entries) {
        next if ($entry =~ /^\./);
        if (-d "$dir/$entry") {
            $errors .= $this->setExecPermisos("$dir/$entry");
        } else {
            next if ($entry !~ /(\.cgi|\.pl|\.py)$/);
            if ($entry =~ /^prontus_/ || $entry =~ /^wizard_/) { # solo cambiar permisos a cgi que comiencen con prontus_ o wizard_
                my $ret = chmod 0755, "$dir/$entry";
                $errors .= "No fue posible asignar permisos de ejecucion a $dir/$entry\n" if (!$ret);
            };
        };
    };
    return $errors;
};


# ---------------------------------------------------------------
sub rollback_update {
# Este metodo sirve para dejar todo como estaba antes de la actualizacion
# Se usa cuando uno de los procesos arroja error
# Esta no es la panacéa absoluta, ya que se pueden dar muchos casos extraños.
# La idea es dejar el prontus operativo mientras se revisa que pudo haber pasado

    my ($this) = shift;

    # Copiar /cgi-cpn del backup al dir oficial del sitio
    &glib_fildir_02::copy_tree($this->{dir_backup}, $this->{nom_cgicpn_current},
                               $this->{document_root}, $this->{nom_cgicpn_current});

    # Copiar /cgi-bin del backup al dir oficial del sitio
    &glib_fildir_02::copy_tree($this->{dir_backup}, $this->{nom_cgicpn_current},
                               $this->{document_root}, $this->{nom_cgibin_current});

    # Asignar permisos ejecucion a las cgis, recursivamente.
    my $permResult = $this->setExecPermisos("$this->{document_root}/$this->{nom_cgicpn_current}", 755);
    if ($permResult ne '') {
        $Update::ERR = "Error en el Rollback de Prontus: no se pudo asignar permisos de ejecucion a las CGIs: [$permResult]";
        cluck $Update::ERR . " - dir de cgis backend[$this->{document_root}/$this->{nom_cgicpn_current}]\n";
    };

    # Se obtienen los prontus a Des-Actualizar
    my $core_dirs = $this->get_core_dirs();
    my @prontus_dirs = split(/;/, $core_dirs);
    foreach my $prontus_dir (@prontus_dirs) {

        next if (! -d "$this->{document_root}/$prontus_dir");
        next if (! -d "$this->{dir_backup}/$prontus_dir");

        # Copiar core de la nueva release a dir destino
        &glib_fildir_02::copy_tree("$this->{dir_backup}/$prontus_dir/cpan", 'core',
                                   "$this->{document_root}/$prontus_dir/cpan", 'core');
    }
}
# ---------------------------------------------------------------
sub get_core_dirs {
    my ($this) = shift;
    my ($dir) = $this->{document_root};
    my @entries = &glib_fildir_02::lee_dir($dir);
    my $core_dirs; # core dirs separados por ;
    my $nom_cgicpn_current = $this->{nom_cgicpn_current};
    # Recorre revisando todas las carpetas de la raiz buscando donde haya *-var.cfg y *-id.cfg
    foreach my $entry (@entries) {
        next if ($entry =~ /^\./);
        next if (!-d "$dir/$entry");
        if ((-f "$dir/$entry/cpan/$entry-var.cfg") && (-f "$dir/$entry/cpan/$entry-id.cfg")) {
            warn "revisando[$dir/$entry/cpan/dir_cgi.js] viendo si contiene DIR_CGI_CPAN = '$nom_cgicpn_current'\n";
            # leer el dir_cgi.js para saber si este core corresponde a la version de cgis de prontus en donde esta corriendo el actualizador
            my $buffer_dir_cgi = &glib_fildir_02::read_file("$dir/$entry/cpan/dir_cgi.js"); # DIR_CGI_CPAN = 'cgi-cpn'
            if ($buffer_dir_cgi =~ /DIR_CGI_CPAN *= *['"]$nom_cgicpn_current['"]/s) {
                $core_dirs .= "$entry;";
                warn "found [$entry]\n";
            } else {
                warn "not found\n";
            };
        };
    };
    $core_dirs =~ s/;$//;
    warn "core_dirs[$core_dirs]\n";
    return $core_dirs;
};
# ---------------------------------------------------------------
return 1;

# Para desplegar la doc. desde linea de comandos:
# perldoc Update.pm
# Para generar la doc en html:
# perldoc -T -o html IO::Handle > IO::Handle.html

__END__

=head1 NOMBRE

B<Update.pm> - Clase para Prontus Updates

=for comment
# ---------------------------------------------------------------

=head1 SINOPSIS

Instanciar y acceder a un metodo publico:

    use Update;

    # Creacion del objeto Update (todas los params son obligatorios).
    my $upd_obj = Update->new(
                    'prontus_id'        => 'prontus_noticias',
                    'version_prontus'   => $prontus_varglb::VERSION_PRONTUS,
                    'path_conf'         => $FORM{'_path_conf'},
                    'document_root'     => $prontus_varglb::DIR_SERVER)
                    || die("Error inicializando objeto Update: $Update::ERR\n");

    # Obtener link para descargar el update disponible
    my $lnk_update = $upd_obj->get_status_update();

=for comment
# ---------------------------------------------------------------

=head1 DESCRIPCION

Contiene operaciones necesarias para gestionar el mecanismo de actualizacion automatica de Prontus.

=for comment
# ---------------------------------------------------------------

=head1 AUTOR

Yerko Chapanoff, E<lt>yerko@altavoz.netE<gt>

=cut
