#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

#-------------------------------COMENTARIO GLOBAL---------------
#---------------------------------------------------------------
# PROPOSITO.
#-----------
# Implementa rutinas para manejar edicion concurrente de artics y ports, pero solo a modo de
# warnings informativos, sin establecer bloqueos.

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#------------------------
# 1.0 - prontus 11.0.0 - ycc - Primera Version.

#---------------------------------------------------------------


#-------------------------------BEGIN LIBRERIA-------------
#---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
#---------------------------
package lib_multiediting;

use strict;
use glib_fildir_02;

our $RELDIR_CONCURRENCY = '/cpan/data/users/concurrency';
our $MAX_DAY_GARBAGE = 5;

#---------------------------------------------------------------#
# SUB-RUTINAS.
#---------------------------------------------------------------#
sub send_ping {
    # Crea archivo de concurrencia

    my ($document_root, $prontus_id, $recurso, $tipo_recurso, $current_user, $id_session) = @_;
    my $dir = "$document_root/$prontus_id$lib_multiediting::RELDIR_CONCURRENCY/$tipo_recurso";
    &glib_fildir_02::check_dir($dir);
    # print STDERR "send_ping[$dir/$recurso.$current_user.$id_session]\n";

    &glib_fildir_02::write_file("$dir/$recurso.$current_user.$id_session", '');

};

sub lock_recurso {
    # Escribe en un archivo el primer usuario que tomo un recurso. (art|port)

    my ($document_root, $prontus_id, $recurso, $tipo_recurso, $current_user, $id_session, $tipo_bloqueo) = @_;
    my $dir = "$document_root/$prontus_id$lib_multiediting::RELDIR_CONCURRENCY/$tipo_recurso/lock";
    &glib_fildir_02::check_dir($dir);
    my $file = "$dir/$recurso.lck";
    # print STDERR "lock_recurso[$file]\n";

    if (!-f $file) {
        # es el primero en editar el recurso.
        &glib_fildir_02::write_file($file, "$current_user|$id_session");
        #~ print STDERR "NEW!: tipo_recurso[$tipo_recurso], current_user[$current_user], id_session[$id_session]\n";
        return 0;
    } else {
        my $buffer = &glib_fildir_02::read_file($file);
        $buffer =~ s/\n//;
        my ($user, $sessid) = split(/\|/, $buffer);
        #~ print STDERR "tipo_recurso[$tipo_recurso], user[$user], sessid[$sessid]\n";
        if ($user eq $current_user && $sessid eq $id_session) {
            #~ print STDERR "Mismo usuario, actualiza\n";
            # Si es el mismo usuario, actualiza el archivo para que tenga una fecha de modificacion mas nueva.
            &glib_fildir_02::write_file($file, "$current_user|$id_session");
            return 0;
        } else {
            # Si no es el mismo usuario... debe retonar el tipo de lock que se aplicará
            # El tipo de lock está setiado en el cfg.
            my $is_recent = &is_ping_reciente("$file");
            if ($is_recent) {
                # Debe retornar el tipo de lock... 0, 1 o 2.
                return $tipo_bloqueo;
            } else {
                return 0;
            }
        }
    };
};

# ---------------------------------------------------------------
sub get_concurrency {
# Detecta uso del $recurso por usuarios distintos a $current_user

    my ($document_root, $prontus_id, $recurso, $tipo_recurso, $current_user, $id_session) = @_;
    # print STDERR "CHECKing [$tipo_recurso][$recurso]\n";
    my $str = '';
    my $dir = "$document_root/$prontus_id$lib_multiediting::RELDIR_CONCURRENCY/$tipo_recurso";
    my (@lisdir) = &glib_fildir_02::lee_dir($dir) if (-d $dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    my %users_incluidos;
    foreach my $k (@lisdir) {
        next if (! -f "$dir/$k");
        # print STDERR "CHECK[$k]\n"; # inicio.php.admin
        my $is_recent = &is_ping_reciente("$dir/$k");
        if ( ($k =~ /$recurso\.(.+?)\.(.+?)$/) && ($is_recent) ) {
            my $user_recurso = $1;
            my $session_recurso = $2;
            # print STDERR "user_recurso[$user_recurso]session_recurso[$session_recurso]\n";
            # devuelve todos los users que no sean el actual y que esten usando el recurso
            if ("$user_recurso.$session_recurso" ne "$current_user.$id_session") {
                $users_incluidos{$user_recurso}++;
            };
        };
    };

    foreach my $user (keys %users_incluidos) {
        if ($users_incluidos{$user} > 1) {
            $str .= "$user ($users_incluidos{$user} usuarios m&aacute;s), ";
        } else {
            $str .= "$user, ";
        };
    };
    $str =~ s/\, $//;
    return $str;
};


# ---------------------------------------------------------------
sub garbage_collector {
# Elimina los locks mas antiguos de X dias
    my ($document_root, $prontus_id, $tipo_recurso) = @_;

    my $dir = "$document_root/$prontus_id$lib_multiediting::RELDIR_CONCURRENCY/$tipo_recurso/lock";
    if (-d $dir) {
        my $cmd = "find $dir -mtime +$lib_multiediting::MAX_DAY_GARBAGE  -name '*.lck' -exec rm \{\} \\;";
        my $res = `$cmd`;
    }
};

# ---------------------------------------------------------------
sub free_concurrency {
# Elimina los flgs de recursos en uso para el user actual

    my ($document_root, $prontus_id, $tipo_recurso, $current_user, $id_session) = @_;

    my $dir = "$document_root/$prontus_id$lib_multiediting::RELDIR_CONCURRENCY/$tipo_recurso";
    my (@lisdir) = &glib_fildir_02::lee_dir($dir) if (-d $dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

    foreach my $k (@lisdir) {
        next if (! -f "$dir/$k");
        if  ($k =~ /(.+?)\.$current_user\.$id_session$/) {
            unlink "$dir/$k";
        };
    };

};

# ---------------------------------------------------------------
sub free_lock {
# Elimina los flgs de recursos en uso para el user actual

    my ($document_root, $prontus_id, $tipo_recurso, $current_user, $id_session) = @_;

    my $dir = "$document_root/$prontus_id$lib_multiediting::RELDIR_CONCURRENCY/$tipo_recurso/lock";
    my (@lisdir) = &glib_fildir_02::lee_dir($dir) if (-d $dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

    foreach my $k (@lisdir) {
        next if (! -f "$dir/$k");
        my $buffer = &glib_fildir_02::read_file("$dir/$k");
        $buffer =~ s/\n//;
        my ($user, $sessid) = split(/\|/, $buffer);
        if ($user eq $current_user && $sessid eq $id_session) {
            unlink "$dir/$k";
        };
    };
};

# ---------------------------------------------------------------
sub is_ping_reciente {

    my $file_recurso_dot_user = $_[0];

    my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,
    $mtime, $ctime,  $blksize,  $blocks) = stat $file_recurso_dot_user;
    # print STDERR "viendo recent[$file_recurso_dot_user]\n";
    # Si los seg. de antiguedad de la pagina son mayores que 20
    if ((time - $mtime) > 20) {
        # print STDERR "ELIMINANDO[$file_recurso_dot_user]\n";
        unlink $file_recurso_dot_user;
        return 0; # ping antiguo
    } else {
        # print STDERR "NO ELIMINANDO[$file_recurso_dot_user]\n";
        return 1; # ping reciente --> recurso en edicion
    };

};

#--------------------------------------------------------------------#
return 1;
#-------------------------------END LIBRERIA---------------------
