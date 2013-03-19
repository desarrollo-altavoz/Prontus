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
# PROPOSITO.
# -----------
# Libreria comun para las labores que realizan los diferentes modulos del Wizard
# 

package wizard_lib;

$INF_DIR = "/wizard_prontus/_data";
$INF_FILE = "inf.txt";

$CORE_DIR = '/wizard_prontus/core';
$MODELS_DIR = '/wizard_prontus/models';

$URL_MODELS = "http://www.prontus.cl/release/models";
$FILE_MODELS = 'models.txt';

$DOWNLOAD_DIR = '/_prontus_update/models/download';
$BACKUP_DIR = '/_prontus_update/models/backup';

# --------------------------------------------------------------------------------------------------
# Chequea que se haya pasado por el paso 1
sub check_paso1 {
    
    my $file = "$prontus_varglb::DIR_SERVER$INF_DIR/$INF_FILE";
    if (! -f $file) {
        return "[errInfFile] Solicitud de ejecución no válida.";
    };

    # Leer y cargar y validar contenido del paso1.
    my $buffer = &glib_fildir_02::read_file($file);
    my $prontus_id;
    if ($buffer =~ /(\[PRONTUS\].*\[\/PRONTUS\]\n\n)/s) {
        my $buffer_prontus = $1;
        # Validar id
        if ($buffer_prontus !~ /PRONTUS_ID=(\w+)\n/) {
            return 'Información de paso previo está corrupta. Para poder continuar debe volver al paso anterior.';
        } else {
            $prontus_id = $1;
        };
    } else {
        return 'Información de paso previo está corrupta. Para poder continuar debe volver al paso anterior.';
    };

    # Validar que no exista el dir destino del prontus.
    # Esto ya se chequea en el paso 1 pero se hace nuevamente por seguridad.
    my $dir_prontus = "$prontus_varglb::DIR_SERVER/$prontus_id";

    if (-d $dir_prontus) {
        return "El directorio prontus ya existe. Para continuar con el proceso de instalación Ud. debe cambiar el nombre especificado para el publicador, o bien, <br>eliminar manualmente el directorio existente que genera el conflicto.";
    } else {
        # Lo creo y luego lo borro para verificar que este ok.
        if (&glib_fildir_02::check_dir($dir_prontus)) {
            &glib_fildir_02::borra_dir($dir_prontus);
        } else {
            return "No se puede crear el directorio destino del publicador. No es posible continuar con la instalación.";
        };
    };
    
    return '';
}

# ---------------------------------------------------------------
sub backup_model {

    my ($nom_origen) = shift;
    
    my $dir_origen = "$prontus_varglb::DIR_SERVER$MODELS_DIR";
    if(-d "$dir_origen/$nom_origen") {
        my $dir_destino = "$prontus_varglb::DIR_SERVER$BACKUP_DIR";
        &glib_fildir_02::check_dir($dir_destino);
        
        # Se calcula el directorio para los backup
        my $ts = &glib_hrfec_02::get_dtime_pack4();
        my $nom_destino = $ts.'_'.$nom_origen;
        while(-d "$dir_destino/$nom_destino") {
            sleep(1);
            $ts = &glib_hrfec_02::get_dtime_pack4();
            $nom_destino = $ts.'_'.$nom_origen;
        }
        &glib_fildir_02::copy_tree($dir_origen, $nom_origen, $dir_destino, $nom_destino);
        &garbage_dirs($dir_destino, 5);
        return 1;
    };
    return 0; 
}

# ---------------------------------------------------------------
sub garbage_dirs {
# Deja solo los ultimos 3 respaldos generados por el update

    my ($dir) = shift;
    my ($max) = shift;

    $max = 5 unless($max);
    return unless(-d $dir);
    my @entries = &glib_fildir_02::lee_dir($dir);

    @entries = grep !/^\./, @entries; # Elimina directorios . y ..

    # Ordena por fecha dejando primero los mas nuevos
    @entries = sort { (stat("$dir/$b"))[9] <=> (stat("$dir/$a"))[9] } @entries;

    # Elimina del 3r dir en adelante
    my $numdir = 0;
    foreach my $entry (@entries) {
        next if (!-d "$dir/$entry");
        $numdir++;
        # print STDERR "garbage: revisando [$dir/$entry]\n";
        if ($numdir > $max) {
            # print STDERR "\tgarbage: borrando [$dir/$entry]\n";
            &glib_fildir_02::borra_dir("$dir/$entry");
        };
    };
};

