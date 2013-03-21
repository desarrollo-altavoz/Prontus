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
# Enviar pass al user.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# 2) Desde la pag. de ingreso al Sistema, via boton 'Ingresar'.
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# No registra.
# ---------------------------------------------------------------
# Prontus 10 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;

use lib_prontus;
use lib_mail;
use lib_captcha2;
use glib_str_02;
use glib_fildir_02;

use strict;

use Digest::MD5 qw(md5_hex);

# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM);
my ($USERS_ID, $USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL);

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});


    $FORM{'_usr'} = &glib_cgi_04::param('_usr');
    $FORM{'_usr'} =~ s/[^a-z\_\-\.0-9@]//g;
    $FORM{'_code'} = &glib_cgi_04::param('_code');
    $FORM{'_code'} =~ s/[^\w]//g;

    # Carga var. globales con los datos del arch. conf.

    &lib_prontus::load_config($FORM{'_path_conf'});   # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;


    if (&lib_prontus::open_dbm_files() ne 'ok') { # Prontus 6.0
        &glib_html_02::print_json_result(0, 'No fue posible abrir archivos de usuarios.', 'exit=1,ctype=1');
    };

    my $user_valido = &is_user_valido();
    my $captcha_valido = &is_captcha_valido();
    if ( ($user_valido) && ($captcha_valido) ) {

        if (!$USERS_EMAIL) {
            &glib_html_02::print_json_result(1, 'Tu cuenta Prontus no registra email, no es posible enviar confirmación de cambio de contraseña.', 'exit=1,ctype=1');
        };

        #~ my $new_pass = &set_new_pass();
        #~ &enviar_clave($USERS_EMAIL, $new_pass);
        &enviar_confirmacion($USERS_USR, $USERS_EMAIL);
        &glib_html_02::print_json_result(1, 'La nueva contraseña ha sido enviada a tu email registrado en Prontus.', 'exit=1,ctype=1');
    }
    else {
        &glib_html_02::print_json_result(0, "Usuario no existe o código no es válido.\nImportante: El Sistema distingue mayúsculas y minúsculas para el 'usuario' ingresado.", 'exit=1,ctype=1');
    };

};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub is_user_valido {
    my ($key, $val);
    foreach $key (keys %prontus_varglb::USERS) {
        $val = $prontus_varglb::USERS{$key};
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $val;
        if ($USERS_USR eq $FORM{'_usr'})  {
            $USERS_ID = $key;
            return 1;
        };
    };
    return 0;
};
# ---------------------------------------------------------------
#~ sub set_new_pass {
    #~ my $new_pass = &glib_str_02::random_string(3) . 'prontus' . &glib_str_02::random_string(3);
    #~ my ($key, $val);
    #~ # CVI - 05/07/2012 - Ahora se usa md5 para encriptar la contraseña
    #~ $prontus_varglb::USERS{$USERS_ID} = $USERS_NOM . '|' . $USERS_USR . '|' . md5_hex($new_pass) . '|' . $USERS_PERFIL . '|' . $USERS_EMAIL;
    #~ &lib_prontus::close_dbm_files();
    #~ return $new_pass;
#~ };

# ---------------------------------------------------------------
sub is_captcha_valido {
    
    # Usando la nueva lib_captcha se manejan ambos formatos
    my $captcha_input = $FORM{'_code'};
    my $captcha_type = 'cpan'; # custom
    my $captcha_img = &glib_cgi_04::param('_captcha_img');
    my $captcha_code = &glib_cgi_04::param('_captcha_code');
    $captcha_input = &glib_cgi_04::param('_captcha_text') unless($captcha_input);
    #~ require 'dir_cgi.pm'; 
    &lib_captcha2::init($prontus_varglb::DIR_SERVER, $prontus_varglb::DIR_CGI_CPAN);
    my $msg_err_captcha = &lib_captcha2::valida_captcha($captcha_input, $captcha_code, $captcha_type, $captcha_img);
    if ($msg_err_captcha ne '') {
        print STDERR "Captcha no es valido o bien no fue posible verificarlo ERRCODE[$lib_captcha::ERRCODE][$lib_captcha::ERRGLOSA{$lib_captcha::ERRCODE}]\n";
        return 1 if ($lib_captcha::ERRCODE == 6); # no hay gd, simplemente no se valida
        return 0;
    };
    return 1;
};
# ---------------------------------------------------------------
#~ sub enviar_clave {
    #~ my ($email, $new_pass) = @_;
    #~ my ($from) = 'prontus@altavoz.net';
    #~ my ($replyto_name) = 'Prontus CMS';
    #~ my ($replyto_email) =  'prontus@altavoz.net';
    #~ my ($asunto) = "Claves Prontus para $prontus_varglb::PUBLIC_SERVER_NAME/$prontus_varglb::PRONTUS_ID";
