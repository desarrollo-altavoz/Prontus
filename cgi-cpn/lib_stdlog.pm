#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

package lib_stdlog;
use strict;
use warnings;
no warnings 'uninitialized';

# ---------------------------------------------------------------
sub set_stdlog {
# Implementa log de errores de max dado, rotandolo.
# Si los rotados son mas de 10, borra el mas antiguo para que no se acumulen.
# Posee comportamiento adaptivo para win o linux

    my $path_script = shift; # habitualmente $0
    my $max_size = shift; # habitualmente 51200 (50k)
    my $nom_dir4log = shift;  # optativo
    my $log_file;
    $nom_dir4log = 'prontus_error_log' if ($nom_dir4log eq '');

    $path_script = $0;
    use FindBin '$Bin';
    my $dir = "$Bin/$nom_dir4log";

    if ($path_script =~ /(\w+\.\w+)$/) {
        $log_file = "$1.error.log";
    } else {
        $log_file = 'error.log';
    };

    use glib_fildir_02;
    # print STDERR "dir[$dir]\n";
    # print STDERR "log_file[$log_file]\n";
    &glib_fildir_02::check_dir($dir) || return 0;

    if ((-s "$dir/$log_file") > $max_size) {
        use File::Copy;
        use glib_hrfec_02;
        my $ts_file = &glib_hrfec_02::get_dtime_pack4();
        &File::Copy::copy("$dir/$log_file", "$dir/$log_file.$ts_file"); # lo rota
        open (STDERR, ">$dir/$log_file"); # abre el nuevo
        &do_garbage($dir, $log_file); # borra el mas antiguo si es q hay mas de 10
    } else {
        open (STDERR, ">>$dir/$log_file");
    };
};
# ---------------------------------------------------------------
sub do_garbage {
    # garbage
    my $dir = shift;
    my $nom_log = shift;

    # print STDERR "dir[$dir] nom_pattern[$nom_pattern]\n";
    opendir(DIRHANDLE, $dir) || warn "ERROR: no se puede leer directorio actual\n";
    my @dir_list = readdir(DIRHANDLE);
    my @dir_list_out = sort grep(/^$nom_log\.\d{14}$/, @dir_list); # de menor a mayor
    my $num_files = @dir_list_out;
    # print STDERR "num_files[$num_files]\n";
    if ($num_files > 10) {
        # borra el mas antiguo que es el primero de la lista
        print STDERR "borrando[$dir_list_out[0]] por ser log mas antiguo\n";
        unlink "$dir/$dir_list_out[0]";
    };
};

# ---------------------------------------------------------------
return 1;
