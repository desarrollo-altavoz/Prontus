#!/usr/bin/perl

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
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

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

# Rescatar parametros recibidos.
&glib_cgi_04::new();
$FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
$FORM{'_ts'} = &glib_cgi_04::param('_ts');

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
    print 'Error de sesión. Ud no tiene permisos para revisar estas im&aacute;genes';
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

# se lee plantilla para banco de imágenes
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

        # my ($reemp) = "<img src=\"$prontus_varglb::DIR_CORE/imag/cpan/reemp_of.gif\" style=\"border:0\;width:16\;heigth:16\;\" alt=\"Reemplazar por nueva imagen\" />";
        my $relpath_foto = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_IMAG . "/$nom_foto";
        $relpath_foto = $relbase_path . $prontus_varglb::DIR_IMAG . "/" . $nom_foto;

        # Se parsean los campos principales
        my $bufferBancoImg = $moldeBancoImg;
        $bufferBancoImg =~ s/%%nom_campo%%/$nom_campo/ig;
        $bufferBancoImg =~ s/%%nom_foto%%/$nom_foto/ig;
        $bufferBancoImg =~ s/%%relpath_foto%%/$relpath_foto/ig;

        # Foto iconizada
        # my $alt = "$nom_campo\nW:$wfoto\nH:$hfoto\n$kbytes_foto";
        my $foto_iconizada;
        if($wfoto >= $hfoto) {
            my $ancho_foto_iconizada = $wfoto;
            $ancho_foto_iconizada = 80 if ($wfoto > 80);
            $ancho_foto_iconizada = 'width:'.$ancho_foto_iconizada.'px;';
            $bufferBancoImg =~ s/%%size_img%%/$ancho_foto_iconizada/ig;

        } else {
            my $alto_foto_iconizada = $wfoto;
            $alto_foto_iconizada = 80 if ($wfoto > 80);
            $alto_foto_iconizada = 'height:'.$alto_foto_iconizada.'px;';
            $bufferBancoImg =~ s/%%size_img%%/$alto_foto_iconizada/ig;
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

        # ---- 1.4 Imprime advertencia en rojo en caso de que el peso de la foto exceda el limite establecido.
        # El limite se establece por c/foto en el formulario, de la forma <!--FOTO1_MAXBYTES=1500-->.
#        my $alertPesoMax = '<br/><span color="#CC0000">¡Advertencia! Peso de imagen excede límite permitido</span>';
#        my $maxbytes = 0;
#        if ($pag =~ /%%$nom_campo\_MAXBYTES\s*=\s*(\d+?)\s*%%/) {
#            $maxbytes = $1;
#            if ($bytes_foto > $maxbytes) {
#                $bufferBancoImg =~ s/%%alertPesoMax%%/$alertPesoMax/ig;
#            };
#        };
#        # ----------

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

# Reemplaza fotos en el banco de imagenes
my $buffer;
my $nro_fotos_banco;
foreach my $nom_campo (sort {$b cmp $a} keys %fotos_controls) {

    if($nro_fotos_banco < $prontus_varglb::BANCO_IMG_MAX) {
        $nro_fotos_banco++;
        next;
    };

    $buffer = $buffer . $fotos_controls{$nom_campo};
    $nro_fotos_banco++;
};


print "<!doctype html><html><head><title>Prueba</title></head><body>";
print $buffer;
print "</body></html>";


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
        print "El XML del artículo no existe";
        print STDERR "El XML del artículo no existe: $path_final_xml\n";
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
