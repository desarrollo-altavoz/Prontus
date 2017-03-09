#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO .
# -----------
# Publicar un artículo desde fuera del administrador Prontus.
# El artículo puede quedar despublicado o bien publicado
# en alguna portada con algun area/orden, con y sin VoBo, todo
# lo anterior dependiendo de los parametros q vengan en el FID y en el archivo cd cfg.
# Implementa control de procesos iguales.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------


# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde cualquier form, vienen los campos como en cualquier fid prontus
# ademas:
# _NP = nombre del publicador, ejemplo "prontus_noticias", se asume q esta en la raiz del sitio
# _IDF = identificador alfanumerico del formulario (ej: "subetuscont")
# _CAPTCHA = captcha a validar
# _MODE = modo en el que correrá la cgi (por ahora sólo acepta modo 'batch'
#
# El resto de los param especiales necesarios se sacan del cfg:
# <nomprontus>-posting.cfg y se agrupan por cada IDF
# ---------


# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------

# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - ycc - 29/01/2007 - primera version
# 1.1 - YCC - 29/11/2007 - Impide que vengan por param el _VB y el _ALTA
# 1.2 - YCC - 01/2008 - Agrega control de captcha y bloqueo de ips
# 1.3 - CVI - 04/2008 - Para el modo Posting Batch
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    use FindBin '$Bin';
    $pathLibs = $Bin;
    unshift(@INC, $pathLibs);
    do 'dir_cgi.pm';
    $pathLibs =~ s/\/[^\/]+$/\/$DIR_CGI_CPAN/;
    unshift(@INC,$pathLibs);
};

use strict;
# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();

use glib_html_02;
use glib_fildir_02;
use lib_prontus;
use glib_str_02;
use glib_hrfec_02;

use glib_cgi_04;

use File::Copy;

use glib_dbi_02;
use DBI;
use lib_tax;
use lib_waitlock; # Bloqueos tipo espera.
use lib_thumb;
use lib_captcha;
use lib_captcha2;
use lib_ipcheck;
use lib_artic;
use lib_maxrunning;
use lib_form;

# ---------------------------------------------------------------
# MAIN.
# -------------
my (%CONFIG_POSTING, $ARTIC_OBJ, %FORM);

my $CACHE_DIR = 'site/cache/posting'; # /pags-vvv Directorio de las paginas generadas.
my $ANSWERS_DIR;

