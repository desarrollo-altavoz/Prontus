#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

#/cgi-cpn/prontus_check_install.cgi?prontus=/prontus_dev

#Prontus - Chequeo de Instalación
#
#- Chequear escritura en carpetas de /prontus_dev
#
#- Crear tabla de pruebas en la BD (de acuerdo al cfg de este prontus).
#Tabla: PRUEBA. Columnas: PRUEBA_ID y PRUEBA_TITULAR.
#Si no existe, se crea. Si ya existe, se borra la que estaba antes.
#
#- Escribir un registro en la tabla PRUEBA. ID correlativo.
#
#- Escribir un registro en la tabla PRUEBA usando lock/unlock, tal como lo hace Prontus.
#
#- Escribir 10 registros (ID correlativo) en la tabla PRUEBA.
#
#- Leer y listar el contenido de la tabla PRUEBA.

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
use lib_prontus;
use glib_dbi_02;
use glib_html_02;
use glib_cgi_04;
use glib_fildir_02;
use lib_waitlock; # Bloqueos tipo espera.
use glib_hrfec_02;
use lib_setbd;



use strict;
# $| = 1; # wuatea en windows

# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM, $BD);
my $PRONTUS_DIR_CREADO_POR_CGI = 0;
my ($CERRAR) = "<center><a href=\"javascript:window.close()\">Cerrar</a></center>";
my ($FIN_OK) = "<BR><B style='color:#008000'>** " . &lib_language::_msg_prontus('_finnish_test_ok') . " **</B>";

main: {
  my ($perfil, $id_usr);

  &lib_prontus::setUtf8();
  # Rescatar parametros recibidos.
  &glib_cgi_04::new();
  $FORM{'accion'} = &glib_cgi_04::param('accion');
  $FORM{'_prontus_id'} = &glib_cgi_04::param('_prontus_id'); # ejemplo : /publicadores/prontus_noticias
  $FORM{'wizard'} = &glib_cgi_04::param('wizard'); # 1 | 0: para saber si viene del wizard

  print "Content-Type: text/html\n\n";
  # print "$CERRAR<br><br>";

  &valida_param();


  if ($FORM{'accion'} == 1) {
    print "<B>" . &lib_language::_msg_prontus('_testing_read_write') . " $FORM{'_prontus_id'} :</B><br>";
    &check_write();
    print $FIN_OK;
  }
  elsif ($FORM{'accion'} == 2) {
    print &lib_language::_msg_prontus('_testing_create_table');
    &crear_tabla();
    print $FIN_OK;
  }
  elsif ($FORM{'accion'} == 3) {
    print &lib_language::_msg_prontus('_testing_insert');
    &escribir_reg();
    print $FIN_OK;
  }
  elsif ($FORM{'accion'} == 4) {
    print &lib_language::_msg_prontus('_testing_insert_lock');
    &test_lock();
    print $FIN_OK;
  }

  elsif ($FORM{'accion'} == 5) {
    print &lib_language::_msg_prontus('_testing_10_insert');
    &escribir_diez_reg();
    print $FIN_OK;
  }
  elsif ($FORM{'accion'} == 6) {
    print &lib_language::_msg_prontus('_testing_table');
    &query_table();
    print $FIN_OK;
  }
  else {
    print '
<HTML>
<HEAD>
  <TITLE>' . &lib_language::_msg_prontus('_prontus_test') . '</TITLE>
  <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=iso-8859-1">
</HEAD>
<BODY bgColor=#ffffff leftMargin=0 topMargin=0 marginheight = 0 marginwidth = 0 >


<FORM METHOD="POST" ACTION="prontus_check_install.cgi" ENCTYPE="multipart/form-data" name="f1" target="_blank">
<input type="hidden" name="_prontus_id" value="' . $FORM{'_prontus_id'} . '">
<input type="hidden" name="wizard" value="' . $FORM{'wizard'} . '">

  <center><b>Prontus - ' . &lib_language::_msg_prontus('_install_test') . '</b></center>
  <br>

 <input type="radio" name="accion" value="1">' . &lib_language::_msg_prontus('_check_write_directory') . ' ' . $FORM{'_prontus_id'} . '
    <br><br>

 <input type="radio" name="accion" value="2">' . &lib_language::_msg_prontus('_create_test_table') . '
    <br><br>


 <input type="radio" name="accion" value="3">' . &lib_language::_msg_prontus('_write_table') . '
    <br><br>


 <input type="radio" name="accion" value="4">' . &lib_language::_msg_prontus('_write_table_lock') . '
    <br><br>


 <input type="radio" name="accion" value="5">' . &lib_language::_msg_prontus('_write_10_reg') . '
 <br><br>


 <input type="radio" name="accion" value="6">' . &lib_language::_msg_prontus('_read_table') . '
<br><br>



<input name="ejec" type="submit" value="Ejecutar">

</FORM>
</BODY>
</HTML>';


  };



}; # main.

