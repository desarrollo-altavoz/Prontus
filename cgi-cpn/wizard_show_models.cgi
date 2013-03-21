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

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

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

main:{
  
    # Valida informacion de paso 1.
    my $msg_err = &wizard_lib::check_paso1();
    if ($msg_err) {
        $prontus_varglb::DIR_CORE = $wizard_lib::CORE_DIR; # solo para efectos de la plantilla de mensaje
        &glib_html_02::print_pag_result('Error', $msg_err, 0, "exit=1, ctype=1");
    };
    # lee la plantilla
    my $plantilla = "$prontus_varglb::DIR_SERVER$wizard_lib::CORE_DIR/models.html";
    my $buffer = &glib_fildir_02::read_file($plantilla);
    
    # Se leen los modelos instalados y disponibles
    my $refmodels = &wizard_lib::get_models();
    my %models = %$refmodels;
    
    # Parsea los modelos e imprime la plantilla
    $buffer = &parsea_modelos($buffer, $refmodels);    
    print "Content-Type: text/html\n\n";
    print $buffer;
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
# Parsea los modelos prontus disponibles.
sub parsea_modelos {

    my ($buffer, $refmodels) = @_;
    my %models = %$refmodels;

    my $nro_models;
    my ($loop_tpl, $loop_out, $loop_item);
    if ($buffer =~ /<!--LOOP_MODELS-->(.*?)<!--\/LOOP_MODELS-->/is) {
        $loop_tpl = $1;
    } else {
        my $msg_err = 'Error en plantilla wizard. No es posible continuar.';
        $prontus_varglb::DIR_CORE = $wizard_lib::CORE_DIR; # solo para efectos de la plantilla de mensaje
        &glib_html_02::print_pag_result('Error', $msg_err, 0, "exit=1, ctype=1");
    };
    
    my ($loop1, $loop2);
    foreach my $k (keys %models) {
        # localiza cfg descriptor del modelo,
        # si lo encuentra asume q se trata de un modelo.
        #~ my $refdatos = $models{$k};
        #~ my %datos = %refdatos;
        $loop_item = $loop_tpl;
        foreach my $dato (keys %{$models{$k}}) {
            #my $refdata = $datos{$dato};
            #~ print STDERR "$dato = $models{$k}{$dato}\n";
            $loop_item =~ s/%%model_$dato%%/$models{$k}{$dato}/ig;
        }
        $loop_item =~ s/%%model_id%%/$k/ig;
        
        if($models{$k}{'instalado'} eq 'instalado') {
            $loop1 = $loop1 . $loop_item;
        } else {
            $loop2 = $loop2 . $loop_item;
        }
    };
    $loop_out = $loop1 . $loop2;
    # Debe haber por lo menos 1 modelo.
    $buffer =~ s/<!--LOOP_MODELS-->.*?<!--\/LOOP_MODELS-->/$loop_out/is;
    return $buffer;
};

# -------------------------------END SCRIPT----------------------

