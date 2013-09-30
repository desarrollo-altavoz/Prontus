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
# Implementa rutinas para manejar el envio de data entre el browser  y el server. Emula a la
# libreria standard de Perl CGI.pm
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ------------------------
# 01   - 02/12/2000 - Primera Version.
# 1.1  - 28/12/2000 - Ajustes a raiz de problema de publicacion de textos grandes.
# 1.2  - 03/01/2001 - Agrega funciones para leer y setear cookies simples.
# 1.3  - 08/03/2001 - Correcciones 1.2
# 1.4  - 16/03/2001 - Correccion para que aparte de las fotos tambien se puedan subir realmedia, tablas y asocfile.
# En la version del prontus previa al P5 esta modif. esta como # 1.2
# 1.5  - 15/05/2001 - Des-webifea tambien los nombres en la rutina new
# 1.6  - 15/05/2001 - Se corrige bug de IE 5.0 que duplica algunos campos cuando viajan caracteres raros (en la rutina new)
# 1.7  - 15/05/2001 - Ajustes para enviar controles multi-listas con formularios normales. CAMBIO A VERSION 02.
# 1.8  - 16/05/2001 - Se permiten nombres de campos no tipo file que comienzen con FILE, etc.
# 1.9  - 01/06/2001 - Los nombres de campos FOTO|REALMEDIA|FILE|ASOCFILE|TABLA estan reservados para controles tipo file
# 1.10 - 27/08/2001 - Cambio a set_simple_cookie para que setee la cookie con path = /

# 3.0 - 15/04/2003 - Cambio a version 03, con lectura buffereada de archivos.
# 3.1 - 05/05/2003 - Mejoras del código implementado en version 03.
# 4.0 - 25/04/2005 - ALD - Cambios revolucionarios para mayor eficiencia:
#                  - Ya no se usa la funcion append_file, ya que abre y cierra el archivo a cada rato.
#                  - Se antepone el numero de proceso (variable $$) al nombre de los archivos
#                    temporales para evitar sobreescribir los de otra instancia.
#                  - Se modifica la funcion get_file_name para eso mismo y para mejor eficiencia
#                    (el grep a un arreglo es muy lento).
#                  - Se dota al garbage collector de una resolucion de segundos, debido a la gran
#                    cantidad de archivos que se pueden subir en FullColor.
#                  - Se reescribe algoritmo de lectura del STDIN para solucionar bug que hacia
#                    crecer el uso de la RAM en forma descontrolada.
#                  - Se comprueba que $BUFFER_SIZE = 100000 es un buen valor.
# 4.1 - 26/04/2005 - ALD - Arreglos de bugs y robustecimiento general.
# 4.2 - 27/04/2005 - ALD - Optimizacion de get_file_name.
# 4.3 - 29/04/2005 - ALD - Soluciona bugs.
# 4.4 - 20/05/2005 - ALD - Lee exacto el STDIN para evitar caidas en Windows.
# 4.5 - 01/06/2005 - ALD - Soluciona bug que abortaba el loop de lectura si justo se leia hasta el limite de un encabezado.
# 4.6 - 15/02/2006 - YCH - Agrega binmode que faltaba, a raiz de lo cual la lib no funcionaba en windows.
# 4.7 - 19/04/2006 - YCH - Cambia \ por / para que funcione con los servidores windows que registran SCRIPT_FILENAME.
# 4.8 - 25/05/2006 - YCH - Cuando en un ctrl tipo file no hay nada, se confunde pq en realidad viene un "" (dos comillas juntas)
# 4.9 - 06/11/2006 - YCH - Elimina %00


# ---------------------------------------------------------------

# -------------------------------BEGIN LIBRERIA-------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
package glib_cgi_04;

use strict;
use lib_cookies;

# ---------------------------------------------------------------#
# SUB-RUTINAS.
# ---------------------------------------------------------------#

