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
# PROPOSITO.
# -----------
# Funciones para envio de emails.

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# -----------------------
# 01 - 07/2003 - YCH

# -------------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

package lib_mail;


use LWP::UserAgent;
use HTTP::Response;

use strict;

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub enviar_mail {  # FROM MAILCENTER
# Envia email correspondiente a los parametros entregados.
# Contenidos basicos del email : Autor, Asunto, Texto.
# Contenidos adicionales : URL y/o archivo adjunto.

# EJEMPLO DE INVOCACION:
# ---------------------------------------------
#  my ($email) = $elip_varglb::MAIL_CUOTA_TO;
#  my ($from) = $elip_varglb::MAIL_CUOTA_FROM;
#  my ($replyto_name) = $elip_varglb::MAIL_CUOTA_REPLYTO;
#  my ($replyto_email) =  $elip_varglb::MAIL_CUOTA_REPLYTO;
#  my ($asunto) = $elip_varglb::MAIL_CUOTA_SUBJECT;
#  my ($texto) = "El nro. de contactos ya ha alcanzado el máximo asignado en el mailcenter correspondiente. ENTIDAD[$FORM{'ENTIDAD'}]";
#  my ($htmldoc) = '';
#  my ($attach) = '';
#  my ($url) = '';
#  my ($dir_attach) = '';
#
#  &lib_mail::enviar_mail($email, $from, $replyto_name, $replyto_email, $asunto, $texto, $htmldoc, $attach, $url, $dir_attach, $smtp);
# ---------------------------------------------

    my ($email, $from, $replyto_name, $replyto_email, $asunto, $texto, $htmldoc, $attach, $url, $dir_attach, $smtp) = @_;
    # my ($autor_replyto) = '"' . $replyto_name . '"' . " <" . $replyto_email . '>';
    my ($autor_replyto) = $replyto_email;
    my $filename = $attach;

    if ($attach ne '') {
        $attach = "$dir_attach/$attach";
    };

    if($attach) {
        if ($htmldoc ne '') {
            $texto =~ s/\n/<br>\n/g;
            $htmldoc =~ s/(<body.*?>)/$1\n$texto<br>\n/is;
            $htmldoc = &procesar_html($htmldoc, $url);
            if(&mail_multipart($from, $email, $autor_replyto, $asunto, $htmldoc, $filename, $attach, 1, $smtp)) {
                return 'S';
            } else {
                return 'N';
            }
        } else {
            if(&mail_multipart($from, $email, $autor_replyto, $asunto, $texto, 0, $smtp)) {
                return 'S';
            } else {
                return 'N';
            }
        }

    } elsif ($htmldoc eq '') {
        if (&mail_text($from, $email, $autor_replyto, $asunto, $texto, 0, $smtp)) {
            # print STDERR "OK"; # DEBUG
            return 'S';
        } else {
            # print STDERR "FAIL"; # DEBUG
            return 'N';
        };
    } else{
        # Envio con html.
        if ($htmldoc ne '') {
            # Inserta bajo el body el $texto, transformando los \n en <br>
            $texto =~ s/\n/<br>\n/g;
            $htmldoc =~ s/(<body.*?>)/$1\n$texto<br>\n/is;
            $htmldoc = &procesar_html($htmldoc, $url);
            if (&mail_text($from, $email, $autor_replyto, $asunto, $htmldoc, 1, $smtp)) {
                return 'S';
            } else {
                return 'N';
            };
        } else {
            return 'N';
        };
    };
};

# ---------------------------------------------------------------
sub get_html {  # FROM MAILCENTER

    my($url) = $_[0];
    return '' if (($url eq '') or ($url !~ /^https?/i));
    my($ua) = new LWP::UserAgent;
    my($request) = new HTTP::Request('GET', $url) || die $!;
    my($response) = $ua->request($request) || die $!;
    if ($response->is_success) {
        return $response->content;
    } else {
        return '';
    };

}; # getHTML

