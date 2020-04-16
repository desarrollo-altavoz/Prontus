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
# Armar y desplegar en el browser la ficha para editar o ingresar un Articulo.
# Deriva de ap_art_ficha_01.pl (construido para www.mercuriovalpo.cl).

# Este script opera para PRONTUS-01, PRONTUS-02, PRONTUS-03 y PRONTUS-04.
# Para PRONTUS-01:
# 1) Se debe utilizar el Hidden FILE de la ficha para indicar el nombre
# del archivo correspondiente al articulo con el que se debe trabajar.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# No registra.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# PRONTUS-02 :
# 1) Desde la pag. de Administracion de Articulos, via boton 'Nuevo'
# pasando por param. los hidden Cmb_TIPO y path_conf.
# 2) Via link para editar articulo con los sgtes. parametros:
# art=<nombre articulo con extension y s/path>
# Cmb_TIPO=<nombre del template de articulo usado en la creacion, con extension y sin path>
# path_conf=<path absoluto al archivo de configuracion>

# PRONTUS-03 y PRONTUS-04 :
# 1) Desde la pag. de Administracion de Articulos, via boton 'Nuevo'
# pasando por param. Cmb_TIPO (valor selecc. en la combo) mas el hidden path_conf y via link para editar articulo con los sgtes. parametros:
# art=<nombre articulo con extension y s/path>
# Cmb_TIPO=<nombre del template de articulo usado en la creacion, con extension y sin path>
# path_conf=<path absoluto al archivo de configuracion>
# ###########
# PRONTUS-01 :
# 1) Directamente del panel de control con los sgtes. parametros :

# Para Nuevo o Editar:

# Cmb_TIPO=<nombre del formulario de publicacion usado en la creacion, con extension y sin path>
# art=<nombre del arch. a editar con extension y sin path>
# path_conf=<path relativo al sitio al archivo de configuracion>
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# Minimo prontus_art_ficha.html
# ---------------------------------------------------------------

# HISTORIAL DE VERSIONES.
# ---------------------------
# 01 - Viernes 02/06/2000 - Primera Version.
# 1.1 - 05/07/2000 - Se agrega posibilidad de manipular archivos realmedia.
# 1.2 - 28/07/2000 - Se agrega posibilidad de manipular archivos cualquiera (por ej. de texto)
# asociados al articulo. Estos archivos estaran disponibles solo a traves de links en el articulo y portada. Son del tipo
# ASOCFILEi.
# 1.3 - 18/08/2000 - Compatibilidad PRONTUS-04NA y PRONTUS-03NA.
# 1.4 - 05/09/2000 - Imprime advertencia en rojo en caso de que el peso de la foto exceda el limite establecido.
# El limite se establece por c/foto en el formulario, de la forma <!--FOTO1_MAXBYTES=1500-->.
# 1.5 - 20/09/2000 - soporte para que el script procese correctamente el path relativo al sitio del arch. de configuracion.
# 1.6 - 04/10/2000 - correciones en el manejo de tablas y pies de fotos y tablas.
# 1.7 - 06/12/2000 - Modificaciones en la llamada a la rutina que carga y valida el archivo de configuracion del prontus.
# Ademas se oficializa la validacion del referer.
# 1.8 - 05/12/2000 - Modificaciones para soportar marcas de codigo html puro dentro de los campos TEXT.
# 1.9 - 05/04/2001 - Modificacion de una linea con bug, lo cual impedia que apareciera correctamente la advertencia de fotos demasiado pesadas.
# 1.10 - 15/05/2001 - Extensiones para Prontus 5. Estas modificaciones se aplicaron antes de escribir este comentario.
# 1.11 - 16/05/2001 - Revision general de detalles de forma.

# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0

# 7.0 - 20/12/2001 - Extensiones p7 :
#   . "- Agrega marca a la portada para que inserte los menús de páginas con subtí­tulos.<br>"
#     . "- Perfilación de periodistas en lista de artículos para permitir artÃículos personales<br>"
#     . "- Capacidad para borrar fotos, asocfile y realmedia<br>"
#     . "- Linkeo de URLs https<br>"
# Prontus 8.0 - 01/08/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# Prontus 8.1 - 09/09/2002 - YCH - Soporte windows media. Ver detalles en /release_prontus81.txt
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT--------------------
# 100.1 - 14/08/2007 - ych - agrega mayor precision en deteccion de https para vtxt
# 100.2 - 17/08/2007 - ych - no intenta leer hoja de estilo si esta no existe.
#
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

use strict;
use utf8;
# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use glib_fildir_02;
use glib_str_02;
use lib_prontus;
use glib_html_02;

use glib_cgi_04;

use DBI;
use glib_dbi_02;
use lib_secc;
use lib_tags;
use lib_waitlock; # Bloqueos tipo espera.
use lib_quota;
use lib_tax;
use Session;

# variables globales del script
my $ART_AUTOINC;
my $BD;
my (%ID_SECCIONES, %ID_TEMAS, %ID_SUBTEMAS, %FORM);
my (%TABLA_SECC, %TABLA_TEMAS, %TABLA_SUBTEMAS);
my $PATH_FICHA;

# ---------------------------------------------------------------
# MAIN.
# -------------

