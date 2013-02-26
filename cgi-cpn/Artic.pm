#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl/
# 2002 - 2012 Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

package Artic;
use strict;
use Carp qw(cluck carp);
use warnings;
no warnings 'uninitialized';

use DBI;
use lib_prontus;
use lib_thumb;
use glib_fildir_02;
use glib_str_02;
use glib_hrfec_02;
use File::Copy;


# use diagnostics;


# ---------------------------------------------------------------
# errores orientados a que los pueda leer el usuario, sin info del ambiente.
# el texto completo del error se tira al STDERR
our $ERR;
our $XML_BASE =
"<?xml version='1.0' encoding='UTF-8'?>
<artic_data>
<_private>
<_txt_titular>
</_txt_titular>
<_art_autoinc></_art_autoinc>
<_users_id></_users_id>
<_fid></_fid>
<_plt></_plt>
<_fechap></_fechap>
<_horap></_horap>
<_fechae></_fechae>
<_horae></_horae>
<_soloportadas></_soloportadas>
<_seccion1></_seccion1>
<_tema1></_tema1>
<_subtema1></_subtema1>
<_seccion2></_seccion2>
<_tema2></_tema2>
<_subtema2></_subtema2>
<_seccion3></_seccion3>
<_tema3></_tema3>
<_subtema3></_subtema3>
<_nom_seccion1></_nom_seccion1>
<_nom_tema1></_nom_tema1>
<_nom_subtema1></_nom_subtema1>
<_nom_seccion2></_nom_seccion2>
<_nom_tema2></_nom_tema2>
<_nom_subtema2></_nom_subtema2>
<_nom_seccion3></_nom_seccion3>
<_nom_tema3></_nom_tema3>
<_nom_subtema3></_nom_subtema3>
<_autor></_autor>
<_txt_bajada></_txt_bajada>
<_alta></_alta>
<_tax></_tax>
<_tags></_tags>
<_tagnames></_tagnames>
</_private>

<_public>
</_public>
</artic_data>";

# ---------------------------------------------------------------
sub new {
# Crea el objeto y retorna una referencia a el.
# Este metodo es el primer paso obligado tanto para crear o leer un articulo.

    my $clase = shift;
    my $artic = {@_};
    bless $artic, $clase;

    # Atributos recibidos.
    $artic->{document_root}      ||= $ENV{'DOCUMENT_ROOT'}; # valor por omision
    $artic->{prontus_id}         ||= '';
    $artic->{public_server_name} ||= '';
    $artic->{cpan_server_name}   ||= '';
    if ( ($artic->{prontus_id} !~ /^[\w\d]+$/) || ($artic->{public_server_name} eq '')
                                               || ($artic->{cpan_server_name} eq '') ) {
        $Artic::ERR = "Artic::new con params no validos:\n"
                    . "prontus_id[$artic->{prontus_id}] \n"
                    . "public_server_name[$artic->{public_server_name}] \n"
                    . "cpan_server_name[$artic->{cpan_server_name}] \n";
        return 0;
    };

    # Si no se indica el TS, asigna uno nuevo
    $artic->{ts} ||= '';
    if ($artic->{ts} ne '') {
        if ($artic->{ts} !~ /^\d{14}$/) {
            $Artic::ERR = "TS indicado a Artic::new no es valido. TS[$artic->{ts}]";
            return 0;
        };
    } else {
        $artic->{ts} = $artic->_get_new_ts();
    };
    $artic->{fechac} = &lib_prontus::get_dirfecha_by_ts($artic->{ts});

    # Establece y chequea dirs
    $artic->_set_dirs() || return 0;
    $artic->{fullpath_xml} = "$artic->{dst_xml}/$artic->{ts}" . '.xml';

    # Si el hash no viene, se incializa como vacio.
    # Los campos de este hash se accesan asi: my $val_campo = $artic->{campos}->{$nom_campo};
    if (!ref($artic->{campos})) {
        $artic->{campos}  = {}; # es {} porque es una referencia, sino seria () # asume todos los nombres de campo en minusc.
    };

    # Inicializa hash de datos que cargaran desde el xml
    $artic->{xml_content} = {};

    # Se llena en el metodo que genera la vista generar_vista_art()
    $artic->{post_proceso_lista} = '';

    return $artic;
};

# ---------------------------------------------------------------
sub set_preview_artic {
    # Permite establecer que el ts para todos los efectos es 'preview'
    my $this = shift;
    $this->{ts} = 'preview';
    # Re-asigna el path xml
    $this->{fullpath_xml} = "$this->{dst_xml}/$this->{ts}" . '.xml';
};

# ---------------------------------------------------------------
sub get_fullpath_artic {
# Esta funcion retorna la ruta absoluta del artic si es que se cuenta con ella en el objeto.
    my $this = shift;
    my $mv = shift;
    my $plt = shift; # puede venir de los campos recibidos del form, o bien, desde el xml
    my $fullpath_artic;

    if ( ($plt ne '') && ($this->{ts} ne '') ) {
        my $ext = &lib_prontus::get_file_extension($plt);
        my $fulldir_vista = $this->_get_fulldir_vista($mv);
        $fullpath_artic = "$fulldir_vista/$this->{ts}" . '.' . $ext;
    };
    return $fullpath_artic;

};

# ---------------------------------------------------------------
sub get_nom_artic {
# Esta funcion retorna el nombre del archivo del articulo, por ejemplo 20090522104356.html
    my $this = shift;
    my $plt = shift; # puede venir de los campos recibidos del form, o bien, desde el xml
    my $nom_artic;

    if ( ($plt ne '') && ($this->{ts} ne '') ) {
        my $ext = &lib_prontus::get_file_extension($plt);
        $nom_artic = $this->{ts} . '.' . $ext;
    };
    return $nom_artic;

};

# ---------------------------------------------------------------
sub _get_fulldir_vista {

    my $this = shift;
    my $mv = shift;

    my $fulldir_vista = $this->{dst_pags};
    # warn "fulldir_vista1[$fulldir_vista]";
    no warnings 'syntax'; # para evitar el msg "\1 better written as $1"
    $fulldir_vista =~ s/(\/site\/artic\/\d{8}\/pags)/\1-$mv/ if ($mv);
    # warn "fulldir_vista2[$fulldir_vista] mv[$mv]";

    return $fulldir_vista;
};
# ---------------------------------------------------------------
sub _set_dirs {
# Setea directorios de trabajo del articulo.
    my $this = shift;

    $this->{dst_base} = $this->{document_root}
                          . "/$this->{prontus_id}"
                          . "/site/artic/$this->{fechac}";
    $this->{dst_xml}        = "$this->{dst_base}/xml";
    $this->{dst_pags}       = "$this->{dst_base}/pags";
    $this->{dst_asocfile}   = "$this->{dst_base}/asocfile/$this->{ts}";
    $this->{dst_foto}       = "$this->{dst_base}/imag";
    $this->{dst_swf}        = "$this->{dst_base}/swf";
    $this->{dst_multimedia} = "$this->{dst_base}/mmedia";

    $this->{pathdir_plt} = $this->{document_root}
                          . "/$this->{prontus_id}"
                          . "/plantillas/artic/fecha";
    $this->{pathdir_plt_macros} = "$this->{pathdir_plt}/macros";
    $this->{pathdir_plt_pags} = "$this->{pathdir_plt}/pags";


    if (! $this->_check_artic_dirs()) {
        $Artic::ERR = "No se pueden crear directorios del artículo, dst_base[$this->{dst_base}]";
        cluck $Artic::ERR . "[$!]\n";
        return 0;
    };

    $this->{lnk_multimedia} = &lib_prontus::remove_front_string($this->{dst_multimedia},
                                                                    $this->{document_root});

};
# ---------------------------------------------------------------
sub DESTROY { # se llama automaticamente al destruirse el objeto

};

# ---------------------------------------------------------------
sub _check_artic_dirs {
    my ($this) = shift;
    &glib_fildir_02::check_dir($this->{dst_xml})        || return 0;
    &glib_fildir_02::check_dir($this->{dst_pags})       || return 0;
    &glib_fildir_02::check_dir($this->{dst_asocfile})   || return 0;
    &glib_fildir_02::check_dir($this->{dst_foto})       || return 0;
    &glib_fildir_02::check_dir($this->{dst_swf})        || return 0;
    &glib_fildir_02::check_dir($this->{dst_multimedia}) || return 0;

};

# --------------------------------------------------------------------
sub exec_post_proceso_art {
# Una vez escrito el articulo, ubica el nombre del script de post-proceso (con extension y
# con path absoluto completo) y lo ejecuta.
# Script de postproceso es optativo y puede ir en cualquier parte del articulo.
# Pueden ser varios.

    my ($this) = shift;
    my ($pathArticulo) = shift;
    my ($isNew) = shift;
    my ($postProcesoLista) = $this->{post_proceso_lista}; # lista separada por \t de postprocesos

    # Ejecuta en bground el proceso pasandole x param. el path completo al articulo.
    use FindBin '$Bin';
    my $rutaScript = $Bin;

    my $newOrEdit = 'E';
    $newOrEdit = 'N' if ($isNew);

    my @postProcesos = split(/\t/, $postProcesoLista);
    foreach my $pp (@postProcesos) {
        # Para que sea un script valido debe ubicarse en el mismo dir. de cgi del prontus o a
        # lo mas un nivel hacia arriba.
        if ( ($pp =~ /^\w/) || ($pp =~ /^\.\.(\/|\\)\w/) ) {
            my $cmd = "$rutaScript/$pp $pathArticulo $this->{public_server_name} $newOrEdit >/dev/null 2>&1 &";
            print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
            system $cmd;
        };
    };
};

# ---------------------------------------------------------------
sub _get_new_ts {
# asigna timestamp unico para el articulo.
    my ($this) = shift;
    my $ts = &glib_hrfec_02::get_dtime_pack4();
    my $fechac = &lib_prontus::get_dirfecha_by_ts($ts);
    while (-f "$this->{document_root}/$this->{prontus_id}/site/artic/$fechac/xml/$ts" . '.xml') {
        $ts = &glib_hrfec_02::suma_segs($ts, 1);
    };
    return $ts;
};
# ---------------------------------------------------------------
sub generar_xml_artic {
# En este XML queda solo lo esencial. Los datos derivados que se calculan u obtienen en base a
# los esenciales no se almacenan aqui.
    my ($this) = shift;

    # Atributos calculados o de uso interno.
    $this->{xml_data} = $Artic::XML_BASE;

    # Escribe htaccess en el dir de xml de artic para prhibir acceso http a este.
    &glib_fildir_02::write_file("$this->{dst_xml}/.htaccess", "Order Allow,Deny\nDeny from all");

    # Adecuar algunos datos que lo requieran para luego reemplazar todo de una en el XML
    if ($this->{campos}->{'_fechap'} eq '') {
        $this->{campos}->{'_fechap'} = &lib_prontus::asigna_fecha_default('_fechap');
    };

    if ($this->{campos}->{'_fechae'} eq '') {
        $this->{campos}->{'_fechae'} = &lib_prontus::asigna_fecha_default('_fechae');
    };

    if ($this->{campos}->{'_txt_titular'} eq '') {
        $this->{campos}->{'_txt_titular'} = 'SIN TITULO';
    };


    # convierte tags a latin1 para poder aplicar la er
    utf8::decode($this->{campos}->{'_tags'});
    $this->{campos}->{'_tags'} =~ s/[^\w\,\-áéíóúüñÁÉÍÓÚÜÑ \.]//g;
    $this->{campos}->{'_tags'} =~ tr/ÁÉÍÓÚÜÑ/áéíóúüñ/;
    $this->{campos}->{'_tags'} = lc($this->{campos}->{'_tags'});
    # restaura a utf8
    utf8::encode($this->{campos}->{'_tags'});



    $this->_artic_ajusta_horas();

    # Guarda recursos del articulo
    $this->_guarda_recursos('asocfile');
    $this->_guarda_recursos('multimedia');
    $this->_guarda_recursos('foto');
    $this->_guarda_recursos('swf');

    # Fotos fijas, a continuacion de las fotos
    $this->_guarda_fotosfijas();

    # Fotos subidas masivamente via uploadify
    $this->_guarda_fotosbatch();

    # Fotos editadas
#     $this->_guarda_fotoeditada();
    $this->_guarda_fotofromdir('/' . $this->{prontus_id} . '/cpan/procs/imgedit', '_fotoeditada');

    foreach my $nom_campo (keys %{$this->{campos}}) {
        # Salta los recursos, ya procesados de manera especial

        next if ($nom_campo =~ /^(asocfile_|swf_|multimedia_|foto_|fotofija_|_wfoto_|_hfoto_)/);
        my $val_campo = $this->{campos}->{$nom_campo};

        # elimina posibles caracteres de control
        # utf8::decode($val_campo);
        # $val_campo =~ s/[^\x0A\x0D\x20-\x9F\xA1-\xFF]//g;
        # restaura a utf8
        # utf8::encode($val_campo);

        # Codigo de reemplazo por ALD 08/02/2011
        $val_campo =~ s/[\x01-\x09\x0B\x0C\x0E-\x1F]//g;


        # Solo permite campos con _ para los reservados que van en el XML

        if ($nom_campo =~ /^_/) {
            next if ($Artic::XML_BASE !~ /<_private>.*<$nom_campo>.*<\/$nom_campo>.*<\/_private>/s);
        };
        next if (! $val_campo);

        my $parse_as_cdata = 0;
        $parse_as_cdata = 1 if ($nom_campo =~ /^(_?txt_|vtxt_)/i);
        $parse_as_cdata = 1 if ($nom_campo !~ /^_/); # aplica cdata cualquier campo no reservado
        if ($nom_campo =~ /^vtxt_/i) {
            $val_campo =~ s/https?:\/\/$this->{cpan_server_name}//isg;
            $val_campo =~ s/https?:\/\/$this->{public_server_name}//isg;
        };
        $this->{xml_data} = &lib_prontus::replace_in_xml($this->{xml_data},
                                                                 $nom_campo,
                                                                 $val_campo,
                                                                 $parse_as_cdata);
    };

    # borra el contenido anterior del hash de campos, porque si se escribe uno nuevo, pues ya no corre.
    # esta var lo usa el obj. para no leer mas de 1 vez el xml
    %{$this->{xml_content}} = ();

    # Se escribe el XML a disco
    return $this->_flush_xml();


};
# ---------------------------------------------------------------
sub _flush_xml {
# Escribe a disco el XML
    my ($this) = shift;

    # Escribir XML
    &glib_fildir_02::write_file($this->{fullpath_xml}, $this->{xml_data});
    if ((-f $this->{fullpath_xml}) && (-s $this->{fullpath_xml})) {
        return 1;
    } else {
        $Artic::ERR = 'Error escribiendo XML del artículo';
        cluck $Artic::ERR . "[$!]";
        return 0;
    };
}