my %FORM = ();
my %REALPATH = ();
my %MULTIVALUES = ();
my $BUFFER_SIZE = 100000; # Usar minimo 512 bytes, de otra forma no funciona.

my $script_path = $ENV{'SCRIPT_FILENAME'};
$script_path =~ s/\\/\//g; # 4.7
my $ridx = rindex($script_path,'/');
if ($ridx < 0) {
  # $ridx = rindex($0,"\\"); # Esto es para la version Windows.
  $script_path = $ENV{'PATH_TRANSLATED'};        # PATH_TRANSLATED = C:\Inetpub\wwwroot
  $script_path =~ s/\\/\//g;
  $script_path =~ s/\/cgi\-.*//g;
  $script_path .= $ENV{'SCRIPT_NAME'};
  $ridx = rindex($script_path,'/');
};
my $CGI_DIR = substr($script_path, 0, $ridx);
my $TEMP_DIR = "$CGI_DIR/prontus_temp";
my $CURRENTFILEIDX = 0; # 4.2

# --------------------------------------------------------------------#
sub param {
# Retorna el valor del objeto de formulario pasado por parametro. ej : $FORM{'campo1'} = &glib_cgi_02::param('campo1');
# Si vienen varios valores para el campo especificado, se retorna un array con estos valores. ej : @valores_campo1 = &glib_cgi_02::param('campo1');
# Si se llama sin parametros, devuelve un array con los nombres de todos los campos. ej : @nom_campos = &glib_cgi_02::param();
# Si el control es de tipo file, retorna el path nombre original del archivo. ej: $FORM{'file1'} = &glib_cgi_02::param('file1');
my ($control_name) = $_[0];

  if ($control_name ne '') {
    if ($MULTIVALUES{$control_name} eq 'S') {
      return split(/\t/, $FORM{$control_name});
    }
    else {
      return $FORM{$control_name};
    };
  }
  else {
    return (keys(%FORM));
  };

}; # param

# --------------------------------------------------------------------#
sub set_formvar {

my ($control_name) = shift;
my ($hash) = shift;

  if ($control_name ne '') {
    if ($MULTIVALUES{$control_name} eq 'S') {
      $$hash{$control_name} = split(/\t/, $FORM{$control_name});
    }
    else {
      $$hash{$control_name} = $FORM{$control_name};
    };
  };


}; # param

# --------------------------------------------------------------------#
sub real_paths {
  # devuelve el path real (original) de un archivo subido
  my ($control_name) = $_[0];

  if ($control_name ne '') {
    return $REALPATH{$control_name};
  };
  return '';
}; # real_paths

