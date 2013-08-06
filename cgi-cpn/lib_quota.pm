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


#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#------------------------


#---------------------------------------------------------------


#-------------------------------BEGIN LIBRERIA-------------
#---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
#---------------------------
package lib_quota;

use strict;

use glib_fildir_02;
use prontus_varglb;

#---------------------------------------------------------------#
# SUB-RUTINAS.
#---------------------------------------------------------------#
sub calcula_unix {
  my $bgbar = '';
  my $usado = '';
  my $quota_asig = '';

  # Si existe el script de cálculo y no tiene .. entremedio
  if($prontus_varglb::SCRIPT_QUOTA && $prontus_varglb::SCRIPT_QUOTA !~ /\.\./ && $prontus_varglb::SCRIPT_QUOTA !~ / /) {
    my $rutascript = "$prontus_varglb::DIR_SERVER$prontus_varglb::SCRIPT_QUOTA";
    if(-f $rutascript) {
      if($rutascript =~ /\.php$/) {
        $rutascript = 'php ' . $rutascript;
      };
      # Si el script funciona, lo ejecuta enviando el nombre del prontus y el DIR_SERVER
      my $res = `$rutascript $prontus_varglb::PRONTUS_ID $prontus_varglb::DIR_SERVER`;
      if($res && $res =~ /(\d+)\|(\d+)/) {
        ($usado, $quota_asig) = ($1, $2);
      } else {
        print STDERR "Script Quota no valido: [$res]\n";
      }
    };
  };

  # Valida que los campos no sean vacios.
  unless (($usado) && ($quota_asig)) {
    ($usado, $quota_asig) = &procesa_command_quota('/usr/bin/quota -v 2>/dev/null'); # descarta EL STDERR
  }

  # Valida que los campos no sean vacios.
  unless (($usado) && ($quota_asig)) {
    ($usado, $quota_asig) = &procesa_command_quota('/usr/bin/quota -g 2>/dev/null');
  };

  unless (($usado) && ($quota_asig)) {
    ($usado, $quota_asig) = &procesa_quota_vps();
  };

  unless(($usado) && ($quota_asig)) {
    return '<b>Espacio en disco:</b> Informaci&oacute;n no disponible.';
  };

  # 1.2 - CVI - Por que no puede ser mayor de 8 ???? Lo saco para que funcione
  # Valida que la quota asignada no tenga mas de 99999999Kb.
  #      if(length($quota_asig) > 8){
  #        $quota_asig = substr($quota_asig,0,8);
  #      };

  # Caso de cuota sobrepasada.
  if ($usado > $quota_asig ) {
    return '<b>Espacio en disco:</b> Cuota sobrepasada.';
  };

  # Conversion a Megas de espacio usado.
  # my $usado_mb = &conver_mb($usado);
  # Conversion a Megas de espacio asignado.
  # my $quota_asig_mb = &conver_mb($quota_asig);
  # Calcula porcentaje del espacio usado.
  my $usado_porc = ($usado * 100) / $quota_asig;
  # Quita los decimales.
  # $usado_porc  =~ s/\..*$//s; # 1.3
  $usado_porc = sprintf("%.0f", $usado_porc); # 1.3
  # Calcula porcentaje del espacio disponible.
  my $nousado_porc = 100 - $usado_porc;
  $usado_porc .= '%';
  $nousado_porc .= '%';
  return ('', $usado, $quota_asig, $usado_porc, $nousado_porc);

}; # calcula_unix

# ------------------------------------------------------------------------------------- #
sub procesa_command_quota {

  my $command = shift;
  my $largo; # 1.1
  my ($usado, $quota_asig);

  my @quota_out = `$command`;

  # Disk quotas for user lan000 (uid 2800):  Para Altavoz
  #      Filesystem   usage   quota   limit   grace   files   quota   limit   grace
  #          /sites13834022 2560000025600000          765811       0       0
  # Disk quotas for group group2550 (gid 2550):  Para T1
  #      Filesystem  blocks   quota   limit   grace   files   quota   limit   grace
  #          /dev/sda4  441356  512000  512000            3534       0       0
  if ($#quota_out >= 2){
    # 1.1 if ($quota_out[2] =~ /^\s*.+?\s+(\d+)\s+(\d+)\s+\d+\s+/) {
    # 1.4 - Para manejar el T1 que usa sda4
    if ($quota_out[2] =~ /(\d{2,})\s+(\d{2,})/) { # 1.1 Toma solo los dos primeros numeros.
      $usado = $1;
      $quota_asig = $2;
      # 1.1 Si la cuota asignada es muy grande (o sea, los numeros se pegaron), la parte en dos y toma el primer numero.
      $largo = length($quota_asig);
      if ( $largo > 10 ) {
        $quota_asig = substr($quota_asig,0,int($largo/2));
      };
    };
  };
  # return (441856, 512000);
  return ($usado, $quota_asig);
};

