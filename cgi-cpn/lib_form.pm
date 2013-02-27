#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

package lib_form;

$Mail::Sender::NO_X_MAILER = 1; # Elimina copyrights.
$SERVER_SMTP;  # Servidor SMTP.

# ------------------------------------------------------------------------- #
# Envia un mensaje de correo electronico.
# &envia_mail($to,$from,$subj,$body,$filename,$filedata)
sub envia_mail {

    my ($to,$from,$subj,$body,$filename,$filedata) = @_;
    my $resp;

    if($filename) {
        $resp = &lib_mail::mail_multipart($from, $to, $from, $subj, $body, $filename, $filedata, 0, $lib_form::SERVER_SMTP);
    } else {
        $resp = &lib_mail::mail_text($from, $to, $from, $subj, $body, 0, $lib_form::SERVER_SMTP);
    };
    return $resp;

}; # envia_mail

# ------------------------------------------------------------------------- #
# Elimina los archivos, del cache de respuestas, de mas de 10 minutos de antiguedad.
sub garbage_collection {
    my $path_answer_dir = $_[0];
    print STDERR "path_answer_dir[$path_answer_dir]\n";
    return unless(-d $path_answer_dir);
    if (opendir(DIR, $path_answer_dir)) {
        my @entries = readdir(DIR);
        closedir DIR;
        foreach my $file (@entries) {
            # Solo limpia archivos del propio formulario, por cortesia.
            # next if ($file !~ /$TS/);
            if (-f "$path_answer_dir/$file") {
                if ((stat("$path_answer_dir/$file"))[9] < (time - 600)) {
                    unlink "$path_answer_dir/$file";
                };
            };
        };
    };
}; # garbage_collection

# ------------------------------------------------------------------------- #
# Aborta y sale con un mensaje de error.
sub aborta {
    #~ print "Content-Type: text/html\n\n";
    print "\n<html><head><title>Error</title></head><body><p>".$_[0]."</p></body></html>";
    exit;
}; # aborta
#-------------------------------END LIBRERIA--------------------

return 1;