# ---------------------------------------------------------------
sub procesar_html {

    my($body, $url) = @_;

    # Agrega tag base si es que no esta.
    if ($body !~ /<BASE HREF=/i) {
        $body =~ s/<HEAD>/<head>\n<base href="$url">/si;
    };

    $url =~ /(https?\:\/\/.*?)\//i;
    my $theserver = $1;

    # Corrige paths no relativos.
    $body =~ s/ HREF="\// href="$theserver\//sig;
    $body =~ s/ SRC="\// src="$theserver\//sig;

    # Corrige la ausencia de retornos de carro.
    $body =~ s/\r\n/\n/sg;
    $body =~ s/\r/\n/sg;

    return $body;
}
# -------------------------------------------------------------------
sub err_mail {
    my $msg = $_[0];
    print STDERR $msg;
    return 0;
};
# -------------------------------------------------------------------
sub mail_text {   # FROM MAILCENTER

    my ($from, $to, $replyto, $subject, $body, $encode_html, $smtp) = @_;
    my ($sender);

    my $no_hay_mailsender;
    eval "require Mail::Sender;";    $no_hay_mailsender = $@;

    if ($no_hay_mailsender) { # intenta enviar con SENDMAIL
        print STDERR "No se encuentra modulo Mail::Sender, enviando con SENDMAIL.\n";
        my $sendmail = "/usr/sbin/sendmail -t";

        open(SENDMAIL, "|$sendmail") or return &err_mail("Error al enviar mail via SENDMAIL EN /usr/sbin/sendmail [$!]");
        print SENDMAIL "From: $from\n";
        print SENDMAIL "Reply-to: $replyto\n";
        print SENDMAIL "Subject: $subject\n";
        print SENDMAIL "To: $to\n";
        print SENDMAIL "MIME-Version: 1.0\n";
        if ($encode_html) {
            print SENDMAIL "Content-type: text/html\nContent-Transfer-Encoding: 7bit\n\n";
        } else {
            print SENDMAIL "Content-type: text/plain\nContent-Transfer-Encoding: quoted-printable\n\n";
        };
        print SENDMAIL $body;
        close(SENDMAIL);
        return 1;
    } else {
        #~ print STDERR "Usando modulo Mail::Sender\n";
        require Mail::Sender;
        $Mail::Sender::NO_X_MAILER = 1; # Evita molestos copyrights.

        #TODO Revisar esto con urgencia, no deberia ser asi, pero funciona
        use Encode qw/encode decode/;
        $subject = encode('MIME-Header', decode("utf8", $subject));
        $from = encode('MIME-Header', decode("utf8", $from));

        ref ($sender = new Mail::Sender({
                from => $from,
                smtp => $smtp,
                to =>$to,
                subject => $subject,
                reply => $replyto,
                tls_allowed => 0 # deshabilita encriptacion SSL
                #~ debug => \*STDERR,
        })) or return &err_mail("Error al enviar mail via Mail::Sender [$!] [$Mail::Sender::Error] [From=$from][To=$to][SMTP=$smtp]");

        if ($encode_html) {
            # Envio de email html sin attachs
            (ref ($sender->MailMsg({
                    msg => $body,
                    ctype => 'text/html; charset=utf-8',
                    encoding => "quoted-printable",
                    disposition => ''
            })) ) or return &err_mail("Error al enviar mail via Mail::Sender [$!] [$Mail::Sender::Error]");

        } else {
            # Envio de email sin html y sin attachs
            (ref ($sender->Open({
                    ctype => 'text/plain; charset=utf-8',
                    encoding => "quoted-printable",
                    #~ encoding => "BASE64"
            })) ) or return &err_mail("Error al enviar mail via Mail::Sender [$!] [$Mail::Sender::Error]");
            $sender->SendEnc($body);
            $sender->Close();
        };
        return 1;
    };
};
# -------------------------------------------------------------------
sub mail_multipart {   # FROM MAILCENTER

    my ($from, $to, $replyto, $subject, $body, $filename, $attach, $encode_html, $smtp) = @_;
    my ($sender);

    my $no_hay_mailsender;
    eval "require Mail::Sender;";    $no_hay_mailsender = $@;

    if ($no_hay_mailsender) { # intenta enviar con SENDMAIL
        print STDERR "No se encuentra modulo Mail::Sender, enviando con SENDMAIL.\n";
        my $sendmail = "/usr/sbin/sendmail -t";

        open(SENDMAIL, "|$sendmail") or return &err_mail("Error al enviar mail via SENDMAIL EN /usr/sbin/sendmail [$!]");
        print SENDMAIL "From: $from\n";
        print SENDMAIL "Reply-to: $replyto\n";
        print SENDMAIL "Subject: $subject\n";
        print SENDMAIL "To: $to\n";
        print SENDMAIL "MIME-Version: 1.0\n";
        if ($encode_html) {
            print SENDMAIL "Content-type: text/html\nContent-Transfer-Encoding: 7bit\n\n";
        } else {
            print SENDMAIL "Content-type: text/plain\nContent-Transfer-Encoding: quoted-printable\n\n";
        };
        print SENDMAIL $body;
        close(SENDMAIL);
        return 1;

    } else {
        #~ print STDERR "Usando modulo Mail::Sender\n";
        require Mail::Sender;
        $Mail::Sender::NO_X_MAILER = 1; # Evita molestos copyrights.

        #TODO Revisar esto con urgencia, no deberia ser asi, pero funciona
        use Encode qw/encode decode/;
        $subject = encode('MIME-Header', decode("utf8", $subject));
        $from = encode('MIME-Header', decode("utf8", $from));

        ref ($sender = new Mail::Sender({
                from => $from,
                smtp => $smtp,
                to => $to,
                subject => $subject,
                reply => $replyto,
                debug => \*STDERR
        })) or return &err_mail("Error al enviar mail via Mail::Sender [$!] [$Mail::Sender::Error] [From=$from][To=$to][SMTP=$smtp]");

        if ($encode_html) {
            # Envio de email html con attachs
            $sender->OpenMultipart();
            $sender->Part({ctype => 'text/html; charset=utf-8', encoding => 'Base64', disposition => 'attachment; filename="' . $filename . '"'});
            my @arr;
            $arr[0] = $body;
            $sender->SendEnc(@arr);
            $sender->SendFile({file => $attach});
            $sender->Close;

        } else {
            # Envio de email sin html con attachs
            (ref ($sender->MailFile({
                    msg => $body,
                    file => $attach,
                    disposition => 'attachment; filename="' . $filename . '"',
                    b_charset => 'utf-8' # para mailfile se usa b_charset en lugar de charset

            })) ) or return &err_mail("Error al enviar mail via Mail::Sender [$!] [$Mail::Sender::Error]");
        };
        return 1;
    };

};

# ---------------------------------------------------------------
return 1;
# -------------------------------END LIBRERIA--------------------
