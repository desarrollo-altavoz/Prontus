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
# PROPOSITO.
#-----------
# Funciones para bloqueo de IPs

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 1.0 - ycc - 12/2006 - Primera version.
#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package lib_ipcheck;

use strict;
use glib_fildir_02;
#----------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub check_bloqueo_ip {
  # $dir_ip_control: full dir donde se almacenan los archivos de control
  # $user_ip: usualmente $ENV{'REMOTE_ADDR'}
  # maxrequest_por_ip: nro. max de requests permitidos en un minuto desde la misma IP
  # bloqueoip_interval: Segundos durante los cuales permanecerá una IP bloqueada

  # Ejemplo de uso: Al comienzo del script poner algo como esto:

  #   my $dir_ip_control = "$coment_varglb::DIR_SERVER/coment/cpan/ip_control";
  #   my $user_ip = $ENV{'REMOTE_ADDR'};
  #   my $maxrequest_por_ip = 30; # valor tipico
  #   my $bloqueoip_interval = 60; # valor tipico
  #   my $bloquear_ip = &lib_ipcheck::check_bloqueo_ip($dir_ip_control, $user_ip, $maxrequest_por_ip, $bloqueoip_interval);
  #   if ($bloquear_ip) {
  #     print "0|Request inhabilitado";
  #     exit;
  #   };


  my ($dir_ip_control, $user_ip, $maxrequest_por_ip, $bloqueoip_interval) = @_;

  if ((!-d $dir_ip_control) || (!$user_ip) || ($maxrequest_por_ip <= 0) ||  ($bloqueoip_interval <= 0)) {
    die "\n\nerror en parametros de invocacion a &lib_ipcheck::check_bloqueo_ip()\n\n";
  };

  my $file_locked_ip = "$dir_ip_control/ip_bloq_$user_ip.txt";
  my $file_request_counter = "$dir_ip_control/$user_ip.txt";

  # Chequea todos los archivos de IPs y elimina los que sean mas antiguos q 1 minuto, de acuerdo a la fecha de modif. del archivo.
  &reset_ip_files($dir_ip_control);

  # analogo pero solo con las bloqueadas.
  &reset_ip_bloqueadas($dir_ip_control, $bloqueoip_interval);

  # Si la IP esta dentro de las bloqueadas o hay que bloquearla, aborta ejecucion.
  if (&bloquear_ip($file_locked_ip, $file_request_counter, $maxrequest_por_ip)) {
    return 1;
  };

  # Incrementa el contador de requests al interior del archivo <ip>.txt, si no existia lo crea.
  &capture_ip($file_request_counter);
  return 0; # no bloqueada

};
# ---------------------------------------------------------------
sub bloquear_ip {
# Detecta si hay que bloquear la IP o si ya esta bloqueada
# Se sabe porque el archivo <ip>.txt tiene el contador interno >= MAXREQUEST_POR_IP (cfg).
  my ($file_locked_ip, $file_request_counter, $maxrequest_por_ip) = @_;
  if (-f $file_locked_ip) {
    return 1; # ip bloqueada
  };

  my $retries = &glib_fildir_02::read_file($file_request_counter);
  if ($retries >= $maxrequest_por_ip) {
    # agregarla a lista de ips bloqueadas
    &anotar_ip_bloqueada($file_locked_ip);
    return 1; # ip bloq.
  }
  else {
    return 0;
  };
};
# ---------------------------------------------------------------
sub capture_ip {
# Incrementa el contador de intentos fallidos al interior del archivo <ip>.txt,
# si no existia lo crea.
  my ($file_request_counter) = $_[0];
  my $retries = &glib_fildir_02::read_file($file_request_counter);
  # print STDERR "ret1[$retries]\n";
  $retries++;
  # print STDERR "ret2[$retries]\n";
  &glib_fildir_02::write_file($file_request_counter, $retries);
};
# ---------------------------------------------------------------
sub anotar_ip_bloqueada {
  my $file_locked_ip = $_[0];
  &glib_fildir_02::write_file($file_locked_ip, '1');
};

# ---------------------------------------------------------------
sub reset_ip_files {
# Chequea todos los archivos de IPs y elimina los que sean mas antiguos q 1 minuto,
# de acuerdo a la fecha de modif. del archivo.

  my $dir_ip_control = $_[0];

  my ($ret, @entries, $entry);

  @entries = &glib_fildir_02::lee_dir($dir_ip_control);
  foreach $entry (@entries) {
    if (($entry !~ /^\./g) && (-f "$dir_ip_control/$entry") && ($entry =~ /^\d+\.\d+\.\d+\.\d+\.txt$/)) {
      # Obtener estadisticas del arch.
      my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,
            $mtime, $ctime,  $blksize,  $blocks) = stat "$dir_ip_control/$entry";

      # Si los seg. de antiguedad de la pagina son mayores que 60
      if ((time - $mtime) > 60) {
        unlink "$dir_ip_control/$entry";
      };

    };
  };

};
# ---------------------------------------------------------------
sub reset_ip_bloqueadas {
# Chequea todos los archivos de IPs bloqueadas y elimina los que sean mas antiguos q BLOQUEOIP_INTERVAL seg,
# de acuerdo a la fecha de modif. del archivo.

  my $dir_ip_control = $_[0];
  my $bloqueoip_interval = $_[1];

  my ($ret, @entries, $entry);

  @entries = &glib_fildir_02::lee_dir($dir_ip_control);
  foreach $entry (@entries) {
    if (($entry !~ /^\./g) && (-f "$dir_ip_control/$entry") && ($entry =~ /^ip_bloq_\d+\.\d+\.\d+\.\d+\.txt$/)) {
      # Obtener estadisticas del arch.
      my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,
            $mtime, $ctime,  $blksize,  $blocks) = stat "$dir_ip_control/$entry";

      # Si los seg. de antiguedad de la pagina son mayores que xx
      if ((time - $mtime) > $bloqueoip_interval) {
        unlink "$dir_ip_control/$entry";
        my $ip = $entry;
        $ip =~ s/^ip_bloq_//;
        unlink "$dir_ip_control/$ip";
      };

    };
  };

};

# ---------------------------------------------------------------
return 1;

# -------------------------------END LIBRERIA--------------------
