#!/usr/bin/perl

# ----------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ----------------------------------------------------------------

# --------------------------------COMENTARIO GLOBAL---------------
# ----------------------------------------------------------------
# PROPOSITO .
# ------------
# Procesar 'submit' de la pagina de ingreso/modif. de edicion.
# Botones procesados :
# 1) Guardar : crea o guarda los cambios de la edicion.
# 2) Borrar : elimina la edicion actual.

# ----------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# -------------------------------
# 1) Despues de Borrar / Guardar, llama a la pag. de Adm. de Ediciones
# (ap_edi_admin.SHTML sin param.).

# ----------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# -------------------------
# 1) Desde la pag. de ingreso/modif. de edicion, via submit.
# ----------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# -------------------------
# No registra.
# ----------------------------------------------------------------
# Version  oficial 1.0 at 04/10/2000
# 1.1 - 06-11-2000 soporte chupoptero (se agrega manejo de hiddens de la forma name = SITEREFpaismundo.html y value=http://www.mercuriovalpo.cl)
# y campo texto con name EDIREFpaismundo.html el que indica el nro de la edicion en el sitio de referencia.
# 1.2 - 16/11/2000 - soporte chupoptero verdadero.
# 2.0 - 21/12/2000 - Chupopterea solo si viene la checkbox Chk_SINC con value SINC
# 2.1 - 26/12/2000 - Modifica para que la generacion de la pagina index.shtml sea ahora a partir de un template /web/index_tmp.shtml
# En este template, se sustituye la marca %%PATH_HOMEPAGE%% por el path a la edicion vigente.
# 2.2 - 27/12/2000 - Correcciones a 1.2 (problemas con e.r. y parseo de marca %%TITPAG%%).

# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0
# 6.1 - 21/11/2001 - Correccion en lectura del working.html
# Prontus 8.0 - 23/05/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# Prontus 8.1 - 09/09/2002 - YCH - Soporte windows media. Ver detalles en /release_prontus81.txt
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# Especial DRs - 08/01/2004 - YCH - Agrega soporte Antialone (parseo de antialone_tmp.html) analogo a lanacion.cl.
# --------------------------------BEGIN SCRIPT--------------------
# ----------------------------------------------------------------
# DECLARACIONES GLOBALES.
# -------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};



use prontus_varglb; &prontus_varglb::init();
use glib_fildir_02;
use glib_hrfec_02;
use glib_html_02;
use lib_prontus;

use glib_cgi_04;

use strict;

my (%FORM); # 8.0




# ----------------------------------------------------------------
# MAIN.
# --------------

main: {

    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});


    # Rescatar valores de campos fijos
    $FORM{'_edic'} = &glib_cgi_04::param('_edic');# Campo hidden con el nombre de la edicion


    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    if ($prontus_varglb::IP_SERVER ne '') { # implica llamada desde ambiente web. # 1.23
        &lib_prontus::test_servers($ENV{'HTTP_REFERER'}); # Autentifica request.  con SERVER_PERM.
    };

    if ($FORM{'_edic'} !~ /^[0-9]{4}_[0-9]{2}_[0-9]{2}_[0-9]$/) {
        &glib_html_02::print_json_result(0, 'Edición no válida', 'exit=1,ctype=1');
    };


    # Valida conf. multi-ed
    if ($prontus_varglb::MULTI_EDICION ne 'SI') {
        &glib_html_02::print_json_result(0, 'Este Prontus no está configurado como multi edición', 'exit=1,ctype=1');
    };

    # user check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    if ($prontus_varglb::EDITOR_ADMINISTRAR_EDICIONES eq 'NO' && $prontus_varglb::USERS_PERFIL eq 'E') {
        &glib_html_02::print_json_result(0, 'La funcionalidad requerida está disponible sólo para el administrador del sistema', 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL ne 'A' && $prontus_varglb::USERS_PERFIL ne 'E') {
        &glib_html_02::print_json_result(0, 'La funcionalidad requerida está disponible sólo para el administrador del sistema y editores', 'exit=1,ctype=1');
    };

    if ($FORM{'_edic'} ne '') {

        # Si esta es la actualmente vigente borrar tag refresh de index.html Y re-escribirlo
        if (&lib_prontus::ed_vigente($FORM{'_edic'}) eq 'SI') {
            my $homesitio = '<HTML>
            <HEAD>
            <TITLE>no hay edicion vigente</TITLE>
            </HEAD>
            <BODY>no hay edicion vigente
            </BODY>
            </HTML>';

            my $path_homesitio = $prontus_varglb::DIR_SERVER . "/$prontus_varglb::PRONTUS_ID/$prontus_varglb::INDEX_SITIO";

            &glib_fildir_02::write_file($path_homesitio, $homesitio);
            &lib_prontus::purge_cache($path_homesitio);

            # Ademas escribe arch de texto con el nro de la ed. vigente
            &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/ed_vigente.txt", '');
        };

        # Borrar el directorio de la edicion
        my $dir_borrar = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_EDIC . "/$FORM{'_edic'}";

        &glib_fildir_02::borra_dir($dir_borrar) if (-d $dir_borrar);
        &lib_prontus::write_log('Borrar', 'Edicion-Portadas', $dir_borrar);
    };

    &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');
};
# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------

# -------------------------------END SCRIPT----------------------

