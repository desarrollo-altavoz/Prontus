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
# Parsea una plantilla para mostrar el listado de asset de un artículo.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
#
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
#
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 07/08/2013 - JOR - Primera version

# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------
BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    $pathLibsProntus =~ s/\/dam$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use strict;
use dam_varglb;
use glib_html_02;
use glib_cgi_04;
use glib_fildir_02;
use lib_prontus;
use lib_dam;


# ---------------------------------------------------------------
# MAIN.
# -------------
my (%FORM, $BD);

main: {
        # Rescatar parametros recibidos
        &glib_cgi_04::new();
        $FORM{'path_conf'}    = &glib_cgi_04::param('_path_conf');
        $FORM{'ts'}    = &glib_cgi_04::param('ts');
        $FORM{'type'}    = &glib_cgi_04::param('type');

        # Ajusta path_conf para completar path y/o cambiar \ por /
        $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

        # Carga variables de configuracion.
        &lib_prontus::load_config($FORM{'path_conf'});  # Prontus 6.0

        # Control de usuarios obligatorio chequeando la cookie contra el dbm.
        ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);

        # Acceso permitido para admin, publicador, redactor CPN
        if (($prontus_varglb::USERS_PERFIL ne 'A') && ($prontus_varglb::USERS_PERFIL ne 'P') && ($prontus_varglb::USERS_PERFIL ne 'E')){
                print "Content-Type: text/html\n\n";
                &glib_html_02::print_pag_result("Acceso a Area Restringida","La funcionalidad requerida está disponible sólo para usuarios registrados.", 'exit=1,ctype=1');
        };

        if($FORM{'ts'} !~ /\d{14}/) {
                &glib_html_02::print_pag_result('Error', 'TS inválido.', 'exit=1,ctype=1');
        };

        if($FORM{'type'} ne 'foto') {
                &glib_html_02::print_pag_result('Error', 'Tipo inválido.', 'exit=1,ctype=1');
        };

        my $plantilla = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . $dam_varglb::DIR_TMPL . $dam_varglb::TMPL_ASSET_LIST;
        my $pagina = glib_fildir_02::read_file($plantilla);

        # Conectar a BD
        my $msg_err_bd;
        ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
        if (! ref($BD)) {
                &glib_html_02::print_pag_result("Error",$msg_err_bd,1,'ctype=1');
        };


        $pagina = &make_lista($pagina);

        print "Content-Type: text/html\n\n";
        print $pagina;

        exit;
};


sub make_lista {
        my $pagina = $_[0];
        my ($sql, $salida);
        my ($asset_file, $asset_art_fotow, $asset_art_fotoh);
        my $loop;
        my $filas;
        my $dir_fecha;
        my $art_titu;
        $FORM{'ts'} =~ /(\d{8})/;
        $dir_fecha = $1;

        $pagina =~ /%%LOOP%%(.*?)%%\/LOOP%%/is;
        $loop = $1;

        $sql = "SELECT ART_TITU, ASSET_FILE, ASSET_ART_WFOTO, ASSET_ART_HFOTO FROM ASSET LEFT JOIN ART ON (ART_ID=ASSET_ART_ID) WHERE ASSET_TYPE = '$FORM{'type'}' AND ASSET_ART_ID = '$FORM{'ts'}' ORDER BY ASSET_FILE";
        $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($art_titu, $asset_file, $asset_art_fotow, $asset_art_fotoh));
        my $loop_counter = 0;
        while ($salida->fetch) {
                my $loop_tmp = $loop;
                my $lafoto = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_EXMEDIA . '/' . $dir_fecha . '/imag/' . $asset_file;

                my ($sizex, $sizey) = &lib_dam::get_proporcion_imagen(610,450, $asset_art_fotow, $asset_art_fotoh);

                my $size_disk = -s $prontus_varglb::DIR_SERVER . $lafoto;
                $size_disk = &lib_prontus::bytes2kb($size_disk);

                $loop_tmp =~ s/%%SIZEKB%%/$size_disk/isg;
                $loop_tmp =~ s/%%FOTO%%/$lafoto/isg;
                $loop_tmp =~ s/%%WFOTO%%/$sizex/isg;
                $loop_tmp =~ s/%%HFOTO%%/$sizey/isg;
                $loop_tmp =~ s/%%WFOTO_ORIG%%/$asset_art_fotow/isg;
                $loop_tmp =~ s/%%HFOTO_ORIG%%/$asset_art_fotoh/isg;
                $loop_tmp =~ s/%%_TS%%/$FORM{'ts'}/isg;
                $loop_tmp =~ s/%%LOOP_COUNTER%%/$loop_counter/isg;
                $filas .= $loop_tmp;

                $loop_counter++;
        };

        $salida->finish;

        $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
        $pagina =~ s/%%_TS%%/$FORM{'ts'}/isg;
        $pagina =~ s/%%LOOP%%.*?%%\/LOOP%%/$filas/isg;
        $pagina =~ s/%%_TOT_ASSET%%/$loop_counter/isg;
        $pagina =~ s/%%_titular%%/$art_titu/isg;

        return $pagina;
};
