#!/usr/bin/perl



# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO .
# -----------
# Este script se usa solo para PRONTUS-02, PRONTUS-03 y PRONTUS-04.
# Deriva de ap_art_public_01.pl (construido para www.mercuriovalpo.cl)
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------


# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------

# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------

# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 01 - Viernes 02/06/2000 - Primera Version.
# 1.1 - 05/07/2000 - Se agrega posibilidad de manipular archivos realmedia.
# 1.2 - 28/07/2000 - Se agrega posibilidad de manipular archivos asociados genericos.
# 1.3 - 20/09/2000 - soporte para que el script procese correctamente el path relativo al sitio del arch. de configuracion.
# 1.4 - 06/12/2000 - Modificaciones en la llamada a la rutina que carga y valida el archivo de configuracion del prontus.
# Ademas se oficializa la validacion del referer.
# 1.5 - 06/12/2000 - Re-estructuraciones varias para implementar limbo.
# 1.6 - 15/05/2001 - Extensiones para Prontus 5. Estas modificaciones se aplicaron antes de escribir este comentario.
# 1.7 - 16/05/2001 - Modificaciones para parametrizacion del protocolo (http o https) a traves del arch. de conf.
# 1.8 - 16/05/2001 - Revision general de detalles de forma.

# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0
# Prontus 8.0 - 23/05/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# Prontus 8.1 - 12/09/2002 - YCH - Soporte windows media y demases. Ver detalles en /release_prontus81.txt
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_fildir_02;
use lib_prontus;
use glib_cgi_04;
use glib_hrfec_02;
use DBI;
use glib_dbi_02;
use lib_tax;
use lib_artic;

# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM);

