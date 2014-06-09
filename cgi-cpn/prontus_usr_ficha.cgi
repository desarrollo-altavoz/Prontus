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

# # Carga la ficha del usuario en base a 3 hash en disco :
# 1) %prontus_varglb::USERS : key = id del usr ; value = valores de las columnas separadas por '|' en el sgte. orden :
# ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL)
#
# 2) %prontus_varglb::ARTUSERS : key = id del tipo de art y id del user separados por '|' ; value = 'filler';
# El id de tipo de articulo corresponde al nombre del formulario html correspondiente a el. (ej .: prontus_art_ficha1.html)
#
# 3) %prontus_varglb::PORTUSERS : key = id de portada y id de user separados por '|' ; value = 'filler';
# El id de portada corresponde al nombre de la portada html, por ej. politica.html
#
# Los hash se almacenan en el dir $prontus_varglb::DIR_DBM  con su mismo nombre con extension .dbm, ej.: users.dbm

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

# 1.1 - 16/05/2001 - Revision general de detalles de forma.
# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0
# Revision Prontus 8.0 - ych - 23/05/2002
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ---------------------------------------------------------------

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
use glib_cgi_04;

use lib_prontus;

use strict;
my $LIMITE_CHARS_NAME = 28;

# ---------------------------------------------------------------
# MAIN.
# -------------
my (%COOKIES, %FORM);
my ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_ID, $USERS_EMAIL);

main: {
    my ($value, $pagina, $plantilla, $cmb_perfil, $lst_artasoc, $lst_artdisp, $dir_tpl_seccs, $lst_portasoc, $lst_portdisp);
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta _path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});


    $FORM{'USERS_ID'} = &glib_cgi_04::param('USERS_ID');

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL ne 'A') {
        &glib_html_02::print_pag_result('Error','La funcionalidad requerida está disponible sólo para el administrador del sistema.', 1, 'exit=1,ctype=1');
    };

    $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . '/prontus_usr_ficha.html';

    if (&lib_prontus::open_dbm_files() ne 'ok') {
        print "Content-Type: text/html\n\n";
        &glib_html_02::print_pag_result("Error","No fue posible abrir archivos dbm.");
        exit;
    };


    # Si se trata de editar
    if ($FORM{'USERS_ID'} ne '') {
        $value = $prontus_varglb::USERS{$FORM{'USERS_ID'}};
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $value;
    };

    #~ $lst_artdisp = &get_lst_tipoart();
    $dir_tpl_seccs = $prontus_varglb::DIR_SERVER .
                   $prontus_varglb::DIR_TEMP .
                   $prontus_varglb::DIR_EDIC .
                   $prontus_varglb::DIR_NROEDIC .
                   $prontus_varglb::DIR_SECC;

    $cmb_perfil = &get_cmb_perfil();

    $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . '/prontus_usr_ficha.html';
    $pagina = &glib_html_02::rellenar_plantilla(10, '%%USERS_ID%%', $FORM{'USERS_ID'},'','',
                                                    '%%EMAIL%%', $USERS_EMAIL,'','',
                                                    '%%NOM%%', $USERS_NOM,'','',
                                                    '%%USR%%', $USERS_USR,'','',
                                                    '%%Cmb_PERFIL%%', $cmb_perfil,'','',
                                                    '%%_path_conf%%', $FORM{'_path_conf'},'','',
                                                    $plantilla);
    
    #~ Se procesan los checks de Tipo de Artículo
    if($FORM{'USERS_ID'} eq '1') {
        $pagina =~ s/%%loop_artics%%(.*?)%%\/loop_artics%%//is;
        
    } elsif($pagina =~ /%%loop_artics%%(.*?)%%\/loop_artics%%/is) {
        my $loop = $1;
        $lst_artdisp = &get_lst_tipoart($loop);
        $pagina =~ s/%%loop_artics%%(.*?)%%\/loop_artics%%/$lst_artdisp/is;
        
    } else {
        print "Content-Type: text/html\n\n";
        &glib_html_02::print_pag_result("Error","Error en la plantilla. No se encuentra el Loop de Artículos");
        exit;
    }
    
    #~ Se procesan los checks de Portada
    if($FORM{'USERS_ID'} eq '1') {
        $pagina =~ s/%%loop_ports%%(.*?)%%\/loop_ports%%//is;
        
    } elsif($pagina =~ /%%loop_ports%%(.*?)%%\/loop_ports%%/is) {
        my $loop = $1;
        $lst_portdisp = &get_lst_port($loop);
        $pagina =~ s/%%loop_ports%%(.*?)%%\/loop_ports%%/$lst_portdisp/is;
        
    } else {
        print "Content-Type: text/html\n\n";
        &glib_html_02::print_pag_result("Error","Error en la plantilla. No se encuentra el Loop de Portadas");
        exit;
    }
    
    # &lib_prontus::close_dbm_files();
    if ($FORM{'USERS_ID'} ne '') {
        # deshabilitar ingreso o modif. de campo usr.
        $pagina =~ s/<!--USR-->.*?<!--\/USR-->/<SPAN CLASS="P-LABELTABLA">$USERS_USR<\/SPAN><input type="hidden" name="USR" value="$USERS_USR">/sg;
        $pagina =~ s/<!--SOLONEW-->.*?<!--\/SOLONEW-->//sg;
    } else {
        $pagina =~ s/<!--SOLOEDIT-->.*?<!--\/SOLOEDIT-->//sg;
    };

    if ($FORM{'USERS_ID'} eq '1') { # admin
        # no mostrar listas de seleccion de tipos de art. y portadas.
        $pagina =~ s/<!--LISTAS-->.*?<!--\/LISTAS-->//sg;
        $pagina =~ s/<!--PERFIL-->.*?<!--\/PERFIL-->/<SPAN CLASS="P-LABELTABLA">Administrador<\/SPAN><input type="hidden" name="Cmb_PERFIL" value="A">/sg;
    };
    
    $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/ig;
    $pagina =~ s/<!--\w+-->//sg;
    $pagina =~ s/<!--\/\w+-->//sg;
    print "Cache-Control: no-cache\n";
    print "Cache-Control: max-age=0\n";
    print "Cache-Control: no-store\n";
    print "Content-Type: text/html\n\n";
    print $pagina;
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

