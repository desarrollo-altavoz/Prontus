#!/usr/bin/perl
# --------------------------------------------------------------
# Respaldo de archivos prontus en Dropbox.
# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 11/11/2014 - JOR - Primera versión
# ---------------------------------------------------------------


BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use strict;
use LWP::UserAgent;
use HTTP::Response;

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use lib_dropbox;

#close STDOUT;

my %FORM;
my $DIR_SEMAF;

main: {
    $FORM{'prontus_id'} = $ARGV[0];
    $FORM{'file'} = $ARGV[1];

    &valida_params();

    my ($prontus_id, $ts, $dir_fecha, $relpath_artic);

    # Carga variables de configuracion de prontus.
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus_id'});
    &lib_prontus::load_config(&lib_prontus::ajusta_pathconf($relpath_conf));

    if ($prontus_varglb::DROPBOX eq 'NO' || $prontus_varglb::DROPBOX_ACCESS_TOKEN eq '') {
        # No se hace nada.
        exit;
    };

    print STDERR "[$$] Inicio\n";

    $DIR_SEMAF = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/semaforos";
    &glib_fildir_02::check_dir($DIR_SEMAF) if (! -d $DIR_SEMAF);

    if (-f "$DIR_SEMAF/dropbox_backup.lck") {
        my $pid = &glib_fildir_02::read_file("$DIR_SEMAF/dropbox_backup.lck");

        if ($pid) {
            print STDERR "[$$] Ya existe un proceso corriendo pid[$pid]\n";
            my $mtime = (stat("$DIR_SEMAF/dropbox_backup.lck"))[9];
            my $now = time;
            my $diff = $now - $mtime;
            if ($diff > 1800) { # 30 minutos.
                print STDERR "[$$] Semaforo muy antiguo, eliminando...";
                unlink "$DIR_SEMAF/dropbox_backup.lck";
            } else {
                my $ret = `ps p $pid | grep prontus_dropbox_backup | grep -v grep`;
                if ($ret) {
                    print STDERR "[$$] pid[$pid] still runnin, leaving...\n";
                    exit;
                } else {
                    print STDERR "[$$] $pid is dead\n";
                };
            };
        };
    };

    &glib_fildir_02::write_file("$DIR_SEMAF/dropbox_backup.lck", $$);

    &procesar_archivo($FORM{'file'}) if (-f $FORM{'file'});

    # Revisar si hay más archivos.
    my $dir_dropbox = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/dropbox";
    my @files = glob("$dir_dropbox/*.txt");
    my $file;

    print STDERR "[$$] Buscando si hay mas archivos...\n";

    while (defined($file = shift @files)) {
        print STDERR "[$$] Procesando [$file]\n";
        next if (!-s $file);
        &procesar_archivo($file);
        print STDERR "[$$] Se termino de procesar [$file].\n";

        # La idea es que si van agregando mas archivos mientras este proceso corre, se procecen.
        if ($#files <= 0) {
            print STDERR "[$$] Buscando si hay mas archivos...\n";
            @files = glob("$dir_dropbox/*.txt");

            sleep 5; # esperar 5 segundos.
        };
    };

    print STDERR "[$$] Fin.\n";

    unlink "$DIR_SEMAF/dropbox_backup.lck";
    exit;

};

sub procesar_archivo {
    my $file = $_[0];

    open (FILE, "<$file");

    foreach my $linea (<FILE>) {
        chomp($linea);
        my ($tipo, $recurso) = split(';', $linea);
        print STDERR "[$$] Procesando [$file] tipo[$tipo] recurso[$recurso]\n";
        if ($tipo eq 'art') {
            &procesa_art($recurso); # ts.
            unlink $file;

            # actualiza fecha modificacion semaforo, para que no lo vayan a matar!
            utime time, time, "$DIR_SEMAF/dropbox_backup.lck";
        } elsif ($tipo eq 'port') {

        };
    };

};

