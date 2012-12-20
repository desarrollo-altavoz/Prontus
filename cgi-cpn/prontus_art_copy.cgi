#!/usr/bin/perl

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO .
# -----------
# CGI encargadad de 
#
# ---------------------------------------------------------------
# TIPO DE RESPUESTA
# ------------------------------
# json
#
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# 
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# Ninguna.
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 29/05/2012 - CVI - Primera Versión 
#
#
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

use strict;
use prontus_varglb; &prontus_varglb::init();
use glib_fildir_02;
use glib_html_02;
use lib_prontus;
use glib_cgi_04;
use glib_hrfec_02;
use DBI;
use glib_dbi_02;
use lib_waitlock;

# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM);

main: {
    
    my $hash;
    
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

    &lib_waitlock::lock_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/art.smf"); # se le pasa el path completo al arch. semaforo.

    # Debe venir si o si el TS
    $FORM{'_ts'} = &glib_cgi_04::param('_ts');
    if ($FORM{'_ts'} !~ /^\d{14}$/) {
        &glib_html_02::print_json_result(0, 'Artículo no válido', 'exit=1,ctype=1');
    };
    
    my $oldts = $FORM{'_ts'};
    
    # Crear el nuevo TS
    my $newts = &generar_nuevo_ts();
        
    # Copia de XML, HTML y otros elementos con el nuevo TS (mmedia, archivos, etc)
    &copia_archivos($oldts, $newts);
    
    # Reemplazo dentro del XML autoinc + ts, dejar sin ALTA y el titular con (copia) al final
    my ($file, $fid) = &editar_nuevo_artic($oldts, $newts);
    
    # Insertar en BD y en los tags
    my $artic_obj = &actualizar_bd($newts);
    
    # Generar el HTML del nuevo articulo
    &generar_html($artic_obj);
    
    my $fullpath_artic = $artic_obj->get_fullpath_artic('', $artic_obj->{campos}->{'_plt'});
    use FindBin '$Bin';
    my $rutaScript = $Bin;

    # Regenerar el DAM
    &call_dam2save($fullpath_artic, $rutaScript);

    # Clustering
    &call_clustering($fullpath_artic, $rutaScript);
    
    # Ejecutar Post Procesos de artículo
    $artic_obj->exec_post_proceso_art($fullpath_artic, 1);
    
    # Borra cache de no publicados
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");

    &lib_waitlock::unlock_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/art.smf");
    
    # Regenerar taxonomía, tags y relacionados
    # NOTA: Esto por ahora no se hace ya que el artículo no tiene Alta
    
    # Si todo sale bien, se debe devolver el nuevo TS, el FILE y el FID
    $hash->{'status'} = '1';
    $hash->{'msg'} = '';
    $hash->{'fid'} = $fid;
    $hash->{'file'} = $file;
    &glib_html_02::print_json_result_hash($hash, 'exit=1,ctype=1');
    
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub generar_nuevo_ts {
    
    my $ts = &glib_hrfec_02::get_dtime_pack4();
    my $fechac = &lib_prontus::get_dirfecha_by_ts($ts);
    while (-f "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/site/artic/$fechac/xml/$ts" . '.xml') {
        $ts = &glib_hrfec_02::suma_segs($ts, 1);
    };
    return $ts;
}
# --------------------------------------------------------------------------------------------------
sub copia_archivos {
# Saca una copia fisica de un articulo y lo copia en otro

    my $oldts = shift;
    my $newts = shift;
    
    my $oldfechac = &lib_prontus::get_dirfecha_by_ts($oldts);
    my $newfechac = &lib_prontus::get_dirfecha_by_ts($newts);
    
    my $dir_base = $prontus_varglb::DIR_SERVER
                       . "/$prontus_varglb::PRONTUS_ID"
                       . "/site/artic";
                       
    # Se crean los nuevos directorios
    my $res = 1;
    $res = 0 unless(&glib_fildir_02::check_dir("$dir_base/$newfechac"));
    $res = 0 unless(&glib_fildir_02::check_dir("$dir_base/$newfechac/xml"));
    $res = 0 unless(&glib_fildir_02::check_dir("$dir_base/$newfechac/pags"));
    $res = 0 unless(&glib_fildir_02::check_dir("$dir_base/$newfechac/asocfile"));
    $res = 0 unless(&glib_fildir_02::check_dir("$dir_base/$newfechac/imag"));
    $res = 0 unless(&glib_fildir_02::check_dir("$dir_base/$newfechac/swf"));
    $res = 0 unless(&glib_fildir_02::check_dir("$dir_base/$newfechac/mmedia"));
    if(! $res) {
        &glib_html_02::print_json_result(0, "Error al crear los directorios", 'exit=1,ctype=1');
    }
        
    # Se copia el XML
    &File::Copy::copy("$dir_base/$oldfechac/xml/$oldts.xml", "$dir_base/$newfechac/xml/$newts.xml");
    
    # Se copia el HTML y los relacionados manuales
    my @pags = &glib_fildir_02::lee_dir("$dir_base/$oldfechac/pags");
    foreach my $file (@pags) {
        if($file =~ /^$oldts/) {
            &File::Copy::copy("$dir_base/$oldfechac/pags/$file", "$dir_base/$newfechac/pags/$file");
        }
    }
    
    # Los archivos adjuntos
    if(-d "$dir_base/$oldfechac/asocfile/$oldts") {
        &glib_fildir_02::check_dir("$dir_base/$newfechac/asocfile/$newts");
        &glib_fildir_02::copy_tree("$dir_base/$oldfechac/asocfile", $oldts, "$dir_base/$newfechac/asocfile", $newts);
        # Se renombran por si las moscas
        my @asoc = &glib_fildir_02::lee_dir("$dir_base/$newfechac/asocfile/$newts");
        foreach my $file (@asoc) {
            if($file =~ /^(.*?)$oldts(.*?)$/) {
                my $newasoc = $1.$newts.$2;
                &File::Copy::move("$dir_base/$newfechac/asocfile/$newts/$file", "$dir_base/$newfechac/asocfile/$newts/$newasoc");
            }
        }
    }
    
    # Se copian las imagenes
    my @imags = &glib_fildir_02::lee_dir("$dir_base/$oldfechac/imag");
    foreach my $file (@imags) {
        print STDERR "testeando de $dir_base/$oldfechac/imag/$file\n";
        if($file =~ /^(.*?)$oldts(\.\w+)$/) {
            my $newimage = $1.$newts.$2;
            &File::Copy::copy("$dir_base/$oldfechac/imag/$file", "$dir_base/$newfechac/imag/$newimage");
            
        }
    }
    
    # Se copian los flashes
    my @swf = &glib_fildir_02::lee_dir("$dir_base/$oldfechac/swf");
    foreach my $file (@swf) {
        if($file =~ /^(.*?)$oldts(\.\w+)$/) {
            my $newswf = $1.$newts.$2;
            &File::Copy::copy("$dir_base/$oldfechac/swf/$file", "$dir_base/$newfechac/swf/$newswf");
        }
    }
    
    # Se copian los multimedia
    my @mmedia = &glib_fildir_02::lee_dir("$dir_base/$oldfechac/mmedia");
    foreach my $file (@mmedia) {
        if($file =~ /^(.*?)$oldts(\.\w+)$/) {
            my $newmmedia = $1.$newts.$2;
            &File::Copy::copy("$dir_base/$oldfechac/mmedia/$file", "$dir_base/$newfechac/mmedia/$newmmedia");
        }
    }    
};
#~ 
#~ # --------------------------------------------------------------------------------------------------
#~ sub actualizar_autoinc {
    #~ 
    #~ my $newts = shift;
    #~ my $autoinc = shift;
    #~ 
    #~ my $oldfechac = &lib_prontus::get_dirfecha_by_ts($oldts);
    #~ my $newfechac = &lib_prontus::get_dirfecha_by_ts($newts);
        #~ 
    #~ my $filexml = $prontus_varglb::DIR_SERVER
                       #~ . "/$prontus_varglb::PRONTUS_ID"
                       #~ . "/site/artic/$newfechac/xml/$newts.xml";
                           #~ 
    #~ my $buffer = &glib_fildir_02::read_file($filexml);
    #~ if($buffer eq '') {
        #~ &glib_html_02::print_json_result(0, "El xml no se pudo leer", 'exit=1,ctype=1');
    #~ };
    #~ 
    #~ $buffer =~ s/<_art_autoinc>.*?<\/_art_autoinc>/<_art_autoinc>$autoinc<\/_art_autoinc>/is;
    #~ 
    #~ &glib_fildir_02::write_file($filexml, $buffer);
    #~ 
#~ };

# --------------------------------------------------------------------------------------------------
# Reemplazo dentro del XML autoinc + ts, dejar sin ALTA y el titular con (copia) al final
sub editar_nuevo_artic {
  
    my $oldts = shift;
    my $newts = shift;
    
    my $oldfechac = &lib_prontus::get_dirfecha_by_ts($oldts);
    my $newfechac = &lib_prontus::get_dirfecha_by_ts($newts);
        
    my $filexml = $prontus_varglb::DIR_SERVER
                       . "/$prontus_varglb::PRONTUS_ID"
                       . "/site/artic/$newfechac/xml/$newts.xml";
                           
    my $buffer = &glib_fildir_02::read_file($filexml);
    if($buffer eq '') {
        &glib_html_02::print_json_result(0, "El xml no se pudo leer", 'exit=1,ctype=1');
    };
    
    # Se borra el autoinc
    $buffer =~ s/<_art_autoinc>.*?<\/_art_autoinc>/<_art_autoinc><\/_art_autoinc>/is;
    
    # se actualiza el Titular
    my %titular = &lib_prontus::getCamposXml($buffer, '_txt_titular');
    my $tagtitu = "<_txt_titular>\n<![CDATA[(Copia de) " . $titular{'_txt_titular'}."]]>\n</_txt_titular>";
    $buffer =~ s/<_txt_titular>\s*.*?\s*<\/_txt_titular>/$tagtitu/is;
    
    # Se deja el articulo sin el alta
    $buffer =~ s/<_alta>.*?<\/_alta>/<_alta><\/_alta>/is;
    
    # Tentativamente se cambian TODAS las instancias de los TS
    # TODO: Analizar si realmente se debe hacer esto de manera tan brusca
    $buffer =~ s/$oldts/$newts/g;
    $buffer =~ s/\/$oldfechac\//\/$newfechac\//g;
    
    &glib_fildir_02::write_file($filexml, $buffer);
    
    $buffer =~ /<_fid>(.*?)<\/_fid>/g;
    my $fid = $1;
    $buffer =~ /<_plt>(.*?)<\/_plt>/g;
    my $plt = $1;
    my $file = $newts . '.' . &lib_prontus::get_file_extension($plt);
    return ($file, $fid);
}

# --------------------------------------------------------------------------------------------------
sub actualizar_bd {
    
    my $newts = shift;
    
    my $autoinc = 0;
    my $hash_datos;
    
    # Conectar a BD
    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        &lib_waitlock::unlock_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/art.smf");
        &glib_html_02::print_json_result(0, $msg_err_bd, 'exit=1,ctype=1');
    };
    
    my $artic_obj = Artic->new(
                'prontus_id' => $prontus_varglb::PRONTUS_ID,
                'public_server_name' => $prontus_varglb::PUBLIC_SERVER_NAME,
                'cpan_server_name' => $prontus_varglb::IP_SERVER,
                'ts' => $newts, # si no va, asigna uno nuevo
                'campos'=> $hash_datos) || &glib_html_02::print_json_result(0, "Error inicializando objeto articulo: $Artic::ERR\n", 'exit=1,ctype=1');
                    
    $autoinc = $artic_obj->art_insert_bd($base);

    if (!$autoinc) {
        unlink $artic_obj->{fullpath_xml};
        &glib_html_02::print_json_result(0, "El ID unico no se pudo obtener", 'exit=1,ctype=1');
    }

    # Agrega autoinc al XML del artic
    $artic_obj->setear_autoinc($autoinc);
    $base->disconnect;
    
    return $artic_obj;
}

