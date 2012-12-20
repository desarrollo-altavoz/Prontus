#!/usr/bin/perl


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
# Via system desde prontus_tags_import.cgi
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
use lib_tags;
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
my ($ID_MAYOR, %DATA_VISTAS);
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
    $lib_logproc::LOG_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/prontus_tags_import_log.html";
    $lib_logproc::MODO_WEB = $MODO_WEB;

    # Bloqueo
    $LOCK_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/semaforo_tags_import";
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

    my ($data_file) = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/tags_import.xml";
    my $archivo = &glib_fildir_02::read_file($data_file);
    my ($err) = &lib_prontus::valid_xml_import($archivo);
    if ($err) {
        &finishLoading("El archivo ingresado no es un XML bien formado, no es posible cargarlo");
        &lib_logproc::handle_error("El archivo ingresado no es un XML bien formado, no es posible cargarlo");
    };

    &lib_logproc::add_to_log_count("Borrando datos actuales de la base de datos.\n");
    my ($sql) = "delete from TAGS";
    $BD->do($sql) || (&finishLoading("No fue posible borrar los TAGS actuales") && &lib_logproc::handle_error("No fue posible borrar Tags") );

    &tags_import($archivo);

    &lib_logproc::add_to_log_count("PROCESO DE IMPORTACION FINALIZADO");
    &lib_logproc::writeRule();

    $TOT_REGS = '0' if ($TOT_REGS eq '');
    $OK_REGS = '0' if ($OK_REGS eq '');

    &lib_logproc::add_to_log("Nro. de registros procesados: $TOT_REGS\nRegistros ingresados OK: $OK_REGS");
    &lib_logproc::add_to_log_finish("Operaci&oacute;n finalizada.");

    # REGENERA EL MAPA
    # &lib_prontus::make_mapa('', $BD); # rotulos tags

#    my $mv;
#    foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
#        &lib_prontus::make_mapa($mv, $BD);
#    };

    # Genera tags en arch. JS, para ser incluido en FIDs
#    my $arr_tst = &lib_secc::genera_array_temas_subtemas($BD, '', 'solo habilitadas');
#    my $dir_tags4fids = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CPAN . '/procs/tags4fids';
#    &glib_fildir_02::check_dir($dir_tags4fids);
#    &glib_fildir_02::write_file($dir_tags4fids . '/tags4fids.js', $arr_tst);

    # Se libera el caché de los tags del fid
    &lib_tags::clear_cache($prontus_varglb::PRONTUS_ID);

    $BD->disconnect;

    &finishLoading('');

    # Elimina el bloqueo y termina ejecucion.
    &lib_lock::unlock_file($lock_obj, $LOCK_FILE);


}; # main

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub get_id_mayor {
  my ($buffer_xml) = $_[0];
  #my ($tipo) = $_[1]; # seccion \ tema \ subtema
  my $id_mayor = 0;
  # Obtiene el mayor id q venga de seccion o de tema o de subtema
  while ($buffer_xml =~ /<tag +id *= *["']([0-9]+)["']>.+?<\/tag>/isg) {
    my $id = $1;
    next if ($id !~ /^[0-9]+$/);
    $id_mayor = $id if ($id > $id_mayor);
  };
  return $id_mayor;
};
# ---------------------------------------------------------------
sub tags_import {

  my ($buffer_xml) = $_[0];
  my ($sql, $ret, $linea);

  &lib_logproc::add_to_log_count("Procesando archivo de datos.");

  $buffer_xml =~ s/(\r\n)/\n/g;
  $buffer_xml =~ s/\r//g;

  my (@data, $i, %tags, @filas);
  my ($id, $nom, $count, $mostrar);

  # obtiene los id mayores de cada tags level para poder asignar id a los reg. nuevos
  $ID_MAYOR = &get_id_mayor($buffer_xml);
  $TOT_REGS = 0;

  while ($buffer_xml =~ /<tag +id *= *["']([0-9]*)["']>(.+?)<\/tag>/isg) {
    $id = $1;
    my $tag = $2;
    # si no viene id asigno uno nuevo
    if (!$id) {
      $ID_MAYOR++;
      $id = $ID_MAYOR;
    };

    next if (! &procesar_xml($id, $tag));

    # Actualiza la portada tagonomica
    #&actualiza_tagport($id);
  };
};
# ---------------------------------------------------------------
sub procesar_xml {

    my ($id_level, $xml_segment) = @_;

    $TOT_REGS++;

    # Si viene id deben ser solo digitos.
    if ($id_level !~ /^[0-9]*$/) {
        $xml_segment=~s/>/&gt;/g;              # >
        $xml_segment=~s/</&lt;/g;              # <
        &saltar_reg("Id no válido en registro [$TOT_REGS] id=$id_level" . $xml_segment);
        &saltar_reg($xml_segment);
        return 0;
    };

    my ($nom, %nom_vistas, $count, $mostrar, $nom4vistas);

    # nom
    if ($xml_segment =~ /<nom>(.*?)<\/nom>/is) {
        $nom = &lib_prontus::despulga_item_tax($1);
        $nom = &lib_prontus::unescape_xml($nom);

    };
    if ($nom !~ /\w+/) {
        $xml_segment=~s/>/&gt;/g;              # >
        $xml_segment=~s/</&lt;/g;              # <
        &saltar_reg("Nombre no válido en registro [$TOT_REGS] id=$id_level" . $xml_segment);
        return 0;
    };
    if (exists $NOMBRES{"$nom"}) {
        $xml_segment=~s/>/&gt;/g;              # >
        $xml_segment=~s/</&lt;/g;              # <
        &saltar_reg("Nombre repetido en registro [$TOT_REGS] id=$id_level" . $xml_segment);
        return 0;
    } else {
        $NOMBRES{"$nom"} = 1;
    };

    # count
    if ($xml_segment =~ /<count>(.*?)<\/count>/is) {
        $count = &lib_prontus::despulga_item_tax($1);
    };
    $count =~ s/[^\d]//g;
    if (!$count || $count !~ /^[\d]+$/) {
      $count = 0;
    };

    # mostrar
    if ($xml_segment =~ /<mostrar>(.*?)<\/mostrar>/is) {
        $mostrar = &lib_prontus::despulga_item_tax($1);
    };

    if ((!$mostrar) || ($mostrar =~ /no/i)) { $mostrar = ''; }
    else { $mostrar = '1'; };

    # nombres de taglevel en otras vistas
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
    $ret = &insert_tag($id_level, $nom, $count, $mostrar, $nom4vistas);
    if ($ret) {
        $OK_REGS++;  # Total de reg. insertados normalmente
    } else {
        $xml_segment=~s/>/&gt;/g;              # >
        $xml_segment=~s/</&lt;/g;              # <
        &lib_logproc::add_to_log_count("INSERT error en registro [$TOT_REGS] id=$id_level ($DBI::errstr) $xml_segment");
        return 0;
    };
    return 1;
};


# ---------------------------------------------------------------
sub insert_tag {
    my ($id, $nom, $count, $mostrar, $nom4vistas) = @_;
    my ($sql, $ret);

    $nom = $BD->quote($nom);

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

    # Se hace la inserción
    $sql = "insert into TAGS values(NULL, $nom, \"$count\", \"$mostrar\", $nom4vistas)";
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
    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_tags_import.js";
    my $msg = '{"status":1, "msg":"'.$msg.'"}';
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", $msg);
};

# -------------------------END SCRIPT----------------------