# --------------------------------------------------------------------------------------------------
sub get_models {
    
    my %models;
    my $models_dir = "$prontus_varglb::DIR_SERVER$wizard_lib::MODELS_DIR";
    my ($rutamodelo, $rutamodelofull);
    
    my @lisdir = &glib_fildir_02::lee_dir($models_dir);
    my $nro_models = 0;
    foreach my $model (@lisdir) {
        next if($model =~ /^\./);
        my %array;
        
        $rutamodelo = "$wizard_lib::MODELS_DIR/$model";
        $rutamodelofull = "$prontus_varglb::DIR_SERVER$wizard_lib::MODELS_DIR/$model";
        
        my $buffer = &glib_fildir_02::read_file("$rutamodelofull/$model.cfg");
        if($buffer eq '') {
            print STDERR "No existe el CFG del modelo modelo [$rutamodelofull$model]\n";
            next; 
        }
        
        my $refcfg = &carga_model_cfg($buffer);
        my %cfg = %$refcfg;
        
        # valida q este el arch de obs del modelo
        if (! -f "$rutamodelofull/descripcion/index.html") {
            print STDERR "No existe la descripcion del modelo [$model]\n";
            next;
        };
        # valida la imagen del modelo
        my ($thumb, $imagen);
        if (-f "$rutamodelofull/$model-thumb.png") {
            $thumb = "$rutamodelo/$model-thumb.png";
            $imagen = "$rutamodelo/$model-big.png";
            
        } elsif (-f "$rutamodelofull/$model.gif") {
            $thumb = "$rutamodelo/$model.gif";
            $imagen = "$rutamodelo/$model.gif";
            
        } else {
            print STDERR "No existe la imagen del modelo [$model]... [$rutamodelo]";
            next;
        }
        $nro_models++;
        $models{$model}{'thumb'} = $thumb;
        $models{$model}{'imagen'} = $imagen;
        if($cfg{'MODELO_VERSION'}) {
            $models{$model}{'version'} = $cfg{'MODELO_VERSION'};
        } else {
            $models{$model}{'version'} = '1.0.0.beta';
        }
        $models{$model}{'last_version'} = '<span>Versi&oacute;n no disponible en el servidor remoto</span>';
        if($cfg{'MODELO_NOMBRE_REAL'}) {
            $models{$model}{'nombre'} = "<div>($model)</div>" . $cfg{'MODELO_NOMBRE_REAL'};
            
        } elsif($cfg{'TITLE_SITE_NAME'}) {
            $models{$model}{'nombre'} = "<div>($model)</div>" . $cfg{'TITLE_SITE_NAME'};
            
        } else {
            $models{$model}{'nombre'} = $model;
        };            
        $models{$model}{'desc'} = $cfg{'MODELO_DESCRIPTION'};
        $models{$model}{'instalado'} = 'instalado';
        $models{$model}{'status'} = 'nodisponible';
        #~ $models{$model} = %array;
    };
    
    my ($text, $msg_err) = &lib_prontus::get_url("$URL_MODELS/$FILE_MODELS", 30);
    if($msg_err) {
        print STDERR "No se pudo acceder a los modelos online [$URL_MODELS]";
        $msg_err = "No se pudo acceder a los modelos online.";
        $prontus_varglb::DIR_CORE = $CORE_DIR; # solo para efectos de la plantilla de mensaje
        &glib_html_02::print_pag_result('Error', $msg_err, 0, "exit=1, ctype=1");
    };
    my @modelos = split(/\s/, $text);
    foreach $onlinemodel (@modelos) {
        #~ print STDERR "Leyendo modelo online: $onlinemodel\n";
        my ($buffercfg, $msg_err) = &lib_prontus::get_url("$URL_MODELS/$onlinemodel/$onlinemodel.cfg", 30);
        if($msg_err || $buffercfg eq '') {
            print STDERR "CFG de modelo no encontrado o invalido [$URL_MODELS]";
            next;
        };
        
        $rutamodelo = "$URL_MODELS/$onlinemodel";
        my $refcfg = &carga_model_cfg($buffercfg);
        my %cfg = %$refcfg;
        # En este caso, se confía que el modelo vendrá ok
        unless($models{$onlinemodel}{'thumb'}) {
            $models{$onlinemodel}{'thumb'} = "$rutamodelo/$onlinemodel-thumb.png";
        }
        unless($models{$onlinemodel}{'imagen'}) {
            $models{$onlinemodel}{'imagen'} = "$rutamodelo/$onlinemodel-big.png";
        }
        if($cfg{'MODELO_NOMBRE_REAL'}) {
            $models{$onlinemodel}{'nombre'} = "<div>($onlinemodel)</div>" . $cfg{'MODELO_NOMBRE_REAL'};
        } elsif($cfg{'TITLE_SITE_NAME'}) {
            $models{$onlinemodel}{'nombre'} = "<div>($onlinemodel)</div>" . $cfg{'TITLE_SITE_NAME'};
        } else {
            $models{$onlinemodel}{'nombre'} = $onlinemodel;
        }; 
        $models{$onlinemodel}{'desc'} = $cfg{'MODELO_DESCRIPTION'};
        if($models{$onlinemodel}{'version'}) {
            # Este modelo esta instalado
            $models{$onlinemodel}{'last_version'} = $cfg{'MODELO_VERSION'};
            $models{$onlinemodel}{'online'} = 'online';
            if($models{$onlinemodel}{'version'} eq $models{$onlinemodel}{'last_version'}) {
                $models{$onlinemodel}{'status'} = 'actualizado';
            } elsif(&es_actualizable($models{$onlinemodel}{'version'}, $models{$onlinemodel}{'last_version'}, $onlinemodel)) {
                $models{$onlinemodel}{'status'} = 'actualizar';
            } else {
                $models{$onlinemodel}{'status'} = 'nodisponible';
            }
        } else {
            # El modelo no está instalado
            $models{$onlinemodel}{'version'} = 'No instalado';
            $models{$onlinemodel}{'last_version'} = $cfg{'MODELO_VERSION'};
            $models{$onlinemodel}{'instalado'} = 'noinstalado';
            $models{$onlinemodel}{'status'} = 'descargar';
        }
        #~ $models{$model} = %array;
        $nro_models++;
    };    
    
    if ($nro_models == 0) {
        $msg_err = "No hay Modelos Prontus disponibles.<br>No es posible continuar.";
        $prontus_varglb::DIR_CORE = $CORE_DIR; # solo para efectos de la plantilla de mensaje
        &glib_html_02::print_pag_result('Error', $msg_err, 0, "exit=1, ctype=1");
    }
    return \%models;
}

