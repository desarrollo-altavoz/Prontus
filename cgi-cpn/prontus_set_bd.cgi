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
# Chequear / conectar un usuario al sistema.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# 2) Desde la pag. de ingreso al Sistema, via boton 'Ingresar'.
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# No registra.
# ---------------------------------------------------------------

# 1.1 - 16/05/2001 - Modificaciones para parametrizacion del protocolo (http o https) a traves del arch. de conf.
# 1.2 - 16/05/2001 - Revision general de detalles de forma.
# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0

# Prontus 8.0 - 01/08/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_dbi_02;
use glib_cgi_04;

use lib_prontus;
use lib_setbd;

use strict;

use DBI; # SQLITE




# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM, $TIPO_PRONTUS, $AREA_MENU, $AREA_CONT, $PRONTUS_KEY);
my ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_ID);
my ($RESULT);
my ($HAY_ERROR) = 0;
my $RELPATHFILE_SQLITE;

main: {

    &lib_prontus::setUtf8();
    my ($lnk);

    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});


    $FORM{'Sbm_ACCION'} = &glib_cgi_04::param('sbm_accion');


    # Carga var. globales con los datos del arch. conf.
    &lib_prontus::load_config($FORM{'path_conf'});   # Prontus 6.0
    $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL ne 'A') {
        print "Content-Type: text/html\n\n";
        &glib_html_02::print_pag_result("Acceso a Area Restringida","La funcionalidad requerida está disponible sólo para el administrador del sistema",1,'exit=1,ctype=1');
        exit;
    };

    # Conectar a BD
    my $msg_err_bd;
    my $base;
    ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();

    $RELPATHFILE_SQLITE = "$prontus_varglb::DIR_DBM/prontus_db.db";

    if ($FORM{'Sbm_ACCION'} =~ /^Crear/i) {
        if (! ref($base)) {
            # si no esta el file sqlite, lo crea con el connect manual
#            if (($prontus_varglb::MOTOR_BD eq 'PRONTUS') && (! -f "$prontus_varglb::DIR_SERVER$RELPATHFILE_SQLITE")) {
#                my $path_sqlite = "$prontus_varglb::DIR_SERVER$RELPATHFILE_SQLITE";
#                $base = DBI->connect("dbi:SQLite2:dbname=$path_sqlite","","")
#                      || warn "DBI Error Code: $DBI::err";
#                if (! ref($base)) {
#                    $msg_err_bd = "No es posible conectar con base de datos Prontus SQLite en $RELPATHFILE_SQLITE. Cod[$DBI::err]" if ($DBI::err);
#                    &glib_html_02::print_pag_result("Error",$msg_err_bd,1,'exit=1,ctype=1');
#                };
#            };
            &glib_html_02::print_pag_result("Error",$msg_err_bd,1,'exit=1,ctype=1');
        };
        &crear_tablas($base);
    }
    elsif ($FORM{'Sbm_ACCION'} =~ /^Listar/i) {
        if (! ref($base)) {
            &glib_html_02::print_pag_result("Error",$msg_err_bd,1,'exit=1,ctype=1');
        };
        &listar_tablas($base);
    }
    else {
        $base->disconnect;
        &glib_html_02::print_pag_result("Error",'Requerimiento no válido.',1,'exit=1,ctype=1');
    };
    $base->disconnect;
    print "Content-Type: text/html\n\n";
    print $RESULT;
    #print "<p>&nbsp;</p><a href='#' onclick='parent.Opciones.cerrarColorbox();' style='color:#0099ff;; font-weight:bold; text-decoration:none;'>[Cerrar]</a>\n";

};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub salir {
  my $msg = $_[0];
  print "Content-Type: text/html\n\n";
  print $msg;
  print "<p>&nbsp;</p><a href='#' onclick='parent.Opciones.cerrarColorbox();' style='color:#0099ff;; font-weight:bold; text-decoration:none;'>[Cerrar]</a>\n";
  exit;
};
# ---------------------------------------------------------------
sub crear_tablas {
    my ($base) = $_[0];


    &add2result("<html><head><link type=\"text/css\" rel=\"stylesheet\" href=\"/$prontus_varglb::PRONTUS_ID/cpan/core/css/estilos.css\" /></head><body><span class=\"check-install\"><div class=\"desc\"><b>Creando tablas en BD MySQL: $prontus_varglb::NOM_BD</b><br/><div class=\"desc\" style=\"text-align:left\">");

    my ($msg_ret, $hay_err);

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_secc($base, $prontus_varglb::MOTOR_BD);
    &add2result($msg_ret, $hay_err);

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_temas($base, $prontus_varglb::MOTOR_BD);
    &add2result($msg_ret, $hay_err);

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_subtemas($base, $prontus_varglb::MOTOR_BD);
    &add2result($msg_ret, $hay_err);

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_tags($base, $prontus_varglb::MOTOR_BD);
    &add2result($msg_ret, $hay_err);

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_tagsart($base, $prontus_varglb::MOTOR_BD);
    &add2result($msg_ret, $hay_err);

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_coment($base, $prontus_varglb::MOTOR_BD);
    &add2result($msg_ret, $hay_err);

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_asset($base, $prontus_varglb::MOTOR_BD);
    &add2result($msg_ret, $hay_err);

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_art($base, $prontus_varglb::MOTOR_BD);
    &add2result($msg_ret, $hay_err);

    &add_html2result('</div></span></body></html>');

};
# ---------------------------------------------------------------
sub add2result {
  # SQLITE
  my $msg = $_[0];
  my $werr = $_[1];
  if ($werr) {
    $HAY_ERROR = 1;
    $RESULT .= "$msg<br/>";
  }
  else {
    $RESULT .= "$msg<br/>";
    $HAY_ERROR = 0;
  };
};

