#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

package lib_loading;

#~ La respuesta hacia el navegador deberia tener los siguientes parametros:
#~      loading: 1 o 0 si el proceso está todavia cargando
#~      total: total en caso de que haya que hacer algun calculo
#~      actual: Se usa con el atributo "total"
#~      error: Para indicar que hubo error
#~      msg: Acá se puede poner algún mensaje

our $STARTED = 0;
our $FILE_LOADING;
our $REL_DIR;
our $FULL_DIR;

use glib_fildir_02;

# ------------------------------------------------------------------------------
sub init {

    my $file = $_[0];

    return 0 unless($file);

    $FILE_LOADING = $file;

    $REL_DIR = "$prontus_varglb::DIR_CPAN/procs/loading";
    $FULL_DIR = "$prontus_varglb::DIR_SERVER$REL_DIR";
    &glib_fildir_02::check_dir($FULL_DIR);

    $STARTED = 1;

    return 1;
}

# ------------------------------------------------------------------------------
sub update_loading {

    my $total = $_[0];
    my $actual = $_[1];
    my $msg = $_[2];

    return if(! $lib_loading::STARTED);
    $msg = '' unless($msg);
    $msg = &fix_message($msg);

    #~ print STDERR "Escribiendo archivo json: $lib_loading::FULL_DIR/$lib_loading::FILE_LOADING\n";
    my $respuesta = '{"loading":"1", "total":"'.$total.'", "actual":"'.$actual.'", "msg":"'.$msg.'", "status":"0"}';
    &glib_fildir_02::write_file("$lib_loading::FULL_DIR/$lib_loading::FILE_LOADING", $respuesta);

};

# ------------------------------------------------------------------------------
sub finish_loading {
# Status: 0 -> Error, 1 -> No hubo Error

    my $status = $_[0];
    my $msg = $_[1];

    return if(! $lib_loading::STARTED);
    $status = '0' if($status eq '');
    # $msg = '' unless($msg);
    $msg = &fix_message($msg);

    #~ print STDERR "Escribiendo archivo json: $lib_loading::FULL_DIR/$lib_loading::FILE_LOADING\n";
    my $respuesta = '{"loading":"0", "total":"100", "actual":"100", "msg":"'.$msg.'", "status":"'.$status.'"}';
    &glib_fildir_02::write_file("$lib_loading::FULL_DIR/$lib_loading::FILE_LOADING", $respuesta);
};

# ------------------------------------------------------------------------------
sub fix_message {

    my $msg = $_[0];

    # Para corregir codificaciones
    if ($msg ne '') {
        $msg =~ s/\s+/ /sg;

        my $tmp_msg = $msg;
        my $es_utf8 = utf8::decode($tmp_msg);
        if(! $es_utf8) {
            print STDERR "Convirtiendo a utf8 el mensaje";
            utf8::encode($msg);
        };
    };
    return $msg;
}

return 1;
