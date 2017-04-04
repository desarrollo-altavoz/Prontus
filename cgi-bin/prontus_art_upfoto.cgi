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
# PROPOSITO .
# -----------
# Recibir foto subida y dejarla en carpeta temporal mientras se presiona el boton guardar articulo,
# momento en que la foto es agregada al articulo.

#    my @campos = &glib_cgi_04::param();
#    my %hash_datos;
#    foreach $nom_campo (sort {$a cmp $b} @campos) {
#        my $nom_lc = lc $nom_campo;
#        $hash_datos{$nom_lc} = &glib_cgi_04::param($nom_campo);
#        print STDERR "NOM[$nom_lc] value[$hash_datos{$nom_lc}]\n";
#    };
# cuando se suben las fotos por el plugin, se generan n requests al server, cada uno envia:
# NOM[Filedata] value[/sites/prontus_development/web/cgi-cpn/prontus_temp/573211.jpg]
# [Mon Apr 19 18:37:03 2010] [error] [client 192.168.13.64] NOM[Filename] value[2008_bolt_002.jpg]
# [Mon Apr 19 18:37:03 2010] [error] [client 192.168.13.64] NOM[upload] value[Submit Query]
# [Mon Apr 19 18:37:03 2010] [error] [client 192.168.13.64] NOM[folder] value[/prontus_toolbox/cpan/core/js-local/uploadify/uploads]

# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# - Desde un FID, via AJAX
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# No registra.
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - XXX - xx/xx/xxxx - primera version
# 1.1 - SCT - 21/04/2016 - Se agrega el nombre de la foto original para ser procesado: $FORM{'filename'}
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibs = $Bin;
    unshift(@INC, $pathLibs);
    do 'dir_cgi.pm';
    $pathLibs =~ s/\/[^\/]+$/\/$DIR_CGI_CPAN/;
    unshift(@INC,$pathLibs);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;

use lib_prontus;
use glib_fildir_02; # Prontus 6.0

use strict;
use File::Copy;
use Session;
use lib_thumb;

