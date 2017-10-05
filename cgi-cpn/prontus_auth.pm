#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

package prontus_auth;
use Digest::MD5 qw(md5_hex);

sub check_password {
    my $input_password = $_[0];
    my $stored_password = $_[1];

    if (&load_module()) {
        # REF: https://gist.github.com/gcrawshaw/1071698/fe4a2ac69d845a65a093a23c4899fd9d80d5c466
        # Obtener el SALT, son 22 caracteres en base64.
        if ($stored_password =~ /^\$2a\$\d{2}\$([A-Za-z0-9+\\.\/]{22})/s) {
            my $match = &encrypt_password_bcrypt($input_password, $1); # Se usa el mismo salt para encriptar la contraseña ingresada por el usuario.
            my $bad = 0;

            # Se compara letra por letra para incrementar la seguridad.
            for (my $x = 0; $x < length $match; $x++) {
                $bad++ if substr($match, $x, 1) ne substr($stored_password, $x, 1);
            }

            return ($bad == 0);
        }
    }

    return 0;
};

sub if_passwd_expired {
    my $fec_exp = $_[0];

    if (time > $fec_exp) {
        return 1;
    } else {
        return 0;
    }
};

sub check_if_new_hash {
    my $username = $_[0];
    my $hash = $_[1];

    foreach $key (keys %prontus_varglb::USERS) {
        $value = $prontus_varglb::USERS{$key};
        my ($users_nom, $users_usr, $users_psw, $users_perfil) = split /\|/, $value;

        if (($users_usr eq $username)) {
            if ($users_psw =~ /^\$2a\$\d{2}\$([A-Za-z0-9+\\.\/]{22})([A-Za-z0-9+\\.\/]{31})/s) {
                if ($hash eq $2) {
                    return $users_psw;
                }
            }
        }
    }

    return $hash;
};

sub encrypt_password_bcrypt {
    if (&load_module()) {
        my $password = shift;
        my $salt = shift || &generate_salt();
        my $settings = '$2a$10$' . $salt;

        return Crypt::Eksblowfish::Bcrypt::bcrypt($password, $settings);
    } else {
        return md5_hex($password);
    }
};

sub generate_salt {
    my $itoa64 = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    my $salt = '';
    $salt .= substr($itoa64,int(rand(64)),1) while length($salt) < 16;

    return en_base64($salt);
};

# Para el nuevo tipo de contraseña se usa solo el hash, no todo el string.
sub get_hash_for_cookie {
    my $hash = $_[0];

    return $hash if (length $hash < 60);

    if ($hash =~ /^\$2a\$\d{2}\$([A-Za-z0-9+\\.\/]{22})([A-Za-z0-9+\\.\/]{31})/s) {
        return $2; # devuelve solo el hash, ultimos 31 caracteres.
    } else {
        return $hash;
    }
};

# Para retrocompatibilidad.
sub load_module {
    return 1 if ($Crypt::Eksblowfish::Bcrypt::VERSION); # ya estaba cargando en la misma ejecucion.

    eval "use Crypt::Eksblowfish::Bcrypt qw(bcrypt_hash en_base64);";

    if ($@) {
        print STDERR "Error : $@\n";
        return 0;
    } else {
        return 1;
    }
};

sub generate_password {
    my $length = $_[0];
    my $chars1 = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'; # al menos 1 en mayuscula.
    my $chars2 = '0987654321';
    my $chars3 = '!%&@#$^*?_~.';
    my @passwd;

    $length = 8 if ($length < 8);
    $length = $length - 2; # dejamos dos espacios para numero y caracter.

    push @passwd, substr($chars1, int(rand(length($chars1))), 1) while scalar(@passwd) < $length;
    push @passwd, substr($chars2, int(rand(length($chars2))), 1); # toma 1
    push @passwd, substr($chars3, int(rand(length($chars3))), 1); # toma 1

    my $str;

    # shuffle.
    for (0 .. scalar(@passwd)) {
        $str .= splice @passwd, rand @passwd, 1;
    }

    return $str;
}

return 1;