#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# SCRIPT.
# -----------
# prontus_cron_taxcalend.cgi

# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/.

# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Generar portadas calendario con cada dia apuntando a los articulos con fechap de ese dia
# Se generan los calendarios y ademas las portadillas correspondientes a cada dia
# Se generan calendarios para cada seccion y tb. calendarios comunes (sin filtrar x seccion)
# Se parsean multivistas.
# Genera hojas de calendario para mes anterior, actual, siguiente y subsiguiente. Siempre
# genera estas hojas, aunque no hayan dias linkeados.
# Las marcas parseadas en las portadillas son las mismas usadas en las taxports tradicionales.
# Se consideran articulos cuya fechap calce con el dia correspondiente y que tengan Alta.
# TO-DO: - generalizar extensiones de plantillas.
#        - usar una plantilla distinta para la portadilla comun
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------
# No registra

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# como cron, con lo sgtes. params:
# $ARGV[0] : Nombre del Prontus (ej. prontus_noticias)
# $ARGV[1] : aaaamm : mes a procesar, si no se indica, se asume el actual.
# Ejemplo:  perl prontus_cron_taxcalend.cgi prontus_minrel
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# Plantilla para mes de calendario:
# /<prontus_id>/plantillas/extra/calendar/mes/port(-vvv)/mescalendar.html

# Plantilla para portadillas:
# /<prontus_id>/plantillas/extra/calendar/fechap/pags(-vvv)/portcalendar.html <--- por seccion
# /<prontus_id>/plantillas/extra/calendar/fechap/pags(-vvv)/portallcalendar.html <--- sin discriminar seccion

# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# Hojas de calendarios:
# /<prontus_id>/site/extra/calendar/<aaaamm>/port(-vvv)/<idseccion>.html <--- por cada mes y seccion
# /<prontus_id>/site/extra/calendar/<aaaamm>/port(-vvv)/all.html <--- por cada mes, sin discriminar seccion

# Portadillas:
# /<prontus_id>/plantillas/extra/calendar/<aaaammdd>/pags(-vvv)/<idseccion>.html <--- por cada dia y seccion
# /<prontus_id>/plantillas/extra/calendar/<aaaammdd>/pags(-vvv)/all.html <--- por cada dia, sin discriminar seccion


# ---------------------------------------------------------------
# Tablas.
# ------------------------
# BD: la configurada en Prontus. Tablas: 'ART', 'SECC', 'TEMAS', 'SUBTEMAS'
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 05/2007 - YCH - Primera Version.

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use lib_tax;
use glib_hrfec_02;
use glib_dbi_02;
use glib_cgi_04;
use glib_fildir_02;
use strict;
use DBI;


# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
my ($LOOP, $NOM_PRONTUS, %TABLA_TEM , %TABLA_SECC);

# cd /sites/sibuc.puc.cl/web/cgi-cpn
# perl prontus_cron_taxcalend.cgi prontus_dev


# Capturar options para exclusion de fids
use Getopt::Long;
my @EXCLUDEFIDS;
GetOptions("excludefids|x=s" => \@EXCLUDEFIDS); # .cgi -x f1,f2 prontus_test
@EXCLUDEFIDS = split(/,/,join(',',@EXCLUDEFIDS));

my $PRONTUS_ID = $ARGV[0];
my $AAAAMM = $ARGV[1];

# print "PRONTUS_ID[$PRONTUS_ID]\n";
# print "AAAAMM[$AAAAMM]\n";


&valida_param();

# Carga variables de configuracion de prontus.
my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($PRONTUS_ID);
&lib_prontus::load_config(  &lib_prontus::ajusta_pathconf($relpath_conf) );


# CALENDARIOS
my ($RELDIR_PORT_TMP_CALEND) = "$prontus_varglb::DIR_TEMP/extra/calendar/mes/port";
my (%EXT_PORT_TMP_CALEND, %BUF_PLT_CALEND, %BUF_PLT_LOOP_CALEND);
my @SEMANAS;
my $PERP_EOM;

# PORTADILLAS
my ($RELDIR_PORT_TMP) = "$prontus_varglb::DIR_TEMP/extra/calendar/fechap/pags";
my (%EXT_PORT_TMP, %BUF_PLT, %BUF_PLT_LOOP);
my (%EXT_PORT_TMP_PORTALL, %BUF_PLT_PORTALL, %BUF_PLT_LOOP_PORTALL);
my ($RELDIR_ARTIC) = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/%%DIRFECHA%%$prontus_varglb::DIR_PAG";


my ($CURR_DTIME) = &glib_hrfec_02::get_dtime_pack4();

&generar_taxcalend();