# ---------------------------------------------------------------
# SUB-RUTINAS.
# --------------------------------------------------------------
sub check_write {
# Chequear escritura de archivos.
#
# - Emular la escritura de un archivo con: html, xml, adjuntos, fotos y mm (todo)
# - Emular art relac
# - Emular tax
# - Emular escritura de portada
# - Escribir en carpeta temp de la cgi
# - Escribir en cpan/data
#
# Crear carpetas si esto no existe.




  # Site de articulos
  my $dirfecha = &glib_hrfec_02::get_date_pack4();
  my $ts = &glib_hrfec_02::get_dtime_pack4();
  my $reldir_pags = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dirfecha/pags";
  my $reldir_img = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dirfecha/imag";
  my $reldir_mmedia = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EXMEDIA/$dirfecha/mmedia";
  my $reldir_asocfile = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dirfecha/asocfile/$ts";
  my $reldir_swf = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dirfecha/swf";
  my $reldir_xml = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dirfecha/xml";

  &write_file_test($reldir_pags);
  &write_file_test($reldir_img);
  &write_file_test($reldir_mmedia);
  &write_file_test($reldir_asocfile);
  &write_file_test($reldir_swf);
  &write_file_test($reldir_xml);

  # art. relac
  &write_file_test("$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_TAXONOMIA");

  # cpan/data y derivados
  &write_file_test($prontus_varglb::DIR_DBM);
  &write_file_test("$prontus_varglb::DIR_CPAN/log");
  &write_file_test("$prontus_varglb::DIR_DBM/search");
  &write_file_test("$prontus_varglb::DIR_DBM/user_lock");
  &write_file_test("$prontus_varglb::DIR_DBM/users");
  &write_file_test("$prontus_varglb::DIR_CPAN/procs");

  # site ediciones
  &write_file_test("$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EDIC");
  &write_file_test("$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EDIC/base");
  &write_file_test("$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EDIC/base/port");
  &write_file_test("$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EDIC/base/rss");
  &write_file_test("$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EDIC/base/xml");

  # port. tipo tema
  &write_file_test("$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_PTEMA");

  # temp
  my $pesoscero = $0;
  # win
  if ($pesoscero =~ /^\w:/) {
    $pesoscero =~ s/(\w+\.cgi)$/prontus_temp/;
  }
  # linux
  else {
    $pesoscero =~ s/(\w+\.cgi)$/prontus_temp/;
  };
  $pesoscero =~ s/\\/\//;
  $pesoscero =~ s/$prontus_varglb::DIR_SERVER//;
  &write_file_test($pesoscero);

  # Si la invocacion vino del wizard es porque el dir prontus no existia
  # y lo tuve q crear para el test asi q ahora lo borro.
  if (($FORM{'wizard'}) && ($PRONTUS_DIR_CREADO_POR_CGI)) {
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER/$FORM{'_prontus_id'}");
    if (-d "$prontus_varglb::DIR_SERVER/$FORM{'_prontus_id'}") {
      &salir(&lib_language::_msg_prontus('_error_directory_erase') . "{'_prontus_id'}");
    }
    else {
      print "<br>[$FORM{'_prontus_id'}] " . &lib_language::_msg_prontus('_erasing_ok');
    };
  };

  print "<br>";
};

