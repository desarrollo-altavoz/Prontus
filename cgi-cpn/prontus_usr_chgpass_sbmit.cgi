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
use glib_html_02;
use glib_cgi_04;
use lib_prontus;
use strict;
use utf8;
use Digest::MD5 qw(md5_hex);
use prontus_auth;

my (%COOKIES, %FORM);

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta _path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    $FORM{'pwd_actual'} = &glib_cgi_04::param('pwd_actual');
    $FORM{'pwd_nuevo'} = &glib_cgi_04::param('pwd_nuevo');
    $FORM{'pwd_confirm'} = &glib_cgi_04::param('pwd_confirm');

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
        exit;
    };

    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL eq 'A') {
        &glib_html_02::print_json_result(0, 'La funcionalidad requerida está disponible sólo para usuario editor y redactor.', 1, 'exit=1,ctype=1');
        exit;
    };

    if (&lib_prontus::open_dbm_files() ne 'ok') {
        &glib_html_02::print_json_result(0, "No fue posible abrir archivos dbm.", 'exit=1,ctype=1');
        exit;
    };

    # Validar datos del formulario.
    my $error_validacion = &validar_datos();
    if ($error_validacion ne '') {
        utf8::decode($error_validacion);
        &glib_html_02::print_json_result(0, $error_validacion, 'exit=1,ctype=1');
        exit;
    };

    # Realizar cambio de contraseña.
    my $change_result = &prontus_auth::save_new_password($prontus_varglb::USERS_ID, $FORM{'pwd_nuevo'});
    if ($change_result ne '') {
        utf8::decode($change_result);
        &glib_html_02::print_json_result(0, $change_result, 'exit=1,ctype=1');
    }
    &glib_html_02::print_json_result(1, "La contraseña se cambió con éxito.", 'exit=1,ctype=1');
    exit;
};
# --------------------------------------------------------------------------------------------------
sub validar_datos {
    my ($users_nom, $users_usr, $users_psw, $users_perfil, $users_email, $users_exp_days, $users_fec_exp) = split /\|/, $prontus_varglb::USERS{$prontus_varglb::USERS_ID};

    if (!$FORM{'pwd_actual'}) {
        return 'Porfavor, ingrese su contraseña actual.';
    }

    if (!&prontus_auth::check_password($FORM{'pwd_actual'}, $users_psw)) {
        return 'La contraseña actual ingresada no es correcta.';
    } else {
        return '';
    }

    if (!$FORM{'pwd_nuevo'}) {
        return 'Por favor, ingrese su nueva contraseña.';
    }

    if ($FORM{'pwd_actual'} eq $FORM{'pwd_nuevo'}) {
        return 'La nueva contraseña no puede ser igual a la actual.';
    }

    if (!$FORM{'pwd_confirm'}) {
        return 'Por favor, ingrese su la confirmación de su nueva contraseña.';
    }

    if ($FORM{'pwd_nuevo'} ne $FORM{'pwd_confirm'}) {
        return 'La nueva contraseña y la confirmación no coinciden.';
    }

    # validacion final de nueva pass
    return &prontus_auth::is_valid_password($FORM{'pwd_nuevo'});
};
# --------------------------------------------------------------------------------------------------
