#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# SCRIPT.
# -----------
# coment_enviar.cgi

# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-bin/coment/.

# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Guardar comentario
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------

# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------

# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------

# ---------------------------------------------------------------
# Tablas.
# ------------------------
# No utiliza.
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 11/2006 - YCC - Primera Version.
# 1.1 - 02/2007 - YCC - Agrega manejo de puntaje, especifico para wow.
# 1.2 - 02/2008 - PRB - Se comenta captcha.
# 1.3 - 05/2008 - YCC - Se habilita captcha. Ademas se aprovecha de actualizar la rutina myself_running
# 1.4 - 30/07/2009 - PRB - Se agrega parametro CAPTCHA en cfg para validar la incorporacion de captcha
# 1.5 - 08/2009 - YCC - Agrega validacion de nick como email en caso de que se requiera notificacion
#                       de publicacion. Opcion util cuando el sistema esta configurado para operar
#                       "con moderacion".

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
#


BEGIN {
    require '../dir_cgi.pm';
    my ($ROOTDIR) = $ENV{'DOCUMENT_ROOT'};  # desde el web
    $ROOTDIR .= '/' . $DIR_CGI_CPAN;
    unshift(@INC,$ROOTDIR); # Para dejar disponibles las librerias de prontus

    $ROOTDIR .= '/coment';
    unshift(@INC,$ROOTDIR); # Para dejar disponibles las librerias de coment

    # print STDERR "ROOTDIR[$ROOTDIR]\n";
};

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use coment_varglb;
use glib_hrfec_02;
use glib_cgi_04;
use lib_coment;
use glib_dbi_02;
use strict;

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;

use lib_val;
use lib_phpsession;
use lib_ipcheck;

use lib_captcha;
use lib_captcha2;
use lib_maxrunning;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
my ($BD, %FORM);
my ($USER_IP) = $ENV{'REMOTE_ADDR'};


&glib_cgi_04::new();

my ($CURR_DTIME) = &glib_hrfec_02::get_dtime_pack4();

my ($CRLF) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;

my $MODERACION;