# --------------------------------------------------------------------------------------------------
sub descarga_componente {
    
    my $modelid = shift;
    my $nombre = shift;
    
    my $url = $wizard_lib::URL_MODELS . '/' . $modelid . '/' .$nombre;
    my ($content, $msg_err) = &lib_prontus::get_url($url, 30);
    if ($msg_err) {
        if ($msg_err =~ /^404 /) {
            return "Error al descargar [$nombre], 404 - no se encuentra el archivo[$url]";
        } else {
            return "Error al descargar [$url]: $msg_err";
        };

    }
    # Se escribe el CFG leído anteriormente
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$MODELS_DIR/$modelid/$nombre", $content);
    return '';
    
};
# --------------------------------------------------------------------------------------------------
sub carga_model_cfg {
    
    my ($buffer) = @_;
    my %cfg;
    
    #~ $buffer =~ s/\[.*?\]\s*?//ig;
    $buffer =~ s/\n+/\n/ig;
    #~ print STDERR "BUFFER[$buffer]\n\n";    
    while($buffer =~ /(\w+)\s*=\s*("|')(.*?)\2/g) {
        $cfg{$1} = $3;
    };

    return \%cfg;
}
# --------------------------------------------------------------------------------------------------
sub es_actualizable {
    
    my ($actual, $last, $model) = @_;
    my ($a1, $a2, $a3, $a4, $l1, $l2, $l3);
    if($actual =~ /(\d+)\.(\d+)\.(\d+)(\.beta)?/) {
        $a1 = $1;
        $a2 = $2;
        $a3 = $3;
        $a4 = 1 if($4);
    } else {
        $a1 = 1;
        $a2 = 0;
        $a3 = 0;
        $a4 = 1;
    }
    if($last =~ /(\d+)\.(\d+)\.(\d+)/) {
        $l1 = $1;
        $l2 = $2;
        $l3 = $3;
        if($a1 != $l1) {
            return 0;
        } elsif($a2 < $l2) {
            return 1; 
        } elsif($a3 < $l3) {
            return 1; 
        } elsif($a3 < $l3) {
            return 1;
        } else {
            if($a3 eq $l3 && $a4) {
                return 1;
            };
        }        
    } else {
        print STDERR "No se pudo leer la versión del modelo online [$model] -> version[$last]\n";
    }
    return 0;
}

return 1;
