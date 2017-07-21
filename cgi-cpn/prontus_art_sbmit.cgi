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
# Procesar 'submit' de la pagina de ingreso/modif. de Articulo.
# Botones procesados :
# 1) Previsualizar : Genera una página intermedia llamada preview.html tal como si fuera
# la pagina definitiva. Esta queda ubicada en el mismo dir. de la pagina final pero como tiene
# el nombre especial 'preview' no es considerada como página del sitio.
# 2) Guardar : Genera la pagina definitiva en base a los datos del formulario y el template seleccionado.
# En cualquiera de los casos, la página es presentada al usuario en una nueva ventana del navegador.
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
# 1.2 - 28/07/2000 - Se agrega posibilidad de manipular archivos cualquiera (por ej. de texto)
# asociados al articulo. Estos archivos estaran disponibles solo a traves de links en el articulo y portada. Son del tipo
# ASOCFILEi.
# 1.3. guarda en el head USER=<user conectado via htaccess> # Modificacion removida.
# 1.4 - 01/09/2000 - Validacion de extension de fotos.
# 1.5 - 01/09/2000 - Se remueve rutina 'salva_fotos' (no se estaba utilizando)
# 1.6 - 20/09/2000 - Al guardar o previs., se trabaja siempre en la misma ventana. Cuando se guarda, se recarga la ficha.
# 1.7 - 02/10/2000 - se pone ancho 80 a las tablas que contienen las fotos.
# 1.8 - 04/10/2000 - Correciones en el manejo de tablas.
# 1.9 - 03/11/2000 - Correciones al regenerar la portada al subri un archivo asociado.
# 1.10 - 07/11/2000 - soporte para articulos shtml
# 1.11 - 06/12/2000 - Modificaciones en la llamada a la rutina que carga y valida el archivo de configuracion del prontus.
# Ademas se oficializa la validacion del referer.
# 1.12 - 24/11/2000 - Antes de escribir el articulo, se agrega al final del head un meta tag con el prontus_key.
# 1.13 - 05/12/2000 - Modificaciones para soportar marcas de codigo html puro dentro de los campos TEXT.
# 1.14 - 15/05/2001 - Extensiones para Prontus 5. Estas modificaciones se aplicaron antes de escribir este comentario.
# 1.15 - 16/05/2001 - Modificaciones para parametrizacion del protocolo (http o https) a traves del arch. de conf.
# 1.16 - 16/05/2001 - Revision general de detalles de forma.

# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0

# 7.0 - 20/12/2001 - Extensiones p7 :
#   . "- Agrega marca a la portada para que inserte los menús de páginas con subtítulos.<br>"
#     . "- Perfilación de periodistas en lista de artículos para permitir artículos personales<br>"
#     . "- Capacidad para borrar fotos, asocfile y realmedia<br>"
#     . "- Linkeo de URLs https<br>"

# Prontus 8.0 - 01/08/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
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

use strict;
# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);
use Data::Dumper;

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_prontus;
use glib_cgi_04;
use glib_hrfec_02;
use lib_tax;
use lib_waitlock; # Bloqueos tipo espera.

use Artic;
use lib_artic;
use lib_quota;

# ---------------------------------------------------------------
# MAIN.
# -------------
my ($ARTIC_OBJ);
my %FORM;
my $PATHNICE;