main: {
    # Rescatar parametros recibidos.
    &glib_cgi_04::new();
    $FORM{'_file'} = &glib_cgi_04::param('_file');
    $FORM{'_fid'} = &glib_cgi_04::param('_fid'); # fid_general
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    $FORM{'_dir_fecha'} = '';
    $FORM{'_dir_fecha'} = &lib_prontus::get_dirfecha_by_ts($FORM{'_file'}) if ($FORM{'_file'} =~ /^\d{14}\.\w+$/);
    $FORM{'_curr_body'} = &glib_cgi_04::param('_curr_body');
    $FORM{'_curr_body'} = 'body1' if ($FORM{'_curr_body'} !~ /^body\d+$/);

    $FORM{'_edic'} = &glib_cgi_04::param('_edic');
    $FORM{'_port'} = &glib_cgi_04::param('_port');
    $FORM{'_area'} = &glib_cgi_04::param('_area');

    $FORM{'_popup'} = &glib_cgi_04::param('_popup');
    $FORM{'_port_dd'} = &glib_cgi_04::param('_port_dd');
    $FORM{'_upd_port_dd'} = &glib_cgi_04::param('_upd_port_dd');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Se lee el titular que habí­a antes, para no perderlo
    $FORM{'_txt_titular'} = &lib_prontus::get_codetext_value(&glib_cgi_04::param('_txt_titular'));

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    # Validar quota
    my $msg_err_quota = &lib_quota::check_quota_suficiente();
    &glib_html_02::print_pag_result('Error',$msg_err_quota, 1, 'exit=1,ctype=1') if ($msg_err_quota);

    print "Cache-Control: no-cache\n";
    print "Cache-Control: max-age=0\n";
    print "Cache-Control: no-store\n";
    print "Content-Type: text/html\n\n";

    my $dir_tpl_pags = $prontus_varglb::DIR_SERVER
                    . $prontus_varglb::DIR_TEMP
                    . $prontus_varglb::DIR_ARTIC
                    . $prontus_varglb::DIR_FECHA
                    . $prontus_varglb::DIR_PAG;


    # Conectar a BD
    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &glib_html_02::print_pag_result("Error",$msg_err_bd,1,'exit=1');
    };

    # Carga la tabla de secciones
    %TABLA_SECC = &lib_tax::carga_hash_seccion($BD);
    %TABLA_TEMAS = &lib_tax::carga_hash_temas($BD);
    %TABLA_SUBTEMAS = &lib_tax::carga_hash_subtemas($BD);

    # Nuevo
    my $ts;   # rc15
    my $pagina;
    if ($FORM{'_file'} eq '') {
        my $popup_tipos = &generar_popup_tipos();
        # print STDERR "fid1[$FORM{'_fid'}]\n";
        $FORM{'_fid'} = &get_first_fid($popup_tipos) if (!$FORM{'_fid'});
        $popup_tipos = &posicionar_popup_tipos($popup_tipos, $FORM{'_fid'});
        # print STDERR "fid2[$FORM{'_fid'}]\n";
        # print STDERR "popup_tipos[$popup_tipos]\n";

        my $PATH_FICHA = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CPAN . "/fid/$FORM{'_fid'}.html";


        # Validar tipo de articulo.
        if (!-f $PATH_FICHA) {
            &glib_html_02::print_pag_result('Error','Tipo de art&iacute;culo no v&aacute;lido o indeterminado.',1,'exit=1,ctype=0');
        };


        # Cod html correspondiente a la combo de templates de articulos
        my $html_tpag = &glib_html_02::generar_popup_from_dir($dir_tpl_pags, '_PLT', '', 1, '', 'SIN_EXT', '', '', 1000000, 'STRASC');

        # Filtrar lista de templates de acuerdo a los soportados por el tipo de ficha de articulo.
        # print STDERR "html_tpag1[$html_tpag] fid[$FORM{'_fid'}]\n";
        $html_tpag = &filtrar_templates($html_tpag, $FORM{'_fid'});
        # print STDERR "html_tpag2[$html_tpag]\n";

        # Generar combo con tipos de articulos
        my $tipos_art = 'FID:<br/>' . $popup_tipos . '&nbsp;';
        my $cmb_multivistas;
        if (keys(%prontus_varglb::MULTIVISTAS)) {
            $cmb_multivistas = 'Vista: ' . &lib_prontus::generar_popup_multivistas();
        };


        $pagina = &carga_buffer_fid($PATH_FICHA);

        # Reemplazar marcas privadas
        $pagina =~ s/%%_FID%%/$tipos_art/ig;
        $pagina =~ s/%%_ART_AUTOINC%%/0/ig;
        $pagina =~ s/%%_CURR_BODY%%/$FORM{'_curr_body'}/ig;
        $pagina =~ s/%%_PLT%%/Plantilla :<br\/> $html_tpag/ig;
        $pagina =~ s/%%_CMB_MV%%/$cmb_multivistas/ig;
        $pagina =~ s/%%_port_dd%%/$FORM{'_port_dd'}/ig;

        # Para no perder el titular
        $pagina =~ s/%%_saved_titular%%/$FORM{'_txt_titular'}/ig;

        my $hiddens = "<input type=\"hidden\" name=\"_file\" value=\"\" />\n"
                    . "<input type=\"hidden\" name=\"_path_conf\" value=\"$FORM{'_path_conf'}\" />\n";


        $pagina =~ s/<form (.*?)>/<form $1>\n$hiddens/is;

        # Agrega el vtxt
        $html_tpag =~ /value *= *"(\w.*?)" *>/i;
        my $tpl_artic = $1;
        $pagina = &add_vtxt($pagina, $tpl_artic);


        $pagina = &incluye_fechahora($pagina);
        $pagina = &incluye_nomseccs($pagina);
        $pagina = &incluye_fotosfijas($pagina);

        my $ts_default = &glib_hrfec_02::get_dtime_pack4();
        my $fecha_default = substr($ts_default, 0, 8);
        my $hora_default = substr($ts_default, 8, 2).':'. substr($ts_default, 10, 2);
        $pagina =~ s/%%_fechap%%/$fecha_default/isg;
        $pagina =~ s/%%_horap%%/$hora_default/isg;

        $pagina =~ s/%%_REL_PATH_PRONTUS%%/$prontus_varglb::RELDIR_BASE\/$prontus_varglb::PRONTUS_ID/ig;
        $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/ig;
        $pagina =~ s/%%LOOP_FOTOS%%.*?%%\/LOOP_FOTOS%%//isg;
        $pagina =~ s/<!--vermas imagenes-->.*?<!--\/vermas imagenes-->//isg;
        $pagina =~ s/%%_SIZE_HTML%%/0/isg;
        $pagina =~ s/%%_SIZE_TOTAL%%/0/isg;
        # reemplazar nombre del prontus
        $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;

        # pagspar
        $pagina =~ s/<!--list_pagspar-->.*?<!--\/list_pagspar-->//isg;

        # Alta control
        if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS eq 'SI') {

            my $alta_control = '<label for="_alta">Alta de art&iacute;culo:</label> <input type="checkbox" id="_alta" name="_ALTA" value="1" %%_ALTA%% />';
            if ($prontus_varglb::USERS_PERFIL eq 'P') { # para periodistas aparece disabled
                $alta_control =~ s/%%_ALTA%%/ disabled/ig;
                $pagina =~ s/%%_ALTA%%/ $alta_control/ig;
            }
            else {
                $alta_control =~ s/%%_ALTA%%//ig;
                $pagina =~ s/%%_ALTA%%/ $alta_control/ig;
            };
        }
        else {
            $pagina =~ s/%%_ALTA%%//ig;
        };

        # solo portadas, nuevo artic.
        if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
            $pagina =~ s/%%_SOLOPORTADAS%%/ checked="checked"/ig;
        }
        else {
            $pagina =~ s/%%_SOLOPORTADAS%%//ig;
        };

        if ($FORM{'_edic'} && $FORM{'_port'} && $FORM{'_area'}) {

            my $hidden_edic = '<input type="hidden" name="_edic" value="' . $FORM{'_edic'} . '" />';
            my $hidden_port = '<input type="hidden" name="_port" value="' . $FORM{'_port'} . '" />';
            my $hidden_area = '<input type="hidden" name="_area" value="' . $FORM{'_area'} . '" />';
            $pagina =~ s/<form (.*?)>/<form $1>\n$hidden_edic\n$hidden_area\n$hidden_port/is;
            my $label_pub_directa = 'Publicaci&oacute;n directa en ';
            if ($FORM{'_edic'} != 'base') {
                my $edic4fecha = $FORM{'_edic'};
                $edic4fecha =~ s/_//ig;
                $label_pub_directa .= "Edici&oacute;n '" . &glib_hrfec_02::des_normaliza_fecha($edic4fecha) . "'" . ' - ';
            };
            my ($port_nom, $ext_port) = &lib_prontus::split_nom_y_extension($FORM{'_port'});
            $label_pub_directa .= "Portada '" . $port_nom . "'" . ' - &Aacute;rea ' . $FORM{'_area'};

            $pagina =~ s/%%_LABEL_PUB_DIRECTA%%/$label_pub_directa/g;
        } else {
            $pagina =~ s/%%_LABEL_PUB_DIRECTA%%//g;
        };

    # Modificar
    } else {
        $PATH_FICHA = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CPAN . "/fid/$FORM{'_fid'}.html";

        # Validar tipo de articulo.
        if (!-f $PATH_FICHA) {
            &glib_html_02::print_pag_result('Error','Tipo de art&iacute;culo no v&aacute;lido o indeterminado.',1,'exit=1,ctype=0');
        };

        $pagina = &cargar_campos($dir_tpl_pags);
    };

    my $hidden_dirfecha = '<input type="hidden" name="_dir_fecha" value="' . $FORM{'_dir_fecha'} . '" />';
    $pagina =~ s/<form (.*?)>/<form $1>\n$hidden_dirfecha/is;

    my $pathrel_arr_tst = $prontus_varglb::DIR_CPAN . '/procs/tax4fids/tax4fids.js';
    my $str_random_tax = &glib_str_02::random_string(10);
    my $str_tax4fids = "<script type=\"text/javascript\" src=\"$pathrel_arr_tst?$str_random_tax\"></script>";
    $str_tax4fids = '' if(! -f "$prontus_varglb::DIR_SERVER$pathrel_arr_tst");
    $pagina =~ s/%%_tax4fids%%/$str_tax4fids/isg;
    $pagina =~ s/%%_ARR_TST%%/$str_tax4fids/;
    # print STDERR "pagina[$pagina]";
    $pagina = &incluye_combostax($pagina);

    # if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^[1-3]$/) {
    $pagina = &lib_secc::parse_seccion($pagina, $BD, 'solo habilitadas');

    $pagina = &posicionar_combo($pagina, '_SECCION1', $ID_SECCIONES{'_SECCION1'});
    $pagina = &posicionar_combo($pagina, '_SECCION2', $ID_SECCIONES{'_SECCION2'});
    $pagina = &posicionar_combo($pagina, '_SECCION3', $ID_SECCIONES{'_SECCION3'});

    $ID_TEMAS{'_TEMA1'} = '0' if ($ID_TEMAS{'_TEMA1'} eq '');
    $ID_TEMAS{'_TEMA2'} = '0' if ($ID_TEMAS{'_TEMA2'} eq '');
    $ID_TEMAS{'_TEMA3'} = '0' if ($ID_TEMAS{'_TEMA3'} eq '');
    $pagina =~ s/%%_TEMA1%%/$ID_TEMAS{'_TEMA1'}/ig;
    $pagina =~ s/%%_TEMA2%%/$ID_TEMAS{'_TEMA2'}/ig;
    $pagina =~ s/%%_TEMA3%%/$ID_TEMAS{'_TEMA3'}/ig;

    $ID_SUBTEMAS{'_SUBTEMA1'} = '0' if ($ID_SUBTEMAS{'_SUBTEMA1'} eq '');
    $ID_SUBTEMAS{'_SUBTEMA2'} = '0' if ($ID_SUBTEMAS{'_SUBTEMA2'} eq '');
    $ID_SUBTEMAS{'_SUBTEMA3'} = '0' if ($ID_SUBTEMAS{'_SUBTEMA3'} eq '');

    $pagina =~ s/%%_SUBTEMA1%%/$ID_SUBTEMAS{'_SUBTEMA1'}/ig;
    $pagina =~ s/%%_SUBTEMA2%%/$ID_SUBTEMAS{'_SUBTEMA2'}/ig;
    $pagina =~ s/%%_SUBTEMA3%%/$ID_SUBTEMAS{'_SUBTEMA3'}/ig;


    my $ts_artic = $FORM{'_file'}; # pal parseo de la tsdata da lo mismo q venga vacio
    $ts_artic =~ s/\.[\w\-]*$//; # saca extension

    # Recupera los tags asignados a este articulo, los nombres ya vienen escapeados para html
    my $tags_for_fid = &lib_tags::get_tags_for_fid($BD, $ts_artic);
    $pagina =~ s/%%_tags4fid%%/$tags_for_fid/ig;


    # Recupera los ultimos tags ingresados, los nombres ya vienen escapeados para html
    my $max_tags = $prontus_varglb::MAX_LAST_TAGS_4FID;
    if($max_tags eq '1') {
      $pagina =~ s/%%_lasttags_text%%/&Uacute;ltimo Tag Ingresado/ig;
    } else {
      $pagina =~ s/%%_lasttags_text%%/&Uacute;ltimos $max_tags Tags Ingresados/ig;
    }
    my $last_tags = &lib_tags::get_last_tags($BD, $max_tags);
    $pagina =~ s/%%_lasttags%%/$last_tags/ig;


    $BD->disconnect;

    if ($FORM{'_file'}) {
        my $marca_file = $prontus_varglb::DIR_CONTENIDO .
                        $prontus_varglb::DIR_ARTIC .
                        "/$FORM{'_dir_fecha'}" .
                        $prontus_varglb::DIR_PAG .
                        "/$FORM{'_file'}";
        $pagina =~ s/%%_FILE%%/$marca_file/ig;
    }
    else {
        $pagina =~ s/%%_FILE%%//ig;
    };

    # Reemplaza TS, FECHAC, FECHACLONG, FECHACSHRT
    $pagina = &lib_prontus::replace_tsdata($pagina, $ts_artic);


    # Borrar marcas sobrantes
    # si no se parseo el titular intentamos el titular anterior
    if ($FORM{'_txt_titular'} ne '' ) {
        $pagina =~ s/%%_TXT_TITULAR%%/$FORM{'_txt_titular'}/isg;
    }
    # si aun no se parseo el titular, parseo algo de relleno
    my $placeholder = 'Sin t&iacute;tulo '. (time - $prontus_varglb::URL_NUMBER);
    $pagina =~ s/%%_TXT_TITULAR%%/$placeholder/isg;

    # parsear SERVER_NAME
    $pagina =~ s/%%_SERVER_NAME%%/$prontus_varglb::PUBLIC_SERVER_NAME/ig;

    # parsea el archivo de configuracion
    $pagina =~ s/%%_path_conf%%/$FORM{'_path_conf'}/isg;

    # parsea id de sesion activa para que pueda enviarsele al prontus_art_upfoto.cgi
    $pagina = &parsea_id_session($pagina);


    # parsea ubic del cgi-bin ya que ahi esta la cgi de upload de fotos
    $pagina =~ s/%%_DIR_CGI_PUBLIC%%/$prontus_varglb::DIR_CGI_PUBLIC/isg;

    # parsea nombre del prontus del manual de operacion
    my $version4manual = $prontus_varglb::VERSION_PRONTUS;
    $version4manual =~ s/^(\d+)\.(\d+)\.(\d+).+$/$1_$2/;
    my $prontus_manual_oper =  'prontus_operacion_v' . $version4manual;
    $pagina =~ s/%%_prontus_manual_oper%%/$prontus_manual_oper/isg;


    # CVI - 21/07/2014 - Para uso desde el CPAN
    if($prontus_varglb::SERVER_PROTOCOLO_HTTPS eq 'SI') {
        $pagina =~ s/%%_ishttps%%(.*?)%%\/_ishttps%%/$1/isg;
    } else {
        $pagina =~ s/%%_ishttps%%.*?%%\/_ishttps%%//isg;
    }

    # CVI - 16/06/2011
    my $open_fid_in_pop = 'open_normally';
    if($prontus_varglb::ABRIR_FIDS_EN_POP eq 'SI') {
        $open_fid_in_pop = 'open_in_pop';
    }
    $pagina =~ s/%%_class_open_fid%%/$open_fid_in_pop/ig;

    # CVI - 16/06/2011
    if($FORM{'_popup'} eq '1') {
      $pagina =~ s/%%_code4popup%%(.*?)%%\/_code4popup%%/$1/isg;
    } else {
      $pagina =~ s/%%_code4popup%%.*?%%\/_code4popup%%//isg;
    }

    if ($FORM{'_upd_port_dd'}) {
        $pagina =~ s/%%_upd_port_dd%%(.*?)%%\/_upd_port_dd%%/$1/isg;
    } else {
        $pagina =~ s/%%_upd_port_dd%%.*?%%\/_upd_port_dd%%//isg;
    };

    # se parsea el numero de version de friendly urls en uso
    if ($prontus_varglb::FRIENDLY_URLS eq 'SI') {
        $pagina =~ s/%%_friendly_urls_ver%%/$prontus_varglb::FRIENDLY_URLS_VERSION/ig;
    } else {
        $pagina =~ s/%%_friendly_urls_ver%%/0/ig;
    }

    if ($prontus_varglb::FRIENDLY_URLS_VERSION eq '4' && !exists $prontus_varglb::FRIENDLY_V4_EXCLUDE_FID{$FORM{'_fid'}}) {
      $pagina =~ s/%%_friendly4%%(.*?)%%\/_friendly4%%/$1/isg;
    } else {
      $pagina =~ s/%%_friendly4%%.*?%%\/_friendly4%%//isg;
    }

    if ($prontus_varglb::MULTITAG eq 'SI') {
        $pagina =~ s/%%_multitag%%(.*?)%%\/_multitag%%/$1/isg;
    } else {
        $pagina =~ s/%%_multitag%%.*?%%\/_multitag%%//isg;
    }

    $pagina =~ s/%%.+?%%//g;

    # Restituir las marcas especiales de las fotos y tablas y htmlfiles embebidas en el texto..
    $pagina =~ s/##(.*?)##/%%$1%%/g;

    $pagina =~ s/&#37;&#37;/%%/sg; # restituyo los %% escritos por el usuario al interior de los campos

    $pagina =~ s/<!--[^\/]+?-->//sg;
    $pagina =~ s/<!-- *\/[^\/]+?-->//sg;

    my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
    $pagina =~ s/>($crlf| )+</>\x0a</sg;

    print $pagina;
}

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
# --------------------------------------------------------------------
sub parsea_id_session {
# parsea id de sesion activa para que pueda enviarsele al prontus_art_upfoto.cgi, dado que este ultimo no tiene acceso a la cookie
    my $pagina = $_[0];
    my $sess_obj = Session->new(
                    'prontus_id'        => $prontus_varglb::PRONTUS_SSO_MANAGER_ID,
                    'document_root'     => $prontus_varglb::DIR_SERVER)
                    || die("Error inicializando objeto Session: $Session::ERR\n");
    my $sdata = $sess_obj->{id_session};
    $pagina =~ s/%%_sdata%%/$sdata/ig;
    return $pagina;
};
# ---------------------------------------------------------------
sub incluye_combostax {
  my $pagina = $_[0];
  my $tax;

  if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^[1-3]$/) {
    $tax = '<div class="tabtax">';
  };

  if ($prontus_varglb::TAXONOMIA_NIVELES >= 1) {
    $tax .= '
          <div class="nivel">
            <div class="item">SECCION 1<br/>
              %%_SECCION1%%
            </div>
            <div class="item">TEMA 1<br/>
              <select name="_TEMA1" size="1" class="P-DATATABLA" onchange="CombosTax.generaSubtemas(1);">
                <option value="">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                </option>
              </select>
            </div>
            <div class="item">SUBTEMA 1<br/>
              <select name="_SUBTEMA1" size="1" class="P-DATATABLA">
                <option value="">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                </option>
              </select>
            </div>
          </div>';
  };

  if ($prontus_varglb::TAXONOMIA_NIVELES >= 2) {
    $tax .= '
          <div class="nivel">
            <div class="item">SECCION 2<br/>
              %%_SECCION2%%
            </div>
            <div class="item">TEMA 2<br/>
              <select name="_TEMA2" size="1" class="P-DATATABLA" onchange="CombosTax.generaSubtemas(2);">
                <option value="">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                </option>
              </select>
            </div>
            <div class="item">SUBTEMA 2<br/>
              <select name="_SUBTEMA2" size="1" class="P-DATATABLA">
                <option value="">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                </option>
              </select>
            </div>
          </div>';
  };

  if ($prontus_varglb::TAXONOMIA_NIVELES == 3) {
    $tax .= '
          <div class="nivel">
            <div class="item">SECCION 3<br/>
              %%_SECCION3%%
            </div>
            <div class="item">TEMA 3<br/>
              <select name="_TEMA3" size="1" class="P-DATATABLA" onchange="CombosTax.generaSubtemas(3);">
                <option value="">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                </option>
              </select>
            </div>
            <div class="item">SUBTEMA 3<br/>
              <select name="_SUBTEMA3" size="1" class="P-DATATABLA">
                <option value="">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                </option>
              </select>
            </div>
          </div>';
  };

  if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^[1-3]$/) {
    $tax .= '</div>';
  };

  $pagina =~ s/%%_TAXONOMIA%%/$tax/i;
  return $pagina;
};