# ---------------------------------------------------------------
# MAIN.
# -------------
my (%FORM);

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();

    $FORM{'filedata'} = &glib_cgi_04::param('Filedata');
    $FORM{'filename'} = &glib_cgi_04::param('Filename');
    $FORM{'prontus_id'} = &glib_cgi_04::param('prontus_id');
    $FORM{'sdata'} = &glib_cgi_04::param('sdata'); # id de session, se le debe pasar porque esta cgi al ser invocada por flash, no tiene acceso a las cookies.

    my $trace_info;
    $trace_info = "prontus_id[$FORM{'prontus_id'}]\n";
    $trace_info .= "filename[$FORM{'filename'}]\n";
    $trace_info .= "filedata[$FORM{'filedata'}]\n";
    $trace_info .= "sdata[$FORM{'sdata'}]\n";

    # $FORM{'prontus_id'} =~ s/[^\w\-]//sg;
    &valida_invocacion($trace_info);

    # Path de cfg de prontus
    my $path_conf = "/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);

    # Carga variables de configuracion de prontus.
    &lib_prontus::load_config($path_conf);
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;


    # print STDERR "PASA OK\ntrace_info[$trace_info]\n\n";

    my $nomfile;
    my $ext;
    if ($FORM{'filedata'} =~ /(\/|\\)?([^\/\\]+?)(\.\w+)$/) {
        $nomfile = lc $2;
        $ext = lc $3; # ext con punto
    } else {
        print STDERR "filedata no valido, trace_info[$trace_info]\n";
        print "Content-Type: text/html\n\n";
        print 0;
        exit;
    };

    if (! -f $FORM{'filedata'}) {
        print STDERR "filedata no valido, trace_info[$trace_info]\n";
        print "Content-Type: text/html\n\n";
        print 0;
        exit;
    };

    # Compone path destino de la imagen y realiza garbage
    my $rel_dst_dir = "/$FORM{'prontus_id'}/cpan/procs/uploadify";

    &glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$rel_dst_dir");

    &garbage_collector("$prontus_varglb::DIR_SERVER$rel_dst_dir");


    my $rel_dst_path = "$rel_dst_dir/$nomfile$ext";
    $trace_info .= "rel_dst_path[$rel_dst_path]\n";
    my $dst_path = "$prontus_varglb::DIR_SERVER$rel_dst_path";

    my $src_path = $FORM{'filedata'};
    $trace_info .= "src_path[$src_path] dst_path[$dst_path] \n";

    &File::Copy::move($src_path, $dst_path);


    print "Content-Type: text/html\n\n";


    if ((-f $dst_path) && (-s $dst_path)) {

        my $idFoto = $nomfile . $FORM{'filename'};
        $idFoto =~ s/[^a-zA-Z0-9]//g;
        my ($msg_size, $wfoto, $hfoto) = &lib_prontus::dev_tam_img($dst_path);
        if($msg_size) {
            print STDERR "No se pudo obtener las dimensiones de la imagen [$msg_size]\n";
            print "Content-Type: text/html\n\n";
            print 0;
            exit;
        }
        # Redimencionar imagen si es que supera los limites configurados.
        if ($prontus_varglb::FOTO_MAX_PIXEL ne '') { # si está vacio no se hace nada.
            my ($wmax, $hmax) = split("x", $prontus_varglb::FOTO_MAX_PIXEL);
            if ($wfoto > $wmax || $hfoto > $hmax) {
                my ($wnew, $hnew) = &lib_thumb::calcular_proporcion_img($wfoto, $hfoto, $wmax, $hmax);
                my ($binfoto, $wfoto, $hfoto) = &lib_thumb::make_resize($wnew, $hnew, $dst_path);
                $dst_path =~ s/\.gif$/\.png/i if($dst_path =~ /\.gif$/i);
                &lib_thumb::write_image($dst_path, $binfoto);
            };
        };

        print "$idFoto,$wfoto,$hfoto,$rel_dst_path,$nomfile,$FORM{'filename'}"; # se devuelve para presentarlo en la pagina y tb. para guardarlo en hiddens
                             # y luego tomar desde ahi la imagen para crearla.
    } else {
        print STDERR "error al subir imagen:\n$trace_info";
        print 0;
    };


};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub valida_invocacion {
    my $trace_info = shift;

    if (! &lib_prontus::valida_prontus($FORM{'prontus_id'})) {
        print STDERR "prontus_id no valido, trace_info[$trace_info]\n";
        print "Content-Type: text/html\n\n";
        print 0;
        exit;
    };


    if ($FORM{'filename'} eq '') {
        print STDERR "filename no valido, trace_info[$trace_info]\n";
        print "Content-Type: text/html\n\n";
        print 0;
        exit;
    };

    my $sess_obj = Session->new(
                    'prontus_id'        => $FORM{'prontus_id'},
                    'id_session_given'  => $FORM{'sdata'}, # en vez de sacarla de la cookie, la saca de aca
                    'document_root'     => $prontus_varglb::DIR_SERVER)
                    || die("Error inicializando objeto Session: $Session::ERR\n");
    if ($sess_obj->{id_session} eq '') {
        print STDERR "user no valido[$prontus_varglb::USERS_PERFIL] - prontus_id[$FORM{'prontus_id'}]\n";
        print "Content-Type: text/html\n\n";
        print 0;
        exit;
    };

};


# 4.0 Inicializa y limpia el directorio temporal.
sub garbage_collector {
  my $dir = $_[0];
  my(@entries,@stats,$entry);
  # Lee el contenido del directorio.
  if (opendir(DIR, $dir)) {
    @entries = readdir(DIR);
    closedir DIR;
  };
  # Borra cualquier archivo con mas de 2 horas de antiguedad.
  # print $$ . 'time = ' . time . ' ';
  foreach $entry (@entries) {
    if (-f "$dir/$entry") {
      @stats = stat "$dir/$entry";
      # print $stats[10] . ' ';
      if ($stats[10] < (time - 7200)) { # 2 horas.
        unlink "$dir/$entry";
      };
    };
  };
}; # garbage_collector

# -------------------------------END SCRIPT----------------------

