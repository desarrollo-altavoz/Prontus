#!/usr/bin/perl
# --------------------------------------------------------------
# Respaldo de archivos prontus en Dropbox.
# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 11/11/2014 - JOR - Primera versión
# ---------------------------------------------------------------


BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use strict;
use LWP::UserAgent;
use HTTP::Response;

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use lib_dropbox;

#close STDOUT;

my %FORM;
my $DIR_SEMAF;

main: {
    $FORM{'prontus_id'} = $ARGV[0];
    $FORM{'file'} = $ARGV[1];

    &valida_params();

    my ($prontus_id, $ts, $dir_fecha, $relpath_artic);

    # Carga variables de configuracion de prontus.
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus_id'});
    &lib_prontus::load_config(&lib_prontus::ajusta_pathconf($relpath_conf));

    if ($prontus_varglb::DROPBOX eq 'NO' || $prontus_varglb::DROPBOX_ACCESS_TOKEN eq '') {
        # No se hace nada.
        exit;
    };

    print STDERR "[$$] Inicio\n";

    $DIR_SEMAF = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/semaforos";
    &glib_fildir_02::check_dir($DIR_SEMAF) if (! -d $DIR_SEMAF);

    if (-f "$DIR_SEMAF/dropbox_backup.lck") {
        my $pid = &glib_fildir_02::read_file("$DIR_SEMAF/dropbox_backup.lck");

        if ($pid) {
            print STDERR "[$$] Ya existe un proceso corriendo pid[$pid]\n";
            my $mtime = (stat("$DIR_SEMAF/dropbox_backup.lck"))[9];
            my $now = time;
            my $diff = $now - $mtime;
            if ($diff > 1800) { # 30 minutos.
                print STDERR "[$$] Semaforo muy antiguo, eliminando...";
                unlink "$DIR_SEMAF/dropbox_backup.lck";
            } else {
                my $ret = `ps p $pid | grep prontus_dropbox_backup | grep -v grep`;
                if ($ret) {
                    print STDERR "[$$] pid[$pid] still runnin, leaving...\n";
                    exit;
                } else {
                    print STDERR "[$$] $pid is dead\n";
                };
            };
        };
    };

    &glib_fildir_02::write_file("$DIR_SEMAF/dropbox_backup.lck", $$);

    &procesar_archivo($FORM{'file'}) if (-f $FORM{'file'});

    # Revisar si hay más archivos.
    my $dir_dropbox = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/dropbox";
    my @files = glob("$dir_dropbox/*.txt");
    my $file;

    print STDERR "[$$] Buscando si hay mas archivos...\n";
    my $x = 0;
    while (defined($file = shift @files)) {
        print STDERR "[$$] Procesando [$file]\n";
        next if (!-s $file);
        &procesar_archivo($file);
        print STDERR "[$$] Se termino de procesar [$file].\n";

        # La idea es que si van agregando mas archivos mientras este proceso corre, se procecen.
        if ($#files <= 0) {
            print STDERR "[$$] Buscando si hay mas archivos...\n";
            @files = glob("$dir_dropbox/*.txt");

            sleep 5; # esperar 5 segundos.
        };

        last if ($x > 50);

        $x++;
    };

    print STDERR "[$$] Fin.\n";

    unlink "$DIR_SEMAF/dropbox_backup.lck";
    exit;

};

sub procesar_archivo {
    my $file = $_[0];

    open (FILE, "<$file");

    foreach my $linea (<FILE>) {
        chomp($linea);
        my ($tipo, $recurso, $param1, $param2, $param3) = split(';', $linea);
        print STDERR "[$$] tipo[$tipo] recurso[$recurso]\n";
        if ($tipo eq 'art') {
            &procesa_art($recurso, $param1, $param2, $param3); # ts, seccion1, tema1, subtema1

            # actualiza fecha modificacion semaforo, para que no lo vayan a matar!
            utime time, time, "$DIR_SEMAF/dropbox_backup.lck";
        } elsif ($tipo eq 'port') {
            &procesar_port($recurso);
        };

        unlink $file;
    };

};