# ---------------------------------------------------------------
sub posicionar_combo {
  my ($pagina) = $_[0];
  my ($nom_combo) = $_[1];
  my ($val_combo) = $_[2];
  my ($combo, $combo_aux);


  $val_combo =~ s/\(/##abc/isg;
  $val_combo =~ s/\)/##cba/isg;

  $pagina =~ s/\(/##abc/isg;
  $pagina =~ s/\)/##cba/isg;

  $pagina =~ /(<select name="$nom_combo".*?<\/select>)/is;
  $combo = $1;

  $combo_aux = $combo;
  $combo =~ s/selected//isg;
  $combo =~ s/option value="$val_combo"/option value="$val_combo" selected="selected"/is;
  $pagina =~ s/\Q$combo_aux\E/$combo/is;

  $pagina =~ s/##abc/\(/isg;
  $pagina =~ s/##cba/\)/isg;
  return $pagina;
};


# ---------------------------------------------------------------
sub posicionar_popup_tipos {
  my ($popup) = $_[0];
  my ($val_combo) = $_[1];
  $popup =~ s/<option value="$val_combo"/<option value="$val_combo" selected="selected"/is;
  return $popup;
};

# ---------------------------------------------------------------
sub generar_popup_tipos {
# Generar combo de tipos de articulos, obteniendo la informacion desde
# el hash global definido en el arch. de configuracion.
# Retorna : Lista de seleccion con datos, lista para imprimirla.

  my($name_obj) = '_fid';
  my($valor_clave) = '';
  my($items_visibles) = '1';
  my($ind_multiple) = '';
  # my($javascript) =  " onchange=\"window.location='prontus_art_ficha.$prontus_varglb::EXTENSION_CGI?_CURR_BODY=$FORM{'_CURR_BODY'}&_PATH_CONF=$FORM{'_PATH_CONF'}&_CMB_TIPO=' + this[this.selectedIndex].value\"";
  my($javascript) =  " onchange=\"Fid.objFormFid.action='prontus_art_ficha.$prontus_varglb::EXTENSION_CGI';Fid.onSetTab();Fid.objFormFid.target='_self';Fid.objFormFid.submit(); \"";
  my($lista) = '';

  my($val_display, $key, $clave);
  my($key2); # 1.11

  # Generar la lista de seleccion en html
  $lista = q{<select name="} . $name_obj . q{" size="} . $items_visibles . q{" } . $ind_multiple . ' ' . $javascript . q{>};

  # 8.0
  my (%sort_tipos, $tipo_glosa);
  foreach $key (keys %prontus_varglb::FORM_PLTS) {
    # El valor a mostrar esta despues de los 2 puntos en la clave.
    $tipo_glosa = $key;
    $tipo_glosa =~ s/^.*://;
    $sort_tipos{$key} = lc $tipo_glosa;
  };


  # foreach $key (keys %prontus_varglb::FORM_PLTS) {    # 8.0 se ordena popup por glosa de tipos de articulos.
  foreach $key (sort {$sort_tipos{$a} cmp $sort_tipos{$b}} keys %prontus_varglb::FORM_PLTS) {
    # print "<br/>key:$key"; # debug
    $val_display = $key;
    # El valor a mostrar esta despues de los 2 puntos en la clave.
    $val_display =~ s/^.*://;

    # La clave de los items de la combo sera lo que esta antes de los 2 puntos (nombre del arch. html que se usara como ficha).
    $clave = $key;

    $clave =~ s/:.*$//;

    my $seleccionado = '';
    if ( $clave eq $valor_clave ) {
       $seleccionado = 'selected="selected"';
    };


    if ( (($prontus_varglb::USERS_PERFIL eq 'P') or ($prontus_varglb::USERS_PERFIL eq 'E')) && $prontus_varglb::PRONTUS_SSO ne 'SI' ) { # Periodista o Editor
      # Mostrar solo los tipos de articulos permitidos al usuario conectado.
      foreach $key2 (keys %prontus_varglb::ARTUSERS) {
        my ($tipart, $usr) = split /\|/, $key2;
        if ( ($usr eq $prontus_varglb::USERS_ID) and ($tipart eq $clave) ) {
          $lista = $lista . '<option value="' . $clave . "\" $seleccionado>";
          $val_display = $key;
          # El valor a mostrar esta despues de los 2 puntos en la clave.
          $val_display =~ s/^.*://;
          $lista = $lista . $val_display . '</option>';
        };
      };
    }
    else { # admin
      # Mostrar todos los tipos.
      $lista = $lista . '<option value="' . $clave . "\" $seleccionado>";
      $val_display = $key;
      # El valor a mostrar esta despues de los 2 puntos en la clave.
      $val_display =~ s/^.*://;
      $lista = $lista . $val_display . '</option>';
    };


  };

  $lista = $lista . q{</select>};
  return $lista;
};
# ---------------------------------------------------------------
sub get_first_fid {
    my $popup_tipos = $_[0];
    my $default_fid = &get_default_fid();
    # print STDERR "default_fid[$default_fid]\n";
    if ($popup_tipos =~ /<option value="$default_fid"/i) {
        return $default_fid;
    } else {
        my $first_fid;
        $first_fid = $1 if ($popup_tipos =~ /<option value="(.+?)"/i);
        return $first_fid;
    };
};
# ---------------------------------------------------------------
sub get_template {
# Obtiene el archivo html usado como plantilla html en la generacion del articulo

# Retorna el archivo usado (con extension y sin path).
my ($xml_data) = $_[0];

my ($text, $head, $cmb_temp, $base_path);

  # Solo disponible cuando hay BD.
  if ($xml_data =~ /<_PLT>(.+?)<\/_PLT>/i) {
    $cmb_temp = $1;
  };

  # Solo disponible cuando hay BD.
  if ($xml_data =~ /<_ART_AUTOINC>(.+?)<\/_ART_AUTOINC>/i) {
    $ART_AUTOINC = $1;
  };

  return $cmb_temp;

};

