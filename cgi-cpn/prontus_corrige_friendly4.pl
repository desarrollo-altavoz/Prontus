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
# SCRIPT.
# -----------
# prontus_corrige_friendly4.pl
# ---------------------------------------------------------------
# UBICACION.
# -----------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Ajustas los slugs de los articulos para que no existan colisiones
# despues de activar friendly 4
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------
# no tiene
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# A traves de linea de comando, ej:
# Parametros:
# 1: nombre del prontus a procesar
#
# Ejemplo de uso:
# perl prontus_corrige_friendly4.pl mi_prontus_id
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# ---------------------------------------------------------------
# Tablas.
# ------------------------
# No utiliza.
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 04/05/2017 - EAG - Primera Version
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    use FindBin '$Bin';
    unshift(@INC,$Bin); # Para dejar disponibles las librerias
    $pathLibsProntus = $Bin;
    $pathLibsProntus =~ s/\/[^\/]+\/?$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

use strict;

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);


use DBI;

use prontus_varglb; &prontus_varglb::init();
use glib_hrfec_02;
use lib_prontus;

use Data::Dumper;
# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
my $separator_orig = '   ';
my $separator = '';
my $counter = 0;

my @marcas = ('_fid','_txt_titular','_custom_slug','_slug');
my $PRONTUS_ID = '';
my $BD;
my $input = $Bin;

main:{
    $PRONTUS_ID = $ARGV[0];

    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($PRONTUS_ID);
    &lib_prontus::load_config("$prontus_varglb::DIR_SERVER$relpath_conf");

    if ($prontus_varglb::FRIENDLY_URLS ne 'SI') {
        print "Prontus [$PRONTUS_ID] no tiene friendly url activada\n";
        exit;
    } elsif ($prontus_varglb::FRIENDLY_URLS_VERSION ne '4') {
        print "Prontus [$PRONTUS_ID] no tiene friendly url v4 activada\n";
        exit;
    }

    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();

    if (!ref($BD)) {
        print STDERR "Error conectar BD: $msg_err_bd\n";
        &glib_html_02::print_json_result(0, "Error conectar BD: $msg_err_bd", 'exit=1,ctype=1');
        exit;
    };

    $input = $prontus_varglb::DIR_SERVER ."/$PRONTUS_ID/site/artic/";
    print "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Inicio Proceso\n";
    print "ID;TS;FID;TITULAR;SLUG_ORIGINAL;SLUG_NUEVO;URL_DIRECTA;URL_FRIENDLY\n";
    &procesa_dir($input);
    print 'Se encontraron ' . $counter .  ' archivos ' . "\n";
    print "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Fin Proceso\n";
};

