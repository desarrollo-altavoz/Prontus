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
# Importar secciones, temas y subtemas a Prontus, desde un arch. de texto.

# El formato del archivo es el sgte:

# Archivo txt con seis columnas separadas por tabuladores:
# Columna 0: Id de sección.
# Columna 1: Nombre de sección.
# Columna 2: Id de tema.
# Columna 3: Nombre de tema.
# Columna 4: Id de subtema.
# Columna 5: Nombre de subtema.
# Columna 6: Mostrar
# Si el valor es 0 o /no/i, entonces no hay que mostrarla.
# Si es vacío o distinto que 0 o /no/i, entonces SI hay que mostrarla.
# Al exportar, se exporta con 'no' o 'si'.

# Si se especifica id, el sistema lo utilizará. Si no, el sistema lo asignará automáticamente.

# Si el id ya existe, se sobreescribirá el nombre.

# En cada línea va un solo dato. No se mezclan secciones, temas y subtemas.


# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# No registra.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Via system desde prontus_tax_import.cgi
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# No utiliza.
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
# ART (BD prontus)
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 09/2004 - YCH - Primera version.
# ---------------------------------------------------------------


# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    unshift(@INC,$Bin); # Para dejar disponibles las librerias
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use DBI;

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use lib_secc;
use glib_dbi_02;
use glib_fildir_02;
use lib_lock;
use glib_cgi_04;
use glib_hrfec_02;

use lib_logproc;

use strict;



my ($LOG_FILE, $PATH_CONF);

# sqlite no requiere esto.
my $NOM_BD_PRONTUS = '';
my $USER_BD = '';
my $PWD_BD = '';
my $SERVER_BD = ''; # asumiendo que los scripts estan instalados en el server Mysql


# ---------------------------------------------------------------
# MAIN.
# -------------

my ($BD, $LOCK_FILE);

