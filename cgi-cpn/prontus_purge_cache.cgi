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
    unshift(@INC,$Bin); # Para dejar disponibles las librerias
};

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use strict;
use lib_stdlog;
use LWP::UserAgent;
use HTTP::Response;
&lib_stdlog::set_stdlog($0, 51200);

close STDOUT;

my %FORM;
my $ua;

main: {
    $FORM{'prontus_id'} = $ARGV[0];
    $FORM{'file'} = $ARGV[1];

    &valida_params();

    # Carga variables de configuracion de prontus.
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus_id'});
    &lib_prontus::load_config( &lib_prontus::ajusta_pathconf($relpath_conf) );

    if (-f $FORM{'file'}) {
        my $espera_segs = 5;
        $ua = new LWP::UserAgent;
        $ua->timeout($espera_segs); # segs # default es 180
        $ua->agent('Mozilla/5.0 (Windows; U; Windows NT 5.1; es-ES; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'); # default es "libwww-perl/#.##"
        &purge($FORM{'file'});
        print STDERR "[$$] Se termino de procesar [$FORM{'file'}].\n";
        unlink $FORM{'file'};
    };
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

    open (PURGEFILE, "<$path_file");
    foreach my $filetopurge (<PURGEFILE>) {
        if (!-f $FORM{'file'}) {
            print STDERR "[$$] Abortado, el archivo [$FORM{'file'}] ya no existe.\n";
            exit;
        };
        $filetopurge =~ s/\n//is;
        my $relpath = &lib_prontus::remove_front_string($filetopurge, $prontus_varglb::DIR_SERVER);
        foreach my $server (keys %prontus_varglb::VARNISH_SERVER_NAME) {
            my $url_purge = "http://$server$relpath";
            my ($resp, $err) = &get_url($url_purge);
            print STDERR "[$$] server[$server], url_purge[$url_purge], status[$err]\n";
        };
    };
    close PURGEFILE;

    # Se intenta realizar el Global Purge, si aplica
    if($prontus_varglb::VARNISH_GLOBAL_PURGE) {
        my @arr = split( /[\n\r]/, $prontus_varglb::VARNISH_GLOBAL_PURGE);
        foreach my $path (@arr) {
            next unless($path);
            next unless($path =~ /^\//); # debe empezar con /
            foreach my $server (keys %prontus_varglb::VARNISH_SERVER_NAME) {
                my $url_purge = "http://$server$path";
                my ($resp, $err) = &get_url($url_purge);
                print STDERR "[$$] global purge -> server[$server], url_purge[$url_purge], status[$err]\n";
            };
        };
    };
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
