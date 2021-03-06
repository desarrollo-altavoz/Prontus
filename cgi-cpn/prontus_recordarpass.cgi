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
            &glib_html_02::print_json_result(1, 'Tu cuenta Prontus no registra email, no es posible enviar confirmaci�n de cambio de contrase�a.', 'exit=1,ctype=1');
        };

        #~ my $new_pass = &set_new_pass();
        #~ &enviar_clave($USERS_EMAIL, $new_pass);
        &enviar_confirmacion($USERS_USR, $USERS_EMAIL);
        my ($casilla, $dominio) = split(/@/, $USERS_EMAIL);
        &glib_html_02::print_json_result(1, "Se ha enviado un mensaje de confirmaci�n a tu correo electr�nico ($casilla@*****) registrado en Prontus.", 'exit=1,ctype=1');
    }
    else {
        &glib_html_02::print_json_result(0, "Usuario no existe o c�digo no es v�lido.\nImportante: El Sistema distingue may�sculas y min�sculas para los datos ingresado.", 'exit=1,ctype=1');
    };

};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub is_user_valido {
    my ($key, $val);
    foreach $key (keys %prontus_varglb::USERS) {
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $prontus_varglb::USERS{$key};
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
    #~ # CVI - 05/07/2012 - Ahora se usa md5 para encriptar la contrase�a
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
    #~ my ($texto) = "Estimado usuario:\nTus claves para ingresar al Panel de Control Prontus en $prontus_varglb::PUBLIC_SERVER_NAME son:\n\nUsuario: $FORM{'_usr'}\nContrase�a: $new_pass\n\n---\nEmail autom�tico, favor no lo respondas.\nSi crees que este correo no corresponde, ponte en contacto con tu WebMaster.";
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
        # Si el archivo existe, ya tiene una confirmacion de cambio de contrase�a pendiente.
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


    my $protocolo = 'http';
    if($prontus_varglb::SERVER_PROTOCOLO_HTTPS eq 'SI') {
        $protocolo = 'https';
    }
    $urltoken = "$protocolo://$prontus_varglb::CPAN_SERVER_NAME/$prontus_varglb::DIR_CGI_CPAN/prontus_olvidopass.cgi?_path_conf=/$prontus_varglb::PRONTUS_ID/cpan/$prontus_varglb::PRONTUS_ID.cfg&_token=$token&_usr=$user";

    $asunto = "[$protocolo://$prontus_varglb::CPAN_SERVER_NAME/$prontus_varglb::PRONTUS_ID] Confirmaci�n de recuperaci�n de contrase�a";
    $cuerpo = "Estimado usuario ($user):<br/><br/>";
    $cuerpo .= "Alguien ha solicitado restablecer la contrase�a de tu cuenta para acceder al Panel de Control Prontus en <a href=\"$protocolo://$prontus_varglb::CPAN_SERVER_NAME/$prontus_varglb::PRONTUS_ID/cpan\">$protocolo://$prontus_varglb::CPAN_SERVER_NAME/$prontus_varglb::PRONTUS_ID/cpan</a>.<br/><br/>Visita el siguiente enlace para iniciar el proceso de recuperaci�n, de lo contrario puedes ignorar este correo.<br/><br/><a href=\"$urltoken\">$urltoken</a><br/><br/>Nota: Esta url tiene una validez de 1 hora.<br/>";
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

