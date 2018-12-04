#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

#-------------------------------COMENTARIO GLOBAL---------------
#---------------------------------------------------------------
# PROPOSITO .
#-----------
# SSI que despliega la lista de Ediciones ....
#
#---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
#------------------------------


#---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
#------------------------
# 1) Desde ap_edi_otras.shtml (sin param.) como SSI.
#---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
#------------------------
# No registra.
#---------------------------------------------------------------
# Version  oficial 1.0 at 04/10/2000
# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0
# Prontus 8.0 - 23/05/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
#-------------------------------BEGIN SCRIPT--------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

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

#---------------------------------------------------------------
# MAIN.
#-------------

my ($RELDIR_EDICIONES);

my ($RELDIR_CONT_EDIC);

my ($RELDIR_CONT_MENU);

my ($RELDIR_CONT_SECC);

my ($RELDIR_CONT_HPAGE);

&main();

sub main {

  my ($nro_filas, @entries, $entry, $dir_homepages, $nom_campo, $i, $homepage, $id_edicion);

  &glib_cgi_04::new();
  $FORM{'path_conf'} = &glib_cgi_04::param('path_conf');
  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

  # Carga variables de configuracion.
  &lib_prontus::load_config($FORM{'path_conf'});
  $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

  ($RELDIR_EDICIONES) = $prontus_varglb::DIR_CONTENIDO .
                         $prontus_varglb::DIR_EDIC;

  ($RELDIR_CONT_EDIC) = $RELDIR_EDICIONES .
                         "/%%ED_NOM%%";

  ($RELDIR_CONT_MENU) = $RELDIR_CONT_EDIC .
                         $prontus_varglb::DIR_MENU;

  ($RELDIR_CONT_SECC) = $RELDIR_CONT_EDIC .
                         $prontus_varglb::DIR_SECC;

  ($RELDIR_CONT_HPAGE) = $RELDIR_CONT_EDIC .
                          $prontus_varglb::DIR_HPAGES;

  if ($prontus_varglb::MULTI_EDICION ne 'SI') {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),&lib_language::_msg_prontus('_prontus_not_configured_multi _edition'));
    exit;
  };

  # Control de usuarios obligatorio chequeando la cookie contra el dbm.
  ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

  print "Content-Type: text/html\n\n";

  # $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . '/prontus_edi_otras.html';
  # $pagina = &glib_html_02::rellenar_plantilla(1,  '%%FILAS%%', $filas ,'','', $plantilla);
  my $pagina = &glib_fildir_02::read_file($prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . '/prontus_edi_otras.html');
  $pagina = &lib_prontus::set_coreplt_ppal($pagina);

  # En primer lugar, agrega macros
  my ($dir_macros_cpan) = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/macros";
  $pagina = &lib_prontus::add_macros($pagina, $dir_macros_cpan, '', '');
  $pagina =~ s/%25%25/%%/sg;
    
  $pagina =~ /<!--item_loop-->(.*)<!--\/item_loop-->/is;
  my $loop = $1;

  my $lista = &make_lista($loop);
  $pagina =~ s/<!--item_loop-->.*<!--\/item_loop-->/$lista/s;
  
  if ($lista eq '') {
  my $str = &lib_language::_msg_prontus('_no_previous_edition');
  	$pagina =~ s/%%_edic_msg%%/$str/isg;
  	$pagina =~ s/<!--ul-->.*<!--\/ul-->//s;
  } else {
  	$pagina =~ s/<!--edic_msg-->.*<!--\/edic_msg-->//s;
  };
  
  $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;

  print $pagina;


};

#---------------------------------------------------------------
# SUB-RUTINAS.
#-------------
sub parse_dirs_edic {
  my $nom_edic = $_[0];

  ($RELDIR_CONT_EDIC) = $RELDIR_EDICIONES .
                         "/%%ED_NOM%%";

  ($RELDIR_CONT_MENU) = $RELDIR_CONT_EDIC .
                         $prontus_varglb::DIR_MENU;

  ($RELDIR_CONT_SECC) = $RELDIR_CONT_EDIC .
                         $prontus_varglb::DIR_SECC;

  ($RELDIR_CONT_HPAGE) = $RELDIR_CONT_EDIC .
                          $prontus_varglb::DIR_HPAGES;


  $RELDIR_CONT_EDIC =~ s/%%ED_NOM%%/$nom_edic/;

  $RELDIR_CONT_MENU =~ s/%%ED_NOM%%/$nom_edic/;

  $RELDIR_CONT_SECC =~ s/%%ED_NOM%%/$nom_edic/;

  $RELDIR_CONT_HPAGE =~ s/%%ED_NOM%%/$nom_edic/;

};
# ---------------------------------------------------------------
sub make_lista {
    my ($loop) = shift;
    # Para c/home page de edicion, obtener valores de los campos de la edicion.
    my @entries = &glib_fildir_02::lee_dir($prontus_varglb::DIR_SERVER . $RELDIR_EDICIONES);

    #  Utiliza un hash auxiliar con las fecha de las ediciones en iso + el correlativo para ordenar.
    my %aux_sort;
    foreach my $entry (@entries) {
        $entry =~ /^(\d\d\d\d)\_(\d\d)\_(\d\d)\_(\d+)$/;
        my $aaaammddnro = $1 . $2 . $3 . $4;
        $aux_sort{$entry} = $aaaammddnro;
    };

    my $filas;

    # Ordena numericamente de mayor a menor.
    @entries = sort { $aux_sort{$b} <=> $aux_sort{$a} } @entries;
    my ($ed_visible);
    my $nro_filas;
    foreach my $entry (@entries) {
        if (($entry !~ /^\./g) and ($entry =~ /^\d\d\d\d\_\d\d\_\d\d\_/)) {
            &parse_dirs_edic($entry);
            my $homepage = $prontus_varglb::DIR_SERVER . $RELDIR_CONT_HPAGE . "/$prontus_varglb::INDEX_EDIC";

            if ((-f $homepage) and ($nro_filas + 1 > $prontus_varglb::NRO_EDICS_WORK)) {
                # Imprimir la fila de datos contenida en el hash.
                $filas .= &generar_fila($entry, $loop);
                $nro_filas++;
            };
        };
    };

    return $filas;

};
# ---------------------------------------------------------------
sub generar_fila {
    my ($ed_nom, $loop_row) = @_;


    $loop_row =~ s/%%_edic%%/$ed_nom/g;

    # Celda con fecha de la edicion.
    $ed_nom =~ /^(\d\d\d\d)\_(\d\d)\_(\d\d)/;
    my $aaammdd = $1 . $2 . $3;
    my $fechaplong = &glib_hrfec_02::expande_fecha($aaammdd);

    $loop_row =~ s/%%_fecha_edic%%/$fechaplong/g;

    my $vigente = 'novigente';
    if (&lib_prontus::ed_vigente($ed_nom) eq 'SI') {
        $vigente = 'vigente';
    }

    $loop_row =~ s/%%_vigente%%/$vigente/g;

    my $ver_edic = $RELDIR_CONT_HPAGE . "/$prontus_varglb::INDEX_EDIC";

    $loop_row =~ s/%%_ver_edic%%/$ver_edic/g;

    return $loop_row;


};

#-------------------------------END SCRIPT----------------------
