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
# Manipulación general de archivos y directorios locales .

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 01 : Primera version at 04/feb/2000.

# 02 : Cambio a segunda version, congelada para prontus 5 - 17/04/2001

# 02.1 : Modificacion en borra_dir - 13/01/2003 - p9

#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package glib_fildir_02;

use strict;
use File::Copy; # este paquete viene con Perl

#---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub parse_ssi {
  my $dir_server = $_[0];
  my $buffer = $_[1];
  $buffer =~ s/<!--#include virtual="([^"]+?)" *-->/&read_file($dir_server . $1)/sge;
  return $buffer
};
# ---------------------------------------------------------------
sub get_extension { # 01.1
  # Recibe ruta y nombre del archivo a buscar (sin extension).
  # Devuelve solo extension (sin punto) del primer archivo que encuentre. Vacio si no lo encuentra.

  my ($dir, $nom_file) = ($_[0], $_[1]);
  my (@files, $i, $ext);

  $ext = '';

  if (-d $dir) { # Verifica si existe directorio.
    @files = &lee_dir($dir); # Obtiene lista de archivos del directorio solicitado.

    for ($i = 0; $#files >= $i; $i++) {
      if ($files[$i] =~ /^$nom_file/) { # Busca coincidencia del archivo.
        $files[$i] =~ /\.(.*)$/ig;
        $ext = $1; # Asigna extension.
        last; # Sale del for.
      };
    };
  };

  return $ext;
};

#-------------------------------------------------------------------------#
sub copy_tree {
# Rutina RECURSIVA. Copia un directorio completo con archivos y subdirs.

# Param. de entrada :
# 0) Dir padre del dir origen, path completo sin / al final
# 1) Nombre del Dir. a copiar sin path (este es el dir origen).
# 2) Dir donde en su interior se creara el dir a copiar, path completo sin / al final
# 3) Nuevo nombre que se le va a poner al Dir. al copiarlo, sin path. Este param. tiene
#        efecto solo la primera vez que se invoca a la rutina.

    my ($padre_origen) = $_[0];
    my ($df_origen) = $_[1];
    my ($df_destino) = $_[2];
    my ($nom_destino) = $_[3];

    my ($ret, @list_dir, $item);

    if (-d $padre_origen . '/' . $df_origen) {
        $ret = opendir (dir_handle, $padre_origen . '/' . $df_origen);
    } else {
        $ret = 0;
    }
    # si es un directorio
    if ($ret) {
        if ($nom_destino ne '') {
            mkdir($df_destino . '/' . $nom_destino, 0777);
            # print "mkdir [$df_destino/$nom_destino]\n\n";
        } else {
            mkdir($df_destino . '/' . $df_origen, 0777);
            # print "mkdir [$df_destino/$df_origen]\n\n";
        }

        @list_dir = readdir dir_handle;
        close dir_handle;
        foreach $item (@list_dir) {
            next if (($item eq '.') || ($item eq '..'));
            if ($nom_destino ne '') {
                &copy_tree($padre_origen . '/' . $df_origen, $item, $df_destino . '/' . $nom_destino);
            } else {
                &copy_tree($padre_origen . '/' . $df_origen, $item, $df_destino . '/' . $df_origen);
            }

        }
    } else { # Es un archivo
        if (-l $padre_origen . '/' . $df_origen) {
            system("cp -a $padre_origen/$df_origen $df_destino/$df_origen");
        } else {
            File::Copy::copy($padre_origen . '/' . $df_origen, $df_destino . '/' . $df_origen);
        }
        # print STDERR "copy [$df_destino/$df_origen]\n\n";
    }
}
#-------------------------------------------------------------------------#
sub copy_tree_exclude_ext {
# Rutina RECURSIVA. Copia un directorio completo con archivos y subdirs.

# Param. de entrada :
# 0) Dir padre del dir origen, path completo sin / al final
# 1) Nombre del Dir. a copiar sin path (este es el dir origen).
# 2) Dir donde en su interior se creara el dir a copiar, path completo sin / al final
# 3) Nuevo nombre que se le va a poner al Dir. al copiarlo, sin path. Este param. tiene
#        efecto solo la primera vez que se invoca a la rutina.
# 4) patron de directorios para excluir, no deben llevar / o .
# 5) patron de extensiones de archivo a excluir, solo pueden llevar .

    my $padre_origen = $_[0];
    my $df_origen    = $_[1];
    my $df_destino   = $_[2];
    my $nom_destino  = $_[3];
    my $dir_excluir  = $_[4];
    my $ext_excluir  = $_[5];

    my ($ret, @list_dir, $item);
    $ret = opendir (dir_handle, $padre_origen . '/' . $df_origen);
    # si es un directorio
    if ($ret) {
        my @exlude_dir = split(',',$dir_excluir);

        if ($nom_destino ne '') {
            foreach my $excluir (@exlude_dir) {
                if ($nom_destino =~ /$excluir/) {
                    return;
                }
            }
            mkdir($df_destino . '/' . $nom_destino, 0777);
            # print "mkdir [$df_destino/$nom_destino]\n\n";
        } else {
            foreach my $excluir (@exlude_dir) {
                if ($df_origen =~ /$excluir/) {
                    return;
                }
            }
            mkdir($df_destino . '/' . $df_origen, 0777);
            # print "mkdir [$df_destino/$df_origen]\n\n";
        }

        @list_dir = readdir dir_handle;
        close dir_handle;
        foreach $item (@list_dir) {
            next if (($item eq '.') || ($item eq '..'));
            if ($nom_destino ne '') {
                &copy_tree_exclude_ext($padre_origen . '/' . $df_origen, $item, $df_destino . '/' . $nom_destino, '', $dir_excluir, $ext_excluir);
            } else {
                &copy_tree_exclude_ext($padre_origen . '/' . $df_origen, $item, $df_destino . '/' . $df_origen,  '', $dir_excluir, $ext_excluir);
            }
        }
    } else { # Es un archivo
        my @exlude_file = split(',',$ext_excluir);
        foreach my $excluir (@exlude_file) {
            # escapeamos los caracteres "meta" que pueda tener el patron
            $excluir = quotemeta $excluir;
            if ($df_origen =~ /$excluir/) {
                return;
            }
        }
        File::Copy::copy($padre_origen . '/' . $df_origen, $df_destino . '/' . $df_origen);
        # print "copy [$df_destino/$df_origen]\n\n";
    }
}
#-------------------------------------------------------------------------#
sub crea_dir {
# Crea un subdirectorio desde un dir. dado.

# Param. de entrada :
# 0) Dir desde donde se creara el subdir
# 1) Nombre del subdir.

my($dir_desde) = $_[0];
my($nom_dir) = $_[1];

  chdir $dir_desde;
  mkdir $nom_dir, 493;

};
#-------------------------------------------------------------------------#
sub read_file_bytes {
# Lee una cantidad de caracteres desde el ppio de un archivo.

# Param. de entrada :
# 0) Path real del archivo.
# 1) Nro. de bytes a leer.

# Retorna : El texto leido | '' en caso que el archivo no exista.

  my ($archivo,$numbytes) = ($_[0],$_[1]);
  my $buffer;

  $archivo =~ s/\.\.\///g;

  if (-f $archivo) {
    open (ARCHIVO,"<$archivo")
      || die "Fail Open file $archivo \n $!\n";
    binmode ARCHIVO;
    read ARCHIVO,$buffer,$numbytes;
    close ARCHIVO;
  };

  return $buffer;

};