# ---------------------------------------------------------------
sub generar_taxcalend {

    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        die "ERROR: $msg_err_bd\n";
        exit;
    };


    # precarga tabla de temas en hash global para uso posterior reiterado.
    %TABLA_SECC = &lib_tax::carga_tabla_seccion($base);
    %TABLA_TEM = &lib_tax::carga_tabla_temas($base);


    # precarga buffers de plantillas de calend para cada vista.
    &precarga_plantillas_calend();

    # precarga buffers de plantillas de portadillas para cada vista.
    &precarga_plantillas_portadillas();

    # Obtiene meses a procesar
    my @meses_a_generar = &get_meses_generar();

    # secc
    my $sql = "select SECC_ID, SECC_NOM, SECC_PORT from SECC ";
    my ($secc_id, $secc_nom, $secc_port);
    my ($salida) = &glib_dbi_02::ejecutar_sql($base, $sql);
    $salida->bind_columns(undef, \($secc_id, $secc_nom, $secc_port));
    while ($salida->fetch) {

        # Para cada mes
        foreach my $aaaamm (@meses_a_generar) {
            my ($aaaa, $mm) = split(/\t/, $aaaamm);
            $mm = '0' . $mm if (length($mm) == 1);
            my %fechas_linkeadas = &get_fechas_linkeadas($secc_id, $aaaa, $mm, $base);

            # Para cada fecha linkeada, genera portadilla, en todas las vistas.
            my %artics;
            foreach my $fecha (keys %fechas_linkeadas) {

                # print STDERR "writing port para secc[$secc_nom] - fecha[$fecha]\n\n";
                my $artics_dia = &generar_portadilla($base, $fecha, $secc_id);
                # acumula articulos por dia
                $artics{$fecha} = $artics_dia; # "$art_id\t$art_horap\t$art_titu\n";
            };
            # Genera la hoja del calendario para cada una de las secciones, en todas las vistas.
            &generar_hoja_calend($secc_id, $aaaa, $mm, \%fechas_linkeadas, \%artics);

            # Borrar portadillas de dias que NO hayan tenido articulos en este mes $aaaamm
            # se borra del tipo /prontus_mim/site/extra/calendar/$aaaamm/pags/$secc_id.ext
            my $dir2clean = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/extra/calendar";
            my @lisdir = &glib_fildir_02::lee_dir($dir2clean);
            @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
            foreach my $subdir (@lisdir) {
                if ( (-d "$dir2clean/$subdir/pags") && ($subdir =~ /^$aaaa$mm[0-9]{2}$/) && (!exists $fechas_linkeadas{$subdir}) ) {
                    my %vistas = %prontus_varglb::MULTIVISTAS;
                    $vistas{''} = 1;
                    foreach my $mv (keys %vistas) {
                        $mv = '-' . $mv if ($mv);
                        my $dirmv = "$dir2clean/$subdir/pags$mv";
                        my @lisdirmv = &glib_fildir_02::lee_dir($dirmv);
                        @lisdirmv = grep !/^\./, @lisdirmv; # Elimina directorios . y ..
                        foreach my $file2del (@lisdirmv) {
                            next if (!-f "$dirmv/$file2del");
                            next if ($file2del !~ /^$secc_id\.\w+$/);
                            # print STDERR "borrar[$dirmv/$file2del]\n";
                            unlink "$dirmv/$file2del";
                        };
                    };
                };
            };


        };

    };
    $salida->finish;


    # generar hoja de calend sin considerar secc.
    foreach my $aaaamm (@meses_a_generar) {
        my ($aaaa, $mm) = split(/\t/, $aaaamm);
        $mm = '0' . $mm if (length($mm) == 1);

        my %fechas_linkeadas = &get_fechas_linkeadas(0, $aaaa, $mm, $base);

        # Generar portadillas correspondientes.
        my %artics;
        foreach my $fecha (keys %fechas_linkeadas) {

            my $artics_dia = &generar_portadilla($base, $fecha, 0);
            $artics{$fecha} = $artics_dia; # "$art_id\t$art_horap\t$art_titu\n";
        };

        &generar_hoja_calend(0, $aaaa, $mm, \%fechas_linkeadas, \%artics);
    };

    $base->disconnect;




};

# ---------------------------------------------------------------
sub get_meses_generar {
# Obtiene meses a procesar, los que corresponden al actual, anterior, siguiente y subsiguiente.
# Si viene el parametro del mes $AAAAMM, entonces se toma ese como actual.

    # aaaamm actual
    my $aaaamm_procesar = $CURR_DTIME;


    $aaaamm_procesar = $AAAAMM if ($AAAAMM);


    # print "procesando[$aaaamm_procesar]\n";
    $aaaamm_procesar =~ /^(\d{4})(\d{2})/;
    my $aaaa_actual = $1;
    my $mm_actual = $2;

   return ("$aaaa_actual\t$mm_actual") if ($AAAAMM);

    # aaaamm anterior
    my $mm_menos1 = $mm_actual - 1;
    my $aaaa_menos1 = $aaaa_actual;
    if ($mm_menos1 <= 0 ) {
        $aaaa_menos1 = $aaaa_actual - 1;
        $mm_menos1 = 12;
    };

    # aaaamm siguiente
    my $mm_mas1 = $mm_actual + 1;
    my $aaaa_mas1 = $aaaa_actual;
    if ($mm_mas1 > 12) {
        $aaaa_mas1 = $aaaa_actual + 1;
        $mm_mas1 = '01';
    };

    # aaaamm subsiguiente
    my $mm_mas2 = $mm_mas1 + 1;
    my $aaaa_mas2 = $aaaa_mas1;
    if ($mm_mas2 > 12) {
        $aaaa_mas2 = $aaaa_mas1 + 1;
        $mm_mas2 = '01';
    };

    return ("$aaaa_menos1\t$mm_menos1", "$aaaa_actual\t$mm_actual", "$aaaa_mas1\t$mm_mas1", "$aaaa_mas2\t$mm_mas2");
};


