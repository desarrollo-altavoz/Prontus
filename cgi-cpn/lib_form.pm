#!/usr/bin/perl

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
# Detecta si es plataforma win32, solo para ambiente web.
sub is_win32 {
    my $ruta_script = $ENV{'SCRIPT_FILENAME'};
    if ($ruta_script eq '') {
        $ruta_script = $ENV{'PATH_TRANSLATED'}; # win
    };
    if ($ruta_script =~ /^\w:/) {
        return 1; # Es Windows.
    } else {
        return 0; # Es Unix.
    };
}; # is_win32

# ------------------------------------------------------------------------- #
# Retorna las copias de del script que se encuentran corriendo.
sub myself_running {
    my($res) = qx/ps axww | grep $0 | grep -v ' grep ' | wc -l/;
    $res =~ s/\D//gs;
    return $res;
}; # myself_running

# ------------------------------------------------------------------------- #
# Aborta si hay mas de $max copias corriendo.
sub max_running {
    my($max) = $_[0];
    if (! &is_win32()) {
        if (&myself_running() > $max) {
            &aborta("Error: Servidor ocupado. Intente otra vez m&aacute;s tarde."); # 1.3.1 # 1.10
        };
    };
}; # max_running
# ------------------------------------------------------------------------- #
# Aborta y sale con un mensaje de error.
sub aborta {
    #~ print "Content-Type: text/html\n\n";
    print "\n<html><head><title>Error</title></head><body><p>".$_[0]."</p></body></html>";
    exit;
}; # aborta
#-------------------------------END LIBRERIA--------------------

return 1;