# ---------------------------------------------------------------
sub filtrar_templates {
# Deja en la combo solo los templates correspondientes al tipo de ficha,
# de acuerdo con %prontus_varglb::FORM_PLTS

# Parametros :
# 0) Cod. html correspondiente a la combo sin filtrar.
# 1) Nombre del archivo usado como ficha de articulo, sin path y con extension.

# Retorna la combo filtrada.

my ($combo_tpls, $ficha) = ($_[0], $_[1]);

my ($tpls_aux, %tpls_validos, $combo_aux, $tpl, $key);

  # Determinar tpls. validos.
  foreach $key (keys %prontus_varglb::FORM_PLTS) {
    # print STDERR "key[$key]";
    if ($key =~ /$ficha:.+/isg) {
      # print STDERR "key[$key]";
      my $templates = $prontus_varglb::FORM_PLTS{$key};

      if ($templates !~ /;/) {
        $tpls_validos{$prontus_varglb::FORM_PLTS{$key}} = 'filler';
      }
      else {
        # print STDERR "templates[$templates]";
        my @arr_tpls = split /;/, $templates;
        my $plt;
        foreach $plt (@arr_tpls) {
          # print STDERR "plt[$plt]";
          $tpls_validos{$plt} = 'filler';
        };
      };
    }
  }


  $combo_aux = $combo_tpls;


  # Recorro los elementos de la combo.
  while ($combo_tpls =~ m/<option value="(.*?)"/isg) {
    $tpl = $1;
    # print STDERR "\ntpl from combo[$tpl]";

    # Si el elemento de la combo no lo encuentro entre los tpls validos
    if (! exists $tpls_validos{$tpl}) {
      # Sacarlo de la combo
      $combo_aux =~ s/<option value="$tpl"\s*>.*?<\/option>//isg;
    }

  }

  return $combo_aux;

};
# ---------------------------------------------------------------
sub get_xml_data {
  # Cargar xml del articulo.

  # Sacar extension del articulo incluido el punto
  my ($path_final_xml) = $FORM{'_file'};
  $path_final_xml =~ s/\.\w*$//;
  # Agregar extension xml
  $path_final_xml .= '.xml';
  $path_final_xml = $prontus_varglb::DIR_SERVER .
                    $prontus_varglb::DIR_CONTENIDO .
                    $prontus_varglb::DIR_ARTIC .
                    "/$FORM{'_dir_fecha'}" .
                    '/xml' .
                    "/$path_final_xml";

  my $xml = &glib_fildir_02::read_file($path_final_xml);

  my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;

  $xml =~ s/$crlf/\x0a/sg;

  my ($priv, $pub);
  if ($xml =~ /<_PRIVATE>(.*?)<\/_PRIVATE>/isg) {
    $priv = $1;
  };
  if ($xml =~ /<_PUBLIC>(.*?)<\/_PUBLIC>/isg) {
    $pub = $1;
  };
  return "$priv\n$pub";
};
# ---------------------------------------------------------------
sub cargar_campos {

# Reemplaza las marcas de campo fijas de la ficha de articulo.
# Luego detecta los nombres de los controles del formulario y para c/u busca su equivalente
# del tipo <!--name--><!--/name--> dentro de la pag. del articulo correspondiente y luego
# los reemplaza en la ficha del articulo.

# Retorna la ficha con todas las marcas reemplazadas.

my ($dir_tpl_pags) = $_[0];
my ($html_tpag, $path_paso, $buf, $pag, $marca, %hash_val, $path_artic, @campos, $nom_campo, $valor_campo, $valor_campo_original, $text_artic, $text_artic_aux, $estilo, $delimitador_ini, $delimitador_fin, $head_artic, $relpath_foto, $nom_foto);
my ($base_path, $relbase_path, $base_path_mm, $relbase_path_mm, $campo, $nom);
my ($nom_seccion1, $nom_tema1, $nom_subtema1);

  # Cargar xml del articulo.
  my $xml_data = &get_xml_data();
  # print STDERR "xml_data[$xml_data]\n";

  # Cod html correspondiente a la combo de templates de articulos
  $html_tpag = &glib_html_02::generar_popup_from_dir($dir_tpl_pags, '_PLT', '', 1, '', 'SIN_EXT', '', '', 1000000, 'STRASC');

  # Filtrar lista de templates de acuerdo a los soportados por el tipo de ficha de articulo.
  $html_tpag = &filtrar_templates($html_tpag, $FORM{'_fid'});


  # Ahora posicionar combo en el tpl actual. spare
  my $tpl_actual = &get_template($xml_data);
  $html_tpag =~ s/(.*)selected(.*)/$1$2/is;
  $html_tpag =~ s/(.*)value *= *"$tpl_actual" *>(.*)/$1value="$tpl_actual" selected="selected">$2/is;

  # Cargar plantilla del FID
  $pag = &carga_buffer_fid($PATH_FICHA);


  $pag =~ s/%%_PLT%%/Plantilla :<br\/>$html_tpag/ig;
  $pag =~ s/%%_ART_AUTOINC%%/$ART_AUTOINC/ig;
  $pag =~ s/%%_ART%%/$FORM{'_file'}/ig;
  $pag =~ s/%%_CURR_BODY%%/$FORM{'_curr_body'}/ig;
  $pag =~ s/%%_port_dd%%/$FORM{'_port_dd'}/ig;
  my $cmb_multivistas;
  if (keys(%prontus_varglb::MULTIVISTAS)) {
    $cmb_multivistas = 'Vista: ' . &lib_prontus::generar_popup_multivistas();
  };
  $pag =~ s/%%_CMB_MV%%/$cmb_multivistas/ig;


  my $fid = $FORM{'_fid'};
  $fid =~ s/\.\w+$//; # borra extension
  my $hiddens = "<input type=\"hidden\" name=\"_file\" value=\"$FORM{'_file'}\" />\n"
              . "<input type=\"hidden\" name=\"_fid\" value=\"$fid\" />\n" # se pone porque no va la combo
              . "<input type=\"hidden\" name=\"_path_conf\" value=\"$FORM{'_path_conf'}\"/>\n";


  $pag =~ s/<form (.*?)>/<form $1>\n$hiddens/is;

  # Agrega el vtxt
  $pag = &add_vtxt($pag, $tpl_actual);

  $pag = &incluye_fechahora($pag);
  $pag = &incluye_nomseccs($pag);
  $pag = &incluye_fotosfijas($pag);

  $pag =~ s/%%_REL_PATH_PRONTUS%%/$prontus_varglb::RELDIR_BASE\/$prontus_varglb::PRONTUS_ID/ig;

  # reemplazar nombre del prontus
  $pag =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;

  # Mostrar glosa de tipo de articulo
  my $glosa_tipo_ficha = &get_glosa_tipo_ficha($FORM{'_fid'});
  $pag =~ s/%%_FID%%/FID:<br\/><div class="label-fid" title="$glosa_tipo_ficha">$glosa_tipo_ficha<\/div>/ig;


  $base_path = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . "/$FORM{'_dir_fecha'}";
  $base_path_mm = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_EXMEDIA . "/$FORM{'_dir_fecha'}";
  $relbase_path = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . "/$FORM{'_dir_fecha'}";
  $relbase_path_mm = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_EXMEDIA . "/$FORM{'_dir_fecha'}";

  my $size_html = -s "$base_path$prontus_varglb::DIR_PAG/$FORM{'_file'}";
  my $size_total = $size_html;
  my $relpath_artic = "$relbase_path$prontus_varglb::DIR_PAG/$FORM{'_file'}";

  $pag = &lib_prontus::replace_mtime($pag, "$base_path$prontus_varglb::DIR_PAG/$FORM{'_file'}");

  # Enmascara marcas Htmlfiles en el texto.
  $xml_data =~ s/<!--(HTMLFILE\w+?)-->/<!---$1--->/isg;
  $xml_data =~ s/<!--\/(HTMLFILE\w+?)-->/<!---\/$1--->/isg;

  my %fotos_icono;
  my %fotos_controls;
  my %fotos_hidden;
  my %fotos_loop;
  my %fotos_size;

  my $titular; # se rescata mas abajo
  my $ts = $FORM{'_file'};
  $ts =~ s/\.[\w\-]*$//; # saca extension


  # se lee plantilla para banco de imagenes
  my $tplBancoImg = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/fid/macro_banco_imagenes.html";
  my $tplBancoImg2 = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/fid/macro_banco_imagenes_noimg.html";
  my $moldeBancoImg = &glib_fildir_02::read_file($tplBancoImg);
  my $moldeBancoImg2 = &glib_fildir_02::read_file($tplBancoImg2);
  # se reemplazan los datos comunes
  $moldeBancoImg =~ s/%%ts%%/$ts/ig;
  $moldeBancoImg =~ s/%%path_conf%%/$FORM{'_path_conf'}/ig;

  while ($xml_data =~ /<(\w+?)>(.*?)<\/\1>/sg) {
    $nom_campo = $1;
    $valor_campo = $2;
    #~ print STDERR "nom_campo[$nom_campo] - valor_campo[$valor_campo]\n";

    if ($nom_campo =~ /^RDO_\w+/i) {
      if ($valor_campo =~ /<!\[CDATA\[(.*?)\]\]>/isg) {
        $valor_campo = $1;
      };
      $pag =~ s/%%$nom_campo%%/$valor_campo/ig;
      $pag = &procesar_obj_seleccion($pag, 'radio',$nom_campo,$valor_campo);
    }
    # alta control
    elsif ($nom_campo =~ /^_ALTA/i) {
      if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS eq 'SI') {
        my $alta_control = '<label for="_alta">Alta de art&iacute;culo:</label> <input type="checkbox" id="_alta" name="_ALTA" value="1" %%_ALTA%% />';

        my $status;
        if ($prontus_varglb::USERS_PERFIL eq 'P') { # para periodistas aparece disabled
          $alta_control .= '<input type="hidden" name="_ALTA" ' . " value=\"$valor_campo\" />";
          $status = 'disabled="disabled"';
        };
        if ($valor_campo eq '1') {
          $alta_control =~ s/%%_ALTA%%/checked="checked" $status/ig;
        }
        else {
          $alta_control =~ s/%%_ALTA%%/$status/ig;
        };
        $pag =~ s/%%_ALTA%%/$alta_control/ig;
      }
      else {
        $pag =~ s/%%_ALTA%%//ig;
      };
    }

    # solo portadas
    elsif ($nom_campo =~ /^_SOLOPORTADAS/i) {
      if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
        if ($valor_campo eq '1') {
          $pag =~ s/%%_SOLOPORTADAS%%/ checked="checked"/ig;
        }
        else {
          $pag =~ s/%%_SOLOPORTADAS%%//ig;
        };
      }
      else {
        $pag =~ s/%%_SOLOPORTADAS%%//ig;
      };
    }


    elsif ($nom_campo =~ /^CHK_\w+/i) {
      if ($valor_campo =~ /<!\[CDATA\[(.*?)\]\]>/isg) {
        $valor_campo = $1;
      };
      $pag =~ s/%%$nom_campo%%/$valor_campo/ig;
      $pag = &procesar_obj_seleccion($pag, 'checkbox',$nom_campo,$valor_campo);
    }
    elsif ($nom_campo =~ /^CMB_\w+/i) {
      if ($valor_campo =~ /<!\[CDATA\[(.*?)\]\]>/isg) {
        $valor_campo = $1;
      };
      $pag =~ s/%%$nom_campo%%/$valor_campo/ig;
      $pag = &procesar_select($pag,$nom_campo,$valor_campo);
    }
    elsif ($nom_campo =~ /^_SECCION(\d)/i) {
      $ID_SECCIONES{'_SECCION' . $1} = $valor_campo;
    }
    elsif ($nom_campo =~ /^_TEMA(\d)/i) {
      $ID_TEMAS{'_TEMA' . $1} = $valor_campo;
    }
    elsif ($nom_campo =~ /^_SUBTEMA(\d)/i) {
      $ID_SUBTEMAS{'_SUBTEMA' . $1} = $valor_campo;
    }
    elsif ($nom_campo =~ /^_nom_seccion1/i) { # rescatar nombre seccion, tema y subtema para friendly url.
        $nom_seccion1 = $valor_campo;
        #~ print STDERR "nom_seccion1[$valor_campo]\n";
    }
    elsif ($nom_campo =~ /^_nom_tema1/i) {
        $nom_tema1 = $valor_campo;
        #~ print STDERR "nom_tema1[$valor_campo]\n";
    }
    elsif ($nom_campo =~ /^_nom_subtema1/i) {
        $nom_subtema1 = $valor_campo;
        #~ print STDERR "nom_subtema1[$valor_campo]\n";
    }
    elsif ($nom_campo =~ /^VTXT_/i) {
      if ($valor_campo =~ /<!\[CDATA\[(.*?)\]\]>/isg) {
        $valor_campo = $1;
        if($prontus_varglb::VTXT_ENCODE_CHARS eq 'SI') {
          $valor_campo =~ s/&lt;/&lt; /g;
          $valor_campo =~ s/&gt;/ &gt;/g;
        }
        $valor_campo = &lib_prontus::escape_html($valor_campo); # para preservar entidades html

         #print STDERR "$valor_campo\n";
        $valor_campo =~ s/%%/&#37;&#37;/sg; # Enmascara para preservar %%
        $pag =~ s/%%$nom_campo%%/$valor_campo/ig;
      };
    }
    elsif ($nom_campo =~ /^_?TXT_/i) {
      if ($valor_campo =~ /<!\[CDATA\[(.*?)\]\]>/isg) {
        $valor_campo_original = $1;
        # Dentro del buffer se sustituyen los segmentos html por marcas del tipo %%HTML[1]%%
        # las que despues de los 'unformats' seran sustituidas por los contenidos reales. # 1.8
        # $pag = &parse_text($pag, $nom_campo, $valor_campo);
        $valor_campo = &lib_prontus::escape_html($valor_campo_original); # para preservar entidades html

        # print STDERR "[$nom_campo]: $valor_campo\n";
        $valor_campo =~ s/%%/&#37;&#37;/sg; # Enmascara para preservar %%
        $pag =~ s/%%$nom_campo%%/$valor_campo/ig;
        $titular = $valor_campo_original if (lc $nom_campo eq '_txt_titular'); # se guarda el titular original sin escapear para generar la frinedly url correctamente

      };
    }

      # ----------
    # Rescatar Fotografias.
    elsif ($nom_campo =~ /^(foto_\w+)/i) {

      my $wfoto;
      my $hfoto;
      # Rescatar anchos de fotos
      if ($valor_campo =~ /<(_w$nom_campo)>(.+?)<\/\1>/i) {
        $wfoto = $2;
        $campo = $1;
        my $valor = '<input type="hidden" name="' . $campo . '" value="'. $wfoto . '" />';
        $pag =~ s/<form (.*?)>/<form $1>\n$valor/is;
      };

      # Rescatar altos de fotos.
      if ($valor_campo =~ /<(_h$nom_campo)>(.+?)<\/\1>/i) {
        $hfoto = $2;
        $campo = $1;

        my $valor = '<input type="hidden" name="' . $campo . '" value="'. $hfoto . '" />';
        $pag =~ s/<form (.*?)>/<form $1>\n$valor/is;
      };

      $fotos_size{$nom_campo}{'w'} = $wfoto;
      $fotos_size{$nom_campo}{'h'} = $hfoto;

      if ($valor_campo =~ /<(_nom$nom_campo)>(.+?)<\/\1>/i) {
        next if (lc $nom_campo eq 'foto_n'); # --> producto de un prb en la glib es posible que hayan fotos fantasma en el xml
        $nom_foto = $2;

        my $bytes_foto = -s $base_path . $prontus_varglb::DIR_IMAG . "/$nom_foto";       # 1.9
        $size_total += $bytes_foto;
        my $kbytes_foto = &lib_prontus::bytes2kb($bytes_foto, 0);

        # CVI - 10/03/2011 - Se cambia sistema para evitar cache del browser, aplicando el random al nombre de la foto
        $relpath_foto = $relbase_path . $prontus_varglb::DIR_IMAG . "/" . $nom_foto;

        # Se parsean los campos principales
        my $bufferBancoImg = $moldeBancoImg;
        $bufferBancoImg =~ s/%%nom_campo%%/$nom_campo/ig;
        $bufferBancoImg =~ s/%%nom_foto%%/$nom_foto/ig;
        $bufferBancoImg =~ s/%%relpath_foto%%/$relpath_foto/ig;
        $bufferBancoImg =~ s/%%relpath_foto%%/$relpath_foto/ig;
        $bufferBancoImg =~ s/%%wfoto%%/$wfoto/ig;
        $bufferBancoImg =~ s/%%hfoto%%/$hfoto/ig;

        # Para los campos hidden de las fotos que no se desplegaran
        my $bufferBancoImg2 = $moldeBancoImg2;
        $bufferBancoImg2 =~ s/%%nom_campo%%/$nom_campo/ig;
        $bufferBancoImg2 =~ s/%%nom_foto%%/$nom_foto/ig;
        $bufferBancoImg2 =~ s/%%relpath_foto%%/$relpath_foto/ig;
        $bufferBancoImg2 =~ s/%%wfoto%%/$wfoto/ig;
        $bufferBancoImg2 =~ s/%%hfoto%%/$hfoto/ig;

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
        $fotos_hidden{$nom_campo} = $bufferBancoImg2;

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

      # Pies
      if ($valor_campo =~ /<(_TXT_P$nom_campo)>(.+?)<\/\1>/i) {
        $campo = $1;
        my $foot = $2;
        if ($foot =~ /<!\[CDATA\[(.*?)\]\]>/i) {
          $foot = $1;
        };
        $pag = &parse_text($pag, $campo, $foot);
      };

    }

    # Parsear las fotos fijas en los divs
    elsif ($nom_campo =~ /^FOTOFIJA_\w+/i) {
      if ($valor_campo =~ /<!\[CDATA\[(.*?)\]\]>/i) {
        $valor_campo = $1;
      };
      # warn "nom_campo[$nom_campo] - valor_campo[$valor_campo] path[$base_path$prontus_varglb::DIR_IMAG]";
      if ($valor_campo =~ /$relbase_path$prontus_varglb::DIR_IMAG\/(foto_\w+)\d{14}/i)  {
        my $nom_foto_fija = $1;
        # warn "nom_foto_fija[$nom_foto_fija]";
        my $foto_fija_aux = $fotos_icono{$nom_foto_fija};
        # warn "foto_fija_aux[$foto_fija_aux]";
        $foto_fija_aux =~ s/ondblclick *= *".+?"//isg;
        $foto_fija_aux =~ s/\n|\r/ /isg;

        my $protocolo = 'http';
        if($prontus_varglb::SERVER_PROTOCOLO_HTTPS eq 'SI') {
            $protocolo = 'https';
        }
        $foto_fija_aux =~ s/src="/src="$protocolo:\/\/$prontus_varglb::IP_SERVER/isg;
        $foto_fija_aux =~ s/"/' \+ String.fromCharCode\(34\) \+ '/isg;
        $pag =~ s/%%_DIV_$nom_campo%%/$foto_fija_aux/ig;
        $pag =~ s/%%$nom_campo%%/$valor_campo/ig; # para el ver imagen

        #~ print STDERR "nom_campo[$nom_campo] nom_foto_fija[$nom_foto_fija] |$fotos_size{$nom_foto_fija}{'w'}\n";

        $pag =~ s/%%_W$nom_campo%%/$fotos_size{$nom_foto_fija}{'w'}/ig;
        $pag =~ s/%%_H$nom_campo%%/$fotos_size{$nom_foto_fija}{'h'}/ig;

      }
      elsif ($valor_campo =~ /^http/i) { # foto externa
        my $img_tag = "<img src=\"$valor_campo\" border=\"0\" name=\"FOTO_EXTERNA\" />";
        $img_tag =~ s/"/' \+ String.fromCharCode\(34\) \+ '/isg;
        # my $img_tag = $valor_campo;
        $pag =~ s/%%_DIV_$nom_campo%%/$img_tag/ig;
        $pag =~ s/%%$nom_campo%%/$valor_campo/ig; # para el ver imagen
      }
      else {
        $pag =~ s/%%_DIV_$nom_campo%%//ig;
        $pag =~ s/%%$nom_campo%%/javascript:void\(0\)" onClick="return false/ig; # para el ver imagen
      };

    }

    # Rescatar arch. multimedia
    elsif ($nom_campo =~ /^MULTIMEDIA_\w+/i) {
      my ($relpath_mm);
      $nom = $valor_campo;
      $relpath_mm = $relbase_path_mm . $prontus_varglb::DIR_MMEDIA . "/$nom";

      my $bytes = -s $base_path_mm . $prontus_varglb::DIR_MMEDIA . "/$nom";
      $size_total += $bytes;
      my $kbytes = &lib_prontus::bytes2kb($bytes, 0);
      $valor_campo = '<a href="' . $relpath_mm . '" target="_blank">Reproducir Archivo Actual</a>' . " ($kbytes)" . '&nbsp;&nbsp;<label for="_BORR_' . $nom_campo . '">Borrar</label><input type="checkbox" value="S" name="_BORR_' . $nom_campo . '" id="_BORR_' . $nom_campo . '" />';
      $valor_campo .= '<input type="hidden" name="_HIDD_' . $nom_campo . '" value="' . $nom .  '" />';
      $marca ='%%' . $nom_campo . '%%';
      $pag =~ s/$marca/$valor_campo/ig;
    }

    # Rescatar arch. generico asociado
    elsif ($nom_campo =~ /^(ASOCFILE_\w+|_gal_archive)/i) {
        $valor_campo =~ s/[\n\r]+//sg;
        next if ($valor_campo eq '');
        $nom = $valor_campo;
        my $relpath_af = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EXASOCFILE/$FORM{'_dir_fecha'}$prontus_varglb::DIR_ASOCFILE/$ts/$nom";
        my $bytes = -s "$prontus_varglb::DIR_SERVER$relpath_af";
        $size_total += $bytes;
        my $kbytes = &lib_prontus::bytes2kb($bytes, 0);
        $valor_campo = '<a href="' . $relpath_af . '" target="_blank">' . $nom . '</a>' . " ($kbytes)" . '&nbsp;&nbsp;<label for="_BORR_' . $nom_campo . '">Borrar</label> <input type="checkbox" value="S" name="_BORR_' . $nom_campo . '" id="_BORR_' . $nom_campo . '" />'; # 7.0
        $valor_campo .= '<input type="hidden" name="_HIDD_' . $nom_campo . '" value="' . $nom .  '" />';
        $marca = '%%' . $nom_campo . '%%';
        $pag =~ s/$marca/$valor_campo/ig;
    }

    # Rescatar htmlfiles
    elsif ($nom_campo =~ /^HTMLFILE_\w+/i) {
        $nom = $valor_campo;

        my $relpath_af = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EXASOCFILE/$FORM{'_dir_fecha'}$prontus_varglb::DIR_ASOCFILE/$nom";
        my $bytes = -s "$prontus_varglb::DIR_SERVER$relpath_af";
        $size_total += $bytes;

        $valor_campo = '<a href="' . $relpath_af . '" target="_blank">Ver HTMLFILE actual</a>&nbsp;&nbsp;Borrar<input type="checkbox" value="S" name="_BORR_' . $nom_campo . '" />'; # 7.0
        $valor_campo .= '<input type="hidden" name="_HIDD_' . $nom_campo . '" value="' . $nom .  '"/>';
        $marca ='%%' . $nom_campo . '%%';
        $pag =~ s/$marca/$valor_campo/ig;
    }


    # Rescatar swf
    elsif ($nom_campo =~ /^SWF_\w+/isg) {
      $nom = $valor_campo;
      my $relpath_swf = $relbase_path . $prontus_varglb::DIR_SWF . "/$nom";

      my $bytes = -s $base_path . $prontus_varglb::DIR_SWF . "/$nom";
      $size_total += $bytes;
      my $kbytes = &lib_prontus::bytes2kb($bytes, 0);
      $valor_campo = '<a href="' . $relpath_swf . '" target="_blank">Swf actual</a>' . " ($kbytes)" . '&nbsp;&nbsp;Borrar<input type="checkbox" value="S" name="_BORR_' . $nom_campo . '"/>';
      $valor_campo .= '<input type="hidden" name="_HIDD_' . $nom_campo . '" value="' . $nom .  '"/>';

      # ---- Imprime advertencia en rojo en caso de que el peso de la swf exceda el limite establecido.
      # El limite se establece por c/swf en el formulario, de la forma <!--SWF1_MAXBYTES=1500-->.
      my $bytes_swf = -s $base_path . $prontus_varglb::DIR_SWF . "/$nom";
      my $maxbytes = 0;
      if ($pag =~ /%%$nom_campo\_MAXBYTES\s*=\s*(\d+?)\s*%%/) {
        $maxbytes = $1;
        if ($bytes_swf > $maxbytes) {
          $valor_campo .=   '<br/><span color="#CC0000">¡Advertencia! Peso de archivo swf excede límite permitido</span>';
        };
      };
      # ----------

      $marca ='%%' . $nom_campo . '%%';
      $pag =~ s/$marca/$valor_campo/ig;
    }


    # rescatar user_id del articulo y ponerlo en un hidden en la ficha, a continuacion del tag form.
    elsif (uc $nom_campo eq '_USERS_ID') {

      if ($valor_campo eq '') { $valor_campo = $prontus_varglb::USERS_ID;}; # 8.0 para compatibilidad con p7
      my $hidd_user = '<input type="hidden" name="_USER_ID" value="' . $valor_campo . '"/>';
      $pag =~ s/<form (.*?)>/<form $1>\n$hidd_user/is;
    }
    else {
      # campos normales
      if ($valor_campo =~ /<!\[CDATA\[(.*?)\]\]>/is) {
        $valor_campo = $1;
      };
      # es necesario escapearlos porque los guardo tal cual

      $valor_campo = &lib_prontus::escape_html($valor_campo);
      $pag =~ s/%%$nom_campo%%/$valor_campo/isg;
    };
  };# while

  # Reemplaza fotos en el banco de imagenes
  my $nro_fotos_banco;
  foreach $nom_campo (sort {$b cmp $a} keys %fotos_controls) {

    if($nro_fotos_banco >= $prontus_varglb::BANCO_IMG_MAX) {
    my $valor_campo = $fotos_hidden{$nom_campo};
    $pag =~ s/%%_HIDDEN_FOTOS%%/$valor_campo%%_HIDDEN_FOTOS%%/ig;
        $nro_fotos_banco++;
        next;
    };

    # Rescata loop para fotos
    my ($loop_fotos, $loop_fotos_result);
    if ($pag =~ /%%LOOP_FOTOS%%(.*?)%%\/LOOP_FOTOS%%/is) {
      $loop_fotos = $1;
    };

    # print STDERR "nom_campo[$nom_campo]\n";
    $loop_fotos_result = "$loop_fotos\n";
    $loop_fotos_result =~ s/FOTO_N/$nom_campo/ig;
    $pag =~ s/%%LOOP_FOTOS%%$loop_fotos%%\/LOOP_FOTOS%%/$loop_fotos_result%%LOOP_FOTOS%%$loop_fotos%%\/LOOP_FOTOS%%/is;

    $marca ='%%' . $nom_campo . '%%';
    $valor_campo = $fotos_controls{$nom_campo};
    $pag =~ s/$marca/$valor_campo/ig;

    $nro_fotos_banco++;
  };


  foreach $nom_campo (sort {$b cmp $a} keys %fotos_icono) {
    $marca ='%%' . $nom_campo . '_ICONO%%';
    $valor_campo = $fotos_icono{$nom_campo};
    $pag =~ s/$marca/$valor_campo/ig;
  };

  # Para el total de imagenes del banco de imagenes
  my $txt_total_fotos;
  $txt_total_fotos = "Total de im&aacute;genes: $nro_fotos_banco" if ($nro_fotos_banco);
  $pag =~ s/%%TOTAL_BANCO_IMAGENES%%/$txt_total_fotos/ig;
  $pag =~ s/%%NRO_TOTAL_BANCO_IMAGENES%%/$nro_fotos_banco/ig;

  # Para el mensaje de que faltan imagenes
  if($nro_fotos_banco > $prontus_varglb::BANCO_IMG_MAX) {
    $pag =~ s/<!--vermas imagenes-->(.*?)<!--\/vermas imagenes-->/$1/isg;
    my $resto = $nro_fotos_banco - $prontus_varglb::BANCO_IMG_MAX;
    my $texto = "Mostrar <b>$resto</b> im&aacute;genes restantes";
    $texto = "Mostrar <b>1</b> imagen restante" if($resto == 1);
    $pag =~ s/%%TEXTO_RESTANTES%%/$texto/isg;

  } else {
    $pag =~ s/<!--vermas imagenes-->(.*?)<!--\/vermas imagenes-->//isg;

  }

  # Finalmente se borra el Loop y el Hidden
  $pag =~ s/%%LOOP_FOTOS%%.*?%%\/LOOP_FOTOS%%//isg;
  $pag =~ s/%%_HIDDEN_FOTOS%%//isg;

  $size_html = &lib_prontus::bytes2kb($size_html, 0);
  $size_total = &lib_prontus::bytes2kb($size_total, 0);

  $pag =~ s/%%_SIZE_HTML%%/$size_html/isg;
  $pag =~ s/%%_SIZE_TOTAL%%/$size_total/isg;

  # pagspar
  my $fullpath_pagspar = $relpath_artic;
  $fullpath_pagspar =~ s/^(.*?)\/pags\/(\d{14})\.(\w+)$/$1\/pagspar\/$2_\*/isg;
  my @pagspar = glob("$prontus_varglb::DIR_SERVER$fullpath_pagspar");
  if (scalar @pagspar) {
    my $list_pagspar;
    foreach my $file (@pagspar) {
        $file =~ s/^$prontus_varglb::DIR_SERVER//isg;
        $list_pagspar .= "$file\n";
    };
    $pag =~ s/%%_pagspar%%/$list_pagspar/isg;
  } else {
    $pag =~ s/<!--list_pagspar-->.*?<!--\/list_pagspar-->//isg;
  };

    my $nom_seccion = $TABLA_SECC{$ID_SECCIONES{'_SECCION1'}}{'nombre'};
    my $nom_tema = $TABLA_TEMAS{$ID_TEMAS{'_TEMA1'}}{'nombre'};
    my $nom_subtema = $TABLA_SUBTEMAS{$ID_SUBTEMAS{'_SUBTEMA1'}}{'nombre'};

    my $fileurl = &lib_prontus::parse_filef('%%_fileurl%%', $titular, $ts, $prontus_varglb::PRONTUS_ID, $relpath_artic, $nom_seccion, $nom_tema, $nom_subtema);
    print STDERR "Editar: $titular, $ts, $prontus_varglb::PRONTUS_ID, $relpath_artic, $fileurl\n";

    $pag =~ s/%%_fileurl%%/$fileurl/ig;
    if ($prontus_varglb::FRIENDLY_URLS eq 'SI') {
        $pag =~ s/%%_fileurlinfo%%/$fileurl/ig;
    } else {
        $pag =~ s/%%_fileurlinfo%%/Friendly URLs no se encuentran activadas/ig;
    }

  if ($prontus_varglb::USAR_PUBLIC_SERVER_NAME_VER_ARTIC eq 'SI') {
    my $protocolo = "http";
    $protocolo = "https" if ($prontus_varglb::SERVER_PROTOCOLO_HTTPS eq 'SI');
    $pag =~ s/%%_fileurl_abs%%/$protocolo:\/\/$prontus_varglb::PUBLIC_SERVER_NAME$fileurl/ig;
  } else {
    $pag =~ s/%%_fileurl_abs%%/$fileurl/ig;
  };

  $pag = &lib_prontus::parse_includes($prontus_varglb::DIR_SERVER, $pag);
  return $pag;

};