#~ 
    #~ my ($texto) = "Estimado usuario:\nTus claves para ingresar al Panel de Control Prontus en $prontus_varglb::PUBLIC_SERVER_NAME son:\n\nUsuario: $FORM{'_usr'}\nContraseña: $new_pass\n\n---\nEmail automático, favor no lo respondas.\nSi crees que este correo no corresponde, ponte en contacto con tu WebMaster.";
    #~ # Codifica en UTF8
    #~ utf8::encode($texto);
#~ 
    #~ my ($htmldoc) = '';
    #~ my ($attach) = '';
    #~ my ($url) = '';
    #~ my ($dir_attach) = '';
    #~ my ($smtp) = $prontus_varglb::SERVER_SMTP;
#~ 
    #~ &lib_mail::enviar_mail($email, $from, $replyto_name, $replyto_email, $asunto, $texto, $htmldoc, $attach, $url, $dir_attach, $smtp);
#~ };

sub enviar_confirmacion {
    my $user = $_[0];
    my $email = $_[1];
    my ($asunto, $cuerpo, $token);
    my ($dirproc, $filepath, $urltoken);
    
    $dirproc = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/procs/recordarpass";
    &glib_fildir_02::check_dir($dirproc);
    $filepath = "$dirproc/$user.txt";
    
    if (-f $filepath) {
        # Si el archivo existe, ya tiene una confirmacion de cambio de contraseña pendiente.
        # Verificar fecha de modificacion del archivo, si es mayor a 1 hora, volver a generar un nuevo token.
        my $mtime = (stat($filepath))[9];
        my $diffsecs = time - $mtime;
        if ($diffsecs > 3600) {
            $token = md5_hex(md5_hex(&glib_str_02::random_string(10)));
        } else {
            # Usar el mismo.
            $token = &glib_fildir_02::read_file($filepath);
            $token =~ s/\n//s;
            $token =~ s/\r//s;
            $token =~ s/\t//s;
            $token =~ s/ *//s;
        };
    } else {
        $token = md5_hex(md5_hex(&glib_str_02::random_string(10)));
    };

    &glib_fildir_02::write_file($filepath, $token);

    $urltoken = "http://$prontus_varglb::PUBLIC_SERVER_NAME/$prontus_varglb::DIR_CGI_CPAN/prontus_olvidopass.cgi?_path_conf=/$prontus_varglb::PRONTUS_ID/cpan/$prontus_varglb::PRONTUS_ID.cfg&_token=$token&_usr=$user";

    $asunto = "[http://$prontus_varglb::PUBLIC_SERVER_NAME/$prontus_varglb::PRONTUS_ID] Confirmación de recuperación de contraseña";
    $cuerpo = "Estimado usuario ($user):<br/><br/>";
    $cuerpo .= "Alguien ha solicitado restablecer la contraseña de su cuenta para acceder al Panel de Control Prontus en http://$prontus_varglb::PUBLIC_SERVER_NAME/$prontus_varglb::PRONTUS_ID.<br/>Visite la siguiente url para iniciar el proceso de recuperación, de lo contrario puede ignorar este correo.<br/><br/><a href=\"$urltoken\">$urltoken</a><br/><br/>Nota: Esta url tiene una validez de 1 hora.<br/>";
    utf8::encode($cuerpo);
    utf8::encode($asunto);

    my ($from) = 'prontus@altavoz.net';
    my ($replyto_name) = 'Prontus CMS';
    my ($replyto_email) =  'area_prontus@altavoz.net';
    my ($attach) = '';
    my ($url) = '';
    my ($dir_attach) = '';
    my ($smtp) = $prontus_varglb::SERVER_SMTP;

    &lib_mail::enviar_mail($email, $from, $replyto_name, $replyto_email, $asunto, '', $cuerpo, $attach, $url, $dir_attach, $smtp);
    
};

# -------------------------------END SCRIPT----------------------

