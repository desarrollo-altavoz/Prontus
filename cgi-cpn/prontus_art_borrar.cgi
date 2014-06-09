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
# Este script se usa solo para PRONTUS-02, PRONTUS-03 y PRONTUS-04.
# Deriva de ap_art_public_01.pl (construido para www.mercuriovalpo.cl)
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------


# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------

# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------

# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 01 - Viernes 02/06/2000 - Primera Version.
# 1.1 - 05/07/2000 - Se agrega posibilidad de manipular archivos realmedia.
# 1.2 - 28/07/2000 - Se agrega posibilidad de manipular archivos asociados genericos.
# 1.3 - 20/09/2000 - soporte para que el script procese correctamente el path relativo al sitio del arch. de configuracion.
# 1.4 - 06/12/2000 - Modificaciones en la llamada a la rutina que carga y valida el archivo de configuracion del prontus.
# Ademas se oficializa la validacion del referer.
# 1.5 - 06/12/2000 - Re-estructuraciones varias para implementar limbo.
# 1.6 - 15/05/2001 - Extensiones para Prontus 5. Estas modificaciones se aplicaron antes de escribir este comentario.
# 1.7 - 16/05/2001 - Modificaciones para parametrizacion del protocolo (http o https) a traves del arch. de conf.
# 1.8 - 16/05/2001 - Revision general de detalles de forma.

# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0
# Prontus 8.0 - 23/05/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# Prontus 8.1 - 12/09/2002 - YCH - Soporte windows media y demases. Ver detalles en /release_prontus81.txt
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT--------------------
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

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_fildir_02;
use lib_prontus;
use glib_cgi_04;
use glib_hrfec_02;
use DBI;
use glib_dbi_02;
use lib_tax;
use lib_artic;

# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM);

main: {

    # Rescatar parametros recibidos
    &glib_cgi_04::new();

    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    if ($prontus_varglb::IP_SERVER ne '') { # implica llamada desde ambiente web. # 1.23
        &lib_prontus::test_servers($ENV{'HTTP_REFERER'}); # Autentifica request.  con SERVER_PERM.
    };

    # user check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };


    $FORM{'_ts'} = &glib_cgi_04::param('_ts');
    if ($FORM{'_ts'} !~ /^\d{14}$/) {
        &glib_html_02::print_json_result(0, 'Artículo no válido', 'exit=1,ctype=1');
    };

    my $ports_ref = &artic_in_ports($FORM{'_ts'});
    if ($ports_ref !~ /^\s*$/) {
        &glib_html_02::print_json_result(0, "Artículo no puede ser borrado porque se encuentra publicado en las sgtes. portadas:\n\n${ports_ref}", 'exit=1,ctype=1');

    } else {

        # Conectar a BD
        my $msg_err_bd;
        my $base;
        ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
        if (! ref($base)) {
            &glib_html_02::print_pag_result("Error",$msg_err_bd . '<br>No es posible eliminar los artículos seleccionados.',1,'exit=1,ctype=1,link=nolink');
        };

        my $artic_obj = Artic->new(
                'prontus_id' => $prontus_varglb::PRONTUS_ID,
                'public_server_name' => $prontus_varglb::PUBLIC_SERVER_NAME,
                'cpan_server_name' => $prontus_varglb::IP_SERVER,
                'ts' => $FORM{'_ts'}, # si no va, asigna uno nuevo
                'campos'=> '') || &glib_html_02::print_json_result(0, "Error inicializando objeto articulo: $Artic::ERR\n", 'exit=1,ctype=1');

        my $resp = $artic_obj->borra_artic($base);
        if($resp) {
            &lib_prontus::write_log('Borrar Error', 'Articulo', $ts);
            &glib_html_02::print_json_result(0, $resp, 'exit=1,ctype=1');
        } else {
            &lib_prontus::write_log('Borrar', 'Articulo', $ts);
        };

    };

    &exec_postproceso_artborrar($FORM{'_ts'});

    &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------

sub artic_in_ports {
# Obtiene las portadas en donde se encuentra publicado un articulo

    my $ts = shift;
    my $referencias;

    # CVI - 08/02/2013 - Se carga el Hash de Articulos publicados en portadas
    my %hash_artic_pubs = &lib_prontus::load_artic_pubs();

    my $hash = \%hash_artic_pubs;

    if($hash->{$ts}) {
        my $ediciones;
        foreach my $edic (keys %{$hash->{$ts}}) {
            my $portadas;
            foreach my $port (keys %{$hash->{$ts}->{$edic}}) {
                $referencias = "$referencias$edic/$port\n";
            }
        }
        print STDERR "El articulo [$ts] no se pudo eliminar\n";

    } else {
        print STDERR "El articulo [$ts] se puede borrar OK\n";
    }
    $referencias = $referencias . "\n";
    return $referencias;

};


# --------------------------------------------------------------------#
sub exec_postproceso_artborrar {
    my ($ts) = $_[0];
    my ($post_proceso) = $prontus_varglb::POST_PROCESO{'ART-BORRAR'};

    if ($post_proceso =~ /\( *([\w\.\\\/ ]+) *\)/) {

        $post_proceso = $1;
        # print STDERR "pp despues[$post_proceso]\n";
        use FindBin '$Bin';
        my $rutaScript = $Bin;

        # para que sea un script valido debe ubicarse en el mismo dir. de cgi del prontus o a lo mas un nivel hacia arriba.
        if ( ($post_proceso =~ /^\w/) || ($post_proceso =~ /^\.\.(\/|\\)\w/) ) {
            my $cmd = "$rutaScript/$post_proceso $ts $prontus_varglb::PRONTUS_ID $prontus_varglb::PUBLIC_SERVER_NAME";
            print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
            system $cmd;
        };
    };
};

# -------------------------------END SCRIPT----------------------
