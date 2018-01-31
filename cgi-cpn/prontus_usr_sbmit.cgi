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

# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
#
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
#
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.1 - 16/05/2001 - Modificaciones para parametrizacion del protocolo (http o https) a traves del arch. de conf.
# 1.2 - 16/05/2001 - Revision general de detalles de forma.
# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0

# ---------------------------------------------------------------
# Revision Prontus 8.0 - ych - 23/05/2002
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt

# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};
use utf8;
use strict;
# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use lib_prontus;
use glib_str_02;
use glib_fildir_02;
use Digest::MD5 qw(md5_hex);
use prontus_auth;

# ---------------------------------------------------------------
# MAIN.
# -------------

my (%COOKIES, %FORM);
my ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL);
my (@Lst_ARTASOC, @Lst_PORTASOC);

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    $FORM{'USERS_ID'} = &glib_cgi_04::param('USERS_ID');
    $FORM{'NOM'} = &glib_cgi_04::param('NOM');
    $FORM{'USR'} = &glib_cgi_04::param('USR');
    $FORM{'PSW1'} = &glib_cgi_04::param('PSW1');
    $FORM{'PSW2'} = &glib_cgi_04::param('PSW2');
    $FORM{'EMAIL'} = &glib_cgi_04::param('EMAIL');
    $FORM{'EXP_DAYS'} = &glib_cgi_04::param('EXP_DAYS');
    $FORM{'Cmb_PERFIL'} = &glib_cgi_04::param('Cmb_PERFIL'); # A | P | E
    @Lst_ARTASOC = &glib_cgi_04::param('arts[]'); # es un array
    @Lst_PORTASOC = &glib_cgi_04::param('ports[]'); # es un array


    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # user check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL ne 'A') {
        &glib_html_02::print_json_result(0, 'La funcionalidad requerida está disponible sólo para el administrador del sistema', 'exit=1,ctype=1');
    };


    my $msg = &datos_validos();

    utf8::decode($msg);
    &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1') if ($msg);

    # Abrir dbm files
    if (&lib_prontus::open_dbm_files() ne 'ok') {
        &glib_html_02::print_json_result(0, 'No fue posible abrir archivos de usuario', 'exit=1,ctype=1');
    };

    $msg = &guardar_usr();
    &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1') if ($msg);

    # Borra cache de lista de articulos
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");


    my $response = '';
    # cambio de clave admin
    if (($FORM{'USERS_ID'} eq '1') && ($FORM{'PSW1'})) {
        $response = 'Sus datos han sido guardados correctamente.';
    } else {
        $response = 'Los datos han sido guardados correctamente.';
    }
    &glib_html_02::print_json_result(1, $response, 'exit=1,ctype=1');
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub guardar_usr {
    my ($key, $new_id);

    # Nuevo registro
    if ($FORM{'USERS_ID'} eq '') {
        if (&usr_repetido() eq 'S') {
            return "Usuario repetido";
        }

        $new_id = &get_new_id();
        $prontus_varglb::USERS{$new_id} = $FORM{'NOM'} . '|' . $FORM{'USR'} . '||' . $FORM{'Cmb_PERFIL'} . '|' . $FORM{'EMAIL'} . '|' . $FORM{'EXP_DAYS'} . '|';

        &insert_artusers($new_id);
        &insert_portusers($new_id);

        my $change_result = &prontus_auth::save_new_password($new_id, $FORM{'PSW1'}, $FORM{'EMAIL'});
        if ($change_result ne '') {
            utf8::decode($change_result);
            &glib_html_02::print_json_result(0, $change_result, 'exit=1,ctype=1');
        }

    } else { # Actualizar registro

        # Rescata datos actuales del user
        my ($users_nom, $users_usr, $users_psw, $users_perfil, $users_email, $users_exp_days, $users_fec_exp) = split /\|/, $prontus_varglb::USERS{$FORM{'USERS_ID'}};

        # actualiza fecha de expiracion si se cambian los dias
        if ($users_exp_days != $FORM{'EXP_DAYS'}) {
            $users_exp_days = $FORM{'EXP_DAYS'};

            if ($FORM{'EXP_DAYS'} == 0) {
                $users_fec_exp = 0;
            } else {
                $users_fec_exp = time + (int($FORM{'EXP_DAYS'}) * 86400);
            }
        }

        # Actualiza registro.
        if ($FORM{'USERS_ID'} ne '1') {
            # Actualiza hash USERS
            $prontus_varglb::USERS{$FORM{'USERS_ID'}} = $FORM{'NOM'} . '|' . $FORM{'USR'} . '|' . $users_psw . '|' . $FORM{'Cmb_PERFIL'} . '|' . $FORM{'EMAIL'} . '|' . $users_exp_days . '|' . $users_fec_exp;

            # Actualiza hash ARTUSERS, eliminando para ello los registros previos del usr correspondiente y luego insertando los nuevos.
            foreach $key  (keys %prontus_varglb::ARTUSERS) {
                my ($idtipo, $idusr) = split /\|/, $key;
                if ($idusr eq $FORM{'USERS_ID'}) {
                    delete $prontus_varglb::ARTUSERS{$key};
                };
            };
            &insert_artusers($FORM{'USERS_ID'});

            # Actualiza hash prontus_varglb::PORTUSERS, eliminando para ello los registros previos del usr correspondiente y luego insertando los nuevos.
            foreach $key  (keys %prontus_varglb::PORTUSERS) {
                my ($port, $idusr) = split /\|/, $key;
                if ($idusr eq $FORM{'USERS_ID'}) {
                    delete $prontus_varglb::PORTUSERS{$key};
                };
            };
            &insert_portusers($FORM{'USERS_ID'});
        } else { # Especial para usuario admin, sin actualizacion de art. y portadas asociadas.
            # Actualiza hash USERS
            $prontus_varglb::USERS{$FORM{'USERS_ID'}} = $FORM{'NOM'} . '|' . $FORM{'USR'} . '|' . $users_psw . '|' . $FORM{'Cmb_PERFIL'} . '|' . $FORM{'EMAIL'} . '|0|0';
        }
        if ($FORM{'PSW1'}) {
            # actualiza fecha de expiracion si se cambia la clave del usuario
            my $change_result = &prontus_auth::save_new_password($FORM{'USERS_ID'}, $FORM{'PSW1'}, $FORM{'EMAIL'});
            if ($change_result ne '') {
                utf8::decode($change_result);
                &glib_html_02::print_json_result(0, $change_result, 'exit=1,ctype=1');
            }
        } else {
            &lib_prontus::close_dbm_files();
        }

        if ($FORM{'USERS_ID'} eq '1') {
            # Escribe archivo extras (para edit)
            &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/extra.txt", &glib_str_02::random_string(8));
        }
    };

    return '';
};