main: {

    # Rescatar parametros recibidos
    &glib_cgi_04::new();

    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    if ($prontus_varglb::IP_SERVER ne '') { # implica llamada desde ambiente web. # 1.23
        &lib_prontus::test_servers($ENV{'HTTP_REFERER'}); # Autentifica request.  con SERVER_PERM.
    };

    # user check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };


    $FORM{'_ts'} = &glib_cgi_04::param('_ts');
    if ($FORM{'_ts'} !~ /^\d{14}$/) {
        &glib_html_02::print_json_result(0, 'Artículo no válido', 'exit=1,ctype=1');
    };

    my $ports_ref = &artic_in_ports($FORM{'_ts'});
    if ($ports_ref !~ /^\s*$/) {
        &glib_html_02::print_json_result(0, "Artículo no puede ser borrado porque se encuentra publicado en las sgtes. portadas:\n\n${ports_ref}", 'exit=1,ctype=1');
    } else {
        &borra_artic($FORM{'_ts'});
    };

    &exec_postproceso_artborrar($FORM{'_ts'});

    &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------

sub artic_in_ports {
# Obtiene las portadas en donde se encuentra publicado un articulo

    my $ts = shift;

    # procesa edicion, vigente, la ultima y la base.
    my (@ediciones) = &lib_prontus::get_edics4update();

    my $referencias;
    foreach my $edic (@ediciones) {
        # print STDERR "edic[$edic]\n";
        # Dir destino de las portadas de la ed.
        $pathdir_seccs = $prontus_varglb::DIR_SERVER .
                        $prontus_varglb::DIR_CONTENIDO .
                        $prontus_varglb::DIR_EDIC .
                        "/$edic" .
                        $prontus_varglb::DIR_SECC;

        my @entries = &glib_fildir_02::lee_dir($pathdir_seccs);

        # Para cada port.
        foreach $port (@entries) {

            next if ($port =~ /^\./);

            # portada en el site
            $arch_seccion = "$pathdir_seccs/$port";

            my ($arch_xml) = $arch_seccion;
            $arch_xml =~ s/\/port\/(\w+?)\.\w*$/\/xml\/\1\.xml/;

            # template de la portada
            $path_tsec = $prontus_varglb::DIR_SERVER .
                        $prontus_varglb::DIR_TEMP .
                        $prontus_varglb::DIR_EDIC .
                        $prontus_varglb::DIR_NROEDIC .
                        $prontus_varglb::DIR_SECC . "/$port";

            # print STDERR "arch_xml[$arch_xml]\n";

            next if ((! -f $arch_xml) || ($port =~ /^preview/i));


            $text_seccion = &glib_fildir_02::read_file($arch_xml);
            $text_seccion = &lib_prontus::ajusta_crlf($text_seccion);
            
            #~ CVI - 16/08/2012 - Se optimiza
            if ($text_seccion =~ /<rowartic>\s*<dir>\d+?<\/dir>\s*<file>$ts<\/file>.*?<\/rowartic>/is) {
                $referencias .= "$edic/$port\n";
            }

            #~ # Rescatar la info de c/artic de la port actual
            #~ while ($text_seccion =~ /<rowartic>[ \n]*?<dir>(\d+?)<\/dir>[ \n]*?<file>(.*?)<\/file>[ \n]*?<area>(\d*?)<\/area>[ \n]*?<ord>(\d*?)<\/ord>[ \n]*?(<vb>(\w*?)<\/vb>)?[ \n]*?<?i?n?>?([\w\/\-]*?)<?\/?i?n?>?[ \n]*?<?o?u?t?>?([\w\/\-]*?)<?\/?o?u?t?>?[ \n]*?<?p?u?b?>?(\d?)<?\/?p?u?b?>?[ \n]*?<\/rowartic>/isg) {
                #~ my ($dirfecha,$art,$area,$prio,$pub,$ext_art,$vb) = '';
                #~ ($dirfecha,$art,$area,$prio,$vb,$pub) = ($1,$2,$3,$4,$6,$9);
                #~ # print STDERR "ENTRA con[$dirfecha,$art,$area,$prio,$vb,$in,$out]";
                #~ # print STDERR "art[$art]\n";
                #~ if ($art eq $ts) {
                    #~ # Articulo publicado en esta port
                    #~ $referencias .= "$edic/$port\n";
                #~ };
            #~ }; # while art. de esta portada


        }; # foreach portadas de la edicion

    }; # foreach

    $referencias = $referencias . "\n";
    return $referencias;
};
# ---------------------------------------------------------------
sub borra_artic {
    my $ts = shift;

    my $ddir = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . '/%%DIR_FECHA%%';
    my $dirpag = $prontus_varglb::DIR_SERVER . $ddir . $prontus_varglb::DIR_PAG;
    my $dirimg = $prontus_varglb::DIR_SERVER . $ddir . $prontus_varglb::DIR_IMAG;
    my $dirmedia = $prontus_varglb::DIR_SERVER . $ddir . $prontus_varglb::DIR_RMEDIA;
    my $dirasocfile =  $prontus_varglb::DIR_SERVER . $ddir . $prontus_varglb::DIR_ASOCFILE;
    my $dirswf = $prontus_varglb::DIR_SERVER . $ddir . $prontus_varglb::DIR_SWF;
    my $dirwmedia = $prontus_varglb::DIR_SERVER . $ddir . $prontus_varglb::DIR_WMEDIA;
    my $dirmmedia = $prontus_varglb::DIR_SERVER . $ddir . $prontus_varglb::DIR_MMEDIA;

    # Conectar a BD
    my $msg_err_bd;
    my $base;
    ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        &glib_html_02::print_pag_result("Error",$msg_err_bd . '<br>No es posible eliminar los artículos seleccionados.',1,'exit=1,ctype=1,link=nolink');
    };

    my $dir_fecha = &lib_prontus::get_dirfecha_by_ts($ts);

    my $dir_aux = $dirpag;
    $dir_aux =~ s/%%DIR_FECHA%%/$dir_fecha/is;

    # Borra pagina
    my @files2delete = glob("$dir_aux/$ts" . '.*');
    foreach my $file2delete (@files2delete) {
        unlink $file2delete;
        &lib_prontus::purge_cache($file2delete);
    };

    # Borra paginas de multivistas
    my $mv;
    foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
        my $dir_art_mv = $dir_aux;
        $dir_art_mv =~ s/(\d{8})\/pags/\1\/pags-$mv/;
        my @files2delete_mv = glob("$dir_art_mv/$ts" . '.*');
        foreach my $file2delete (@files2delete_mv) {
            unlink $file2delete;
            &lib_prontus::purge_cache($file2delete);
        };

    };

    my $path_artic_xml = "$dir_aux/$ts";
    $path_artic_xml =~ s/\/pags\/(\w+)$/\/xml\/\1\.xml/;

    # Antes de eliminarlo, lee articulo xml para luego poder determinar cuales son sus asocfiles
    # y sus tags
    my $buffer_artic = &glib_fildir_02::read_file($path_artic_xml);

    unlink $path_artic_xml;          # Borra xml
    &lib_prontus::write_log('Borrar', 'Articulo', $ts);

    # Borra imagenes
    &borrar_artic_files($dirimg, $ts, $dir_fecha);

    # Borra realmedia.
    &borrar_artic_files($dirmedia, $ts, $dir_fecha);

    # Borra windowsmedia
    &borrar_artic_files($dirwmedia, $ts, $dir_fecha);

    # Borra multimedia.
    &borrar_artic_files($dirmmedia, $ts, $dir_fecha);

    # Borra swf
    &borrar_artic_files($dirswf, $ts, $dir_fecha);

    # Borra arch. asociados. # 1.2
    $dir_aux = $dirasocfile;
    $dir_aux =~ s/%%DIR_FECHA%%/$dir_fecha/is;
    while ($buffer_artic =~ /<(ASOCFILE_\d+)>(.+?)<\/\1>/isg) {
        my $nom_af = "$dir_aux/$ts/$2";
        unlink $nom_af;
    };

    # Desasocia tags al artic
    my $sql_deltag = "delete from TAGSART where TAGSART_IDART='$ts'";
    $base->do($sql_deltag);


    if ($buffer_artic =~ /<_tags>(.+?)<\/_tags>/is) {
        my $tags_data = $1;
        &lib_artic::generar_relacionados_tagging($base, "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO", $tags_data);
#        my @tags = split(/ *, */, $tags_data);
#        foreach my $tag (@tags) {
#            my $sql = "select TAGS_ID from TAGS where TAGS_TAG = \"$tag\" and TAGS_COUNT > 0";
#            my $tags_id = &lib_prontus::existe_registro($sql, $base);
#            if ($tags_id) {
#                $sql = "update TAGS set TAGS_COUNT = (TAGS_COUNT - 1) where TAGS_ID = \"$tags_id\" ";
#            };
#            $base->do($sql);
#        };
    };
    # Borra relacionados manual
    $dir_aux = $dirpag;
    $dir_aux =~ s/%%DIR_FECHA%%/$dir_fecha/is;
    &lib_tax::borrar_relacionados_manualtax($dir_aux, $ts);

    # Obtiene taxonomia antes de eliminar
    if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^[1-3]$/) {
        ($secc, $tem, $stem) = &get_taxonomia($ts, $base);
    };

    # Elimina
    $base->do("delete from ART where ART_ID = '$ts'");

    # regenera relacionados
    if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^[1-3]$/) {
        &regen_art_relac($secc, $tem, $stem, $base);
    };

    $base->disconnect;

    # Borra cache listas de articulo
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");

    use FindBin '$Bin';
    my $rutaScript = $Bin;

    # regenera taxports
    my $fid;
    if ($buffer_artic =~ /<_fid>(.+?)<\/_fid>/is) {
      $fid = $1;
    };

    $secc = '0' if ($secc < 0); # para evitar el -1, ver dps por que get_taxonomia devuelve -1
    my $param_especif_taxport = $fid
                              . '/' . $secc
                              . '/' . $tem
                              . '/' . $stem;

    &call_taxports_regen($rutaScript, $param_especif_taxport);
    
    &call_list_regen($rutaScript, $param_especif_taxport);

    # DAM
    &call_dam2delete($ts, $rutaScript);

};