# ---------------------------------------------------------------
sub write_file_test {
  my $reldir = $_[0];

  if ( ! (&glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$reldir")) ) {
    print &lib_language::_msg_prontus('_directory_not_exists') . " : [$reldir]";
    return;
  };

  my $file_test = "$prontus_varglb::DIR_SERVER$reldir/prueba.txt";
  &glib_fildir_02::write_file($file_test, 'test');
  print "\n<br>[$reldir/prueba.txt] ... ";
  if ( (-f $file_test) && (-s $file_test) )  {
    print &lib_language::_msg_prontus('_msg_generic_ok');
    print " - " . &lib_language::_msg_prontus('_deleting');
    if (unlink $file_test) {
      print &lib_language::_msg_prontus('_msg_generic_ok');
    }
    else {
      print &lib_language::_msg_prontus('_msg_generic_fail');
    };
  }
  else {
    print &lib_language::_msg_prontus('_msg_generic_fail');
  };

};

# ---------------------------------------------------------------
sub query_table {

  my $base;

  # Conectando con BD
  if ($prontus_varglb::MOTOR_BD eq 'MYSQL') {
    print &lib_language::_msg_prontus('_connect_mysql_db_name') . ": $prontus_varglb::NOM_BD / " . &lib_language::_msg_prontus('_server') . ": $prontus_varglb::SERVER_BD / " . &lib_language::_msg_prontus('_user') . ": $prontus_varglb::USER_BD / " . &lib_language::_msg_prontus('_password') . ": $prontus_varglb::PWD_BD<br>";
    $base = DBI->connect("DBI:mysql:$prontus_varglb::NOM_BD:$prontus_varglb::SERVER_BD", $prontus_varglb::USER_BD, $prontus_varglb::PWD_BD) || &salir("Error: la base de datos MySQL '$prontus_varglb::NOM_BD' no existe o no fue posible conectarse a ella con los parámetros indicados en el cfg.<br>(" . DBI->errstr . ")");
  };

  if ($prontus_varglb::MOTOR_BD eq 'PRONTUS') {
    my $file_db = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/prontus_db.db";
    print &lib_language::_msg_prontus('_connect_db_route') . " <b>$file_db</b> <br>";
    $base = DBI->connect("dbi:SQLite2:dbname=$file_db","","") || &salir("Error, problema de I/O accediendo BD Prontus<br>(" . DBI->errstr . ")");
  };

  my $sql = "SELECT PRUEBA_ID, PRUEBA_TITULAR from PRUEBA";
  my ($id, $nom);
  my $salida = &local_sql_bind($base, $sql, \($id, $nom)) || &salir("Error al realizar query:<br>SQL [$sql]<br>(" . DBI->errstr . ")");
  while ($salida->fetch) {
    print "&nbsp;&nbsp; PRUEBA_ID[$id] - PRUEBA_TITULAR[$nom] <br>";
  };
  $salida->finish;
  $base->disconnect;

};
#-------------------------------------------------------------------------#
sub local_sql_bind { # 01.2
  # ejecuta una sentencia sql y devuelve su handler.
  # Param entrada:
  #  0) descriptor de la base de datos abierta.
  #  1) sentencia SQL propiamente tal.
  #  2) nombres de las variables asociadas a los campos.
  #  retorno:
  #  0) descriptor de la respuesta. (Usar solamente fetch para cargar las variables con las filas siguientes.

  my ($dbh) = shift;
  my ($sql) = shift;
  my (@var) = (@_);
  my ($sth);

  $sth = $dbh->prepare($sql) || return 0;

  $sth->execute || return 0;
  $sth->bind_columns(undef, (@var)) || return 0;

  return($sth);
};


# ---------------------------------------------------------------
sub escribir_diez_reg {

  my $base;

  # Conectando con BD
  if ($prontus_varglb::MOTOR_BD eq 'MYSQL') {
    print &lib_language::_msg_prontus('_connect_mysql_db_name') . ": $prontus_varglb::NOM_BD / " . &lib_language::_msg_prontus('_server') . ": $prontus_varglb::SERVER_BD / " . &lib_language::_msg_prontus('_user') . ": $prontus_varglb::USER_BD / " . &lib_language::_msg_prontus('_password') . ": $prontus_varglb::PWD_BD<br>";
    $base = DBI->connect("DBI:mysql:$prontus_varglb::NOM_BD:$prontus_varglb::SERVER_BD", $prontus_varglb::USER_BD, $prontus_varglb::PWD_BD) || &salir("Error: la base de datos MySQL '$prontus_varglb::NOM_BD' no existe o no fue posible conectarse a ella con los parámetros indicados en el cfg.<br>(" . DBI->errstr . ")");
  };

  if ($prontus_varglb::MOTOR_BD eq 'PRONTUS') {
    my $file_db = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/prontus_db.db";
    print &lib_language::_msg_prontus('_connect_db_route') . " <b>$file_db</b> <br>";
    $base = DBI->connect("dbi:SQLite2:dbname=$file_db","","") || &salir("Error, problema de I/O accediendo BD Prontus<br>(" . DBI->errstr . ")");
  };

  my $i;
  for ($i = 1; $i <= 10; $i++) {
    my $sql = "insert into PRUEBA values(NULL, \"TEXTO DEL REGISTRO\")";
    $base->do($sql) || &salir("Error escribiendo registro nro. $i<br>(" . $base->errstr . ")");
    print &lib_language::_msg_prontus('_register_nro') . " $i " . &lib_language::_msg_prontus('_written_ok');
  };
  $base->disconnect;
  print &lib_language::_msg_prontus('_10_reg_inserted_ok');
};
# ---------------------------------------------------------------
sub escribir_reg {
# Prueba de escribir un registro en la tabla PRUEBA.
  my $base;

  # Conectando con BD
  if ($prontus_varglb::MOTOR_BD eq 'MYSQL') {
    print &lib_language::_msg_prontus('_connect_mysql_db_name') . ": $prontus_varglb::NOM_BD / " . &lib_language::_msg_prontus('_server') . ": $prontus_varglb::SERVER_BD / " . &lib_language::_msg_prontus('_user') . ": $prontus_varglb::USER_BD / " . &lib_language::_msg_prontus('_password') . ": $prontus_varglb::PWD_BD<br>";
    $base = DBI->connect("DBI:mysql:$prontus_varglb::NOM_BD:$prontus_varglb::SERVER_BD", $prontus_varglb::USER_BD, $prontus_varglb::PWD_BD) || &salir("Error: la base de datos MySQL '$prontus_varglb::NOM_BD' no existe o no fue posible conectarse a ella con los parámetros indicados en el cfg.<br>(" . DBI->errstr . ")");
  };

  if ($prontus_varglb::MOTOR_BD eq 'PRONTUS') {
    my $file_db = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/prontus_db.db";
    print &lib_language::_msg_prontus('_connect_db_route') . " <b>$file_db</b> <br>";
    $base = DBI->connect("dbi:SQLite2:dbname=$file_db","","") || &salir("Error, problema de I/O accediendo BD Prontus<br>(" . DBI->errstr . ")");
  };

  my $sql;
  # Inserta registro en la tabla.
  print &lib_language::_msg_prontus('_writting_reg_in_table');
  $sql = "insert into PRUEBA values(NULL, \"TEXTO DEL REGISTRO\")";
  $base->do($sql) || &salir("Error escribiendo registro<br>(" . $base->errstr . ")");
  $base->disconnect;
  print &lib_language::_msg_prontus('_register_ok');

};
# ---------------------------------------------------------------
sub crear_tabla {
#Crear tabla de pruebas en la BD.
#Tabla: PRUEBA. Columnas: PRUEBA_ID y PRUEBA_TITULAR.
#Si no existe, se crea.
#Si ya existe, se borra la que estaba antes.
#Con SQLite si es SQLite (en cpan/data).
#Con MySQL si es MySQL, tomando los datos del cfg.

  my $base;

  # Conectando con BD
  if ($prontus_varglb::MOTOR_BD eq 'MYSQL') {
    print &lib_language::_msg_prontus('_connect_mysql_db_name') . ": $prontus_varglb::NOM_BD / " . &lib_language::_msg_prontus('_server') . ": $prontus_varglb::SERVER_BD / " . &lib_language::_msg_prontus('_user') . ": $prontus_varglb::USER_BD / " . &lib_language::_msg_prontus('_password') . ": $prontus_varglb::PWD_BD<br>";
    $base = DBI->connect("DBI:mysql:$prontus_varglb::NOM_BD:$prontus_varglb::SERVER_BD", $prontus_varglb::USER_BD, $prontus_varglb::PWD_BD) || &salir("Error: la base de datos MySQL '$prontus_varglb::NOM_BD' no existe o no fue posible conectarse a ella con los parámetros indicados en el cfg.<br>(" . DBI->errstr . ")");
  };

  if ($prontus_varglb::MOTOR_BD eq 'PRONTUS') {
    my $file_db = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/prontus_db.db";
    print &lib_language::_msg_prontus('_connect_db_route') . " <b>$file_db</b> <br>";
    $base = DBI->connect("dbi:SQLite2:dbname=$file_db","","") || &salir("Error, problema de I/O accediendo BD Prontus<br>(" . DBI->errstr . ")");
  };

  # Chequeando existencia
  my $sql;
  print &lib_language::_msg_prontus('_check_table_exists');
  if (&lib_setbd::existe_tabla($base, 'PRUEBA', $prontus_varglb::MOTOR_BD)) {
    print &lib_language::_msg_prontus('_erasing_test_table');
    # SECC
    $sql = 'drop table PRUEBA';
    $base->do($sql) || &salir("Error eliminando tabla 'PRUEBA': [" . $base->errstr . "]");
    print &lib_language::_msg_prontus('_erase_ok');
  };

  # Crear tabla
  print &lib_language::_msg_prontus('_creating_test_table');
  if ($prontus_varglb::MOTOR_BD eq 'MYSQL') {
    $sql = "
        CREATE TABLE PRUEBA (
          PRUEBA_ID int(5) NOT NULL auto_increment,
          PRUEBA_TITULAR varchar(128) NOT NULL default '',
          PRIMARY KEY  (PRUEBA_ID),
          KEY PRUEBA_TITULAR (PRUEBA_TITULAR)
        )
    ";
  };

  if ($prontus_varglb::MOTOR_BD eq 'PRONTUS') {
    $sql = "
        CREATE TABLE PRUEBA (
          PRUEBA_ID integer primary key,
          PRUEBA_TITULAR varchar(128) NOT NULL default ''
        );
    ";
  };
  $base->do($sql) || &salir("Error creando tabla 'PRUEBA': [" . $base->errstr . "]");
  print &lib_language::_msg_prontus('_test_table_created_ok');

  $base->disconnect;
};
# ---------------------------------------------------------------
sub test_lock {

    my $lock_file = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/prueba.lock";
    print &lib_language::_msg_prontus('_blocking') . " [$lock_file]<br>";
    &lib_waitlock::lock_file($lock_file);
    print &lib_language::_msg_prontus('_block_ok');

    &escribir_reg();

    print &lib_language::_msg_prontus('_unblocking') . " [$lock_file]<br>";
    &lib_waitlock::unlock_file($lock_file);
    print &lib_language::_msg_prontus('_unblock_ok');


};
# ---------------------------------------------------------------
sub get_path_conf {
  
  if (&lib_prontus::valida_prontus($FORM{'_prontus_id'})) {
    return "$prontus_varglb::DIR_SERVER/$FORM{'_prontus_id'}/cpan/$FORM{'_prontus_id'}.cfg";
  };
  return '';
};

# ---------------------------------------------------------------
sub valida_param {
  $FORM{'_prontus_id'} =~ s/\\/\//g;
  $FORM{'_prontus_id'} =~ s/\/$//g;
  if ( ($FORM{'_prontus_id'} eq '') || ($FORM{'_prontus_id'} eq '/') )  {
    &salir(&lib_language::_msg_prontus('_error_prontus_directory_not_valid'));
  };

  if ($FORM{'wizard'}) {
    # En este caso no debe existir la carpeta del prontus asi q se intenta crear.
    if (! -d "$prontus_varglb::DIR_SERVER/$FORM{'_prontus_id'}") {
      if ( ! (&glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER/$FORM{'_prontus_id'}")) ) {
        &salir(&lib_language::_msg_prontus('_error_prontus_directory_not_exists'));
      }
      else {
        print &lib_language::_msg_prontus('_creating_directory') . " $FORM{'_prontus_id'} " . &lib_language::_msg_prontus('_created_ok');
        $PRONTUS_DIR_CREADO_POR_CGI = 1;
      };
    }
    else {
      &salir(&lib_language::_msg_prontus('_error_directory') . " $FORM{'_prontus_id'} " . &lib_language::_msg_prontus('_already_exists'));
    };
    # Cargar variables para emular carga de arch. de config
    $prontus_varglb::DIR_CONTENIDO = "/$FORM{'_prontus_id'}/site";
    $prontus_varglb::DIR_DBM = "/$FORM{'_prontus_id'}/cpan/data";
    $prontus_varglb::DIR_CPAN = "/$FORM{'_prontus_id'}/cpan";
  }
  else {
    if (! -d "$prontus_varglb::DIR_SERVER/$FORM{'_prontus_id'}") {
      &salir(&lib_language::_msg_prontus('_error_directory') . " $FORM{'_prontus_id'} " . &lib_language::_msg_prontus('_not_exist'));
    };
    # Carga variables de configuracion.
    my $path_conf = &get_path_conf();
    &lib_prontus::load_config($path_conf);

  };

};
# ---------------------------------------------------------------
sub salir {
  my $msg = $_[0];
  print "<span style=\"color:#990000\">$msg</span>";
  exit;
};
# ----------------------------END SCRIPT---------------------