# ---------------------------------------------------------------
sub insert_portusers {
    my ($id_usr) = $_[0];
    my ($port);

    foreach $port (@Lst_PORTASOC) {
        if ($port ne '') {
          $prontus_varglb::PORTUSERS{$port . '|' . $id_usr} = 'filler';
        };
    };
};


# ---------------------------------------------------------------
sub insert_artusers {
    my ($id_usr) = $_[0];
    my ($tipo_art);

    foreach $tipo_art (@Lst_ARTASOC) {
        if ($tipo_art ne '') {
          $prontus_varglb::ARTUSERS{$tipo_art . '|' . $id_usr} = 'filler';
        };
    };
};

# ---------------------------------------------------------------
sub get_new_id {
    my ($i, %paso);

    $i = '2'; # del 2 en adelante pues el 1 corresponde al 'admin'.
    %paso = %prontus_varglb::USERS;
    while (exists $paso{$i}) {
        $i++;
    };

    return $i;
};

# ---------------------------------------------------------------
sub usr_repetido {
    my ($key, $value);

    foreach $key (keys %prontus_varglb::USERS) {
        $value = $prontus_varglb::USERS{$key};
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $value;
        if ($USERS_USR eq $FORM{'USR'}) {
            return 'S';
        };
    };

    return 'N';
};
# ---------------------------------------------------------------

sub datos_validos {
    my ($result) = '';
    my ($elems1) = @Lst_ARTASOC;
    my ($elems2) =  @Lst_PORTASOC;

    if (($FORM{'NOM'} eq '') or ($FORM{'USR'} eq '') or ($FORM{'EMAIL'} eq '')) {
        return 'Por favor ingrese todos los campos marcados con asterisco (*)';
    };

    if ($FORM{'EMAIL'} !~ /^[a-zA-Z\_\-\.0-9]+@[a-zA-Z\_\-0-9]+\.[0-9a-zA-Z\.\-\_]+$/) {
        return 'Email no válido';
    };

    if ($FORM{'USR'} !~ /^[a-z\_\-\.0-9@]+$/) {
        return 'Usuario no válido.<br>Caracteres permitidos: letras en minúsculas sin tildes, guión, guión bajo, punto, arroba y números';
    };

    if ($FORM{'USERS_ID'} eq '') {
        if (!$FORM{'PSW1'}) {
            return 'Por favor ingrese la contraseña para el usuario';
        };

        if (!$FORM{'PSW2'}) {
            return 'Por favor ingrese confirmación de contraseña';
        };
    };


    if ($FORM{'PSW1'}) {
        if ($FORM{'PSW1'} ne $FORM{'PSW2'}) {
            return "La contraseña y su confirmación no coinciden.\nPor favor especifique el mismo valor para ambos campos.";
        };
        # validacion final de nueva pass
        my $valid_msg = &prontus_auth::is_valid_password($FORM{'PSW1'});
        if ($valid_msg ne '') {
            return $valid_msg;
        }
    };

    if ($prontus_varglb::PRONTUS_SSO ne 'SI') {
        if ($FORM{'USERS_ID'} ne '1') {
            if (($elems1 eq '') or ($elems2 eq '')) {
                return 'Usuario debe tener autorizados a lo menos un Artículo y una Portada.';
            }
        }
    }

    return '';
};

# ----------------------------END SCRIPT---------------------
