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
$SERVER_SMTP = '';  # Servidor SMTP.

%MULTIVISTAS = ();
$SEPARADOR = ';';
$DELIMITADOR = '"';
$MAX_COLS = 6;
$MAX_ROWS = 50;

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
    # print STDERR "path_answer_dir[$path_answer_dir]\n";
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
# --------------------------------------------------------------------------------------------------
sub add_to_csv {

    my $data = shift;
    $data = &glib_str_02::trim($data); # Elimina espacios para que no molesten.
    $data =~ s/\"/\'\'/gs; # Convierte comillas para que no arruinen el archivo csv.
    $data =~ s/\r//gs;     # 1.5 Elimina retornos de carro para que no arruinen el archivo csv.
    return "$DELIMITADOR$data$DELIMITADOR$SEPARADOR";
};
# --------------------------------------------------------------------------------------------------
sub array_to_csv {

    my @arr = @_;
    my $total = $#arr;
    my $row = '';
    for(my $i = 0; $i <= $total; $i++) {
        $row = $row . &lib_form::add_to_csv($arr[$i]);
    };
    return $row;
};

# ------------------------------------------------------------------------- #
# Aborta y sale con un mensaje de error.
sub aborta {
    #~ print "Content-Type: text/html\n\n";
    print "\n<html><head><title>Error</title></head><body><p>".$_[0]."</p></body></html>";
    exit;
}; # aborta

# -------------------------------------------------------------------#
# Rescata y valida las variables del chorro.
sub getFormData {
    my($pair,$buffer);
    my %FORM;
    if ($ENV{'REQUEST_METHOD'} eq 'GET') {
        $buffer = $ENV{'QUERY_STRING'};
    } else {
        read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
    };
    my(@pairs) = split(/&/, $buffer);
    foreach $pair (@pairs) {
        my($name, $value) = split(/=/,$pair);
        # Un-Webify plus signs and %-encoding
        $value =~ tr/+/ /;
        $value =~ s/%([0-9A-Ha-h]{2})/pack("c",hex($1))/ge;
        # 1.9 $value =~ s/~!/ ~!/g;
        $value =~ s/\.\.\///g; # 1.4 Elimina toda referencia de directorios hacia atras.
        # 1.9 $value =~ s/\|//g;     # 1.4 Elimina toda posibilidad de activar pipes.
        $value =~ s/\x00//g;   # 1.4 Elimina nulls.
        $value =~ s/\x1B//g;   # 1.4 Elimina escapes.
        $value =~ s/[<>%!\|\\\~\$]/ /g; # 1.9 Elimina caracteres peligrosos
        # $value =~ s/[\+\.\^\$\(\)\[\]\{\}\|\\]//g;   # 1.8 Elimina caracteres reservados de Perl.
        $name = lc $name; # 1.3
        $FORM{$name} = $value;
    };
    # Valida variables.
    $FORM{'ts'} =~ s/[^\d]//g; # Elimina todos los no-numeros.
    $FORM{'prontus'} =~ s/[^\w\.\-]//g; # Elimina caracteres no validos como nombres de prontus.
    return \%FORM;
    # print "<p>FILTROACTIVO = $FILTROACTIVO $FORMfechaini $FORMfechafin"; # debug
}; # getFormData
#-------------------------------END LIBRERIA--------------------


return 1;
