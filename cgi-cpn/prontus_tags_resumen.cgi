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
# SCRIPT.
# -----------
# prontus_secc_guardar.cgi.
#
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /prontus/.
#
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Mantencion Secciones. Crea, actualiza y/o elimina.
#
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------------
# Location: prontus_secc_admin.cgi (Administrador de Secciones).
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde pagina 'Administrador de Secciones' (/prontus4_nots/cpan/core/mant_seccs/prontus_secc_admin.html) boton 'Guardar'.
#
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# Plantillas: /prontus4_nots/cpan/core/mant_seccs/mensajes.html (para mensajes de error).
#
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# Paginas web: No registra.
#
# ---------------------------------------------------------------
# Tablas.
# -------------------
# SECC - TEMAS - SUBTEMAS.
# ---------------------------------------------------------------


# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 16/10/2003 - YCH - Primera version.
# ---------------------------------------------------------------


# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use DBI;

use prontus_varglb; &prontus_varglb::init();
use glib_dbi_02;
use glib_hrfec_02;
use glib_html_02;
use glib_cgi_04;
use glib_str_02;
use lib_secc;

use lib_prontus;
use strict;



# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM, $BD);


my %DATA_VISTAS;
my $RELPATH_TEMPL = '/cpan/core/prontus_tags_resumen.html';
my $MAX_ARTIC_RESUMEN = 10;
my $MSG_NO_ARTIC = &lib_language::_msg_prontus('_tag_no_items_associated');
my (%TABLA_SECC, %TABLA_TEMAS, %TABLA_SUBTEMAS);

main: {

    # Rescatar parametros recibidos.

    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # user no valido
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin o editor
    if ($prontus_varglb::USERS_PERFIL eq 'P') {
      &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_access_restricted_area'),&lib_language::_msg_prontus('_functionality_available_writer'),1,'exit=1,ctype=1');
    };

    # Carga la plantilla
    my $pagina = &glib_fildir_02::read_file($prontus_varglb::DIR_SERVER . "$prontus_varglb::RELDIR_BASE/$prontus_varglb::PRONTUS_ID$RELPATH_TEMPL");
    $pagina = &lib_prontus::set_coreplt_ppal($pagina);

    $FORM{'_id'}= &glib_cgi_04::param('_id');
    if ($FORM{'_id'} ne '') {
        if (($FORM{'_id'} !~ /^[0-9]+$/) || (!$FORM{'_id'})) {
            &parse_error(&lib_language::_msg_prontus('_invalid_id'), $pagina);
        };
    };

    # Conectar a BD
    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &parse_error($msg_err_bd, $pagina);
    };

    &carga_tabla_secc();
    &carga_tabla_temas();
    &carga_tabla_subtemas();

    my ($msg, $nom, $count) = &valida_tag();
    &parse_error($msg, $pagina) if ($msg);

    $pagina =~ /<!--loop-->(.*?)<!--\/loop-->/igs;
    my $loop = $1;

    if($count) {
        $loop = &make_lista($loop);
        $pagina =~ s/<!--loop-->.*?<!--\/loop-->/$loop/is;
    } else {
        $pagina =~ s/<!--msg-->.*?<!--\/msg-->/$MSG_NO_ARTIC/is;
    }

    $BD->disconnect;

    # Se parsean los campos globales
    $pagina =~ s/%%_max_artics%%/$MAX_ARTIC_RESUMEN/igs;
    $pagina =~ s/%%_tags_id%%/$FORM{'_id'}/ig;
    $pagina =~ s/%%_tags_tag%%/$nom/igs;
    $pagina =~ s/%%_tags_total%%/$count/igs;

    # CVI - 16/06/2011
    my $open_fid_in_pop = 'open_normally';
    if($prontus_varglb::ABRIR_FIDS_EN_POP eq 'SI') {
        $open_fid_in_pop = 'open_in_pop';
    }
    $pagina =~ s/%%_class_open_fid%%/$open_fid_in_pop/ig;


    # Ya que no hubo error, se limpian las marcas
    $pagina =~ s/%%.*?%%//igs;
    $pagina =~ s/<!--error-->.*?<!--\/error-->//igs;
    $pagina =~ s/<!--content-->(.*?)<!--\/content-->/\1/igs;

    print "Content-Type: text/html\n\n";
    print $pagina;

}; # main.

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

