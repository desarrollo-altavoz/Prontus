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
# Armar y desplegar la ficha de Edicion
#---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
#------------------------------
# No registra.
#---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
#------------------------
# 1) Desde la pag. de Administracion de Ediciones, via boton 'Nuevo'
# sin parametros y via link para editar edicion, con param: nom_edi.
#---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
#------------------------
# ap_edi_ficha.html
#---------------------------------------------------------------
# Version  oficial 1.0 at 04/10/2000
# 1.1 - 20/11/2000 - Correccion en bug de expresion regular.

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
use glib_fildir_02;
use lib_prontus;

use glib_cgi_04;
use glib_hrfec_02;
use strict;

my ($RELDIR_EDICIONES);

my ($RELDIR_CONT_EDIC);

my ($RELDIR_CONT_MENU);

my ($RELDIR_CONT_SECC);

my ($RELDIR_CONT_HPAGE);


my (%FORM);
#---------------------------------------------------------------
# MAIN.
#-------------

my ($plantilla, $pagina, $homepage, $text_html, @arr_valores, $nro_campos, $i);
my ($valor_marca, $marca, $nom_campo, $nomport, $ediref);


  # Rescatar parametros recibidos
  &glib_cgi_04::new();
  $FORM{'_edic'} = &glib_cgi_04::param('_edic');
  $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});


  # Carga variables de configuracion.
  &lib_prontus::load_config($FORM{'_path_conf'});
  $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;


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
    &glib_html_02::print_pag_result('Error','Este Prontus no está configurado como multi edición', 1, 'exit=1,ctype=1');
  };


