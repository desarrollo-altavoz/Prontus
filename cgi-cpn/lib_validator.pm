#!/usr/bin/perl

package lib_validator;


# --------------------------------------------------------------------#
# Chequea un telefono.
# Si hay problemas retorna 0, si no, 1.
sub chequea_telefono {
    my $fono = shift;
    if ($fono !~ /\d{4,}/g) {
        return 0;
    };
    return 1;
}; # chequeaTelefono

# --------------------------------------------------------------------#
# Chequea direccion email.
# Si hay problemas retorna 0, si no, 1.
sub chequea_email {
    my $eml = shift;
    if ($eml !~ /^[a-zA-Z0-9\.,\-_\']+\@[a-zA-Z0-9\.\-]+\.[a-zA-Z]+$/g) {
        return 0;
    };
    return 1;
}; # chequeaEMail

# --------------------------------------------------------------------#
# Chequea el digito verificador.
# Si hay problemas retorna 0, si no, 1.
sub chequea_rut {
    my($rut) = $_[0];
    my($i);
    $rut =~ s/[^0-9Kk]//g; # Elimina todo lo no-numerico.
    if ($rut eq '') {
        return 0;
    };
    my($dvr,$suma,$mul,$dvi) = (0,0,2,0);
    my($drut) = lc(substr($rut,-1,1));
    $rut = substr($rut,0,(length($rut)-1));
    my(@rut) = split(//,$rut);
    if ( $drut eq 'k' ) {
        $drut = 1;
    };
    for ($i= length($rut) -1 ; $i >= 0; $i--) {
        $suma = $suma + $rut[$i] * $mul;
        if ($mul == 7) {
            $mul = 2;
        } else {
            $mul++;
        };
    };
    my($res) = $suma % 11;
    if ($res==1) {
        $dvr = 1;
    } else {
        if ($res == 0) {
            $dvr = 0;
        } else {
            $dvi = 11 - $res;
            $dvr = $dvi;
        };
    };
    if ( $dvr != $drut ) {
        return 0;
    } else {
        return 1;
    };
}; # chequeaDV

#-------------------------------END LIBRERIA--------------------

return 1;