main: {
    # Soporta un maximo de n copias corriendo.
    if (&lib_maxrunning::maxExcedido(4)) {
        print "Content-Type: text/html\n\n";
        print "Error: Servidor ocupado.";
        exit;
    };


    # valida
    if ($ENV{'REQUEST_METHOD'} ne 'POST') {
        &glib_html_02::print_pag_result("Error", 'Solicitud no válida', 0, 'exit=1,ctype=1');
    };

    # Validacion y gestion de ip bloqueada
    my $dir_ip_control = 'ip_control_art_posting'; # dentro del prontus_temp
    my $user_ip = $ENV{'REMOTE_ADDR'};
    my $maxrequest_por_ip = 30;
    my $bloqueoip_interval = 60;
    my $bloquear_ip = &lib_ipcheck::check_bloqueo_ip($dir_ip_control, $user_ip, $maxrequest_por_ip, $bloqueoip_interval);
    if ($bloquear_ip) {
        &glib_html_02::print_pag_result("Error","907-Request inhabilitado.", 0, 'exit=1,ctype=1');
    };

    # Validar size total de los datos submitidos
    &validar_content_length();

    # Rescatar parametros recibidos, se asumen todos en mayusculas
    &glib_cgi_04::new();

    # Nombre del prontus
    $FORM{'_NP'} = &glib_cgi_04::param('_NP');
    # $FORM{'_NP'} =~ s/[^0-9a-zA-Z\-\_]//sg;
    if (!&lib_prontus::valida_prontus($FORM{'_NP'})) {
        &glib_html_02::print_pag_result("Error","901-Error en los datos enviados.", 0, 'exit=1,ctype=1');
    };

    # Id del form de posting
    $FORM{'_IDF'} = &glib_cgi_04::param('_IDF');
    $FORM{'_IDF'} =~ s/[^0-9a-zA-Z\-\_]//sg;
    if (!$FORM{'_IDF'}) {
        &glib_html_02::print_pag_result("Error","902-Error en los datos enviados.", 0, 'exit=1,ctype=1');
    };

    # Path de cfg de prontus
    $FORM{'_PATH_CONF'} = "/$FORM{'_NP'}/cpan/$FORM{'_NP'}.cfg";
    $FORM{'_PATH_CONF'} = &lib_prontus::ajusta_pathconf($FORM{'_PATH_CONF'});

    # Carga variables de configuracion de prontus.
    &lib_prontus::load_config($FORM{'_PATH_CONF'});
    $FORM{'_PATH_CONF'} =~ s/^$prontus_varglb::DIR_SERVER//;


    # Cargar var de conf de posting
    if (!&load_config_posting()) {
        &glib_html_02::print_pag_result("Error","903-Error en los datos enviados.", 0, 'exit=1,ctype=1');
    };

    # Asigna valores por defecto a vars de cfg de posting.
    &load_default_posting_params();

    # Define directorio de las respuestas y la identificacion de esta.
    $ANSWERS_DIR = "/$FORM{'_NP'}/$CACHE_DIR";
    #~ print STDERR "ANSWERS_DIR[$ANSWERS_DIR]\n";
    if (! (-d "$prontus_varglb::DIR_SERVER$ANSWERS_DIR") ) {
        if (&glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$ANSWERS_DIR") == 0) {
            &make_resp_and_exit("No se puede crear directorio de respuestas [$ANSWERS_DIR].", 1);
        };
    };

    # Limpia el directorio de archivos temporales.
    &lib_form::garbage_collection("$prontus_varglb::DIR_SERVER$ANSWERS_DIR");

    # CVI - Cambio para Posting Batch
    $FORM{'_MODE'} = &glib_cgi_04::param('_MODE'); # 'batch' | <anything>

    # Validacion captcha
    # Si es modo batch, no se valida captcha
    if ($FORM{'_MODE'} ne 'batch') {

        # Usando la nueva lib_captcha se manejan ambos formatos
        my $captcha_input = &glib_cgi_04::param('_CAPTCHA');
        my $captcha_type = 'posting'; # custom
        my $captcha_img = &glib_cgi_04::param('_captcha_img');
        my $captcha_code = &glib_cgi_04::param('_captcha_code');
        $captcha_input = &glib_cgi_04::param('_captcha_text') unless($captcha_input);
        #~ require 'dir_cgi.pm';
        &lib_captcha2::init($prontus_varglb::DIR_SERVER, $prontus_varglb::DIR_CGI_CPAN);
        my $msg_err_captcha = &lib_captcha2::valida_captcha($captcha_input, $captcha_code, $captcha_type, $captcha_img);
        if ($msg_err_captcha ne '') {
            &make_resp_and_exit($msg_err_captcha, 1);
        };
    };

    # Crear objeto Artic
    $lib_artic::ARTIC_OBJ = &crear_objeto_artic();

    # Salvar el articulo en base a los datos del objeto Artic
    my $is_new = 1;
    my $msg_err_save = &lib_artic::save_artic_with_object($is_new);
    &glib_html_02::print_pag_result("Error", $msg_err_save, 1, 'exit=1,ctype=1') if ($msg_err_save);

    my $rutaScript = "$prontus_varglb::DIR_SERVER/$prontus_varglb::DIR_CGI_CPAN";

    # Solo se ejecutan estos procesos si el articulo tiene alta.
    &call_procs($rutaScript) if (&param('_alta'));

    my $fullpath_artic = $lib_artic::ARTIC_OBJ->get_fullpath_artic('', $lib_artic::ARTIC_OBJ->{campos}->{'_plt'});
    &call_clustering($rutaScript, $fullpath_artic);

    # Agregar el art. a portada
    if ((&param('_port')) && (&param('_area'))) {
        # Publicar art. nuevo.
        my $dir_port = "$prontus_varglb::DIR_SERVER/$FORM{'_NP'}/site/edic/base/port";
        my $nom_port = &param('_port');
        my $ts = $lib_artic::ARTIC_OBJ->{ts};
        &lib_artic::publica_art_in_port("$dir_port/$nom_port", 'base', $nom_port, $FORM{'_NP'}, $ts, $lib_artic::ARTIC_OBJ->{campos}->{'_fid'}, &param('_area'));
    };

    # CVI - Para el modo batch... esto es lo mas simple que pude encontrar
    if ($FORM{'_MODE'} eq 'batch') {
        print "Content-Type: text/plain\n\n";
        print '1';
    } else {
        &make_resp_and_exit(&param('_msg_ok'));
    };

};
# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