sub get_cmb_perfil {
  my $cmb =
          '<select name="Cmb_PERFIL">
            <option value="P">Redactor</option>
            <option value="E">Editor</option>
          </select>';

  if ($USERS_PERFIL eq 'P') {
    $cmb =~ s/value="P"/value="P" selected/;
  }
  elsif ( ($USERS_PERFIL eq 'E') or ($USERS_PERFIL eq '') ) {
    $cmb =~ s/value="E"/value="E" selected/;
  };


  return $cmb;

};

# ---------------------------------------------------------------
sub get_lst_tipoart {
    
    my ($loop) = @_;
    my ($looptot, $looptmp);
    my ($key, $key2, $val_display, $clave, $lista, %tipoart_usr);
    
    foreach $key2 (keys %prontus_varglb::ARTUSERS) {
        my ($tipart, $usr) = split /\|/, $key2;
        if ( ($usr eq $FORM{'USERS_ID'})) {
            $tipoart_usr{$tipart} = 1;
        };
    };
    
    foreach $key (sort keys %prontus_varglb::FORM_PLTS) {
        $val_display = $key;
        $val_display =~ s/^.*://;
        $clave = $key;
        $clave =~ s/:.*$//;

        my $checked;
        my $label_class;
        if (defined $tipoart_usr{$clave}) {
            $checked = "checked=\"checked\"";
            $label_class = "class=\"checked\"";
        };
        my $val_display_short = &procesar_nombre($val_display);
        
        $looptmp = $loop;
        $looptmp =~ s/%%clave%%/$clave/isg;
        $looptmp =~ s/%%val_display%%/$val_display/isg;
        $looptmp =~ s/%%val_display_short%%/$val_display_short/isg;
        $looptmp =~ s/%%checked%%/$checked/isg;
        $looptmp =~ s/%%label_class%%/$label_class/isg;
        
        $looptot = $looptot . $looptmp;
    };
    
    return $looptot;
};

# ---------------------------------------------------------------
sub get_lst_port {
    
    my ($loop) = @_;
    my ($looptot, $looptmp);
    my ($key, $key2, %port_usr, $val_display, $clave, $lista);
    
    foreach $key2 (keys %prontus_varglb::PORTUSERS) {
        my ($port, $usr) = split /\|/, $key2;
        if ( ($usr eq $FORM{'USERS_ID'})) {
            $port_usr{$port} = 1;
        };
    };
        
    foreach $key (sort keys %prontus_varglb::PORT_PLTS) {
        $val_display = $key;
        $val_display =~ s/\..*$//;
        $clave = $key;

        my $checked;
        my $label_class;
        if ($port_usr{$clave}) {
            $checked = "checked=\"checked\"";
            $label_class = "class=\"checked\"";
        };
        my $val_display_short = &procesar_nombre($val_display);
        
        $looptmp = $loop;
        $looptmp =~ s/%%clave%%/$clave/isg;
        $looptmp =~ s/%%val_display%%/$val_display/isg;
        $looptmp =~ s/%%val_display_short%%/$val_display_short/isg;
        $looptmp =~ s/%%checked%%/$checked/isg;
        $looptmp =~ s/%%label_class%%/$label_class/isg;
        
        $looptot = $looptot . $looptmp;
        #$lista = $lista . "<div class=\"itemlistado\"><input type=\"checkbox\" value=\"$clave\"  name=\"ports[]\" id=\"$val_display\" $checked\/> <label for=\"$val_display\" $label_class>$val_display<\/label><\/div>";
    
    };
    
    return $looptot;
    
};
# ---------------------------------------------------------------
sub procesar_nombre {
    
    my ($nombre) = shift;
    if(length ($nombre) > $LIMITE_CHARS_NAME) {
        
        my $newname = substr($nombre, 0, $LIMITE_CHARS_NAME - 3);
        $nombre = $newname . '...';
        
        
    };
    return $nombre;
    
}
# -------------------------------END SCRIPT----------------------
