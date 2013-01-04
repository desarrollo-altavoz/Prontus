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
use glib_cgi_04;

use lib_prontus;
use Session;
use glib_hrfec_02;
use glib_fildir_02; # Prontus 6.0

use strict;
use File::Copy;

use lib_cookies;
use lib_multiediting;
use Update;
use Net::FTP;
use Net::DNS;
use Digest::MD5 qw(md5_hex);

# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM, $TIPO_PRONTUS, $AREA_MENU, $AREA_CONT, $PRONTUS_KEY);
my ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_ID, $USERS_EMAIL);


my $MAX_RETRIES_LOGIN = 10;

main: {
    my ($lnk);

    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});
    $FORM{'_usr'} = &glib_cgi_04::param('_usr');
    $FORM{'_psw'} = &glib_cgi_04::param('_psw');

    # Carga var. globales con los datos del arch. conf.
    &lib_prontus::load_config($FORM{'_path_conf'});   # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Escribe htaccess en el data para prohibir acceso http a este dir.
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/.htaccess",
                                "Order Allow,Deny\nDeny from all");

    if ($ENV{'REQUEST_METHOD'} ne 'POST') {
        &glib_html_02::print_json_result(0, 'Solicitud no válida', 'exit=1,ctype=1');
    };

    # Dir de user lock
    my $dir_userlock = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/user_lock";
    if ( ! (&glib_fildir_02::check_dir($dir_userlock)) ) {
        &glib_html_02::print_json_result(0, 'No se pudo crear dir userlock', 'exit=1,ctype=1');
    };

    if ( ($FORM{'_usr'} eq '') or ($FORM{'_psw'} eq '') ) {
        &glib_html_02::print_json_result(0, 'Usuario o Contraseña no válida', 'exit=1,ctype=1');
    };

    my $file_userlock = lc "$dir_userlock/$FORM{'_usr'}.txt";

    # Chequea archivo de bloqueo de User actual y lo elimina si es mas antiguo q 1/2 hora, de acuerdo a la fecha de modif. del archivo.
    &reset_user_lockfile($file_userlock);

    # Si el user esta dentro de los bloqueados.
    # Se sabe porque el archivo <user>.txt tiene el contador interno >= 4
    if (&user_bloqueado($file_userlock)) {
        &glib_html_02::print_json_result(0, "Se ha alcanzado el número máximo de intentos para ingresar, "
        . "tu cuenta ha sido bloqueada.", 'exit=1,ctype=1');
    };

    if (&lib_prontus::open_dbm_files() ne 'ok') {
        &glib_html_02::print_json_result(0, 'No fue posible abrir archivos de usuarios.', 'exit=1,ctype=1');
    };

    my $login_result = &user_valido();
    if ($login_result >= 1) {

        my $check_msg;
        $check_msg = &check_modules() if (! &lib_prontus::is_win32());
        &glib_html_02::print_json_result(0, $check_msg, 'exit=1,ctype=1') if ($check_msg);
        my $user4log = $FORM{'_usr'};
        $user4log = 'sys-admin' if ($login_result == 2);
        &lib_prontus::write_log('Login', $user4log, '');
        &release_user($file_userlock);

        if ((($FORM{'_usr'} eq 'admin') && ($FORM{'_psw'} eq 'prontus')) || ($FORM{'_psw'} =~ /\w\w\wprontus\w\w\w/)) {
            # Si metio la "clave power", entonces obligar a cambiarla, de paso le borro la cookie pa q no siga navegando.
            &lib_cookies::set_simple_cookie('USERS_USR_' . $prontus_varglb::PRONTUS_ID, ''); # pa q no pueda navegar
            &lib_cookies::set_simple_cookie('KEY_' . $prontus_varglb::PRONTUS_ID, '');
            # Mata sesion en caso de que haya
            my $sess_obj = Session->new(
                            'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                            'document_root'     => $prontus_varglb::DIR_SERVER)
                            || die("Error inicializando objeto Session: $Session::ERR\n");
            # libera recursos de sesion existente para info de concurrencia
            if ($sess_obj->{id_session} ne '') {
                my %cookies = &lib_cookies::get_cookies();
                my $user_anterior = $cookies{'USERS_USR_' . $prontus_varglb::PRONTUS_ID};

                &lib_multiediting::free_concurrency( $prontus_varglb::DIR_SERVER,
                                                      $prontus_varglb::PRONTUS_ID,
                                                      'port',
                                                      $user_anterior,
                                                      $sess_obj->{id_session});

                &lib_multiediting::free_concurrency( $prontus_varglb::DIR_SERVER,
                                                      $prontus_varglb::PRONTUS_ID,
                                                      'art',
                                                      $user_anterior,
                                                      $sess_obj->{id_session});
                                                      
                &lib_multiediting::free_lock( $prontus_varglb::DIR_SERVER,
                                                      $prontus_varglb::PRONTUS_ID,
                                                      'art',
                                                      $user_anterior,
                                                      $sess_obj->{id_session});
                                                      
                &lib_multiediting::free_lock( $prontus_varglb::DIR_SERVER,
                                                      $prontus_varglb::PRONTUS_ID,
                                                      'port',
                                                      $user_anterior,
                                                      $sess_obj->{id_session});
            };
            $sess_obj->end_session();

            my $buffer_changepass = &get_changepass(); # hacer location a cgi
            &glib_html_02::print_json_result(2, $buffer_changepass, 'exit=1,ctype=1');
        } else {
            # Ok y setear cookie.
            &lib_cookies::set_simple_cookie('USERS_USR_' . $prontus_varglb::PRONTUS_ID, $USERS_USR);
            &lib_cookies::set_simple_cookie('KEY_' . $prontus_varglb::PRONTUS_ID, $USERS_PSW);
            # crea obj session
            my $sess_obj = Session->new(
                            'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                            'document_root'     => $prontus_varglb::DIR_SERVER)
                            || die("Error inicializando objeto Session: $Session::ERR\n");

            # libera recursos de sesion existente para info de concurrencia
            if ($sess_obj->{id_session} ne '') {
                my %cookies = &lib_cookies::get_cookies();
                my $user_anterior = $cookies{'USERS_USR_' . $prontus_varglb::PRONTUS_ID};

                &lib_multiediting::free_concurrency( $prontus_varglb::DIR_SERVER,
                                                      $prontus_varglb::PRONTUS_ID,
                                                      'port',
                                                      $user_anterior,
                                                      $sess_obj->{id_session});

                &lib_multiediting::free_concurrency( $prontus_varglb::DIR_SERVER,
                                                      $prontus_varglb::PRONTUS_ID,
                                                      'art',
                                                      $user_anterior,
                                                      $sess_obj->{id_session});

                &lib_multiediting::free_lock( $prontus_varglb::DIR_SERVER,
                                                      $prontus_varglb::PRONTUS_ID,
                                                      'art',
                                                      $user_anterior,
                                                      $sess_obj->{id_session});
                                                      
                &lib_multiediting::free_lock( $prontus_varglb::DIR_SERVER,
                                                      $prontus_varglb::PRONTUS_ID,
                                                      'port',
                                                      $user_anterior,
                                                      $sess_obj->{id_session});
                                                      
            };
            # nueva sesion
            $sess_obj->set_new_session();

            # Descarga archivo descriptor de update
            my $upd_obj = Update->new(
                            'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                            'version_prontus'   => $prontus_varglb::VERSION_PRONTUS,
                            'path_conf'         => $FORM{'_path_conf'},
                            'document_root'     => $prontus_varglb::DIR_SERVER)
                            || &glib_html_02::print_pag_result('Error',"Error inicializando objeto Update: $Update::ERR", 1, 'exit=1,ctype=1');

            $upd_obj->descarga_upd_descriptor();

            &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');
        };
    } else {
        if ($login_result == -1) { # flag_sysadmin.txt pero no se supo la clave
            &glib_html_02::print_json_result(0, $prontus_varglb::MSG_BLOQUEOSYSADMIN, 'exit=1,ctype=1');
        } else {  # user no valido normal
            my $referer = $ENV{'HTTP_REFERER'};
            $referer = "Referer[$referer]" if ($referer);
            &lib_prontus::write_log('FailLogin', "$FORM{'_usr'}/$FORM{'_psw'}", $referer);
            if ( &user_existente() ) {
                &capture_user($file_userlock); # incrementa el contador de intentos fallidos al interior del archivo <user>.txt, si no existia lo crea.
            };
            &glib_html_02::print_json_result(0, 'Usuario o Contraseña no válida', 'exit=1,ctype=1');
        };
    };



};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------


# ---------------------------------------------------------------


sub check_modules {
    my $no_hay_sqlite;
    my $no_hay_mysql;
    eval "require DBD::SQLite2;";    $no_hay_sqlite = $@;
    eval "require DBD::mysql;";    $no_hay_mysql = $@;
    # print STDERR "SQLITE[$no_hay_sqlite]\n";
    # print STDERR "MYSQL[$no_hay_mysql]\n";


    if (($no_hay_sqlite) && ($no_hay_mysql)) {
        return "No se detectó ningún módulo Perl válido para utilizar BD en el Servidor";
    };

    if (($no_hay_sqlite) && ($prontus_varglb::MOTOR_BD eq 'PRONTUS') && (!$no_hay_mysql)) {
        return "El módulo Perl requerido para utilizar el motor de BD 'PRONTUS', indicado en CFG, no se encuentra disponible en el Servidor.\nEspecifique 'MYSQL' como motor de BD.";
    };

    if (($no_hay_mysql) && ($prontus_varglb::MOTOR_BD eq 'MYSQL') && (!$no_hay_sqlite)) {
        return "El módulo Perl requerido para utilizar el motor de BD 'MYSQL', indicado en CFG, no se encuentra disponible en el Servidor.<br>Especifique 'PRONTUS' como motor de BD.";
    };

    return '';

};
# ---------------------------------------------------------------
sub ftp_connect {
    my ($ipServer, $userServer, $passServer) = @_;
    my $ftp_debug = 0;
    my $stamp = &glib_hrfec_02::get_dtime_pack4();
    my $ftp = Net::FTP->new($ipServer,Timeout=>15,Debug=>$ftp_debug,Passive=>1) or return ("\t* $stamp - FTP a [$ipServer][$userServer]... No se puede conectar con el servidor, timeout[15]segs, modo[Pasivo] : $@\n");
    my $ret;
    $ret = $ftp->login($userServer,$passServer);
    if (!$ret) {
        my $errMsg = $ftp->message; # incluye un \n al final
        $ftp->quit();
        return("\t* FTP a [$ipServer][$userServer]... Falla login : " . $errMsg);
    };

    $ret = $ftp->cwd('/'); # release/
    if (!$ret) {
        my $errMsg = $ftp->message;
        $ftp->quit();
        return("\t* FTP a [$ipServer][$userServer]... Falla cwd('/') : " . $errMsg);
    };

    return $ftp;
};

# ---------------------------------------------------------------
sub user_bloqueado {
# Detecta si el user esta dentro de los bloqueados para abortar ejecucion.
# Se sabe porque el archivo <user>.txt tiene el contador interno >= N

  my $file_userlock = $_[0];
  my $retries = &glib_fildir_02::read_file($file_userlock);
  if ($retries >= $MAX_RETRIES_LOGIN) {
    return 1;
  }
  else {
    return 0;
  };
};
# ---------------------------------------------------------------
sub capture_user {
# Incrementa el contador de intentos fallidos al interior del archivo <user>.txt,
# si no existia lo crea.
  my $file_userlock = $_[0];
  my $retries = &glib_fildir_02::read_file($file_userlock);
  $retries++;
  &glib_fildir_02::write_file($file_userlock, $retries);
};
# ---------------------------------------------------------------
sub release_user {
# Borra archivo <user>.txt
  my $file_userlock = $_[0];
  unlink $file_userlock;
};
# ---------------------------------------------------------------
sub reset_user_lockfile {
# Chequea archivo de bloqueo de User actual y lo elimina
# si es mas antiguos q 1/2 hora, de acuerdo a la fecha de modif. del archivo.

  my $file_userlock = $_[0];

  if (-f $file_userlock) {
    # Obtener estadisticas del arch.
    my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,
          $mtime, $ctime,  $blksize,  $blocks) = stat $file_userlock;

    # Si los seg. de antiguedad de la pagina son mayores que 1800 (30 min)
    if ((time - $mtime) > 1800) {
      unlink $file_userlock;
    };

  };

};
# ---------------------------------------------------------------
#sub show_menu {
#  my $perfil = $_[0];
#  my $buf = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/prontus_menu.html");
#
#  my $custom_area = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/include_custom_menu.html");
#  $buf =~ s/%%_CUSTOM_AREA%%/$custom_area/isg;
#
#  $buf =~ s/%%REL_PATH_PRONTUS%%/$prontus_varglb::RELDIR_BASE\/$prontus_varglb::PRONTUS_ID/isg;
#  $buf =~ s/%%PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg; # por compatibilidad
#  $buf =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
#  $buf =~ s/%%_DIR_CGI_PUBLIC%%/$prontus_varglb::DIR_CGI_PUBLIC/isg;
#
#  $buf =~ s/<!--EDI_ADMIN-->.*<!--\/EDI_ADMIN-->//s if ($prontus_varglb::MULTI_EDICION ne 'SI');
#
#  if (($prontus_varglb::PRONTUS_EDITOR ne 'SI') or ($perfil ne 'A')) {
#    $buf =~ s/<!--PRONTUS_EDITOR-->.*<!--\/PRONTUS_EDITOR-->//s;
#  };
#
#  if (($prontus_varglb::ADMIN_PORT ne 'SI') or ($perfil ne 'A')) {
#    $buf =~ s/<!--ADMIN_PLTPORT-->.*<!--\/ADMIN_PLTPORT-->//s;
#  };
#
#  if ($perfil ne 'A') {
#    $buf =~ s/<!--USR_ADMIN-->.*<!--\/USR_ADMIN-->//s;
#  };
#
#  if (($prontus_varglb::ACTUALIZACION_MASIVA ne 'SI') or ($perfil ne 'A')) {
#    $buf =~ s/<!--PRONTUS_REGEN-->.*<!--\/PRONTUS_REGEN-->//s;
#  };
#
#  if (($prontus_varglb::ADMIN_BASEDATOS ne 'SI') or ($perfil ne 'A')) {
#    $buf =~ s/<!--ADMIN_BASEDATOS-->.*<!--\/ADMIN_BASEDATOS-->//s;
#  };
#
#  if (($prontus_varglb::ADMIN_TAX ne 'SI') or ($perfil ne 'A')) {
#    $buf =~ s/<!--TAXONOMIA-->.*<!--\/TAXONOMIA-->//s;
#  };
#
#
#  if (($prontus_varglb::PRONTUS_LOG ne 'SI') or ($perfil ne 'A')) {
#    $buf =~ s/<!--LOGS-->.*<!--\/LOGS-->//s;
#  };
#
#  if (($prontus_varglb::ADMIN_BUSCADOR ne 'SI') or ($perfil ne 'A')) {
#    $buf =~ s/<!--ADMIN_BUSCADOR-->.*<!--\/ADMIN_BUSCADOR-->//s;
#  }
#  else {
#    # carga lista de plantillas desde el directorio de plantillas del buscador
#    my $dir_tpl_search = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_TEMP . '/extra/search/pags';
#    my $lista_plantillas_search;
#    if (-d $dir_tpl_search) {
#      $lista_plantillas_search = &glib_html_02::generar_popup_from_dir($dir_tpl_search, '_CMB_SEARCHTEMP', '', 1, '', 'CON_EXT', '', '', 1000000, 'STRASC');
#    };
#    $buf =~ s/%%_CMB_SEARCHTEMP%%/$lista_plantillas_search/ig;
#  };
#
#  if (($prontus_varglb::VERIFICAR_INSTALACION ne 'SI') or ($perfil ne 'A')) {
#    $buf =~ s/<!--CHECKINSTALL-->.*<!--\/CHECKINSTALL-->//s;
#  };
#
#  if ($perfil ne 'A') {
#    $buf =~ s/<!--QUOTA-->.*<!--\/QUOTA-->//s;
#  };
#
#
#  if ((! $prontus_varglb::TAXONOMIA_NIVELES ) or ($perfil ne 'A')) {
#    $buf =~ s/<!--TAXONOMIA-->.*<!--\/TAXONOMIA-->//s;
#  };
#
#  if (($perfil ne 'A') and ($perfil ne 'E')) {
#    $buf =~ s/<!--EDI_ADMIN-->.*<!--\/EDI_ADMIN-->//s;
#  };
#
#
#  if ($perfil ne 'A') {
#    while ($buf =~ s/<!--ADMIN-->.+?<!--\/ADMIN-->//sg){};
#    $buf =~ s/<!--ENCAB_FULL-->.+?<!--\/ENCAB_FULL-->//s;
#  }
#  else {
#    $buf =~ s/<!--ENCAB_OPER_ONLY-->.+?<!--\/ENCAB_OPER_ONLY-->//sg
#  };
#
#  $buf =~ s/%%_PRONTUS_VERSION%%/$VERSION_PRONTUS/ig;
#
#  $buf =~ s/%%_PRONTUS_USER_NAME%%/$prontus_varglb::USERS_USR/isg;
#  my $perfil_glosa;
#  $perfil_glosa = 'Redactor' if (lc $perfil eq 'p');
#  $perfil_glosa = 'Editor' if (lc $perfil eq 'e');
#  $perfil_glosa = 'Administrador' if (lc $perfil eq 'a');
#  $buf =~ s/%%_PRONTUS_USER_PERFIL%%/$perfil_glosa/isg;
#
#  if ($prontus_varglb::STAMP_DEMO) {
#    $buf =~ s/<!--\/?STAMP_DEMO-->//sg;
#  } else {
#    $buf =~ s/<!--STAMP_DEMO-->.+?<!--\/STAMP_DEMO-->//sg;
#  };
#
#
#  print "Content-Type: text/html\n\n";
#  print $buf;
#};
# ---------------------------------------------------------------
sub get_changepass {
    my $buf = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/prontus_changepass.html");


    $buf =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
    $buf =~ s/%%_PRONTUS_USER_PASS%%/$FORM{'_psw'}/isg;
    $buf =~ s/%%_PRONTUS_USER_NAME%%/$FORM{'_usr'}/isg;
    $buf =~ s/%%_PATH_CONF%%/$FORM{'_path_conf'}/isg;
    $buf =~ s/%%_PRONTUS_USER_EMAIL%%/$USERS_EMAIL/isg;


    return $buf


};
# ---------------------------------------------------------------
sub user_existente {
my ($key, $val);

  foreach $key (keys %prontus_varglb::USERS) {
    $val = $prontus_varglb::USERS{$key};
    my ($users_nom, $users_usr, $users_psw, $users_perfil, $users_email) = split /\|/, $val;
    if ($users_usr eq $FORM{'_usr'}) {
      return 1;
    };
  };
  return 0;
};
# ---------------------------------------------------------------
sub user_valido {
# retorna:
# 0: user no valido normal
# 1: user valido normal
# -1 : user no valido por existir prontus_flag_sysadmin.txt
# 2: user valido luego de comprobar clave contra prontus_flag_sysadmin.txt

    my ($key, $val);

    # Si esta este archivo, solo deja pasar con user admin y la pass contenida en el.
    # Los demas usuarios son bloqueados.
    my ($flag_sysadmin) = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/prontus_flag_sysadmin.txt";
    if (-f $flag_sysadmin) {
        my $pass_sysadmin = &glib_fildir_02::read_file($flag_sysadmin);
        if (($FORM{'_psw'} eq $pass_sysadmin) && ($FORM{'_usr'} eq 'admin')) {
            $USERS_USR = $FORM{'_usr'};
            # CVI - 05/07/2012 - Ahora se usa md5 para encriptar la contraseña
            $USERS_PSW = md5_hex($pass_sysadmin);
            return 2;
        } else {
            return -1;
        };
    };


    foreach $key (keys %prontus_varglb::USERS) {
        $val = $prontus_varglb::USERS{$key};
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $val;
        # print STDERR "\n\nTIPEADA[$FORM{'_psw'}] USERS_PSW[$USERS_PSW] CRYPT[" . crypt($FORM{'_psw'}, $USERS_PSW) . "]\n" if ($USERS_USR eq $FORM{'_usr'});
        # CVI - 05/07/2012 - Ahora se usa md5 para encriptar la contraseña
        my $crypted_pass;
        if(length($USERS_PSW) == 32) {
            $crypted_pass = md5_hex($FORM{'_psw'});
        } else {
            $crypted_pass = crypt($FORM{'_psw'}, $USERS_PSW);
        }
        if ( ($USERS_USR eq $FORM{'_usr'}) && ($crypted_pass eq $USERS_PSW) ) {
            return 1;
        };
    };


    # si esta presente este archivo, permite entrar con admin/prontus y luego obliga a cambiar la pass
    my ($flag_file) = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/prontus_flag_admin.txt";
    if ( (!(-f $flag_file)) && ($FORM{'_usr'} eq 'admin') && ($FORM{'_psw'} eq 'prontus') ) {
        # Resetear clave admin
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $prontus_varglb::USERS{'1'}; # para rescatar email
        # CVI - 05/07/2012 - Ahora se usa md5 para encriptar la contraseña
        $prontus_varglb::USERS{'1'} = 'Administrador|admin|' . md5_hex('prontus') . '|A|' . $USERS_EMAIL;
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $prontus_varglb::USERS{'1'};

        # USERS
        my $linea = '';
        my $buffer = '';
        my $k;
        foreach $k (keys %prontus_varglb::USERS) {
            my $users_id = $k;
            my ($users_nom, $users_usr, $users_psw, $users_perfil, $users_email) = split /\|/, $prontus_varglb::USERS{$k};
            $linea = $users_id . '|' . $users_nom . '|' . $users_usr . '|' . $users_psw . '|' . $users_perfil . '|' . $users_email . "\n";
            $buffer .= $linea;
        };
        if ($buffer) {
            open (ARCHIVO,">$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/users.txt") || return 0;
            print ARCHIVO $buffer;
            close ARCHIVO;
        };

        &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/prontus_flag_admin.txt", 'No server domain, please try later.');
        return 1;
    };



    return 0;

};

# ---------------------------------------------------------------
sub get_pass_admin {
    my $pass;
    foreach my $key (keys %prontus_varglb::USERS) {
        my $val = $prontus_varglb::USERS{$key};
        my ($users_nom, $users_usr, $users_psw, $users_perfil, $users_email) = split /\|/, $val;
        if  ($users_usr eq 'admin')  {
            return $users_psw;
        };
    };
    return '';

};

# -------------------------------END SCRIPT----------------------

