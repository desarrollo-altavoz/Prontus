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
# Manipulación de fecha y hora.

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 01 : Primera version at 04/feb/2000.
# 01a: Se remueve rutina 'is_date' removiendose con ella la
# sentencia 'use HTTP::Date;'. Ademas, se incorpora rutina 'get_date_time'.

# 02 : Cambio a segunda version, congelada para prontus 5 - 17/04/2001
# 02.1 : Descomenta POSIX - 08/01/2003 para uso en p9.0
# 02.2 : Cambia meses a minúsculas - 13/01/2003 para uso en p9.0

#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package glib_hrfec_02;

use POSIX; # paquete que viene con Perl (manejo de fechas)

use glib_str_02;

#---------------------------------------------------------------
# SUB-RUTINAS.
#-------------
# 01a:
sub get_date_time {
# Retorna la fecha y hora correspondientes a un nro. de segundos
# transcurridos desde el epoch.

# Ejemplo de llamada :
# $con_dia_sem = '';
# $con_mes = '1';
# $con_dia_mes = '1';
# $con_anno = '1';
# $con_hora = '1';
# $con_zona = '';
# $seg_from_epoch = time; # Fecha y hora actual.
# print "\n" . &glib_hrfec_02::get_date_time($con_dia_sem,$con_mes , $con_dia_mes, $con_anno, $con_hora, $con_zona, $seg_from_epoch) . "\n\n";


  my $Display_Week_Day = $_[0];

  my $Display_Month = $_[1];

  my $Display_Month_Day = $_[2];

  my $Display_Year = $_[3];

  my $Display_Time = $_[4];

  my $Display_Time_Zone = $_[5];

  my $sec_from_epoch = $_[6];

  my $Standard_Time_Zone = 'EST';
  my $Daylight_Time_Zone = 'EDT';


  my $fec_hr;

  # Done                                                                       #
  ##############################################################################

  my @Week_Days = ('Domingo','Lunes','Martes','Miercoles',
                'Jueves','Viernes','Sabado');

  my @Months = ('enero','febrero','marzo','abril','mayo','junio','julio',
             'agosto','septiembre','octubre','noviembre','diciembre');


  ($Second,$Minute,$Hour,$Month_Day,
  $Month,$Year,$Week_Day,$IsDST) = (localtime($sec_from_epoch))[0,1,2,3,4,5,6,8];

  if ($IsDST == 1) {
      $Time_Zone = $Daylight_Time_Zone;
  }
  else {
      $Time_Zone = $Standard_Time_Zone;
  }

  if ($Second < 10) {
      $Second = "0$Second";
  }
  if ($Minute < 10) {
      $Minute = "0$Minute";
  }
  if ($Hour < 10) {
      $Hour = "0$Hour";
  }
  if ($Month_Day < 10) {
      $Month_Day = "0$Month_Day";
  }
  $Year += 1900;

  if ($Display_Week_Day != 0) {
      $fec_hr = $Week_Days[$Week_Day];

      if ($Display_Month != 0) {
          $fec_hr .= ", ";
      }
  }

  if ($Display_Month != 0) {
      $fec_hr .= $Months[$Month] . ' ';
  }

  if ($Display_Month_Day != 0) {
      $fec_hr .= $Month_Day;
      if ($Display_Year != 0) {
          $fec_hr .= ", ";
      }
  }

  if ($Display_Year != 0) {
      $fec_hr .= $Year;
      if ($Display_Time != 0) {
          $fec_hr .= " - ";
      }
      elsif ($Display_Time_Zone != 0) {
          $fec_hr .= " ";
      }
  }

  if ($Display_Time != 0) {
      $fec_hr .= "$Hour\:$Minute\:$Second";
      if ($Display_Time_Zone != 0) {
          $fec_hr .= " ";
      }
  }

  if ($Display_Time_Zone != 0) {
      $fec_hr .= $Time_Zone;
  }

  return $fec_hr;

}

