#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use strict;
use LWP::UserAgent;
use HTTP::Response;
use glib_fildir_02;
use Time::HiRes qw(sleep);

close STDOUT;

my %FORM;
my $ua;
my $dir_semaf;

main: {
    $FORM{'prontus_id'} = $ARGV[0];
    $FORM{'file'} = $ARGV[1];

    &valida_params();

    # Carga variables de configuracion de prontus.
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus_id'});
    &lib_prontus::load_config( &lib_prontus::ajusta_pathconf($relpath_conf) );

    $dir_semaf = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/semaforos";
    &glib_fildir_02::check_dir($dir_semaf) if (!-d $dir_semaf);

    if (-f "$dir_semaf/purge_cache.lck") {
        my $pid = &glib_fildir_02::read_file("$dir_semaf/purge_cache.lck");

        if ($pid) {
            print STDERR "[$$] Ya existe un proceso corriendo pid[$pid]\n";
            my $mtime = (stat("$dir_semaf/purge_cache.lck"))[9];
            my $now = time;
            my $diff = $now - $mtime;
            if ($diff > 1800) { # 30 minutos.
                print STDERR "[$$] Semaforo muy antiguo, eliminando...";
                unlink "$dir_semaf/purge_cache.lck";
                system("kill -9 $pid"); # matar proceso.
            } else {
                my $ret = `ps p $pid | grep prontus_purge_cache | grep -v grep`;
                if ($ret) {
                    print STDERR "[$$] pid[$pid] still runnin, leaving...\n";
                    exit;
                } else {
                    print STDERR "[$$] $pid is dead\n";
                };
            };
        };
    };

    &glib_fildir_02::write_file("$dir_semaf/purge_cache.lck", $$);

    my $espera_segs = 5;
    $ua = new LWP::UserAgent;
    $ua->timeout($espera_segs); # segs # default es 180
    $ua->agent('Mozilla/5.0 (Windows; U; Windows NT 5.1; es-ES; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'); # default es "libwww-perl/#.##"

    if (-f $FORM{'file'}) {
        &purge($FORM{'file'});
        print STDERR "[$$] Se termino de procesar [$FORM{'file'}].\n";
        unlink $FORM{'file'};
    };

    # Revisar si hay más archivos.
    my $dir_purgepend = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/purgepend";
    my @files = glob("$dir_purgepend/*.txt");
    my $file;

    print STDERR "[$$] Buscando si hay mas archivos...\n";

    while (defined($file = shift @files)) {
        print STDERR "[$$] Procesando [$file]\n";
        next if (!-s $file);
        &purge($file);
        print STDERR "[$$] Se termino de procesar [$file].\n";
        unlink $file;

        # La idea es que si van agregando mas archivos mientras este proceso corre, se procecen.
        if ($#files <= 0) {
            print STDERR "[$$] Buscando si hay mas archivos...\n";
            @files = glob("$dir_purgepend/*.txt");
        };
    };

    print STDERR "[$$] Fin.\n";

    unlink "$dir_semaf/purge_cache.lck";
    exit;
};

sub valida_params {
    if ($FORM{'prontus_id'} eq '') {
        print STDERR "[$$] Debe indicar el nombre del Prontus.\n";
        exit;
    };
    if ($FORM{'file'} eq '') {
        print STDERR "[$$] Debe indicar el path hacia el archivo con recursos.\n";
        exit;
    };
};

