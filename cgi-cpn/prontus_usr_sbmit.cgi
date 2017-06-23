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

# ---------------------------------------------------------------
# MAIN.
# -------------

my (%COOKIES, %FORM);
my ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL);
my (@Lst_ARTASOC, @Lst_PORTASOC);

main: {
    my ($lnk);

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

    &lib_prontus::close_dbm_files();


    # Borra cache de lista de articulos
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");


    # cambio de clave admin
    if (($FORM{'USERS_ID'} eq '1') && ($FORM{'PSW1'})) {
        my $response = 'Sus datos han sido guardados correctamente.';
        utf8::decode($response);
        &glib_html_02::print_json_result(1, $response, 'exit=1,ctype=1');
    } else {
        my $response = 'Los datos han sido guardados correctamente.';
        utf8::decode($response);
        &glib_html_02::print_json_result(1, $response, 'exit=1,ctype=1');
    };
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
        };

        $new_id = &get_new_id();
        # CVI - 05/07/2012 - Los nuevos usuarios se guardan si o si con md5
        $prontus_varglb::USERS{$new_id} = $FORM{'NOM'} . '|' . $FORM{'USR'} . '|' . md5_hex($FORM{'PSW1'}) . '|' . $FORM{'Cmb_PERFIL'} . '|' . $FORM{'EMAIL'};

        &insert_artusers($new_id);
        &insert_portusers($new_id);

    } else { # Actualizar registro

        # Rescata datos actuales del user
        my ($users_nom, $users_usr, $users_psw, $users_perfil, $users_email) = split /\|/, $prontus_varglb::USERS{$FORM{'USERS_ID'}};
        # Actualiza clave si corresponde
        if ($FORM{'PSW1'}) {
            # CVI - 05/07/2012 - Los nuevos usuarios se guardan si o si con md5
            $users_psw =  md5_hex($FORM{'PSW1'});
        };
        print STDERR "crypted_pass[$users_psw]\n";
        # Actualiza registro.
        if ($FORM{'USERS_ID'} ne '1') {

            # Actualiza
            $prontus_varglb::USERS{$FORM{'USERS_ID'}} = $FORM{'NOM'} . '|' . $FORM{'USR'} . '|' . $users_psw . '|' . $FORM{'Cmb_PERFIL'} . '|' . $FORM{'EMAIL'};

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
            $prontus_varglb::USERS{$FORM{'USERS_ID'}} = $FORM{'NOM'} . '|' . $FORM{'USR'} . '|' . $users_psw . '|' . $FORM{'Cmb_PERFIL'} . '|' . $FORM{'EMAIL'};

            # Escribe archivo extras (para edit)
            &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/extra.txt", &glib_str_02::random_string(8));
        };
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
        if ($FORM{'PSW1'} =~ /^\s+$/) {
            return 'La contraseña no puede contener solamente espacios.';
        };

        if ($FORM{'PSW1'} !~ /^.{6,32}$/) {
            return 'La nueva contraseña debe estar compuesta por un mínimo de 6 caracteres y un máximo de 32 caracteres.';
        };

        if (lc $FORM{'PSW1'} eq 'prontus') {
            return "La contraseña es inválida, ya que no puede ser \"$FORM{'PSW1'}\", por favor ingrese una distinta.";
        };

        if ($FORM{'PSW1'} ne $FORM{'PSW2'}) {
            return "La contraseña y su confirmación no coinciden.\nPor favor especifique el mismo valor para ambos campos.";
        };
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
