#!/usr/bin/perl
#-------------------------------COMENTARIO GLOBAL---------------
#---------------------------------------------------------------
# PROPOSITO.
#-----------
# Implementa rutinas bloquear archivos
# uso:

#  # Detecta semaforo.
#  my ($semaforo_file) = "$DIR_SERVER/control_files/semaforo_sender_$CLTE_ID";
#  my ($lock_obj) = &lib_lock::lock_file($semaforo_file);
#  if (!ref $lock_obj) { # si ya tiene un bloqueo anterior, aborta.
#    exit;
#  };
#  .....
#
#  # Libera lock
#  &lib_lock::unlock_file($lock_obj, $semaforo_file);

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#------------------------
# 1.0 - YCH - Primera Version.



#---------------------------------------------------------------


#-------------------------------BEGIN LIBRERIA-------------
#---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
#---------------------------
package lib_lock;

use strict;



#---------------------------------------------------------------#
# SUB-RUTINAS.
#---------------------------------------------------------------#
sub lock_file {
# Intenta bloquear el archivo pasado x param.
# Si lo logra, retorna la ref. al objeto lock.
# Si falla dado q ya esta tomado el archivo, retorna undef.
# No es necesario q el archivo exista, sin embargo su dir de ubicacion debe ser valido.
# Si despues del bloqueo el script se cae entre medio, el lock se libera automaticamente la prox. vez que se le bloquee.
  my ($file2lock) = $_[0];
  my $no_hay_lfsimple;
  eval "require LockFile::Simple;";    $no_hay_lfsimple = $@;

  if ($no_hay_lfsimple) {
    print STDERR "BLOQUEO MANUAL\n";
    if (-f $file2lock) {
      # Si el semaforo es menos antiguo que 8 horas, aborta la ejecucion.
      # (0: $dev, 1: $ino, 2: $mode, 3: $nlink, 4: $uid, 5: $gid, 6: $rdev, 7: $size, 8: $atime, 9: $mtime, 10: $ctime, 11: $blksize, 12: $blocks).
      if ((stat($file2lock))[9] > (time - 28800)) {
        print STDERR "BLOQUEADO\n";
        return undef;
      };
    };
    unlink $file2lock;
    open SEMAFORO, ">$file2lock";
    print SEMAFORO time;
    close SEMAFORO;
    print STDERR "RET 1\n";
    return \1;

  }
  else {

    require LockFile::Simple;
    my ($lockmgr) = LockFile::Simple->make(-format => '%f.lck',
  	-max => 20, -delay => 1, -nfs => 1, -autoclean => 1, -stale => 1, hold => 28800); # 1.1 - 8 horas como max dura el bloqueo (es en segs)
    my ($lock_obj) = $lockmgr->trylock($file2lock);
    return $lock_obj;

  };
};
# ---------------------------------------------------------------
sub unlock_file {
# Libera el lock sobre el archivo apuntado por el obj pasado x param.
  my ($lock_obj) = $_[0];
  my ($lock_file) = $_[1];

  my $no_hay_lfsimple;
  eval "require LockFile::Simple;";    $no_hay_lfsimple = $@;

  if ($no_hay_lfsimple) {
    unlink $lock_file;
  }
  else {
    require LockFile::Simple;
    $lock_obj->release if ref $lock_obj;
  };

};
#--------------------------------------------------------------------#
return 1;
#-------------------------------END LIBRERIA---------------------