# Control de usuarios obligatorio chequeando la cookie contra el dbm.
($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
if ($prontus_varglb::USERS_ID eq '') {
    &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
};

    if ($prontus_varglb::EDITOR_ADMINISTRAR_EDICIONES eq 'NO' && $prontus_varglb::USERS_PERFIL eq 'E') {
        &glib_html_02::print_pag_result('Error', 'La funcionalidad requerida está disponible sólo para el administrador del sistema.', 1, 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL ne 'A' && $prontus_varglb::USERS_PERFIL ne 'E') {
        &glib_html_02::print_pag_result('Error', 'La funcionalidad requerida está disponible sólo para el administrador del sistema y editores', 1, 'exit=1,ctype=1');
    };


  # Cargar plantilla de la pagina a imprimir (ficha de edicion)
  $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/prontus_edi_ficha.html";
  $pagina = &glib_fildir_02::read_file($plantilla);


  # Nuevo
  if ($FORM{'_edic'} eq '') {
    # Poner combo Cmb_EDIC con ultimas 20 ediciones
    # Generar cod. html correspondiente a la combo de ediciones
    my $html_ediciones = &lib_prontus::generar_popupdirs_from_dir($prontus_varglb::DIR_SERVER . $RELDIR_EDICIONES, 'Cmb_EDIC', '', 1, '', '', '', $prontus_varglb::NRO_EDICS_WORK, 'STRDESC');
    $html_ediciones =~ s/<\/select>/<option value="" selected>&nbsp;<\/option><\/select>/is;; # agrega item en blanco
    # print STDERR "html_ediciones[$html_ediciones]";
    my $edic_base = $prontus_varglb::DIR_UNICAEDIC;
    $edic_base =~ s/^\///;
    $html_ediciones =~ s/<OPTION VALUE="$edic_base" >$edic_base<\/OPTION>//;

    $pagina =~ s/%%_path_conf%%/$FORM{'_path_conf'}/ig;
    $pagina =~ s/%%Cmb_EDIC%%/$html_ediciones/sg;
    $pagina =~ s/<!--ED_NOM-->.+<!--\/ED_NOM-->//sg;
    $pagina =~ s/%%ED_NOM%%//sg;
  }
  else {
    # Cargar homepage de la edicion en un string.
    &parse_dirs_edic($FORM{'_edic'});

    # Si la edicion actual es la vigente
    $marca = '%%ED_VIGENTE%%';
    if (&lib_prontus::ed_vigente($FORM{'_edic'}) eq 'SI') {
      $valor_marca = 'CHECKED="1"';
    }
    else {
      $valor_marca = '';
    }
    $pagina =~ s/$marca/$valor_marca/;



    $FORM{'_edic'} =~ /^(\d\d\d\d)\_(\d\d)\_(\d\d)/;
    my $feccorta = $3 . '/' . $2 . '/' . $1;

    $pagina =~ s/%%_path_conf%%/$FORM{'_path_conf'}/ig;
    
    $pagina =~ s/%%ED_NOM%%/$FORM{'_edic'}/sg;

    $pagina =~ s/<!--ED_FECCORTA-->.+<!--\/ED_FECCORTA-->/$feccorta/sg;

    $pagina =~ s/<!--BASE_EDIC-->.+<!--\/BASE_EDIC-->//sg;
  };

  $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;

  $pagina = &parse_all_edics($pagina);
  $pagina = &parse_port_list($pagina);

  print "Content-type: text/html\n\n";
  print $pagina;
  exit;


#---------------------------------------------------------------
# SUB-RUTINAS.
#-------------

sub parse_dirs_edic {
  my $nom_edic = $_[0];

  $RELDIR_CONT_EDIC =~ s/%%ED_NOM%%/$nom_edic/;

  $RELDIR_CONT_MENU =~ s/%%ED_NOM%%/$nom_edic/;

  $RELDIR_CONT_SECC =~ s/%%ED_NOM%%/$nom_edic/;

  $RELDIR_CONT_HPAGE =~ s/%%ED_NOM%%/$nom_edic/;

};

sub parse_all_edics {
    my $buffer = $_[0];
    my $filas;

    if ($prontus_varglb::MULTI_EDICION eq 'SI') {
        my @entries = &glib_fildir_02::lee_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EDIC");
        my %aux_sort;

        $buffer =~ /<!--port_all_edics-->(.*)<!--\/port_all_edics-->/is;
        my $loop = $1;

        return $buffer if (!$loop);

        foreach my $entry (@entries) {
            $entry =~ /^(\d\d\d\d)\_(\d\d)\_(\d\d)\_(\d+)$/;
            my $aaaammddnro = $1 . $2 . $3 . $4;
            $aux_sort{$entry} = $aaaammddnro;
        }

        # Ordena numericamente de mayor a menor.
        @entries = sort { $aux_sort{$b} <=> $aux_sort{$a} } @entries;
        my $nro_filas = scalar @entries;

        foreach my $entry (@entries) {
            if ($entry =~ /^\d\d\d\d\_\d\d\_\d\d\_/) {
                my $homepage = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EDIC/$entry$prontus_varglb::DIR_HPAGES/$prontus_varglb::INDEX_EDIC";
                if (-f $homepage) {
                    # Imprimir la fila de datos contenida en el hash.
                    $filas .= &generar_fila_edic($entry, $loop);
                }
            }
        }
    }

    $buffer =~ s/<!--port_all_edics-->.*<!--\/port_all_edics-->/$filas/s;

    return $buffer;
}

sub parse_port_list {
    my $buffer = $_[0];
    my %PORTS_TO_ORDER;

    $buffer =~ /<!--not_base_port_list-->(.*)<!--\/not_base_port_list-->/is;
    my $loop = $1;
    my $filas;

    return $buffer if (!$loop);

    foreach my $key (sort { $a cmp $b } keys %prontus_varglb::PORT_PLTS) {
        my $name = $key;
        $name = $prontus_varglb::PORT_PLTS_NOM{$key} if ($prontus_varglb::PORT_PLTS_NOM{$key} ne '');
        $name =~ s/^\s+//;
        $name =~ s/\s+$//;

        if ($name =~ /(.*?)\.(.*?)$/i) {
            $name =~ s/\.$2//ig;
        }

        $PORTS_TO_ORDER{$key} = $name;
    }

    my %base_ports = map {$_ => 1} @prontus_varglb::BASE_PORTS;


    foreach my $key (sort { lc($PORTS_TO_ORDER{$a}) cmp lc($PORTS_TO_ORDER{$b}) } keys %PORTS_TO_ORDER) {
        my $val_display = $prontus_varglb::PORT_PLTS_NOM{$key};

        if (!exists $base_ports{$key}) {
            my $tmp = $loop;
            $tmp =~ s/%%_portname%%/$key/sg;

            $filas .= $tmp;
        }
    }

    print STDERR "filas[$filas]\n";

    $buffer =~ s/<!--not_base_port_list-->.*<!--\/not_base_port_list-->/$filas/s;

    return $buffer;
};

sub generar_fila_edic {
    my ($ed_nom, $loop_row) = @_;
    $loop_row =~ s/%%_nombre_edic%%/$ed_nom/g;
    # Celda con fecha de la edicion.
    $ed_nom =~ /^(\d\d\d\d)\_(\d\d)\_(\d\d)/;
    my $aaammdd = $1 . $2 . $3;
    my $fechaplong = &glib_hrfec_02::expande_fecha($aaammdd);

    $loop_row =~ s/%%_fecha_edic%%/$fechaplong/g;

    my $vigente_class = 'default';
    my $vigente_status = 0;
    my $vigente_status_name = 'No vigente';

    if (&lib_prontus::ed_vigente($ed_nom) eq 'SI') {
        $vigente_class = 'success';
        $vigente_status = 1;
        $vigente_status_name = 'Vigente';
    }

    $loop_row =~ s/%%ed_vigente%%/$vigente_class/g;
    $loop_row =~ s/%%ed_vigente_status%%/$vigente_status/g;
    $loop_row =~ s/%%ed_vigente_status_name%%/$vigente_status_name/g;

    my $ver_edic = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EDIC/$ed_nom$prontus_varglb::DIR_HPAGES/$prontus_varglb::INDEX_EDIC";

    $loop_row =~ s/%%_ver_edic%%/$ver_edic/g;

    return $loop_row;
}

#-------------------------------END SCRIPT----------------------