#-------------------------------------------------------------------------#
#------------------------------------------------------------------------------#
sub format_year {
# Formatea un ano a 4 digitos, tomando en cuenta el problema del ano 2000.

# Param :
# 0) String correspondiente al ano (ej. : 80, 90, 100, 00) hasta de 4 digitos.

# Retorna : ano formateado a 4 digitos

  my($aux) = $_[0];

  $aux = &glib_str_02::solo_digitos($aux);

  $aux = substr($aux,0,4); # Toma primeros 4 digitos.
  if ($aux eq '') { $aux = 0; };

  if (($aux >= 100) && ($aux < 1000)){ return 1900 + $aux; };
  if (($aux > 50) && ($aux < 100)){ return "19$aux"; };
  if (($aux <= 50) && ($aux > 9)){ return "20$aux"; };
  if ($aux < 10) { return "200$aux"; };

  return $aux;
};

#--------------------------------------------------------------------#
sub get_dtime_pack4 {
# Entrega la fechahora actual compactada, con ano de 4 digitos.

# Param : No utiliza parametros, toma la fecha y hora del sistema.

# Retorna : "$year$mon$mday$hour$min$sec"


  my($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime(time);
  $mon++;
  $mon = &glib_str_02::format_n($mon,2);
  $mday = &glib_str_02::format_n($mday,2);
  $hour = &glib_str_02::format_n($hour,2);
  $min = &glib_str_02::format_n($min,2);
  $sec = &glib_str_02::format_n($sec,2);
  $year = &format_year($year);
  return "$year$mon$mday$hour$min$sec";
};

#--------------------------------------------------------------------#
sub get_date_pack4 {
# Entrega la fecha actual compactada, con ano de 4 digitos.

# Param : No utiliza parametros, toma la fecha y hora del sistema.

# Retorna : "$year$mon$mday"

  my($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime(time);
  $mon++;
 $mon = &glib_str_02::format_n($mon,2);
  $mday = &glib_str_02::format_n($mday,2);
  $year = &format_year($year);
  return "$year$mon$mday";
};

#--------------------------------------------------------------------#
sub normaliza_fecha {
# Toma una fecha escrita como dia/mes/ano, la normaliza y la entrega
# compactada en formato ISO.

# Param : string con la fecha a normalizar.

# Retorna : "$ano$mes$dia"
  return '' if (!$_[0]);
  my($dia,$mes,$ano) = split (/\//,$_[0]);
  $ano = &format_year($ano);
  $mes = &glib_str_02::format_n($mes,2);
  $dia = &glib_str_02::format_n($dia,2);
  return "$ano$mes$dia";

};

#--------------------------------------------------------------------#
sub des_normaliza_fecha {
# Toma una fecha en formato ISO y la escribe como dia/mes/ano.

# Param : string con la fecha a des-normalizar.

# Retorna : "$dia/$mes/$ano"
  return '' if (!$_[0]);
  my($fecha) = $_[0];
  if($fecha =~ /^(\d\d\d\d)(\d\d)(\d\d)/g) {
    my($dia,$mes,$ano) = ($3,$2,$1);
    return "$dia/$mes/$ano";
  } else {
    return '';
  }

};

#--------------------------------------------------------------------#
 sub expande_fecha {
 # Toma una fecha en formato ISO y la escribe como "Lunes 10 de Mayo de 2000"

 # Param : string con la fecha ISO.

 # Retorna : string con la fecha convertida.

   my($fecha) = $_[0];
   my(@dias) = ('Domingo','Lunes','Martes','Mi&eacute;rcoles','Jueves','Viernes','S&aacute;bado');
   my(@meses) = ('enero','febrero','marzo','abril','mayo','junio','julio',
                    'agosto','septiembre','octubre','noviembre','diciembre');
   $fecha =~ /(\d\d\d\d)(\d\d)(\d\d)/g;
   my($dia,$mes,$ano) = ($3,$2,$1);
   my($tiempo) = &POSIX::mktime(0,0,12,$dia,($mes - 1),($ano - 1900));
   my($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($tiempo);
   $dia = $dia + 0; # Para extraer los ceros de adelante.
   return $dias[$wday] . " $dia de " . $meses[($mes - 1)] . " de $ano";

 };
# ---------------------------------------------------------------
sub suma_segs {
  # Suma x seg a un TS
  my ($ts, $inc_seg) = @_;
  $ts =~ /(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)/g;
  my($ano,$mes,$dia,$hh,$mm,$ss) = ($1,$2,$3,$4,$5,$6);
  # mktime(sec, min, hour, mday, mon, year, wday = 0, yday = 0, isdst = 0)
  my($tiempo) = &POSIX::mktime($ss,$mm,$hh,$dia,($mes - 1),($ano - 1900));
  $tiempo += $inc_seg;
  my $ts_inc = &time2ts($tiempo);
  return $ts_inc;

};
# --------------------------------------------------------------------
sub time2ts {
# Convierte de TIME a TS.

# Param : segs from epoch

# Retorna : "$year$mon$mday$hour$min$sec"

  my $tiempo = $_[0];
  my($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime($tiempo);
  $mon++;
  $mon = &glib_str_02::format_n($mon,2);
  $mday = &glib_str_02::format_n($mday,2);
  $hour = &glib_str_02::format_n($hour,2);
  $min = &glib_str_02::format_n($min,2);
  $sec = &glib_str_02::format_n($sec,2);
  $year = &glib_hrfec_02::format_year($year);
  return "$year$mon$mday$hour$min$sec";
};


# -------------------------------------------------------------- #
# Retorna la fecha actual en formato dd/mm/aaaa.
sub fecha_human {
    # (0: $sec, 1: $min, 2: $hour, 3: $mday, 4: $mon, 5: $year, 6: $wday, 7: $yday, 8: $isdst)
    my(@fecha) = localtime(time);
    my($ano,$mes,$dia) = ($fecha[5],$fecha[4],$fecha[3]);
    if ($ano < 2000) { 
        $ano += 1900; 
    };
    $mes = sprintf('%02d',($mes + 1));
    $dia = sprintf('%02d',$dia);
    return "$dia/$mes/$ano";
}; # fecha_corta

# -------------------------------------------------------------- #
# Retorna la hora actual en formato hh:mm:ss.
sub hora_human {
    # (0: $sec, 1: $min, 2: $hour, 3: $mday, 4: $mon, 5: $year, 6: $wday, 7: $yday, 8: $isdst)
    my(@fecha) = localtime(time);
    my($hr,$min,$sec) = ($fecha[2],$fecha[1],$fecha[0]);
    $hr = sprintf('%02d',$hr);
    $min = sprintf('%02d',$min);
    $sec = sprintf('%02d',$sec);
    return "$hr\:$min\:$sec";
}; # hora

# Convierte un ts en epoch.
sub get_epoch_from_ts {
    my $ts = $_[0]; #aaaammdd

    #Obtener año, mes, dia, hora min y sec para epoch
    $ts =~ /(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/is;
    my($year, $mon, $mday, $hour, $min, $sec) = ($1, $2, $3, $4, $5, $6);

    my $time = mktime($sec, $min, $hour, $mday, $mon - 1, $year - 1900);

    return $time;
};

# Retorna la antiguedad en segundos del ts.
sub get_antiguedad_ts {
  my $ts = $_[0];
  my $epoch = &get_epoch_from_ts($ts);
  my $diff = time - $epoch;

  return $diff;
};

#--------------------------------------------------------------------#
# sub compo_fecha {
# # Toma una fecha en formato ISO (aaaammdd) devuelve el ano, mes, dia y dia de
# # la semana en un arreglo (lunes=0, domingo=6);
#
# # Param : string con la fecha ISO aaaammdd.
#
# # Retorna : array con la info obtenida.
#
#   my($fecha) = $_[0];
#   my(@dias) = (6,0,1,2,3,4,5);
#   my(@salida);
#
#   $fecha =~ /(\d\d\d\d)(\d\d)(\d\d)/g;
#   my($dia,$mes,$ano) = ($3,$2,$1);
#   my($tiempo) = &POSIX::mktime(0,0,12,$dia,($mes - 1),($ano - 1900));
#   my($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($tiempo);
#   $year += 1900;
#   $mon += 1;
#   @salida = ($year,$mon,$mday,$dias[$wday]);
#   return @salida;
#
# };

#-------------------------------END LIBRERIA--------------------

return 1;