sub procesar_port {
    my $recurso = $_[0];
    my ($edic, $port) = split('/', $recurso);
    my @local_filelist = &get_port_filelist($edic, $port);

    &lib_dropbox::conectar();

    my $remote_dir = "$prontus_varglb::DIR_CONTENIDO/edic";
    my @dropbox_filelist = &lib_dropbox::get_dir_filelist($remote_dir);

    &sincroniza_directorios(\@local_filelist, \@dropbox_filelist);

};

sub procesa_art {
    my $ts = $_[0];
    my $seccion1 = $_[1];
    my $tema1 = $_[2];
    my $subtema1 = $_[3];
    my $dir_fecha;

    &lib_dropbox::conectar();

    $ts =~ /(\d{8})/;
    $dir_fecha = $1; # solo fecha.
    #$dir_fecha = "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}/site/artic/$dir_fecha"; # ruta completa.

    # Obtener listado de directorios asociados al articulo, incluye vistas.
    my @dirlist = &get_artic_dirlist($dir_fecha);

    foreach my $dir (@dirlist) {
        my $artic_dir = "$prontus_varglb::DIR_SERVER$dir";
        next if (!-d $artic_dir); # saltar si el directorio no existe.

        # Obtener listado de archivos locales.
        my @local_filelist = &get_artic_filelist($artic_dir, $ts);
        # Obtener listado de archivos en Dropbox.
        my @dropbox_filelist = &lib_dropbox::get_dir_filelist($dir);

        &sincroniza_directorios(\@local_filelist, \@dropbox_filelist);

    };

    if ($seccion1) {
        my @local_filelist = &get_relac($ts, $seccion1, $tema1, $subtema1);
        my @dropbox_filelist = &lib_dropbox::get_dir_filelist("$prontus_varglb::DIR_CONTENIDO/cache/taxonomia/pags");

        &sincroniza_directorios(\@local_filelist, \@dropbox_filelist);
    };

};

sub get_relac {
    my $ts = $_[0];
    my $seccion1 = $_[1];
    my $tema1 = $_[2];
    my $subtema1 = $_[3];
    my @local_filelist;
    my $cache_dir = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/cache/taxonomia/pags";
    my @files = glob("$cache_dir/$seccion1*");

    foreach my $file (@files) {
        push @local_filelist, $file;
    };

    return @local_filelist;
};

sub valida_params {
    if ($FORM{'prontus_id'} eq '') {
        print STDERR "[$$] Debe indicar el nombre del Prontus.\n";
        exit;
    };

    if ($FORM{'file'} eq '') {
        print STDERR "[$$] Debe indicar la ruta hacia archivo.\n";
        exit;
    };

};

sub get_artic_filelist {
    my $dir_fecha = $_[0];
    my $ts = $_[1];
    my @files = glob("$dir_fecha/*");
    my @filelist;

    foreach my $file (@files) {
        next if ($file !~ /$ts/); # si tiene el ts del articulo, se sube.
        $file =~ /\.(\w+)$/;
        my $ext = $1;
        next if (exists $prontus_varglb::DROPBOX_FILEXT_EXCLUDE_LIST{$ext});
        my $mtime = (stat($file))[9];
        my $bytes = -s $file;

        next if (-d $file && $bytes == 4096);
        #next if ((time - $mtime) > 60); # solo considerar archivos modificados hace menos de 1 minuto.

        push @filelist, "$file\t$bytes";
    };

    return @filelist;

};

sub get_port_filelist {
    my $edic = $_[0];
    my $port = $_[1];
    my @filelist;

    $port =~ /(.*?)\.\w+$/;
    my $sinext = $1;

    push @filelist, "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/edic/$edic$prontus_varglb::DIR_SECC/$port";
    push @filelist, "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/edic/$edic/xml/$sinext.xml";
    push @filelist, "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/edic/base/rss/$sinext.xml";

    foreach my $port_cfg (keys %prontus_varglb::PORT_PLTS_EXTRA) {
        next if ($port ne $port_cfg);

        my $extra_ports = $prontus_varglb::PORT_PLTS_EXTRA{$port_cfg};

        while ($extra_ports =~ /([\w\-\.]+) *;?/g) {
            my $extra_port = $1;
            push @filelist, "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/edic/$edic$prontus_varglb::DIR_SECC/$extra_port";

            foreach my $mv (keys(%prontus_varglb::MULTIVISTAS)) {
                push @filelist, "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/edic/$edic$prontus_varglb::DIR_SECC-$mv/$extra_port";
            };
        };
    };

    foreach my $mv (keys(%prontus_varglb::MULTIVISTAS)) {
        push @filelist, "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/edic/$edic$prontus_varglb::DIR_SECC-$mv/$port";
    };

    return @filelist;
};

