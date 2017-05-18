#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

package lib_artic;
use strict;
use Carp qw(cluck carp);
use warnings;
no warnings 'uninitialized';

use DBI;
use lib_prontus;
use lib_waitlock;
use glib_fildir_02;
use lib_tax;

our $ARTIC_OBJ; # debe setearse antes de usar la funcion maestra save_artic_with_object()

# ---------------------------------------------------------------
sub save_artic_with_object {
# Esta funcion asume que ya esta cargado el cfg de prontus
# Realiza todo lo necesario para crear o updatear un articulo, excepto clustering.
# Incluye semaforo.
# To-Do: Incluir hash de conf para indicar si tal operacion se realiza o no.
    my $is_new = $_[0]; # 1 | 0

    &lib_waitlock::lock_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/art.smf"); # se le pasa el path completo al arch. semaforo.

    # Conectar a BD
    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();

    if (! ref($base)) {
        &lib_waitlock::unlock_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/art.smf");
        return $msg_err_bd;
    };

    my $pag_articulo;
    my $autoinc = 0;
    my $post_proceso_lista;

    # regenera los <tag>.txt para los tags q tenía el artículo antes de ser modificado
    my %campos_xml_old;
    my $tags_old;
    if (!$is_new) {
        %campos_xml_old = $ARTIC_OBJ->get_xml_content();
        $tags_old = $campos_xml_old{'_tags'};
    };

    # Generar y guardar xml. Se guardan los recursos subidos a traves del fid
    # Esto es comun para nuevo y actualizar
    if (!$ARTIC_OBJ->generar_xml_artic()) {
        &lib_waitlock::unlock_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/art.smf");
        return $Artic::ERR;
    };

    # Guardar articulo.
    my $msg_err_save = &do_save($base, $is_new);
    if ($msg_err_save) {
        &lib_waitlock::unlock_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/art.smf");
        return $msg_err_save;
    };

    # Full path del artic (de la vista default)
    my $fullpath_artic = $ARTIC_OBJ->get_fullpath_artic('', $ARTIC_OBJ->{campos}->{'_plt'});

    # Loguear modificacion
    my $label_action = 'Actualizar';
    $label_action = 'Ingresar' if ($is_new);
    &lib_prontus::write_log($label_action, 'Articulo', $fullpath_artic);

    # Lee de vuelta del XML
    my %campos_xml = $ARTIC_OBJ->get_xml_content();

    # Regen ports que correspondan
    &regen_ports($fullpath_artic);

    my ($s1, $t1, $st1) = ($campos_xml{'_seccion1'}, $campos_xml{'_tema1'}, $campos_xml{'_subtema1'});

    # Si el articulo tenía s/t/st hay que regenerar los relacionados para que no aparezca.
    if ($campos_xml_old{'_seccion1'} && !$s1) {
      $s1 = $campos_xml_old{'_seccion1'};
    };

    if ($campos_xml_old{'_tema1'} && !$t1) {
      $t1 = $campos_xml_old{'_tema1'};
    };

    if ($campos_xml_old{'_subtema1'} && !$st1) {
      $st1 = $campos_xml_old{'_subtema1'};
    };

    # Se agregan los relacionados manuales antiguos para tambien regenerarlos.
    my $tax = $campos_xml{'_tax'};
    $tax .= "," . $campos_xml_old{'_tax'} if ($campos_xml_old{'_tax'});

    # Regen relacionados
    &generar_relacionados($tax, $ARTIC_OBJ->{ts}, $base, $ARTIC_OBJ->{dst_pags},
                          $s1, $t1, $st1);


    # genero pa los q tenia el artic. mas los re100 asociados
    my $tags2regen = $campos_xml{'_tags'} . ',' . $tags_old;
    $tags2regen =~ s/^,//;
    $tags2regen =~ s/,$//;
    $tags2regen =~ s/,+/,/;

    # Geenero los txt para los tags agregados
    &generar_relacionados_tagging($base, "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO", $tags2regen);

    $base->disconnect;

    $ARTIC_OBJ->exec_post_proceso_art($fullpath_artic, $is_new);

    # Borra cache de no publicados
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");

    &lib_waitlock::unlock_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/art.smf");

    return '';
};
# ---------------------------------------------------------------
sub generar_relacionados {

    return if ($prontus_varglb::TAXONOMIA_NIVELES !~ /^[1-3]$/);

    my ($tax, $ts, $base, $dst_pags, $s, $t, $st) = @_;

    # print STDERR "dir_cont[$prontus_varglb::DIR_CONTENIDO]\n";
    &lib_tax::set_vars($prontus_varglb::DIR_CONTENIDO,
                        $prontus_varglb::DIR_ARTIC,
                        $prontus_varglb::DIR_PAG,
                        $prontus_varglb::DIR_TEMP,
                        $prontus_varglb::DIR_TAXONOMIA,
                        $prontus_varglb::NUM_RELAC_DEFAULT,
                        $prontus_varglb::CONTROLAR_ALTA_ARTICULOS);
    my $mv;
    # Genera taxonomia manual.
    if ($tax ne '') {
        &lib_tax::generar_relacionados_manualtax($tax, $dst_pags, $ts, $base, '');
        # Ahora parsea art relacionados para MVs
        foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
            &lib_tax::generar_relacionados_manualtax($tax, $dst_pags, $ts, $base, $mv);
        };
    # Si no hay manual usa la automatica
    } else {
        &lib_tax::borrar_relacionados_manualtax($dst_pags, $ts);
        if ($s) {
            &lib_tax::generar_relacionados($s, $t, $st, $base, '');
            # Ahora parsea art relacionados para MVs
            foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
                &lib_tax::generar_relacionados($s, $t, $st, $base, $mv);
            };
        };
    };

};