# ---------------------------------------------------------------
sub generar_portadilla {
    my ($base, $fecha, $secc_id) = @_;

    my $where = "(ART_FECHAP = \"$fecha\") and (ART_ALTA = \"1\") ";

    if ($secc_id) {
        $where .= " and (ART_IDSECC1 = \"$secc_id\" or ART_IDSECC2 = \"$secc_id\" or ART_IDSECC3 = \"$secc_id\")";
    };

    # Aplicar exclusion de FIDs
    foreach my $fid (@EXCLUDEFIDS) {
        $where .= " and (ART_TIPOFICHA <> '$fid') " if ($fid =~ /^[\w\-]+$/);
    };

    # SQL para lista de articulos
    my $sql = "select ART_ID, ART_FECHAP, ART_HORAP, ART_TITU, "
            . "ART_DIRFECHA, ART_EXTENSION, ART_TIPOFICHA, ART_IDTEMAS1 from ART where "
            . $where
            . " order by ART_FECHAP desc, ART_HORAP desc";
    # print "sql portadilla[$sql]\n";
    my $tot_artics = &lib_prontus::existe_registro("select count(ART_ID) from ART where $where", $base);

    my ($art_id, $art_fecha, $art_horap, $art_titu,
        $art_dirfecha, $art_extension,
        $art_tipoficha, $art_idtemas1);

    my $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($art_id, $art_fecha, $art_horap, $art_titu,
                                                                $art_dirfecha, $art_extension,
                                                                $art_tipoficha, $art_idtemas1));
    my $nro_filas = 0;
    my $nro_pag = 0;
    my %filas;
    my $artics_dia;
    my %art_xml_fields;
    while ($salida->fetch) {
        $nro_filas++;

        $artics_dia .= "$art_id\t$art_horap\t$art_titu\t$art_extension%%\n%%";
        # print "artics_dia[$artics_dia]\n";
        # parsea esta fila en todas las multivistas

        my ($tem, $filler1, $filler2, $filler3) = split (/\t\t/, $TABLA_TEM{$art_idtemas1});

        my $mv;
        my %vistas = %prontus_varglb::MULTIVISTAS;
        $vistas{'<vista_normal>'} = 1;

        foreach $mv (keys %vistas) {
            my $plt_loop = $BUF_PLT_LOOP{$mv};
            $plt_loop = $BUF_PLT_LOOP_PORTALL{$mv} if (!$secc_id); # si no hay seccion, usar plantilla especial.

            next if (!$plt_loop);
            my ($fila_content, $auxref) = &lib_tax::generar_fila($RELDIR_ARTIC, $art_id, $art_extension, $plt_loop,
                                                                 $nro_filas, $tot_artics, $art_xml_fields{$art_id});

            $art_xml_fields{$art_id} = $auxref if (! exists $art_xml_fields{$art_id}); # para no leer 2 veces un xml
            $filas{$mv} .= $fila_content;
        };
    };

    # escribir
    if ($nro_filas) {

        &write_portadilla($fecha, $secc_id, \%filas);
    }

    $salida->finish;

    return $artics_dia;

};


# ---------------------------------------------------------------
sub get_fechas_linkeadas {
    my ($secc_id, $aaaa, $mm, $base) = @_;
    my ($secc_nom, $secc_port, $secc_nom4vistas) = split (/\t\t/, $TABLA_SECC{$secc_id});
    # cargar todas las fechap de articulos q cumplan con los criterios.
    # esto es para saber de antemano si se debe linkear o no cada dia del mes.

    my $fecha_desde = $aaaa . $mm . '01';
    my $fecha_hasta = $aaaa . $mm . '31';
    my $sql = "select distinct(ART_FECHAP) from ART WHERE "
            . "(ART_FECHAP >= \"$fecha_desde\" and ART_FECHAP <= \"$fecha_hasta\") "
            . " and (ART_ALTA = \"1\") ";

    if ($secc_id) {
        $sql .= " and (ART_IDSECC1 = \"$secc_id\" or ART_IDSECC2 = \"$secc_id\" or ART_IDSECC3 = \"$secc_id\")";
    };

    # Aplicar exclusion de FIDs
    foreach my $fid (@EXCLUDEFIDS) {
        $sql .= " and (ART_TIPOFICHA <> '$fid') " if ($fid =~ /^[\w\-]+$/);
    };
    # print "sql calend[$sql]\n";
    my $fechap_ok;
    my $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($fechap_ok));
    my %fechas_linkeadas;
    while ($salida->fetch) {
        $fechas_linkeadas{$fechap_ok} = 1;
        # print "fecha link[$fechap_ok]\n";
    };
    $salida->finish();

    return %fechas_linkeadas;

};