# ---------------------------------------------------------------
sub valida_tag {

  # Verifica que el nombre exista en la tabla.
  my $id = $FORM{'_id'};
  my $sql = "select TAGS_TAG from TAGS where TAGS_ID = $id";

  my ($name, $count);
  my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \$name);
  $salida->fetch;
  $salida->finish;
  unless($name){
    return ('El tag #'.$id.' no existe', '');
  };

  # Se cuentan los articulos de este Tag
  $sql = "select count(TAGSART_IDTAGS) from TAGSART where TAGSART_IDTAGS = $id";
  $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \$count);
  $salida->fetch;
  $salida->finish;
  return ('', $name, $count);

}

# ---------------------------------------------------------------
sub make_lista {
  my ($loop) = ($_[0]);

  my ($loop_tmp, $loop_tot);

  my $sql = "select TAGSART_IDTAGS, TAGSART_IDART, ART_TITU, ART_EXTENSION, ART_TIPOFICHA, ART_ALTA, ART_FECHAPHORAP, ART_FECHAEHORAE, ART_SOLOPORTADAS, ART_IDSECC1, ART_IDTEMAS1, ART_IDSUBTEMAS1 from TAGSART";
  $sql .= " left join ART on TAGSART_IDART = ART_ID where TAGSART_IDTAGS = " . $FORM{'_id'};
  $sql .= " order by ART_FECHAPHORAP desc ";
  $sql .= " limit " . $MAX_ARTIC_RESUMEN;
  # warn('SQL: ' . $sql);

  my ($tags_id, $tags_ts, $tags_tit, $tags_ext, $tags_tipoficha, $tags_alta, $tags_fechahorap, $tags_fechahorae, $tags_soloportadas, $tags_idseccion1, $tags_idtema1, $tags_idsubtema1);
  my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($tags_id, $tags_ts, $tags_tit, $tags_ext, $tags_tipoficha, $tags_alta, $tags_fechahorap, $tags_fechahorae, $tags_soloportadas, $tags_idseccion1, $tags_idtema1, $tags_idsubtema1));
  my ($filas);
  while($salida->fetch){
    $loop_tmp = $loop;

    my $nom_seccion1 = $TABLA_SECC{$tags_idseccion1};
    my $nom_tema1 = $TABLA_TEMAS{$tags_idtema1};
    my $nom_subtema1 = $TABLA_SUBTEMAS{$tags_idsubtema1};

    $loop_tmp =~ s/%%_tag_id%%/$tags_id/ig;
    $loop_tmp =~ s/%%_tag_ts%%/$tags_ts/ig;
    $loop_tmp =~ s/%%_tag_titu%%/$tags_tit/ig;

    my ($fechap, $horap);
    if($tags_fechahorap =~ /(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)/) {
      $fechap = "$3/$2/$1";
      $horap = "$4:$5";
    }
    $loop_tmp =~ s/%%_tag_fechap%%/$fechap/ig;
    $loop_tmp =~ s/%%_tag_horap%%/$horap/ig;

    my $file = $tags_ts . '.' . $tags_ext;
    my $fid = $tags_tipoficha;
    my $tag_edit_link = 'prontus_art_ficha.cgi?_file='.$file.'&_fid='.$fid.'&_path_conf='.$FORM{'_path_conf'}.'&fotosvtxt=/1/2/3/4';
    $loop_tmp =~ s/%%_tag_edit_link%%/$tag_edit_link/ig;

    if(! &chequea_status($tags_alta, $tags_fechahorap, $tags_fechahorae, $tags_soloportadas)) {
      $loop_tmp =~ s/%%class_disabled%%/ class="li-disabled"/ig;
      $loop_tmp =~ s/%%_mostrar%%/btn_ticket_red/g;
    } else {
      $loop_tmp =~ s/%%class_disabled%%//ig;
      $loop_tmp =~ s/%%_mostrar%%/btn_ticket_green/g;
    }

    $tags_ts =~ /^(\d{8})\d{6}$/;
    my $fechac = $1;
    my $link = '/'.$prontus_varglb::PRONTUS_ID.'/site/artic/'.$fechac.'/pags/'.$tags_ts.'.'.$tags_ext;
    # CVI - 29/03/2011 - Para habilitar las friendly urls en el admin de comentarios
    # JOR - 23/07/2012 - Agrega seccion, tema y subtema para nuevo tipo de friendly.
    if ($prontus_varglb::FRIENDLY_URLS eq 'SI') {
      $link = &lib_prontus::parse_filef('%%_FILEURL%%', $tags_tit, $tags_ts, $prontus_varglb::PRONTUS_ID, $link, $nom_seccion1, $nom_tema1, $nom_subtema1);
    }
    $loop_tmp =~ s/%%_tag_link%%/$link/ig;
    $loop_tot .= $loop_tmp;
  }

  return $loop_tot;

}; # guardar_new_entidad.