sub get_artic_dirlist {
    my $dir_fecha = $_[0];
    my @dirlist;

    push @dirlist, "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha";
    push @dirlist, "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha$prontus_varglb::DIR_ASOCFILE";
    push @dirlist, "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha$prontus_varglb::DIR_IMAG";
    push @dirlist, "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha$prontus_varglb::DIR_MMEDIA";
    push @dirlist, "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha$prontus_varglb::DIR_PAG";
    push @dirlist, "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha/pagspag";
    push @dirlist, "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha$prontus_varglb::DIR_SWF";
    push @dirlist, "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha/xml";

    # Se agregan los directorios custom.
    foreach my $custom_dir (keys %prontus_varglb::DROPBOX_CUSTOM_DIR) {
        next if (!$custom_dir);
        push @dirlist, "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha/$custom_dir";
    };

    foreach my $mv (keys(%prontus_varglb::MULTIVISTAS)) {
        push @dirlist, "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha$prontus_varglb::DIR_PAG-$mv";
        push @dirlist, "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha/pagspar-$mv";
    };

    # Se incluye la media externa.
    if ($prontus_varglb::EXTERNAL_MMEDIA == 1) {
        push @dirlist, "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EXMEDIA/$dir_fecha";
    };

    return @dirlist;
};

sub sincroniza_directorios {
    my $local_filelist_ref = $_[0];
    my $dropbox_filelist_ref = $_[1];
    my @local_filelist = @{$local_filelist_ref};
    my @dropbox_filelist = @{$dropbox_filelist_ref};

    foreach my $local_file (@local_filelist) {
        my ($local_fullpath, $local_bytes) = split(/\t/, $local_file);
        my $local_relpath = $local_fullpath;
        $local_relpath =~ s/$prontus_varglb::DIR_SERVER//sg;
        my $upload = 1;

        next if (!-f $local_fullpath);

        #print STDERR "local_relpath[$local_relpath] local_bytes[$local_bytes]\n";

        foreach my $remote_file (@dropbox_filelist) {
            my ($remote_path, $remote_isdir, $remote_bytes) = split(/\t/, $remote_file);
            next if ($remote_isdir);

            #print STDERR "remote_path[$remote_path] remote_bytes[$remote_bytes]\n";

            if ($local_relpath eq $remote_path) { # archivo encontrado, decidir si se sube o no.
                $upload = 0;
                if ($local_bytes != $remote_bytes) {
                    $upload = 1;
                };
                last;
            };
        };

        if ($upload) {
            print STDERR "[$$] Subiendo [$local_fullpath] => [$local_relpath]\n";
            my ($resp, $msgerr) = &lib_dropbox::upload_file($local_fullpath, $local_relpath);
            if (!$resp) {
                print STDERR "[$$] No fue posible subir el archivo [$local_fullpath] => [$local_relpath] msgerr[$msgerr]\n";
                # vuelve a intentar.
                ($resp, $msgerr) = &lib_dropbox::upload_file($local_fullpath, $local_relpath);
            };

            if (!$resp) {
                print STDERR "[$$] No fue posible subir el archivo [$local_fullpath] => [$local_relpath] msgerr[$msgerr]\n";
            } else {
                print STDERR "[$$] Archivo subido [$local_fullpath] => [$local_relpath]\n";
            };
        };
    };

    # Articulo o archivo eliminado.
    foreach my $remote_file (@dropbox_filelist) {
        my ($remote_path, $remote_isdir, $remote_bytes) = split(/\t/, $remote_file);
        next if ($remote_isdir);

        my $local_path = "$prontus_varglb::DIR_SERVER$remote_path";

        if (!-f $local_path) { # si el archivo local no existe con el mismo nombre, es que fue eliminado.
            my $resp = &lib_dropbox::delete_path($remote_path);
            if ($resp) {
                print STDERR "[$$] Archivo eliminado remote_path[$remote_path].\n";
            } else {
                print STDERR "[$$] El archivo remote_path[$remote_path] no se pudo eliminar.\n";
            };
        };
    };

};