main: {

    # Rescatar parametros recibidos
    &glib_cgi_04::new();

    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});
    $FORM{'_curr_body'} = &glib_cgi_04::param('_curr_body');
    $FORM{'_accion'} = &glib_cgi_04::param('_accion');
    $FORM{'_fid'} =  &glib_cgi_04::param('_fid'); # Tipo de ficha
    $FORM{'_file'} =  &glib_cgi_04::param('_file'); # ARTIC CUANDO ES EDICION
    $FORM{'_MV'} = &glib_cgi_04::param('_CMB_MV');
    $FORM{'_popup'} = &glib_cgi_04::param('_popup');
    $FORM{'_port_dd'} = &glib_cgi_04::param('_port_dd');
    $FORM{'_alta'} = &glib_cgi_04::param('_ALTA');

    # Para public. directa
    $FORM{'_edic'} = &glib_cgi_04::param('_edic');
    $FORM{'_port'} = &glib_cgi_04::param('_port');
    $FORM{'_area'} = &glib_cgi_04::param('_area');

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Autentifica request.  con SERVER_PERM.
    &lib_prontus::test_servers($ENV{'HTTP_REFERER'}) if ($prontus_varglb::IP_SERVER);

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 0, 'exit=1,ctype=1');
    };

    my %marcas_multimedia_art = ();
    my @lista_campos = &glib_cgi_04::param();
    foreach my $campo (@lista_campos) {
        if ($campo =~ /(MULTIMEDIA_VIDEO\d+)/i) {
            my $marca_video = lc($1);
            $marcas_multimedia_art{$marca_video} = 1;
            if ($campo =~ /^MULTIMEDIA_VIDEO/i) {
                my $video_subido = &glib_cgi_04::param($campo);
                if ($video_subido ne '') {
                    my $ts = &glib_cgi_04::param('_file');
                    $ts =~ s/\.html//;
                    &lib_prontus::write_log('Carga Video', 'Articulo', "TS[$ts] [$campo] VIDEOTEMP[$video_subido]", $prontus_varglb::USERS_USR);
                }
            } elsif ($campo =~ /^_BORR_(MULTIMEDIA_VIDEO\d+)/i) {
                my $borrar_video = &glib_cgi_04::param($campo);
                if ($borrar_video eq 'S') {
                    my $ts = &glib_cgi_04::param('_file');
                    $ts =~ s/\.html//;
                    &lib_prontus::write_log('Borrar Video', 'Articulo', "TS[$ts] [$marca_video] VIDEO[". &glib_cgi_04::param('_HIDD_'.$marca_video)."]", $prontus_varglb::USERS_USR);
                }
            }
        }
    }

    # Validar quota
    my $msg_err_quota = &lib_quota::check_quota_suficiente();
    &glib_html_02::print_pag_result('Error',$msg_err_quota, 0, 'exit=1,ctype=1') if ($msg_err_quota);


    # Crear objeto Artic
    $ARTIC_OBJ = &crear_objeto_artic();

    # Previsualizar
    if ($FORM{'_accion'} eq 'preview') {
        &do_preview();
        exit;
    };

    # Pasarle el objeto a la lib_artic
    $lib_artic::ARTIC_OBJ = $ARTIC_OBJ;
    undef $ARTIC_OBJ;

    # Salvar el articulo en base a los datos del objeto Artic
    my $is_new = 0;
    $is_new = 1 if ($FORM{'_file'} eq '');

    # Se comprueba si el articulo debe ser guardado
    my $buff_xml_data = &lib_prontus::get_xml_data($lib_artic::ARTIC_OBJ->{fullpath_xml});
    my $regenerar_procesos = 1;
    my %campos_xml = &lib_prontus::getCamposXml($buff_xml_data, '_alta');
    my $alta = $campos_xml{'_alta'};
    if($FORM{'_alta'} eq '' && ($alta eq '' || $is_new)) {
        $regenerar_procesos = 0;
    };

    my %campos_stst_old = &lib_prontus::getCamposXml($buff_xml_data, '_seccion1,_tema1,_subtema1,_seccion2,_tema2,_subtema2,_seccion3,_tema3,_subtema3');

    # Se revisa si se deben regenerar todas las taxport o solo una página
    my %ts_list;
    ($ts_list{'1'}, $ts_list{'2'}, $ts_list{'3'}) = &check_taxport2process($buff_xml_data, \%campos_stst_old, $is_new);

    my $msg_err_save = &lib_artic::save_artic_with_object($is_new);
    &glib_html_02::print_pag_result("Error", $msg_err_save, 0, 'exit=1,ctype=1') if ($msg_err_save);

    # Agregar el art. a portada
    if ($FORM{'_edic'} && $FORM{'_port'} && $FORM{'_area'}) {
        # print STDERR "PUB IN $FORM{'_edic'} Y $FORM{'_port'} Y $FORM{'_area'}\n";
        # Publicar art.
        my $dir_port = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/site/edic/$FORM{'_edic'}/port";
        my $nom_port = $FORM{'_port'};
        &lib_artic::publica_art_in_port("$dir_port/$nom_port", $FORM{'_edic'}, $nom_port, $prontus_varglb::PRONTUS_ID, $lib_artic::ARTIC_OBJ->{'ts'}, $lib_artic::ARTIC_OBJ->{campos}->{'_fid'}, $FORM{'_area'});
    };

    my $fullpath_artic = $lib_artic::ARTIC_OBJ->get_fullpath_artic('', $lib_artic::ARTIC_OBJ->{campos}->{'_plt'});
    use FindBin '$Bin';
    my $rutaScript = $Bin;

    # cargamos la ruta de nice
    $PATHNICE = &lib_prontus::get_path_nice();
    $PATHNICE = "$PATHNICE -n19 " if ($PATHNICE);

    if ($lib_artic::ARTIC_OBJ->{xml_content}->{'_gal_archive'} ne '') {
        &call_gallery_save($fullpath_artic, $rutaScript);
    }

    # Xcoding
    if (keys %marcas_multimedia_art) {
        &call_xcoding($rutaScript, $lib_artic::ARTIC_OBJ->{campos}->{'_fid'}, join(',', keys %marcas_multimedia_art), $lib_artic::ARTIC_OBJ->{ts});
    }

    # DAM
    &call_dam2save($fullpath_artic, $rutaScript);

    # Clustering
    &call_clustering($fullpath_artic, $rutaScript);

    # Dropbox.
    &call_dropbox_backup($lib_artic::ARTIC_OBJ->{ts}, $lib_artic::ARTIC_OBJ->{campos}->{'_seccion1'}, $lib_artic::ARTIC_OBJ->{campos}->{'_tema1'}, $lib_artic::ARTIC_OBJ->{campos}->{'_subtema1'});

    # se indica el fid a procesar, la cgi que genera las taxports determina si hay una vista
    # propia de este fid que generar
    my $filtro_fid = $lib_artic::ARTIC_OBJ->{campos}->{'_fid'};

    #print STDERR "filtro_fid[$filtro_fid]\n";
    if($regenerar_procesos && !($lib_artic::ARTIC_OBJ->{campos}->{'_seccion1'} || $lib_artic::ARTIC_OBJ->{campos}->{'_seccion2'} || $lib_artic::ARTIC_OBJ->{campos}->{'_seccion3'})) {
        my $param_especif_taxport = $lib_artic::ARTIC_OBJ->{campos}->{'_fid'} . '///';
        &call_list_regen($rutaScript, $param_especif_taxport);
    };

    for (my $i = 1; $i < 4; $i++) {
        # Tripleta 1
        print STDERR "Tripleta $i\n";
        if ($regenerar_procesos && $lib_artic::ARTIC_OBJ->{campos}->{'_seccion'.$i}) {
            my $xml_id_seccion = $campos_stst_old{'_seccion'.$i};
            my $xml_id_tema = $campos_stst_old{'_tema'.$i};
            my $xml_id_subtema = $campos_stst_old{'_subtema'.$i};

            my $id_seccion = $lib_artic::ARTIC_OBJ->{campos}->{'_seccion'.$i};
            my $id_tema = $lib_artic::ARTIC_OBJ->{campos}->{'_tema'.$i};
            my $id_subtema =  $lib_artic::ARTIC_OBJ->{campos}->{'_subtema'.$i};

            # La sección que viene por POST es distinta a la que está guardada en el XML.
            if ($xml_id_seccion ne $id_seccion && $id_seccion ne '') {
                # Se actualiza tax/list para la seccion que viene por POST
                my $param_especif_taxport = "$filtro_fid/$id_seccion/$id_tema/$id_subtema";
                &call_taxports_regen($rutaScript, $param_especif_taxport, $ts_list{$i});

                $param_especif_taxport = "/$id_seccion/$id_tema/$id_subtema";
                &call_taxports_regen($rutaScript, $param_especif_taxport, $ts_list{$i});

                $param_especif_taxport = $lib_artic::ARTIC_OBJ->{campos}->{'_fid'}
                                          . '/' . $id_seccion
                                          . '/' . $id_tema
                                          . '/' . $id_subtema;
                &call_list_regen($rutaScript, $param_especif_taxport);
                # Se actualiza tax/list para la seccion que estaba en el XML (antigua).
                if ($xml_id_seccion ne '') {
                    my $param_especif_taxport = "$filtro_fid/$xml_id_seccion/$xml_id_tema/$xml_id_subtema";
                    &call_taxports_regen($rutaScript, $param_especif_taxport, $ts_list{$i});

                    $param_especif_taxport = "/$xml_id_seccion/$xml_id_tema/$xml_id_subtema";
                    &call_taxports_regen($rutaScript, $param_especif_taxport, $ts_list{$i});

                    $param_especif_taxport = $lib_artic::ARTIC_OBJ->{campos}->{'_fid'}
                                              . '/' . $xml_id_seccion
                                              . '/' . $xml_id_tema
                                              . '/' . $xml_id_subtema;
                    &call_list_regen($rutaScript, $param_especif_taxport);
                };
            } elsif ($xml_id_seccion eq $id_seccion) { # lo que viene es igual a lo que está, se actualiza tax/list.
                    my $param_especif_taxport = "$filtro_fid/$id_seccion/$id_tema/$id_subtema";
                    &call_taxports_regen($rutaScript, $param_especif_taxport, $ts_list{$i});

                    $param_especif_taxport = "/$id_seccion/$id_tema/$id_subtema";
                    &call_taxports_regen($rutaScript, $param_especif_taxport, $ts_list{$i});

                    $param_especif_taxport = $lib_artic::ARTIC_OBJ->{campos}->{'_fid'}
                                              . '/' . $id_seccion
                                              . '/' . $id_tema
                                              . '/' . $id_subtema;
                    &call_list_regen($rutaScript, $param_especif_taxport);
            };

            # El tema que viene por POST es distinto al que está guardado en el XML.
            if ($xml_id_tema ne $id_tema && $id_tema ne '' && $xml_id_tema ne '') {
                my $param_especif_taxport = "$filtro_fid/$xml_id_seccion/$xml_id_tema/$xml_id_subtema";
                &call_taxports_regen($rutaScript, $param_especif_taxport, $ts_list{$i});

                $param_especif_taxport = "/$xml_id_seccion/$xml_id_tema/$xml_id_subtema";
                &call_taxports_regen($rutaScript, $param_especif_taxport, $ts_list{$i});

                $param_especif_taxport = $lib_artic::ARTIC_OBJ->{campos}->{'_fid'}
                                          . '/' . $xml_id_seccion
                                          . '/' . $xml_id_tema
                                          . '/' . $xml_id_subtema;
                &call_list_regen($rutaScript, $param_especif_taxport);
            };

            if ($xml_id_subtema ne $id_subtema && $xml_id_subtema ne '' && $id_subtema ne '') { # si cambia la seccion, generar la nueva y la anterior.
                my $param_especif_taxport = "$filtro_fid/$xml_id_seccion/$xml_id_tema/$xml_id_subtema";
                &call_taxports_regen($rutaScript, $param_especif_taxport, $ts_list{$i});

                $param_especif_taxport = "/$xml_id_seccion/$xml_id_tema/$xml_id_subtema";
                &call_taxports_regen($rutaScript, $param_especif_taxport, $ts_list{$i});

                $param_especif_taxport = $lib_artic::ARTIC_OBJ->{campos}->{'_fid'}
                                          . '/' . $xml_id_seccion
                                          . '/' . $xml_id_tema
                                          . '/' . $xml_id_subtema;
                &call_list_regen($rutaScript, $param_especif_taxport);
            };

        } else {
            my $xml_id_seccion = $campos_stst_old{'_seccion'.$i};
            my $xml_id_tema = $campos_stst_old{'_tema'.$i};
            my $xml_id_subtema = $campos_stst_old{'_subtema'.$i};
            # No viene la sección por POST
            if ($xml_id_seccion ne '') {
                # Se actualiza la seccion, tema, subtema antiguos.
                my $param_especif_taxport = "$filtro_fid/$xml_id_seccion/$xml_id_tema/$xml_id_subtema";
                &call_taxports_regen($rutaScript, $param_especif_taxport, $ts_list{$i});

                $param_especif_taxport = "/$xml_id_seccion/$xml_id_tema/$xml_id_subtema";
                &call_taxports_regen($rutaScript, $param_especif_taxport, $ts_list{$i});

                $param_especif_taxport = $lib_artic::ARTIC_OBJ->{campos}->{'_fid'}
                                          . '/' . $xml_id_seccion
                                          . '/' . $xml_id_tema
                                          . '/' . $xml_id_subtema;
                &call_list_regen($rutaScript, $param_especif_taxport);
            };
        };
    }

    # Regenerar tagonomicas
    if ($regenerar_procesos && $lib_artic::ARTIC_OBJ->{campos}->{'_tags'}) {
        my $tags_id = $lib_artic::ARTIC_OBJ->{campos}->{'_tags'};
        $tags_id =~ s/\,/\//g;
        my $param_especif_tagonomicas = $tags_id;
        $param_especif_tagonomicas .= " $filtro_fid" if ($filtro_fid);
        &call_tagonomicas_regen($rutaScript, $param_especif_tagonomicas);
    };


    # Hace location al mismo o a nuevo
    my $nom_file_artic = $lib_artic::ARTIC_OBJ->get_nom_artic($lib_artic::ARTIC_OBJ->{campos}->{'_plt'});
    my $dir_fecha = $lib_artic::ARTIC_OBJ->{fechac};
    if ($FORM{'_accion'} =~ /save_new/i) { # Guardar y nuevo
        $nom_file_artic = '';
        $dir_fecha = '';
    };

    my $upd_port_preview;
    if ($FORM{'_port_dd'}) {
        # decirle a prontus_art_ficha que actualice la portada en el parent.
        $upd_port_preview = '&_upd_port_dd=1';
    };

    my $port_preview = '';
    $port_preview = '&_port_dd=1' if ($FORM{'_port_dd'});

    # CVI - 16/06/0211
    my $popup = '';
    $popup = '&_popup=1' if($FORM{'_popup'});
    print "Location: prontus_art_ficha.$prontus_varglb::EXTENSION_CGI?_curr_body=$FORM{'_curr_body'}" . '&_dir_fecha=' . $dir_fecha . '&_file=' . $nom_file_artic . '&_fid=' . $FORM{'_fid'} . '&_path_conf=' . $FORM{'_path_conf'} . '&fotosvtxt=/1/2/3/4' . $popup . $port_preview . $upd_port_preview . "\n\n";    # 1.15
    exit;
};
# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub call_dropbox_backup {
    my $ts = $_[0];
    my $seccion1 = $_[1];
    my $tema1 = $_[2];
    my $subtema1 = $_[3];

    if ($prontus_varglb::DROPBOX eq 'SI') {
        &lib_prontus::dropbox_backup("art;$ts;$seccion1;$tema1;$subtema1");
    };
};
# ---------------------------------------------------------------
sub call_clustering {
    my $fullpath_artic = shift;
    my $rutaScript = shift;

    if (keys(%prontus_varglb::CLUSTERING_SERVER) > 0) {
        print STDERR $rutaScript . "/prontus_cluster_artic.cgi $fullpath_artic &\n";
        system $rutaScript . "/prontus_cluster_artic.cgi $fullpath_artic >/dev/null 2>&1 &";
    };
};
# ---------------------------------------------------------------
sub call_dam2save {
    my $fullpath_artic = shift;
    my $rutaScript = shift;
    my $cmd = "$PATHNICE $rutaScript/dam/prontus_dam_ppart_save.cgi $fullpath_artic $prontus_varglb::PUBLIC_SERVER_NAME >/dev/null 2>&1 &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};
# ---------------------------------------------------------------
sub call_gallery_save {
    my $fullpath_artic = shift;
    my $rutaScript = shift;
    my $cmd = "$PATHNICE $rutaScript/galeria/prontus_galeria_procesar.cgi $fullpath_artic >/dev/null 2>&1 &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};
# ---------------------------------------------------------------
sub call_xcoding {
    print STDERR "call_xcoding\n";
    my $rutaScript = shift;
    my $fid = shift;
    my $marcas_video = shift;
    my $ts = shift;
    my $cmd = "$PATHNICE perl $rutaScript/xcoding/prontus_procesar_videos.pl $prontus_varglb::PRONTUS_ID $ts $marcas_video >/dev/null 2>&1 &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};
# ---------------------------------------------------------------
sub call_taxports_regen {
    my $rutaScript = shift;
    my $param_especif_taxport = shift;
    my $param_ts = shift;
    my $cmd = "$PATHNICE $rutaScript/prontus_cron_taxport.cgi $prontus_varglb::PRONTUS_ID $param_especif_taxport $param_ts >/dev/null 2>&1 &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};
# ---------------------------------------------------------------
sub call_list_regen {
    my $rutaScript = shift;
    my $param_especif_list = shift;
    return if($prontus_varglb::LIST_PROCESO_INTERNO ne 'SI');
    my $cmd = "$PATHNICE $rutaScript/prontus_cron_list.cgi $prontus_varglb::PRONTUS_ID $param_especif_list >/dev/null 2>&1 &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};
# ---------------------------------------------------------------
sub call_tagonomicas_regen {
    my $rutaScript = shift;
    my $param_especif_tagonomicas = shift;
    my $cmd = "$PATHNICE $rutaScript/prontus_tags_ports.cgi $prontus_varglb::PRONTUS_ID $param_especif_tagonomicas >/dev/null 2>&1 &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};
# ---------------------------------------------------------------
sub crear_objeto_artic {
# Crea objeto Artic, para lo cual es basico cargar el hash de datos a partir
# de los datos submitidos.

    my @campos = &glib_cgi_04::param();
    my %hash_datos;
    foreach my $nom_campo (sort {$a cmp $b} @campos) {
        my $nom_lc = lc $nom_campo;
        $hash_datos{$nom_lc} = &glib_cgi_04::param($nom_campo);
        if (($nom_lc =~ /^asocfile_/ || $nom_lc eq '_gal_archive') && ($hash_datos{$nom_lc} ne '')) {
            # revisar como se esta pasando el real path del archivo
            no strict "refs";
            $hash_datos{$nom_lc}{'real_path'} = &glib_cgi_04::real_paths($nom_campo);
            use strict;
        };
    };

    my ($ts, $ext);
    my $propietario = $prontus_varglb::USERS_ID;
    if ($FORM{'_file'} ne '') {
        ($ts, $ext) = &lib_prontus::split_nom_y_extension($FORM{'_file'});
        $propietario = &glib_cgi_04::param("_USER_ID"); # conservar creador del artic
    };
    # agrega item extra para guardar el user
    $hash_datos{'_users_id'} = $propietario;

    # cvi - Para la nueva forma de controlar los tags
    my $tags = &glib_cgi_04::param('_tags');
    my $tags4fid = &glib_cgi_04::param('_tags4fid');
    $tags =~ s/[^0-9,]//g;
    $tags =~ s/,{2,}/,/g;
    $tags =~ s/^,|,$//s;
    $hash_datos{'_tags'} = $tags;
    # warn("tags[$tags]");

    # cvi - Para guardar los nombres de los tags tambien
    my $tagnames = '';
    my @tagscomp = split(/,/, $tags4fid);
    foreach my $idandname (@tagscomp) {
      if($idandname =~ /^\d+\|(.+?)$/) {
        $tagnames = $tagnames.$1.',';
      }
    }
    $tagnames =~ s/,$//;
    $hash_datos{'_tagnames'} = $tagnames;
    # warn("tagnames[$tagnames]");

    # Si no hay control de alta, todos quedan con alta=1.
    # ToDo: pasar el control alta como var del objeto.
    if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS ne 'SI') {
        $hash_datos{'_alta'} = '1';
    };

    my $artic_obj = Artic->new(
                    'prontus_id'=>$prontus_varglb::PRONTUS_ID,
                    'public_server_name'=>$prontus_varglb::PUBLIC_SERVER_NAME,
                    'cpan_server_name'=>$prontus_varglb::IP_SERVER,
                    'ts'=>$ts, # si no va, asigna uno nuevo
                    'campos'=>\%hash_datos) || die "Error inicializando objeto articulo: $Artic::ERR\n";
    return $artic_obj;
};
# ---------------------------------------------------------------
sub do_preview {
# Realiza preview del articulo

    my $dst_pags = $ARTIC_OBJ->{dst_pags};
    my $multivista4preview = $FORM{'_MV'};
    my $ext = shift;

    $ARTIC_OBJ->set_preview_artic();

    # Generar xml
    $ARTIC_OBJ->generar_xml_artic()
              || &glib_html_02::print_pag_result("Error",$Artic::ERR,1,'exit=1,ctype=1');

    $ARTIC_OBJ->generar_vista_art($multivista4preview, $prontus_varglb::STAMP_DEMO, $prontus_varglb::PRONTUS_KEY)
            || &glib_html_02::print_pag_result("Error",$Artic::ERR,1,'exit=1,ctype=1');

    # Location al preview
    my $dst_location = $ARTIC_OBJ->get_fullpath_artic($multivista4preview, $ARTIC_OBJ->{campos}->{'_plt'});

    if (-s $dst_location) {
        $dst_location = &lib_prontus::remove_front_string($dst_location, $prontus_varglb::DIR_SERVER);
        print 'Location: ..' . $dst_location . "\n\n";
    }
    else {
        &glib_html_02::print_pag_result("Error",'La vista requerida no existe, o bien, no pudo ser generada.',1,'exit=1,ctype=1');
    };
};

# ---------------------------------------------------------------
# Se cheque que los cambios en este articulo ameriten regenerar todas las taxport.
# Los posibles cambios que generan esto son:
#   - Cambio en el Alta
#   - Cambios en la taxonomia
#   - Cambios en las Fechas u Horas de Publicacipon / Expiración
# Si el orden es por fecha de Creación, el $all es siempre <ts>
# si el orden es por Titular,
sub check_taxport2process {

    my $buff_xml_data = shift;
    my $ref_campos_stst_old = shift;
    my $is_new = shift;

    my %campos_stst_old = %$ref_campos_stst_old;
    my ($ts1, $ts2, $ts3) = ('', '', '', '');

    my ($ts, $ext) = &lib_prontus::split_nom_y_extension($FORM{'_file'});
    my %campos_old = lib_prontus::getCamposXml($buff_xml_data, '_alta,_fechap,_horap,_fechae,_horae');

    # En este caso no hacemos nada, porque no se regenerarán las taxport
    return ('', '', '') if($is_new && $FORM{'_alta'} eq '');

    # En este caso no hacemos nada, porque no se regenerarán las taxport
    if($FORM{'_alta'} eq '' && $campos_old{'_alta'} eq '') {
        print STDERR "[taxport2process] No hay alta, ni antes ni dsps, no se hace nada\n";
        return ($ts, $ts, $ts);
    };

    # En este caso, regeneraremos todo, por la complejidad de saber si hubo cambio o no
    if($prontus_varglb::TAXPORT_ORDEN_TIPO eq 'TITULAR') {
        print STDERR "[taxport2process] Orden por titular\n";
        return ('', '', '');
    };

    # Primero chequeamos el alta: Si hubo cambio de alta se regenera todo
    if($FORM{'_alta'} ne $campos_old{'_alta'}) {
        print STDERR "[taxport2process] Hubo cambio de alta\n";
        return ('', '', '');
    };

    # Segundo la fecha/hora de Publicacion.
    my $fechap = &glib_cgi_04::param('_FECHAP');
    my $horap = &glib_cgi_04::param('_HORAP');
    if($campos_old{'_fechap'} ne $fechap || $campos_old{'_horap'} ne $horap) {
        print STDERR "Cambio fecha de Publicacion\n";
        return ('', '', '');
    }

    # Tercero la fecha/hora de Expiración
    my $fechae = &glib_cgi_04::param('_FECHAE');
    my $horae = &glib_cgi_04::param('_HORAE');
    if($campos_old{'_fechae'} eq '99999999') {
        $campos_old{'_fechae'} = '';
        if($campos_old{'_horae'} eq '00:00') {
            $campos_old{'_horae'} = '';
        };
    };
    if($campos_old{'_fechae'} ne $fechae || $campos_old{'_horae'} ne $horae) {
        print STDERR "[taxport2process] Cambio fecha de Expiracion\n";
        print STDERR "[taxport2process] $campos_old{'_fechae'}, $fechae, $campos_old{'_horae'}, $horae\n";
        return ('', '', '');
    }

    # Cuarto: Revisamos cambios en la expiración / publicación
    # TODO: Esto queda para futuro, para no aumentar complejidad

    # Seguimos con las taxonomias: Primera tripleta
    my $secc1 = &glib_cgi_04::param('_SECCION1');
    my $tema1 = &glib_cgi_04::param('_TEMA1');
    my $stem1 = &glib_cgi_04::param('_SUBTEMA1');
    $secc1 = '' if($secc1 eq '0');
    $tema1 = '' if($tema1 eq '0');
    $stem1 = '' if($stem1 eq '0');
    if($campos_stst_old{'_seccion1'} eq $secc1 && $campos_stst_old{'_tema1'} eq $tema1 && $campos_stst_old{'_subtema1'} eq $stem1) {
        $ts1 = $ts;
    };

    # Segunda tripleta
    my $secc2 = &glib_cgi_04::param('_SECCION2');
    my $tema2 = &glib_cgi_04::param('_TEMA2');
    my $stem2 = &glib_cgi_04::param('_SUBTEMA2');
    $secc2 = '' if($secc2 eq '0');
    $tema2 = '' if($tema2 eq '0');
    $stem2 = '' if($stem2 eq '0');
    if($campos_stst_old{'_seccion2'} eq $secc2 && $campos_stst_old{'_tema2'} eq $tema2 && $campos_stst_old{'_subtema2'} eq $stem2) {
        $ts2 = $ts;
    };

    # Tercera tripleta
    my $secc3 = &glib_cgi_04::param('_SECCION3');
    my $tema3 = &glib_cgi_04::param('_TEMA3');
    my $stem3 = &glib_cgi_04::param('_SUBTEMA3');
    $secc3 = '' if($secc3 eq '0');
    $tema3 = '' if($tema3 eq '0');
    $stem3 = '' if($stem3 eq '0');
    if($campos_stst_old{'_seccion3'} eq $secc3 && $campos_stst_old{'_tema3'} eq $tema3 && $campos_stst_old{'_subtema3'} eq $stem3) {
        $ts3 = $ts;
    };

    #~ print STDERR "_seccion1[".$campos_stst_old{'_seccion1'}."]... [".$secc1."]\n";
    #~ print STDERR "_tema1[".$campos_stst_old{'_tema1'}."]... [".$tema1."]\n";
    #~ print STDERR "_subtema1[".$campos_stst_old{'_subtema1'}."]... [".$stem1."]\n";
    #~ print STDERR "_seccion2[".$campos_stst_old{'_seccion2'}."]... [".$secc2."]\n";
    #~ print STDERR "_tema2[".$campos_stst_old{'_tema2'}."]... [".$tema2."]\n";
    #~ print STDERR "_subtema2[".$campos_stst_old{'_subtema2'}."]... [".$stem2."]\n";
    #~ print STDERR "_seccion2[".$campos_stst_old{'_seccion2'}."]... [".$secc2."]\n";
    #~ print STDERR "_seccion3[".$campos_stst_old{'_seccion3'}."]... [".$secc3."]\n";
    print STDERR "[taxport2process] No se deben regenerar todas las taxport [$ts1, $ts2, $ts3]\n";
    return ($ts1, $ts2, $ts3);
};
# -------------------------------END SCRIPT----------------------