# ---------------------------------------------------------------
sub chequea_status {

  my ($tags_alta, $tags_fechahorap, $tags_fechahorae, $tags_soloportadas) = ($_[0], $_[1], $_[2], $_[3]);

  # se chequea el alta
  if($prontus_varglb::CONTROLAR_ALTA_ARTICULOS eq 'SI' &&  $tags_alta ne '1') {
    return 0;
  }

  my $dthr_system = &glib_hrfec_02::get_dtime_pack4();
  $dthr_system =~ s/^(\d{12})\d{2}$/\1/;

  # se chequea la fecha de publicacion
  if($tags_fechahorap > $dthr_system) {
    return 0;
  }

  # Se chequea la expiracion, siempre que haya control_fecha y no tenga el despublicar sólo de portadas
  if($prontus_varglb::CONTROL_FECHA eq 'SI') {
    if($tags_soloportadas ne '1' && $tags_fechahorae < $dthr_system) {
      return 0;
    }
  }

  return 1;

};

# ---------------------------------------------------------------
sub parse_error {

    my ($msg, $pagina) = ($_[0], $_[1]);

    $pagina =~ s/<!--content-->.*?<!--\/content-->//igs;
    $pagina =~ s/<!--error-->(.*?)<!--\/error-->/\1/igs;

    $pagina =~ s/%%_msg%%/$msg/gs;

    print "Content-Type: text/html\n\n";
    print $pagina;
    exit;
};

# ---------------------------------------------------------------
sub carga_tabla_secc {
  my ($sql, $salida, $nom, $id);

  $sql = "select SECC_ID, SECC_NOM from SECC ";
  $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id, $nom));
  while ($salida->fetch) {
    $TABLA_SECC{$id} = $nom;
  };
  $salida->finish;
};

# ---------------------------------------------------------------
sub carga_tabla_temas {
  my ($sql, $salida, $nom, $id);

  $sql = "select TEMAS_ID, TEMAS_NOM from TEMAS ";
  $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id, $nom));
  while ($salida->fetch) {
    $TABLA_TEMAS{$id} = $nom;
  };
  $salida->finish;
};

# ---------------------------------------------------------------
sub carga_tabla_subtemas {
  my ($sql, $salida, $nom, $id);

  $sql = "select SUBTEMAS_ID, SUBTEMAS_NOM from SUBTEMAS ";
  $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id, $nom));
  while ($salida->fetch) {
    $TABLA_SUBTEMAS{$id} = $nom;
  };
  $salida->finish;
};

# ----------------------------END SCRIPT---------------------