#-------------------------------------------------------------------------#
sub read_file {
# Lee un archivo por completo.

# Param. de entrada :
# 0) Path real del archivo.

# Retorna : El texto leido | '' en caso que el archivo no exista.
    my $archivo = shift;
    my $buffer = '';
    $archivo =~ s/\.\.\///g;

    if (-f $archivo) {
        open (ARCHIVO,"<$archivo")
        || die "Fail Open file $archivo \n $!\n";
        binmode ARCHIVO;
        read ARCHIVO, $buffer, -s $archivo;
        close ARCHIVO;
    }

    return $buffer;
}
#-------------------------------------------------------------------------#
sub read_file_ref {
# Lee un archivo por completo y devuelve la ref a el.

# Param. de entrada :
# 0) Path real del archivo.

# Retorna : El texto leido | '' en caso que el archivo no exista.

  my $archivo = $_[0];
  $archivo =~ s/\.\.\///g;

  my $size = (-s $archivo);
  my $buffer = '';

  if ((-s $archivo) and (! -d $archivo)) {
    open (ARCHIVO,"<$archivo")
      || die "Fail Open file $archivo \n $!\n";
    binmode ARCHIVO;
    read ARCHIVO,$buffer,$size;
    close ARCHIVO;

    my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
    $buffer =~ s/$crlf/\x0a/sg;
  };

  return \$buffer;

};
#------------------------------------------------------------------------#
sub write_file {
# Escribe un archivo.
# Param. de entrada :
# 0) Path real del archivo.
# 1) Texto a escribir.

    my($archivo,$buffer) = ($_[0],$_[1]);

    $archivo =~ s/\.\.\///g;
    open (ARCHIVO,">$archivo")
        || die "Content-Type: text/plain\n\n Fail Open file $archivo \n $!\n";
    binmode ARCHIVO;
    print ARCHIVO $buffer; #Escribe buffer completo
    close ARCHIVO;
}

# -------------------------------------------------------------------- #
sub append_file {
# Escribe datos al final de un archivo.
# Param. de entrada :
# 0) Path real del archivo.
# 1) Texto a escribir.

    my($file,$data) = ($_[0],$_[1]);
    $file =~ s/\.\.\///g;
    open(DATA,">>$file");
    print DATA $data;
    close DATA;
}; # append_file

