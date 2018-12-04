#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# Realiza una revision en el sistema para ver si los modulos perl
# requeridos por Prontus estan presentes.

# Invocaciones:
# - por web: /cgi-cpn/prontus_check_platform.cgi
# - por S.O.: perl prontus_check_platform.cgi
# En ambas modalidades el resultado es identico.

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use strict;
use prontus_varglb;
#~ use lib_prontus;
&prontus_varglb::init();

$| = 1;

# ---------------------------------------
# Check versions of dependencies.  0 for version = any version acceptible
my $MODULES = [
  {name => 'DBI', version => '1.50'},

  {name => 'DBD::mysql', version => '3.0002'},

  # {name => 'DBD::SQLite2',version => '0.33'},

  {name => 'GD',version => '2.30'},

  {name => 'JSON',version => '1.14'},

  {name => 'LockFile::Simple',version => '0.205'},

  {name => 'Mail::Sender',version => '0.8.13'},

  {name => 'XML::Parser',version => '2.34'},

  {name => 'HTTP::Response',version => '1.53',from => 'libwww'},

  {name => 'LWP::UserAgent',version => '2.033',from => 'libwww'},

  {name => 'Net::DNS', version => '0.65'},

  {name => 'URI::Escape', version => '3.20'},

  {name => 'PHP::Session', version => '0.26'},

  {name => 'Digest::SHA', version => '5.60'}


];

# ---------------------------------------
my $ambiente_web;
main: {

  if ($ENV{'SERVER_NAME'} ne '') {
    $ambiente_web = 1;
  };


  print "Content-Type: text/html\n\n" if ($ambiente_web);
  print "<style type=\"text/css\">.check-error {color:#d00;}</style>" if ($ambiente_web);
  print "<center><b>" if ($ambiente_web);
  print "\n" . &lib_language::_msg_prontus('_prontus_check_platform') . "\n";
  print "</b></center>" if ($ambiente_web);
  print "<pre><b>" if ($ambiente_web);
  print &lib_language::_msg_prontus('_checking_perl_modules');
  print "</b>" if ($ambiente_web);

  # S.O.
  my $os = uc $^O; # solo esta en algunas plataformas
  print &lib_language::_msg_prontus('_operative_system') . ": $os\n";

  if ($] < 5.008) {
    print &lib_language::_msg_prontus('_error_perl_version');
    print "</pre>" if ($ambiente_web);
    exit;
  };

  # Perl
  my $perlv = $];
  $perlv =~ s/\.0+/\./;
  $perlv =~ s/0+([1-9]+)$/\.\1/;
  print &lib_language::_msg_prontus('_perl_version') . ": $perlv " . &lib_language::_msg_prontus('_msg_generic_ok') . "\n";

  my %missing = ();

  foreach my $module (@{$MODULES}) {
      unless (have_vers($module->{name}, $module->{version}, $module->{from})) {
          $missing{$module->{name}} = $module->{version};
      }
  }

  # chequeo de xcoding
  my @paths_ffmpeg;

  # Se busca en las rutas especificadas en la variable de entorno PATH.
  my $str = "echo \$PATH";
  my $ret_path = `$str`;
  $ret_path =~ s/\n//sg;
  $ret_path =~ s/\t//sg;
  $ret_path =~ s/\s//sg;
  $ret_path =~ s/\r//sg;

  if ($ret_path) {
    @paths_ffmpeg = split(/:/, $ret_path);
  } else {
    push @paths_ffmpeg, '/usr/local/bin/ffmpeg';
    push @paths_ffmpeg, '/usr/bin/ffmpeg';
  };

  print "\n<b>" if ($ambiente_web);
  print &lib_language::_msg_prontus('_checking_transcode_support');
  print "</b>" if ($ambiente_web);

#    # Se comprueba presencia de Python
#    printf("* %28s %-12s ", 'Python', '');
#    my $resp3 = `python -V 2>&1`;
#    $resp3 =~ s/(^[\s\n]+|[\s\n]+$)//isg;
#    if($resp3 =~ /^Python [0-9]/i) {
#      print "ok ($resp3)\n";
#    } else {
#      print "<span class=\"check-error\">No se ha encontrado Pyhton en el Sistema [$resp3]</span>\n";
#    }

  # ffmpeg
  # printf("* %28s %-12s ", 'ffmpeg', '');
  my $found_path_ffmpeg = 0;
  foreach my $path_ffmpeg (@paths_ffmpeg) {

    if (-f "$path_ffmpeg/ffmpeg") {
        $found_path_ffmpeg = 1;
        &check_xcoding("$path_ffmpeg/ffmpeg");
    };
  };

  if (!$found_path_ffmpeg) {
    print "<span class=\"check-error\">" if ($ambiente_web);
    print &lib_language::_msg_prontus('_ffmpeg_not_installed');
    print "<br>" if ($ambiente_web);
    print &lib_language::_msg_prontus('_ffmpeg_viewed_path');
    print "<br>" if ($ambiente_web);
    print "$paths_ffmpeg[0] " . &lib_language::_msg_prontus('_and') . " $paths_ffmpeg[1]\n";
    print "</span>\n" if ($ambiente_web);
  };

  print &lib_language::_msg_prontus('_end');
  print "</pre>" if ($ambiente_web);

}; # main

