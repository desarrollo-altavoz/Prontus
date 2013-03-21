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
# PROPOSITO.
# -----------
# Procesar paso 2 del wizard : Configuracion del Publicador,
# grabando la info. en la seccion [MODEL]...[/MODEL] de /wizard_prontus/data/inf.txt
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Al termino del script se invoca via location a wizard_show_paso3.cgi sin parametros.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Via submit desde /wizard_prontus/core/paso2.html
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# No utiliza.
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
# No utiliza.
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 12/2005 - YCH - Primera Version.
# p10.11 - 04/02/2008 - CVI - Correciones al wizard. Manejo de extensión via cfg del modelo.
# ---------------------------------------------------------------


# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
use glib_cgi_04;
use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ------

my (%FORM, %PRONTUS);
my ($INF_DIR) = "$prontus_varglb::DIR_SERVER/wizard_prontus/_data";
my ($INF_FILE) = "$INF_DIR/inf.txt";

main:{

  &glib_cgi_04::new();

  $FORM{'PRONTUS_MODEL'} = &glib_cgi_04::param('PRONTUS_MODEL');
  $FORM{'Sbm_ACCION'} = &glib_cgi_04::param('Sbm_ACCION');

  my ($msg_err, $model_ext, $title_site_name) = &validar_datos();
  if ($msg_err) {
    $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
    &glib_html_02::print_pag_result('Error', $msg_err, 0, "exit=1, ctype=1");
  };


  &grabar_datos($model_ext, $title_site_name);

  print "Location: wizard_show_confirm.cgi\n\n";
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub grabar_datos {
# Graba la info del paso actual en el arch. de texto /wizard_prontus/data/inf.txt, seccion [MODEL]...[/MODEL]
# creando el dir. inf si no existe.
  my ($model_ext) = $_[0];
  my ($title_site_name) = $_[1];
  my ($buffer) = &glib_fildir_02::read_file($INF_FILE);
  # Borra seccion en caso de que exista.
  $buffer =~ s/\[MODEL\].*\[\/MODEL\]\n\n//isg;

  # Agrega seccion
  $buffer .= "[MODEL]\nMODEL_NOM=$FORM{'PRONTUS_MODEL'}\nMODEL_EXT=$model_ext\nTITLE_SITE_NAME=$title_site_name\n[/MODEL]\n\n";

  &glib_fildir_02::write_file($INF_FILE, $buffer);

};
# ---------------------------------------------------------------
sub validar_datos {
# Valida datos provenientes del formulario PASO 2.
# Retorna msg de error si lo hay o nada si todo ok.

  if (!$FORM{'PRONTUS_MODEL'}) {
    return 'Modelo de Prontus no es válido.';
  };

  # Algunas validaciones basicas para el modelo escogido
  my $path_to_cfg = "$prontus_varglb::DIR_SERVER/wizard_prontus/models/$FORM{'PRONTUS_MODEL'}/$FORM{'PRONTUS_MODEL'}.cfg";

  # Existencia de cfg del modelo
  if (!-f $path_to_cfg) {
    return "No se econtró cfg del modelo [$FORM{'PRONTUS_MODEL'}]";
  };

  # Extension de paginas del modelo
  my ($buffer_cfg) = &glib_fildir_02::read_file($path_to_cfg);

  return "Error en cfg del modelo [$FORM{'PRONTUS_MODEL'}]: extensión no declarada." if ($buffer_cfg !~ /MODEL_EXT\s*=\s*["'](\w+)["']\n/);
  my $model_ext = $1;

  return "Error en cfg del modelo [$FORM{'PRONTUS_MODEL'}]: No se encontró TITLE_SITE_NAME." if ($buffer_cfg !~ /TITLE_SITE_NAME\s*=\s*["'](.*?)["']\n/);
  my $title_site_name = $1;


  if ($FORM{'Sbm_ACCION'} !~ /siguiente/i) {
    return "Solicitud de ejecución no válida.";
  };

  # Esto esta deprecated
  # Validar existencia de articulo tipo link obligatorio en todo modelo
  # return "Error en cfg del modelo [$FORM{'PRONTUS_MODEL'}]: Falta artículo obligatorio tipo link." if ($buffer_cfg !~ /\s*ARTICULO\_OBLIGATORIO\s*=\s*("|')link("|')/);
  # El fid, plantilla etc. se valida junto con los demas artics obligatorios en wizard_show_paso5.cgi

  # Leer y cargar y validar contenido del paso1.
  if (! -f $INF_FILE) {
    return "[errInfFile] Solicitud de ejecución no válida.";
  };
  my $buffer = &glib_fildir_02::read_file($INF_FILE);
  my $prontus_id;
  if ($buffer =~ /(\[PRONTUS\].*\[\/PRONTUS\]\n\n)/s) {
    my $buffer_prontus = $1;
    # Validar id
    if ($buffer_prontus !~ /PRONTUS_ID=(\w+)\n/) {
      return 'Información de paso previo está corrupta. Para poder continuar debe volver al paso anterior.';
    }
    else {
      $prontus_id = $1;
    };
  }
  else {
    return 'Información de paso previo está corrupta. Para poder continuar debe volver al paso anterior.';
  };


  # Validar que no exista el dir destino del prontus.
  # Esto ya se chequea en el paso 1 pero se hace nuevamente por seguridad.
  my $dir_prontus = "$prontus_varglb::DIR_SERVER/$prontus_id";

  if (-d $dir_prontus) {
    return "El directorio " . "[prontus]" . " ya existe. Para continuar con el proceso de instalación Ud. debe cambiar el nombre especificado para el publicador, o bien, <br>eliminar manualmente el directorio existente que genera el conflicto.";
  }
  else {
    # Lo creo y luego lo borro para verificar que este ok.
    if (&glib_fildir_02::check_dir($dir_prontus)) {
      &glib_fildir_02::borra_dir($dir_prontus);
    }
    else {
      return "No se puede crear el directorio destino del publicador. No es posible continuar con la instalación.";
    };
  };

  return ('', $model_ext, $title_site_name);
};

# -------------------------------END SCRIPT----------------------