#-----------------------------------------------------------------------#
sub check_dir {
# Chequea directorio. Si no existe, lo crea.

# Param. de entrada :
# 0) Path real del directorio.

# Retorna : 0 si hubo error, y 1 si no lo hubo.

  my($dir) = $_[0];
  $dir =~ s/\.\.\///g;

  my ($dir2, $dir3);

  return 0 if (($dir eq '') || ($dir eq '/'));

  $dir =~ s/\/$//sg;

  if ( ! (-e $dir) ) {

    if ($dir =~ /\/([^\/]+$)/g) {
        $dir2 = $`; # Sube 1 directorio.
        $dir3 = $1; # Directorio del final.
    } else {
        return 0;
    };

    if ( ! (-e $dir2) ) {
      # Si no existe, vuelve a llamar a esta misma funcion.
      # print STDERR "<P>no existe [$dir2]\n";  # debug
      if (&check_dir($dir2) == 0) {
        return 0; # Si falla la creacion retorna error de inmediato.
      };
    };
    # Asume que lo anterior fue exitoso, asi que crea el directorio que falta bajo el.
    # print "<P>creando $dir3 en $dir2\n"; # debug
    chdir($dir2) || return 0;  # Se cambia al directorio superior para crear este.

#    if ( mkdir($dir3, 493) == 0 ) {
#      return 0; # Si falla la creacion retorna error de inmediato.
#    };
    mkdir($dir3, 493) || return 0;

  };
  return 1;
};

#-----------------------------------------------------------------------#
sub borra_dir {
# Recorre directorio borrandolo todo. Al final tambien borra el
# directorio itself.

# Param. de entrada :
# 0) Path real del directorio.

  my $dir = $_[0];
  $dir =~ s/\.\.\///g;

  my @entries;
  if (-e $dir) {
    # Abre directorio.
    opendir(DIR, $dir) || die "Can't opendir" . $dir . $!;
    @entries = readdir(DIR);
    closedir DIR;

    # print "<P>Borrara dir: [$dir]\n"; # debug
    foreach my $entry (@entries) {
      if (($entry ne '.') and ($entry ne '..')) {
        if (-d "$dir/$entry") {
          &borra_dir("$dir/$entry");
        }else{
          unlink "$dir/$entry";
        };
      };
    };

    rmdir $dir;
    # print "<P>Borro dir: [$dir]\n"; # debug
  };

};

#-----------------------------------------------------------------------#
sub lee_dir {
# Lee un directorio y entrega la lista ordenada de entries en bruto.

# Param. de entrada :
# 0) Path real del directorio.

# Retorna : Arreglo ordenado de entradas en bruto del directorio.

  my $eldir = $_[0];
  $eldir =~ s/\.\.\///g;

  # Abre directorio.
  opendir(DIR, $eldir) || die "Can't opendir" . $eldir . $!;
  my @entries = readdir(DIR);
  closedir DIR;
  # Ordena entries alfabeticamente.
  @entries = sort @entries;
  return @entries;
};


#-------------------------------END LIBRERIA------------------
use Fcntl;
sub sys_read_file {

    my( $file_name, %args ) = @_ ;
    $file_name =~ s/\.\.\///g;
    return '' if (!-f $file_name);
    my $buf ;
    my $buf_ref = $args{'buf_ref'} || \$buf ;

    my $mode = O_RDONLY ;
    $mode |= O_BINARY if $args{'binmode'} ;

    local( *FH ) ;
    sysopen( FH, $file_name, $mode ) or
        die "Can't open $file_name: $!" ;

    my $size_left = -s FH ;

    while( $size_left > 0 ) {

        my $read_cnt = sysread( FH, ${$buf_ref},
            $size_left, length ${$buf_ref} ) ;

        unless( $read_cnt ) {

            die "read error in file $file_name: $!" ;
            last ;
        }

            $size_left -= $read_cnt ;
    }

# handle void context (return scalar by buffer reference)
    return unless defined wantarray ;

# handle list context
    return split m|?<$/|, ${$buf_ref} if wantarray ;

# handle scalar context
    return ${$buf_ref} ;
}

sub sys_read_file_lines {
# handle list context
return &sys_read_file if wantarray;
# otherwise handle scalar context
return [ &sys_read_file ] ;
}

sub sys_write_file {
    # &sys_write_file($path, $buffer)

    my $file_name = shift ;
    my $buf = shift;
    $file_name =~ s/\.\.\///g;
    # print "escrib[$file_name]\n";
    local( *FH ) ;
    sysopen( FH, $file_name, O_RDWR | O_CREAT | O_TRUNC | O_BINARY | O_NONBLOCK ) ||
        die "Can't open $file_name: $!" ;

    my $size = length( $buf ) ;

    my $write_cnt = syswrite( FH, $buf, $size) ;

    die "syswrite failed on $file_name: $!\n" unless $write_cnt == $size;

}

# Retorna la antiguedad del archivo en segundos con respecto a la fecha de hoy.
sub get_antiguedad_archivo {
  my $file = $_[0];
  my $mtime = (stat($file))[9];
  my $now = time;
  my $diff = time - $mtime;

  return $diff;
};

return 1;