# ---------------------------------------------------------------
sub _artic_ajusta_horas {
# Ajusta horas desde los valores de entrada antes de guardarlos en el xml
    my ($this) = shift;

    my %horas;

    $horas{'_horap'} = $this->{campos}->{'_horap'};
    if (!$horas{'_horap'}) {
        $horas{'_horap'} = &glib_hrfec_02::get_dtime_pack4();
        if ($horas{'_horap'} =~ /(\d{2})(\d{2})\d{2}$/) {
            $horas{'_horap'} = $1 . ':' . $2;
        };
    };
    $horas{'_horae'} = $this->{campos}->{'_horae'};

    my ($iso_horap, $iso_horae);

    foreach my $nom_campo (keys %horas) {
        my $val_campo = $horas{$nom_campo};
        $val_campo = '00:00' if ($val_campo !~ /^\d\d:\d\d$/);
        my ($hh, $mm);
        if ($val_campo =~ /^(\d\d):(\d\d)$/) {
            $hh = $1;
            $mm = $2;
            $hh = '00' if ($hh eq '24');
            $hh = '23' if ($hh > 23);
            $hh = '59' if ($mm > 59);
            $val_campo = $hh . ':' . $mm;
        };
        $this->{campos}->{$nom_campo} = $val_campo;
    }; # foreach horas

};

# ---------------------------------------------------------------
sub _guarda_recursos {
# Guarda en xml y disco los recursos de un cierto tipo asociados al articulo

    my ($this) = shift;
    my ($type) = shift; # SWF, FOTO, ASOCFILE, MULTIMEDIA
    my ($dst_dir);
    return if ($type !~ /^(swf|foto|asocfile|multimedia)$/);
    $dst_dir = $this->{'dst_' . $type};

    foreach my $nom_campo (keys %{$this->{campos}}) {
        my $val_campo = $this->{campos}->{$nom_campo};
        next if ($nom_campo !~ /^$type\_\w+/);
        # Ver si hay archivo existente para el recurso
        my $arch_existente = $this->{campos}->{'_hidd_' . $nom_campo}; # ej: foto_1120090528115643.jpg
        my $nom_arch;

        # Variables especiales solo para FOTOs
        my ($msg_size, $wfoto, $hfoto);

        # Si el usr. especifico uno nuevo
        if ($val_campo ne '') {
            $nom_arch = $this->_get_newnom_arch($type, $nom_campo, $val_campo, $arch_existente);
            next if ($nom_arch eq '');
            &glib_fildir_02::check_dir($dst_dir);
            &File::Copy::move($val_campo, "$dst_dir/$nom_arch");

            # Si es foto, medirla
            if ($type eq 'foto') {
                ($msg_size, $wfoto, $hfoto) = &lib_prontus::dev_tam_img("$dst_dir/$nom_arch");
                if ($msg_size) {
                    cluck "Error: $msg_size foto[$dst_dir/$nom_arch] - dim[$wfoto, $hfoto]\n";
                    next;
                };
            };

            # Guarda archivo descriptor, especial para MULTIMEDIA
            if ($type eq 'multimedia') {
                # my ($nomfile_aux, $buffer_aux) = $this->_get_aux_mediafile("$nom_campo$this->{ts}", $nom_arch);
                # &glib_fildir_02::write_file("$dst_dir/$nomfile_aux", $buffer_aux);
            };

        # Si no se esta subiendo nada nuevo, ver si habia uno existente
        } else {
            if ($arch_existente ne '') {
                $nom_arch = $arch_existente;

                if ($type eq 'foto') {
                    $wfoto = $this->{campos}->{'_w' . $nom_campo}; # ancho
                    $hfoto = $this->{campos}->{'_h' . $nom_campo}; # alto
                };

                my $borrar_arch = $this->{campos}->{'_borr_' . $nom_campo};
                if ($borrar_arch eq 'S') {
                    # my $full_path_arch = "$dst_dir/$nom_arch";
                    # unlink $full_path_arch if (-f $full_path_arch);

                    # Obtener nombre de arch. sin extension
                    my $nom_sin_ext = $nom_arch;
                    $nom_sin_ext =~ s/\.\w*$//;

                    # Borra todos los relacionados
                    my $res = unlink glob("$dst_dir/$nom_sin_ext" . '.*');

                    $nom_arch = ''; # para no grabar la entrada en el xml
                } else {
# ya no se edita por aca la img, sino via editor de imagenes
#                    if ($type eq 'foto') {
#                        # ver si habia q hacerle algo a la imagen , como por ej. un crop
#                        my $crop_data = $this->{campos}->{'_crop_' . $nom_campo};
#                        # print STDERR "nom_campo[$nom_campo] crop_data[$crop_data] nom_arch[$nom_arch] y val_campo[$val_campo]\n";
#                        if ($crop_data =~ /^[0-9]+,[0-9]+,[0-9]+,[0-9]+$/) {
#                            my ($srcX, $srcY, $width, $height) = split(/\,/, $crop_data);
#                            my ($binfoto, $final_dimx, $final_dimy) = &lib_thumb::make_crop($srcX, $srcY, $width, $height, "$dst_dir/$nom_arch");
#                            my $nom_arch_crop = $this->_guarda_binfoto_prontus($nom_arch, $final_dimx, $final_dimy, $binfoto, '');
#                            print STDERR "nom_campo[$nom_campo] crop_data[$crop_data] nom_arch_crop[$nom_arch_crop] y nom_arch[$nom_arch]\n";
#                            $this->_add_foto_prontus_xml($final_dimx, $final_dimy, $nom_arch_crop);
#                        };
#                    };

                };
            };
        };

        # Guardar nombre del archivo en el xml
        if ($nom_arch ne '') {
            if ($type eq 'foto') {
                $this->_add_foto_prontus_xml($wfoto, $hfoto, $nom_arch);
                if($nom_campo =~ /^foto_posting_.*?$/) {
                    $this->_guarda_fotos_posting($nom_campo, $nom_arch);
                }
            } else {
                $this->{xml_data} = &lib_prontus::replace_in_xml($this->{xml_data}, $nom_campo, $nom_arch);
            };
        };

    };
};

# ---------------------------------------------------------------
sub _get_newnom_arch {
# Obtiene un nuevo nombre para el recurso
    my ($this) = shift;
    my ($type) = shift;
    my ($nom_campo) = shift;
    my ($val_campo) = shift;
    my ($arch_existente) = shift;

    my $nom_arch;

    # Valida extensiones permitidas por prontus (seguridad)
    return '' if(! &lib_prontus::check_extension($val_campo, $prontus_varglb::UPLOADS_PERMITIDOS));

    if ($type =~ /^(swf|multimedia)$/) {
        my $extension_arch = &lib_prontus::get_file_extension($val_campo);
        $extension_arch = 'xxx' if ($extension_arch eq '');
        $nom_arch = "$nom_campo$this->{ts}.$extension_arch";
    };

    if ($type eq 'foto') {
        $this->_check_ext_foto($val_campo) || return '';
        $nom_arch = $this->_get_nom_foto($val_campo, $arch_existente);
    };

    if ($type eq 'asocfile') {
        no strict "refs";
        my $real_path = $this->{campos}->{$nom_campo}{'real_path'};
        use strict;
        $nom_arch = $this->_get_nom_asocfile($real_path, $arch_existente);
    };

    return $nom_arch;
};

# ---------------------------------------------------------------
sub _check_ext_foto {
    my ($this) = shift;
    my ($path_foto) = shift;

    my $ext;
    $ext = $1 if ($path_foto =~ /\.(\w+)$/);
    if ($ext =~ /^(jpe?g|jpeg?|gif|png)$/i)  {
        return 1;
    } else {
        return 0;
    };
};