# --------------------------------------------------------------------#
sub borrar_artic_files {
    my $dir_aux = shift;
    my $ts = shift;
    my $dir_fecha = shift;

    $dir_aux =~ s/%%DIR_FECHA%%/$dir_fecha/is;
    @files2delete = glob($dir_aux . '/*' . $ts . '.*');
    unlink @files2delete;
};

# --------------------------------------------------------------------#
sub exec_postproceso_artborrar {
    my ($ts) = $_[0];
    my ($post_proceso) = $prontus_varglb::POST_PROCESO{'ART-BORRAR'};

    if ($post_proceso =~ /\( *([\w\.\\\/ ]+) *\)/) {

        $post_proceso = $1;
        # print STDERR "pp despues[$post_proceso]\n";
        use FindBin '$Bin';
        my $rutaScript = $Bin;

        # para que sea un script valido debe ubicarse en el mismo dir. de cgi del prontus o a lo mas un nivel hacia arriba.
        if ( ($post_proceso =~ /^\w/) || ($post_proceso =~ /^\.\.(\/|\\)\w/) ) {
            my $cmd = "$rutaScript/$post_proceso $ts $prontus_varglb::PRONTUS_ID $prontus_varglb::PUBLIC_SERVER_NAME";
            print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
            system $cmd;
        };
    };
};