# ---------------------------------------------------------------
sub generar_hoja_calend {
    my ($secc_id, $aaaa, $mm, $ref_fechas_linkeadas, $ref_artics) = @_;
    my %fechas_linkeadas = %$ref_fechas_linkeadas; undef $ref_fechas_linkeadas;
    my %artics = %$ref_artics; undef $ref_artics;


    my ($semana, $loop_parsed, $rows, $nomdia, $nrodia);
    my (@sdays) = ('LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM');

    @SEMANAS = ();

    &get_semanas($aaaa, $mm);
    my %rows_out;

    foreach $semana (@SEMANAS) {
        my %vistas = %prontus_varglb::MULTIVISTAS;
        $vistas{'<vista_normal>'} = 1;
        my %loop_out;
        my $mv;
        my %art_xml_fields;
        foreach $mv (keys %vistas) {
            $loop_out{$mv} = $BUF_PLT_LOOP_CALEND{$mv};

            foreach $nomdia (@sdays) {
                # print STDERR "semana[$semana]";
                if ($semana =~ /.*$nomdia\_\_(\d\d?);?.*/) {
                    my $dd = $1;
                    my $nrodia = $dd; # para parsearlo visualmente
                    $dd = '0' . $dd if (length($dd) == 1);

                    # rescata plt de loop para articulos de ese dia
                    my $artics_loop;
                    my $maxchars;
                    my $maxartics;
                    if ($BUF_PLT_LOOP_CALEND{$mv} =~ /%%LOOP_$nomdia(\((\d+)?\))?%%(.+?)%%\/LOOP_$nomdia%%/is) {
                        $artics_loop = $3;
                        $maxartics = $2;
                    };
                    # print STDERR "FECHA [$aaaa$mm$dd] ..." if (("$aaaa$mm$dd" eq '20110606') && ($mv eq '<vista_normal>') && ($secc_id eq '26'));
                    if (exists $fechas_linkeadas{"$aaaa$mm$dd"}) {
                        # print STDERR "con artics ...\n" if (("$aaaa$mm$dd" eq '20110606') && ($mv eq '<vista_normal>') && ($secc_id eq '26'));
                        $nrodia = &linkear_dia($aaaa, $mm, $dd, $secc_id, $mv);

                        # articulos de este dia
                        my @artics_this_day = split(/%%\n%%/, $artics{"$aaaa$mm$dd"}); # "$art_id\t$art_horap\t$art_titu\n";
                        my $artics_loop_out;
                        my $artic_row;
                        my $count_artics = 0;
                        foreach my $k (@artics_this_day) {
                            $count_artics++;
                            last if ($count_artics > $maxartics);
                            my ($art_id, $art_horap, $art_titu, $art_extension) = split(/\t/, $k);

                            # ahora
                            my $tot_artics = 0; # no se dispone de este dato.
                            my ($fila_content, $auxref) = &lib_tax::generar_fila($RELDIR_ARTIC, $art_id, $art_extension, $artics_loop,
                                                                                 $count_artics, $tot_artics, $art_xml_fields{$art_id});

                            $art_xml_fields{$art_id} = $auxref if (! exists $art_xml_fields{$art_id}); # para no leer 2 veces un xml
                            $artics_loop_out .= $fila_content;

                        };
                        $loop_out{$mv} =~ s/%%LOOP_$nomdia(\(.*?\))?%%.*?%%\/LOOP_$nomdia%%/$artics_loop_out/isg;

                    }
                    else {
                        # print STDERR "sin artics ... mv[$mv]nomdia[$nomdia]\n" if (("$aaaa$mm$dd" eq '20110606') && ($mv eq '<vista_normal>') && ($secc_id eq '26'));
                        # $loop_out{$mv} =~ s/%%$nomdia%%/&nbsp;/;

                        if ($loop_out{$mv} =~ s/%%LOOP_$nomdia(\(.*?\))?%%.*?%%\/LOOP_$nomdia%%//isg) {
                            # print STDERR "repl ok\n" if (("$aaaa$mm$dd" eq '20110606') && ($mv eq '<vista_normal>') && ($secc_id eq '26'));
                        };

                    };

                    $loop_out{$mv} =~ s/%%$nomdia%%/$nrodia/;
                }
                else {
                    $loop_out{$mv} =~ s/%%$nomdia%%/&nbsp;/;
                    $loop_out{$mv} =~ s/%%LOOP_$nomdia(\(.*?\))?%%.*?%%\/LOOP_$nomdia%%//isg;
                };
            }; # foreach $nomdia

            $rows_out{$mv} .= $loop_out{$mv};
        }; # foreach $mv

    }; # foreach $semana

    # parseos generales y escritura del archivo "hoja de calendario" para cada vista.
    my $nom_mes = uc &get_mes($mm);

    my ($secc_nom, $secc_port, $secc_nom4vistas) = split (/\t\t/, $TABLA_SECC{$secc_id});

    my %vistas; # incluye las mv y la normal
    %vistas = %prontus_varglb::MULTIVISTAS;
    $vistas{'<vista_normal>'} = 1;
    my $mv;
    foreach $mv (keys %vistas) {
        # parsea pagina
        my $pagina = $BUF_PLT_CALEND{$mv};
        my $ext = $EXT_PORT_TMP_CALEND{$mv};
        $pagina =~ s/%%LOOP%%.*?%%\/LOOP%%/$rows_out{$mv}/is;
        $pagina =~ s/%%nom_mes%%/$nom_mes/ig;
        $pagina =~ s/%%aaaa%%/$aaaa/ig;
        $pagina =~ s/%%mm%%/$mm/ig;

        # Nombre de la secc en la vista correspondiente
        $mv = '' if ($mv eq '<vista_normal>');
        $secc_nom = &lib_prontus::get_nomtax_envista($mv, $secc_nom4vistas) if ($mv);
        $secc_nom = &lib_prontus::escape_html($secc_nom);

        $pagina =~ s/%%NOMSECC%%/$secc_nom/isg;
        $pagina =~ s/%%SECC%%/$secc_id/isg;
        $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
        $pagina = &lib_prontus::parser_custom_function($pagina);
        # Escribe pagina en dir correspondiente
        $mv = '-' . $mv if ($mv);
        &glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/extra/calendar/$aaaa$mm/port$mv");
        $secc_id = 'all' if (!$secc_id);
        my $dst_hojacal = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/extra/calendar/$aaaa$mm/port$mv/$secc_id$ext";
        # print STDERR "writing[$dst_hojacal]\n" if (($secc_id eq '26') && ("$aaaa$mm" eq '201106')); # if (("$aaaa$mm" eq '201106') && ($mv eq '<vista_normal>') && ($secc_id eq '26'));
        &glib_fildir_02::write_file($dst_hojacal, $pagina);
        &lib_prontus::purge_cache($dst_hojacal);
    };

};