sub purge {
    my ($path_file) = shift;
    my $purge_cloudflare = 0;
    my $only_cloudflare = 0;

    if ($prontus_varglb::CLOUDFLARE eq 'SI' && $prontus_varglb::CLOUDFLARE_API_URL ne '' && $prontus_varglb::CLOUDFLARE_API_KEY ne '' && $prontus_varglb::CLOUDFLARE_EMAIL ne '' && $prontus_varglb::CLOUDFLARE_ZONE ne '') {
        $purge_cloudflare = 1;
    };

    if ($path_file =~ /_cf\.txt$/i) {
        $only_cloudflare = 1;
    };

    open (PURGEFILE, "<$path_file");

    my $counter_cf = 0;

    foreach my $filetopurge (<PURGEFILE>) {
        if (!-f $path_file) {
            print STDERR "[$$] Abortado, el archivo [$path_file] ya no existe.\n";
            unlink "$dir_semaf/purge_cache.lck";
            exit;
        };

        $filetopurge =~ s/\n//is;
        my $relpath = &lib_prontus::remove_front_string($filetopurge, $prontus_varglb::DIR_SERVER);

        if (!$only_cloudflare) { # si no es solo cloudflare, se hace purge normal a varnish.
            foreach my $server (keys %prontus_varglb::VARNISH_SERVER_NAME) {
                next if (!$server);
                my $url_purge = "http://$server$relpath";
                my ($resp, $err) = &get_url($url_purge);
                print STDERR "[$$] varnish: server[$server], url_purge[$url_purge], status[$err]\n";
            };
        } else {
                print STDERR "[$$] purge_cloudflare[$purge_cloudflare] only_cloudflare[$only_cloudflare]\n";
        };

        if ($purge_cloudflare) {
            my %datos_post;
            my $url_purge = "http://$prontus_varglb::PUBLIC_SERVER_NAME$relpath";

            $datos_post{'a'} = 'zone_file_purge';
            $datos_post{'tkn'} = $prontus_varglb::CLOUDFLARE_API_KEY;
            $datos_post{'email'} = $prontus_varglb::CLOUDFLARE_EMAIL;
            $datos_post{'z'} = $prontus_varglb::CLOUDFLARE_ZONE;
            $datos_post{'url'} = $url_purge;

            my ($resp, $err) = &post_url($prontus_varglb::CLOUDFLARE_API_URL, \%datos_post);

            print STDERR "[$$] cloudflare: api_key[$prontus_varglb::CLOUDFLARE_API_KEY], url_purge[$url_purge], status[$err] resp[$resp]\n";

            $counter_cf++;

            if ($counter_cf >= 100) {
                $counter_cf = 0;
                print STDERR "[$$] api rate limit! sleep 60 segundos...\n";
                sleep 60; # There is a rate limit for file purges of 100 per minute. Exceeding this limit will return an error in the JSON response.
            } else {
                sleep 0.5; # para no bombardear la api.
            };

        };
    };

    close PURGEFILE;

    # Se intenta realizar el Global Purge, si aplica
    if ($prontus_varglb::VARNISH_GLOBAL_PURGE) {
        my @arr = split( /[\n\r]/, $prontus_varglb::VARNISH_GLOBAL_PURGE);
        foreach my $path (@arr) {
            next unless($path);
            next if ($path !~ /^\//); # debe empezar con /
            foreach my $server (keys %prontus_varglb::VARNISH_SERVER_NAME) {
                my $url_purge = "http://$server$path";
                my ($resp, $err) = &get_url($url_purge);
                print STDERR "[$$] global purge -> server[$server], url_purge[$url_purge], status[$err]\n";
            };
        };
    };

    if ($purge_cloudflare && !$only_cloudflare) {
        if ($prontus_varglb::CLOUDFLARE_GLOBAL_PURGE) {
            my @arr = split(/[\n\r]/, $prontus_varglb::CLOUDFLARE_GLOBAL_PURGE);
            foreach my $path (@arr) {
                next unless($path);
                next if ($path !~ /^\//); # debe empezar con /

                my %datos_post;
                my $url_purge = "http://$prontus_varglb::PUBLIC_SERVER_NAME$path";

                $datos_post{'a'} = 'zone_file_purge';
                $datos_post{'tkn'} = $prontus_varglb::CLOUDFLARE_API_KEY;
                $datos_post{'email'} = $prontus_varglb::CLOUDFLARE_EMAIL;
                $datos_post{'z'} = $prontus_varglb::CLOUDFLARE_ZONE;
                $datos_post{'url'} = $url_purge;

                my ($resp, $err) = &post_url($prontus_varglb::CLOUDFLARE_API_URL, \%datos_post);
                print STDERR "[$$] global purge cloudflare: api_key[$prontus_varglb::CLOUDFLARE_API_KEY], url_purge[$url_purge], status[$err] resp[$resp]\n";

                $counter_cf++;

                if ($counter_cf >= 100) {
                    $counter_cf = 0;
                    print STDERR "[$$] api rate limit! sleep 60 segundos...\n";
                    sleep 60; # There is a rate limit for file purges of 100 per minute. Exceeding this limit will return an error in the JSON response.
                } else {
                    sleep 0.5; # para no bombardear la api.
                };
            };
        };
    };

    # Actualiza fecha de modificación del semaforo en caso de que se procesen muchos archivos
    # no llegue otro proceso y lo pise.
    # El semaforo es util cuando el script se caiga o se quede pegado (sin actualizar mtime).
    utime time, time, "$dir_semaf/purge_cache.lck";
};

sub get_url {
    my($url) = $_[0];

    return '' if (($url eq '') or ($url !~ /^https?/i));
    # my($request) = new HTTP::Request('GET', $url . "/purge") || return ('', $!);
    # CVI - Por n-ésima vez se cambia esto. Finalmente se decide usar método PURGE
    my($request) = new HTTP::Request('PURGE', $url) || return ('', $!);
    my($response) = $ua->request($request) || return ('', $!);
    #~ print STDERR "[$$] status_line[" . $response->status_line . "], header: [" . $response->headers_as_string . "]\n";
    if ($response->is_success) {
        return ($response->content, $response->status_line);
    } else {
        return ('', $response->status_line);
    };

}; # getHTML

sub post_url {
    my $url = $_[0];
    my $data_ref = $_[1];
    my %data = %{$data_ref};

    my $ua       = LWP::UserAgent->new();
    my $response = $ua->post( $url, \%data );

    if ($response->is_success) {
        return ($response->content, $response->status_line);
    } else {
        return ('', $response->status_line);
    };

};