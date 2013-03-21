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
# Hacer deploy del prontus en base a lo indicado por el user en los pasos anteriores
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Al termino del script se invoca via location a wizard_report.cgi sin parametros.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Via submit desde /wizard_prontus/core/confirm.html
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# No utiliza.
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
# No utiliza.
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 12/2005 - YCH - Primera Version.
# p10.11 - 01/02/2008 - YCH - Ahora la extension de las paginas del modelo y las resultantes son de la extension que se declare para el modelo en el cfg del mismo en MODEL_EXT
# p10.11 - 04/02/2008 - CVI - Correciones al wizard. Manejo de extensión via cfg del modelo.
# p10.12.20 - 26/05/2009 - PRB - Se incorpora restriccion para creacion de carpetas en modelo vacio.
# ---------------------------------------------------------------


# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

use glib_cgi_04;
use glib_fildir_02;
use glib_hrfec_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use File::Copy;
use strict;
use glib_dbi_02;
use DBI;
use lib_prontus;
use lib_setbd;

# ---------------------------------------------------------------
# MAIN.
# ------
my (%FILES_CAMBIAR_REF);
my (%FORM, %PRONTUS);
my ($INF_DIR) = "$prontus_varglb::DIR_SERVER/wizard_prontus/_data";
my ($INF_FILE) = "$INF_DIR/inf.txt";
my ($CRLF) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;