# ---------------------------------------------------------------

sub linkear_dia {

    my ($aaaa, $mm, $dd, $secc_id, $mv) = @_;

    my ($fecha);

    my $ext_conpunto = $EXT_PORT_TMP{$mv};
    $ext_conpunto = $EXT_PORT_TMP_PORTALL{$mv} if (!$secc_id);

    $mv = '' if ($mv eq '<vista_normal>');
    $mv = '-' . $mv if ($mv);

    $fecha = "$aaaa$mm$dd";
    $secc_id = 'all' if (!$secc_id);
    my $dst_dia = "$prontus_varglb::DIR_CONTENIDO/extra/calendar/$fecha/pags$mv/$secc_id$ext_conpunto";

    $dd =~ s/^0//;
    return "<a href=\"$dst_dia\">$dd</a>";

};
# ---------------------------------------------------------------

sub get_semanas {
# Genera el arreglo de semanas @SEMANAS (cada componente corresponde a una semana).

    my ($aaaa, $mm) = @_;

    my ($sem, $dia, $fec_secs, $sday);

    $sem = 0;
    &perpetual_calendar($mm,1,$aaaa);

    for ($dia = 1 ; $dia <= $PERP_EOM; $dia++) {

        $dia = sprintf("%0.0d",$dia);
        # Fecha actual en formato segundos.
        $fec_secs = &POSIX::mktime(0,0,12,$dia,($mm - 1),($aaaa - 1900));
        # Dia de la semana.
        $sday = &glib_hrfec_02::get_date_time(1,'' , '', '', '', '', $fec_secs);
        $sday = uc(substr($sday, 0, 3));
        $SEMANAS[$sem] .= $sday . '__' . $dia . ';';

        if ($sday eq 'DOM') {
            $sem++;
        };

    }; # for

};
# ---------------------------------------------------------------
sub perpetual_calendar {
    # This perpetual calendar routine provides accurate day/date
    # correspondences for dates from 1601 to 2899 A.D.  It is based on
    # the Gregorian calendar, so be aware that early correspondences
    # may not always be historically accurate.  The Gregorian calendar
    # was adopted by the Italian states, Portugal and Spain in 1582,
    # and by the Catholic German states in 1583.  However, it was not
    # adopted by the Protestant German states until 1699, by England
    # and its colonies until 1752, by Sweden until 1753, by Japan
    # until 1873, by China until 1912, by the Soviet Union until 1918,
    # and by Greece until 1923.
    my ($perp_mon,$perp_day,$perp_year) = @_;
    my %day_counts =
      (1,0,2,31,3,59,4,90,5,120,6,151,7,181,
      8,212,9,243,10,273,11,304,12,334);
    my $perp_days = (($perp_year-1601)*365)+(int(($perp_year-1601)/4));
    $perp_days += $day_counts{$perp_mon};
    $perp_days += $perp_day;
    my $perp_sofar = $day_counts{$perp_mon};
    $perp_sofar += $perp_day;
    my $perp_togo = 365-$perp_sofar;
    if (int(($perp_year-1600)/4) eq (($perp_year-1600)/4)) {
        $perp_togo++;
        if ($perp_mon > 2) {
            $perp_days++;
            $perp_sofar++;
            $perp_togo -= 1;
        };
    };
    my $key;
    foreach $key (1700,1800,1900,2100,2200,2300,2500,2600,2700) {
        if ((($perp_year == $key) && ($perp_mon > 2))
          || ($perp_year > $key)) {
            $perp_days -= 1;
        };
    };

    my $perp_dow = $perp_days - (int($perp_days/7)*7);
    if ($perp_dow == 7) { $perp_dow = 0; }
#   if ($vars{monsunweek} eq "Yes") {
#       $perp_dow -= 1;
#       if ($perp_dow == -1) { $perp_dow = 6; };
#   };
    $PERP_EOM = 31;
    if (($perp_mon == 4) || ($perp_mon == 6)
      || ($perp_mon == 9) || ($perp_mon == 11)) {
        $PERP_EOM = 30;
    };
    if (($perp_mon == 2)) {
        $PERP_EOM = 28;
    };
    if ((int(($perp_year-1600)/4) eq (($perp_year-1600)/4))
      && ($perp_mon == 2)) {
        $PERP_EOM = 29;
    };
    foreach $key (1700,1800,1900,2100,2200,2300,2500,2600,2700) {
        if ($perp_year == $key) {
            if ($perp_mon == 1) {
                $perp_togo -= 1;
            }
            elsif ($perp_mon == 2) {
                $perp_togo -= 1;
                $PERP_EOM = 28;
            }
            else {
                $perp_sofar -= 1;
            };
        };
    };
};