# ---------------------------------------
# ------------- SUBRUTINAS --------------
# ---------------------------------------

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

# ---------------------------------------
# This was originally clipped from the libnet Makefile.PL, adapted here to
# use the above vers_cmp routine for accurate version checking.
sub have_vers {
  my ($pkg, $wanted, $realname) = @_;
  my ($msg, $vnum, $vstr);
  my $pkg4display = $pkg;
  $pkg4display .= "($realname)" if ($realname);
  no strict 'refs';

  my $version = !$wanted?'(any version)':"(v$wanted)";

  printf(" * %28s %-12s ", $pkg4display, !$wanted?'(any)':"(v$wanted)");

  # Modules may change $SIG{__DIE__} and $SIG{__WARN__}, so localise them here
  # so that later errors display 'normally'
  local $::SIG{__DIE__};
  local $::SIG{__WARN__};

  eval "require $pkg;";

  # do this twice to avoid a "used only once" error for these vars
  $vnum = ${"${pkg}::VERSION"} || ${"${pkg}::Version"} || 0;
  $vnum = ${"${pkg}::VERSION"} || ${"${pkg}::Version"} || 0;
  $vnum = -1 if $@;

  if ($vnum eq "-1") { # string compare just in case it's non-numeric
    $vstr = "fail (not found)";
  }
  elsif (vers_cmp($vnum,"0") > -1) {
    $vstr = "(found v$vnum)";
  }
  else {
    $vstr = "(unknown version)";
  }

  my $vok = (vers_cmp($vnum,$wanted) > -1);

  my $error = "error $vstr\n";
  $error = "<span class=\"check-error\">$error</span>\n" if ($ambiente_web);
  print ((($vok) ? "ok $vstr\n" : $error));

  if ($pkg eq 'GD') {
    &check_soporte_gd('gif');

    &check_soporte_gd('jpeg');

    &check_soporte_gd('png');

  };

  return $vok;
};

# ---------------------------------------
# can checks if the object or class has a method called METHOD. If it does then a reference to the sub is returned.
# If it does not then undef is returned. This includes methods inherited or imported by $obj, CLASS, or VAL.
sub check_soporte_gd { # jpeg, libungif y libpng
  my $format = $_[0];
  my $nomlib;
  $nomlib = 'jpeg' if ($format eq 'jpeg');
  $nomlib = 'libungif' if ($format eq 'gif');
  $nomlib = 'libpng' if ($format eq 'png');
  printf(" * %28s %-12s ", "GD - soporte $format", "($nomlib)");
  if (GD::Image->can($format)) {
    print &lib_language::_msg_prontus('_msg_generic_ok') . "\n";
  }
  else {
    print "not found\n";
  };
};

