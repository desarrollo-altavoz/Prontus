#!/usr/bin/perl
# --------------------------------------------------------------
# Purge de caché de CloudFlare. Global o por archivos.
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
# 1.0.0 - 02/03/2015 - JOR - Primera versión
# ---------------------------------------------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use glib_cgi_04;
use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_prontus;
use lib_multiediting;

use Session;
use Update;
use strict;

my %FORM;

main: {
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    $FORM{'_path_conf'} = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'_path_conf'});
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # user no valido
    if ($prontus_varglb::USERS_ID eq '') {
        #~ &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    # Validar datos.
    if ($prontus_varglb::CLOUDFLARE eq 'NO' || $prontus_varglb::CLOUDFLARE_API_URL eq '' || $prontus_varglb::CLOUDFLARE_API_KEY eq ''
        || $prontus_varglb::CLOUDFLARE_EMAIL eq '' || $prontus_varglb::CLOUDFLARE_ZONE eq '') {
        &glib_html_02::print_json_result(0, 'Error: CloudFlare no está habilitado o los datos ingresados son insuficientes.', 'exit=1,ctype=1');
    };

    $FORM{'purge_all'} = &glib_cgi_04::param('purge_all');
    $FORM{'purge_files'} = &glib_cgi_04::param('purge_files');

    my @zoneArr = split(/[\n\r]/, $prontus_varglb::CLOUDFLARE_ZONE);

    if ($FORM{'purge_all'} eq '1') {
        # purge a todo.
        my %datos_post;
        my $zoneStatus;

        $datos_post{'a'} = 'fpurge_ts'; # 4.4 - "fpurge_ts" -- Clear CloudFlare's cache
        $datos_post{'tkn'} = $prontus_varglb::CLOUDFLARE_API_KEY;
        $datos_post{'email'} = $prontus_varglb::CLOUDFLARE_EMAIL;
        $datos_post{'v'} = '1';

        foreach my $zone (@zoneArr) {
            next if (!$zone);
            $datos_post{'z'} = $zone;

            my ($resp, $err) = &post_url($prontus_varglb::CLOUDFLARE_API_URL, \%datos_post);

            print STDERR "cloudflare purge files: api_key[$prontus_varglb::CLOUDFLARE_API_KEY], zone[$zone] status[$err] resp[$resp]\n";

            if ($err) {
                $zoneStatus .= "[$zone] ERROR: $err\n";
            } else {
                if ($resp =~ /"result": "success"/) {
                    $zoneStatus .= "[$zone] OK\n";
                } else {
                    $zoneStatus .= "[$zone] ERROR: Respuesta de CloudFlare inválida.\n";
                };
            };
        };

    } elsif ($FORM{'purge_files'} ne '') {
        # Llamar a cgi prontus_purge_cache.cgi.
        my @files = split(/\n/, $FORM{'purge_files'});

        if ((scalar @files) > 100) {
            &glib_html_02::print_json_result(0, 'Se permite un máximo de 100 archivos.', 'exit=1,ctype=1');
        };

        foreach my $file (@files) {
            next if (!$file);
            next if ($file !~ /^\//); # debe empezar con /

            print STDERR "cloudflare purge file [$file]\n";
            &lib_prontus::purge_cache($file, 1);
        };

        &lib_prontus::call_purge_proc(1); # solo purge de cloudflare.

        &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');
    };

};

sub post_url {
    my $url = $_[0];
    my $data_ref = $_[1];
    my %data = %{$data_ref};

    my $ua       = LWP::UserAgent->new();
    my $response = $ua->post( $url, \%data );

    if ($response->is_success) {
        return ($response->content, '');
    } else {
        return ('', $response->status_line);
    };

};