# ---------------------------------------------------------------
sub incluye_fechahora {
  my $buffer = $_[0];
  my $fechahora = '<table class="fechahora" cellpadding="0" cellspacing="0"><tr><td><span class="titulo">Publicaci&oacute;n:&nbsp;</span></td>
          <td><input type="text" name="_FECHAPSHRT" size="12" value="%%_FECHAPSHRT%%" class="fieldform fecha" maxlength="10" />&nbsp;</td>
          <td><input type="text" name="_HORAP" size="6" value="%%_HORAP%%" class="fieldform hora" maxlength="5" /> hrs
          <input type="hidden" name="_FECHAP" value="%%_FECHAP%%" /></td>
          <td><div class="actualizar" title="Actualiza Fecha/Hora de Publicaci&oacute;n por la hora Fecha/Hora actual" onclick="Fid.actualizaFechaHora(\'pub\');">&nbsp;</div></td></tr>';
  if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
    $fechahora .= '<tr><td><span class="titulo">Expiraci&oacute;n:&nbsp;</span></td>
           <td><input type="text" name="_FECHAESHRT" size="12" value="%%_FECHAESHRT%%"  class="fieldform fecha" maxlength="10" />&nbsp;</td>
           <td><input type="text" name="_HORAE" size="6" value="%%_HORAE%%" class="fieldform hora" maxlength="5" /> hrs
               <input type="hidden" name="_FECHAE" value="%%_FECHAE%%" /></td>
           <td><div class="actualizar" title="Actualiza Fecha/Hora de Expiraci&oacute;n por la hora Fecha/Hora actual" onclick="Fid.actualizaFechaHora(\'exp\');">&nbsp;</div></td></tr>
           <tr><td colspan="4">
               <div class="check-item"><label for="_soloportadas">S&oacute;lo despublicar de portadas:</label> <input type="checkbox" id="_soloportadas" name="_SOLOPORTADAS" value="1" %%_SOLOPORTADAS%% /></div></td></tr>';
  };
  $fechahora .= '</table>';
  $buffer =~ s/%%_FECHAHORA%%/$fechahora/i;
  return $buffer;
};
# ---------------------------------------------------------------
sub incluye_nomseccs {
  my $buffer = $_[0];
  my $nomseccs = '
<input type="hidden" name="_NOM_SECCION1" value="%%_NOM_SECCION1%%" />
<input type="hidden" name="_NOM_TEMA1" value="%%_NOM_TEMA1%%" />
<input type="hidden" name="_NOM_SUBTEMA1" value="%%_NOM_SUBTEMA1%%" />

<input type="hidden" name="_NOM_SECCION2" value="%%_NOM_SECCION2%%" />
<input type="hidden" name="_NOM_TEMA2" value="%%_NOM_TEMA2%%" />
<input type="hidden" name="_NOM_SUBTEMA2" value="%%_NOM_SUBTEMA2%%" />

<input type="hidden" name="_NOM_SECCION3" value="%%_NOM_SECCION3%%" />
<input type="hidden" name="_NOM_TEMA3" value="%%_NOM_TEMA3%%" />
<input type="hidden" name="_NOM_SUBTEMA3" value="%%_NOM_SUBTEMA3%%" />
';

  $buffer =~ s/<form (.*?)>/<form $1>\n$nomseccs\n/is;

  return $buffer;
};