sub procesa_art {
    my $ts = $_[0];
    my $dir_fecha;

    &lib_dropbox::conectar();

    $ts =~ /(\d{8})/;
    $dir_fecha = $1; # solo fecha.
    #$dir_fecha = "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}/site/artic/$dir_fecha"; # ruta completa.

    # Obtener listado de directorios asociados al articulo, incluye vistas.
    my @dirlist = &get_artic_dirlist($dir_fecha);

    foreach my $dir (@dirlist) {
        # Obtener listado de archivos locales.
        my @local_filelist = &get_artic_filelist("$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}/site/$dir", $ts);
        # Obtener listado de archivos en Dropbox.
        my @dropbox_filelist = &lib_dropbox::get_dir_filelist($dir);

        foreach my $local_file (@local_filelist) {
            my ($local_fullpath, $local_bytes) = split(/\t/, $local_file);
            my $local_relpath = $local_fullpath;
            $local_relpath =~ s/.*?\/(artic\/.*?)$/\/$1/sg;
            my $upload = 1;

            #print "local_relpath[$local_relpath] local_bytes[$local_bytes]\n";

            foreach my $remote_file (@dropbox_filelist) {
                my ($remote_path, $remote_isdir, $remote_bytes) = split(/\t/, $remote_file);

                next if ($remote_isdir);

                #print "remote_path[$remote_path] remote_bytes[$remote_bytes]\n";

                if ($local_relpath eq $remote_path) { # archivo encontrado, decidir si se sube o no.
                    $upload = 0;
                    if ($local_bytes != $remote_bytes) {
                        $upload = 1;
                    };
                    last;
                };
            };

            if ($upload) {
                print STDERR "[$$] Subiendo [$local_fullpath] => [$local_relpath]\n";
                my ($resp, $msgerr) = &lib_dropbox::upload_file($local_fullpath, $local_relpath);
                if (!$resp) {
                    print STDERR "[$$] No fue posible subir el archivo [$local_fullpath] => [$local_relpath] msgerr[$msgerr]\n";
                    # vuelve a intentar.
                    ($resp, $msgerr) = &lib_dropbox::upload_file($local_fullpath, $local_relpath);
                };

                if (!$resp) {
                    print STDERR "[$$] No fue posible subir el archivo [$local_fullpath] => [$local_relpath] msgerr[$msgerr]\n";
                } else {
                    print STDERR "[$$] Archivo subido [$local_fullpath] => [$local_relpath]\n";
                };
            };
        };
    };

};

sub valida_params {
    if ($FORM{'prontus_id'} eq '') {
        print STDERR "[$$] Debe indicar el nombre del Prontus.\n";
        exit;
    };

    if ($FORM{'file'} eq '') {
        print STDERR "[$$] Debe indicar la ruta hacia archivo.\n";
        exit;
    };

};

sub get_artic_filelist {
    my $dir_fecha = $_[0];
    my $ts = $_[1];
    my @files = glob("$dir_fecha/*");
    my @filelist;

    foreach my $file (@files) {
        next if ($file !~ /$ts\.\w+$/);
        $file =~ /\.(\w+)$/;
        my $ext = $1;
        next if (exists $prontus_varglb::DROPBOX_FILEXT_EXCLUDE_LIST{$ext});
        my $mtime = (stat($file))[9];
        my $bytes = -s $file;

        #next if ((time - $mtime) > 60); # solo considerar archivos modificados hace menos de 1 minuto.

        push @filelist, "$file\t$bytes";
    };

    return @filelist;

};

sub get_artic_dirlist {
    my $dir_fecha = $_[0];

    my @dirlist;
    push @dirlist, "/artic/$dir_fecha";
    push @dirlist, "/artic/$dir_fecha/asocfile";
    push @dirlist, "/artic/$dir_fecha/imag";
    push @dirlist, "/artic/$dir_fecha/mmedia";
    push @dirlist, "/artic/$dir_fecha/pags";
    push @dirlist, "/artic/$dir_fecha/pagspag";
    push @dirlist, "/artic/$dir_fecha/swf";
    push @dirlist, "/artic/$dir_fecha/xml";

    foreach my $mv (keys(%prontus_varglb::MULTIVISTAS)) {
        push @dirlist, "/artic/$dir_fecha/pags-$mv";
        push @dirlist, "/artic/$dir_fecha/pagspar-$mv";
    };

    return @dirlist;
}