# ---------------------------------------------------------------
sub precarga_plantillas_calend {
    # Plantilla completa --> %BUF_PLT
    # Loop de cada fila de hoja de calend --> %BUF_PLT_LOOP

    # Primero para multivistas
    my $mv;
    foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
        my $reldir_port_tmp = $RELDIR_PORT_TMP_CALEND . '-' . $mv;

        if (! -d "$prontus_varglb::DIR_SERVER$reldir_port_tmp") {
            print &lib_language::_msg_prontus('_error_invalid_calendar_template_directory')."\n";
            next;
        };

        $EXT_PORT_TMP_CALEND{$mv} = &get_ext($reldir_port_tmp, 'mescalendar'); # extension con punto
        my $relpathfile_port_tmp = $reldir_port_tmp . '/' . 'mescalendar' . $EXT_PORT_TMP_CALEND{$mv};

        if (! -f "$prontus_varglb::DIR_SERVER$relpathfile_port_tmp") {
            print &lib_language::_msg_prontus('_error_invalid_calendar_template_view')." [$mv]\n";
            next;
        };

        my $pagina = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$relpathfile_port_tmp");
        $BUF_PLT_CALEND{$mv} = $pagina;
        if ($pagina =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg) {
            $BUF_PLT_LOOP_CALEND{$mv} = $1;
        };

    };

    # Para vista normal.
    my $reldir_port_tmp = $RELDIR_PORT_TMP_CALEND;
    if (! -d "$prontus_varglb::DIR_SERVER$reldir_port_tmp") {
        print &lib_language::_msg_prontus('_error_invalid_calendar_template_directory')." [$prontus_varglb::DIR_SERVER$reldir_port_tmp]\n";
        next;
    };

    $EXT_PORT_TMP_CALEND{'<vista_normal>'} = &get_ext($reldir_port_tmp, 'mescalendar'); # extension con punto
    my $relpathfile_port_tmp = $reldir_port_tmp . '/' . 'mescalendar' . $EXT_PORT_TMP_CALEND{'<vista_normal>'};

    if (! -f "$prontus_varglb::DIR_SERVER$relpathfile_port_tmp") {
        print &lib_language::_msg_prontus('_error_invalid_tac_template_normal_view')." [$prontus_varglb::DIR_SERVER$relpathfile_port_tmp]\n";
        next;
    };

    my $pagina = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$relpathfile_port_tmp");
    # print STDERR "plt mes[$prontus_varglb::DIR_SERVER$relpathfile_port_tmp]\n";
    $BUF_PLT_CALEND{'<vista_normal>'} = $pagina;
    if ($pagina =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg) {
        $BUF_PLT_LOOP_CALEND{'<vista_normal>'} = $1;
    };

};