main:{

  &glib_cgi_04::new();
  $FORM{'Sbm_ACCION'} = &glib_cgi_04::param('Sbm_ACCION');

  my ($msg_err,
        $prontus_id,
        $extension,
        $smtp,
        $model_nom,
        $title_site_name,
        $new_title_site_name,
        $server_bd,
        $nom_bd,
        $user_bd,
        $pwd_bd,
        $superuser_bd,
        $superpwd_bd) = &check_paso_anterior();

  my $lnk_paso1 = '<br/><br/><a href="/wizard_prontus/core/paso1.html">Volver a Paso 1</a><br/><br/>';

  if ($msg_err) {
    $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
    &glib_html_02::print_pag_result('Error', $msg_err . $lnk_paso1, 0, "exit=1, ctype=1, link=nolink");
  };

  my ($err_basedatos, $err_postprocesos) = &deploy($prontus_id, $extension, $smtp, $model_nom, $title_site_name, $new_title_site_name, $server_bd, $nom_bd, $user_bd,$pwd_bd,$superuser_bd,$superpwd_bd);
  if ($err_basedatos ne '') {
    $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
    &glib_html_02::print_pag_result('Error', $err_basedatos . "<br/><br/>El Asistente Prontus no pudo instalar correctamente la base de datos, no es posible continuar con el proceso.<br/><br/>Verifique los datos indicados para la base de datos.<br /><br />$lnk_paso1", 0, "exit=1, ctype=1, link=nolink");
  };

  if ($err_postprocesos ne '') {
    $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
    &glib_html_02::print_pag_result('¡Atención!', $err_postprocesos . "<br/><br/>No obstante este error, Wizard Prontus de igual manera instaló el publicador, intente gatillar nuevamente el proceso que falló, desde el Panel de Control del publicador instalado.<br/><br/>Haga click <a href=\"wizard_reporte.cgi?DIR=/$prontus_id&TOPE=/\">aquí</a> para continuar y ver el reporte de instalación.<br /><br />", 0, "exit=1, ctype=1, link=nolink");
  };


  print "Location: wizard_reporte.cgi?DIR=/$prontus_id&TOPE=/\n\n";
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

sub deploy {
    my ($prontus_id, $extension, $smtp, $model_nom, $title_site_name, $new_title_site_name, $server_bd, $nom_bd, $user_bd,$pwd_bd,$superuser_bd,$superpwd_bd) = @_;

    # Crea la BD si es que se indicaron los datos y si es que no existe.
    my $err_createdb;
    if (($superuser_bd ne '') && ($superpwd_bd ne '')) {

        # ver si existe
        my @databases = DBI->data_sources("mysql", {"host" => $server_bd, "user" => $superuser_bd, "password" => $superpwd_bd});
        my $existe_base = 0;
        foreach my $k (@databases) {
            if ($k eq $nom_bd) {
                $existe_base = 1;
                last;
            };
        };

        # si no existe, crearla
        if (!$existe_base) {
            # crear BD
            my $drh = DBI->install_driver('mysql') || warn "No se pudo obtener handler para crear BD. DBI Error Code: [$DBI::err][$DBI::errstr] ";
            if ($DBI::err) {
                $err_createdb = "No fue posible crear base de datos MySQL '$nom_bd'. Cod[$DBI::err][$DBI::errstr]";
            } else {
                my $rc = $drh->func("createdb", $nom_bd, $server_bd, $superuser_bd, $superpwd_bd, 'admin') || warn "Error en createdb. DBI Error Code: [$DBI::err][$DBI::errstr]";
                $err_createdb = "No fue posible crear base de datos MySQL '$nom_bd'. Cod[$DBI::err][$DBI::errstr]" if ($DBI::err);
            };

            return ($err_createdb, '') if ($err_createdb ne '');

            # Si llega hasta aca, es porque se ha creado ok.
        };

        # Si se especifico superusuario, haya existido o no la bd, igual regulariza el user y el charset

        # Conectarse a la bd re100 creada, para asignar user y setear charset
        my ($base_admin, $conn_result_admin) = &lib_prontus::conectar_prontus_bd('MYSQL', $nom_bd, $server_bd, $superuser_bd, $superpwd_bd,);
        return ($conn_result_admin, '') if ($conn_result_admin ne '');

        # asignar el usuario, previa conn normal a la BD
        my $sql_grant = "grant all privileges on $nom_bd.* to '$user_bd'\@'$server_bd' identified by '$pwd_bd'";
        $base_admin->do($sql_grant)
                     || warn "Error en grant, DBI Error Code: [$DBI::err][$DBI::errstr] sql[$sql_grant]";
        return ("No es posible asignar privilegios al usuario de la base de datos MySQL. Cod[$DBI::err][$DBI::errstr]", '') if ($DBI::err);

        # asignar el charset, previa conn normal a la BD
        $base_admin->do("alter database $nom_bd CHARACTER SET=utf8 COLLATE=utf8_general_ci")
                     || warn "Error al setear charset, DBI Error Code: [$DBI::err][$DBI::errstr]";
        return ("No es posible establecer el charset para base de datos MySQL, es probable que el superusuario especificado no tenga privilegios de 'alter' para la BD. Cod[$DBI::err][$DBI::errstr]", '') if ($DBI::err);

        $base_admin->disconnect;
    };



    # Intenta conectarse a la BD existente, si no resulta, aborta todo.
    my ($base, $conn_result) = &lib_prontus::conectar_prontus_bd('MYSQL', $nom_bd, $server_bd, $user_bd, $pwd_bd);
    return ($conn_result, '') if ($conn_result ne '');

    # En este punto, se supone que ya existe la BD y esta creada la conn,
    # Por tanto ya se pueden crear las tablas.
    # Si ya existen, no crea nada y arroja error, puede significar que se esta usando la misma BD para 2 prontuses!

    my ($msg_ret, $hay_err);
    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_secc($base, 'MYSQL');
    return ($msg_ret, '') if ($hay_err ne '');

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_temas($base, 'MYSQL');
    return ($msg_ret, '') if ($hay_err ne '');

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_subtemas($base, 'MYSQL');
    return ($msg_ret, '') if ($hay_err ne '');

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_tags($base, 'MYSQL');
    return ($msg_ret, '') if ($hay_err ne '');

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_tagsart($base, 'MYSQL');
    return ($msg_ret, '') if ($hay_err ne '');

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_coment($base, 'MYSQL');
    return ($msg_ret, '') if ($hay_err ne '');

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_asset($base, 'MYSQL');
    return ($msg_ret, '') if ($hay_err ne '');

    ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_art($base, 'MYSQL');
    return ($msg_ret, '') if ($hay_err ne '');

    $base->disconnect;


    # copiar /wizard_prontus/prontus_dir/ --> /<prontus_id>/

    &glib_fildir_02::copy_tree("$prontus_varglb::DIR_SERVER/wizard_prontus", 'prontus_dir',
    $prontus_varglb::DIR_SERVER, $prontus_id);

    my $dir_models = "$prontus_varglb::DIR_SERVER/wizard_prontus/models";
    my $path_model = "$dir_models/$model_nom";


    # copiar /wizard_prontus/models/<modelo> --> /<prontus_id>
    &glib_fildir_02::copy_tree($dir_models, $model_nom, $prontus_varglb::DIR_SERVER, $prontus_id);


    # No copiar el id, lo crea la aplicacion
    # &File::Copy::copy("$path_model/cpan/$model_nom-id.cfg", "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id" . '-id.cfg');

    # al copiar la carpeta completa del modelo ya se copiaron los cfg, ahora solo hay que renombrarlos.
    &File::Copy::move("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$model_nom" . '-art.cfg', "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id" . '-art.cfg');
    &File::Copy::move("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$model_nom" . '-port.cfg', "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id" . '-port.cfg');
    # &File::Copy::move("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$model_nom" . '-bd.cfg', "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id" . '-bd.cfg');
    &File::Copy::move("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$model_nom" . '-tax.cfg', "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id" . '-tax.cfg');
    &File::Copy::move("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$model_nom" . '-usr.cfg', "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id" . '-usr.cfg');
    &File::Copy::move("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$model_nom" . '-var.cfg', "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id" . '-var.cfg');
    &File::Copy::move("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$model_nom" . '-coment.cfg', "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id" . '-coment.cfg');
    &File::Copy::move("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$model_nom" . '-posting.cfg', "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id" . '-posting.cfg');
    # &File::Copy::move("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/buscador_prontus.cfg", "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/buscador_prontus.cfg");
    # Si el CFG de BD del modelo antiguo existe, se borra.
    unlink("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$model_nom" . '-bd.cfg') if(-f "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$model_nom" . '-bd.cfg');

    # eliminar de -var.cfg el server_smtp
    &remove_var_cfg($prontus_id, 'SERVER_SMTP', '-var');

    # Agrega smtp al inicio del -var.cfg
    &add_prontus_cfg($prontus_id, "\n[SERVIDOR SMTP]\nSERVER_SMTP = '$smtp'\n", 1, '-var');
    &add_prontus_cfg($prontus_id, "\n[NOMBRE DEL SERVER NECESARIO PARA CRONS]\nPUBLIC_SERVER_NAME = '$ENV{'HTTP_HOST'}'\n", 0, '-var');

    # Elimina el -id.cfg que traia el modelo, para poner el del nuevo prontus
    unlink "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$model_nom" . '-id.cfg';

    # Agrega datos generales al inicio del -id.cfg
    &add_prontus_cfg($prontus_id, "[IDENTIFICACION]\nPRONTUS_ID = '$prontus_id'\nTIPO_PRONTUS = 'PRONTUS-04'\n", 1, '-id');
    #&add_prontus_cfg($prontus_id, "\n[NOMBRE DEL SERVER NECESARIO PARA CRONS]\nPUBLIC_SERVER_NAME = '$ENV{'HTTP_HOST'}'\n", 0, '-id');

    # Agrega datos de la BD al -bd.cfg
    &add_prontus_cfg($prontus_id, "[BASE DE DATOS]\nMOTOR_BD = 'MYSQL'\nNOM_BD = '$nom_bd'\nUSER_BD = '$user_bd'\nPWD_BD = '$pwd_bd'\nSERVER_BD = '$server_bd'\n", 1, '-bd');

    # Rescata nom del prontus_base
    my $prontus_base = $model_nom;

    # Cambia referencias
    &cambia_referencias("$prontus_varglb::DIR_SERVER/$prontus_id", $prontus_base, $prontus_id, $title_site_name, $new_title_site_name);

    # Elimina archivos de usuario
    my $dir2del = "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/data/users";
    my @lisdir = &glib_fildir_02::lee_dir($dir2del);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    foreach my $k (@lisdir) {
        unlink "$dir2del/$k" if (-f "$dir2del/$k");
    };

    # Elimina cfg e icono del modelo, utiles solo para el wizard
    my $file2del = "$prontus_varglb::DIR_SERVER/$prontus_id/$prontus_base.cfg";
    unlink $file2del if (-f $file2del);

    $file2del = "$prontus_varglb::DIR_SERVER/$prontus_id/$prontus_base.gif";
    unlink $file2del if (-f $file2del);


    # Renombra carpeta de indices del buscador
    if (-d "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/data/search/$prontus_base") {
        &File::Copy::move("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/data/search/$prontus_base",
        "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/data/search/$prontus_id");
    };

    # Borra cache de no publicados
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/data/cache");

    # Regenerar tabla de articulos, para que se pueble en base a los XML
    use FindBin '$Bin';
    my $rutaScript = $Bin;
    system "$rutaScript/prontus_regenerabd_real.cgi $prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id.cfg ";
    return ('', 'Error al poblar tabla de artículos') if ($? != 0);
    
    system "$rutaScript/dam/prontus_dam_regen_real.cgi $prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id.cfg ";
    return ('', 'Error al poblar tabla multimedia') if ($? != 0);


    # Importa XML de tax que venia en el modelo en la carpeta $path_model/cpan/procs/tax_import.xml y que se copio al prontus re100 instalado
    if (!-f "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/procs/tax_import.xml") {
        return ('', "Error al importar Categorías del Modelo. No se encuentra, en el prontus instalado, el archivo XML con la información: /$prontus_id/cpan/procs/tax_import.xml")
    };
    system "$rutaScript/prontus_tax_import_real.cgi $prontus_varglb::DIR_SERVER $prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id.cfg ";
    return ('', 'Error al importar Categorías del Modelo') if ($? != 0);

    return ('', '');

};


# ---------------------------------------------------------------
sub cambia_referencias {
# Cambia sintaxis de includes a plantillas y site en prontus destino

  my ($dir) = $_[0];
  my ($prontus_base) = $_[1]; # nom del publicador en base al cual se hizo este modelo
  my ($prontus_id) = $_[2];
  my ($title_site_name) = $_[3];
  my ($new_title_site_name) = $_[4];

  if (-d $dir) {
    # Abre directorio.
    opendir(DIR, $dir) || die "Can't opendir" . $dir . $!;
    my @entries = readdir(DIR);
    closedir DIR;
    my $entry;
    foreach $entry (@entries) {
      if (($entry ne '.') and ($entry ne '..')) {

        if (-d "$dir/$entry") {
          next if ($entry eq 'core');
          &cambia_referencias("$dir/$entry", $prontus_base, $prontus_id, $title_site_name, $new_title_site_name);
        }else{
          if (($entry =~ /\.html$/) || ($entry =~ /\.shtml$/) || ($entry =~ /\.php$/) || ($entry =~ /\.asp$/) || ($entry =~ /\.xml$/) || ($entry =~ /\.js$/) || ($entry =~ /\.css$/) || ($entry =~ /\.idx$/)) {
            my $buffer = &glib_fildir_02::read_file("$dir/$entry");
            $buffer =~ s/$CRLF/\x0a/sg;
            my ($nompag, $newnompag);
            # cambia en cada pagina las referencias a archivos con posible extension erronea.
            # p10.11
            # foreach $nompag (keys %FILES_CAMBIAR_REF) {
            #  $newnompag = $FILES_CAMBIAR_REF{$nompag};
            #  $buffer =~ s/$nompag/$newnompag/ig;
            # };

            # Cambia nombre del publicador de origen por el q escogio el user.
            $buffer =~ s/$prontus_base\//$prontus_id\//ig;
            $buffer =~ s/"$prontus_base"/"$prontus_id"/ig;
            $buffer =~ s/'$prontus_base'/'$prontus_id'/ig;
            $buffer =~ s/\/$prontus_base("|'|\&)?/\/$prontus_id\1/ig;

            # CAMBIA SITE NAME
            if (($entry =~ /\.html$/) || ($entry =~ /\.shtml$/) || ($entry =~ /\.php$/) || ($entry =~ /\.asp$/) || ($entry =~ /\.xml$/)) {
                if ($buffer =~ /<title>(.*?)<\/title>/i) {
                    my $title_content = $1;
                    my $new_tsn = &lib_prontus::escape_xml($new_title_site_name);
                    $title_content =~ s/$title_site_name/$new_tsn/ig;
                    $buffer =~ s/<title>.*?<\/title>/<title>$title_content<\/title>/i;
                };
            };

            &glib_fildir_02::write_file("$dir/$entry", $buffer);
          };
        };
      };
    };
  };


};

# ---------------------------------------------------------------
sub remove_var_cfg {
# Agrega texto al cfg del publicador destino.
  my $prontus_id = $_[0];
  my $nom_var = $_[1];
  my $tipocfg = $_[2];
  my $cfg_file = "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id$tipocfg.cfg";
  my $buffer_cfg = &glib_fildir_02::read_file($cfg_file);
  $buffer_cfg =~ s/$CRLF/\x0a/sg;

  $buffer_cfg =~ s/(\s*\[[^\]]*\]\n+)?\s*$nom_var\s*=\s*("|').*?(\n|$)//;

  &glib_fildir_02::write_file($cfg_file, $buffer_cfg);
};

# ---------------------------------------------------------------
sub add_prontus_cfg {
# Agrega texto al cfg del publicador destino.
  my $prontus_id = $_[0];
  my $text = $_[1];
  my $infront = $_[2];
  my $tipocfg = $_[3];
  my $cfg_file = "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id$tipocfg.cfg";
  my $buffer_cfg = &glib_fildir_02::read_file($cfg_file);
  $buffer_cfg =~ s/$CRLF/\x0a/sg;
  if ($infront) {
    $buffer_cfg = $text . $buffer_cfg;
  }
  else {
    $buffer_cfg .= $text;
  };
  &glib_fildir_02::write_file($cfg_file, $buffer_cfg);
};

# ---------------------------------------------------------------
sub check_paso_anterior {
# Chequea que se haya pasado por el paso 1

  if (! -f $INF_FILE) {
    return "[errInfFile] Solicitud de ejecución no válida.";
  };

  # Leer y cargar y validar contenido del INF.
  my $buffer = &glib_fildir_02::read_file($INF_FILE);
  my ($prontus_id, $extension, $smtp);

  my $title_site_name; # del segmento MODEL (obt. desde cfg del modelo)
  my $new_title_site_name; # del segmento PRONTUS (ingresado por el usuario)

  my ($server_bd, $nom_bd, $user_bd,$pwd_bd,$superuser_bd,$superpwd_bd);

  if ($buffer =~ /(\[PRONTUS\].*\[\/PRONTUS\]\n\n)/s) {
    my $buffer_prontus = $1;
    # Validar id
    if ($buffer_prontus !~ /PRONTUS_ID=(\w+)\n/) {
      return 'Información de paso 1 está corrupta.';
    }
    else {
      $prontus_id = $1;
    };



    # extension
    # CVI se movió a la seccion [MODEL] [/MODEL]
#    if ($buffer_prontus !~ /MODEL_EXT=(\w+)\n/) {
#      return 'Información de paso 1 está corrupta.';
#    }
#    else {
#      $extension = $1;
#    };

    # smtp
    if ($buffer_prontus =~ /SERVER_SMTP=([\w\.\-]+)\n/) {
      $smtp = $1;
    };


    if ($buffer_prontus !~ /NEW_TITLE_SITE_NAME=(.+?)\n/) {
      return 'Información de paso 1 está corrupta.';
    }
    else {
      $new_title_site_name = $1;
    };


    $server_bd = $1 if ($buffer_prontus =~ /server_bd=(.*?)\n/i);
    $nom_bd = $1 if ($buffer_prontus =~ /nom_bd=(.*?)\n/i);
    $user_bd = $1 if ($buffer_prontus =~ /user_bd=(.*?)\n/i);
    $pwd_bd = $1 if ($buffer_prontus =~ /pwd_bd=(.*?)\n/i);
    $superuser_bd = $1 if ($buffer_prontus =~ /superuser_bd=(.*?)\n/i);
    $superpwd_bd = $1 if ($buffer_prontus =~ /superpwd_bd=(.*?)\n/i);


  }
  else {
    return 'Información de paso 1 está corrupta';
  };

  # Validar que no exista el dir destino del prontus.
  # Esto ya se chequea en el paso 1 pero se hace nuevamente por seguridad.
  my $dir_prontus = "$prontus_varglb::DIR_SERVER/$prontus_id";

  if (-d $dir_prontus) {
    return "El directorio " . "[/$prontus_id]" . " ya existe. Para concretar el proceso de instalación, Ud. debe cambiar el nombre especificado para el publicador, o bien, <br>eliminar manualmente el directorio existente que genera el conflicto.";
  }
  else {
    # Lo creo y luego lo borro para verificar que este ok.
    if (&glib_fildir_02::check_dir($dir_prontus)) {
      &glib_fildir_02::borra_dir($dir_prontus);
    }
    else {
      return "No se puede crear el directorio destino del publicador " . "[/$prontus_id]" . " No es posible continuar con la instalación.";
    };
  };

  # valida q se haya pasado por paso2
  my $model_nom;
  if ($buffer =~ /(\[MODEL\].*\[\/MODEL\]\n\n)/s) {
    my $buffer_model = $1;
    # Validar id
    if ($buffer_model !~ /MODEL_NOM=(\w+)\n/) {
      return 'Información de paso 2 está corrupta.';
    }
    else {
      $model_nom = $1;
    };
    # p10.11
    if ($buffer_model !~ /MODEL_EXT=(\w+)\n/) {
      return 'Error en cfg del modelo: extensión no declarada.';
    }
    else {
      $extension = $1;
    };

    if ($buffer_model !~ /TITLE_SITE_NAME=(.+?)\n/) {
      return 'Error en cfg del modelo: falta TITLE_SITE_NAME';
    }
    else {
      $title_site_name = $1;
    };

  }
  else {
    return 'Información de paso 2 está corrupta';
  };


  return ('', $prontus_id,$extension, $smtp, $model_nom, $title_site_name, $new_title_site_name, $server_bd, $nom_bd, $user_bd,$pwd_bd,$superuser_bd,$superpwd_bd);

};


# -------------------------------END SCRIPT----------------------