my ($TOT_REGS, $OK_REGS) = '0';
my (%ID_MAYOR, %DATA_VISTAS);
my (%NOMBRES);
my (%FORM);
my ($MODO_WEB) = 0;
main:{

    if ($ARGV[0] && $ARGV[1]) {
        close STDOUT;
        $prontus_varglb::DIR_SERVER = $ARGV[0];
        $PATH_CONF = $ARGV[1];
        print STDERR "DIR_SERVER: [$prontus_varglb::DIR_SERVER]\n";
        print STDERR "PATH_CONF: [$PATH_CONF]\n";
    } else {
        &glib_cgi_04::new(); # Rescata parametros
        $FORM{'path_conf'} = &glib_cgi_04::param('path_conf');

        # Ajusta path_conf para completar path y/o cambiar \ por /
        $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});
        $PATH_CONF = $FORM{'path_conf'};
        $MODO_WEB = 1;
        print "Content-Type: text/html\n\n";
        $| = 1;
    };


    if (! -d $prontus_varglb::DIR_SERVER) {
        print STDERR "ERROR: DIR_SERVER no válido[$prontus_varglb::DIR_SERVER]\n";
        exit;
    };


    &lib_prontus::load_config($PATH_CONF);
    $lib_logproc::LOG_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/prontus_tax_import_log.html";
    $lib_logproc::MODO_WEB = $MODO_WEB;

    # Bloqueo
    $LOCK_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/semaforo_tax_import";
    # Detecta semaforo.
    my ($lock_obj) = &lib_lock::lock_file($LOCK_FILE);
    if (!ref $lock_obj) { # si ya tiene un bloqueo anterior, aborta.
        &finishLoading("Proceso en ejecución.\nPor favor espere hasta que la importación anterior termine.");
        &lib_logproc::handle_error("Proceso en ejecución.\nPor favor espere hasta que la importación anterior termine.");
    };

    # Mysql
    my ($msg_err_bd);
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &finishLoading("ERROR: $msg_err_bd");
        &lib_logproc::handle_error("ERROR: $msg_err_bd");
    };




    &lib_logproc::flush_log();
    &lib_logproc::writeRule();
    &lib_logproc::add_to_log_count("INICIANDO PROCESO DE IMPORTACION");

    my ($data_file) = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/tax_import.xml";
    my $archivo = &glib_fildir_02::read_file($data_file);
    my ($err) = &lib_prontus::valid_xml_import($archivo);
    if ($err) {
        &finishLoading("El archivo ingresado no es un XML bien formado, no es posible cargarlo");
        &lib_logproc::handle_error("El archivo ingresado no es un XML bien formado, no es posible cargarlo");
    };
    
    &lib_logproc::add_to_log_count("Borrando datos actuales de la base de datos.\n");
    my ($sql) = "delete from SECC";
    $BD->do($sql) || (&finishLoading("No fue posible borrar Secciones actuales") && &lib_logproc::handle_error("No fue posible borrar Secciones actuales") );

    my ($sql) = "delete from TEMAS";
    $BD->do($sql) || (&finishLoading("No fue posible borrar Temas actuales") && &lib_logproc::handle_error("No fue posible borrar Temas actuales"));

    my ($sql) = "delete from SUBTEMAS";
    $BD->do($sql) || (&finishLoading("No fue posible borrar SubTemas actuales") && &lib_logproc::handle_error("No fue posible borrar SubTemas actuales"));

    &tax_import($archivo);

    &lib_logproc::add_to_log_count("PROCESO DE IMPORTACION FINALIZADO");
    &lib_logproc::writeRule();

    $TOT_REGS = '0' if ($TOT_REGS eq '');
    $OK_REGS = '0' if ($OK_REGS eq '');

    &lib_logproc::add_to_log("Nro. de registros procesados: $TOT_REGS\nRegistros ingresados OK: $OK_REGS");
    &lib_logproc::add_to_log_finish("Operaci&oacute;n finalizada.");

    # REGENERA EL MAPA
    &lib_prontus::make_mapa('', $BD); # rotulos tax

    my $mv;
    foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
        &lib_prontus::make_mapa($mv, $BD);
    };

    # Genera tax en arch. JS, para ser incluido en FIDs
    my $arr_tst = &lib_secc::genera_array_temas_subtemas($BD, '', 'solo habilitadas');
    my $dir_tax4fids = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CPAN . '/procs/tax4fids';
    &glib_fildir_02::check_dir($dir_tax4fids);
    &glib_fildir_02::write_file($dir_tax4fids . '/tax4fids.js', $arr_tst);

    $BD->disconnect;

    &finishLoading('');

    # Elimina el bloqueo y termina ejecucion.
    &lib_lock::unlock_file($lock_obj, $LOCK_FILE);


}; # main

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub importa_tax_level {
    my ($tipo, $id_level, $id_superlevel, $xml_segment) = @_;

    $TOT_REGS++;

    # Si viene id deben ser solo digitos.
    if ($id_level !~ /^[0-9]*$/) {
        $xml_segment=~s/>/&gt;/g;              # >
        $xml_segment=~s/</&lt;/g;              # <
        &saltar_reg("Id no válido en registro [$TOT_REGS] $tipo id=$id_level" . $xml_segment);
        &saltar_reg($xml_segment);
        return 0;
    };

    if (($id_superlevel !~ /^[0-9]+$/) && ($tipo ne 'seccion')) {
        $xml_segment=~s/>/&gt;/g;              # >
        $xml_segment=~s/</&lt;/g;              # <
        &saltar_reg("Id no válido en registro [$TOT_REGS] $tipo id=$id_level" . $xml_segment);
        return 0;
    };

    my ($nom, %nom_vistas, $mostrar, $port, $posmapa, $nom4vistas);

    # nom
    if ($xml_segment =~ /<nom>(.*?)<\/nom>/is) {
        $nom = &lib_prontus::despulga_item_tax($1);
        $nom = &lib_prontus::unescape_xml($nom);

    };
    if ($nom !~ /\w+/) {
        $xml_segment=~s/>/&gt;/g;              # >
        $xml_segment=~s/</&lt;/g;              # <
        &saltar_reg("Nombre no válido en registro [$TOT_REGS] $tipo id=$id_level" . $xml_segment);
        return 0;
    };
    if (exists $NOMBRES{"$tipo\t$id_level\t$nom"}) {
        $xml_segment=~s/>/&gt;/g;              # >
        $xml_segment=~s/</&lt;/g;              # <
        &saltar_reg("Nombre repetido en registro [$TOT_REGS] $tipo id=$id_level" . $xml_segment);
        return 0;
    } else {
        $NOMBRES{"$tipo\t$id_level\t$nom"} = 1;
    };

    # mostrar
    if ($xml_segment =~ /<mostrar>(.*?)<\/mostrar>/is) {
        $mostrar = &lib_prontus::despulga_item_tax($1);
    };

    if ((!$mostrar) || ($mostrar =~ /no/i)) { $mostrar = ''; }
    else { $mostrar = '1'; };

    if ($xml_segment =~ /<posmapa>(.*?)<\/posmapa>/is) {
        $posmapa = &lib_prontus::despulga_item_tax($1);
    };
    # Si viene, debe ser number.
    if (($posmapa) && ($posmapa !~ /^[0-9]*$/) ) {
        $xml_segment=~s/>/&gt;/g;              # >
        $xml_segment=~s/</&lt;/g;              # <
        &saltar_reg($xml_segment);
        &saltar_reg("Pos. en mapa no válida en registro [$TOT_REGS] $tipo id=$id_level" . $xml_segment);
        return 0;
    };

    # port
    if ($xml_segment =~ /<port>(.*?)<\/port>/is) {
        $port = &lib_prontus::despulga_item_tax($1);
        $port = &lib_prontus::unescape_xml($port);
    # CVI - 16/03/2011 - corrige bug al importar taxonomia sin paginas asociadas
    } else {
        $port = '';
    };

    # nombres de taxlevel en otras vistas
    my $nom4vistas;
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        my $nom_envista;
        if ($xml_segment =~ /<nom-$mv>(.*?)<\/nom-$mv>/is) {
            $nom_envista = $1;
            $nom_envista = &lib_prontus::despulga_item_tax($nom_envista);
            $nom_envista = &lib_prontus::unescape_xml($nom_envista);
        };
        $nom_envista = $nom if (!$nom_envista);
        $nom4vistas .= "$mv\t$nom_envista\n";
    };
    $nom4vistas =~ s/\n$//; # elimina \n sobrante

    # inserta
    my $ret;
    $ret = &insert_secc($id_level, $nom, $mostrar, $port, $posmapa, $nom4vistas) if ($tipo eq 'seccion');
    $ret = &insert_tema($id_level, $nom, $id_superlevel, $mostrar, $port, $posmapa, $nom4vistas) if ($tipo eq 'tema');
    $ret = &insert_subtema($id_level, $nom, $id_superlevel, $mostrar, $port, $posmapa, $nom4vistas) if ($tipo eq 'subtema');
    if ($ret) {
        $OK_REGS++;  # Total de reg. insertados normalmente
    } else {
        $xml_segment=~s/>/&gt;/g;              # >
        $xml_segment=~s/</&lt;/g;              # <
        &lib_logproc::add_to_log_count("INSERT error en registro [$TOT_REGS] $tipo id=$id_level ($DBI::errstr) $xml_segment");
        return 0;
    };


    return 1;


};
# ---------------------------------------------------------------
sub get_id_mayor {
  my ($buffer_xml) = $_[0];
  my ($tipo) = $_[1]; # seccion \ tema \ subtema
  my $id_mayor = 0;
  # Obtiene el mayor id q venga de seccion o de tema o de subtema
  while ($buffer_xml =~ /<$tipo +id *= *["']([0-9]+)["']>.+?<\/$tipo>/isg) {
    my $id = $1;
    next if ($id !~ /^[0-9]+$/);
    $id_mayor = $id if ($id > $id_mayor);
  };
  return $id_mayor;
};

# ---------------------------------------------------------------
sub tax_import {
# Columna 0: Id de sección.
# Columna 1: Nombre de sección.
# Columna 2: Id de tema.
# Columna 3: Nombre de tema.
# Columna 4: Id de subtema.
# Columna 5: Nombre de subtema.
# Columna 6: Mostrar
# Columna 7: Portada
# Columna 8: Orden
# Si el valor es 0 o /no/i, entonces no hay que mostrarla.
# Si es vacío o distinto que 0 o /no/i, entonces SI hay que mostrarla.
# Al exportar, se exporta con 'no' o 'si'.


my ($buffer_xml) = $_[0];
my ($sql, $ret, $linea);


  &lib_logproc::add_to_log_count("Procesando archivo de datos.");

  $buffer_xml =~ s/(\r\n)/\n/g;
  $buffer_xml =~ s/\r//g;

  my (@data, $i, %secciones,%temas,%subtemas, @filas);
  my ($id_s, $id_t, $id_st);
  my ($id_s_curr, $id_t_curr, $id_st_curr);
  my ($nom_s, $nom_t, $nom_st, $mostrar, $port, $orden);

  # obtiene los id mayores de cada tax level para poder asignar id a los reg. nuevos
  $ID_MAYOR{'seccion'} = &get_id_mayor($buffer_xml, 'seccion');
  $ID_MAYOR{'tema'} = &get_id_mayor($buffer_xml, 'tema');
  $ID_MAYOR{'subtema'} = &get_id_mayor($buffer_xml, 'subtema');


  $TOT_REGS = 0;

  while ($buffer_xml =~ /<seccion +id *= *["']([0-9]*)["']>(.+?)<\/seccion>/isg) {
    $id_s = $1;
    my $seccion = $2;
    my $temas;
    if ($seccion =~ s/(<tema +id *= *["'][0-9]*["']>.+<\/tema>)//s) {
      $temas = $1;
    };
    # si no viene id asigno uno nuevo
    if (!$id_s) {
      $ID_MAYOR{'seccion'}++;
      $id_s = $ID_MAYOR{'seccion'};
    };

    next if (! &importa_tax_level('seccion', $id_s, '', $seccion));
    while ($temas =~ /<tema +id *= *["']([0-9]*)["']>(.+?)<\/tema>/isg) {
      $id_t = $1;
      my $tema = $2;
      my $subtemas;
      # si no viene id asigno uno nuevo
      if (!$id_t) {
        $ID_MAYOR{'tema'}++;
        $id_t = $ID_MAYOR{'tema'};
      };

      if ($tema =~ s/(<subtema +id *= *["'][0-9]*["']>.+<\/subtema>)//s) {
        $subtemas = $1;
      };
      next if (! &importa_tax_level('tema', $id_t, $id_s, $tema));
      while ($subtemas =~ /<subtema +id *= *["']([0-9]*)["']>(.+?)<\/subtema>/isg) {
        $id_st = $1;
        my $subtema = $2;
        # si no viene id asigno uno nuevo
        if (!$id_st) {
          $ID_MAYOR{'subtema'}++;
          $id_st = $ID_MAYOR{'subtema'};
        };

        next if (! &importa_tax_level('subtema', $id_st, $id_t, $subtema));
      };
    };
  };

  # Actualiza xmls de nombres de taxlevels en otras vistas
  &actualiza_xml_vista();

};
# ---------------------------------------------------------------
sub actualiza_xml_vista {

  my $xml_buf = "<?xml version='1.0' encoding='iso-8859-1'?>\n<ROTULOS>\n%%ITEMS%%</ROTULOS>";
  my %items_seccion;
  my %items_tema;
  my %items_subtema;
  my $id_s;
  my $mv;
  my $sql = "select SECC_ID from SECC ";
  my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id_s));
  while($salida->fetch){
    foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
      my $nom = &lib_prontus::unescape_xml($DATA_VISTAS{"$mv\tseccion\t$id_s"});
      $items_seccion{$mv} .= "<ITEM>\n<ID>$id_s</ID>\n<NOM>$nom</NOM>\n</ITEM>\n";
    };
  	# temas
    $sql = "select TEMAS_ID from TEMAS WHERE TEMAS_IDSECC = $id_s ";
    my $id_t;
    my $salida_t = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id_t));
  	while ($salida_t->fetch) {
      foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
        my $nom = &lib_prontus::unescape_xml($DATA_VISTAS{"$mv\ttema\t$id_t"});
        $items_tema{$mv} .= "<ITEM>\n<ID>$id_t</ID>\n<NOM>$nom</NOM>\n</ITEM>\n";
      };
    	# subtemas
      $sql = "select SUBTEMAS_ID from SUBTEMAS WHERE SUBTEMAS_IDTEMAS = $id_t ";
      my $id_st;
      my $salida_st = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id_st));
    	while ($salida_st->fetch) {
        foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
          my $nom = &lib_prontus::unescape_xml($DATA_VISTAS{"$mv\tsubtema\t$id_st"});
          $items_subtema{$mv} .= "<ITEM>\n<ID>$id_st</ID>\n<NOM>$nom</NOM>\n</ITEM>\n";
        };
      };
      foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
        my $xml_out = $xml_buf;
        my $items = $items_subtema{$mv};
        $xml_out =~ s/%%ITEMS%%/$items/;
        my $dir_xml_vista = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/tax_multivista/$mv";
        &glib_fildir_02::check_dir($dir_xml_vista);
        &glib_fildir_02::write_file($dir_xml_vista . "/subtema-$id_t.xml", $xml_out);
      };
      $salida_st->finish;
    };
    foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
      my $xml_out = $xml_buf;
      my $items = $items_tema{$mv};
      $xml_out =~ s/%%ITEMS%%/$items/;
      my $dir_xml_vista = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/tax_multivista/$mv";
      &glib_fildir_02::check_dir($dir_xml_vista);
      &glib_fildir_02::write_file($dir_xml_vista . "/tema-$id_s.xml", $xml_out);
    };
    $salida_t->finish;
  };
  foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
    my $xml_out = $xml_buf;
    my $items = $items_seccion{$mv};
    $xml_out =~ s/%%ITEMS%%/$items/;
    my $dir_xml_vista = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/tax_multivista/$mv";
    &glib_fildir_02::check_dir($dir_xml_vista);
    &glib_fildir_02::write_file($dir_xml_vista . "/seccion.xml", $xml_out);
  };
  $salida->finish;


};
# ---------------------------------------------------------------
sub insert_secc {
    my ($id, $nom, $mostrar, $port, $orden, $nom4vistas) = @_;
    my ($sql, $ret);

    $nom = $BD->quote($nom);
    $port = $BD->quote($port);

    if ($nom4vistas ne '') {
        $nom4vistas = $BD->quote($nom4vistas);
    } else {
        $nom4vistas = "''";
    };


    # Setear autoinc a ser usado en el insert
    $sql = "SET INSERT_ID = $id";
    $ret = $BD->do($sql);
    if (! $ret) {
        &add_to_log("$sql\n");
        return $ret;
    };

    # CVI - 16/03/2011 - corrige bug al importar taxonomia sin paginas asociadas
    # $sql = "insert SECC set SECC_NOM = $nom, SECC_MOSTRAR = \"$mostrar\", SECC_PORT = $port, SECC_ORDEN = \"$orden\", SECC_NOM4VISTAS = $nom4vistas  ";
    $sql = "insert into SECC values(NULL, $nom, \"$mostrar\", $port, \"$orden\", $nom4vistas)";

    $ret = $BD->do($sql);

    return $ret;
};
# ---------------------------------------------------------------
sub insert_tema {
    my ($id, $nom, $id_s, $mostrar, $port, $orden, $nom4vistas) = @_;
    my ($sql, $ret);

    $nom = $BD->quote($nom);
    $port = $BD->quote($port);

    if ($nom4vistas ne '') {
        $nom4vistas = $BD->quote($nom4vistas);
    } else {
        $nom4vistas = "''";
    };


    # Setear autoinc a ser usado en el insert
    $sql = "SET INSERT_ID = $id";
    $ret = $BD->do($sql);
    return $ret if (! $ret);

    # CVI - 16/03/2011 - corrige bug al importar taxonomia sin paginas asociadas
    # $sql = "insert TEMAS set TEMAS_NOM = $nom, TEMAS_IDSECC = $id_s, TEMAS_MOSTRAR = \"$mostrar\", TEMAS_PORT = $port, TEMAS_ORDEN = \"$orden\", TEMAS_NOM4VISTAS = $nom4vistas ";
    $sql = "insert into TEMAS values(NULL, $nom, $id_s, \"$mostrar\", $port, \"$orden\", $nom4vistas)";

    # print STDERR "sql[$sql]\n";
    $ret = $BD->do($sql);
    return $ret;
};
# ---------------------------------------------------------------
sub insert_subtema {
    my ($id, $nom, $id_t, $mostrar, $port, $orden, $nom4vistas) = @_;
    my ($sql, $ret);

    $nom = $BD->quote($nom);
    $port = $BD->quote($port);

    if ($nom4vistas ne '') {
        $nom4vistas = $BD->quote($nom4vistas);
    } else {
        $nom4vistas = "''";
    };


    # Setear autoinc a ser usado en el insert
    $sql = "SET INSERT_ID = $id";
    $ret = $BD->do($sql);
    return $ret if (! $ret);

    # CVI - 16/03/2011 - corrige bug al importar taxonomia sin paginas asociadas
    # $sql = "insert SUBTEMAS set SUBTEMAS_NOM = $nom, SUBTEMAS_IDTEMAS = $id_t, SUBTEMAS_MOSTRAR = \"$mostrar\", SUBTEMAS_PORT = $port, SUBTEMAS_ORDEN = \"$orden\", SUBTEMAS_NOM4VISTAS = $nom4vistas ";
    $sql = "insert into SUBTEMAS values(null, $nom, $id_t, \"$mostrar\", $port, \"$orden\", $nom4vistas)";

    $ret = $BD->do($sql);
    return $ret;
};

# ---------------------------------------------------------------
sub saltar_reg {
  my ($registro) = $_[0];
  &lib_logproc::add_to_log_count("Registro con errores, se omite.\n$registro");
  # $CORRUPTOS++;
};

# ---------------------------------------------------------------
sub parse_comillas {
  my ($str) = $_[0];
  if ($str eq '""') {
    return '';
  } else {
    $str =~ s/""/'/sg;
    $str =~ s/^"//s;
    $str =~ s/"$//s;
    return $str;
  };
};

# ---------------------------------------------------------------
sub finishLoading {
    my $msg = $_[0];
    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_tax_import.js";
    my $msg = '{"status":1, "msg":"'.$msg.'"}';
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", $msg);
};

# -------------------------END SCRIPT----------------------