# ---------------------------------------
sub check_xcoding {
  my $path_ffmpeg = shift;

  print &lib_language::_msg_prontus('_checking_support_with') . " $path_ffmpeg\n";
  my $xcoding_ver = '0.5.2';

  # Primero se chequea la version
  my $resp = `$path_ffmpeg -version 2>&1`;
  print STDERR '['.$resp.']';
  if($resp =~ /^FFmpeg (version | |)([^\s,]+)/i) {
    my $ver = $2;
    printf(" * %28s %-12s ", 'FFmpeg', "($xcoding_ver)");

    if($ver =~ /\d+\.\d+\.\d+/) {
      my $vok = (vers_cmp($ver,$xcoding_ver) > -1);
      print ((($vok) ? &lib_language::_msg_prontus('_msg_generic_ok') ." (found $ver)\n" : "<span class=\"check-error\">" . &lib_language::_msg_prontus('_msg_generic_error') . " (found $ver)</span>\n"));

    } elsif($resp =~ /(built on .*?) with/) {
      my $built = $1;
      print "<span class=\"check-error\">" . &lib_language::_msg_prontus('_error_compare_version') . "</span>\n";
      printf(" * %42s", '');
      print "<span class=\"check-error\">($built)</span>\n";
    } else {
      print "<span class=\"check-error\">" . &lib_language::_msg_prontus('_error_compare_version') . " ($ver)</span>\n";
    }

    # Se comprueba soporte para libx264
    printf(" * %28s %-12s ", &lib_language::_msg_prontus('_ffmpeg_support_libx264'), '');
    if($resp =~ /--enable-libx264/) {
      print &lib_language::_msg_prontus('_msg_generic_ok') . "\n";
    } else {
      my $resp = `$path_ffmpeg -codecs 2> /dev/null | grep x264`;
      if($resp ne '') {
        print &lib_language::_msg_prontus('_msg_generic_ok') . "\n";
      } else {
        print "<span class=\"check-error\">" if ($ambiente_web);
        print &lib_language::_msg_prontus('_not_enabled');
        print "</span>\n" if ($ambiente_web);
      };
    }

    # Se comprueba soporte para libfaac
    printf(" * %28s %-12s ", &lib_language::_msg_prontus('_ffmpeg_support_libfaac'), '');
    if($resp =~ /--enable-libfaac/) {
      print &lib_language::_msg_prontus('_msg_generic_ok') . "\n";
    } else {
      my $resp = `$path_ffmpeg -codecs 2> /dev/null | grep libfaac`;
      if($resp ne '') {
        print &lib_language::_msg_prontus('_msg_generic_ok') . "\n";
      } else {
        print "<span class=\"check-error\">" if ($ambiente_web);
        print &lib_language::_msg_prontus('_not_enabled');
        print "</span>" if ($ambiente_web);
      };
    };

    # Se comprueba soporte para libfdk_aac
    printf(" * %28s %-12s ", &lib_language::_msg_prontus('_ffmpeg_support_libfdk'), '');
    if($resp =~ /--enable-libfdk-aac/) {
      print &lib_language::_msg_prontus('_msg_generic_ok') ."\n";
    } else {
      my $resp = `$path_ffmpeg -codecs 2> /dev/null | grep libfdk_aac`;
      if($resp ne '') {
        print &lib_language::_msg_prontus('_msg_generic_ok') ."\n";
      } else {
        print "<span class=\"check-error\">" if ($ambiente_web);
        print &lib_language::_msg_prontus('_not_enabled');
        print "</span>" if ($ambiente_web);
      };
    };

    # Se comprueba presencia de la libx264
    printf(" * %28s %-12s ", &lib_language::_msg_prontus('_lib_x264'), '');
    my $resp2 = `ls /usr/local/lib/ | grep libx264`;
    $resp2 =~ s/^\s+|\s$//isg;
    if($resp2) {
      $resp2 =~ s/\s+$//ig;
      $resp2 =~ s/\s+/, /ig;
      print &lib_language::_msg_prontus('_msg_generic_ok') . " ($resp2)\n";
    } else {
      print "<span class=\"check-error\">" if ($ambiente_web);
      print "/usr/local/lib/ -> ". &lib_language::_msg_prontus('_not_found');
      print "</span>" if ($ambiente_web);

      printf(" * %42s", '');
      $resp2 = `ls /usr/lib/ | grep libx264`;
      if($resp2) {
        $resp2
         =~ s/\s+$//ig;
        $resp2 =~ s/\s+/, /ig;
        print "/usr/lib/       -> ". &lib_language::_msg_prontus('_msg_generic_ok') . " ($resp2)\n";
      } else {
        print "<span class=\"check-error\">" if ($ambiente_web);
        print "/usr/lib/       -> " . &lib_language::_msg_prontus('_not_found');
        print "</span>" if ($ambiente_web);

        printf(" * %42s", '');
        $resp2 = `ls /usr/bin/ | grep x264`;
        if($resp2) {
          $resp2 =~ s/\s+$//ig;
          $resp2 =~ s/\s+/, /ig;
          print "/usr/bin/       -> ok ($resp2)\n";
        } else {
          print "<span class=\"check-error\">" if ($ambiente_web);
          print "/usr/bin/       -> " . &lib_language::_msg_prontus('_not_found';)
          print "</span>" if ($ambiente_web);
        }
      }
    }

    my $url_manual = 'http://develop.prontus.cl';
    my $version = $prontus_varglb::VERSION_PRONTUS;
    $version =~ s/^(\d+)\.(\d+)\.(\d+).+$/\1_\2/;
    my $url_manual_desa = $url_manual . '/prontus_desarrollo_v' . $version;

    my $msg = &lib_language::_msg_prontus('_msg_important_1');
    $msg .= &lib_language::_msg_prontus('_mgs_important_2') . " <a href=\"$url_manual_desa\" target=\"_blank\">" . &lib_language::_msg_prontus('_develop_manual') . "</a>, ";
    $msg .= &lib_language::_msg_prontus('_develop_manual_route');
    print "<br>".$msg."<br><br>" if ($ambiente_web);

  } else {
    print "FFmpeg... <span class=\"check-error\">" if ($ambiente_web);
    print &lib_language::_msg_prontus('_unable_read_version') . "\n";
    print "</span>\n" if ($ambiente_web);
    return;
  }

}
# ----------
