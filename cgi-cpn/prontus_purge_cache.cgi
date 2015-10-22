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

END {
    &delete_semaphore();
};

$SIG{INT} = \&signal_callback;
$SIG{TERM} = \&signal_callback;

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use strict;
use LWP::UserAgent;
use LWP::ConnCache;
use HTTP::Response;
use glib_fildir_02;
use Time::HiRes qw(sleep);

close STDOUT;

my %FORM;
my $ua;
my $dir_semaf;
my %PURGED_FILES;
my $FILE_LIFE_SEGS = 5;
my $RUNNING = 0;
my @SUBDOMAINS = ('www', 'm');

main: {
    $FORM{'prontus_id'} = $ARGV[0];

    &valida_params();

    # Carga variables de configuracion de prontus.
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus_id'});
    &lib_prontus::load_config( &lib_prontus::ajusta_pathconf($relpath_conf) );

    $dir_semaf = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/data/semaforos";
    &glib_fildir_02::check_dir($dir_semaf) if (!-d $dir_semaf);

    if (-f "$dir_semaf/purge_cache.lck") {
        my $mtime = (stat("$dir_semaf/purge_cache.lck"))[9];
        my $now = time;
        my $diff = $now - $mtime;

        if ($diff > 1800) { # 30 min.
            print STDERR "[$$] Semaforo muy antiguo, eliminando...";
            unlink "$dir_semaf/purge_cache.lck";

            my $res = `ps auxww |grep 'prontus_purge_cache.cgi $prontus_varglb::PRONTUS_ID' | grep -v grep | wc -l`;
            chomp($res);

            if ($res) {
                system('kill -9 `ps auxww | grep \'prontus_purge_cache.cgi ' . $prontus_varglb::PRONTUS_ID . '\' | grep -v grep | awk \'{print $2}\' | grep -v ' . $$ . '`');
            };
        } else {
            exit; # ya existe un proceso.
        };
    };

    # escribe el semaforo y ya esta corriendo.
    &glib_fildir_02::write_file("$dir_semaf/purge_cache.lck", $$);
    $RUNNING = 1;

    my $espera_segs = 5;
    $ua = new LWP::UserAgent;
    $ua->timeout($espera_segs); # segs # default es 180
    $ua->agent('Mozilla/5.0 (Windows; U; Windows NT 5.1; es-ES; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'); # default es "libwww-perl/#.##"
    my $conn_cache = LWP::ConnCache->new;
    $ua->conn_cache($conn_cache);

    my $dir_purgepend = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/purgepend";
    my @purgepend_chunklist = &get_purgepend_list($dir_purgepend);
    my $chunk;

    while (defined($chunk = shift @purgepend_chunklist)) {
        my @chunk = @{$chunk};
        my %filelist;

        foreach my $file (@chunk) {
            if (-f $file) {
                print STDERR "[$$] Procesando cola [$file]...\n";
                %filelist = &get_filelist_hash($file, \%filelist);
            };
        };

        my $num_of_files = keys %filelist;

        print STDERR "[$$] Archivos a purgear: $num_of_files\n";

        if ($num_of_files) {
            &purge(\%filelist);
        };

        # Borrar archivos
        foreach my $file (@chunk) {
            unlink $file if (-f $file);
        };

        if (!scalar @purgepend_chunklist) {
            print STDERR "[$$] Buscando mas archivos en la cola...\n";
            @purgepend_chunklist = &get_purgepend_list($dir_purgepend);
        };
    };

    print STDERR "[$$] Fin.\n";

    unlink "$dir_semaf/purge_cache.lck";
    exit;
};

sub get_purgepend_list {
    my $dir = $_[0];

    my $dir_purgepend = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/purgepend";
    my @files = glob("$dir_purgepend/*.txt");
    my @chunks;

    # Dividir array de archivos.
    push @chunks, [splice @files, 0, 50] while (@files); # grupos de 50 archivos.

    return @chunks;
};

sub get_filelist_hash {
    my $file = $_[0];
    my %hash = %{$_[1]};

    open (PURGEFILE, "<$file");

    foreach my $filetopurge (<PURGEFILE>) {
        $filetopurge =~ s/\n//is;
        my $relpath = &lib_prontus::remove_front_string($filetopurge, $prontus_varglb::DIR_SERVER);

        $hash{$relpath} = time if (!exists $hash{$relpath});
    };

    return %hash;
};

sub valida_params {
    if ($FORM{'prontus_id'} eq '') {
        print STDERR "[$$] Debe indicar el nombre del Prontus.\n";
        exit;
    };
};