# --------------------------------------------------------------------
sub regen_art_relac {
    # Regenera art. relacionados
    my ($secc, $tem, $stem, $base) = @_;

    my ($tripleta);

    &lib_tax::set_vars($prontus_varglb::DIR_CONTENIDO, $prontus_varglb::DIR_ARTIC, $prontus_varglb::DIR_PAG, $prontus_varglb::DIR_TEMP, $prontus_varglb::DIR_TAXONOMIA, $prontus_varglb::DIR_CONTENIDO, $prontus_varglb::NUM_RELAC_DEFAULT, $prontus_varglb::CONTROLAR_ALTA_ARTICULOS);

    &lib_tax::generar_relacionados($secc, $tem, $stem, $base);
    # Ahora parsea art relacionados para MVs
    my $mv;
    foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
        &lib_tax::generar_relacionados($secc, $tem, $stem, $base, $mv);
    };

    # print STDERR "\n regen $secc, $tem, $stem\n";

};

# --------------------------------------------------------------------
sub get_taxonomia {
# Obtiene seccion, tema, stema del articulo.
  my ($id) = $_[0];
  my ($base) = $_[1];
  my ($secc, $tem, $stem);
  my $sql = "select ART_IDSECC1, ART_IDTEMAS1, ART_IDSUBTEMAS1 from ART where ART_ID = '$id'";
  my $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($secc, $tem, $stem));
  $salida->fetch;
  $salida->finish;
  if ($secc) {
    $tem = '0' if ($tem eq '');
    $stem = '0' if ($stem eq '');
    return ($secc, $tem, $stem);
  }
  else {
    return ('-1','0','0');
  };
};

# ---------------------------------------------------------------
sub call_taxports_regen {
    my $rutaScript = shift;
    my $param_especif_taxport = shift;
    
    my $cmd = "$rutaScript/prontus_cron_taxport.cgi $prontus_varglb::PRONTUS_ID $param_especif_taxport &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};

# ---------------------------------------------------------------
sub call_list_regen {
    my $rutaScript = shift;
    my $param_especif_list = shift;
    return if($prontus_varglb::LIST_PROCESO_INTERNO ne 'SI');
    
    my $cmd = "$rutaScript/prontus_cron_list.cgi $prontus_varglb::PRONTUS_ID $param_especif_list &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};

# ---------------------------------------------------------------
sub call_dam2delete {
    my $ts = shift;
    my $rutaScript = shift;
    
    my $cmd = "$rutaScript/dam/prontus_dam_ppart_delete.cgi $ts $prontus_varglb::PRONTUS_ID $prontus_varglb::PUBLIC_SERVER_NAME &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};

# -------------------------------END SCRIPT----------------------