main:{
    print "Content-Type: text/html\n\n";
    # Recibe campos del form
    my @campos = &glib_cgi_04::param();
    foreach my $key (@campos) {
        $FORM{$key} = &glib_cgi_04::param($key);
    };

    # Soporta un maximo de n copias corriendo.
    if (&lib_maxrunning::maxExcedido(6)) {
        print "Content-Type: text/html\n\n";
        print "0|Error: Servidor ocupado.";
        exit;
    };

    # Despulgues varios
    $FORM{'OBJTIPO'} =~ s/[^\w]//sg;
    $FORM{'OBJID'} =~ s/[^\w\.\-]//sg;
    $FORM{'NICK'} =~ s/[^\w\.\-@]//sg;
    $FORM{'OBJTIT'} =~ s/"/""/sg;
    $FORM{'OBJTIT'} =~ s/\\//sg;
    $FORM{'COMENT_TEXTO'} =~ s/"/""/sg;
    $FORM{'COMENT_TEXTO'} =~ s/\\//sg;
    $FORM{'COMENT_TEXTO'}=~s/\r//sg;
    $FORM{'COMENT_TEXTO'}=~s/\n{3,}/\n\n/sg;
    #~ $FORM{'CODSEG'} =~ s/[^\w]//sg;

    # Validacion y gestion de ip bloqueada
    my $dir_ip_control = "$coment_varglb::DIR_SERVER/coment/cpan/ip_control";
    my $user_ip = $ENV{'REMOTE_ADDR'};
    my $maxrequest_por_ip = 30;
    my $bloqueoip_interval = 60;
    my $bloquear_ip = &lib_ipcheck::check_bloqueo_ip($dir_ip_control, $user_ip, $maxrequest_por_ip, $bloqueoip_interval);
    if ($bloquear_ip) {
        print "0|Request inhabilitado";
        exit;
    };

    # Validaciones basicas
    if(  (!$FORM{'OBJTIT'}) || (!$FORM{'NICK'}) || (!$FORM{'OBJID'}) || (!$FORM{'OBJTIPO'}) || (!$FORM{'COMENT_TEXTO'}) ) {
        print "0|Error en los datos enviados - 900";
        exit;
    };

    if ($FORM{'_prontus_id'} !~ /^\w+$/) {
        print "0|Error en los datos enviados - 901";
        exit;
    };

    if (! -d "$coment_varglb::DIR_SERVER/$FORM{'_prontus_id'}") {
        print "0|Error en los datos enviados - 902";
        exit;
    };

    # Carga variables de configuracion.
    $FORM{'_path_conf'} = "$coment_varglb::DIR_SERVER/$FORM{'_prontus_id'}/cpan/$FORM{'_prontus_id'}.cfg";
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0

    # Carga y valida cfg
    my ($options_tipo, $msg_err, $hash_tipos_ref) = &lib_coment::get_objtipos($coment_varglb::DIR_SERVER, '', $prontus_varglb::PRONTUS_ID);
    if ($msg_err) {
        print "0|$msg_err";
        exit;
    };
    my %hash_tipos = %$hash_tipos_ref;
    if (! exists $hash_tipos{$FORM{'OBJTIPO'}}{'NOM'}) {
        print "0|Error en los datos enviados - 903";
        exit;
    };


    # Si es con aviso de publicacion, en el nick debe venir el email.
    if(lc($hash_tipos{$FORM{'OBJTIPO'}}{'ENVIAR_MAIL_PUBLICACION'}) eq 'si') {
        if ($FORM{'NICK'} !~ /[\w\.\-\,\']+\@[\w\-\.]+\.[\w]+/) {
            print "0|Error: E-mail no válido [$FORM{'NICK'}].";
            exit;
        };
    };

    $MODERACION = $hash_tipos{$FORM{'OBJTIPO'}}{'MODERACION'};
    if ($MODERACION eq '') {
        $MODERACION = 'SI';
    };


    # Usando la nueva lib_captcha se manejan ambos formatos
    my $captcha_input = &glib_cgi_04::param('_CAPTCHA');
    my $captcha_type = 'form'; # custom
    my $captcha_img = &glib_cgi_04::param('_captcha_img');
    my $captcha_code = &glib_cgi_04::param('_captcha_code');
    $captcha_input = &glib_cgi_04::param('_captcha_text') unless($captcha_input);


    if($captcha_img && $captcha_code) {
        # Valida nuevo captcha sin sesion
        &lib_captcha2::init($prontus_varglb::DIR_SERVER, $prontus_varglb::DIR_CGI_CPAN);
        my $msg_err_captcha = &lib_captcha2::valida_captcha($captcha_input, $captcha_code, $captcha_type, $captcha_img);
        if ($msg_err_captcha ne '') {
            print "0|$msg_err_captcha\n";
            exit;
        };
    } else {
        # Valida captcha de sesion php
        # 1.4 Valida captcha
        if(lc($hash_tipos{$FORM{'OBJTIPO'}}{'CAPTCHA'}) eq 'si') {
            my $msg_captcha = &check_captcha($hash_tipos{$FORM{'OBJTIPO'}}{'PHP_SESSION_NAME'}, $hash_tipos{$FORM{'OBJTIPO'}}{'PHP_SESSION_PATH'});
            if ($msg_captcha) {
                print "0|$msg_captcha";
                exit;
            };
        };
    }

    # Validacion custom, optativa
    my $msg_custom = &lib_val::validation(\%hash_tipos, \%FORM);
    if ($msg_custom) {
        print "0|$msg_custom";
        exit;
    };

    # Recorte de texto segun valor max en cfg
    $FORM{'COMENT_TEXTO'} = substr($FORM{'COMENT_TEXTO'}, 0, $hash_tipos{$FORM{'OBJTIPO'}}{'LIMIT_CHARS'});

    # Guarda comentario
    &guarda_comentario();

    my $msg_resp;
    if ($MODERACION eq 'SI') {
        $msg_resp = $hash_tipos{$FORM{'OBJTIPO'}}{'MSG_MODER'};
        $msg_resp = 'Gracias, tu comentario ha sido recibido y pronto lo publicaremos!' if (!$msg_resp);
    } else {
        $msg_resp = $hash_tipos{$FORM{'OBJTIPO'}}{'MSG_NOMODER'};
        $msg_resp = 'Gracias, tu comentario ya se encuentra publicado!' if (!$msg_resp);
    };
    print "1|$msg_resp";

    exit;

};

# ---------------------------------------------------------------
sub check_captcha {
    my ($session_name, $session_path) = @_;

    # Valida captcha
    if (!$FORM{'CODSEG'}) {
        return 'Debes ingresar C&oacute;digo de Seguridad.';
    };
    my $session_captcha = &lib_phpsession::get_php_session_var('_COMENT_CAPTCHA_' . $FORM{'OBJID'}, $session_name, $session_path); # CPN - 16/08/2008 - Variable session con ts articulo #

    if (!$session_captcha) {
        return 'No es posible verificar C&oacute;digo de Seguridad.'
    };

    my $codseg_crypt = crypt(lc $FORM{'CODSEG'},'av');
    print STDERR "codseg_crypt[$codseg_crypt] - session_captcha[$session_captcha]\n";
    if ($codseg_crypt ne $session_captcha) {
        return "Verifica el C&oacute;digo de Seguridad ingresado.";
    };
    return '';
};

# ---------------------------------------------------------------
sub guarda_comentario {

  # Abrir BD.
    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        print "0|$msg_err_bd";
        exit;
    };

  my $coment_status = '1';
  if ($MODERACION eq 'SI') {
    $coment_status = '0';
  };

  my $ret = &glib_dbi_02::check_table_column($BD, "COMENT", "COMENT_EMAIL", "VARCHAR(100) NOT NULL DEFAULT ''");

  my $sql = " insert COMENT set "
          . "COMENT_OBJTIPO = \"$FORM{'OBJTIPO'}\", "
          . "COMENT_OBJID = \"$FORM{'OBJID'}\", "
          . "COMENT_OBJTIT = \"$FORM{'OBJTIT'}\", "
          . "COMENT_DATETIME = \"$CURR_DTIME\", "
          . "COMENT_TEXTO = \"$FORM{'COMENT_TEXTO'}\", "
          . "COMENT_NICK = \"$FORM{'NICK'}\", "
          . "COMENT_EMAIL = \"$FORM{'EMAIL'}\", "
          . "COMENT_STATUS = \"$coment_status\" ";
  my $new_coment_id = &glib_dbi_02::insert_dev_id($BD, $sql);

  # print STDERR $sql;
  if ($MODERACION eq 'NO') {
    # comentario se publica de inmediato
    if ($new_coment_id) {
      &lib_coment::generar_comentarios($BD, $coment_varglb::DIR_SERVER, $FORM{'OBJTIPO'}, $FORM{'OBJID'}, $prontus_varglb::PRONTUS_ID);
    };
  };

  $BD->disconnect;
};

# -------------------------END SCRIPT----------------------
