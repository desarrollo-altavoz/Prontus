# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

#---------------------------------------------------------------
# PROPOSITO.
#-----------
# Implementa rutinas para efectuar bloqueo tipo espera.
# Si hay un bloqueo, espera hasta q se libere.
# Si el proceso q estaba bloqueando se muere, el bloqueo se libera automaticamente.
# uso:

#  use lib_waitlock;
#  # Bloquear
#  $path_file_sem = '/sites/....../filesem.txt';
#  &lib_waitlock::lock_file($path_file_sem);
#
#  # Area critica (ejemplo)
#  my $i = 0;
#  while ($i < 8) {
#    print "$i\n";
#    sleep 1;
#    $i++;
#  };
#  # Fin area critica
#
#  # Desbloquear
#  &lib_waitlock::unlock_file($path_file_sem);


#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#------------------------
# 1.0 - 05/11/2003 - Primera Version.
# 1.1 - 03/02/2004 - Agrega compatibilidad para servers win32.



#---------------------------------------------------------------


#-------------------------------BEGIN LIBRERIA-------------
#---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
#---------------------------
package lib_waitlock;

use strict;
use lib_prontus;

our $MAX_SEGS = 60; # max. duracion del bloqueo, en segs
#---------------------------------------------------------------#
# SUB-RUTINAS.
#---------------------------------------------------------------#

sub lock_file {

  my ($path_semaforo) = $_[0];

  if (&lib_prontus::is_win32()) {

    while (! &chequear_lock($path_semaforo)) {  };
  }
  else {

    my ($lock_sh) = 1;
    my ($lock_ex) = 2;
    my ($lock_nb) = 4;
    my ($lock_un) = 8;
    open SEMWAIT, ">$path_semaforo" or die "No se pudo localizar archivo a bloquear. $!";

    my $ret = flock SEMWAIT, $lock_ex;
    if (!$ret) {
      print STDERR "Error al bloquear[$path_semaforo]";
      exit;
    };

  };

};
#---------------------------------------------------------------#

sub unlock_file {
  my ($path_semaforo) = $_[0];

  if (&lib_prontus::is_win32()) {
    &lock_remove($path_semaforo);
  }
  else {
    my ($lock_sh) = 1;
    my ($lock_ex) = 2;
    my ($lock_nb) = 4;
    my ($lock_un) = 8;
    # Libera bloqueo.
    my $ret = flock SEMWAIT, $lock_un;
    &lock_remove($path_semaforo);
    if (!$ret) {
      print STDERR "Error al desbloquear[$path_semaforo]";
      exit;
    };
  };
};

# ---------------------RUTINAS PARA WIN32------------------------#
# ---------------------------------------------------------------#
sub chequear_lock {
  # USO: # while (! &chequear_lock()) { };
  my ($path_semaforo) = $_[0];
  my $antiguedad_maxima = $MAX_SEGS; # 1 minuto (en segs.)
  # print STDERR "SEM:$prontus_varglb::DIR_SERVER$prontus_varglb::RELDIR_BASE/$prontus_varglb::PRONTUS_ID/art.smf";
  my $ret = &lock_detect($path_semaforo, $antiguedad_maxima);
  if ($ret eq 'RED') {
    # exit;
    return 0;
  };
  return 1;
};
# ---------------------------------------------------------------#
# Detecta existencia de archivo $lock_file. Si existe, aborta, si no, lo crea.
# Si el archivo es mas viejo que $max_time segundos, entonces crea uno nuevo y no aborta.
sub lock_detect {
  my($lock_file) = $_[0]; # Con path completo absoluto.
  my($max_time) = $_[1];

  my(@data) = stat $lock_file;
  my($ret);

  if ((-e $lock_file) && ((time - $data[9]) < $max_time)) {
    # print "[$lock_file] existe. Aborta ejecucion.\n"; # debug
    return 'RED';
    # print "RED\n";
  }else{
    # El archivo existe pero tiene una antiguedad mayor o igual a $max_time
    if ((-e $lock_file) && ((time - $data[9]) >= $max_time)) {
      $ret = 'YELLOW';
      # print "yellow\n";
      # print STDERR "\nADVERTENCIA: SEMAFORO = $ret\n";
    }
    else {
      $ret = 'GREEN';
      # print "green\n";
    };
    open (OUT, ">$lock_file") || die $!;
    # open (OUT, ">$lock_file");
    print OUT 'xxx';
    close OUT;
    return $ret;
  };
}; # lock_detect


# ------------------------------------------------------------------- #
# Borra el archivo $LOCK_FILE para permitir la ejecucion de otras
# instancias.
sub lock_remove {
  my($lock_file) = $_[0];

  unlink $lock_file;
  # print STDERR "*** LOCK RM[$lock_file] ***\n"; # debug
}; # lock_remove


return 1;
#-----------------------END LIBRERIA-----------------------------#