# ---------------------------------------------------------------
sub add_html2result {
  # SQLITE
  my $html = $_[0];
  $RESULT .= $html;
};

# ---------------------------------------------------------------
sub listar_tablas {
  my ($base) = $_[0];

  my ($sql, $res);

  # MYSQL
  if ($prontus_varglb::MOTOR_BD eq 'MYSQL') {
    my $nom;
    $sql = "show tables";

    my $charset = &get_charset($base, $prontus_varglb::NOM_BD);
    $charset = " ($charset)" if($charset);

    # $RESULT .= "<b>Tablas en base de datos: $prontus_varglb::NOM_BD</b>&nbsp;&nbsp;<INPUT TYPE='button' VALUE='Cerrar' OnClick='javascript:window.close();'><br><br>";
    $RESULT .= "<html><head><link rel=\"stylesheet\" type=\"text/css\" href=\"/$prontus_varglb::PRONTUS_ID/cpan/core/css/estilos.css\" /></head><body>";
    $RESULT .= "<span class=\"check-install\"><div class=\"desc\"><b>Tablas en Base de Datos MySQL: $prontus_varglb::NOM_BD $charset</b><br><br>";
    $RESULT .= "<div class=\"desc\" style=\"text-align:left;\">";

    my $res = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($nom));
    # $RESULT .= '<br>------------<br>';
    while ($res->fetch) {
      my $count;

      $count = &get_count($base, $nom);
      $nom = '<b>' . $nom . '</b>';

      if ($count ne '') {
        $RESULT .= "En la tabla [$nom] se encontraron: $count registros<br/>";
      } else {
        $RESULT .= "En la tabla [$nom]... no se pudo obtener la información<br/>";
      };
    };
    $RESULT .= "</div></div></span></body>";
    $res->finish;
  };


};
# ---------------------------------------------------------------
sub get_count {
  my ($base) = $_[0];
  my ($tabla) = $_[1];
  my ($sql, $salida, $nom);
  my $campo = $tabla . '_ID';
  $campo = 'ASSET_ART_ID' if ($tabla eq 'ASSET');
  $campo = 'TAGSART_IDTAGS' if ($tabla eq 'TAGSART');
  $sql = "SELECT count($campo) from $tabla";
  $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($nom));
  $salida->fetch;
  $salida->finish;
  $nom = '0' if (!$nom);
  return $nom;
};
# ---------------------------------------------------------------
sub get_charset {
  my ($base) = $_[0];
  my ($nombd) = $_[1];
  my ($sql, $salida, $charset);
  $sql = "SELECT default_character_set_name FROM information_schema.schemata WHERE schema_name='$nombd';";
  $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($charset));
  $salida->fetch;
  $salida->finish;
  return $charset;
};

# -------------------------------END SCRIPT----------------------