sub crear_objeto_artic {
# Crea objeto Artic, para lo cual es basico cargar el hash de datos a partir
# de los datos submitidos.

    my @campos = &param(); # No toma los datos directamente submitidos, sino los adaptados
                           # y complementados con la conf de posting.
    my %hash_datos;
    foreach my $nom_campo (sort {$a cmp $b} @campos) {
        # Al obj artic se le pasan los campos en minusculas
        my $nom_lc = lc $nom_campo;
        $hash_datos{$nom_lc} = &param($nom_campo);
        if (($nom_lc =~ /^asocfile_/) && ($hash_datos{$nom_lc} ne '')) {
            $hash_datos{$nom_lc}{'real_path'} = &glib_cgi_04::real_paths($nom_campo);
        };
    };


    # Si no hay control de alta, todos quedan con alta=1.
    $hash_datos{'_alta'} = '1' if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS ne 'SI');

    my $artic_obj = Artic->new(
                    'prontus_id'        =>$prontus_varglb::PRONTUS_ID,
                    'public_server_name'=>$prontus_varglb::PUBLIC_SERVER_NAME,
                    'cpan_server_name'  =>$prontus_varglb::IP_SERVER,
                    'ts'                =>'', # si no va, asigna uno nuevo
                    'campos'            =>\%hash_datos)
                    || die "Error inicializando objeto articulo: $Artic::ERR\n";


    return $artic_obj;

};