# ---------------------------------------------------------------
sub valida_param {
  $PRONTUS_ID =~ s/\\/\//g;
  $PRONTUS_ID =~ s/\/$//g;
  if ( (! -d "$prontus_varglb::DIR_SERVER/$PRONTUS_ID") || ($PRONTUS_ID eq '') || ($PRONTUS_ID eq '/') )  {
    print "\n".&lib_language::_msg_prontus('_error_invalid_publisher_directory');
    print "\n".&lib_language::_msg_prontus('_enter_prontus_name_processing_as_first_parameter')."\n";
    exit;
  };

  $AAAAMM =~ s/[^0-9]//g;
  if ( ($AAAAMM !~ /^\d{6}$/) && ($AAAAMM) )  {
    print "\n".&lib_language::_msg_prontus('_error_invalid_month_to_generate');
    print "\n".&lib_language::_msg_prontus('_indicate_yyyymm_or_leave_blanck_to_process_current_month')."\n";
    exit;
  };

};

# ---------------------------------------------------------------
sub get_ext {
    my ($relpath_dir) = $_[0];
    my ($solonom) = $_[1];
    my $dir = "$prontus_varglb::DIR_SERVER$relpath_dir";

    my @lisdir = &glib_fildir_02::lee_dir($dir);
    my %taxonomia;
    my $ext;
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    foreach my $arch (@lisdir) {
        if ((-f "$dir/$arch") && ($arch =~ /^$solonom(\.\w+)$/)) {
            return $1; # ext. con punto
        };
    };
    return '';

};
# ---------------------------------------------------------------
sub get_mes {
    my ($mm) = $_[0];
    my ($mesanno);
    $mesanno = 'Enero' if ($mm eq '01');
    $mesanno = 'Febrero' if ($mm eq '02');
    $mesanno = 'Marzo' if ($mm eq '03');
    $mesanno = 'Abril' if ($mm eq '04');
    $mesanno = 'Mayo' if ($mm eq '05');
    $mesanno = 'Junio' if ($mm eq '06');
    $mesanno = 'Julio' if ($mm eq '07');
    $mesanno = 'Agosto' if ($mm eq '08');
    $mesanno = 'Septiembre' if ($mm eq '09');
    $mesanno = 'Octubre' if ($mm eq '10');
    $mesanno = 'Noviembre' if ($mm eq '11');
    $mesanno = 'Diciembre' if ($mm eq '12');
    return $mesanno;
};
# ---------------------------------------------------------------
sub precarga_plantillas_portadillas {
    # Plantilla completa --> %BUF_PLT
    # Loop --> %BUF_PLT_LOOP

    # Primero para multivistas
    my $mv;
    foreach $mv (keys %prontus_varglb::MULTIVISTAS) {

        my $reldir_port_tmp = $RELDIR_PORT_TMP . '-' . $mv;
        if (! -d "$prontus_varglb::DIR_SERVER$reldir_port_tmp") {
            print &lib_language::_msg_prontus('_error_invalid_title_page_template_directory_for_calendar')."\n";
            next;
        };


        # Plantilla de portadilla por seccion
        $EXT_PORT_TMP{$mv} = &get_ext($reldir_port_tmp, 'portcalendar'); # extension con punto
        my $relpathfile_port_tmp = $reldir_port_tmp . '/' . 'portcalendar' . $EXT_PORT_TMP{$mv};
        if (! -f "$prontus_varglb::DIR_SERVER$relpathfile_port_tmp") {
            print &lib_language::_msg_prontus('_error_title_page_template_portcalendar_invalid_for_view')." [$mv]\n";
            next;
        };

        my $pagina = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$relpathfile_port_tmp");
        $BUF_PLT{$mv} = $pagina;
        if ($pagina =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg) {
            $BUF_PLT_LOOP{$mv} = $1;
        };

        if ($pagina =~ /%%_TAXPORT_ARTXPAG=\d+%%/i) {
            print &lib_language::_msg_prontus('_error_mark')." %%_TAXPORT_ARTXPAG=n%% ".&lib_language::_msg_prontus('_no_considerate_mode_cron')."\n";
        };

        # Plantilla de portadilla comun
        $EXT_PORT_TMP_PORTALL{$mv} = &get_ext($reldir_port_tmp, 'portallcalendar'); # extension con punto
        $relpathfile_port_tmp = $reldir_port_tmp . '/' . 'portallcalendar' . $EXT_PORT_TMP_PORTALL{$mv};
        if (! -f "$prontus_varglb::DIR_SERVER$relpathfile_port_tmp") {
            print &lib_language::_msg_prontus('_error_title_page_template_portallcalendar_invalid_for_view')." [$mv]\n";
            next;
        };

        $pagina = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$relpathfile_port_tmp");
        $BUF_PLT_PORTALL{$mv} = $pagina;
        if ($pagina =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg) {
            $BUF_PLT_LOOP_PORTALL{$mv} = $1;
        };

        if ($pagina =~ /%%_TAXPORT_ARTXPAG=\d+%%/i) {
            print &lib_language::_msg_prontus('_error_mark')." %%_TAXPORT_ARTXPAG=n%% ".&lib_language::_msg_prontus('_no_considerate_mode_cron')."\n";
        };

    };

    # Para vista normal.
    my $reldir_port_tmp = $RELDIR_PORT_TMP;
    if (! -d "$prontus_varglb::DIR_SERVER$reldir_port_tmp") {
        print &lib_language::_msg_prontus('_error_invalid_tax_template_directory')." [$prontus_varglb::DIR_SERVER$reldir_port_tmp]\n";
        next;
    };

    # Plantilla de portadilla por seccion
    $EXT_PORT_TMP{'<vista_normal>'} = &get_ext($reldir_port_tmp, 'portcalendar'); # extension con punto
    my $relpathfile_port_tmp = $reldir_port_tmp . '/' . 'portcalendar' . $EXT_PORT_TMP{'<vista_normal>'};

    if (! -f "$prontus_varglb::DIR_SERVER$relpathfile_port_tmp") {
        print &lib_language::_msg_prontus('_error_tax_portcalendar_template_invalid_for_normal_view')."\n";
        next;
    };

    my $pagina = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$relpathfile_port_tmp");
    $BUF_PLT{'<vista_normal>'} = $pagina;
    if ($pagina =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg) {
        $BUF_PLT_LOOP{'<vista_normal>'} = $1;
    };

    # Plantilla de portadilla comun
    $EXT_PORT_TMP_PORTALL{'<vista_normal>'} = &get_ext($reldir_port_tmp, 'portallcalendar'); # extension con punto
    $relpathfile_port_tmp = $reldir_port_tmp . '/' . 'portallcalendar' . $EXT_PORT_TMP_PORTALL{'<vista_normal>'};

    if (! -f "$prontus_varglb::DIR_SERVER$relpathfile_port_tmp") {
        print &lib_language::_msg_prontus('_error_tax_portcalendar_template_invalid_for_normal_view')."\n";
        next;
    };

    my $pagina = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$relpathfile_port_tmp");
    $BUF_PLT_PORTALL{'<vista_normal>'} = $pagina;
    if ($pagina =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg) {
        $BUF_PLT_LOOP_PORTALL{'<vista_normal>'} = $1;
    };

};


