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

our $BCRYPT_AVAILABLE = 0;
eval "use Crypt::Eksblowfish::Bcrypt qw(bcrypt_hash en_base64);";
if ($@) {
    $BCRYPT_AVAILABLE = 0;
} else {
    $BCRYPT_AVAILABLE = 1;
}

our $PWS_MAX_LENGTH = 32;
our $PWS_MIN_LENGTH = 8;
our $PWS_TO_REMEMBER = 0;
our $PWS_COMPARE_PREVIOUS = 0;
our $USERS_USR_ID;
our $USERS_USR;
our $USERS_PSW;
our $USERS_NOM;
our $USERS_PERFIL;
our $USERS_EMAIL;
our $USERS_EXP_DAYS = 0;
our $USERS_FEC_EXP = 0;
our $EXTERNAL_PROCESS = '';

eval "use prontus_auth_custom;";


# ---------------------------------------------------------------
sub check_valid_login {
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
        if ($usr eq 'admin') {
            my $pass_sysadmin = &glib_fildir_02::read_file($flag_sysadmin);
            $pass_sysadmin =~ s/\s+//g;
            print STDERR "[$psw] eq [$pass_sysadmin]\n";
            if ($psw eq $pass_sysadmin) {
                $USERS_USR_ID = 1;
                $USERS_USR = $usr;
                $USERS_PSW = md5_hex($pass_sysadmin);
                return 2;
            }
        }
        return -1;
    }

    foreach my $user_id (keys %prontus_varglb::USERS) {
        $USERS_USR_ID = $user_id + 0;
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL, $USERS_EXP_DAYS, $USERS_FEC_EXP) = split /\|/, $prontus_varglb::USERS{$USERS_USR_ID};
        $USERS_EXP_DAYS += 0;
        $USERS_FEC_EXP += 0;
        if ($USERS_USR eq $usr) {
            if (&check_password($psw, $USERS_PSW)) {
              return 3 if (&is_passwd_expired());
              return 1;
            }
        }
    }

    # si no esta presente este archivo, permite entrar con admin/prontus y luego obliga a cambiar la pass
    my $flag_file = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/prontus_flag_admin.txt";
    if ($usr eq 'admin' && $psw eq 'prontus') {
        if (!(-f $flag_file)) {
            # Resetear clave admin
            ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $prontus_varglb::USERS{'1'}; # para rescatar email
            $USERS_PSW = &encrypt_password('prontus');
            $USERS_EXP_DAYS = 0;
            $USERS_FEC_EXP = 0;
            $prontus_varglb::USERS{'1'} = 'Administrador|admin|' . $USERS_PSW . '|A|' . $USERS_EMAIL. "|0|0";
            # guardamos los datos
            &lib_prontus::close_dbm_files();
            # desactivamos el reset
            &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/prontus_flag_admin.txt", 'No server domain, please try later.');
            return 1;
        }
    }
    return 0;
}
# ---------------------------------------------------------------
sub check_valid_hash_psw {
    my ($username, $hash_psw) = @_;
    # Devuelve el password encriptado que corresponda. Si es nuevo, lo devuelve completo, ya que en la cookie
    # se almacena solo el hash.
    my $crypted_pass = &check_if_new_hash($username, $hash_psw);

    # Si esta este archivo, solo deja pasar con user admin y la pass contenida en el.
    # Los demas usuarios son bloqueados.
    my $flag_sysadmin = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/prontus_flag_sysadmin.txt";
    if (-f $flag_sysadmin) { # sysadmin
        if ($username eq 'admin') {
            my $pass_sysadmin = &glib_fildir_02::read_file($flag_sysadmin);
            $pass_sysadmin =~ s/\s+//g;
            my $crypted_sys_pass = md5_hex($pass_sysadmin);

            if ($crypted_pass eq $crypted_sys_pass) {
                ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL, $USERS_EXP_DAYS, $USERS_FEC_EXP) = split /\|/, $prontus_varglb::USERS{'1'};
                $USERS_EXP_DAYS += 0;
                $USERS_FEC_EXP += 0;
                $USERS_USR_ID = 1;
                return 2;
            }
        }
        return -1;
    } else { # users normales
        foreach my $user_id (keys %prontus_varglb::USERS) {
            # print "key[$key] y value[$value]<br>";
            ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL, $USERS_EXP_DAYS, $USERS_FEC_EXP) = split /\|/, $prontus_varglb::USERS{$user_id};
            $USERS_EXP_DAYS += 0;
            $USERS_FEC_EXP += 0;
            $USERS_USR_ID = $user_id + 0;

            if (($USERS_USR eq $username) && ($crypted_pass eq $USERS_PSW)) {
                return 3 if (&is_passwd_expired());
                return 1;
            }
        }
        return 0;
    }
}
# ---------------------------------------------------------------
sub is_passwd_expired {
    if ($USERS_USR_ID == 1) {
        return 0;
    }

    if ($USERS_EXP_DAYS < 1) {
        return 0;
    }

    if ($USERS_FEC_EXP ne '' && time > $USERS_FEC_EXP) {
        return 1;
    } else {
        return 0;
    }
}
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
sub check_password {
    my $input_password = $_[0];
    my $stored_password = $_[1];

    if (length($stored_password) == 60) {
        if ($BCRYPT_AVAILABLE) {
            # REF: https://gist.github.com/gcrawshaw/1071698/fe4a2ac69d845a65a093a23c4899fd9d80d5c466
            # Obtener el SALT, son 22 caracteres en base64.
            if ($stored_password =~ /^\$2a\$\d{2}\$([A-Za-z0-9+\\.\/]{22})/s) {
                my $match = &encrypt_password($input_password, $1); # Se usa el mismo salt para encriptar la contraseña ingresada por el usuario.
                my $bad = 0;

                # Se compara letra por letra para incrementar la seguridad.
                for (my $x = 0; $x < length $match; $x++) {
                    $bad++ if substr($match, $x, 1) ne substr($stored_password, $x, 1);
                }

                return ($bad == 0);
            }
        }
    }

    my $crypted_pass;
    if (length($stored_password) == 32) {
        $crypted_pass = md5_hex($input_password);
    } else {
        $crypted_pass = crypt($input_password, $stored_password);
    }
    if ($crypted_pass eq $stored_password) {
        return 1;
    }

    return 0;
};
# ---------------------------------------------------------------
sub encrypt_password {
    my $password = shift;

    if ($BCRYPT_AVAILABLE) {
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
sub save_new_password {
    #  si el usuario ya existe validar que la clave es distinta a las anteriores
    my ($user_id, $new_psw, $new_mail) = @_;
    my ($users_nom, $users_usr, $old_users_psw, $users_perfil, $users_mail, $users_exp_days, $users_fec_exp) = split /\|/, $prontus_varglb::USERS{$user_id};

    if ($PWS_COMPARE_PREVIOUS) {
        my $buffer = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/pass_store/$user_id.txt");
        my @stored = split /\|/, $buffer;
        push (@stored, $old_users_psw) if ($old_users_psw ne '');
        for (my $i = 0; $i < scalar @stored; $i++) {
            if ($stored[$i] eq '') { next; }
            if (&check_password($new_psw, $stored[$i])) {
                print STDERR "Esta contraseña ya ha sido usada previamente\n";
                return "Esta contraseña ya ha sido usada previamente";
            }
        }
    }

    $users_fec_exp = 0;
    $users_fec_exp = time + (int($users_exp_days) * 86400) if ($users_exp_days > 0);

    if ($new_mail) {
        $users_mail = $new_mail;
    }

    my $new_psw_hash = &prontus_auth::encrypt_password($new_psw);

    $prontus_varglb::USERS{$user_id} = $users_nom . '|' .  $users_usr . '|' . $new_psw_hash . '|' . $users_perfil . '|' . $users_mail . '|' . $users_exp_days . '|' . $users_fec_exp;

    &store_old_passwords($user_id, $old_users_psw);

    &lib_prontus::close_dbm_files();

    if ($EXTERNAL_PROCESS ne '') {
        print STDERR "save_new_password exec[$EXTERNAL_PROCESS $prontus_varglb::PRONTUS_ID]\n";
        system("$EXTERNAL_PROCESS $prontus_varglb::PRONTUS_ID $users_usr $new_psw_hash 1>/dev/null 2>/dev/null &");
    }
    return '';
}
# ---------------------------------------------------------------
sub store_old_passwords {
    if ($PWS_TO_REMEMBER == 0) {
        return;
    }

    my $user_id  =  $_[0];
    my $old_pass =  $_[1];

    if ($old_pass eq '') {
        return;
    }
    &glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/pass_store/");
    my $input = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/pass_store/$user_id.txt");

    my $output = $old_pass .'|';
    if ($input ne '') {
        my @stored = split /\|/, $input;
        my $i = 1;
        # se decrementa ya que una de las antiguas se almacena en los usuarios
        $PWS_TO_REMEMBER--;
        while ($i < $PWS_TO_REMEMBER && $i <= scalar(@stored)) {
            $output .= $stored[$i - 1] .'|';
            $i++;
        }
    }

    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/pass_store/$user_id.txt", $output);
}
# ---------------------------------------------------------------
sub is_user_valido {
    my $usr = $_[0];
    foreach my  $key (keys %prontus_varglb::USERS) {
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL, $USERS_EXP_DAYS, $USERS_FEC_EXP) = split /\|/, $prontus_varglb::USERS{$key};
        if ($USERS_USR eq $usr)  {
            $USERS_USR_ID = $key;
            return 1;
        }
    }
    return 0;
}
# ---------------------------------------------------------------
sub is_valid_password {
    my $psw = $_[0];

    if ($psw =~ /^\s+$/) {
        return 'Password no puede contener solamente espacios.';
    }

    my $psw_length = length($psw);
    if ($psw_length > $PWS_MAX_LENGTH || $psw_length < $PWS_MIN_LENGTH) {
        return "La nueva contraseña debe estar compuesta por un mínimo de $PWS_MIN_LENGTH caracteres y máximo $PWS_MAX_LENGTH caracteres.";
    }

    if (lc $psw eq 'prontus') {
        return "Contraseña no válida.<br>Su contraseña no puede ser \"$psw\", por favor ingrese una distinta";
    }

    if ($psw !~ /([a-z].*[A-Z])|([A-Z].*[a-z])/) {
        return 'La contraseña debe tener al menos una letra mayúscula, una letra minúscula, un número y un caracter especial: !%&@#$^*?_.';
    }

    if ($psw !~ /([0-9])/) {
        return 'La contraseña debe tener al menos una letra mayúscula, una letra minúscula, un número y un caracter especial: !%&@#$^*?_.';
    }

    if ($psw !~ /([\!%&@#\$\^\*\?_\.])/) {
        return 'La contraseña debe tener al menos una letra mayúscula, una letra minúscula, un número y un caracter especial: !%&@#$^*?_.';
    }
    return '';
}

return 1;
