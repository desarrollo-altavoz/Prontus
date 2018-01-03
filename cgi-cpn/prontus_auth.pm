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
use strict;
use Digest::MD5 qw(md5_hex);

our $USERS_USR;
our $USERS_PSW;
our $USERS_NOM;
our $USERS_PERFIL;
our $USERS_EMAIL;
our $USERS_EXP_DAYS;
our $USERS_FEC_EXP;

our %FORM;

# ---------------------------------------------------------------
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
# ---------------------------------------------------------------
sub if_passwd_expired {
    my $fec_exp = $_[0];

    if (time > $fec_exp) {
        return 1;
    } else {
        return 0;
    }
};
# ---------------------------------------------------------------
sub check_if_new_hash {
    my $username = $_[0];
    my $hash = $_[1];

    foreach my $key (keys %prontus_varglb::USERS) {
        my $value = $prontus_varglb::USERS{$key};
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
# ---------------------------------------------------------------
sub encrypt_password_bcrypt {
    my $password = shift;

    if (&load_module()) {
        my $salt = shift || &generate_salt();
        my $settings = '$2a$10$' . $salt;

        return Crypt::Eksblowfish::Bcrypt::bcrypt($password, $settings);
    } else {
        return md5_hex($password);
    }
};
# ---------------------------------------------------------------
sub generate_salt {
    my $itoa64 = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    my $salt = '';
    $salt .= substr($itoa64,int(rand(64)),1) while length($salt) < 16;

    return en_base64($salt);
};
# ---------------------------------------------------------------
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
# ---------------------------------------------------------------
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
# ---------------------------------------------------------------
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
# ---------------------------------------------------------------
sub user_valido {
# retorna:
# 0: user no valido normal
# 1: user valido normal
# -1 : user no valido por existir prontus_flag_sysadmin.txt
# 2: user valido luego de comprobar clave contra prontus_flag_sysadmin.txt

    my ($usr, $psw) = @_;

    # Si esta este archivo, solo deja pasar con user admin y la pass contenida en el.
    # Los demas usuarios son bloqueados.
    my $flag_sysadmin = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/prontus_flag_sysadmin.txt";
    if (-f $flag_sysadmin) {
        my $pass_sysadmin = &glib_fildir_02::read_file($flag_sysadmin);
        if (($psw eq $pass_sysadmin) && ($usr eq 'admin')) {
            $USERS_USR = $usr;
            $USERS_PSW = &pronntus_auth::encrypt_password_bcrypt($pass_sysadmin);
            return 2;
        } else {
            return -1;
        }
    }

    foreach my $key (keys %prontus_varglb::USERS) {
        my $val = $prontus_varglb::USERS{$key};
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL, $USERS_EXP_DAYS, $USERS_FEC_EXP) = split /\|/, $val;
        # print STDERR "\n\nTIPEADA[$psw] USERS_PSW[$USERS_PSW] CRYPT[" . crypt($psw, $USERS_PSW) . "]\n" if ($USERS_USR eq $usr);
        my $crypted_pass = '';

        if (length $USERS_PSW == 60) {
            if (($USERS_USR eq $usr) && &check_password($psw, $USERS_PSW)) {
              return 3 if (&if_passwd_expired($USERS_FEC_EXP) && $USERS_FEC_EXP ne '' && $USERS_EXP_DAYS > 0 && $key != 1); # se excluye al admin.
              return 1;
            }
        }

        if (length($USERS_PSW) == 32) {
            $crypted_pass = md5_hex($psw);
        } else {
            $crypted_pass = crypt($psw, $USERS_PSW);
        }
        if (($USERS_USR eq $usr) && ($crypted_pass eq $USERS_PSW)) {
            return 3 if (&if_passwd_expired($USERS_FEC_EXP) && $USERS_FEC_EXP ne '' && $USERS_EXP_DAYS > 0 && $key != 1);
            return 1;
        }
    }

    # si esta presente este archivo, permite entrar con admin/prontus y luego obliga a cambiar la pass
    my ($flag_file) = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/prontus_flag_admin.txt";
    if ( (!(-f $flag_file)) && ($usr eq 'admin') && ($psw eq 'prontus') ) {
        # Resetear clave admin
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $prontus_varglb::USERS{'1'}; # para rescatar email

        $prontus_varglb::USERS{'1'} = 'Administrador|admin|' . &encrypt_password_bcrypt('prontus') . '|A|' . $USERS_EMAIL;
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $prontus_varglb::USERS{'1'};

        # USERS
        my $linea = '';
        my $buffer = '';
        my $k;
        foreach $k (keys %prontus_varglb::USERS) {
            my $users_id = $k;
            my ($users_nom, $users_usr, $users_psw, $users_perfil, $users_email) = split /\|/, $prontus_varglb::USERS{$k};
            $linea = $users_id . '|' . $users_nom . '|' . $users_usr . '|' . $users_psw . '|' . $users_perfil . '|' . $users_email . "\n";
            $buffer .= $linea;
        }
        if ($buffer) {
            open (ARCHIVO,">$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/users.txt") || return 0;
            print ARCHIVO $buffer;
            close ARCHIVO;
        }

        &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/prontus_flag_admin.txt", 'No server domain, please try later.');
        return 1;
    }
    return 0;
};


return 1;
