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
# Muestra pagina a traves de la cual se escoge el modelo en base al que se generara el sitio prontus.
# Cada modelo tendra un cfg que permitira al motor del wizard desplegar al
# usuario lo que corresponda.
# Cada modelo tendra ademas una imagen representativa de éste y un link
# a descripción y observaciones del mismo.
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------
# No registra, imprime directamente al browser.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Via location desde wizard_paso1.cgi sin parametros.
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------------
# - Informacion de paso1 para verificacion:
# /wizard_prontus/data/inf.txt

# - Plantilla: /wizard_prontus/core/paso2.html

# - Informacion de modelos disponibles. Cada modelo es descrito por un cfg:
# /wizard_prontus/models/<nom_model>/<nom_model>.cfg
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ----------------------------
# No registra.
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
# No utiliza.
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 01 - 11/2005 - YCH - Primera Version.


# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use strict;
use lib_prontus;

use wizard_lib;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my (%PRONTUS);
my ($INF_DIR) = "$prontus_varglb::DIR_SERVER/wizard_prontus/_data";
my ($INF_FILE) = "$INF_DIR/inf.txt";


main:{

  # Valida informacion de paso 1.
  my $msg_err = &wizard_lib::check_paso1();
  if ($msg_err) {

    $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
    &glib_html_02::print_pag_result('Error', $msg_err, 0, "exit=1, ctype=1");
  };


  my $buffer = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER/wizard_prontus/core/paso2.html");
  $msg_err = '';
  ($msg_err, $buffer) = &carga_modelos($buffer);
  if ($msg_err) {

    $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
    &glib_html_02::print_pag_result('Error', $msg_err, 0, "exit=1, ctype=1");

  };

  print "Content-Type: text/html\n\n";
  print $buffer;



};

# --------------------------------------------------------------------------------------------------
# SUB-RUTINAS.
# --------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------
sub carga_modelos {
    # Valida y carga modelos prontus disponibles.
    my $buffer = $_[0];
    my $models_dir = "$prontus_varglb::DIR_SERVER/wizard_prontus/models";
  
    if(! -d $models_dir) {
        return 'Directorio de modelos, no valido.';
    }
  
    my @lisdir = &glib_fildir_02::lee_dir($models_dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    my $k;
    my $nro_models;
    my ($loop_tpl, $loop_out, $loop_item);
    if ($buffer =~ /<!--LOOP_MODELS-->(.*?)<!--\/LOOP_MODELS-->/is) {
        $loop_tpl = $1;
    } else {
        return 'Error en plantilla wizard. No es posible continuar.';
    };
    foreach $k (@lisdir) {
        # localiza cfg descriptor del modelo,
        # si lo encuentra asume q se trata de un modelo.
        print STDERR "K[$k]\n";
        if (-f "$models_dir/$k/$k.cfg") {
            
            $loop_item = $loop_tpl;
            
            # valida icono
            my $imagen = "/wizard_prontus/models/$k/$k-thumb.png";
            if(-f "$prontus_varglb::DIR_SERVER$imagen") {
                $loop_item =~ s/%%MODEL_IMG%%/$imagen/isg;
            } else {
                $imagen = "/wizard_prontus/models/$k/$k.gif";
                if(-f "$prontus_varglb::DIR_SERVER$imagen") {
                    $loop_item =~ s/%%MODEL_IMG%%/$imagen/isg;
                } else {
                    return "En Modelo [$k] falta icono";
                }
            }
            
            # valida q este el arch de obs del modelo
            if (! -f "$models_dir/$k/descripcion/index.html") {
                return "En Modelo [$k] falta $k/descripcion/index.html";
            };
            $nro_models++;
            
            $loop_item =~ s/%%MODEL_NOM%%/$k/isg;
            
            # Deja el primero como seleccionado por defecto
            if ($nro_models == 1) {
                $loop_item =~ s/%%checked%%/checked/isg;
            } else {
                $loop_item =~ s/%%checked%%//isg;
            };
            $loop_out .= $loop_item;
            if($nro_models % 3 == 0) {
                $loop_out = $loop_out . '<div class="separador"></div>';
            }
        };
    };

    # Debe haber por lo menos 1 modelo.
    if (! $nro_models) {
        return "No hay Modelos Prontus disponibles.<br>No es posible continuar.";
    } else {
        $buffer =~ s/<!--LOOP_MODELS-->.*?<!--\/LOOP_MODELS-->/$loop_out/is;
        return ('', $buffer);
    };
};

# -------------------------------END SCRIPT----------------------

