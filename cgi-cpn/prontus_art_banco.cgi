#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO .
# -----------
# Desplegar las fotos faltantes del banco de imagenes
#
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# No registra.
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# macro_banco_imagenes.html
#
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use strict;
use prontus_varglb; &prontus_varglb::init();
use glib_fildir_02;
use glib_cgi_04;
use lib_prontus;

my %FORM;
my $DIR_FECHA;
# ---------------------------------------------------------------
# MAIN.
# -------------

main: {
    # Rescatar parametros recibidos.
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    $FORM{'_ts'} = &glib_cgi_04::param('_ts');
    $FORM{'_all'} = &glib_cgi_04::param('_all');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    print "Cache-Control: no-cache\n";
    print "Cache-Control: max-age=0\n";
    print "Cache-Control: no-store\n";
    print "Content-Type: text/html\n\n";

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);
    if ($prontus_varglb::USERS_ID eq '') {
        print 'Error de sesi�n. Ud no tiene permisos para revisar estas im&aacute;genes';
        exit;
    };

    # Se chequea el TS del articulo
    if ($FORM{'_ts'} =~ /^(\d{8})\d{6}$/) {
        $DIR_FECHA = $1;
    } else {
        print 'El TS del articulo no es valido';
        exit;
    };

    # Cargar xml del articulo.
    my $xml_data = &get_xml_data();

    my $base_path = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . "/$DIR_FECHA";
    my $relbase_path = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . "/$DIR_FECHA";

    my %fotos_controls;
    my %fotos_icono;

    # se lee plantilla para banco de im�genes
    my $tplBancoImg = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/fid/macro_banco_imagenes.html";
    my $moldeBancoImg = &glib_fildir_02::read_file($tplBancoImg);

    # se reemplazan los datos comunes
    $moldeBancoImg =~ s/%%ts%%/$FORM{'_ts'}/ig;
    $moldeBancoImg =~ s/%%path_conf%%/$FORM{'_path_conf'}/ig;

    while ($xml_data =~ /<(\w+?)>(.*?)<\/\1>/sg) {

        my $nom_campo = $1;
        my $valor_campo = $2;

        # ----------
        # Rescatar solo las Fotografias.
        next unless($nom_campo =~ /^(foto_\w+)/i);

        my $wfoto;
        my $hfoto;
        my $campo;

        # Rescatar anchos de fotos
        if ($valor_campo =~ /<(_w$nom_campo)>(.+?)<\/\1>/i) {
            $wfoto = $2;
            $campo = $1;
        };

        # Rescatar altos de fotos.
        if ($valor_campo =~ /<(_h$nom_campo)>(.+?)<\/\1>/i) {
            $hfoto = $2;
            $campo = $1;
        };

        if ($valor_campo =~ /<(_nom$nom_campo)>(.+?)<\/\1>/i) {
            next if (lc $nom_campo eq 'foto_n'); # --> producto de un prb en la glib es posible que hayan fotos fantasma en el xml
            my $nom_foto = $2;

            my $bytes_foto = -s $base_path . $prontus_varglb::DIR_IMAG . "/$nom_foto";       # 1.9
            my $kbytes_foto = &lib_prontus::bytes2kb($bytes_foto, 0);

            my $relpath_foto = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_IMAG . "/$nom_foto";
            $relpath_foto = $relbase_path . $prontus_varglb::DIR_IMAG . "/" . $nom_foto;

            # Se parsean los campos principales
            my $bufferBancoImg = $moldeBancoImg;
            $bufferBancoImg =~ s/%%nom_campo%%/$nom_campo/ig;
            $bufferBancoImg =~ s/%%nom_foto%%/$nom_foto/ig;
            $bufferBancoImg =~ s/%%relpath_foto%%/$relpath_foto/ig;
            $bufferBancoImg =~ s/%%wfoto%%/$wfoto/ig;
            $bufferBancoImg =~ s/%%hfoto%%/$hfoto/ig;

            my $img_type = &lib_prontus::get_img_type($relpath_foto);
            $bufferBancoImg =~ s/%%img_type%%/$img_type/ig;

            if (!&lib_prontus::can_edit_img($img_type)) {
                $bufferBancoImg =~ s/%%openFotoEditor%%/openFotoEditorDisabled/ig;
            } else {
                $bufferBancoImg =~ s/%%openFotoEditor%%/openFotoEditor/ig;
            }

            # Para los iconos de acciones sobre la imagen
            my $reldir_icons = "$prontus_varglb::DIR_CORE/imag/boto";
            $bufferBancoImg =~ s/%%reldir_icons%%/$reldir_icons/ig;

            $nom_foto =~ /^(.*?)\.(\w+)/;
            my $nom_foto_wo_ext = $1;
            $bufferBancoImg =~ s/%%nom_foto_wo_ext%%/$nom_foto_wo_ext/ig;

            my ($dimensiones) = "$wfoto x $hfoto px";
            my ($tamano) = "$kbytes_foto";
            $bufferBancoImg =~ s/%%dimensiones%%/$dimensiones/ig;
            $bufferBancoImg =~ s/%%tamano%%/$tamano/ig;

            my $fotoSinUsar = '<div style="width:50px;"></div>'; # div de relleno
            if ($xml_data !~ /$relpath_foto/i) {
                $fotoSinUsar = '(sin usar)';
            }
            $bufferBancoImg =~ s/%%fotoSinUsar%%/$fotoSinUsar/ig;

            # Se guarda el loop
            $fotos_controls{$nom_campo} = $bufferBancoImg;

            # guardar los datos para Parsear ademas la marca _DIV_FOTOFIJA_<identificador> mas abajo
            my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
            $bufferBancoImg =~ /<!--FOTO_ICONIZADA-->(.*?)<!--\/FOTO_ICONIZADA-->/isg;
            my $foto_iconizada = $1;
            # print STDERR '1 --> '.$foto_iconizada;
            $foto_iconizada =~ s/$crlf//sg;
            $foto_iconizada =~ s/ +/ /sg;
            $foto_iconizada =~ s/ </</sg;
            $foto_iconizada =~ s/> />/sg;
            # print STDERR '2 --> '.$foto_iconizada;
            $fotos_icono{$nom_campo} = $foto_iconizada;
        };

    }; # while

    my $banco_img_max = $prontus_varglb::BANCO_IMG_MAX;

    if ($FORM{'_all'}) {
        $banco_img_max = 0; # todas.
    }

    # Reemplaza fotos en el banco de imagenes
    my $buffer;
    my $nro_fotos_banco;

    foreach my $nom_campo (sort {$b cmp $a} keys %fotos_controls) {

        if ($nro_fotos_banco < $banco_img_max) {
            $nro_fotos_banco++;
            next;
        }

        $buffer = $buffer . $fotos_controls{$nom_campo};
        $nro_fotos_banco++;
    }


    print $buffer;
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

sub get_xml_data {

    # Cargar xml del articulo.

    my $path_final_xml = $prontus_varglb::DIR_SERVER .
                    $prontus_varglb::DIR_CONTENIDO .
                    $prontus_varglb::DIR_ARTIC .
                    "/$DIR_FECHA" .
                    '/xml' .
                    "/$FORM{'_ts'}.xml";
    if(! (-f $path_final_xml)) {
        print "El XML del art�culo no existe";
        print STDERR "El XML del art�culo no existe: $path_final_xml\n";
        exit;
    };
    my $xml = &glib_fildir_02::read_file($path_final_xml);

    my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
    $xml =~ s/$crlf/\x0a/sg;

    my ($priv, $pub);
    if ($xml =~ /<_private>(.*?)<\/_private>/isg) {
        $priv = $1;
    };
    if ($xml =~ /<_public>(.*?)<\/_public>/isg) {
        $pub = $1;
    };
    return "$priv\n$pub";
};

# -------------------------------END SCRIPT----------------------
