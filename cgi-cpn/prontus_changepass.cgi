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
# Procesar cambio de clave de admin.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Al final hace location a /<prontus_dir>/cpan/core/prontus_index.html
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# 2) Desde la pag. de cambio de clave: /prontus_dev/cpan/core/prontus_changepass.html
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# No registra.
# ---------------------------------------------------------------
# 1.0 - 05/2006 - Primera version.
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use glib_fildir_02;
use glib_str_02;
use lib_prontus;
use strict;
use File::Copy;
use Digest::MD5 qw(md5_hex);

# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM);
my ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL, $USERS_ID);
my $USERID;

main: {

    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    $FORM{'_usr'} = &glib_cgi_04::param('_usr');
    $FORM{'_psw'} = &glib_cgi_04::param('_psw');
    $FORM{'_new_psw'} = &glib_cgi_04::param('_new_psw');
    $FORM{'_new_psw_confirm'} = &glib_cgi_04::param('_new_psw_confirm');
    $FORM{'_email'} = &glib_cgi_04::param('_email');
    $FORM{'_token'} = &glib_cgi_04::param('_token');

    # Carga var. globales con los datos del arch. conf.
    &lib_prontus::load_config($FORM{'_path_conf'});   # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    if (&lib_prontus::open_dbm_files() ne 'ok') {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_error_open_user_files'), 'exit=1,ctype=1');
    };
    
    # Cambio de contrase�a por recuperaci�n.
    if ($FORM{'_token'} ne '' && $FORM{'_usr'} ne '') {
        if (&validacion_token()) {
            my $msg = &valida_datos();
            if ($msg) {
                &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1');
            };
            if (&is_user_valido()) {
                my $val = $prontus_varglb::USERS{$USERID};
                my ($users_nom, $users_usr, $users_psw, $users_perfil, $users_mail) = split /\|/, $val;
                $prontus_varglb::USERS{$USERID} = $users_nom . '|' .  $users_usr . '|' . md5_hex($FORM{'_new_psw'}) . '|' . $users_perfil . '|' . $users_mail;
                &lib_prontus::close_dbm_files();
                unlink "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/procs/recordarpass/$FORM{'_usr'}.txt";
                &glib_html_02::print_json_result(1, &lib_language::_msg_prontus('_pswd_change_success'), 'exit=1,ctype=1');
            } else {
                &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_user_not_valid'), 'exit=1,ctype=1');
            };
            
        } else {
            &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_token_not_valid'), 'exit=1,ctype=1');
        };
    };

    my $msg = &valida_datos();
    if ($msg) {
        &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1');
    };

    if (&user_valido() eq 'S') {
		
		my $val = $prontus_varglb::USERS{$USERID};
		my ($users_nom, $users_usr, $users_psw, $users_perfil, $users_mail) = split /\|/, $val;
        # CVI - 05/07/2012 - Ahora se usa md5 para encriptar la contrase�a
        $prontus_varglb::USERS{$USERID} = $users_nom . '|' .  $users_usr . '|' . md5_hex($FORM{'_new_psw'}) . '|' . $users_perfil . '|' . $FORM{'_email'};
        &lib_prontus::close_dbm_files();

        # Escribe archivo extras (para edit)
        &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/extra.txt", &glib_str_02::random_string(8));

        &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');

    }
    else {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_previous_user_pswd_missmatch'), 'exit=1,ctype=1');
    };


};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub valida_datos {

    if ($FORM{'_token'} eq '' && (($FORM{'_usr'} eq '') or ($FORM{'_psw'} eq ''))) {
    return &lib_language::_msg_prontus('_validation_not_valid');
    };


    if ( ($FORM{'_new_psw'} eq '') or ($FORM{'_new_psw_confirm'} eq '') ) {
    return &lib_language::_msg_prontus('_validation_enter_password');
    };

    if ($FORM{'_new_psw'} ne $FORM{'_new_psw_confirm'}) {
    return &lib_language::_msg_prontus('_validation_password_missmatch');
    };


    if ($FORM{'_new_psw'} =~ /^\s+$/) {
    return &lib_language::_msg_prontus('_validation_password_invalid_characters');
    };

    if ($FORM{'_new_psw'} !~ /^.{6,32}$/) {
    return &lib_language::_msg_prontus('_validation_min_max_password');
    # return 'Password debe estar compuesta por, al menos, 6 caracteres.';
    };

    if (lc $FORM{'_new_psw'} eq 'prontus') {
    return &lib_language::_msg_prontus('_validation_password_not_valid') . " \"$FORM{'_new_psw'}\", " . &lib_language::_msg_prontus('_validation_enter_other_password');
    };

    if ($FORM{'_token'} eq ''  && $FORM{'_email'} !~ /^[a-zA-Z\_\-\.0-9]+@[a-zA-Z\_\-0-9]+\.[0-9a-zA-Z\.\-\_]+$/) {
    return &lib_language::_msg_prontus('_validation_email_not_valid');
    };

    return '';
};

# ---------------------------------------------------------------
sub user_valido {
    my ($key, $val);

    foreach $key (keys %prontus_varglb::USERS) {
        $val = $prontus_varglb::USERS{$key};
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL) = split /\|/, $val;
        # CVI - 05/07/2012 - Ahora se usa md5 para encriptar la contrase�a
        my $crypted_pass;
        if(length($USERS_PSW) == 32) {
            $crypted_pass = md5_hex($FORM{'_psw'});
        } else {
            $crypted_pass = crypt($FORM{'_psw'}, $USERS_PSW);
        }
        if ( ($USERS_USR eq $FORM{'_usr'}) and ($crypted_pass eq $USERS_PSW) ) {
            $USERID = $key;
            return 'S';
        };
    };
    return 'N';

};

sub is_user_valido {
    my ($key, $val);
    foreach $key (keys %prontus_varglb::USERS) {
        $val = $prontus_varglb::USERS{$key};
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $val;
        if ($USERS_USR eq $FORM{'_usr'})  {
            $USERID = $key;
            return 1;
        };
    };
    return 0;
};

sub validacion_token {
    my $dirprocuser = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/procs/recordarpass/$FORM{'_usr'}.txt";
    #~ print STDERR "dirprocuser[$dirprocuser]\n";
    if (!-f $dirprocuser) {
        print "Content-Type: text/html\n\n";
        return 0;
    } else {
        my $token = &glib_fildir_02::read_file($dirprocuser);
        $token =~ s/\n//s;
        $token =~ s/\r//s;
        $token =~ s/\t//s;
        $token =~ s/ *//s;
        #~ print STDERR "token[$token]\n";
        if ($FORM{'_token'} ne $token) {
            print "Content-Type: text/html\n\n";
            return 0;
        };
    };
    return 1;
};

# -------------------------------END SCRIPT----------------------