# ---------------------------------------------------------------
sub parse_text {
  my ($pag, $nom_campo, $valor_campo) = @_;

  my $i = 0;
  my $conten = '';
  my @html_puro = ();
  my $valor_campo_aux = $valor_campo;

  # Sustituir valor en la ficha.

  my $marca ='%%' . $nom_campo . '%%';
  $pag =~ s/$marca/$valor_campo/ig;

  return $pag;
};


# ---------------------------------------------------------------
sub procesar_obj_seleccion {
  my $pag = $_[0];
  my $tipo = $_[1];
  my $nom_campo = $_[2];
  my $valor_campo = $_[3];
  my $pag_aux = $pag;
  while ($pag_aux =~ /(<input +([^>]+ +)?type *= *['"]$tipo['"] +([^>]+?)?>)/isg) {
    my $tag = $1;
    #print STDERR "\n\n\n\n\ntag[$tag] FOUND\n";
    my $parte1 = $2;
    my $parte2 = $3;
    if (($parte1 =~ /name *= *['"]$nom_campo['"]/is) or ($parte2 =~ /name *= *['"]$nom_campo['"]/is)) { # ubica control con nombre correspondiente.

      if (($parte1 =~ /value *= *['"]$valor_campo['"]/is) or ($parte2 =~ /value *= *['"]$valor_campo['"]/is)) { # chequea si el value calza.

        # Compone el tag.
        $tag =~ /^(<.+?)\/?>$/;

        #~ my $tag_aux = $1;
        my $tag_original = $tag;
        #$tag =~ s/>$/$tag_aux checked \/>/is;
        $tag =~ s/(\/?>)$/ checked="checked" $1/is;
        $pag =~ s/$tag_original/$tag/is;
      };
    };
  };
  return $pag;
};
# ---------------------------------------------------------------
sub procesar_select {
  my $pag = $_[0];
  my $tipo = 'select';
  my $nom_campo = $_[1];
  my $valor_campo = $_[2];
  my $pag_aux = $pag;
  while ($pag_aux =~ /(<select +([^>]+ *)>.+?<\/select *>)/isg) {
    my $tag = $1;
    my $parte1 = $2;
    if ($parte1 =~ /name *= *['"]$nom_campo['"]/is) { # ubica control con nombre correspondiente.
      my $tag_original = $tag;

      # remueve actual seleccionado en caso de haberlo.
      # CVI - 17/01/2014 - Se robustece la expresión regular
      #~ $tag =~ s/(.*)selected(.*)/$1$2/is;
      $tag =~ s/(.*)selected(="selected")?(.*)/$1$3/is;

      # Posiciona en el option correspondiente
      # CVI - 17/01/2014 - Se robustece la expresión regular
      #~ $tag =~ s/(.*)value *= *["']$valor_campo["'] *>(.*)/$1value="$valor_campo" selected="selected">$2/is;
      #~ $pag =~ s/$tag_original/$tag/is;
      $tag =~ s/ value *= *["']$valor_campo["']([^>]*>)/ value="$valor_campo" selected="selected"$1/is;
      $pag =~ s/\Q$tag_original\E/$tag/is;

    };
  };
  return $pag;

};
# -------------------------------------------------------------------------#
sub add_vtxt {
  # Incluye en el fid el vtxt

  my ($textpag) = $_[0];
  my ($tpl_artic) = $_[1];

  my ($include4vtxt) = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/vtxt/include_common.html";

  $include4vtxt = &glib_fildir_02::read_file($include4vtxt);

  #~ Lee la plantilla del artículo para distintas tareas
  my $path_tpl = $prontus_varglb::DIR_SERVER .
             $prontus_varglb::DIR_TEMP .
             $prontus_varglb::DIR_ARTIC .
             $prontus_varglb::DIR_FECHA .
             $prontus_varglb::DIR_PAG . "/$tpl_artic";
  my $buffer = &glib_fildir_02::read_file($path_tpl);
  my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
  $buffer =~ s/$crlf/\x0a/sg;
  $buffer =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg; # a pedido del publico

  #~ Carga los css desde la plantilla del artículo
  my $include_css = "$prontus_varglb::DIR_CORE/vtxt/editor/plugins/insert/css/content.css";
  my $path_css_artic = &get_css_artic($path_tpl, $buffer);
  if($path_css_artic) {
    $path_css_artic = "$include_css,$path_css_artic";
  } else {
    $path_css_artic = "$include_css";
  }

  # estilos para mejorar usabilidad de editor vtxt
  $path_css_artic = "$path_css_artic,$prontus_varglb::DIR_CORE/vtxt/css/vtxt_extras.css";

  $include4vtxt =~ s/%%_PATH_CSS_ARTIC%%/$path_css_artic/isg;

  my $data_include_type = &get_include_artic($path_tpl, $buffer);
  $include4vtxt =~ s/%%_data_include_type%%/$data_include_type/isg;


  if ($prontus_varglb::VTXT_PASTE_NEWLINES_AS_P eq 'SI') {
    $include4vtxt =~ s/%%_VTXT_PASTE_NEWLINES_AS_P%%/1/isg;
  } else {
    $include4vtxt =~ s/%%_VTXT_PASTE_NEWLINES_AS_P%%/0/isg;
  };

  if ($prontus_varglb::VTXT_MEDIA_SCRIPT eq 'SI') {
    $include4vtxt =~ s/%%_VTXT_MEDIA_SCRIPT%%/true/isg;
  } else {
    $include4vtxt =~ s/%%_VTXT_MEDIA_SCRIPT%%/false/isg;
  };


  my $custom_estilos = &get_custom_estilos($path_css_artic, 'vtxt');
  $include4vtxt =~ s/%%_CUSTOM_ESTILOS%%/$custom_estilos/isg;

  my $custom_estilos_table = &get_custom_estilos($path_css_artic, 'vtxt_table');
  $custom_estilos_table = $custom_estilos if (!$custom_estilos_table);
  $include4vtxt =~ s/%%_CUSTOM_ESTILOS_TABLE%%/$custom_estilos_table/isg;

  my $custom_estilos_tr = &get_custom_estilos($path_css_artic, 'vtxt_tr');
  $custom_estilos_tr = $custom_estilos if (!$custom_estilos_tr);
  $include4vtxt =~ s/%%_CUSTOM_ESTILOS_TR%%/$custom_estilos_tr/isg;

  my $custom_estilos_td = &get_custom_estilos($path_css_artic, 'vtxt_td');
  $custom_estilos_td = $custom_estilos if (!$custom_estilos_td);
  $include4vtxt =~ s/%%_CUSTOM_ESTILOS_TD%%/$custom_estilos_td/isg;

  my $custom_estilos_img = &get_custom_estilos($path_css_artic, 'vtxt_img');
  $custom_estilos_img = $custom_estilos if (!$custom_estilos_img);
  $include4vtxt =~ s/%%_CUSTOM_ESTILOS_IMG%%/$custom_estilos_img/isg;

  if ($prontus_varglb::VTXT_DTD eq 'TRANSITIONAL') {
    $include4vtxt =~ s/<!--STRICT-->.*?<!--\/STRICT-->//sg;
    $include4vtxt =~ s/<!--\/?TRANSITIONAL-->//g;
    $include4vtxt =~ s/%%_DTD%%/XHTML 1.0 Transitional/g;

  }
  else {
    $include4vtxt =~ s/<!--TRANSITIONAL-->.*?<!--\/TRANSITIONAL-->//sg;
    $include4vtxt =~ s/<!--\/?STRICT-->//g;
    $include4vtxt =~ s/%%_DTD%%/XHTML 1.0 Strict/g;
  };


  my $bodys_style;
  if ($ENV{'HTTP_USER_AGENT'} =~ /Gecko/) {
    $bodys_style = '<style>.BODYS {position:absolute;left:-600px;width:570px;visibility:hidden;}</style>';
  }
  else {
    $bodys_style = '<style>.BODYS {display:none;width:570px;}</style>';
  };

  $textpag =~ s/%%_BODYS_STYLE%%/$bodys_style/i;

  $textpag =~ s/%%_INIT_VTXT%%/$include4vtxt/i;

  $textpag =~ s/%%_PATH_CSS_ARTIC%%/$path_css_artic/isg;


  return $textpag;

};
# -------------------------------------------------------------------------#
sub incluye_fotosfijas {
  # Incluye html para fotos fijas en el fid

  my ($textpag) = $_[0];


  my ($tpl_ff) = &glib_fildir_02::read_file($prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/fid/include_fotofija.html");
  # print STDERR "textpag[$textpag]\n";
    my $textpag_aux = $textpag;
    while ($textpag_aux =~ /%%FOTOFIJA_(\w+?)\((\d+) *\, *(\d+)\)%%/isg) { # %%FOTOFIJA_ART(w,h)%%

        my ($name) = $1;
        my ($w) = $2;
        my ($h) = $3;
        my ($bloque_ff) = $tpl_ff;
        # print STDERR "name[$name]\n";
        $bloque_ff =~ s/##name##/$name/ig;
        $bloque_ff =~ s/##w##/$w/ig;
        $bloque_ff =~ s/##h##/$h/ig;
        $textpag =~ s/%%FOTOFIJA_$name\($w *, *$h\)%%/$bloque_ff/ig;
    };

  return $textpag;

};
# -------------------------------------------------------------------------#
sub get_custom_estilos {
  # Obtiene todos los estilos que aparezcan marcados entre /*vtxt*/ y /*/vtxt*/ o similar
  # en todos los .css detectados.
  my $lista_css = $_[0]; # p ej.: /prontus_dev/css/articulo.css,/prontus_dev/css/global.css
  my $tipo = $_[1];
  my @css = split(/\,/, $lista_css);
  my $k;
  my $estilos;
  my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
  # Primero rescatar los segmentos marcados dentro de los .css
  foreach $k (@css) {
    $k =~ s/\,//g;
    next if (!$k); # 100.2
    next if ($k =~ /^http/);
    # print STDERR "k[$prontus_varglb::DIR_SERVER$k]\n";
    my $buf = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$k");

    $buf =~ s/$crlf/\x0a/sg;


    if ($buf =~ /\/\*$tipo\*\/(.+?)\/\*\/$tipo\*\//is) {
      $estilos .= "\n$1";
    };
  };

  # print STDERR "estilos[$estilos]\n";

  # Segundo, disponerlos a la manera requerida por el control vtxt, donde cada uno
  # va por ejemplo asi:
  # "subtit" : "subtit","rojo" : "rojo"
  my $plt_estilos_vtxt = "%%nom_estilo%%=%%nom_estilo%%;";
  # my $estilos_vtxt = "'Normal' : '',";
  my $estilos_vtxt;
  my %estilos_incluidos;
  while ($estilos =~ /(\w+[\w\-]*?)[ \n]*?(\/\*.*?\*\/)?[ \n]*?\{/isg) {
    my $nom_estilo = $1;
    if (! exists $estilos_incluidos{$nom_estilo}) { # para evitar incluir nombres de estilos que se puedan repetir
      # print STDERR "nom_estilo[$nom_estilo]\n";
      my $estilo_vtxt = $plt_estilos_vtxt;
      $estilo_vtxt =~ s/%%nom_estilo%%/$nom_estilo/ig;
      $estilos_vtxt .= $estilo_vtxt;
      $estilos_incluidos{$nom_estilo} = 1;
    };
  };
  $estilos_vtxt =~ s/\;$//;
  return $estilos_vtxt;

};
# -------------------------------------------------------------------------#
sub get_css_artic {
  # Obtiene CSSs del articulo separados por coma para incluirlos en el vtxt
  my $path_tpl = shift;
  my $buffer = shift;

  my $paths;

  my ($elcss,$ellink);
  while ($buffer =~ /(<link [^>]*?href="([^>]+?)"[^>]*?>)/isg) {
    $ellink = $1;
    $elcss = $2;
    next unless($ellink =~ /type="text\/css"/i || $ellink =~ /rel="stylesheet"/i);
    # print STDERR "css[$elcss]\n";
    $elcss = &relative2abs($path_tpl, $elcss);
    $elcss =~ s/,/%2C/g; # para tomar en cuenta googlefonts
    $paths .= "$elcss,";
  };
  $paths =~ s/\,$//;
  return $paths;
};
# -------------------------------------------------------------------------#
sub get_include_artic {
  my $buffer = shift;

  if($buffer =~ /<\?php\s/) {
    return 'php';

  } elsif($buffer =~ /<!--\#/) {
    return 'ssi';

  } else {
    return 'php';
  };
}
# -------------------------------------------------------------------------#
sub relative2abs {
  # Transforma un link relativo a absoluto respecto de la raiz del webserver
  # y respecto de la ubicacion del archivo en que el link va inserto.
  my ($ubic_artic) = $_[0]; # path relativo al webserver del archivo en que el link va inserto.
  my ($link2convert) = $_[1];

  return $link2convert if ($link2convert =~ /^\//);
  return $link2convert if ($link2convert =~ /^http/);

  # Elimina el nombre del archivo para dejar solo el dir hasta el /
  $ubic_artic =~ s/\/\w+.*$/\//;

  my $abs_ubic = $ubic_artic;
  while ($link2convert =~ /(\.\.\/)(\w.*)/g) {
    my $part1 = $1;
    my $part2 = $2;
    $abs_ubic =~ s/\w+\/$//;

    # print "part1[$part1] - part2[$part2]\n";
    $link2convert =~ s/$part1$part2/$part2/;
  };
  return "$abs_ubic$link2convert";
};
# ---------------------------------------------------------------
sub get_glosa_tipo_ficha {
  # Obtiene la glosa asociada al tipo de articulo
  my ($tipo_ficha) = $_[0];
  my ($glosa, $key);

  foreach $key (keys %prontus_varglb::FORM_PLTS) {
    # El valor a mostrar esta despues de los 2 puntos en la clave.
    if ($key =~ /^$tipo_ficha *: *(.+)/) {
      $glosa = $1;
    };
  };
  return $glosa;
};
# ---------------------------------------------------------------
sub get_default_fid {
  # Obtiene la glosa asociada al tipo de articulo

  my $fid;

  if ($prontus_varglb::FID_DEFAULT =~ /^([\w@-]+) *: *.+/) {
    $fid = $1;
  };

  return $fid; # el ultimo del hash es el que estaba primero declarado en el cfg

};

# ---------------------------------------------------------------
sub carga_buffer_fid {
    my $path_ficha = $_[0];

    # Cargar plantilla del FID
    my $buffer = &glib_fildir_02::read_file($path_ficha);
    $buffer =~ s/%25%25/%%/sg;

    $buffer = &add_macros_fid($buffer, '');
    $buffer =~ s/%25%25/%%/sg;

    # procesamos marca loop_artic
    $buffer = &lib_prontus::procesa_loop_artic($buffer, '##');

    $buffer = &lib_prontus::set_coreplt_ppal($buffer);

    return $buffer;
};


# -------------------------------------------------------------------------
sub add_macros_fid {
    # Incluye en el tpl las macros senaladas en el con la marca
    # %%MACRO(<nomfilemacro>)%%
    # <nomfilemacro> : Nombre del archivo de la macro (con extension y sin path), ubicado dentro del dir macros

    # Version especifica de esta funcion, para macros de fids, para considerar simultaneamente las
    # reservadas y las de usuario, permitiendo anidamiento cruzado.

    my ($textpag) = shift; # buffer de la plantilla conteniendo invocaciones a macros
    my ($profundidad) = shift; # solo para invocaciones internas, para manejar recursividad


    my $pag_aux = $textpag;

    # Recorre plantillas y parsea macros.
    while ($pag_aux =~ /%%MACRO\((.+?)\)%%/ig) {
        my $arg_str = $1;
        my @args_macro = split(",", $arg_str);

        my $nomfile = $args_macro[0];
        my $id = $args_macro[1];

        $id =~ s/ //sg;
        $id = 1 if (!$id);

        my $dir_macros = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/fid/macros";
        if ($nomfile =~ /^_/) {
            $dir_macros = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/fid/macros_reservadas";
        };

        my $buffer_macro;
        # si la macro no existe, marcamos la plantilla y continuamos con la siguiente
        if (! -f "$dir_macros/$nomfile") {
            my $relpath_macro = &lib_prontus::remove_front_string("$dir_macros/$nomfile", $prontus_varglb::DIR_SERVER);
            $buffer_macro = "Macro '$relpath_macro' no existe!";
            $textpag =~ s/%%MACRO\(\Q$arg_str\E\)%%/$buffer_macro/is;
            next;
        };

        $buffer_macro = &glib_fildir_02::read_file("$dir_macros/$nomfile");
        $buffer_macro = &lib_prontus::ajusta_crlf($buffer_macro);

        # si es galeria con carga masiva debemos parsear los parametros
        if ($nomfile eq '_galeria_prontus.html') {
            $buffer_macro =~ /<!--loop_gal-->[\n\r]*(.*?) *?<!--\/loop_gal-->/is;
            my $loop_gal= $1;
            my $loop_gal_temp;
            my @temp_array = split(/\|/,$id);
            my $temp_buffer = '';
            if (scalar @temp_array < 2) {
                print STDERR "No hay configuracion de galeria, se usan valores por defecto\n";
                # cargamos valores por defecto
                $id = '1:fotofija_galeria@@_low:65x65|2:fotofija_galeria@@_high:800x600';
                @temp_array = split(/\|/,$id);
            }
            my $counter = 1;
            foreach my $conf_size (@temp_array) {
                $loop_gal_temp = $loop_gal;
                my @data_temp = split (/:/, $conf_size);
                $loop_gal_temp =~ s/##i##/$counter/g;
                # se cambia x por , para la resolucion
                $data_temp[2] =~ s/x/,/g;
                $loop_gal_temp =~ s/##_size##/$data_temp[2]/g;
                $temp_buffer .= $loop_gal_temp;
                $counter++;
            }
            $buffer_macro =~ s/<!--loop_gal-->.*?<!--\/loop_gal-->/$temp_buffer/s;
            $temp_buffer = $id;
            $temp_buffer =~ s/:\d+x\d+//sg;
            $buffer_macro =~ s/##_gal_conf##/$temp_buffer/s;
        }
        $buffer_macro =~ s/##id##/$id/sg;

        my $body;
        if ($buffer_macro =~ /<body.*?>(.*)<\/body *>/is) {
            $body = $1;
        };
        $buffer_macro = $body if ($body);
        $profundidad++;

        if ($profundidad > 10) {
            $buffer_macro = '<b>[Error: Se alcanzo el nivel maximo de anidamiento de macros (max=10)]</b>';
            $textpag =~ s/%%MACRO\(\Q$arg_str\E\)%%/$buffer_macro/is;
            $profundidad = 0;
            next;
        } else {
            if ($buffer_macro =~ /%%MACRO\(.+?\)%%/is) {
                $buffer_macro = &add_macros_fid($buffer_macro, $profundidad);
            };
        };
        $profundidad = 0;
        $textpag =~ s/%%MACRO\(\Q$arg_str\E\)%%/$buffer_macro/is;
    };

    # parsear SERVER_NAME --> sacar despues de aca y poner en una funcion onda init_plantilla
    $textpag =~ s/%%_SERVER_NAME%%/$prontus_varglb::PUBLIC_SERVER_NAME/ig;
    return $textpag;
};

# -------------------------------END SCRIPT----------------------