# ---------------------------------------------------------------
sub write_portadilla {
  my ($fecha, $secc_id, $filas_hashref) = @_;

  my ($secc_nom, $secc_port, $secc_nom4vistas) = split (/\t\t/, $TABLA_SECC{$secc_id});

  my %filas = %$filas_hashref;

  # escribe pagina en todas las vistas incluida la normal
  my %vistas; # incluye las mv y la normal
  %vistas = %prontus_varglb::MULTIVISTAS;
  $vistas{'<vista_normal>'} = 1;
  my $mv;

  foreach $mv (keys %vistas) {
    # print "mv[$mv] seccion[$secc_id]\n";
    # parsea pagina
    my $pagina = $BUF_PLT{$mv};

    if (!$secc_id) { # si no hay seccion, usar plantilla especial.
        $pagina = $BUF_PLT_PORTALL{$mv};
        # print "\n\n\nsecc[$secc_id] vista [$mv]\n[$pagina]\n";
    };

    my $lista = $filas{$mv};
    $filas{$mv} = ''; # reset

    my $ext = $EXT_PORT_TMP{$mv};
    $ext = $EXT_PORT_TMP_PORTALL{$mv} if (!$secc_id); # si no hay seccion, usar plantilla especial.

    $pagina =~ s/%%LOOP%%(.*?)%%\/LOOP%%/$lista/isg;

    # Nombre de la secc en la vista correspondiente
    $mv = '' if ($mv eq '<vista_normal>');
    $secc_nom = &lib_prontus::get_nomtax_envista($mv, $secc_nom4vistas) if ($mv);
    $secc_nom = &lib_prontus::escape_html($secc_nom);


    $pagina =~ s/%%NOMSECC%%/$secc_nom/isg;
    $pagina =~ s/%%SECC%%/$secc_id/isg;
    # reemplazar nombre del prontus
    $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
    $pagina = &lib_prontus::parser_fechap($pagina, $fecha, '_FECHAP');

    $pagina = &lib_prontus::parser_custom_function($pagina);

    $pagina =~ s/%%.*?%%//isg;


    # Prepara y chequea dir para escribir
    $mv = '-' . $mv if ($mv);
    # Escribe pagina
    &glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/extra/calendar/$fecha/pags$mv");
    my $secc_id4filename = $secc_id;
    $secc_id4filename = 'all' if (!$secc_id);
    my $dst_portadilla = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/extra/calendar/$fecha/pags$mv/$secc_id4filename$ext";
    &glib_fildir_02::write_file($dst_portadilla, $pagina);
    &lib_prontus::purge_cache($dst_portadilla);

  };

};



# -------------------------END SCRIPT----------------------