# ------------------------------------------------------------------------------------- #
sub procesa_quota_vps {

    my ($usado, $quota_asig, $disponible);
    my ($usado_raiz, $disponible_raiz);

    my $df = `df -T | grep -v tmpfs`;

    return ('','') if (!$df);

    my @lineas_df = split(/\n/, $df); shift @lineas_df; # quitar cabecera.
    my $document_root = $prontus_varglb::DIR_SERVER;

    return ('', '') if (scalar @lineas_df == 0);

    while ($document_root =~ /^.+(\/.*?)$/sg) {
        my $part = $1;
        $document_root =~ s/$part//sg;

        # Tratar de buscar el punto de montaje en base al document root.
        # por ejemplo comienza con:
        # /var/www/sitios/xxxx
        # /var/www/sitios
        # /var/www
        # /var
        # /
        # hasta dar con alguno...
        foreach my $linea (@lineas_df) {
            if ($linea =~ /(\d+)\s+(\d+)\s+(\d+)%\s+(\/.*)/) {
                $usado = $1;
                $disponible = $2;
                my $montaje = $4;

                # Los guardamos, en caso de que no haya match!, usar por defecto la particion raiz.
                if ($montaje eq '/') {
                    $usado_raiz = $usado;
                    $disponible_raiz = $disponible;
                };

                #~ print STDERR "montaje[$montaje] document_root[$document_root]\n";
                if ($montaje eq $document_root) {
                    print STDERR "match! document_root[$document_root] = montaje[$montaje]\n";
                    $quota_asig = $usado + $disponible;
                    last;
                };
            };
        };

        last if ($quota_asig);
    };

    if (!$quota_asig) {
        print STDERR "Usando valores de la partición raiz\n";
        $usado = $usado_raiz;
        $quota_asig = $usado_raiz + $disponible_raiz;
    };

    return ($usado, $quota_asig);
};

# ------------------------------------------------------------------------------------- #
sub conver_mb {
  # Recibe cantidad espacio de disco en Kb.
  # Devuelve cantidad espacio de disco en Mb con dos decimales.
  my $espacio = shift;
  # Conversion a Megas.
  my $espacio_mb = $espacio / 1024;
  # Verifica si tiene decimales, si tiene mas que dos elimina el resto.
  if ($espacio_mb =~ /^(\d+)\.(\d+)$/) {
    my $entero = $1;
    my $decimales = $2;
    if (length($decimales) > 2){
      $decimales = substr ($decimales, 0, 2);
      $espacio_mb =  $entero.'.'.$decimales;
    };
  };
  return $espacio_mb;
}; # conver_mb


# ------------------------------------------------------------------------------------- #
sub format_bytes {

  my $espacio = shift;
  # Conversion a Megas.
  my $espacio_final = $espacio / 1024;
  my $unidad = ' MB';
  if($espacio_final >= 1000) {
    $espacio_final = $espacio_final / 1024;
    $unidad = ' GB';
    if($espacio_final >= 1000) {
      $espacio_final = $espacio_final / 1024;
      $unidad = ' TB';
    }
  }
  $espacio_final = &format_number($espacio_final);
  if($espacio_final) {
    return $espacio_final . $unidad;
  } else {
    return '0 B';
  };
};

# ------------------------------------------------------------------------------------- #
sub format_number {

  my $number = shift;
  $number =~ s/[^\d\.\,]//g; # se limpia el numero

  # Verifica si tiene decimales, si tiene mas que dos elimina el resto.
  if ($number =~ /^(\d+)\.(\d+)$/) {
    my $entero = $1;
    my $decimales = $2;
    if (length($decimales) > 1){
      $decimales = substr($decimales, 0, 1);
      if($decimales) {
        $number =  $entero.','.$decimales;
      } else {
        $number =  $entero;
      };
    };
  };
  return $number;
};

# ------------------------------------------------------------------------------------- #
sub check_quota_suficiente {
# Revisa si hay cuota suficiente para publicar, siempre que esta se pueda calcular

    my $cuota_limit = 98; # en %
    my ($msg, $usado_mb, $quota_asig_mb, $usado_porc, $nousado_porc) = &lib_quota::calcula_unix();
    # my ($msg, $usado_mb, $quota_asig_mb, $usado_porc, $nousado_porc) = ('', 111, 222, '98%', '60%');# debug
    if ($msg eq '') { # cuota se pudo calcular
        $usado_porc =~ s/\%$//;
        if ($usado_porc >= $cuota_limit) {
            return "No es posible completar la operación porque no hay espacio suficiente en el disco.<br />Espacio utilizado: $usado_porc" . '%' . " ($usado_mb MB)";
        };
    };
    return '';
};


#--------------------------------------------------------------------#
return 1;
#-------------------------------END LIBRERIA---------------------