# --------------------------------------------------------------------#
sub new {
# Recibe la data enviada enviada y la pone dentro de los hash %FORM e %IMAGENES.
  my($pair,$buffer,$value,$aux,@itm,$head,$con,$nom,$fgn);
  my($prematch,$buf1,$buf2);
  my($sep,$itm,$status,$readbytes,$wrotebytes,$filename,$extension,$temp_filename);
  my(@pairs,$data,$findata);

  &garbage_collector();

  binmode STDIN;
  # open (CHORRO,'>chorro2.txt'); # debug
  # binmode CHORRO; # debug

  # Determina el metodo a utilizar.
  # Ejemplo: multipart/form-data; boundary=---------------------------7d31d6b2bc
  $aux = $ENV{'CONTENT_TYPE'};
  # print STDERR "AUX[$aux]\n";

  if ( ($ENV{'REQUEST_METHOD'} ne 'GET') && ($aux =~ /multipart\/form-data/) ) {

    # &graba_stdin(); # return; # debug

    # Se trata de un formulario con submit de archivos.
    # Obtiene string separador.
    $sep = '--' . &getheadvalue($aux,'boundary');

    $aux = '';
    $nom = '';
    $buf1 = '';
    $buf2 = '';
    $temp_filename = '0';
    $findata = 0; # 4.1
    $readbytes = 0; # 4.4

    do {
      # print CHORRO "buf1[$buf1]\n"; # debug
      if ($buf1 !~ /$sep.+?\r\n\r\n/s) {
        # print CHORRO "Hay que leer? "; # debug
        if ($readbytes < $ENV{'CONTENT_LENGTH'}) { # 4.4
          # print CHORRO "SI\n"; # debug
          # 4.4 Ajusta tamano del buffer a leer.
          if ( ($ENV{'CONTENT_LENGTH'} - $readbytes) < $BUFFER_SIZE) {
            $BUFFER_SIZE = $ENV{'CONTENT_LENGTH'} - $readbytes;
          };
          # print "leo $BUFFER_SIZE..."; # debug
          $readbytes += read(STDIN, $buf2, $BUFFER_SIZE); # Lee 1 trozo solo si lo necesita.
          # print CHORRO $buf2; # debug
          # print "listo\n"; # debug
        }else{
          # print CHORRO "NO\n"; # debug
          $buf2 = '';
        };
        if ($buf2 eq '') { $findata = 1; }; # 4.1
      };
      # print CHORRO "buf2[$readbytes][" . length($buf2) . "]\n"; # debug
      $aux = $buf1 . $buf2;
      if ($aux =~ /$sep.+?\r\n\r\n/s) { # Encontro un separador con encabezado y todo.
        # Redefine buffers para acomodarse al limite recien descubierto.
        $prematch = $`; # Prematch.
        chop $prematch; # 4.1
        chop $prematch; # 4.1
        $head = $&; # Match.
        $buf1 = $'; # Postmatch.
        $buf2 = '';
        $aux = '';
        # print CHORRO "prematch[$prematch]head[$head]buf1[$buf1]\n"; # debug
        # Finiquita datos anteriores.
        if ($temp_filename eq '0') {
          if ($nom ne '') {
            $data .= $prematch;
            # Artilugio para compatibilidad multivalues.
            if ( ($FORM{$nom} eq '') || ($filename ne '') ) {
              $FORM{$nom} = $data;
            }elsif ( ($data) and ($FORM{$nom} ne $data) and ($FORM{$nom} !~ /\t$data$/) and ($FORM{$nom} !~ /\t$data\t/) and ($FORM{$nom} !~ /^$data\t/)) {    # 8.0 ajusta e.r.
              $MULTIVALUES{$nom} = 'S';
              $FORM{$nom} .= "\t$data"; # Acumula contenido separado por tabs.
            };
            $data = '';
          };
        }else{
          print OUTFILE $prematch;
          close OUTFILE;
          $wrotebytes += length $prematch;
          # if ($wrotebytes == 0) { delete $FORM{$nom}; };
          if ($wrotebytes == 0) {
            $FORM{$nom} = '';
            unlink "$TEMP_DIR/$temp_filename";
          };
        };
        # Inicializa nueva variable.
        $nom = &getheadvalue($head,'name');
        $filename = &getheadvalue($head,'filename');
        # print STDERR "nom[$nom] filename[$filename]\n"; # debug
        # if ($filename ne '') {
        if ($filename =~ /\w/) {
          $extension = '';
          $REALPATH{$nom} = $filename; # guarda el path real del archivo por si se desea usar.
          if ($filename =~ /(\/|\\)([^\/\\]+)$/) { $filename = $2; }; # Elimina el path.
          if ($filename =~ /\.([^.]*)$/) { $extension = '.' . $1; }; # Detecta la extension.
          $temp_filename = &get_file_name($extension) . $extension; # 4.2 Genera nombre temporal.
          open OUTFILE, ">$TEMP_DIR/$temp_filename";
          binmode OUTFILE; # 4.6
          $wrotebytes = 0;
          $data = "$TEMP_DIR/$temp_filename"; # Si se trataba de un archivo, el dato es el nombre del archivo con full path.
          $FORM{$nom} = $data; # 4.1
        }else{
          $temp_filename = '0';
          $data = '';
        };
      }else{ # No encuentra aun un separador con encabezado y todo.
        # Acumula datos.
        # print "Acumula datos[$temp_filename][$nom][$buf1][$data]\n"; # debug
        if ($temp_filename eq '0') {
          if ($nom ne '') {
            $data .= $buf1;
          };
        }else{
          print OUTFILE $buf1;
          $wrotebytes += length $buf1;
          # if ($wrotebytes == 0) { delete $FORM{$nom}; };
          if ($wrotebytes == 0) {
            $FORM{$nom} = '';
            close OUTFILE if (-t OUTFILE);
            unlink "$TEMP_DIR/$temp_filename";
          };
        };
        $buf1 = $buf2;
        $buf2 = '';
      };

  # 4.5 } until (($buf1 eq '') || ($findata)); # 4.1 La cosa termina cuando no queda data que analizar.
  } until ($findata); # 4.5 La cosa termina cuando no queda data que analizar.

    # print "buf1[$buf1]\n"; # debug
    # print "findata[$findata]\n"; # debug
    if (($buf1 ne '') || ($data ne '')) { # 4.1 4.3 Quedan datos por rescatar.
      # Finiquita datos de la variable en curso.
      if ($temp_filename eq '0') {
        if ($nom ne '') {
          $data .= $buf1;
          # 4.3 Elimina posible ultimo separador.
          $data =~ s/\r\n$sep.*$//s; # 4.3
          # Artilugio para compatibilidad multivalues.
          if ( ($FORM{$nom} eq '') || ($filename ne '') ) {
            $FORM{$nom} = $data;
          }elsif ( ($data) and ($FORM{$nom} ne $data) and ($FORM{$nom} !~ /\t$data$/) and ($FORM{$nom} !~ /\t$data\t/) and ($FORM{$nom} !~ /^$data\t/)) {    # 8.0 ajusta e.r.
            $MULTIVALUES{$nom} = 'S';
            $FORM{$nom} .= "\t$data"; # Acumula contenido separado por tabs.
          };
          $data = '';
        };
      }else{
        print OUTFILE $buf1;
        close OUTFILE;
        $wrotebytes += length $buf1;
      };
    };

  }else{

    if ($ENV{'REQUEST_METHOD'} eq 'GET') {
      $buffer = $ENV{'QUERY_STRING'};
    }else{
      read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
    };
    # Se trata de un formulario "normal" (application/x-www-form-urlencoded).
    # print STDERR "buffer [$buffer]\n"; # debug
    @pairs = split(/&/, $buffer);
    foreach $pair (@pairs) {
      ($nom, $data) = split(/=/, $pair);
      # Un-Webify plus signs and %-encoding
      $nom =~ tr/+/ /; # ych
      $nom =~ s/%00//sg; # 4.9
      $nom =~ s/%([0-9A-Ha-h]{2})/pack("c",hex($1))/ge; # ych
      $data =~ tr/+/ /;
      $data =~ s/%00//sg; # 4.9
      $data =~ s/%([0-9A-Ha-h]{2})/pack("c",hex($1))/ge;
      # Anulacion de subshells.
      $data =~ s/~!/ ~!/g;

      if (($nom ne '') and ($FORM{$nom} eq '')) {  # ych
        $FORM{$nom} = '';
      };

      # Artilugio para compatibilidad multivalues.
      if ($FORM{$nom} eq '') {
        $FORM{$nom} = $data;
      }elsif ( ($FORM{$nom} ne $data) and ($FORM{$nom} !~ /\t$data$/) and ($FORM{$nom} !~ /\t$data\t/) and ($FORM{$nom} !~ /^$data\t/)) {    # 8.0 ajusta e.r.
        $MULTIVALUES{$nom} = 'S';
        $FORM{$nom} .= "\t$data"; # Acumula contenido separado por tabs.
      };
      # print STDERR "$nom = [" . $FORM{$nom} . "]\n"; # debug
    };
  };

  # close CHORRO; # debug

}; # new

# --------------------------------------------------------------------#
sub graba_stdin {
  my $buffer;
  binmode STDIN;
  read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
  open (ARCHIVO,">chorro.txt")
    || die "Content-Type: text/plain\n\n Fail Open file \n $!\n";
  binmode ARCHIVO;
  print ARCHIVO $buffer; # Escribe buffer completo
  close ARCHIVO;
}; # graba_stdin


# --------------------------------------------------------------------#
# Retorna el valor del item de un encabezado.
sub getheadvalue {
  my($header,$item) = @_;
  my (@sub_sep, $sub_nom,$sub_val);
  @sub_sep = split(/(\; |\r\n)/, $header); # Separa header en '; ' y en retornos de carro.
  foreach (@sub_sep) {
    ($sub_nom,$sub_val) = split('=');
    if ($sub_nom eq $item) {
      if ($sub_val =~ /\"([^\"]+)\"/) {    # Elimina las comillas (si las tiene).
        return $1;
      }else{
        return $sub_val;
      };
    };
  };
}; # getheadvalue

# --------------------------------------------------------------------#
# 4.0 Inicializa y limpia el directorio temporal.
sub garbage_collector {
  my(@entries,@stats,$entry);
  if (! (-d $TEMP_DIR)) {
    mkdir $TEMP_DIR, 493;
  };
  # Lee el contenido del directorio.
  if (opendir(DIR, $TEMP_DIR)) {
    @entries = readdir(DIR);
    closedir DIR;
  };
  # Borra cualquier archivo con mas de 2 horas de antiguedad.
  # print $$ . 'time = ' . time . ' ';
  foreach $entry (@entries) {
    if (-f "$TEMP_DIR/$entry") {
      @stats = stat "$TEMP_DIR/$entry";
      # print $stats[10] . ' ';
      if ($stats[10] < (time - 7200)) { # 2 horas.
        unlink "$TEMP_DIR/$entry";
      };
    };
  };
}; # garbage_collector

# --------------------------------------------------------------------#
# 4.2 Obtiene un nombre de archivo unico.
sub get_file_name {
  my($extension) = $_[0];
  $CURRENTFILEIDX++;
  # Comprueba si el archivo no existe, si existe, incrementa $CURRENTFILEIDX.
  while (-e "$TEMP_DIR/" . $$ . "$CURRENTFILEIDX\.$extension") {
    $CURRENTFILEIDX++;
    if ($CURRENTFILEIDX > 10000) { return 0; };
  };
  return $$ . $CURRENTFILEIDX;
}; # get_file_name

# --------------------------------------------------------------------#
# 4.0 Obtiene un nombre de archivo unico.
sub get_file_name_old {
  my(@entries,%entries);
  my($i,$entry);
  # Lee el contenido del directorio temporal.
  if (opendir(DIR, $TEMP_DIR)) {
    @entries = readdir(DIR);
    closedir DIR;
    foreach $entry (@entries) {
      $entry =~ s/\.[^\.]*$//; # Elimina la extension.
      $entries{$entry} = 1;
    };
    # Prueba numeros hasta que encuentra uno libre.
    for ($i=1;$i<10240;$i++) {
      last if ( $entries{$$ . $i} eq '' );
    };
    return $$ . $i;
  };
  return 0;
}; # get_file_name_old

# ------------------------------------------------------------------------#
#~ sub append_file {
  #~ my($archivo,$buffer) = ($_[0],$_[1]);
  #~ return if ($buffer eq '');
  #~ open (ARCHIVO,">>$archivo")
    #~ || die "Content-Type: text/plain\n\n Fail Open file $archivo \n $!\n";
  #~ binmode ARCHIVO;
  #~ print ARCHIVO $buffer; # Escribe buffer completo
  #~ close ARCHIVO;
#~ }; # append_file


#--------------------------------------------------------------------#
return 1;
#-------------------------------END LIBRERIA---------------------
