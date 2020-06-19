#!/usr/bin/perl


#-------------------------------COMENTARIO GLOBAL---------------
#---------------------------------------------------------------
# PROPOSITO.
#-----------
# Manipulación general de archivos y directorios locales.

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

package sitemap_glib_fildir_02;

use File::Copy; # este paquete viene con Perl


#---------------------------------------------------------------
# SUB-RUTINAS.
#-------------
#-------------------------------------------------------------------------#
sub copy_tree {
# Rutina RECURSIVA. Copia un directorio completo con archivos y subdirs.
# Param. de entrada :
#   0) Dir padre del dir origen, path completo sin / al final
#   1) Nombre del Dir. a copiar sin path (este es el dir origen).
#   2) Dir donde en su interior se creara el dir a copiar, path completo sin / al final
#   3) Nuevo nombre que se le va a poner al Dir. al copiarlo, sin path. Este param. tiene
#      efecto solo la primera vez que se invoca a la rutina.

    my ($padre_origen) = $_[0];
    my ($df_origen) = $_[1];
    my ($df_destino) = $_[2];
    my ($nom_destino) = $_[3];

    my ($ret, @list_dir, $item);
    $ret = opendir (dir_handle, $padre_origen . '/' . $df_origen);
    # si es un directorio
    if ($ret) {
        if ($nom_destino ne '') {
            mkdir($df_destino . '/' . $nom_destino, 0777);
            # print "mkdir [$df_destino/$nom_destino]\n\n"; DEBUG
        } else {
            mkdir($df_destino . '/' . $df_origen, 0777);
            # print "mkdir [$df_destino/$df_origen]\n\n"; DEBUG
        };

        @list_dir = readdir dir_handle;
        close dir_handle;
        foreach $item (@list_dir) {
            next if (($item eq '.') || ($item eq '..'));
            if ($nom_destino ne '') {
                &copy_tree($padre_origen . '/' . $df_origen, $item, $df_destino . '/' . $nom_destino);
            } else {
                &copy_tree($padre_origen . '/' . $df_origen, $item, $df_destino . '/' . $df_origen);
            };
        };
    } else { # Es un archivo
        File::Copy::copy($padre_origen . '/' . $df_origen, $df_destino . '/' . $df_origen);
        # print "copy [$df_destino/$df_origen]\n\n"; DEBUG
    };
};

#-------------------------------------------------------------------------#
sub crea_dir {
# Crea un subdirectorio desde un dir. dado.
# Param. de entrada :
#   0) Dir desde donde se creara el subdir
#   1) Nombre del subdir.

    my($dir_desde) = $_[0];
    my($nom_dir) = $_[1];
    chdir $dir_desde;
    mkdir $nom_dir, 493;
};

#-------------------------------------------------------------------------#
sub read_file_bytes {
# Lee una cantidad de caracteres desde el ppio de un archivo.
# Param. de entrada :
#   0) Path real del archivo.
#   1) Nro. de bytes a leer.
#   Retorna : El texto leido | '' en caso que el archivo no exista.

    my($archivo,$numbytes) = ($_[0],$_[1]);
    my($buffer);

    if (-e $archivo) {
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
#   0) Path real del archivo.
#   Retorna : El texto leido | '' en caso que el archivo no exista.

    my($archivo) = $_[0];
    my($size) = (-s $archivo);
    my($buffer) = '';

    if (-e $archivo) {
        open (ARCHIVO,"<$archivo")
                || die "Fail Open file $archivo \n $!\n";
        binmode ARCHIVO;
        read ARCHIVO,$buffer,$size;
        close ARCHIVO;
    };
    return $buffer;
};

#------------------------------------------------------------------------#
sub write_file {
# Escribe un archivo.
# Param. de entrada :
#   0) Path real del archivo.
#   1) Texto a escribir.

    my($archivo,$buffer) = ($_[0],$_[1]);
    open (ARCHIVO,">$archivo")
            || die "Content-Type: text/plain\n\n Fail Open file $archivo \n $!\n";
    binmode ARCHIVO;
    print ARCHIVO $buffer; #Escribe buffer completo
    close ARCHIVO;
};

#-----------------------------------------------------------------------#
sub check_dir {
# Chequea directorio. Si no existe, lo crea.
# Param. de entrada :
#   0) Path real del directorio.
#   Retorna : 0 si hubo error, y 1 si no lo hubo.

    my($dir) = $_[0];
    my($dir2);
    my($dir3);

    if ( ! (-e $dir) ) {
        $dir =~ /\/([^\/]+$)/g; # Cambiar : por /
        $dir2 = $`; # Sube 1 directorio.
        $dir3 = $1; # Directorio del final.
        if ( !(-e $dir2) ) {
            # Si no existe, vuelve a llamar a esta misma funcion.
            if (&check_dir($dir2) == 0) {
                return 0; # Si falla la creacion retorna error de inmediato.
            };
        };
        # Asume que lo anterior fue exitoso, asi que crea el directorio que falta bajo el.
        chdir $dir2;  # Se cambia al directorio superior para crear este.
        if ( mkdir($dir3, 493) == 0 ) {
            return 0; # Si falla la creacion retorna error de inmediato.
        };
    };
    return 1;
};

#-----------------------------------------------------------------------#
sub borra_dir {
# Recorre directorio borrandolo todo. Al final tambien borra el
# directorio itself.
# Param. de entrada :
#   0) Path real del directorio.

    my($dir) = $_[0];
    my(@entries);

    if (-e $dir) {
        # Abre directorio.
        opendir(DIR, $dir) || die "Can't opendir" . $dir . $!;
        @entries = readdir(DIR);
        closedir DIR;

        foreach $entry (@entries) {
            if (($entry ne '.') and ($entry ne '..')) {
                if (-d "$dir/$entry") {
                    &borra_dir("$dir/$entry");
                } else {
                    unlink "$dir/$entry";
                };
            };
        };
        rmdir $dir;
    };
};

#-----------------------------------------------------------------------#
sub lee_dir {
# Lee un directorio y entrega la lista ordenada de entries en bruto.
# Param. de entrada :
#   0) Path real del directorio.
#   Retorna : Arreglo ordenado de entradas en bruto del directorio.

    my($eldir) = $_[0];
    # Abre directorio.
    opendir(DIR, $eldir) || die "Can't opendir" . $eldir . $!;
    my @entries = readdir(DIR);
    closedir DIR;
    # Ordena entries alfabeticamente.
    @entries = sort @entries;
    return @entries;
};

#-------------------------------END LIBRERIA------------------
return 1;