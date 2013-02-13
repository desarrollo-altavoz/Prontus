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
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ---------------------------------------------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};


use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;

use lib_prontus;


use strict;


# ---------------------------------------------------------------
# MAIN.
# -------------
my (%FORM);


main: {
  my ($value, $pagina, $plantilla);

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

  # Acceso permitido solo para admin
  if (($prontus_varglb::ADMIN_PORT ne 'SI') or ($prontus_varglb::USERS_PERFIL ne 'A')) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Acceso a Area Restringida", "La funcionalidad requerida est&aacute; disponible s&oacute;lo para el administrador del sistema,<br>siempre que &eacute;sta haya sido previamente configurada.");
    exit;
  };

  $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . '/prontus_pltport_admin.html';

  my ($dir);
  $dir = $prontus_varglb::DIR_SERVER .
         $prontus_varglb::DIR_TEMP .
         $prontus_varglb::DIR_EDIC .
         $prontus_varglb::DIR_NROEDIC .
         $prontus_varglb::DIR_SECC;

  my $lst_port1 = &get_html_secciones($dir, 'Lst_PORT1');
  my $lst_port2 = &get_html_secciones($dir, 'Lst_PORT2');
  my $lst_port3 = &get_html_secciones($dir, 'Lst_PORT3');
  my $lst_port4 = &get_html_secciones($dir, 'Lst_PORT4');

  $dir = $prontus_varglb::DIR_SERVER .
         $prontus_varglb::DIR_TEMP .
         $prontus_varglb::DIR_EDIC .
         $prontus_varglb::DIR_NROEDIC .
         $prontus_varglb::DIR_SPARE;


  $pagina = &glib_html_02::rellenar_plantilla(5, '%%Lst_PORT1%%', $lst_port1,'','',
                                                 '%%Lst_PORT2%%', $lst_port2,'','',
                                                 '%%Lst_PORT3%%', $lst_port3,'','',
                                                 '%%Lst_PORT4%%', $lst_port4,'','',
                                                 '%%_path_conf%%', $FORM{'_path_conf'},'','',
                                                 $plantilla);
    
    $pagina = &lib_prontus::set_coreplt_ppal($pagina);
        # En primer lugar, agrega macros
    my ($dir_macros_cpan) = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/macros";
    $pagina = &lib_prontus::add_macros($pagina, $dir_macros_cpan, '', '');
    $pagina =~ s/%25%25/%%/sg;

    # oculta html correspondiente solo a admin
    $pagina =~ s/<!--admin_only-->.*?<!--\/admin_only-->//sg if ($prontus_varglb::USERS_PERFIL ne 'A');

  $pagina =~ s/%%REL_PATH_PRONTUS%%/$prontus_varglb::RELDIR_BASE\/$prontus_varglb::PRONTUS_ID/isg;
  $pagina =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/isg;

  # Saca boton "duplicar para multied" si no es un prontus con multied.
  if ($prontus_varglb::MULTI_EDICION ne 'SI') {
    $pagina =~ s/<!--multied-->.*?<!--\/multied-->//isg;
  };

  print "Cache-Control: no-cache\n";
  print "Cache-Control: max-age=0\n";
  print "Cache-Control: no-store\n";
  print "Content-Type: text/html\n\n";
  print $pagina;
};



# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub get_html_secciones {
    my($dir) = $_[0];
    my($name_obj) = $_[1];
    my($valor_clave) = '';
    my($items_visibles) = '12';
    my($ind_multiple) = '';
    my($javascript) =  '';

    my($lista) = '';


    my($val_display, $key, $clave);


    # Generar la lista de seleccion en html
    $lista = q{<select name="} . $name_obj . q{" SIZE="} . $items_visibles . q{" } . $ind_multiple . ' ' . $javascript . q{>};



    foreach $key (sort {$a cmp $b} keys %prontus_varglb::PORT_PLTS) {

        $val_display = $key;

        if ($prontus_varglb::PORT_PLTS_NOM{$key} ne '') {
            $val_display = $prontus_varglb::PORT_PLTS_NOM{$key};
            $val_display = ($val_display);
        };


        # La clave de los items de la combo sera lo que esta antes de los 2 puntos (nombre del arch. html que se usara como ficha).
        $clave = $key;

        # print STDERR "  \nclave[$clave]";


        # si es multied, considerar solo las de la ed. base
        #if ($prontus_varglb::MULTI_EDICION eq 'SI') {
        #    my $found;
        #    foreach my $bport (@prontus_varglb::BASE_PORTS) {
        #        if ($clave eq $bport) {
        #            $found = 1;
        #        };
        #    };
        #    if (!$found) {
        #        next;
        #    };
        #};

        # las portadas base, marcarlas con un *.
        if ($prontus_varglb::MULTI_EDICION eq 'SI') {
            my $found;
            foreach my $bport (@prontus_varglb::BASE_PORTS) {
                if ($clave eq $bport) {
                    $val_display = $key . ' *';
                };
            };
        };


        if (! -f "$dir/$clave") {

            $val_display .= ' (X)';
            $clave = '';

        };

        my $seleccionado = '';
        if ( $clave eq $valor_clave ) {
            $seleccionado = 'selected="selected"';
        };

        $lista = $lista . '<option value="' . $clave . '" ';

        # CVI - 29/03/2011 - Cambio estético y de interface
        $lista = $lista . ' class="port-base"' if($val_display =~ / \*$/);

        $lista = $lista . $seleccionado . '>';
        $lista = $lista . $val_display . '</option>'."\n"; # 01.i
    };


    $lista = $lista . q{</select>};

    return $lista;

};



# -------------------------------END SCRIPT----------------------