#-----------------------------------------------------------------------#
sub procesa_dir {
    my($input) = $_[0];

    unless(-d $input) {
        die "El directorio $input no existe.";
    };
    $input = $input . '/' unless ($input =~ /\/$/);

    my @entries = &lee_dir($input);
    foreach my $k (@entries) {
        next if($k eq '.' || $k eq '..');
        if(-f $input . $k) {
            &procesa_file($k, $input);

        } elsif(-d $input . $k) {
            $separator = $separator . $separator_orig;
            &procesa_dir($input . $k);
        };
    };
    $separator =~ s/$separator_orig$//;

};
#-----------------------------------------------------------------------#
sub procesa_file {
    my($filename, $path) = ($_[0], $_[1]);
    my $filepath = $path . $filename;
    my $ts;
    if ($filename !~ /^(\d+?)\.xml/isg) {
        return;
    }
    $ts = $1;

    if (-f $filepath) {
        my $xml_data = &read_file($filepath);
        my $fid;

        if ($xml_data =~ /<_fid>(.*?)<\/_fid>/is) {
            $fid = $1;
            $fid =~ s/[\n\r]//g;
        } else {
            print STDERR "Artículo [$filepath] [$ts] no tiene fid asignado\n";
            next;
        }


        if (exists $prontus_varglb::FRIENDLY_V4_EXCLUDE_FID{$fid}) {
            next;
        }

        my $artic_obj;
        unless($artic_obj = Artic->new(
                    'document_root'     => $prontus_varglb::DIR_SERVER,
                    'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                    'public_server_name'=> $prontus_varglb::PUBLIC_SERVER_NAME,
                    'cpan_server_name'  => $prontus_varglb::IP_SERVER,
                    'ts'                => $ts,
                    'campos'            => {})) {
            print "[$ts] Error inicializando objeto articulo: $Artic::ERR\n";
            return '';
        };

        # cargamos los campos del xml
        my %campos = $artic_obj->get_xml_content();
        my $slug_original = '';

        # revisamos si se usa el slug custom para verificar colision
        if ($campos{'_custom_slug'} eq 'SI') {
            $slug_original = &lib_prontus::ajusta_titular_f4($campos{'_slug'});
        } else {
            $slug_original = &lib_prontus::ajusta_titular_f4($campos{'_txt_titular'});
        }

        my $nuevo_slug = $slug_original;
        my $changed = 0;
        for (my $i = 1; $i < 50; $i++) {
            if ($artic_obj->verifica_colision_url_titular($BD, $nuevo_slug)) {
                my $new_string = '-' . $i;
                if (length($slug_original) > ($prontus_varglb::FRIENDLY_URLS_LARGO_TITULAR - length($new_string))) {
                    $nuevo_slug = substr($slug_original, 0, $prontus_varglb::FRIENDLY_URLS_LARGO_TITULAR - length($new_string)). $new_string;
                } else {
                    $nuevo_slug = $slug_original . '-' . $i;
                }
                $nuevo_slug =~ s/-+/-/g;
                $changed = 1;
            } else {
                last;
            }
        }

        #~ $changed = 1;
        #~ $nuevo_slug ='slug de prueba';

        if ($changed) {
            if ($xml_data =~ /<_slug>.*?<\/_slug>/s) {
                $xml_data =~ s/<_slug>.*?<\/_slug>/<_slug>$nuevo_slug<\/_slug>/is;
            } else {
                $xml_data =~ s/<\/_txt_titular>/<\/_txt_titular>\n<_slug>$nuevo_slug<\/_slug>/is;
            }

            if ($xml_data =~ /<_custom_slug>.*?<\/_custom_slug>/s) {
                $xml_data =~ s/<_custom_slug>.*?<\/_custom_slug>/<_custom_slug>SI<\/_custom_slug>/is;
            } else {
                $xml_data =~ s/<\/_txt_titular>/<\/_txt_titular>\n<_custom_slug>SI<\/_custom_slug>/is;
            }

            # se actualiza el xml de articulo
            &write_file($artic_obj->{'fullpath_xml'}, $xml_data);
            # recargamos los campos
            $artic_obj->{'xml_content'} = {};
            my %campos = $artic_obj->get_xml_content();

            # generamos el link v4
            $artic_obj->genera_friendly_v4($BD);

            # Generar vista (a partir del xml)
            $artic_obj->generar_vista_art('', $prontus_varglb::STAMP_DEMO, $prontus_varglb::PRONTUS_KEY)
                    || &registra_artic_error("\t\t\t\tError: $Artic::ERR");

            foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
                # Generar vista (a partir del xml)
                $artic_obj->generar_vista_art($mv, $prontus_varglb::STAMP_DEMO, $prontus_varglb::PRONTUS_KEY)
                        || &registra_artic_error("\t\t\t\tError: $Artic::ERR");
            }
            my $relpath_artic = '/'.$PRONTUS_ID.'/site/artic/' . substr($ts, 0, 8) . '/pags/'. $ts . '.html';
            my $friendlyUrl = "%%_FILEURL%%";
            $friendlyUrl = &lib_prontus::parse_filef($friendlyUrl, $campos{'_txt_titular'}, $ts, $PRONTUS_ID, $relpath_artic, $campos{'_nom_seccion1'}, $campos{'_nom_tema1'}, $campos{'_nom_subtema1'});
            $campos{'_txt_titular'} =~ s/[\n\r\t]+/ /g;
            $campos{'_txt_titular'} =~ s/"//g;

            print "$campos{'_art_autoinc'};$ts;$campos{'_fid'};\"$campos{'_txt_titular'}\";\"$slug_original\";\"$campos{'_slug'}\";\"$relpath_artic\";\"$friendlyUrl\"\n";

            $counter++;
        }
    };
};

#-----------------------------------------------------------------------#
# Funciones de apoyo, tomadas de la glin_fildir_02.pm
#-----------------------------------------------------------------------#
sub lee_dir {
# Lee un directorio y entrega la lista ordenada de entries en bruto.

# Param. de entrada :
# 0) Path real del directorio.

# Retorna : Arreglo ordenado de entradas en bruto del directorio.

  my($eldir) = $_[0];
  # Abre directorio.
  opendir(DIR, $eldir) || die "Can't opendir" . $eldir . $!;
  my @entries = readdir(DIR);
  closedir DIR;
  # Ordena entries alfabeticamente.
  @entries = sort @entries;
  @entries = sort {$b <=> $a} @entries;
  return @entries;
};
#-------------------------------------------------------------------------#
sub read_file {
# Lee un archivo por completo.

# Param. de entrada :
# 0) Path real del archivo.

# Retorna : El texto leido | '' en caso que el archivo no exista.

  my($archivo) = $_[0];
  my($size) = (-s $archivo);
  my($buffer) = '';
  $archivo =~ s/\.\.\///g;

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
# 0) Path real del archivo.
# 1) Texto a escribir.

  my($archivo,$buffer) = ($_[0],$_[1]);
  $archivo =~ s/\.\.\///g;

  open (ARCHIVO,">$archivo")
    || die "Content-Type: text/plain\n\n Fail Open file $archivo \n $!\n";
  binmode ARCHIVO;
  print ARCHIVO $buffer; #Escribe buffer completo
  close ARCHIVO;

};
# -------------------------END SCRIPT----------------------