# ---------------------------------------------------------------
sub generar_relacionados_tagging {
# generar /prontus_dir/site/cache/tagging/pags/<idtag>.txt
# Cada archivo contiene lineas del tipo <fechaphorap>\t<ts>\t<titular>\n
# ordenadas por fechaphorap.

    my ($base, $dir_cont, $str_idtags) = @_;

    my $dthr_system = &glib_hrfec_02::get_dtime_pack4();
    $dthr_system =~ /^(\d{8})(\d\d\d\d)/;
    my $hhmm_system = $2;
    my $dt_system = $1;

    my $dir_tagging = "$dir_cont/cache/tagging/pags";
    &glib_fildir_02::check_dir($dir_tagging);
    my @tags = split(/,/, $str_idtags);
    my %hash_tags_procesados;
    my $ctrl_fecha = 0;
    $ctrl_fecha = 1 if ($prontus_varglb::CONTROL_FECHA eq 'SI');
    foreach my $idtag (@tags) {
        next if (exists $hash_tags_procesados{$idtag});
        $hash_tags_procesados{$idtag} = 1;
        my $pathfile_tag = "$dir_tagging/$idtag.txt";

        my $filtros = "TAGSART_IDTAGS='$idtag' and TAGSART_IDART=ART_ID";
        $filtros .= " and (ART_FECHAPHORAP <= '$dt_system$hhmm_system') ";
        $filtros .= " and (ART_ALTA = '1') " if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS eq 'SI');

        if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
          $filtros .= " and ( (ART_FECHAEHORAE >= '$dt_system$hhmm_system') OR ( (ART_FECHAEHORAE < '$dt_system$hhmm_system') AND (ART_SOLOPORTADAS = '1') ) )";
        };
        my $sql = "select ART_ID, ART_FECHAPHORAP, ART_FECHAEHORAE, ART_TITU, ART_EXTENSION, ART_TIPOFICHA, ART_SOLOPORTADAS from ART, TAGSART where $filtros order by ART_FECHAPHORAP desc limit 50";

        my ($art_id, $art_fechaphorap, $art_titu, $art_extension, $art_tipoficha, $art_fechaehorae, $art_soloportadas);
        my $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($art_id, $art_fechaphorap, $art_fechaehorae, $art_titu, $art_extension, $art_tipoficha, $art_soloportadas));
        my $buffer_tag_txt;
        while ($salida->fetch) {
            $art_titu =~ s/[\t\r\n]//;
            $buffer_tag_txt .= "$art_id\t$art_fechaphorap\t$art_fechaehorae\t$art_titu\t$art_extension\t$art_tipoficha\t$art_soloportadas\t$ctrl_fecha\n";
        };
        $salida->finish;
        # warn "pathfile_tag[$pathfile_tag]\n";
        &glib_fildir_02::write_file($pathfile_tag, $buffer_tag_txt);
    };

};
# ---------------------------------------------------------------
sub do_save {
# Actualiza registro de bd en base a info que carga del xml
    my $base = shift;
    my $is_new = shift; # 1 | 0

    my $autoinc = 0;
    if ($is_new) {
        $autoinc = $ARTIC_OBJ->art_insert_bd($base);
        unlink $ARTIC_OBJ->{fullpath_xml} if (!$autoinc);
    } else {
        $autoinc = $ARTIC_OBJ->art_update_bd($base);
    };

    return $Artic::ERR if (!$autoinc);

    # Agrega autoinc al XML del artic
    $ARTIC_OBJ->setear_autoinc($autoinc);

    # Generar vista principal (a partir del xml)
    # print STDERR "Generar vista normal con autoinc[$autoinc]\n";
    %{$ARTIC_OBJ->{xml_content}} = (); # fuerza a que se lea el XML porque cuando se hizo el new, se setearon algunas vars pero no todas.
    $ARTIC_OBJ->generar_vista_art('', $prontus_varglb::STAMP_DEMO, $prontus_varglb::PRONTUS_KEY)
            || return $Artic::ERR;

    my $fid = $ARTIC_OBJ->{campos}->{'_fid'};

    # Generar vistas secundarias (a partir del xml)
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        # print STDERR "Generar vista $mv con autoinc[$autoinc]\n";
        $ARTIC_OBJ->generar_vista_art($mv, $prontus_varglb::STAMP_DEMO, $prontus_varglb::PRONTUS_KEY)
                || return $Artic::ERR;
    };

    $ARTIC_OBJ->tags2bd($base, $is_new) || return $Artic::ERR;
    # print STDERR "fin save con autoinc[$autoinc]\n";

    if ($prontus_varglb::FRIENDLY_URLS eq 'SI' && $prontus_varglb::FRIENDLY_URLS_VERSION eq '4') {
        # guardamos el titular friendly v4 en la base de datos
        $ARTIC_OBJ->genera_friendly_v4($base, $is_new) || return $Artic::ERR;
    }

    if ($prontus_varglb::MULTITAG eq 'SI') {
        # guardamos los campos de multitag en la db
        $ARTIC_OBJ->multitag2db($base, $is_new) || return $Artic::ERR;
    }

    return '';

};
# ---------------------------------------------------------------
sub regen_ports {
# Sea nuevo o modificar, y si hay control de alta, se reconstruyen las portadas de la
# edicion base, vigente y ultima que tengan ese articulo publicado.
# Las portadas que no tengan el articulo publicado no se tocan.

    my $artic = shift;
    # Recibe el path completo de la vista pero lo machetea para dejar solo el nombre del
    # archivo mas su extension.
    no warnings 'syntax'; # para evitar el msg "\1 better written as $1"
    $artic =~ s/.+(\d{14})\.\w+$/\1/;
    if ($prontus_varglb::ARTIC_ACTUALIZA_PORTS eq 'SI') {
        &lib_prontus::actualizar_portadas_byartic($artic, 'ALTA_CONTROL');
    };
};
# ---------------------------------------------------------------
sub publica_art_in_port {
# funcion para publicacion directa de 1 artic en alguna port.
  my ($full_path_port, $edic, $nom_port, $prontus_id, $ts_new_artic, $fid_artic, $area) = @_;

#  print STDERR "full_path_port[$full_path_port]\n";
  # print STDERR "nom_port[$nom_port]\n";
#  print STDERR "prontus_id[$prontus_id]\n";
#  print STDERR "nom_artic[$nom_artic]\n";
#  print STDERR "area[$area]\n";

  my ($pathdir_pags, $pathdir_seccs, @entries, $entry, $text_seccion,  $id);


  %lib_prontus::AREA = ();
  %lib_prontus::PRIO = ();
  %lib_prontus::DIR_FECHA = ();
  %lib_prontus::VB = ();


  my $full_path_xmlport = $full_path_port;
  no warnings 'syntax'; # para evitar el msg "\1 better written as $1"
  $full_path_xmlport =~ s/\/port\/(\w+)(\.\w+)?$/\/xml\/\1\.xml/;

  # Rescatar la info de c/artic de la portada
  # print STDERR "full_path_xmlport[$full_path_xmlport]\n";
  my %rowartics = &lib_prontus::get_rowartics($full_path_xmlport);

  my $orden_art_new;
  my $is_first = 1;
  # art publicados en la portada, ordenados por area/orden
  foreach my $art (sort{$rowartics{$a}{'area'} <=> $rowartics{$b}{'area'} || $rowartics{$a}{'ord'} <=> $rowartics{$b}{'ord'}}(keys %rowartics)) {
    # art es de la forma <ts>

    $lib_prontus::AREA{$art} = $rowartics{$art}{'area'};
    $lib_prontus::PRIO{$art} = $rowartics{$art}{'ord'};
    $lib_prontus::DIR_FECHA{$art} = $rowartics{$art}{'dir'};
    $lib_prontus::VB{$art} = $rowartics{$art}{'vb'};
    # $last_orden = $rowartics{$art}{'ord'} if ($rowartics{$art}{'area'} == $area);

    # Rescata FIDs de cada articulo, a fin de poder publicar el nuevo artic encima del primero de su tipo.
    my $artic_obj = Artic->new(
                    'prontus_id'=>$prontus_id,
                    'public_server_name'=>$prontus_varglb::PUBLIC_SERVER_NAME,
                    'cpan_server_name'=>$prontus_varglb::IP_SERVER,
                    'document_root'=>$prontus_varglb::DIR_SERVER,
                    'ts'=>$art,
                    'campos'=>{}) || die "Error inicializando objeto articulo: $Artic::ERR\n";
    my %campos_xml = $artic_obj->get_xml_content();

    # print STDERR "art[$art] area[$rowartics{$art}{'area'}] orden[$rowartics{$art}{'ord'}]art existente[$campos_xml{'_txt_titular'}]\n";

    # revisar pq no funciona!!!!!!!!!!!!!!!
    if (($campos_xml{'_fid'} eq $fid_artic) && ($is_first)) {
        $orden_art_new = $rowartics{$art}{'ord'} - 1;
        $is_first = 0;
    };
  };

  $orden_art_new = 1 if ($orden_art_new < 1);  # en caso de que no se haya detectado ninguno de este tipo

  # Agrega art. a publicar
  $lib_prontus::DIR_FECHA{$ts_new_artic} = &glib_hrfec_02::get_date_pack4();
  $lib_prontus::AREA{$ts_new_artic} = $area;      # Asocia area al articulo.
  $lib_prontus::PRIO{$ts_new_artic} = $orden_art_new;      # Asocia prioridad correspondiente.

  # VoBo depende del perfil, si es periodista --> lo deja sin VB
  my $vb = 'S';
  $vb = '' if ($prontus_varglb::USERS_PERFIL eq 'P');

  # Si es Editor y no tiene asignada la portada, tb. lo deja sin VoBo
  if ($prontus_varglb::USERS_PERFIL eq 'E') { # Editor
    if (! &lib_prontus::port_asoc($nom_port)) {
      $vb = '';
    };
  };

  $lib_prontus::VB{$ts_new_artic} = $vb;

  # Regenera la portada correspondiente
  my $mv = '';
  my $sin_regen_xml = 0;
  my $ts_preview = '';
  &lib_prontus::make_portada($full_path_port, "$prontus_varglb::DIR_SERVER/$prontus_id/plantillas/edic/nroedic/port/$nom_port", $prontus_varglb::DIR_SERVER, $prontus_id,
                           $mv, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
                           $edic, $sin_regen_xml, $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
                           $ts_preview, $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $prontus_varglb::USERS_PERFIL);



  # Ahora proceso multivistas
  $sin_regen_xml = 1;
  foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
    &lib_prontus::make_portada($full_path_port, "$prontus_varglb::DIR_SERVER/$prontus_id/plantillas/edic/nroedic/port/$nom_port", $prontus_varglb::DIR_SERVER, $prontus_id,
                             $mv, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
                             'base', $sin_regen_xml, $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
                             $ts_preview, $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $prontus_varglb::USERS_PERFIL);
  };

  # print STDERR "DESPUES";
};

# ---------------------------------------------------------------
return 1;

