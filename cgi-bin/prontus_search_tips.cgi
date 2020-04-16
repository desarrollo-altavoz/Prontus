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
    $pathLibs = $Bin;
    unshift(@INC, $pathLibs);
    require 'dir_cgi.pm';

    $pathLibs =~ s/(\/)[^\/]+$/\1$DIR_CGI_CPAN/;
    unshift(@INC,$pathLibs);
}

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use strict;
use lib_maxrunning;
use lib_prontus;
use lib_search;
use glib_html_02;
use lib_ipcheck;
use prontus_varglb; &prontus_varglb::init();
use glib_cgi_04;
use glib_fildir_02;

my (%FORM, %TIPS, %CFG);

main: {
    &glib_cgi_04::new();

    print "Content-Type: application/json\n\n";

    # Soporta un maximo de n copias corriendo.
    if (&lib_maxrunning::maxExcedido(5)) {
        print "[]";
        exit;
    }

    $FORM{"search_prontus"} = &glib_cgi_04::param("search_prontus");
    $FORM{"search_texto"} = lc &glib_cgi_04::param("search_texto");

    $FORM{"search_texto"} = &lib_search::notildesUtf8($FORM{"search_texto"});
    $FORM{"search_texto"} = lc $FORM{"search_texto"};
    $FORM{"search_texto"} =~ s/[^0-9a-z ]//g; # elimina todos los caracteres no palabra
    $FORM{"search_texto"} =~ s/ +/ /g; # quitar doble espacios.

    if(! &lib_prontus::valida_prontus($FORM{"search_prontus"})) {
      print STDERR "Directorio Prontus no válido [".$FORM{"search_prontus"}."]\n";
      print "[]";
      exit;
    }
    # $FORM{"search_prontus"} =~ s/[^0-9a-zA-Z_-]//g;

    # Validar prontus.
    my $path_to_prontus = "$prontus_varglb::DIR_SERVER/$FORM{'search_prontus'}";
    exit if (!-d $path_to_prontus);
    exit if (!-f "$path_to_prontus/cpan/$FORM{'search_prontus'}-id.cfg");

    %CFG = &lib_search::get_config("$path_to_prontus/cpan/buscador_prontus.cfg");

    # Validacion y gestion de ip bloqueada
    my $dir_ip_control = "ip_control_captcha_prontus"; # dentro del prontus_temp
    my $user_ip = $ENV{'REMOTE_ADDR'};
    my $maxrequest_por_ip = $CFG{'SEARCHTIPS_MAXREQUESTXIP'}; # numero maximo de peticiones por IP.
    my $bloqueoip_interval = 60;
    my $bloquear_ip = &lib_ipcheck::check_bloqueo_ip($dir_ip_control, $user_ip, $maxrequest_por_ip, $bloqueoip_interval);
    if ($bloquear_ip) {
        print "[]";
        exit;
    }

    my $dir_search_tips_cache = "$path_to_prontus/cpan/data/cache/search_tips";
    my $dir_search = "$path_to_prontus/cpan/data/search/$FORM{'search_prontus'}";
    my @words_idx_files = glob("$dir_search/*/words.idx");

    &glib_fildir_02::check_dir($dir_search_tips_cache);

    my @search_texto_array = split(" ", $FORM{"search_texto"});
    my ($search_texto, $search_result_prefix);
    $search_texto = $search_texto_array[0];
    $search_texto = $search_texto_array[$#search_texto_array] if ($#search_texto_array > 0);
    pop @search_texto_array;
    $search_result_prefix = join(" ", @search_texto_array);

    # Elimina archivos antiguos.
    &garbage_collector($dir_search_tips_cache);
    # print "search_texto_first[$search_texto_first] search_texto_last[$search_texto_last]\n";
    # print "search_texto[$search_texto]\n";

    if ((length $search_texto) < $CFG{'SEARCHTIPS_MINLEN'}) {
        print "[\"$FORM{'search_texto'}\"]";
        exit;
    }

    my $cache = &buscar_cache($dir_search_tips_cache, $search_texto);
    if ($cache) {
        $cache =~ s/([\[|,]")/\1$search_result_prefix /ig if ($search_result_prefix);

        print $cache;
        exit;
    }

    foreach my $words_idx_file (@words_idx_files) {
        &search($words_idx_file, $search_texto);
    }

    my $num_tips = keys %TIPS;

    if ($num_tips) {
        my $to_cache = "[\"$search_texto\",";
        foreach my $tip (sort keys(%TIPS)) {
            next if ($tip eq $search_texto);
            $to_cache .= "\"$tip\",";
        }

        $to_cache = substr($to_cache, 0, (length $to_cache) - 1);
        $to_cache .= "]";

        &guardar_cache($search_texto, $to_cache, $dir_search_tips_cache) if($num_tips > 1);
        $to_cache =~ s/([\[|,]")/\1$search_result_prefix /ig if ($search_result_prefix);

        print $to_cache;
        exit;
    }

    print "[\"$FORM{'search_texto'}\"]";
    exit;
}


sub search {
  my($archivo, $key) = @_;
  my $key_len = length $key;
  open ARCHIVO, "<$archivo";

  while (<ARCHIVO>) {
    my $linea = $_;
    chomp($linea);
    my ($word, $idx) = split(/=/, $linea);

    next if (length $word < $key_len);

    if ($word =~ /^$key/) {
        $TIPS{$word} = $idx if (!$TIPS{$word});
    }

    return if ((keys %TIPS) >= $CFG{'SEARCHTIPS_MAXRESULT'});
  }
}

sub guardar_cache {
    my $key = $_[0];
    my $buffer = $_[1];
    my $dir_search_tips_cache = $_[2];
    my $first_letter = substr($key, 0, 1);
    my $file = "$dir_search_tips_cache/$first_letter/$key\.txt";

    &glib_fildir_02::check_dir("$dir_search_tips_cache/$first_letter");
    &glib_fildir_02::write_file($file, $buffer);
}

sub buscar_cache {
    my $dir_search_tips_cache = $_[0];
    my $key = $_[1];
    my $first_letter = substr($key, 0, 1);

    &glib_fildir_02::check_dir("$dir_search_tips_cache/$first_letter");

    my $file = "$dir_search_tips_cache/$first_letter/$key.txt";
    if (-f $file) {
        my $mtime = (stat($file))[9];
        if ((time - $mtime) > $CFG{'SEARCHTIPS_DURACION_CACHE'}) {
            unlink $file;
        } else {
            my $buffer = &glib_fildir_02::read_file($file);
            return $buffer;
        }
    }

    return;
}

sub garbage_collector {
    my $dir_search_tips_cache = $_[0];
    my @listado = glob("$dir_search_tips_cache/*");
    foreach my $dir (@listado) {
        my @archivos = glob("$dir/*.txt");
        foreach my $archivo (@archivos) {
            my $mtime = (stat($archivo))[9];
            if ((time - $mtime) > $CFG{'SEARCHTIPS_DURACION_CACHE'}) {
                unlink $archivo;
            }
        }
    }
}