# ---------------------------------------------------------------
sub _get_aux_mediafile {
# Obtiene nombre de archivo descriptor para multimedia y su contenido.
    my ($this) = shift;
    my ($solo_nom) = shift;
    my ($nom_arch_mm) = shift;
    my ($extension_mm) = &lib_prontus::get_file_extension($nom_arch_mm);
    my ($nom_file, $texto_mm);
    # Real
    if ($extension_mm =~ /^(rm|ra|rmvb|rts)$/) {
        $texto_mm = 'http://'. $this->{public_server_name} . $this->{lnk_multimedia} . '/' . $nom_arch_mm;
        $nom_file = $solo_nom . '.ram';
    }
    # m3u
    elsif ($extension_mm =~ /^(aac|aif|aiff|m4a|mid|midi|mp2|mp3|mpa|mpu|msv|ogg|wav|wave|wma)$/) {
        $texto_mm = 'http://'. $this->{public_server_name} . $this->{lnk_multimedia} . '/' . $nom_arch_mm;
        $nom_file = $solo_nom . '.m3u';
    }
    # m4u
    elsif ($extension_mm =~ /^(m1v|m2v|m4e|mp4|mpe|mpeg|mpg|mpv2|ogm)$/) {
        $texto_mm = 'http://'. $this->{public_server_name} . $this->{lnk_multimedia} . '/' . $nom_arch_mm;
        $nom_file = $solo_nom . '.m4u';
    }
    # wvx
    elsif ($extension_mm =~ /^(asf|wm|wmv)$/i) {
        $texto_mm = 'http://'. $this->{public_server_name} . $this->{lnk_multimedia} . '/' . $nom_arch_mm;
        $texto_mm = '<asx version="3.0">'
                  . '<entry>'
                  . "<ref href=\"$texto_mm\" />"
                  . '</entry>'
                  . '</asx>';

        $nom_file = $solo_nom . '.wvx';
    }
    # Otros tipos se parsean directamente.
    else {
        $nom_file = $nom_arch_mm;
    };

    return($nom_file, $texto_mm);

};
# ---------------------------------------------------------------
sub _get_nom_asocfile {
# retorna nombre de archivo para asocfile_i, con extension y sin path
    my ($this) = shift;

    my $texto = shift;
    my $af_existente = shift;


    my $nomfile;
    my $ext;
    # print STDERR "texto[$texto] - af_existente[$af_existente]\n";
    if ($texto =~ /(\/|\\)?([^\/\\]+?)(\.\w+)$/) {
        $nomfile = lc $2;
        $ext = lc $3; # ext con punto
    };
    $ext = '.xxx' if ($ext eq '');

    # print STDERR "nomfile[$nomfile]\n";
    $nomfile =~ tr/\xe1\xe9\xed\xf3\xfa\xc1\xc9\xcd\xd3\xda\xd1\xf1\x20\xfc\xdc/aeiouaeiounn_uu/;
    $nomfile =~ s/\W/_/sg;

    return '' if ($nomfile eq '');

    # elimina el existente porque ahora viene uno nuevo
    if ( ($af_existente ne '') && (-f "$this->{dst_asocfile}/$af_existente") ) {
        unlink "$this->{dst_asocfile}/$af_existente";
    };


    if (-f "$this->{dst_asocfile}/$nomfile$ext") {
        # Si el arch. existe debo ponerle un nombre distinto,
        # salvo q ya haya un archivo para este control,
        # en cuyo caso lo reemplazo, usease, uso el mismo nombre de archivo.
        if ($af_existente eq "$nomfile$ext") {
            return "$nomfile$ext";
        };

        my $sufijo = '1';
        my $nomfile_orig = $nomfile;
        while (-f "$this->{dst_asocfile}/$nomfile$ext") {
            $nomfile = $nomfile_orig . '_' . $sufijo;
            $sufijo++;
        };
        return "$nomfile$ext";
    };

    return "$nomfile$ext";
};
# ---------------------------------------------------------------
sub _get_nom_foto {
# Obtiene nombre de la sgte foto que toca para este articulo.
# Dicho nombre comenzara con el correlativo sgte al ultimo ingresado
# 10/03/2011 - CVI - Ahora se hará un random para minimizar que el nombre no se repita
# 20/02/2012 - CVI - Se corrige random, y se cambia a un esquema mejor
    my $this = shift;

    my $path_foto = shift;
    my $foto_existente = shift;

    #~ print STDERR "foto_existente[$foto_existente]\n";
    my $regexp = "--regexp='".$this->{ts}.'\.[a-zA-Z]\{1,\}$'."'";
    my $res = `ls $this->{dst_foto} | grep $regexp`;

    my @files = split(/\s+/, $res);
    my $max = 0;
    foreach my $imag (@files) {
        # CVI - por seguridad se agrega un IF, ya que ese $1 a veces traia basura
        if($imag =~ /foto_(\d+)$this->{ts}/i) {
            my $thisnum = $1;
            if($thisnum > $max) {
                $max = $thisnum;
            };
        };
    }
    my $num = $max + 1;
    $num = &glib_str_02::format_n($num, 8) if(length($num) < 8);
    my $nomfile = 'foto_' . $num . $this->{ts};

    my $ext;
    if ($path_foto =~ /(\/|\\)?([^\/\\]+?)(\.\w+)$/) {
        $ext = lc $3; # ext con punto
    };

    return "$nomfile$ext";
};
# --------------------------------------------------------------------
sub _existe_foto {
# chequea si la foto ya existe, sabiendo que viene en formato
# foto_\d{2}\d{3}\d{14}\.\w+ siendo \d{3} un random
    my $this = shift;
    my $ruta = shift;

    my ($ruta_dir, $nom, $ts);
    if ($ruta =~ /(.*)(\/|\\)([^\/\\]+?)\d{3}(\d{14})(\.\w+)$/) {
        $ruta_dir = $1;
        $nom = $3;
        $ts = $4;
    };

    return 0 if (! -d $ruta_dir);
    my @lisdir = &glib_fildir_02::lee_dir($ruta_dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    foreach my $k (sort @lisdir) {
        if ((-f "$ruta_dir/$k") && ($k =~ /^$nom\d{3}$ts\.\w+/)) {
            return 1; # encuentra
        };
    };

    return 0;
};

# ---------------------------------------------------------------
sub _guarda_fotosbatch {
    my $this = shift;
    my $document_root = $this->{document_root};
    my $prontus_id = $this->{prontus_id};
    my $dst_dir = $this->{'dst_foto'};

    my $rel_dir_uploadify = "/$prontus_id/cpan/procs/uploadify";
    my $dir_uploadify = "$document_root$rel_dir_uploadify";
    &glib_fildir_02::check_dir($dir_uploadify);

    foreach my $nom_campo (keys %{$this->{campos}}) {
        next if ($nom_campo !~ /^_fotobatch\d+/);
        my $val_campo = $this->{campos}->{$nom_campo}; # path de la foto, pero s/doc. root
        my $path_foto_batch = "$document_root$val_campo";
        next if ((!-f $path_foto_batch) || (!-s $path_foto_batch));

        my $nom_arch;

        # Variables especiales solo para FOTOs
        my ($msg_size, $wfoto, $hfoto);

        $nom_arch = $this->_get_newnom_arch('foto', '', $path_foto_batch, '');
        next if ($nom_arch eq '');
        &glib_fildir_02::check_dir($dst_dir);
        &File::Copy::move($path_foto_batch, "$dst_dir/$nom_arch");
        &lib_prontus::purge_cache("$dst_dir/$nom_arch");

        # medir foto
        ($msg_size, $wfoto, $hfoto) = &lib_prontus::dev_tam_img("$dst_dir/$nom_arch");
        if ($msg_size) {
            cluck "Error: $msg_size foto[$dst_dir/$nom_arch] - dim[$wfoto, $hfoto]\n";
            next;
        };

        # Guardar nombre del archivo en el xml
        if ($nom_arch ne '') {
            $this->_add_foto_prontus_xml($wfoto, $hfoto, $nom_arch);
        };

    };

};
# ---------------------------------------------------------------
sub _guarda_fotoeditada {
    my $this = shift;
    my $document_root = $this->{document_root};
    my $prontus_id = $this->{prontus_id};
    my $dst_dir = $this->{'dst_foto'};

    my $rel_dir_imgedit = "/$prontus_id/cpan/procs/imgedit";
    my $dir_imgedit = "$document_root$rel_dir_imgedit";
    &glib_fildir_02::check_dir($dir_imgedit);

    foreach my $nom_campo (keys %{$this->{campos}}) {
        next if ($nom_campo !~ /^_fotoeditada$/);
        my $val_campo = $this->{campos}->{$nom_campo}; # path de la foto, pero s/doc. root
        my $path_fotoeditada = "$document_root$val_campo";
        next if ((!-f $path_fotoeditada) || (!-s $path_fotoeditada));

        my $nom_arch;

        # Variables especiales solo para FOTOs
        my ($msg_size, $wfoto, $hfoto);

        $nom_arch = $this->_get_newnom_arch('foto', '', $path_fotoeditada, '');
        next if ($nom_arch eq '');
        &glib_fildir_02::check_dir($dst_dir);
        &File::Copy::move($path_fotoeditada, "$dst_dir/$nom_arch");
        &lib_prontus::purge_cache("$dst_dir/$nom_arch");

        # medir foto
        ($msg_size, $wfoto, $hfoto) = &lib_prontus::dev_tam_img("$dst_dir/$nom_arch");
        if ($msg_size) {
            cluck "Error: $msg_size foto[$dst_dir/$nom_arch] - dim[$wfoto, $hfoto]\n";
            next;
        };

        # Guardar nombre del archivo en el xml
        if ($nom_arch ne '') {
            $this->_add_foto_prontus_xml($wfoto, $hfoto, $nom_arch);
        };

    };

};

# ---------------------------------------------------------------
sub _guarda_fotofromdir {
    my $this = shift;
    my $rel_dir_imgedit = shift; # my $rel_dir_imgedit = "/$prontus_id/cpan/procs/imgedit";
    my $nomcontrol_con_url = shift;
    my $document_root = $this->{document_root};
    my $prontus_id = $this->{prontus_id};
    my $dst_dir = $this->{'dst_foto'};

    my $dir_imgedit = "$document_root$rel_dir_imgedit";
    &glib_fildir_02::check_dir($dir_imgedit);

    foreach my $nom_campo (keys %{$this->{campos}}) {
        # next if ($nom_campo !~ /^_fotoeditada$/);
        next if ($nom_campo !~ /^$nomcontrol_con_url$/);
        my $val_campo = $this->{campos}->{$nom_campo}; # path de la foto, pero s/doc. root
        my $path_fotoeditada = "$document_root$val_campo";
        next if ((!-f $path_fotoeditada) || (!-s $path_fotoeditada));

        my $nom_arch;

        # Variables especiales solo para FOTOs
        my ($msg_size, $wfoto, $hfoto);

        $nom_arch = $this->_get_newnom_arch('foto', '', $path_fotoeditada, '');
        next if ($nom_arch eq '');
        &glib_fildir_02::check_dir($dst_dir);
        &File::Copy::move($path_fotoeditada, "$dst_dir/$nom_arch");
        &lib_prontus::purge_cache("$dst_dir/$nom_arch");

        # medir foto
        ($msg_size, $wfoto, $hfoto) = &lib_prontus::dev_tam_img("$dst_dir/$nom_arch");
        if ($msg_size) {
            cluck "Error: $msg_size foto[$dst_dir/$nom_arch] - dim[$wfoto, $hfoto]\n";
            next;
        };

        # Guardar nombre del archivo en el xml
        if ($nom_arch ne '') {
            $this->_add_foto_prontus_xml($wfoto, $hfoto, $nom_arch);
        };

    };

};


# ---------------------------------------------------------------
sub _guarda_fotosfijas {
    my $this = shift;
    my $cpan_server_name = $this->{cpan_server_name};
    my $document_root = $this->{document_root};

    foreach my $nom_campo (keys %{$this->{campos}}) {
        my $val_campo = $this->{campos}->{$nom_campo};
        next if ($nom_campo !~ /^fotofija_\w+/);
        next if (! $val_campo);

        my $cuadrar = $this->{campos}->{'chk_cuadrar_'.$nom_campo};
        #warn("cuadrar[$cuadrar], nom_campo[$nom_campo]");

        # foto externa al sitio
        if (($val_campo =~ /^https?:/i) && ($val_campo !~ /^https?\:\/\/$cpan_server_name/i)) {
            $this->_add_foto_sitioexterno($nom_campo, $val_campo);
            next;
        };

        # foto local al sitio, asi q saca el server name.
        if ($val_campo =~ /^https?\:\/\/$cpan_server_name/i) {
            $val_campo =~ s/^https?\:\/\/$cpan_server_name//i;
        };

        # Correccion a issue FFox 3.6.11
        # foto local al sitio, caso que venga con ../, sacarlos
        # warn("1-nom_campo[$nom_campo] val_campo[$val_campo]");
        if ($val_campo =~ /^\.\.\//) {
            no warnings 'syntax'; # para evitar el msg "\2 better written as $2"
            $val_campo =~ s/^(\.\.\/)+(\w)/\/\2/;
        };
        # warn("2-nom_campo[$nom_campo] val_campo[$val_campo]");

        # - En adelante, puede tratarse de una foto local al articulo, o bien,
        # local al sitio (pero no al artic). -
        if (! -f "$document_root$val_campo") {
            my $parse_as_cdata = 1;
            $this->{xml_data} = &lib_prontus::replace_in_xml($this->{xml_data}, $nom_campo, '', $parse_as_cdata);
            next;
        };

        # Obtiene dimensiones actuales de la foto
        my ($msg, $foto_dimx, $foto_dimy) = &lib_prontus::dev_tam_img("$document_root$val_campo");

        # Obtiene dimensiones maximas permitidas para la foto
        my ($maxw) = $this->{campos}->{'_maxw' . $nom_campo};
        my ($maxh) = $this->{campos}->{'_maxh' . $nom_campo};

        # Solo procede si viene ancho o alto
        if (($maxw =~ /^\d+$/) || ($maxh =~ /^\d+$/)) {
            # si la FOTO es externa al articulo pero local al server:
            if ($val_campo =~ /\/(foto_\w+)$this->{ts}\.\w+/) {
                # foto local al articulo
                my $nom_campo_orig = $1;
                # print STDERR "add foto local, artic local [$prontus_varglb::DIR_SERVER$val_campo]\n";
                $this->_add_foto_sitiolocal_articulolocal($nom_campo, $val_campo, $maxw, $maxh, $foto_dimx, $foto_dimy, $cuadrar, $nom_campo_orig);
            }
            else {
                # print STDERR "add_foto_sitiolocal_articuloexterno\n";
                $this->_add_foto_sitiolocal_articuloexterno($nom_campo, $val_campo, $maxw, $maxh, $foto_dimx, $foto_dimy, $cuadrar);
            };
        };

    };
};
# ---------------------------------------------------------------
sub _guarda_fotos_posting {

    my ($this, $nom_campo_foto, $nom_foto) = @_;
    my $cpan_server_name = $this->{cpan_server_name};
    my $document_root = $this->{document_root};
    my $ts = $this->{ts};
    my $prontus_id = $this->{prontus_id};
    return unless($ts =~ /(\d{8})\d{6}/);
    my $fechac = $1;
    my $path_foto = "/$prontus_id/site/artic/$fechac/imag/$nom_foto";

    # Se comprueba que la foto realmente exista
    if (! -f "$document_root$path_foto") {
        print STDERR "\t$document_root$path_foto no existe\n";
        return;
    };

    # Obtiene dimensiones actuales de la foto
    my ($msg, $foto_dimx, $foto_dimy) = &lib_prontus::dev_tam_img("$document_root$path_foto");
    unless($foto_dimx && $foto_dimy) {
        print STDERR "\tError dev_tam_img $document_root$path_foto: $msg\n";
        return;
    }

    foreach my $nom_campo (keys %{$this->{campos}}) {
        my $val_campo = $this->{campos}->{$nom_campo};
        next if ($nom_campo !~ /^fotofija_\w+/i);
        next if (!$val_campo);
        next if ($val_campo !~ /$nom_campo_foto *\((\d+) *\, *(\d+)\)/i);

        # Obtiene dimensiones maximas permitidas para la foto
        my ($maxw) = $1;
        my ($maxh) = $2;

        # Solo procede si viene ancho o alto
        if (($maxw =~ /^\d+$/) || ($maxh =~ /^\d+$/)) {
            # print STDERR "\tval_campo[$val_campo], maxw[$maxw], maxh[$maxh]\n";

            my $cuadrar = $this->{campos}->{'chk_cuadrar_'.$nom_campo};
            #print STDERR "\tcuadrar[$cuadrar], nom_campo[$nom_campo]";

            if ($path_foto =~ /\/(foto_\w+)$this->{ts}\.\w+/) {
                my $nom_campo_orig = $1;
                $this->{campos}->{'_hidd_'.$nom_campo_orig} = $nom_foto;
                $this->{campos}->{'_path_'.$nom_campo_orig} = $path_foto;
                $this->{campos}->{$nom_campo} = '';
                $this->_add_foto_sitiolocal_articulolocal($nom_campo, $path_foto, $maxw, $maxh, $foto_dimx, $foto_dimy, $cuadrar, $nom_campo_orig);
                print STDERR "\tdatos: $nom_campo, $path_foto, $maxw, $maxh, $foto_dimx, $foto_dimy, $cuadrar, $nom_campo_orig\n";

            };
        };
    };
};

# ---------------------------------------------------------------
sub _add_foto_sitioexterno {
    my ($this) = shift;
    my ($nom_campo) = shift;
    my ($val_campo) = shift;

    my $wfoto_externa = $this->{campos}->{'_w' . $nom_campo};
    my $hfoto_externa = $this->{campos}->{'_h' . $nom_campo};

    # warn "add foto sitio externo val_campo[$val_campo] nom_campo[$nom_campo] wfoto_externa[$wfoto_externa]\n";

    my $foto_externa_xml =
                        "<$nom_campo>"
                        . "\n<_w$nom_campo>$wfoto_externa</_w$nom_campo>"
                        . "\n<_h$nom_campo>$hfoto_externa</_h$nom_campo>"
                        . "\n<![CDATA[$val_campo]]>"
                        . "\n</$nom_campo>\n";

    if (!($this->{xml_data} =~ s/<$nom_campo>.*?<\/$nom_campo>/$foto_externa_xml/is)) {
        $this->{xml_data} =~ s/<_public>/<_public>\n$foto_externa_xml/s;
    };
};

# ---------------------------------------------------------------
sub _add_foto_sitiolocal_articulolocal {
    my ($this, $nom_campo, $val_campo, $maxw, $maxh, $dx, $dy, $cuadrar, $nom_campo_orig) = @_;
    my $document_root = $this->{document_root};

    my $foto_existente = $this->{campos}->{'_hidd_' . $nom_campo_orig};

    # si la foto es mas grande lo que debe ser, se redimensiona
    # y se crea una nueva fotoprontus y esa es asignada a fotofija
    my ($binfoto, $final_dimx, $final_dimy);

    ($final_dimx, $final_dimy) = ($dx, $dy);
    if (($dx > $maxw) || ($dy > $maxh)) {

        ($binfoto, $final_dimx, $final_dimy) = &lib_thumb::make_thumbnail($maxw, $maxh, "$document_root$val_campo", $cuadrar);

        my $nom_arch = $this->_guarda_binfoto_prontus($val_campo, $final_dimx, $final_dimy, $binfoto, $foto_existente);
        return if ($nom_arch eq '');
        $this->_add_foto_prontus_xml($final_dimx, $final_dimy, $nom_arch);
        # Reasigna val_campo para parsear en el artic.
        $val_campo = "$this->{dst_foto}/$nom_arch";
        $val_campo =~ s/^$document_root//;
    };

    # foto local, asi q saca el server name.
    $val_campo =~ s/^https?:\/\/$this->{cpan_server_name}//i;
    $val_campo =~ s/^https?:\/\/$this->{public_server_name}//i;

    # Reemplaza fotofija en xml
    my $parse_as_cdata = 1;
    $this->{xml_data} = &lib_prontus::replace_in_xml($this->{xml_data}, $nom_campo, $val_campo, $parse_as_cdata);

};
# ---------------------------------------------------------------
sub _add_foto_prontus_xml {
  # Parsea foto basica al xml
  my ($this, $wfoto, $hfoto, $nom_arch) = @_; # nom_arch: FOTO_23<TS>.jpg

  my ($num);
  my $ts = $this->{ts};
  if ($nom_arch =~ /^(foto_)(\w+)$ts/i) {
    $num = $2;
  };

  # Guardar foto en el xml
  my $fotoxml = "<foto_$num>"
              . "\n<_nomfoto_$num>$nom_arch</_nomfoto_$num>"
              . "\n<_wfoto_$num>$wfoto</_wfoto_$num>"
              . "\n<_hfoto_$num>$hfoto</_hfoto_$num>"
              . "\n</foto_$num>";

  $this->{xml_data} =~ s/<_public>/<_public>\n$fotoxml/is;

};
# ---------------------------------------------------------------
sub _add_foto_sitiolocal_articuloexterno {
    my ($this, $nom_campo, $val_campo, $maxw, $maxh, $dx, $dy, $cuadrar) = @_;
    my $document_root = $this->{document_root};

    # Si la foto externa es mas grande de lo que debe ser, se redimensiona.
    # Requiera o no ser redimensioanada, siempre se genera una nueva foto
    # prontus para el articulo y luego esta nueva foto, ya internalizada, se asigna a la fotofija.

    my ($binfoto, $final_dimx, $final_dimy);
    if (($dx > $maxw) || ($dy > $maxh)) {
        ($binfoto, $final_dimx, $final_dimy) = &lib_thumb::make_thumbnail($maxw, $maxh, "$document_root$val_campo", $cuadrar);
        # si no se puede redim, tonces la agarra asi no mas.
        if (!$binfoto || !$final_dimx || !$final_dimy) {
            ($final_dimx, $final_dimy) = ($dx, $dy);
            $binfoto = &glib_fildir_02::read_file("$document_root$val_campo");
        };
    }
    else {
        ($final_dimx, $final_dimy) = ($dx, $dy);
        $binfoto = &glib_fildir_02::read_file("$document_root$val_campo");
    };


    my $nom_arch = $this->_guarda_binfoto_prontus($val_campo, $final_dimx, $final_dimy, $binfoto, '');
    return if ($nom_arch eq '');
    $this->_add_foto_prontus_xml($final_dimx, $final_dimy, $nom_arch);


    # Reasigna val_campo al nuevo valor de la nueva foto generada para el articulo.
    $val_campo = "$this->{dst_foto}/$nom_arch";
    $val_campo =~ s/^$document_root//;

    # Guardar en xml y parsear en html la nueva fotofija
    my $parse_as_cdata = 1;
    $this->{xml_data} = &lib_prontus::replace_in_xml($this->{xml_data}, $nom_campo, $val_campo, $parse_as_cdata);

};
# ---------------------------------------------------------------
sub _add_foto_filesystem {
# Recibe como parametro el Path de la imagen sin el document_root

    my ($this, $path_foto) = @_;
    my $cpan_server_name = $this->{cpan_server_name};
    my $document_root = $this->{document_root};
    my $ts = $this->{ts};
    my $prontus_id = $this->{prontus_id};

    return unless($ts =~ /(\d{8})\d{6}/);
    my $fechac = $1;
    my $new_path_foto = "/$prontus_id/site/artic/$fechac/imag/";
    my $nom_foto = $this->_get_nom_foto($new_path_foto, '');
    my $foto_ext = &lib_prontus::get_file_extension($path_foto);

#    print "copiando... $document_root$path_foto  -->  $document_root$new_path_foto$nom_foto.$foto_ext";
    &File::Copy::copy("$document_root$path_foto", "$document_root$new_path_foto$nom_foto.$foto_ext");

    # Obtiene dimensiones actuales de la foto
    my ($msg, $foto_dimx, $foto_dimy) = &lib_prontus::dev_tam_img("$document_root$new_path_foto$nom_foto.$foto_ext");
    unless($foto_dimx && $foto_dimy) {
        print STDERR "\tError dev_tam_img: $msg\n";
        return;
    }
    # Se agrega la imagen al xml
    $this->_add_foto_prontus_xml($foto_dimx, $foto_dimy, "$nom_foto.$foto_ext");
    return "$nom_foto.$foto_ext";
};

# ---------------------------------------------------------------
sub _guarda_binfoto_prontus {
    my ($this, $val_campo, $final_dimx, $final_dimy, $binfoto, $arch_existente) = @_;
    return '' if (!$binfoto || !$final_dimx || !$final_dimy);
    $this->_check_ext_foto($val_campo) || return '';

    my $nom_arch = $this->_get_nom_foto($val_campo, $arch_existente);

    # si es gif , se genera png
    if ($val_campo =~ /\.gif$/i) {
        $nom_arch =~ s/\.gif$/\.png/i;
    };

    # warn "dst_img[$this->{dst_foto}] - nom_arch[$nom_arch]";
    my $dst_binfoto = "$this->{dst_foto}/$nom_arch";
    &lib_thumb::write_image($dst_binfoto, $binfoto);
    &lib_prontus::purge_cache($dst_binfoto);

    return $nom_arch;

};
# ---------------------------------------------------------------
sub _genera_fotofija {
# Recibe como parametro:
# - El nombre de la foto_n. Ej: foto_134520110619122632.jpg
# - El nombre la foto fija (nombre marca marca)
# - El ancho maximo
# - El alto maximo
# - Si se debe cuadrar la imagen o no: si|<anything>

    my ($this, $nom_foto, $fotofija, $maxw, $maxh, $cuadrar) = @_;
    my $cpan_server_name = $this->{cpan_server_name};
    my $document_root = $this->{document_root};
    my $ts = $this->{ts};
    my $prontus_id = $this->{prontus_id};

    $cuadrar = '' unless($cuadrar eq 'si');
    my $path_foto = "/$this->{prontus_id}/site/artic/$this->{fechac}/imag/$nom_foto";

    # Se revisa que la foto exista
    return "La foto no existe $nom_foto: $document_root$path_foto" unless(-f "$document_root$path_foto");

    # Obtiene dimensiones actuales de la foto
    my ($msg, $foto_dimx, $foto_dimy) = &lib_prontus::dev_tam_img("$document_root$path_foto");
    return $msg if($msg);

    # Solo procede si viene ancho o alto
    if (($maxw =~ /^\d+$/) || ($maxh =~ /^\d+$/) || ($foto_dimx =~ /^\d+$/) || ($foto_dimy =~ /^\d+$/)) {

        if ($nom_foto =~ /(foto_\w+)$this->{ts}\.\w+/) {
            # Foto local al articulo
            my $nom_campo_orig = $1;
            print STDERR "$fotofija, $path_foto, $maxw, $maxh, $foto_dimx, $foto_dimy, $cuadrar, $nom_campo_orig\n";
            $this->_add_foto_sitiolocal_articulolocal($fotofija, $path_foto, $maxw, $maxh, $foto_dimx, $foto_dimy, $cuadrar, $nom_campo_orig);
        } else {
            return "Error en regexp: nom_foto[$nom_foto]";
        }
    } else {
        return "Error en las dimensiones: maxw[$maxw], maxh[$maxh], foto_dimx[$foto_dimx], foto_dimy[$foto_dimy]";
    }
    return '';
};
# ---------------------------------------------------------------
sub add_campos_extra {
    # metodo publico a ser invocado desde el guardar para agregar campos especiales
    my ($this) = shift; # ya estan listos _FID Y _PLT Y _USER_ID (ESTE DEBE CONSERVAR EL DEL AUTOR)
    # EL _ALTA TB. DEBE ADAPTARSE
    # IDEM _SOLOPORTADAS
};
# ---------------------------------------------------------------
sub get_xml_content {
# Retorna hash de datos leidos del xml con los nombres de campo en minusculas.
# Si los datos ya estan cargados en el objeto, no lo lee de nuevo.

    my ($this) = shift;
    # print STDERR  "get content[$this->{fullpath_xml}]\n";
    my $num_elem = keys(%{$this->{xml_content}});
    if (!$num_elem) {
        my $buff_xml_data = lib_prontus::get_xml_data($this->{fullpath_xml});
        my %campos_from_xml = lib_prontus::getCamposXml($buff_xml_data);
        $this->{xml_content} = \%campos_from_xml;
    };
    return %{$this->{xml_content}};
};

# ---------------------------------------------------------------
#sub tagsCounting {
## Inserta o actualiza contador de tags en BD.
## Se invoca al momento de guardar un articulo.
#
#    my ($this, $base, $tags_old, $is_new) = @_;
#
#    my $motor_bd = &lib_prontus::get_motor_from_bdhandler($base);
#    my %campos = $this->get_xml_content();
#    my @tags = split(/ *, */, $campos{'_tags'});
#
#    # Deja los 'tags old' como keys de un hash
#    my %tags_old_hash;
#    my @aux = split(/ *, */, $tags_old);
#    foreach my $k (@aux) {
#        $tags_old_hash{$k} = 1;
#    };
#
#    if ($is_new && $campos{'_tags'}) {
#        foreach my $tag (@tags) {
#
#            my $sql = "select TAGS_ID from TAGS where TAGS_TAG = \"$tag\"";
#            my $tags_id = &lib_prontus::existe_registro($sql, $base);
#            if ($tags_id) {
#                $sql = "update TAGS set TAGS_COUNT = (TAGS_COUNT + 1) where TAGS_ID = \"$tags_id\" ";
#            } else {
#                $sql = "insert into TAGS values(NULL, \"$tag\", 1) ";
#            };
#            my $res = $base->do($sql);
#            if (!$res) {
#                $Artic::ERR = "Error actualizando tabla de Tags, ts[$this->{ts}]\n";
#                cluck $Artic::ERR . "sql[$sql][$!]";
#                return 0;
#            };
#        }
#    # si es edicion y vienen tags
#    } elsif (!$is_new && $campos{'_tags'}) {
#        # hay que contabilizarlos solo si no existian ya de antes
#
#        foreach my $tag (@tags) {
#            # si ya existia de antes, lo salta
#            next if (exists $tags_old_hash{$tag});
#
#            my $sql = "select TAGS_ID from TAGS where TAGS_TAG = \"$tag\"";
#            my $tags_id = &lib_prontus::existe_registro($sql, $base);
#            if ($tags_id) {
#                $sql = "update TAGS set TAGS_COUNT = (TAGS_COUNT + 1) where TAGS_ID = \"$tags_id\" ";
#            } else {
#                $sql = "insert into TAGS values(NULL, \"$tag\", 1) ";
#            };
#            my $res = $base->do($sql);
#            if (!$res) {
#                $Artic::ERR = "Error actualizando tabla de Tags, ts[$this->{ts}]\n";
#                cluck $Artic::ERR . "sql[$sql][$!]";
#                return 0;
#            };
#        };
#
#    };
#
#    # solo caso editar: si existian antes y ahora no, hay que decrementarlos
#    if (!$is_new && $tags_old) {
#        # traspasa los nuevos a un hash pa usarlos mas facilmente
#        my %tags_new_hash;
#        foreach my $k (@tags) {
#            $tags_new_hash{$k} = 1;
#        };
#        # recorre los antiguos, viendo si aun estan
#        foreach my $tag (keys %tags_old_hash) {
#
#            # si no existe en los nuevos, lo decrementa
#            if (!exists $tags_new_hash{$tag}) {
#
#                my $sql = "select TAGS_ID from TAGS where TAGS_TAG = \"$tag\"";
#                my $tags_id = &lib_prontus::existe_registro($sql, $base);
#                if ($tags_id) {
#                    $sql = "update TAGS set TAGS_COUNT = (TAGS_COUNT - 1) where TAGS_ID = \"$tags_id\" ";
#                };
#                my $res = $base->do($sql);
#                if (!$res) {
#                    $Artic::ERR = "Error actualizando tabla de Tags, ts[$this->{ts}]\n";
#                    cluck $Artic::ERR . "sql[$sql][$!]";
#                    return 0;
#                };
#            };
#        };
#    };
#
#    return 1;
#
#};

# ---------------------------------------------------------------
sub tags2bd {
# puebla nub de art con tags
# Se invoca al momento de guardar un articulo.

    my ($this, $base, $is_new) = @_;

    my $motor_bd = &lib_prontus::get_motor_from_bdhandler($base);
    my %campos = $this->get_xml_content();
    my @tags = split(/,/, $campos{'_tags'});

    # Primero elimina los tags del artic actual:
    my $sql = "delete from TAGSART where TAGSART_IDART='$this->{ts}'";
    my $res = $base->do($sql);
    if (!$res) {
        $Artic::ERR = "Error actualizando tabla de Tags, ts[$this->{ts}]\n";
        cluck $Artic::ERR . "sql[$sql][$!]";
        return 0;
    };

    # Asocia los TAGS al artic
    foreach my $idtag (@tags) {
        $sql = "insert into TAGSART set TAGSART_IDTAGS='$idtag', TAGSART_IDART='$this->{ts}'";
        my $res = $base->do($sql);
        if (!$res) {
            $Artic::ERR = "Error actualizando tabla de Tags, ts[$this->{ts}]\n";
            cluck $Artic::ERR . "sql[$sql][$!]";
            return 0;
        };
    };

    return 1;
};


# ---------------------------------------------------------------
sub art_update_bd {
# Actualiza art. en base de datos prontus a partir de info del xml


    my ($this, $base) = @_;

    my $motor_bd = &lib_prontus::get_motor_from_bdhandler($base);
    my %campos = $this->get_xml_content();
    %campos = $this->_ajusta_campos_art4bd(\%campos);
    %campos = &lib_prontus::escapea_bd(\%campos, $base);

    my $sql = "select ART_AUTOINC from ART where ART_ID = '$this->{ts}'";
    my $autoinc = &lib_prontus::existe_registro($sql, $base);
    if ($autoinc) {

        $sql = "update ART set ART_AUTOR = $campos{'_autor'},

                ART_IDSECC1 = $campos{'_seccion1'},
                ART_IDTEMAS1 = $campos{'_tema1'},
                ART_IDSUBTEMAS1 = $campos{'_subtema1'},

                ART_IDSECC2 = $campos{'_seccion2'},
                ART_IDTEMAS2 = $campos{'_tema2'},
                ART_IDSUBTEMAS2 = $campos{'_subtema2'},

                ART_IDSECC3 = $campos{'_seccion3'},
                ART_IDTEMAS3 = $campos{'_tema3'},
                ART_IDSUBTEMAS3 = $campos{'_subtema3'},

                ART_TITU = $campos{'_txt_titular'},
                ART_BAJA = $campos{'_txt_bajada'},
                ART_HORAP = $campos{'_horap'},
                ART_TIPOFICHA = $campos{'_fid'},
                ART_ALTA = $campos{'_alta'},
                ART_FECHAPHORAP = $campos{'_fechap_horap'},
                ART_IDUSR = $campos{'_users_id'},
                ART_FECHAP = $campos{'_fechap'},
                ART_FECHAE = $campos{'_fechae'},
                ART_HORAE = $campos{'_horae'},
                ART_SOLOPORTADAS = $campos{'_soloportadas'},
                ART_FECHAEHORAE = $campos{'_fechae_horae'}

                where ART_ID = '$this->{ts}' ";


        my $res = $base->do($sql);
        # print STDERR "$sql\n";
        if (!$res) {
            $Artic::ERR = "Error actualizando tabla de artículos, ts[$this->{ts}] Cod[$DBI::err]\n";
            cluck $Artic::ERR . "sql[$sql][$!][$DBI::errstr]";
            return 0;
        };

    } else {
        $Artic::ERR = "Error actualizando tabla de artículos, no se pudo ubicar autoinc correspondiente al TS[$this->{ts}]\n";
        return 0;
    };

    return $autoinc;

};
# ---------------------------------------------------------------
sub art_insert_bd {
# Crea art. en base de datos prontus a partir de info del xml

    my ($this, $base, $regenerar_registro) = @_; # $regenerar_registro: 1 => sacar autoinc del xml
                                                 # basicamente apara regeneracion de tabla de arts.

    my $motor_bd = &lib_prontus::get_motor_from_bdhandler($base);
    my %campos = $this->get_xml_content();
    my %campos4bd = %campos;
    %campos4bd = $this->_ajusta_campos_art4bd(\%campos4bd);

    %campos4bd = &lib_prontus::escapea_bd(\%campos4bd, $base);

    my $sql_part_fields = " '$this->{ts}',
                        $campos4bd{'_seccion1'},
                        $campos4bd{'_tema1'},
                        $campos4bd{'_subtema1'},

                        $campos4bd{'_seccion2'},
                        $campos4bd{'_tema2'},
                        $campos4bd{'_subtema2'},

                        $campos4bd{'_seccion3'},
                        $campos4bd{'_tema3'},
                        $campos4bd{'_subtema3'},

                        $campos4bd{'_autor'},

                        $campos4bd{'_txt_titular'},
                        $campos4bd{'_txt_bajada'},
                        $campos4bd{'_fechap'},
                        $campos4bd{'_horap'},
                        $campos4bd{'_fechap_horap'},
                        '$this->{fechac}',
                        $campos4bd{'_extension'},
                        $campos4bd{'_fid'},
                        $campos4bd{'_alta'},
                        $campos4bd{'_users_id'},
                        $campos4bd{'_fechae'},
                        $campos4bd{'_horae'},
                        $campos4bd{'_soloportadas'},
                        $campos4bd{'_fechae_horae'} ";

    # Setear autoinc a ser usado en el insert, si corresponde
    my $sql;

    if ($regenerar_registro) {
        if ($campos{'_art_autoinc'} !~ /^\d+$/) {
            $Artic::ERR = "No es posible regenerar registro, artículo TS[$this->{ts}] sin ID autoincremento en XML.\n";
            cluck $Artic::ERR . " $this->{fullpath_xml} ";
            return 0;
        };
        if ($prontus_varglb::MOTOR_BD eq 'MYSQL') {
            my $ret = $base->do("SET INSERT_ID = $campos{'_art_autoinc'}");
            if (! $ret) {
                $Artic::ERR = "Error estableciendo ID = $campos{'_art_autoinc'} en tabla de artículos, TS[$this->{ts}]\n";
                cluck $Artic::ERR . " [$!]  $this->{fullpath_xml} [$DBI::errstr]";
                return 0;
            };
            $sql = "insert into ART values(NULL, $sql_part_fields)";
        } else {
            $sql = "insert into ART values($campos{'_art_autoinc'}, $sql_part_fields)";
        };
    } else {
        $sql = "insert into ART values(NULL, $sql_part_fields)";
    };

    # Realizar el insert

    my $autoinc = &lib_prontus::insert_dev_id($sql, $base, $motor_bd);

    if (!$autoinc) {
        $Artic::ERR = "Error insertando en tabla de artículos, ts[$this->{ts}] Cod[$DBI::err]\n";
        cluck $Artic::ERR . "sql[$sql][$!]  $this->{fullpath_xml} [$DBI::errstr]";
        return 0;
    };

    return $autoinc;

};
# ---------------------------------------------------------------
sub _ajusta_campos_art4bd {
    my ($this) = shift;
    my ($refhash_campos) = shift;
    my %campos = %$refhash_campos;
    $campos{'_autor'} = '' if ($campos{'_autor'} eq '');
    $campos{'_fid'} = '' if ($campos{'_fid'} eq '');
    $campos{'_alta'} = '' if ($campos{'_alta'} eq '');

    $campos{'_users_id'} = '' if ($campos{'_users_id'} eq '');
    $campos{'_soloportadas'} = '' if ($campos{'_soloportadas'} eq '');



    $campos{'_seccion1'} = '0' if ($campos{'_seccion1'} eq '');
    $campos{'_tema1'} = '0' if ($campos{'_tema1'} eq '');
    $campos{'_subtema1'} = '0' if ($campos{'_subtema1'} eq '');
    $campos{'_seccion2'} = '0' if ($campos{'_seccion2'} eq '');
    $campos{'_tema2'} = '0' if ($campos{'_tema2'} eq '');
    $campos{'_subtema2'} = '0' if ($campos{'_subtema2'} eq '');
    $campos{'_seccion3'} = '0' if ($campos{'_seccion3'} eq '');
    $campos{'_tema3'} = '0' if ($campos{'_tema3'} eq '');
    $campos{'_subtema3'} = '0' if ($campos{'_subtema3'} eq '');

    $campos{'_horap'} =~ s/://g;
    $campos{'_horap'} = '0000' if ($campos{'_horap'} eq '');

    $campos{'_horae'} =~ s/://g;
    $campos{'_horae'} = '0000' if ($campos{'_horae'} eq '');

    $campos{'_extension'} = &lib_prontus::get_file_extension($campos{'_plt'});

    # Ajusta bajada
    my $bajada = $campos{'_txt_bajada'};
    if ($bajada eq '') {
        $bajada = $this->{campos}->{'vtxt_cuerpo'};
        $bajada = &lib_prontus::get_minitext_value($bajada);
    };
    $bajada =~ s/\s+$//s;
    $bajada =~ s/^\s+//s;
    $bajada =~ s/ +/ /sg;
    $bajada =~ s/ +$//sg;
    # Ajusta en caso de bajada muy larga, de manera de evitar truncado brusco en la BD

    # convierte a latin1 para poder contar bien los chars
    # utf8::decode($bajada);

    my $largo_bajada = length($bajada);
    # print STDERR "bajada original[$bajada] largo[$largo_bajada]\n";

    if ((length $bajada) < 200) {
        if ( ($bajada !~ /\.$/) && ($bajada ne '') ) {
            $bajada .= '.'; # queda de 200
        };
    } else {
        # $bajada = substr($bajada, 0, 197) . '...';
        $bajada = &lib_prontus::ajusta_nchars($bajada, 200, 1); # ajusta por palabras en modo conteo de bytes
    };
    # restaura a utf8
    # utf8::encode($bajada);
    # print STDERR "bajada ajustada[$bajada]\n";

    $campos{'_txt_bajada'} = $bajada;

    # Ajusta titular
    my $titu = $campos{'_txt_titular'};
    # convierte a latin1 para poder contar bien los chars
    utf8::decode($titu);
    # Ajusta en caso de tiulares muy largos, de manera de evitar truncado brusco en la BD
    if ((length $titu) > 255) {
        $titu = substr($titu, 0, 252) . '...';
    };
    # restaura a utf8
    utf8::encode($titu);
    $campos{'_txt_titular'} = $titu;



    $campos{'_fechap_horap'} = "$campos{'_fechap'}$campos{'_horap'}";
    $campos{'_fechae_horae'} = "$campos{'_fechae'}$campos{'_horae'}";

    return %campos;
};
# ---------------------------------------------------------------
sub generar_vista_art {
# Genera vista html del articulo y graba el archivo.
# Toma como entrada los datos del XML, no los que vengan en el hash $this->{campos}.
    my ($this) = shift;
    my ($mv) = shift;
    my ($stamp_demo) = shift;
    my ($prontus_key) = shift;

    # Carga campos
    my %campos_xml = $this->get_xml_content();
    my $titular_crudo = $campos_xml{'_txt_titular'}; # lo rescata para usos varios
    my ($nom_seccion1, $nom_tema1, $nom_subtema1);
    $nom_seccion1 = $campos_xml{'_nom_seccion1'};
    $nom_tema1 = $campos_xml{'_nom_tema1'};
    $nom_subtema1 = $campos_xml{'_nom_subtema1'};

    # Carga plantilla
    my ($fullpath_plt) = "$this->{pathdir_plt_pags}/$campos_xml{'_plt'}";
    my ($pathdir_plt_macros) = $this->{pathdir_plt_macros};
    my $buffer = &lib_prontus::carga_buffer_plt($fullpath_plt, $pathdir_plt_macros, $mv);

    # Path completo al articulo a generar
    my $fullpath_vista = $this->get_fullpath_artic($mv, $campos_xml{'_plt'});

    if ($buffer) {

        my %claves_adicionales; # que no estan en el xml del artic

        # Recupera marcas externas (desde /xdata)
        %claves_adicionales = $this->get_xdata($buffer);

        # Agrega el TS para los condicionales
        $claves_adicionales{_ts} = $this->{ts};

        # Procesar IFs y NIFs
        $buffer = &lib_prontus::procesa_condicional($buffer, \%campos_xml, \%claves_adicionales);

        # Parsea datos del artic
        $buffer = $this->parse_artic_data($fullpath_vista, $buffer, \%campos_xml, \%claves_adicionales);

        undef %campos_xml;
        undef %claves_adicionales;

        # Stamp demo
        no warnings 'syntax'; # para evitar el msg "\1 better written as $1"
        $buffer =~ s/<title>(.*?)<\/title>/<title>$stamp_demo\1<\/title>/is;

        # tag Generator
        $buffer = &lib_prontus::add_generator_tag($buffer);

        $buffer = &lib_prontus::parser_custom_function($buffer);

        # Borra marcas no sustituidas
        $buffer =~ s/%%.+?%%//g;

        $buffer =~ s/&#37;&#37;/%%/sg; # restituyo los %% escritos por el usuario al interior de los campos

        # aprovecha de rescatar el post_proceso
        if (!$mv) {
            while ($buffer =~ /<!--POST_PROCESO=(.+?)-->/isg) {
                $this->{post_proceso_lista} .= "$1\t";
            };
        };
        $buffer =~ s/<!--POST_PROCESO=.+?-->//isg;

    } else {
        no warnings 'syntax'; # para evitar el msg "\1 better written as $1"
        my $titular = $titular_crudo;
        $titular =~ s/<\!\[CDATA\[(.*?)\]\]>/\1/i;
        $titular = &lib_prontus::saca_tags_rets($titular);

        $Artic::ERR = 'Plantilla de artículo vacia o no existe, el art. ' . $this->{ts} . ' (' . $titular . ") se creó en blanco. plt[$campos_xml{'_plt'}] vista[$mv]\n";
        warn "$Artic::ERR fullpath_plt[$fullpath_plt]";
        return 0;
    };

    # Check dir
    my $fulldir_vista = $this->_get_fulldir_vista($mv);
    my $dir_ret = &glib_fildir_02::check_dir($fulldir_vista);
    if (!$dir_ret) {
        $Artic::ERR = "Error creando directorio para el artículo. TS[$this->{ts}]\n";
        cluck "$Artic::ERR fulldir_vista[$fulldir_vista] $!";
        return 0;
    };

    # Escribe vista del articulo
    # warn "escribiendo[$fullpath_vista]";
    &glib_fildir_02::write_file($fullpath_vista, $buffer);


    # Chequea que se haya podido crear el archivo
    if (!-f $fullpath_vista) {
        $Artic::ERR = "No se pudo crear archivo vista para el artículo. TS[$this->{ts}]\n";
        cluck "$Artic::ERR fullpath_vista[$fullpath_vista] $!";
        return 0;
    };

    # Para la vista pppal,
    if (!$mv) {
        # chequea que el archivo no haya quedado vacio.
        if (!-s $fullpath_vista) {
            $Artic::ERR = "Error escribiendo archivo de la vista principal para el artículo. Quedó de largo cero. Esto puede deberse a problemas de espacio disponible, o bien, a que no se dispone de plantilla de artículo o ésta está vacía. TS[$this->{ts}] PLT[$campos_xml{'_plt'}]\n";
            cluck "$Artic::ERR fullpath_vista[$fullpath_vista] $!";
            return 0;
        };
        # hace purge de la vista, ya sea del path normal o friendly url, dependiendo de como este configurado.
        my $marca_file = $fullpath_vista;
        $marca_file = &lib_prontus::remove_front_string($marca_file, $this->{document_root});
        my $fileurl = '%%_FILEURL%%';
        $fileurl = &lib_prontus::parse_filef($fileurl, $titular_crudo, $this->{ts}, $this->{prontus_id}, $marca_file, $nom_seccion1, $nom_tema1, $nom_subtema1);

        &lib_prontus::purge_cache($fileurl);
    };

    return 1;

};



# ---------------------------------------------------------------
sub parse_artic_data {
# parsea todas las marcas del xml mas algunas derivadas de estas.
    my $this = shift;
    my $fullpath_vista = shift; # se requiere minimo el relativo, si es el abs, se despulga
    my $buffer = shift;
    my $ref_campos_xml = shift;
    my $vars_adicionales = shift;

    my %campos_xml = %$ref_campos_xml;
    undef $ref_campos_xml;

    # Obtiene nom de secc, tema y subtema en vista correspondiente
    if ($fullpath_vista =~ /\/pags\-(\w+)\/[0-9]{14}\.\w+$/) {
        my $mv = $1;
        ($campos_xml{'_nom_seccion1'}, $campos_xml{'_nom_tema1'}, $campos_xml{'_nom_subtema1'})
            = &lib_prontus::get_nom4vistas($mv, $campos_xml{'_seccion1'}, $campos_xml{'_tema1'}, $campos_xml{'_subtema1'});
    } else {
        # Obtiene nom de secc, tema y subtema vista principal.
        ($campos_xml{'_nom_seccion1'}, $campos_xml{'_nom_tema1'}, $campos_xml{'_nom_subtema1'})
            = &lib_prontus::get_nom4vistas('', $campos_xml{'_seccion1'}, $campos_xml{'_tema1'}, $campos_xml{'_subtema1'});
    };

    # Agrega algunas vars adicionales que no vienen en el XML.
    # Es posible que estas sobreescriban las del XML
    if (ref $vars_adicionales) {
        foreach my $k (keys %$vars_adicionales) {
            $campos_xml{lc $k} = $$vars_adicionales{$k};
        };
        undef $vars_adicionales;
    };

    # Parsea campos
    foreach my $nom_campo (keys %campos_xml) {
        my $val_campo = $campos_xml{$nom_campo};
        next if ($val_campo eq '');
        next if ($nom_campo =~ /^_fecha(p|e)$/);
        next if ($nom_campo =~ /^chk_cuadrar_fotofija|^_NOMfoto_|^_wfoto_|^_hfoto_|^foto_\d+/);

        if ($nom_campo =~ /^vtxt_/i) {
            # warn "[$nom_campo][$val_campo]";
            $buffer = $this->_parsing_vtxt($buffer, $nom_campo, $val_campo);

        } elsif ($nom_campo =~ /^asocfile_|^swf_|^multimedia_/i) {
            $buffer = $this->_parsing_recursos($nom_campo, $val_campo, $buffer);

        } elsif ($nom_campo =~ /^fotofija_/i) {
            $buffer = $this->_parsing_fotos($nom_campo, $val_campo, $buffer);

        } else {
            # Replace en artic, incluye minitext
            $buffer = &lib_prontus::replace_in_artic($val_campo, $nom_campo, $buffer);
        };
    };



    # Parseos especiales para fechas y horas
    $buffer = &lib_prontus::artic_parser_fechas($buffer, $campos_xml{'_fechap'}, $campos_xml{'_fechae'});


    # Replace en artic el UTC de publicacion
    my $fechap_horap_iso = $campos_xml{'_fechap'} . &lib_prontus::get_hora_iso($campos_xml{'_horap'});
    my $utc_pub = &lib_prontus::get_dtime_rfc822($fechap_horap_iso);
    $buffer = &lib_prontus::replace_in_artic($utc_pub, '_utcp', $buffer);

    # Reemplaza TS, FECHAC, FECHACLONG, FECHACSHRT
    $buffer = &lib_prontus::replace_tsdata($buffer, $this->{ts});

    # Marca _FILE y _FILEURL
    my $marca_file = $fullpath_vista;
    $marca_file = &lib_prontus::remove_front_string($marca_file, $this->{document_root});
    $buffer =~ s/%%_FILE%%/$marca_file/ig;
    $buffer = &lib_prontus::parse_filef($buffer, $campos_xml{'_txt_titular'}, $this->{ts}, $this->{prontus_id}, $marca_file, $campos_xml{'_nom_seccion1'}, $campos_xml{'_nom_tema1'}, $campos_xml{'_nom_subtema1'});

    # Reemplazar nombre del prontus y server name
    $buffer = &lib_prontus::parse_globals($buffer, '', $this->{public_server_name}, $this->{prontus_id});

    $buffer = &lib_prontus::parse_includes($this->{document_root}, $buffer);

    return $buffer;
};
# ---------------------------------------------------------------
sub get_xdata {
# Obtiene hash con las marcas externas (y su contenido) desde el directorio /<prontus_id>/xdata
# No permite marcas q comiencen con _ para evitar conflictos con las reservadas.
# Las marcas que se carguen por esta via sobreescribiran las marcas del articulo.
# Estructura del dir:
# <prontus_id>/
#     xdata/
#        <sistema_externo>/
#           <nom_marca_grl1>.txt
#           ...
#           <nom_marca_grlN>.txt
#           <ts>/
#               <nom_marca1>.txt
#               ...
#               <nom_marcaN>.txt

    my ($this) = shift;
    my ($buffer) = shift;
    my (%xdata, $nom_marca, $valor_marca);
    my %globalxdata;

    my ($pathdir_xdata) = "$this->{document_root}/$this->{prontus_id}/xdata";
    return %xdata if (!-d $pathdir_xdata);

    my @lisdir = &glib_fildir_02::lee_dir($pathdir_xdata);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

    foreach my $sist_externo (@lisdir) {
        next if (!-d "$pathdir_xdata/$sist_externo"); # solo lee directorios

        # Detecta marcas comunes a todos los articulos
        if(%prontus_varglb::globalxdata) {
            # Utiliza cache de las marcas comunes
            %xdata = %prontus_varglb::globalxdata;
        } else {
            # Si no está cacheado, lee el directorio y busca las marcas
            my @lisdirext = &glib_fildir_02::lee_dir("$pathdir_xdata/$sist_externo");
            @lisdirext = grep !/^\./, @lisdirext; # Elimina directorios . y ..
            foreach my $k (@lisdirext) {
                if ((-f "$pathdir_xdata/$sist_externo/$k") && ($k =~ /^(\w+)\.txt$/i)) {
                    $nom_marca = $1;
                    next if ($nom_marca =~ /^_/); # descarta las q comienzan con _
                    $valor_marca = &glib_fildir_02::read_file("$pathdir_xdata/$sist_externo/$k");
                    $xdata{$nom_marca} = $valor_marca;
                };
            };
            %prontus_varglb::globalxdata = %xdata;
        };

        # Detecta marcas especificas para este articulo
        my $fechac = $this->{fechac};
        my $path = '';
        if (-d "$pathdir_xdata/$sist_externo/$this->{ts}") {
            $path = "$pathdir_xdata/$sist_externo/$this->{ts}";

        } elsif (-d "$pathdir_xdata/$sist_externo/$fechac/$this->{ts}") {
            $path = "$pathdir_xdata/$sist_externo/$fechac/$this->{ts}";
        };
        if($path) {
            my @lisdir_ts = &glib_fildir_02::lee_dir($path);
            @lisdir_ts = grep !/^\./, @lisdir_ts; # Elimina directorios . y ..
            foreach my $marca (@lisdir_ts) {
                next if ($marca =~ /^_/); # descarta las q comienzan con _
                if ((-f "$path/$marca") && ($marca =~ /^(\w+)\.txt$/i)) {
                    $nom_marca = $1;
                    $valor_marca = &glib_fildir_02::read_file("$path/$marca");
                    $xdata{$nom_marca} = $valor_marca;
                };
            };
        };
    };

    return %xdata;

};
# ---------------------------------------------------------------
sub _parsing_recursos {
# Parsea en vista del artic los recursos de un cierto tipo asociados al mismo

    my ($this) = shift;
    my ($nom_campo) = shift; # SWF_xx, ASOCFILE_xx, MULTIMEDIA_xx, SWF_xx
    my ($val_campo) = shift;
    my ($buffer) = shift;
    my ($dst_dir);
    return if ($nom_campo !~ /^(swf|asocfile|multimedia)_/);
    my $type = $1;
    $dst_dir = $this->{'dst_' . $type};

    my ($path) = "$dst_dir/$val_campo";
    # return 0 if (!-f $path);
    if (!-f $path) {
        print STDERR "[$this->{ts}] Archivo no existe [$path]\n";
        $buffer =~ s/%%_S$nom_campo%%/0/isg;
        $buffer =~ s/%%$nom_campo%%/$nom_campo\[$val_campo\]FILE_NOT_FOUND/isg;
        $buffer =~ s/%%_E$nom_campo%%//isg;
        return $buffer;
    };

    # Parsea el size.
    my $bytes = -s $path;
    $bytes = &lib_prontus::bytes2kb($bytes, 0);
    $buffer =~ s/%%_S$nom_campo%%/$bytes/isg;

    # Parsea el recurso como tal
    $path = &lib_prontus::remove_front_string($path, $this->{document_root});
    $buffer =~ s/%%$nom_campo%%/$path/isg;

    # Parsear la extension del archivo
    my $ext = &lib_prontus::get_file_extension($val_campo);
    $buffer =~ s/%%_E$nom_campo%%/$ext/isg;

    return $buffer;
};

# ---------------------------------------------------------------
sub _parsing_fotos {
# Parseo de fotos fijas

    my ($this) = shift;
    my ($nom_campo) = shift; # FOTOFIJA_xx,
    my ($val_campo) = shift;
    my ($buffer) = shift;
    my ($msg, $foto_dimx, $foto_dimy);
    my %campos = $this->get_xml_content();

    #~ return $buffer unless(index($buffer, $nom_campo) > -1);
    $buffer =~ s/%%$nom_campo%%/$val_campo/isg;
    #~ $buffer = &lib_prontus::replace_in_artic($val_campo, $nom_campo, $buffer);

    my $este_prontus = "/$this->{prontus_id}/site/artic";
    if ($val_campo =~ /$este_prontus/i) { # val_campo es del tipo: /prontus_dev/site/artic/20060410/imag/FOTO_0120060410165548.jpg
        my $ts = $this->{ts};
        # parseo ademas las dimensiones de la foto en el articulo
        if ($val_campo =~ /(foto_\d+)$ts\.\w+$/i) {
            my $nom_foto_original = lc $1;
            $foto_dimx = $campos{"_w$nom_foto_original"};
            $foto_dimy = $campos{"_h$nom_foto_original"};
        };
        $buffer =~ s/%%_W$nom_campo%%/$foto_dimx/ig;
        $buffer =~ s/%%_H$nom_campo%%/$foto_dimy/ig;
    }
    elsif ($val_campo =~ /https?:\/\//i) { # url externa
#        foreach my $k (keys %campos) {
#            next if ($k !~ /fotofija/i);
#            warn "k[$k] val[$campos{$k}]";
#        };
        # parseo dimensiones
        $foto_dimx = $campos{"_w$nom_campo"}; # _wfotofija_art200
        # warn "foto externa nom_campo[$nom_campo] nom_campo_w[_w$nom_campo] foto_dimx[$foto_dimx]";
        $buffer =~ s/%%_W$nom_campo%%/$foto_dimx/ig;

        $foto_dimy = $campos{"_h$nom_campo"};
        $buffer =~ s/%%_H$nom_campo%%/$foto_dimy/ig;
    };
    return $buffer;
};

# ---------------------------------------------------------------
sub _parsing_vtxt {
    my $this = shift;
    my $buffer = shift;
    my $nom_campo = shift;
    my $val_campo = shift;

#    my $refhash_subtits = shift;
#    my %hash_subtits = %$refhash_subtits;

    return $buffer if($buffer !~ /%%$nom_campo/i);

    my ($looptit, $tithtml) = $this->_get_data4subtit($buffer, $nom_campo);
    my $curr_nrotit = '0';
    my %hash_subtits;


    # Saca el server name.
    $val_campo =~ s/https?:\/\/$this->{cpan_server_name}//isg;
    $val_campo =~ s/https?:\/\/$this->{public_server_name}//isg;

    $val_campo =~ s/^[ \s]+//isg;
    $val_campo =~ s/^(&nbsp;)+//isg;

    $val_campo =~ s/[ \s]+$//isg;
    $val_campo =~ s/(&nbsp;)+$//isg;

    # Corrige issue ffox 3.6.11, elimina las rutas relativas, ppalmente de las imagenes.
    # Da por sentado que si encuentra alguna ruta relativa, al sacarle los puntos quedara absoluta
    # Esto siempre sera true para imagenes prontus
    if ($val_campo =~ /src *= *("|')\.\.\//i) {
        no warnings 'syntax'; # para evitar el msg "\2 better written as $2"
        $val_campo =~ s/src *= *("|')(\.\.\/)+(\w)/src=\1\/\3/ig;
    } elsif ($val_campo =~ /src *= *("|')\w+?\//i) {
        no warnings 'syntax'; # para evitar el msg "\2 better written as $2"
        $val_campo =~ s/(src) *= *("|')(\w+?)\//\1=\2\/\3\//ig;
    };

    my $vtxt_aux = $val_campo;

    # Elimina funcion q resetea tam. de imagenes en el vtxt.
    $vtxt_aux =~ s/ondblclick *= *".+?"//isg;

    # Parsea los subtits en el vtxt
    my $vtxt_aux_consubtit = $vtxt_aux;
    while ($vtxt_aux =~ /(<[^<>]*? class=["']?subtit(\d?)["']?[ >][^<]*?<\/\w+?>)/isg) {
        my $tag = $1;
        my $level_subtit = $2;
        my $tit = $tag;
        $tit =~ s/<.*?>//sg;
        next if ($tit !~ /\w/);
        if ($tithtml) {
            # Usa mini tpl si es q esta en la plantilla del art.
            my $tithtml_aux = $tithtml;
            $tithtml_aux =~ s/%%_SUBTIT%%/$tit/i;
            $tithtml_aux =~ s/%%_SUBTIT_ANAME%%/$nom_campo\_T$curr_nrotit/i;
            $tithtml_aux =~ s/%%_level_subtit%%/$level_subtit/ig;
            $vtxt_aux_consubtit =~ s/\Q$tag\E/$tithtml_aux/is;
        }
        else {
            $vtxt_aux_consubtit =~ s/\Q$tag\E/<a name="$nom_campo\_T$curr_nrotit">$tag<\/a>/is;
        };

        # Guarda item a incluir en el menu
        my $looptit_aux = $looptit;
        $looptit_aux =~ s/%%_SUBTIT_KEY%%/#$nom_campo\_T$curr_nrotit/ig;
        $looptit_aux =~ s/%%_SUBTIT%%/$tit/ig;
        $looptit_aux =~ s/%%_level_subtit%%/$level_subtit/ig;
        $hash_subtits{$curr_nrotit} = '<!--STIT_' . $nom_campo . '-->' . $looptit_aux . '<!--/STIT_' . $nom_campo . '-->'; # acumula item para ponerlo despues en el menu
        $curr_nrotit++;
    };

    no warnings 'syntax'; # para evitar el msg "\1 better written as $1"
    foreach my $st (sort{$a <=> $b}(keys %hash_subtits)) {
        # print STDERR "st[$st]\n";
        my $item_menu = $hash_subtits{$st};
        # Reemplazar en la pagina misma.
        $buffer =~ s/%%_SUBTIT_LOOP_$nom_campo%%(.*?)%%\/_SUBTIT_LOOP_$nom_campo%%/$item_menu%%_SUBTIT_LOOP_$nom_campo%%\1%%\/_SUBTIT_LOOP_$nom_campo%%/is;
    };
    # Eliminar TITLOOP sobrante.
    $buffer =~ s/%%_SUBTIT_LOOP_$nom_campo%%(.*?)%%\/_SUBTIT_LOOP_$nom_campo%%//isg;
    # Eliminar BLOQUE %%TITHTML%% sobrante
    $buffer =~ s/%%_SUBTIT_HTML_$nom_campo%%(.*?)%%\/_SUBTIT_HTML_$nom_campo%%//isg;

    # Detectar si el VTXT esta insertando invocaciones a funciones js derivadas del uso del boton media.
    # Si las encuentra, incluye el JS necesario.

    # Incluir solo si se esta invocando a alguna de las funciones del boton media.
    if ($val_campo =~ /<script type="text\/javascript">write(Flash|ShockWave|Embed|QuickTime|RealMedia|WindowsMedia)\(\{/) {
        my $pathJs = $this->{document_root} . "/$this->{prontus_id}" . '/cpan/core/fid/vtxt_embed_media.js';
        my $bufferJs = &glib_fildir_02::read_file($pathJs);
        my $codeJs4Media = "<script type=\"text/javascript\">$bufferJs</script>";
        # Incluir el js siempre que no haya sido incluido antes, para otro vtxt
        if ($buffer !~ /\Q$codeJs4Media\E/) {
            $vtxt_aux_consubtit = "\n\n$codeJs4Media\n" . $vtxt_aux_consubtit; # lo incluye ANTES de su posible invocacion
        };
    };



    $buffer = &lib_prontus::replace_in_artic($vtxt_aux_consubtit, $nom_campo, $buffer);
    return $buffer;
    # return ($vtxt_aux_consubtit, $curr_nrotit, %hash_subtits);
};
# --------------------------------------------------------------------
sub _get_data4subtit {
    my $this = shift;
    my $buffer = shift;
    my $nom_campo = shift;

    # Obtencion de template de indice de titulos
    my ($looptit, $tithtml);

    # La cosa es sin framesets, o sea el indice va en la pagina misma.
    $buffer =~ /%%_SUBTIT_LOOP_$nom_campo%%(.*?)%%\/_SUBTIT_LOOP_$nom_campo%%/is;
    $looptit = $1; # segmento html que se repite para cada titulo.

    # Plantilla para los subtitulos
    if ($buffer =~ /%%_SUBTIT_HTML_$nom_campo%%(.+?)%%\/_SUBTIT_HTML_$nom_campo%%/is) {
        $tithtml = $1;
    };

    return ($looptit, $tithtml);

};

# --------------------------------------------------------------------
sub setear_autoinc {
# Agrega autoinc obtenido al xml del articulo.
    my ($this) = shift;
    my ($autoinc) = shift;

    my $buffer = &glib_fildir_02::read_file($this->{fullpath_xml});
    $buffer =~ s/<_art_autoinc>.*?<\/_art_autoinc>/<_art_autoinc>$autoinc<\/_art_autoinc>/is;
    &glib_fildir_02::write_file($this->{fullpath_xml}, $buffer);

};


# ---------------------------------------------------------------
return 1;

# Para desplegar la doc. desde linea de comandos:
# perldoc Artic.pm
# Para generar la doc en html:
# perldoc -T -o html Artic.pm > Artic.pm.html

__END__

=head1 NAME

B<Artic.pm> - Clase para manipulacion de articulos Prontus, por medio de la creacion de un objeto tipo "Artic"

=for comment

=head1 DESCRIPTION

Esta clase contiene operaciones tipicas a realizar con los artículos, como por ejemplo leer su XML,
obtener el path de este, generar el html, parsear sus datos, etc., sin necesidad de conocer la logica
interna, solo basta instanciar correctamente el objeto de tipo 'Artic'. Esta clase se utiliza en todas
las partes de Prontus en donde se manipulan los articulos.
Ademas de ser util internamente para las CGIs de prontus, tambien puede servir para simplificar
la programacion de post-procesos, scripts de migracion de contenidos, etc., utilizando los metodos
publicos y atributos de la clase.

=for comment

=head1 SYNOPSIS

Instanciar y acceder a un metodo publico:

    use Artic;

    # Creacion del objeto Artic.

OPCION 1: utilizando variables globales prontus ($prontus_varglb::NOM_VARIABLE).
Esta es la opción más segura y recomendada, pero requiere cargar la conf de prontus primero,
de la sgte. forma:

    # Path conf y load config de prontus
    use prontus_varglb; &prontus_varglb::init();
    use lib_prontus;
    my $prontus_id = 'prontus_noticias';
    my $path_conf = "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);

    # Creacion de obj Artic usando variables globales Prontus
    my $artic_obj = Artic->new(
                    'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                    'public_server_name'=> $prontus_varglb::PUBLIC_SERVER_NAME,
                    'cpan_server_name'  => $prontus_varglb::IP_SERVER,
                    'document_root'     => $prontus_varglb::DIR_SERVER,
                    'ts'                => $ts,
                    'campos'=>{})
                    || die("Error inicializando objeto articulo: $Artic::ERR TS[$ts]\n");

OPCION 2: Creacion de obj Artic sin usar var. globales Prontus

    # Creacion del obj Artic, sin var Prontus
    my $artic_obj = Artic->new(
                    'prontus_id'        => 'prontus_noticias',
                    'public_server_name'=> 'www.misitio.cl',
                    'cpan_server_name'  => 'prontus.misitio.cl',
                    'document_root'     => '/sites/misitio/web',
                    'ts'                => '20081023172849',
                    # ********** Ver Nota (1) ************
                    'campos'=>{})
                    # ********** Ver Nota (2) ************
                    || die("Error inicializando objeto articulo: $Artic::ERR TS[$ts]\n");

Ejemplo de utilizacion de metodos del obj Artic

    # Generar vista o html del articulo.
    $artic_obj->generar_vista_art($mv, '', $prontus_varglb::PRONTUS_KEY)
                || die("Error: $Artic::ERR");

    # carga hash con campos del XML del articulo, con nombre_campo => valor_campo
    my %campos_xml = $artic_obj->get_xml_content();


Nota (1):
El atributo 'campos' en el constructor es para poder pasarle un hash con todos los datos
necesarios para poder crear un articulo. Para el caso de que solo se necesite LEER info del articulo,
basta con dejarlo de la forma indicada en el ejemplo.

Nota (2):
Si se trata del procesamiento de un solo articulo, generalmente el die() sera suficiente.
pero en caso de que estemos procesando varios articulos dentro de un bucle, en donde se desea que
aunque uno falle, se continue con el resto, en vez de die() se puede realizar algo como lo siguiente:

    foreach my $ts (@arr_artic) {
        # Creacion del objeto Artic.
        my $artic_obj = Artic->new(...)
                        || print("Error inicializando objeto articulo: $Artic::ERR TS[$ts]\n");

        # En la instruccion siguiente al constructor, revisamos si se creo el objeto y en caso negativo
        # hacemos un next al siguiente articulo
        next if (!ref($artic_obj));

        # Si el artic se instancio OK, realizo el resto de las operaciones, por ejemplo,
        # reparsearlo en todas las vistas a partir de los datos del XML:
        # Para la vista ppal:
        $artic_obj->generar_vista_art('', '', $prontus_varglb::PRONTUS_KEY) || print $Artic::ERR;

        # Para vistas secundarias, agregar:
        foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
            $artic_obj->generar_vista_art($mv, '', $prontus_varglb::PRONTUS_KEY) || print $Artic::ERR;
        };

    };

=for comment
# ---------------------------------------------------------------

=head2 CONSTRUCTOR

=over 8

=item B<new()>

Devuelve un nuevo objeto Artic. Los parametros son los indicados en la sinopsis.
Es importante considerar que los campos pasados en el hash 'campos' al constructor deben tener
los nombres correspondientes a los campos del XML del artic.
para un ejemplo sobre como pasar pasarle este hash al objeto a fin de ingresar un nuevo articulo,
revisar la lib_artic.pm

=back

=for comment
# ---------------------------------------------------------------

=head2 VARIABLES DE CLASE ESTATICAS

=over 8

=item C<$Artic::XML_BASE>

Contiene el XML matriz de los articulos prontus:

    <?xml version='1.0' encoding='UTF-8'?>
    <artic_data>
    <_private>
    <_txt_titular>
    </_txt_titular>
    <_art_autoinc></_art_autoinc>
    <_users_id></_users_id>
    <_fid></_fid>
    <_plt></_plt>
    <_fechap></_fechap>
    <_horap></_horap>
    <_fechae></_fechae>
    <_horae></_horae>
    <_soloportadas></_soloportadas>
    <_seccion1></_seccion1>
    <_tema1></_tema1>
    <_subtema1></_subtema1>
    <_seccion2></_seccion2>
    <_tema2></_tema2>
    <_subtema2></_subtema2>
    <_seccion3></_seccion3>
    <_tema3></_tema3>
    <_subtema3></_subtema3>
    <_nom_seccion1></_nom_seccion1>
    <_nom_tema1></_nom_tema1>
    <_nom_subtema1></_nom_subtema1>
    <_nom_seccion2></_nom_seccion2>
    <_nom_tema2></_nom_tema2>
    <_nom_subtema2></_nom_subtema2>
    <_nom_seccion3></_nom_seccion3>
    <_nom_tema3></_nom_tema3>
    <_nom_subtema3></_nom_subtema3>
    <_autor></_autor>
    <_txt_bajada></_txt_bajada>
    <_alta></_alta>
    <_tax></_tax>
    <_tags></_tags>
    </_private>

    <_public>
    </_public>
    </artic_data>


=item C<$Artic::ERR>

Variable que se carga con el texto descriptivo del error en caso de que un metodo retorne 0.
Este texto esta adecuado para ser presentado directamente al usuario, ya que el texto completo
del error, incluyendo paths y backtrace es enviado al STDERR.

=back

=for comment
# ---------------------------------------------------------------

=head2 ATRIBUTOS

Luego de creado el objeto, se puede acceder a una serie de atributos con informacion del articulo.
Estos atributos se acceden de la forma:

    my $attr = $artic_obj->{nombre_atributo};

Los atributos son:

B<ts>:

    timestamp del articulo, por ejemplo '20081023172849'

B<fechac>:

    string correspondiente a la fecha de creacion del artic,
    por ejemplo '20081023'

B<fullpath_xml>:

    path completo al XML del articulo.
    por ejemplo: '/sites/misitio.cl/web/prontus_noticias/site/artic/20081023/xml/20081023172849.xml'

B<prontus_id>:

    nombre del publicador al que pertenece el articulo,
    por ejemplo 'prontus_noticias'

B<public_server_name>:

    nombre del servidor donde estara publicado el articulo,
    por ejemplo 'www.misitio.cl'

B<cpan_server_name>:

    nombre del servidor desde donde se publicara el articulo,
    usualmente es el mismo que public_server_name, aunque
    podrian diferir en caso de que por ejemplo hayan clusters

B<document_root>:

    document root asociado al server del articulo,
    por ejemplo '/sites/misitio/web'

B<campos>:

    Hash con todos los campos pasados al constructor.
    Para acceder a alguno en particular:
    my $plt = $artic_obj->{campos}->{'_plt'};

B<dst_base>:

    path completo del directorio donde se ubican los archivos del articulo,
    por ejemplo: '/sites/misitio.cl/web/prontus_noticias/site/artic/20081023'

B<dst_pags>:

    path completo del directorio donde se ubica el html del articulo,
    por ejemplo: '/sites/misitio.cl/web/prontus_noticias/site/artic/20081023/pags'

B<dst_xml>:

    path completo del directorio donde se ubica el xml del articulo,
    por ejemplo: '/sites/misitio.cl/web/prontus_noticias/site/artic/20081023/xml'

B<dst_asocfile>:

    path completo del directorio donde se ubican los asocfile del articulo,
    por ejemplo: '/sites/misitio.cl/web/prontus_noticias/site/artic/20081023/asocfile/20081023172849'

B<dst_foto>:

    path completo del directorio donde se ubican las imag del articulo,
    por ejemplo: '/sites/misitio.cl/web/prontus_noticias/site/artic/20081023/imag'

B<dst_swf>:

    path completo del directorio donde se ubican los swf del articulo,
    por ejemplo: '/sites/misitio.cl/web/prontus_noticias/site/artic/20081023/swf'

B<dst_multimedia>:

    path completo del directorio donde se ubican los mmedia del articulo,
    por ejemplo: '/sites/misitio.cl/web/prontus_noticias/site/artic/20081023/mmedia'

B<lnk_multimedia>:

    path relativo al doc. root del directorio donde se ubican los mmedia del articulo,
    por ejemplo: '/prontus_noticias/site/artic/20081023/mmedia'

B<pathdir_plt>:

    path completo del directorio donde se ubican las plantillas de articulo,
    por ejemplo: '/sites/misitio.cl/web/prontus_noticias/plantillas/artic/fecha'

B<pathdir_plt_macros>:

    path completo del directorio donde se ubican las macros de articulo,
    por ejemplo: '/sites/misitio.cl/web/prontus_noticias/plantillas/artic/fecha/macros'

B<pathdir_plt_pags>:

    path completo del directorio donde se ubican las plantillas de la vista default de articulo,
    por ejemplo: '/sites/misitio.cl/web/prontus_noticias/plantillas/artic/fecha/pags'



=for comment
# ---------------------------------------------------------------

=head2 METODOS PUBLICOS

=for comment
# ---------------------------------------------------------------

=over 8

=item B<generar_vista_art($mv,$stamp_demo,$prontus_key)>

Genera HTML (o lo que corresponda a la plantilla) del articulo y graba el archivo.

Toma como entrada los datos del XML, no los que vengan en el hash $this->{campos}.

B<Parametros>:

$mv

  nombre de la vista en la que se desea generar el html articulo.
  para la vista default, poner ''. Para otras vistas poner por ejemplo: 'pda'

$stamp_demo

  deprecated: marca a incluir indicando que la PK no es valida. En general, si se sabe que
  el sitio ya posee una pK valida, este parametro se puede dejar como ''.

$prontus_key

  prontus key del sitio. Esto se requiere para poder incluirla como comentario HTML

B<Retorna>:

1 | 0 (exito o error).
En caso de error, ademas setea la variable de clase $Artic::ERR con el texto correspondiente.


=for comment
# ---------------------------------------------------------------

=item B<get_fullpath_artic($mv, $plt)>

Obtiene el path completo al html del artic., por ejemplo:
'/sites/misitio.cl/web/prontus_noticias/site/artic/20081023/pags/20081023172849.html'

B<Parametros>:

$mv

  nombre de la vista en la que se desea generar el html articulo.
  para la vista default, poner ''. Para otras vistas poner
  por ejemplo: 'pda'

$plt

  nombre del archivo de plantilla de artic.
  Puede obtenerse de los campos recibidos del form, o bien,
  desde el xml, invocando antes a get_xml_content()

B<Retorna>:

El path completo al html del artic., por ejemplo:
'/sites/misitio.cl/web/prontus_noticias/site/artic/20081023/pags/20081023172849.html'

=for comment
# ---------------------------------------------------------------

=item B<get_xml_content()>

Obtiene un hash con los campos del XML del artic.
Cada entrada es del tipo nom_campo => valor_campo
Ya vienen eliminados los bloques CDATA, en caso de haberlos.

Uso tipico:

  my %campos_xml = $artic_obj->get_xml_content();

B<Retorna>:

Hash con los campos del XML del artic.

=for comment
# ---------------------------------------------------------------

=item B<parse_artic_data($fullpath_artic, $buffer, \%campos_xml, \%claves_adicionales)>

Parsea todas las marcas del XML mas algunas derivadas de estas en el buffer dado.
Este metodo NO elimina las marcas que queden sin sustituir.

Uso tipico:

  my $fullpath_artic = $artic_obj->get_fullpath_artic($mv, $campos_xml{'_plt'});
  $buffer = $artic_obj->parse_artic_data($fullpath_artic, $buffer, \%campos_xml, \%claves_adicionales);

B<Parametros>:

$fullpath_artic

  path completo del html del articulo. Se puede obtener facilmente asi:

  my $fullpath_artic = $artic_obj->get_fullpath_artic($mv, $campos_xml{'_plt'});

$buffer

  string, normalmente html, en donde se deben parsear los datos del articulo

\%campos_xml

  Hash con los campos del XML.
  Si el articulo ya existe, este dato se obtiene facilmente asi:
  my %campos_xml = $artic_obj->get_xml_content();

\%campos_adicionales

  Hash con campos custom que se deseen parsear en el buffer.


B<Retorna>:

String con buffer parseado

=for comment
# ---------------------------------------------------------------

=item B<get_nom_artic($plt)>

Obtiene el nombre del archivo del articulo, por ejemplo:
'20081023172849.html'

B<Parametros>:

$plt

  nombre del archivo de plantilla de artic.
  Puede obtenerse de los campos recibidos del form, o bien,
  desde el xml, invocando antes a get_xml_content():

  my %campos_xml = $artic_obj->get_xml_content();
  my $plt = $campos_xml{'_plt'};

  o bien,desde el mismo hash de campos pasado al constructor:

  my $plt = $artic_obj->{campos}->{'_plt'};

B<Retorna>:

El path completo al html del artic., por ejemplo:
'/sites/misitio.cl/web/prontus_noticias/site/artic/20081023/pags/20081023172849.html'


=for comment
# ---------------------------------------------------------------

=item B<art_insert_bd($base, $regenerar_registro)>

Crea art. en base de datos prontus a partir de info del xml.

Uso tipico:

  # Conectar a BD Prontus
  my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
  $regenerar_registro = 1;
  $autoinc = $ARTIC_OBJ->art_insert_bd($base, $regenerar_registro);

  my ($this, $base, $regenerar_registro) = @_; # $regenerar_registro: 1 => sacar autoinc del xml
                                                 # basicamente apara regeneracion de tabla de arts.

B<Parametros>:

$base

  handler de la BD Prontus

$regenerar_registro

  booleano 1 o 0. 1 implica sacar el autoinc del xml y usar ese. Si es 0, implica asignar uno nuevo.
  Este parametro es util setearlo en 1 para regeneracion de tabla de articulos.

B<Retorna>:

Id autoincremento del articulo.

=for comment
# ---------------------------------------------------------------

=item B<Otros metodos utiles>

Revisar codigo fuente para mas detalles.

B<exec_post_proceso_art()>

B<art_update_bd()>

B<setear_autoinc()>

B<tags2bd()>

B<get_xdata()>

B<set_preview_artic()>

=for comment
# ---------------------------------------------------------------

=back

=head1 AUTHOR

Yerko Chapanoff, E<lt>yerko@altavoz.netE<gt>

=cut