sub purge {
    my %hash = %{$_[0]};
    my $purge_cloudflare = 0;
    my $counter_cf = 0;
    my @cloudflareZones;

    if ($prontus_varglb::CLOUDFLARE eq 'SI' && $prontus_varglb::CLOUDFLARE_API_URL ne '' && $prontus_varglb::CLOUDFLARE_API_KEY ne '' && $prontus_varglb::CLOUDFLARE_EMAIL ne '' && $prontus_varglb::CLOUDFLARE_ZONE ne '') {
        $purge_cloudflare = 1;
        @cloudflareZones = split(/[\n\r]/, $prontus_varglb::CLOUDFLARE_ZONE);
    };

    if ($purge_cloudflare) {
        print STDERR "[$$] Cloudflare activado. CLOUDFLARE_API_URL[$prontus_varglb::CLOUDFLARE_API_URL]\n";

        # Agregar purge global al listado.
        if ($prontus_varglb::CLOUDFLARE_GLOBAL_PURGE) {
            my @arr = split(/[\n\r]/, $prontus_varglb::CLOUDFLARE_GLOBAL_PURGE);
            
            foreach my $path (@arr) {
                next unless($path);
                next if ($path !~ /^\//); # debe empezar con /

                $hash{$path} = time if (!exists $hash{$path});
            }      
        }

        # v1.
        if ($prontus_varglb::CLOUDFLARE_API_URL eq 'https://www.cloudflare.com/api_json.html') {
            foreach my $relpath (keys %hash) {
                if (defined $PURGED_FILES{$relpath} && &check_life($PURGED_FILES{$relpath})) {
                    print STDERR "[$$] Saltando [$relpath].\n";
                    next;
                };

                $PURGED_FILES{$relpath} = time;

                my %datos_post;

                $datos_post{'a'} = 'zone_file_purge';
                $datos_post{'tkn'} = $prontus_varglb::CLOUDFLARE_API_KEY;
                $datos_post{'email'} = $prontus_varglb::CLOUDFLARE_EMAIL;

                foreach my $zone (@cloudflareZones) {
                    next if (!$zone);
                    my $url_purge = "http://$zone$relpath";

                    $datos_post{'z'} = $zone;
                    $datos_post{'url'} = $url_purge;

                    my ($resp, $err) = &http_post($prontus_varglb::CLOUDFLARE_API_URL, \%datos_post);

                    print STDERR "[$$] cloudflare: api_key[$prontus_varglb::CLOUDFLARE_API_KEY], zone[$zone] url_purge[$url_purge], status[$err] resp[$resp]\n";

                    $counter_cf++;

                    if ($counter_cf >= 100) {
                        # Actualiza fecha de modificación del semaforo en caso de que se procesen muchos archivos
                        # no llegue otro proceso y lo pise.
                        # El semaforo es util cuando el script se caiga o se quede pegado (sin actualizar mtime).
                        utime time, time, "$dir_semaf/purge_cache.lck";

                        $counter_cf = 0;
                        print STDERR "[$$] api rate limit! sleep 60 segundos...\n";
                        sleep 15; # There is a rate limit for file purges of 100 per minute. Exceeding this limit will return an error in the JSON response.
                    } else {
                        sleep 0.5; # para no bombardear la api.
                    }
                }
            }

        } elsif ($prontus_varglb::CLOUDFLARE_API_URL eq 'https://api.cloudflare.com/client/v4') {
            # Se envian a la api grupos de 30 url.
            my @archivos = (keys %hash);
            my @chunks;
            push @chunks, [splice @archivos, 0, 30] while (@archivos); # grupos de 30 archivos.

            # Obtener id de las zonas.
            my %zones_id = &get_zones_id(\@cloudflareZones);
            my %headers = (
                'Content-Type' => 'application/json',
                'X-Auth-Email' => $prontus_varglb::CLOUDFLARE_EMAIL,
                'X-Auth-Key' => $prontus_varglb::CLOUDFLARE_API_KEY
            );

            # The CloudFlare API sets a maximum of 1,200 requests in a five minute period.
            # 240 por minuto, 4 por segundo.
            if (keys %zones_id) {
                foreach my $chunk (@chunks) {
                    foreach my $zone (keys %zones_id) {
                        foreach my $sub (@SUBDOMAINS) {
                            my @files = map {"http://$sub.$zone" . $_} @{$chunk}; # agregar la zona al principio.
                            my %data = (
                                'files' => \@files,
                                'tags' => []
                            );

                            print STDERR "[$$] cloudflare purge: sub[$sub] name[$zone] id[$zones_id{$zone}] files[" . (join(",", @files)) . "]\n";

                            my $req_url = "https://api.cloudflare.com/client/v4/zones/$zones_id{$zone}/purge_cache";
                            my ($resp, $http_code) = &http_delete($req_url, \%headers, &JSON::to_json(\%data));
                        
                            if ($http_code ne '200') {
                                print STDERR "[$$] Error al hacer purge en la zona[$zone] sub[$sub] resp[$resp]\n";
                            } else {
                                my $msg = &JSON::from_json($resp);
                                print STDERR "[$$] OK.\n";
                            }
                        
                            sleep(0.25);
                        }
                    }
                }
            }
        }

    } else {
        print STDERR "[$$] Varnish activado.\n";

        # Agregar purge global al listado.
        if ($prontus_varglb::VARNISH_GLOBAL_PURGE) {
            my @arr = split( /[\n\r]/, $prontus_varglb::VARNISH_GLOBAL_PURGE);
            foreach my $path (@arr) {
                next unless($path);
                next if ($path !~ /^\//); # debe empezar con /

                $hash{$path} = time if (!exists $hash{$path});
            }
        }

        # Si no está habilitado cloudflare, se prueba con varnish.
        foreach my $relpath (keys %hash) {
            if (defined $PURGED_FILES{$relpath} && &check_life($PURGED_FILES{$relpath})) {
                print STDERR "[$$] Saltando [$relpath].\n";
                next;
            }

            $PURGED_FILES{$relpath} = time;

            foreach my $server (keys %prontus_varglb::VARNISH_SERVER_NAME) {
                next if (!$server);
                my $url_purge = "http://$server$relpath";

                my ($resp, $err) = &http_purge($url_purge);
                print STDERR "[$$] varnish: server[$server], url_purge[$url_purge], status[$err]\n";
            }
        }  
    }

    # Actualiza fecha de modificación del semaforo en caso de que se procesen muchos archivos
    # no llegue otro proceso y lo pise.
    # El semaforo es util cuando el script se caiga o se quede pegado (sin actualizar mtime).
    utime time, time, "$dir_semaf/purge_cache.lck";
};

sub get_zones_id {
    my @zones = @{$_[0]};
    my $req_url = $prontus_varglb::CLOUDFLARE_API_URL . '/zones?status=active&per_page=50'; # solo v4.
    my %headers = (
        'Content-Type' => 'application/json',
        'X-Auth-Email' => $prontus_varglb::CLOUDFLARE_EMAIL,
        'X-Auth-Key' => $prontus_varglb::CLOUDFLARE_API_KEY
    );
    my %zones_id;
    my ($resp, $http_code) = &http_get($req_url, \%headers);

    if ($http_code ne '200') {
        print STDERR "[$$] No se pudo obtener el listado de zonas. http_code[$http_code] resp[$resp]\n";
    } else {
        my $json = &JSON::from_json($resp);
        #print STDERR "resp[$resp]\n";
        if (exists $json->{'success'} && $json->{'success'}) {
            foreach my $result (@{$json->{'result'}}) {
                foreach my $zone (@zones) {
                    if ($zone eq $result->{'name'}) {
                        $zones_id{$zone} = $result->{'id'};
                    }
                }
            }
        } else {
            print STDERR "[$$] No se pudo obtener el listado de zonas. http_code[$http_code] resp[$resp]\n";
        }
    }

    return %zones_id;
};

sub check_life {
    my $t = $_[0];
    my $dif = time - $t;

    if ($dif <= $FILE_LIFE_SEGS) {
        return 1;
    };

    return 0;
};

sub http_purge {
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

};

sub http_get {
    my $url = $_[0];
    my $headers_ref = $_[1];
    my %headers = %{$headers_ref};

    my $ua = LWP::UserAgent->new();
    my $req = HTTP::Request->new('GET', $url);

    foreach my $header (keys %headers) {
        $req->header($header => $headers{$header});
    };

    my $response = $ua->request($req);    

    return ($response->content, $response->code);
};

sub http_post {
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

sub http_delete {
    my $url = $_[0];
    my $headers_ref = $_[1];
    my $data = $_[2];
    my %headers = %{$headers_ref};

    my $ua = LWP::UserAgent->new();
    my $req = HTTP::Request->new('DELETE', $url);

    foreach my $header (keys %headers) {
        $req->header($header => $headers{$header});
    };

    $req->content($data) if ($data);

    my $response = $ua->request($req);    

    return ($response->content, $response->code);
};

sub signal_callback {
    print STDERR  "Terminado por signal @_\n";
    exit(0);
};

sub delete_semaphore {
    if ($RUNNING) {
        unlink "$dir_semaf/purge_cache.lck";
    };
};
