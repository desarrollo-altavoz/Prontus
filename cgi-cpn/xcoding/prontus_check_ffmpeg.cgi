#!/usr/bin/perl

# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Comprueba la ruta entregada de ffmpeg y revisa la disponibilidad
# de librerias/codecs
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como cgi, usando metodo GET o POST. Los parametros son:
# path - carpeta en la que se enceuntra ffmpeg
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 13/05/2015 - EAG - Primera version.
# 1.1.0 - 04/06/2015 - EAG - Se agregan mensajes de compatibilidad y sugerencias
# -------------------------------BEGIN SCRIPT--------------------
BEGIN {
    use FindBin '$Bin';
    my $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/xcoding$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ---------------------------------------------------------------
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use strict;
use prontus_varglb; &prontus_varglb::init();
use JSON;
use glib_html_02;
use glib_cgi_04;
use lib_prontus;
#~ use utf8;
use Data::Dumper;

my %FORM;        # Contenido del formulario de invocacion.

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    &glib_cgi_04::set_formvar('path', \%FORM);
    &glib_cgi_04::set_formvar('prontus_id', \%FORM);

    # Valida datos de entrada
    my $msg_err;
    $msg_err = &lib_language::_msg_prontus('invalid_prontus_id_paratemer') if (! &lib_prontus::valida_prontus($FORM{'prontus_id'}));
    $msg_err = &lib_language::_msg_prontus('invalid_prontus_id_paratemer') if (!-d "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}");

    &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_msg_generic_error').": $msg_err", 'exit=1,ctype=1') if ($msg_err);

    # Path conf y load config de prontus
    my $path_conf = "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;

    # User check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    print "Cache-Control: no-cache, must-revalidate\r\n";
    print "Content-Type: text/html\n\n";
    #~ print "Content-type: application/json\n\n";

    print "<style type=\"text/css\">.check-error {color:#d00;}</style>\n";
    print "<center><b>";
    print "Prontus - Verificar FFMPEG";
    print "</b></center>";
    print "<pre><b>";
    print &lib_language::_msg_prontus('_check_ffmpeg_config')." ...\n";
    print "</b>";

    my $os = uc $^O; # solo esta en algunas plataformas
    print &lib_language::_msg_prontus('_os').": $os\n";

    printf(" * %28s %-12s ", &lib_language::_msg_prontus('_directory')." $FORM{'path'}", '' );
    if ( -d $FORM{'path'}) {
        print "ok\n";
    } else {
        print "<span class=\"check-error\">".&lib_language::_msg_prontus('_error_no_directory')."</span>\n";
        print "</pre>";
        exit;
    }
    print "\n";

    my $path_ffmpeg = $FORM{'path'}."/ffmpeg";
    &check_xcoding($path_ffmpeg);
    print "</pre>";
    exit;
}
# -------------------------------------------------------------------#
sub check_xcoding {
    my $path_ffmpeg = shift;

    print &lib_language::_msg_prontus('_checking_support')." $path_ffmpeg\n";
    my $xcoding_ver = '0.5.2';

    # Primero se chequea la version
    my $resp = `$path_ffmpeg -version 2>&1`;
    print STDERR '['.$resp.']';
    if($resp =~ /^FFmpeg (version | |)([^\s,]+)/i) {
        my $x264 = 0;
        my $faac = 0;
        my $fdk = 0;
        my $ver = $2;
        my $origver = $ver;
        printf(" * %28s %-12s ", 'FFmpeg', "($xcoding_ver)");

        # eliminamos el texto '.git' si es una version de git, lo reemplazamos por un 0
        $ver =~ s/(git)/0/;

        if($ver =~ /\d+\.\d+\.\d+/) {
            my $vok = (vers_cmp($ver,$xcoding_ver) > -1);
            print ((($vok) ? "ok (found $origver)\n" : "<span class=\"check-error\">error (found $origver)</span>\n"));

        } elsif($resp =~ /(built on .*?) with/) {
            my $built = $1;
            print "<span class=\"check-error\">".&lib_language::_msg_prontus('_unable_version_comparison')."</span>\n";
            printf(" * %42s", '');
            print "<span class=\"check-error\">($built)</span>\n";
        } else {
            print "<span class=\"check-error\">"&lib_language::_msg_prontus('_unable_version_comparison')" ($origver)</span>\n";
        }

        # Se comprueba soporte para libx264
        printf(" * %28s %-12s ", 'FFmpeg - soporte libx264', '');
        my $test = `$path_ffmpeg -codecs 2> /dev/null | grep x264`;
        if ($test ne '') {
            $x264 = 1;
            print "ok\n";
        } else {
            print "<span class=\"check-error\">";
            print "not enabled";
            print "</span>\n";
        };

        # Se comprueba soporte para libfaac
        printf(" * %28s %-12s ", 'FFmpeg - soporte libfaac', '');
        $test = '';
        $test = `$path_ffmpeg -codecs 2> /dev/null | grep libfaac`;
        if ($test ne '') {
            $faac = 1;
            print "ok\n";
        } else {
            print "<span class=\"check-error\">";
            print "not enabled";
            print "</span>\n";
        };

        # Se comprueba soporte para libfdk_aac
        printf(" * %28s %-12s ", 'FFmpeg - soporte libfdk_aac', '');
        $test = '';
        $test = `$path_ffmpeg -codecs 2> /dev/null | grep libfdk_aac`;
        if($test ne '') {
            $fdk = 1;
            print "ok\n";
        } else {
            print "<span class=\"check-error\">";
            print "not enabled";
            print "</span>\n";
        };

        print "\n\n";

        if ($x264 && ($faac || $fdk)) {
            if ($fdk && !$faac) {
                print " <span class=\"check-error\">".&lib_language::_msg_prontus('_must_be_activated')." USAR_LIB_FDK, ".&lib_language::_msg_prontus('_to_use_codec')." AAC.</span>\n";
            } elsif ($fdk) {
                print &lib_language::_msg_prontus('_activate')." USAR_LIB_FDK, ".&lib_language::_msg_prontus('_to_use')." libfdk_aac.\n";
            }
            if (vers_cmp($ver,'1.0.0') > -1) {
                print &lib_language::_msg_prontus('_activate_advanced_transcoding').", ADVANCED_XCODING. (FFmpeg version: $origver)\n";
                print &lib_language::_msg_prontus('_activate_generation_HLS').", GEN_HLS.\n";
            }
            if (vers_cmp($ver,'1.2.12') > -1) {
                print &lib_language::_msg_prontus('_enable_improved_accuracy_generating_HLS').", PRECISION_HLS. (FFmpeg version: $origver)\n";
            }
            if (vers_cmp($ver,'2.0.0') < 1) {
                print "\n ".&lib_language::_msg_prontus('_recommend_ffmpeg_version').". (FFmpeg version: $origver)\n";
            }
        } else {
            print "<span class=\"check-error\">";
            print &lib_language::_msg_prontus('_media_required_not_found');
            print "</span>\n";
        }

        my $url_manual = 'http://develop.prontus.cl';
        my $version = $prontus_varglb::VERSION_PRONTUS;
        $version =~ s/^(\d+)\.(\d+)\.(\d+).+$/$1_$2/;
        my $url_manual_desa = $url_manual . '/prontus_desarrollo_v' . $version;

        my $msg = "<u>".&lib_language::_msg_prontus('_important').":</u> ".&lib_language::_msg_prontus('_transcodig_failure_warning')." <br>".&lib_language::_msg_prontus('_fulfilling_requirements');
        $msg .= &lib_language::_msg_prontus('_more_information')." <br>al <a href=\"$url_manual_desa\" target=\"_blank\">".&lib_language::_msg_prontus('_development_manual')."</a>, ";
        $msg .= &lib_language::_msg_prontus('_section')."\"".&lib_language::_msg_prontus('_instalation')."\", ".&lib_language::_msg_prontus('_sub_section')." \"".&lib_language::_msg_prontus('_transcoding_support')."\"";
        print "<br>".$msg."<br><br>";

    } else {
        print "FFmpeg... <span class=\"check-error\">";
        print &lib_language::_msg_prontus('_unable_read_version')."\n";
        print "</span>\n";
        return;
    }

}
# ----------
# vers_cmp is adapted from Sort::Versions 1.3 1996/07/11 13:37:00 kjahds,
# which is not included with Perl by default, hence the need to copy it here.
# Seems silly to require it when this is the only place we need it...
sub vers_cmp {
  if (@_ < 2) { die "not enough parameters for vers_cmp" }
  if (@_ > 2) { die "too many parameters for vers_cmp" }
  my ($a, $b) = @_;
  my (@A) = ($a =~ /(\.|\d+|[^\.\d]+)/g);
  my (@B) = ($b =~ /(\.|\d+|[^\.\d]+)/g);
  my ($A,$B);
  while (@A and @B) {
    $A = shift @A;
    $B = shift @B;
    if ($A eq "." and $B eq ".") {
      next;
    } elsif ( $A eq "." ) {
      return -1;
    } elsif ( $B eq "." ) {
      return 1;
    } elsif ($A =~ /^\d+$/ and $B =~ /^\d+$/) {
      return $A <=> $B if $A <=> $B;
    } else {
      $A = uc $A;
      $B = uc $B;
      return $A cmp $B if $A cmp $B;
    }
  }
  @A <=> @B;
};