# --------------------------------------------------------------------------------------------------
sub generar_html {
  
    my $artic_obj = shift;
    
    # Fuerza a que se lea el XML porque cuando se hizo el new, se setearon algunas vars pero no todas.
    %{$artic_obj->{xml_content}} = (); 
    
    # Generar vista principal (a partir del xml)
    $artic_obj->generar_vista_art('', $prontus_varglb::STAMP_DEMO, $prontus_varglb::PRONTUS_KEY)
            || &glib_html_02::print_json_result(0, $Artic::ERR, 'exit=1,ctype=1');

    # Generar vistas secundarias (a partir del xml)
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        $artic_obj->generar_vista_art($mv, $prontus_varglb::STAMP_DEMO, $prontus_varglb::PRONTUS_KEY)
                || &glib_html_02::print_json_result(0, $Artic::ERR, 'exit=1,ctype=1');
    };
}

# ---------------------------------------------------------------
sub call_clustering {
    my $fullpath_artic = shift;
    my $rutaScript = shift;

    if (keys(%prontus_varglb::CLUSTERING_SERVER) > 0) {
        my $cmd = "$rutaScript/prontus_cluster_artic.cgi $fullpath_artic &";
        print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
        system $cmd;
    };
};

# ---------------------------------------------------------------
sub call_dam2save {
    my $fullpath_artic = shift;
    my $rutaScript = shift;

    my $cmd = "$rutaScript/dam/prontus_dam_ppart_save.cgi $fullpath_artic $prontus_varglb::PUBLIC_SERVER_NAME &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};

# -------------------------------END SCRIPT----------------------