# ---------------------------------------------------------------
sub validar_content_length {
    # Validar tamaño del chorro
    my $posting_limit_mb = 20; # MB
    if (-s 'posting_limit.cfg') {
        $posting_limit_mb = &glib_fildir_02::read_file('posting_limit.cfg');
        if ($posting_limit_mb !~ /^\d+$/) {
            &glib_html_02::print_pag_result("Error","908-Error de configuración en valor de posting limit."
                                            , 0, 'exit=1,ctype=1');
        };
    };
    if ($ENV{'CONTENT_LENGTH'} > (1048576 * $posting_limit_mb)) {
        &glib_html_02::print_pag_result("Error","909-Datos enviados exceden límite permitido de $posting_limit_mb MB"
                                        , 0, 'exit=1,ctype=1');
    };
};
# ---------------------------------------------------------------
sub salir {
  my $msg = $_[0];
  print "Content-Type: text/html\n\n";
  print $msg;
  exit;
};
# ---------------------------------------------------------------
sub load_config_posting {
  # Ejemplo de cfg.
  # [subetuscont]
  # _users_id = '1', id de usr a nombre del cual se publica el artic, si no viene, se asume admin
  # _fid = 'fid_general.html', usr a nombre del cual se publica el artic, si no viene, se asume admin
  # _plt = 'general.html', usr a nombre del cual se publica el artic, si no viene, se asume admin
  # _alta = '1'
  #
  # _seccion1 = '8';
  # _tema1 = '';
  # _subtema1 = '';
  #
  # _nom_seccion1 = 'deportes';
  # _nom_tema1 = '';
  # _nom_subtema1 = '';

  # las sgtes. marcas son nuevas y reservadas:
  # _msg_plantilla = 'msg.html' /<nomprontus>/plantillas/extra/posting/pags/
  # _msg_marca = '%%msg%%'
  # _msg_ok = 'gracias por enviar tus contenidos'

  # _portada = 'inicio.html' si no viene, el art. no se publica en la portada
  # _area = '1' si no viene, el art. no se publica en la portada
  # _orden = '2' si no viene, se asume 1
  # _vb = 's' si no viene, se asume n
  # [/subetuscont]

  # Carga config de posting.
  my $path_cfg = "$prontus_varglb::DIR_SERVER/$FORM{'_NP'}/cpan/$FORM{'_NP'}-posting.cfg";
  my $buffer = &glib_fildir_02::read_file($path_cfg);
  #~ print STDERR "path_cfg [$path_cfg]\n";
  return 0 if (!$buffer);

  my $idf = $FORM{'_IDF'}; # id del form de posting
  if ($buffer =~ /\[$idf\](.*?)\[\/$idf\]/is) {
    my $data = $1;
    while ($data =~ /\s*([\w\-]+) *= *("|')(.*?)("|')/isg) {
      my ($clave, $valor) = ($1, $3);
      #~ print STDERR "$clave [$valor]\n";
      $CONFIG_POSTING{lc $clave} = $valor;
    };
  }
  else {
    return 0;
  };
  return 1;

};
# ---------------------------------------------------------------
sub make_resp_and_exit {
    # Genera respuesta.
    my $msg = $_[0];
    my $error = $_[1];

    my $plt = '';
    my $plterror = &param('_error_plantilla');
    if($error && $plterror) {
        $plt = $plterror;
    } else {
        $plt = &param('_msg_plantilla');
    };
    my $path_plt = "$prontus_varglb::DIR_SERVER/$FORM{'_NP'}/plantillas/extra/posting/pags/" . $plt;

    my $buffer;
    #~ print STDERR "path_plt[$path_plt]\n";
    if (-f $path_plt) {
        $buffer = &glib_fildir_02::read_file($path_plt);
    };

    if ($buffer) {
        my $marca = &param('_msg_marca');
        $buffer =~ s/$marca/$msg/ig;
    } else {
        $buffer = $msg;
    };

    my $answerid = $prontus_varglb::PRONTUS_ID . time . $$; # rand(1000000000);
    my $extension = &lib_prontus::get_file_extension($path_plt);

    # Escribe el archivo de respuesta.
    my $archivo = "$ANSWERS_DIR/$answerid\.$extension";
    open (ARCHIVO,">$prontus_varglb::DIR_SERVER$archivo")
            || die "Content-Type: text/plain\n\n Fail Open file $archivo \n $!\n";

    #~ print STDERR "archivo[$prontus_varglb::DIR_SERVER$archivo]\n";

    #binmode(ARCHIVO, ":utf8");
    print ARCHIVO $buffer; #Escribe buffer completo
    close ARCHIVO;

    # Redirige al visitante hacia la pagina de respuesta.
    print "Location: $archivo\n\n";
    exit;

};
# ---------------------------------------------------------------
sub param {
    # Obtiene dato del hash del cfg de posting y si no existe,
    # entonces lo saca de los submitidos.
    my $key = $_[0];
    if ($key) {
      if ($CONFIG_POSTING{lc $key}) {
        return $CONFIG_POSTING{lc $key};
      }
      else {
        return '' if (uc $key eq '_ALTA'); # NO PERMITE QUE VENGA EL _ALTA POR PARAMETRO.
        return '' if (uc $key eq '_VB'); # NO PERMITE QUE VENGA EL _VB POR PARAMETRO.
        return '' if (uc $key eq '_REGEN_LIST'); # NO PERMITE QUE VENGA POR PARAMETRO.
        return '' if (uc $key eq '_REGEN_TAXPORT'); # NO PERMITE QUE VENGA POR PARAMETRO.
        return '' if (uc $key eq '_REGEN_TAGPORT'); # NO PERMITE QUE VENGA POR PARAMETRO.
        return &glib_cgi_04::param($key);
      };
    }
    else {
      my @campos = &glib_cgi_04::param();
      my $k;
      foreach $k (keys %CONFIG_POSTING) {
        push @campos, $k if (!exists $glib_cgi_04::FORM{$k});
      };
      return @campos;
    };

};
# ---------------------------------------------------------------
sub load_default_posting_params {
  $CONFIG_POSTING{'_users_id'} = '1' if (!&param('_users_id'));

  $CONFIG_POSTING{'_fid'} = 'fid_general' if (!&param('_fid'));

  $CONFIG_POSTING{'_plt'} = 'general.html' if (!&param('_plt'));

  $CONFIG_POSTING{'_msg_marca'} = '%%MSG%%' if (!&param('_msg_marca'));

  $CONFIG_POSTING{'_msg_ok'} = 'Gracias, su información ha sido recibida' if (!&param('_msg_ok'));

  $CONFIG_POSTING{'_orden'} = '1' if (!&param('_orden'));

  $CONFIG_POSTING{'_vb'} = 'N' if (!&param('_vb'));

  $CONFIG_POSTING{'_seccion1'} = '' if (!&param('_seccion1'));
  $CONFIG_POSTING{'_tema1'} = '' if (!&param('_tema1'));
  $CONFIG_POSTING{'_subtema1'} = '' if (!&param('_subtema1'));


  $CONFIG_POSTING{'_regen_list'} = 'N' if (!&param('_regen_list'));
  $CONFIG_POSTING{'_regen_taxport'} = 'N' if (!&param('_regen_taxport'));
  $CONFIG_POSTING{'_regen_tagport'} = 'N' if (!&param('_regen_tagport'));
};
# ---------------------------------------------------------------
sub call_procs {
    my $rutaScript = $_[0];
    my $fid = &param('_fid');
    my $tags_id = &param('_tags');
    my $filtro_fid = '';

    # Verifica que exista filtro para FID
    my $dir_filtro_fid = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_TEMP
                       . $prontus_varglb::DIR_PTEMA . '/' . $fid;

    if (-e $dir_filtro_fid) {
        $filtro_fid = $fid;
    };

    my $seccion1 = &param('_seccion1');
    my $tema1 = &param('_tema1');
    my $subtema1 = &param('_subtema1');

    my $seccion2 = &param('_seccion2');
    my $tema2 = &param('_tema2');
    my $subtema2 = &param('_subtema2');

    my $seccion3 = &param('_seccion3');
    my $tema3 = &param('_tema3');
    my $subtema3 = &param('_subtema3');

    if ($seccion1) {
        my $param_especif_taxport = '/' . $seccion1
                                  . '/' . $tema1
                                  . '/' . $subtema1;

        &call_taxports_regen($rutaScript, "$filtro_fid$param_especif_taxport") if ($CONFIG_POSTING{'_regen_taxport'} eq 'S');
        &call_list_regen($rutaScript, "$fid$param_especif_taxport") if ($CONFIG_POSTING{'_regen_list'} eq 'S');
    };

    if ($seccion2) {
        my $param_especif_taxport = '/' . $seccion2
                                  . '/' . $tema2
                                  . '/' . $subtema2;

        &call_taxports_regen($rutaScript, "$filtro_fid$param_especif_taxport") if ($CONFIG_POSTING{'_regen_taxport'} eq 'S');
        &call_list_regen($rutaScript, "$fid$param_especif_taxport") if ($CONFIG_POSTING{'_regen_list'} eq 'S');
    };

    if ($seccion3) {
        my $param_especif_taxport = '/' . $seccion3
                                  . '/' . $tema3
                                  . '/' . $subtema3;

        &call_taxports_regen($rutaScript, "$filtro_fid$param_especif_taxport") if ($CONFIG_POSTING{'_regen_taxport'} eq 'S');
        &call_list_regen($rutaScript, "$fid$param_especif_taxport") if ($CONFIG_POSTING{'_regen_list'} eq 'S');
    };

    if (!($seccion1 || $seccion3 || $seccion3)) {
        my $param_especif_taxport = $fid . '///';
        &call_list_regen($rutaScript, $param_especif_taxport) if ($CONFIG_POSTING{'_regen_list'} eq 'S');
    };

    # Regenerar tagonomicas
    if ($tags_id && $CONFIG_POSTING{'_regen_tagport'} eq 'S') {
        $tags_id =~ s/\,/\//g;
        my $param_especif_tagonomicas = $tags_id;
        $param_especif_tagonomicas .= " $filtro_fid" if ($filtro_fid);
        &call_tagonomicas_regen($rutaScript, $param_especif_tagonomicas);
    };

};
# ---------------------------------------------------------------
sub call_taxports_regen {
    my $rutaScript = shift;
    my $param_especif_taxport = shift;

    my $pathnice = &lib_prontus::get_path_nice();
    $pathnice = "$pathnice -n19 " if ($pathnice);
    my $cmd = "$pathnice $rutaScript/prontus_cron_taxport.cgi $prontus_varglb::PRONTUS_ID $param_especif_taxport >/dev/null 2>&1 &";

    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};
# ---------------------------------------------------------------
sub call_list_regen {
    my $rutaScript = shift;
    my $param_especif_list = shift;
    return if ($prontus_varglb::LIST_PROCESO_INTERNO ne 'SI');
    my $pathnice = &lib_prontus::get_path_nice();
    $pathnice = "$pathnice -n19 " if($pathnice);
    my $cmd = "$pathnice $rutaScript/prontus_cron_list.cgi $prontus_varglb::PRONTUS_ID $param_especif_list >/dev/null 2>&1 &";

    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};
# ---------------------------------------------------------------
sub call_tagonomicas_regen {
    my $rutaScript = shift;
    my $param_especif_tagonomicas = shift;
    my $pathnice = &lib_prontus::get_path_nice();
    $pathnice = "$pathnice -n19 " if($pathnice);
    my $cmd = "$pathnice $rutaScript/prontus_tags_ports.cgi $prontus_varglb::PRONTUS_ID $param_especif_tagonomicas >/dev/null 2>&1 &";

    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
};
# ---------------------------------------------------------------
sub call_clustering {
    my $rutaScript = shift;
    my $fullpath_artic = shift;

    if (keys(%prontus_varglb::CLUSTERING_SERVER) > 0) {
        print STDERR $rutaScript . "/prontus_cluster_artic.cgi $fullpath_artic &\n";
        system $rutaScript . "/prontus_cluster_artic.cgi $fullpath_artic >/dev/null 2>&1 &";
    };
};
# -------------------------------END SCRIPT----------------------

