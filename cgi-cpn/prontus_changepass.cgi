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
use prontus_auth;

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
    $FORM{'_expired'} = &glib_cgi_04::param('_expired');

    # Carga var. globales con los datos del arch. conf.
    &lib_prontus::load_config($FORM{'_path_conf'});   # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    if (&lib_prontus::open_dbm_files() ne 'ok') {
        &glib_html_02::print_json_result(0, 'No fue posible abrir archivos de usuarios', 'exit=1,ctype=1');
    }

    # Cambio de contrase�a por recuperaci�n. contrase�a olvidada
    if ($FORM{'_token'} ne '' && $FORM{'_usr'} ne '') {
        if (&validacion_token()) {
            my $msg = &valida_datos();
            if ($msg) {
                &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1');
            };
            if (&prontus_auth::is_user_valido($FORM{'_usr'})) {
                my $change_result = &prontus_auth::save_new_password($prontus_auth::USERS_USR_ID, $FORM{'_new_psw'}, $FORM{'_email'});
                if ($change_result ne '') {
                    utf8::decode($change_result);
                    &glib_html_02::print_json_result(0, $change_result, 'exit=1,ctype=1');
                }
                unlink "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/procs/recordarpass/$FORM{'_usr'}.txt";
                &glib_html_02::print_json_result(1, 'La contrase�a se cambi� correctamente.', 'exit=1,ctype=1');
            } else {
                &glib_html_02::print_json_result(0, 'El usuario es inv�lido.', 'exit=1,ctype=1');
            };

        } else {
            &glib_html_02::print_json_result(0, 'Token inv�lido o expirado.', 'exit=1,ctype=1');
        };
    };

    # cambio de pass para admin
    my $msg = &valida_datos();
    if ($msg) {
        &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1');
    };

    my $login = &prontus_auth::check_valid_login($FORM{'_usr'}, $FORM{'_psw'});
    if ($login  >= 1) {
        my $change_result = &prontus_auth::save_new_password($prontus_auth::USERS_USR_ID, $FORM{'_new_psw'}, $FORM{'_email'});
        if ($change_result ne '') {
            utf8::decode($change_result);
            &glib_html_02::print_json_result(0, $change_result, 'exit=1,ctype=1');
        }
        # Escribe archivo extras (para edit)
        &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/extra.txt", &glib_str_02::random_string(8));

        &glib_html_02::print_json_result(1, 'La contrase�a ha sido cambiada con �xito.', 'exit=1,ctype=1');

    } else {
        &glib_html_02::print_json_result(0, 'Usuario o contrase�a anterior no corresponden', 'exit=1,ctype=1');
    }
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub valida_datos {
    if ($FORM{'_token'} eq '' && (($FORM{'_usr'} eq '') or ($FORM{'_psw'} eq ''))) {
        return 'Solicitud de ejecuci�n no v�lida.';
    }

    if ( ($FORM{'_new_psw'} eq '') or ($FORM{'_new_psw_confirm'} eq '') ) {
        return 'Por favor ingrese y confirme su contrase�a.';
    }

    if ($FORM{'_new_psw'} ne $FORM{'_new_psw_confirm'}) {
        return 'La contrase�a ingresada y su confirmaci�n son distintas, �stas deben ser id�nticas.';
    }

    if ($FORM{'_expired'} eq '1' && $FORM{'_new_psw'} eq $FORM{'_psw'}) {
        return 'La nueva contrase�a no puede ser igual a la actual.';
    }

    if ($FORM{'_expired'} eq '' && $FORM{'_token'} eq ''  && $FORM{'_email'} !~ /^[a-zA-Z\_\-\.0-9]+@[a-zA-Z\_\-0-9]+\.[0-9a-zA-Z\.\-\_]+$/) {
        return 'Email no v�lido';
    }

    return &prontus_auth::is_valid_password($FORM{'_new_psw'});
};
# ---------------------------------------------------------------
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

