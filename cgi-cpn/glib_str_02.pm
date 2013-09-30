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
# Manipulacion general de strings
#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 01 : Primera version at 04/feb/2000.
# 01a: Agrega funcion 'trim'. 30/10/2000
# 01b: Agrega funcion 'format_miles'. 02/11/2000
# 01c: Agrega funcion 'devuelve_dv_rut'. 23/11/2000
# 01d: Agrega funcion 'instr'. 23/11/2000

# 02 : Cambio a segunda version, congelada para prontus 5 - 17/04/2001
#
#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package glib_str_02;

#---------------------------------------------------------------
# SUB-RUTINAS.
#-------------
sub format_miles { # 01b
# Retorna un nro. formateado con punto separador de miles.
my ($num) = $_[0];
my ($sal);

  $num =~ s/\D//g;
  $num += 0;

  $sal = '';
  if ($num =~ s/((\d){3})$//) {
    $sal = $1;
  }else{
    $sal = $num;
    $num = '';
  };
  while ($num =~ s/((\d){3})$//) {
    $sal = "$1\.$sal";
  };
  if ($num ne '') {
    $sal = "$num\.$sal";
  };

  return $sal;
};
#---------------------------------------------------------------
sub format_miles_dec { # 01e
  # Recibe numero real y lo formatea con separadores de miles y cant. de decimales deseada.
  my ($valor1, $valor2, $dec) = ($_[0], $_[0], $_[1]);
  my ($signo);

  # print "valor1 s/f:[$valor1]"; # debug

  $signo = '';
  if ($valor1 < 0) {
    $signo = '-';
  };

  $valor1 = $valor2 = abs $valor1;
  # Si el valor hay que devolverlo como entero sin decimales.
  # $valor1 += 1 if ($valor2 - int($valor2) and $dec == 0) >= 0.5;  # 03.2

  # 03.2
  if ($dec == 0) {
    if ($valor1 =~ /\.(\d)/) {
      my $d = $1;
      $valor1 += 1 if ($d >= 5);
    };
  };

  # Si el valor hay que devolverlo como entero con decimales.
  $valor1 += '0.' . '0' x ($dec - 1) . (1 - ($valor2 - int($valor2))) if ($valor2 - int($valor2) and $dec > 0) >= 0.5;
  $valor2 = sprintf("%.${dec}f", $valor2);
  $valor2 =~ s/^\d+\.//g;

  $valor1 =~ s/\..*//g;

  $valor1 = &format_miles($valor1);  # 03.2

  if ($dec > 0) {
    $valor1 .= ',' . $valor2;
  };

  if ($signo eq '-') {
    $valor1 = '-' . $valor1;
  };

  # print "valor1 c/f:[$valor1]<br>"; # debug
  return $valor1;
};
#---------------------------------------------------------------
sub bytes2kb {
  my $bytes = $_[0];
  $bytes = $bytes / 1024;
  $bytes = 1 if ($bytes < 1);
  $bytes = &format_miles_dec($bytes, 0);
  $bytes .= ' kb';
  return $bytes;
};

#-------------------------------------------------------------------------#
sub chars_dir_ok {
# Valida nombres de directorios ingresados por el usuario.

# Param :
# 0) Nombre del directorio (sin path) a validar

# Retornos : 1 si esta ok, 0 en caso contrario

my($nombre) = $_[0];

  if ($nombre =~ /[^a-z0-9_~]/g) {
     return 0;
  }
  else{
    return 1;
  }

};

#-------------------------------------------------------------------------#
sub is_digit {
# Valida que el dato ingresado contenga sólo digitos.

# Param :
# 0) String a validar

# Retornos : 1 si esta ok, 0 en caso contrario

my($valor) = $_[0];

  if ($valor =~ /[^0-9]/g) {
     return 0;
  }
  else{
    return 1;
  }

};

#-----------------------------------------------------------------------#
sub solo_digitos {
# Devuelve solo los digitos de un string.

# Param :
# 0) String de entrada.

# Retorna : string con todos los caracteres que no eran digitos
# eliminados.

  my($texto) = $_[0];
  $texto =~ s/[^0-9]//g;
  return $texto;
};

#------------------------------------------------------------------------------#
sub format_n {
# Retorna valor con un 0 adelante si el largo del string pasado
# es < N, y 00 si el largo es 0.

# Param :
# 0) String de entrada.
# 1) N (nro. de posiciones a las que se desea formatear el nro.)

# Retorna : string formateado.

  my($aux,$auxN) = ($_[0],$_[1]);

  $aux = &solo_digitos($aux);

  $aux = substr($aux,0,$auxN);

  while (length($aux) < $auxN) {
    $aux = "0$aux";
  };
  return $aux;
};

#------------------------------------------------------------------------------#
sub trim { # 01a
  my $valor = $_[0];
  $valor =~ s/^[\s\n\r]*//;
  $valor =~ s/[\s\n\r]*$//;
  return $valor;
};

#------------------------------------------------------------------------------#
sub devuelve_dv_rut { # 01c
  # Funcion que calcula el digito verificador de un rut dado.
  # Parametro:
  # 0) rut sin dv.

  # for($_=$ARGV[0];s/\d$//||($_=(11-$a%11)%10)*0;$a+=$&*(++$r-7?$r:($r=1))+$&){}print$_||"k";   rutina original

  for ($_=$_[0]; s/\d$// || ($_= (11-$a%11)%10)*0; $a+=$&*(++$r-7?$r:($r=1))+$&) {
    # nada.
  }

  return $_ || "K";
};

#------------------------------------------------------------------------------#
sub instr { # 01d
  # Funcion que encuentra el caracter buscado dentro de un string
  # Parametros:
  # 0) String;
  # 1) caracter(es) a buscar.

  if (length($_[0]) > 0) {
    for ($contador = 1; $contador le length($campo_pre); $contador++) {
       last if (substr($campo_pre, $contador, length($_[1])) = $_[1]);
    };
    return $contador;
  }
  else {
    return 0;
  };
};

# --------------------------------------------------------------------------- #
# Retorna un string aleatorio de n letras.
sub random_string {
  my $n = $_[0];
  my $charset = 'ABCDEFGHJKLMNPRTUVWXY23456789abcdeghijkmnoprsuvwxyz';
  my $i;
  my $salida = '';
  for($i=0;$i<$n;$i++) {
    $salida .= substr($charset,int(rand(length $charset)),1);
  };
  # print "$salida\n"; # debug
  return $salida;
}; # random_string
# --------------------------------------------------------------------------- #
sub solo_texto {
    my $str = shift;
    $str =~ s/[^\wáéíóúÁÉÍÓÚüÜñÑ]/ /sg; # solo permite nombres normales
    return $str;
};
# -------------------------------END LIBRERIA--------------------

return 1;
