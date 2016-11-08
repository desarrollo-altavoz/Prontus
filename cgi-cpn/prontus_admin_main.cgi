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
# Listar directorios relativos a la raiz del publicador para permitir la edicion de los archivos relacionados con este.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Genera el link para que se invoque a /cgi-cpn/prontus_edit_file.exe para editar el archivo clickeado.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde el web sin parametros o pasando por parametro el dir., relativo a la raiz del publicador, que se quiere examinar.
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# <dir_publicador>/cpan/core/prontus_edit/prontus_edit_arbol.html
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
# NO
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 01_00  - 03/04/2002 - Primera Version.
# 1.1 - 03/05/2002 - Soporte para editar xml y xsl
# 1.2 - 06/05/2002 - Siu el usr. no es admin, tira un &nbsp;, para que no se repita el msg. de error junto con el de prontus_edit_file.exe
# ---------------------------------------------------------------
# Revision Prontus 8.0 - ych - 23/05/2002
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);

    $pathLibsProntus = $Bin . "/coment";
    unshift(@INC, $pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use glib_cgi_04;
use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_prontus;

use lib_search;

use coment_varglb;
use lib_coment;
use lib_tax;

use strict;

my (%FORM);
my $REL_DIR_LOGS = '/cpan/log';
my $DB;

main: {
  # Rescatar parametros recibidos
  &glib_cgi_04::new();
  $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');

  $FORM{'tab'} = &glib_cgi_04::param('tab');

  # Deduce path conf del referer, en caso de no ser suministrado.
  $FORM{'path_conf'} = &get_path_conf() if ($FORM{'path_conf'} eq '');

  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

  # Carga variables de configuracion.
  &lib_prontus::load_config($FORM{'path_conf'});
  $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

  ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);
  # Acceso permitido solo para admin
  if ($prontus_varglb::USERS_PERFIL ne 'A') {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Acceso a Area Restringida","La funcionalidad requerida est� disponible s�lo para el administrador del sistema");
    exit;
  };

  my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
  if (! ref($base)) {
    &glib_html_02::print_pag_result("Error","$msg_err_bd");
    exit;
  };

  $DB = $base;

  print "Content-Type: text/html\n\n";
  # Generar pagina final (loopeando una fila modelo)
  my $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/prontus_admin_main.html";
  my $pagina = &glib_fildir_02::read_file($plantilla);

  $pagina = &lib_prontus::set_coreplt_ppal($pagina);

  # Se parsean variables
  $pagina =~ s/%%_path_conf%%/$FORM{'path_conf'}/sg;
  $pagina =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/ig;

  if ($FORM{'tab'} ne '') {
    if ($FORM{'tab'} =~ /^cfg\-tab(\d+)$/) {
        $pagina =~ s/%%default_tab%%/$FORM{'tab'}/sg;
    } else {
        $pagina =~ s/%%default_tab%%//sg;
    };
  } else {
      $pagina =~ s/%%default_tab%%//sg;
  };

  # Random para tax4fids.
  my $str_random_tax = &glib_str_02::random_string(10);
  $pagina =~ s/%%str_random_tax%%/$str_random_tax/sg;

  # Se parsean los logs de operacion
  $pagina = &parseaLogs($pagina);

  # Se parsean los crons del crontab
  $pagina = &parseaCrontab($pagina);

  # Se parsean las vars de configuracion.
  $pagina = &parseaVars($pagina);

  # Se parsean las marcas para la configuracion avanzada de la regeneracion de articulos
  $pagina = &parseRegen($pagina);

  # se esconde el link de Actualizacion masiva si no existe
  unless(-f ($prontus_varglb::DIR_SERVER.'/'.$prontus_varglb::PRONTUS_ID.'/cpan/procs/prontus_art_regen_log.html')) {
    $pagina =~ s/<!--link_last_proc-->.*?<!--\/link_last_proc-->//gs;
  };

  # Se parsea el tab custom en caso de existir.
  $pagina = &parseCustom($pagina);

  print $pagina;


};

# ------------------------------------------------------------------------------
sub parseCustom {
    my $pagina = $_[0];
    # Tab custom en pesta�a Administraci�n.
    # Se puede utilizar para integrar sistemas externos a prontus.
    my $plantilla_custom = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CPAN . "/custom/admin_custom.html";

    if (-f $plantilla_custom) {
        my $pagina_custom = &glib_fildir_02::read_file($plantilla_custom);
        my $custom_tab_name = "Custom";
        my $custom_css;
        my $custom_js;

        while ($pagina_custom =~ /<!--\s*CONFIG\s*(\w+)\s*=\s*(.*?)\s*-->/sg) {
            my $name = $1;
            my $value = $2;

            if ($name eq 'TAB_NAME') {
                $custom_tab_name = $2;
            };

            if ($name eq 'CSS') {
                my @csslist = split(',', $value);
                foreach my $cssname (@csslist) {
                    $cssname =~ s/\s*//sg;
                    $custom_css .= '<link type="text/css" rel="stylesheet" href="/' . $prontus_varglb::PRONTUS_ID . '/cpan/custom/css/' . $cssname . '" />';
                    $custom_css .= "\n";
                };
            };

            if ($name eq 'JS') {
                my @jslist = split(',', $value);
                foreach my $jsname (@jslist) {
                    $jsname =~ s/\s*//sg;
                    $custom_js .= '<script type="text/javascript" src="/' . $prontus_varglb::PRONTUS_ID . '/cpan/custom/js-local/' . $jsname . '"></script>';
                    $custom_js .= "\n";
                };
            };
        };

        # Quitar variables de configuraci�n.
        $pagina_custom =~ s/<!--\s*CONFIG\s*(\w+)\s*=\s*(.*?)\s*-->//sg;

        $pagina_custom =~ s/%%_path_conf%%/$FORM{'path_conf'}/sg;
        $pagina_custom =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/ig;
        $pagina_custom =~ s/%%_public_server_name%%/$prontus_varglb::PUBLIC_SERVER_NAME/ig;

        $pagina =~ s/%%custom_tab_name%%/$custom_tab_name/sg;
        $pagina =~ s/%%CUSTOM%%/$pagina_custom/sg;
        $pagina =~ s/%%CUSTOM_CSS%%/$custom_css/sg;
        $pagina =~ s/%%CUSTOM_JS%%/$custom_js/sg;

    } else {
        $pagina =~ s/<!--custom-->.*?<!--\/custom-->//gs;
    };

    return $pagina;
};

# ------------------------------------------------------------------------------
sub parseaLogs {

  my ($pagina) = $_[0];
  my $dir_logs = '/'.$prontus_varglb::PRONTUS_ID.$REL_DIR_LOGS;

  # se renombran los .htaccess antiguos que pudieran existir
  if(-f $prontus_varglb::DIR_SERVER . $dir_logs . '/.htaccess') {
    rename($prontus_varglb::DIR_SERVER . $dir_logs . '/.htaccess', $prontus_varglb::DIR_SERVER . $dir_logs . '/_htaccess');
  }

  $pagina =~ s/%%path_logs%%/$dir_logs/;
  $pagina =~ /<!--loop_logs-->(.*?)<!--\/loop_logs-->/s;
  my $buffer = $1;
  my $buffer_total;
  &glib_fildir_02::check_dir($prontus_varglb::DIR_SERVER . $dir_logs);
  my @dirs = &glib_fildir_02::lee_dir($prontus_varglb::DIR_SERVER . $dir_logs);
  my $actual_year = '';
  foreach my $item (reverse sort @dirs) {
    next unless(-f ($prontus_varglb::DIR_SERVER.$dir_logs.'/'.$item));
    if($item =~ /(\d{4})\d{4}\.txt$/) {
      my $thisyear = $1;
      if($actual_year ne $thisyear) {
        $buffer_total = $buffer_total . '<div class="titu-year">' . $thisyear . '</div>';
        $actual_year = $thisyear;
      };
      my $buffer_temp = $buffer;
      $buffer_temp =~ s/%%link_log%%/$dir_logs\/$item/g;
      $buffer_temp =~ s/%%nombre_log%%/$item/g;
      $buffer_total = $buffer_total . $buffer_temp;
    };
  };
  if($#dirs >= 0) {
    $pagina =~ s/<!--loop_logs-->.*?<!--\/loop_logs-->/$buffer_total/s;
  } else {
    $pagina =~ s/<!--loop_logs-->.*?<!--\/loop_logs-->/No se registran logs/s;
  };
  return $pagina;
};

# ------------------------------------------------------------------------------
sub parseaCrontab {

  my ($pagina) = $_[0];
  $pagina =~ /<!--loop_crons-->(.*?)<!--\/loop_crons-->/s;

  my $loop = $1;
  my $loop_total;
  my $loop_temp;

  my $cron_buffer = `crontab -l`;

  my @cron_lines = split(/\n+/, $cron_buffer);
  my $lines = 0;
  foreach my $line (@cron_lines) {
    $loop_temp = $loop;
    next if (($line !~ /\w/) || ($line =~ /^#/) || ($line !~ /prontus/));
    $line =~ s/\/usr\/bin\/perl//isg;
    $line =~ s/\/usr\/local\/bin\/php//isg;
    $line =~ s/\/[\w\.\-_\/]+\///isg;
    $line =~ s/ +/ /isg;
    # para cuando se quiere imprimir una linea nomas
    $loop_temp =~ s/%%line%%/$line/isg;
    # para cuando se quiere imprimir por parte (6 columnas)
    $line =~ /^([\S]+)\s([\S]+)\s([\S]+)\s([\S]+)\s([\S]+)\s(.*?)$/isg;
    my ($col1, $col2, $col3, $col4, $col5, $col6) = ($1, $2, $3, $4, $5, $6);
    $loop_temp =~ s/%%col1%%/$col1/isg;
    $loop_temp =~ s/%%col2%%/$col2/isg;
    $loop_temp =~ s/%%col3%%/$col3/isg;
    $loop_temp =~ s/%%col4%%/$col4/isg;
    $loop_temp =~ s/%%col5%%/$col5/isg;
    $loop_temp =~ s/%%col6%%/$col6/isg;
    $loop_total = $loop_total . $loop_temp;
    $lines++;
  };
  if (!$lines) {
    $pagina =~ s/<!--loop_crons-->.*?<!--\/loop_crons-->//sig;
    $pagina =~ s/<!--no_crons-->(.*?)<!--\/no_crons-->/\1/sig;
  } else {
    $pagina =~ s/<!--loop_crons-->.*?<!--\/loop_crons-->/$loop_total/sig;
    $pagina =~ s/<!--no_crons-->(.*?)<!--\/no_crons-->//sig;
  };
  return $pagina;
};

sub parseaVars {
    my ($pagina) = $_[0];

    my ($loop, $buffer, $temp);

    # -id.cfg
    if ($prontus_varglb::RELDIR_BASE eq '') {
        $pagina =~ s/%%RELDIR_BASE%%/\//ig;
    } else {
        $pagina =~ s/%%RELDIR_BASE%%/$prontus_varglb::RELDIR_BASE/ig;
    };

    my %PORTS_TO_ORDER;
    foreach my $key (sort {$a cmp $b} keys %prontus_varglb::PORT_PLTS) {
        my $name = $key;
        $name =  $prontus_varglb::PORT_PLTS_NOM{$key} if ($prontus_varglb::PORT_PLTS_NOM{$key} ne '');
        next if ($key =~ /^\./);
        $name =~ s/^\s+//;
        $name =~ s/\s+$//;
        if ($name =~ /(.*?)\.(.*?)$/i) {
            $name =~ s/\.$2//ig;
        };

        $PORTS_TO_ORDER{$key} = $name;
    };

    # -------------------------------------------------------------------------------
    # -cache.cfg

    if ($prontus_varglb::CACHE_PURGE_TAXPORT eq 'SI') {
        $pagina =~ s/%%CACHE_PURGE_TAXPORT_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%CACHE_PURGE_TAXPORT_NO%%//ig;
    } else {
        $pagina =~ s/%%CACHE_PURGE_TAXPORT_SI%%//ig;
        $pagina =~ s/%%CACHE_PURGE_TAXPORT_NO%%/ checked="checked"/ig;
    }

    if ($prontus_varglb::CACHE_PURGE_TAGPORT eq 'SI') {
        $pagina =~ s/%%CACHE_PURGE_TAGPORT_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%CACHE_PURGE_TAGPORT_NO%%//ig;
    } else {
        $pagina =~ s/%%CACHE_PURGE_TAGPORT_SI%%//ig;
        $pagina =~ s/%%CACHE_PURGE_TAGPORT_NO%%/ checked="checked"/ig;
    }

    if ($prontus_varglb::CACHE_PURGE_TAXPORT_MV eq 'SI') {
        $pagina =~ s/%%CACHE_PURGE_TAXPORT_MV_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%CACHE_PURGE_TAXPORT_MV_NO%%//ig;
    } else {
        $pagina =~ s/%%CACHE_PURGE_TAXPORT_MV_SI%%//ig;
        $pagina =~ s/%%CACHE_PURGE_TAXPORT_MV_NO%%/ checked="checked"/ig;
    }

    if ($prontus_varglb::CACHE_PURGE_TAGPORT_MV eq 'SI') {
        $pagina =~ s/%%CACHE_PURGE_TAGPORT_MV_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%CACHE_PURGE_TAGPORT_MV_NO%%//ig;
    } else {
        $pagina =~ s/%%CACHE_PURGE_TAGPORT_MV_SI%%//ig;
        $pagina =~ s/%%CACHE_PURGE_TAGPORT_MV_NO%%/ checked="checked"/ig;
    }

    if ($prontus_varglb::CACHE_PURGE_MAPA eq 'SI') {
        $pagina =~ s/%%CACHE_PURGE_MAPA_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%CACHE_PURGE_MAPA_NO%%//ig;
    } else {
        $pagina =~ s/%%CACHE_PURGE_MAPA_SI%%//ig;
        $pagina =~ s/%%CACHE_PURGE_MAPA_NO%%/ checked="checked"/ig;
    }

    if ($prontus_varglb::CACHE_PURGE_ART_RELAC eq 'SI') {
        $pagina =~ s/%%CACHE_PURGE_ART_RELAC_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%CACHE_PURGE_ART_RELAC_NO%%//ig;
    } else {
        $pagina =~ s/%%CACHE_PURGE_ART_RELAC_SI%%//ig;
        $pagina =~ s/%%CACHE_PURGE_ART_RELAC_NO%%/ checked="checked"/ig;
    }

    $buffer = '';
    $pagina =~ /<!--loop_cache_purge_fid-->(.*?)<!--\/loop_cache_purge_fid-->/s;
    $loop = $1;
    my $cont = 1;

    foreach my $fid (sort keys %prontus_varglb::FORM_PLTS) {
      $temp = $loop;
      my @fid_info = split(/:/, $fid);

      $temp =~ s/%%archivofid%%/$fid_info[0]/isg;
      $temp =~ s/%%nombrefid%%/$fid_info[1]/isg;
      $temp =~ s/%%num%%/$cont/isg;

      if (defined $prontus_varglb::CACHE_PURGE_EXCLUDE_FID{$fid_info[0]}) {
        $temp =~ s/%%checked%%/ checked="checked"/isg;
      } else {
        $temp =~ s/%%checked%%//isg;
      }

      $buffer = $buffer . $temp;
      $cont++;
    };

    $pagina =~ s/<!--loop_cache_purge_fid-->.*?<!--\/loop_cache_purge_fid-->/$buffer/sig;

    # -------------------------------------------------------------------------------
    # -art.cfg

    # Lee directorio de plantillas de art�culo.
    my $dir_plt = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/plantillas/artic/fecha/pags/';
    &glib_fildir_02::check_dir($dir_plt);
    my @plts_listado = &glib_fildir_02::lee_dir($dir_plt);


    $buffer = '';
    $pagina =~ /<!--loop_fid_item-->(.*?)<!--\/loop_fid_item-->/s;
    $loop = $1;
    my $cont = 1;
    my $fid_default = '';

    if ($prontus_varglb::FID_DEFAULT =~ /^([\w@-]+) *: *.+/) {
        $fid_default = $1;
    };

    my %fids_utilizados;
    foreach my $fid (sort keys %prontus_varglb::FORM_PLTS) {
        $temp = $loop;

        my @fid_info = split(/:/, $fid);
        $temp =~ s/%%num%%/$cont/isg;
        $temp =~ s/%%archivofid%%/$fid_info[0]/isg;
        $temp =~ s/%%nombrefid%%/$fid_info[1]/isg;

        if ($fid_info[0] eq $fid_default) {
            my $input = '<input type="radio" name="form_plts_ini" value="' . $fid_info[0] . '" checked="checked"/>';
            $temp =~ s/%%fid_default%%/$input/isg;
        } else {
            my $input = '<input type="radio" name="form_plts_ini" value="' . $fid_info[0] . '"/>';
            $temp =~ s/%%fid_default%%/$input/isg;
        };


        $fids_utilizados{$fid_info[0].'.html'} = 1;

        my $options_select = "";
        my %options_selected;
        my $num_options_selected = 0;
        foreach my $plt_file (sort @plts_listado) {
            if ($plt_file =~ /(.*?)\.(.*?)/ && $plt_file ne '.' && $plt_file ne '..' && $plt_file !~ /^\./) {
                if ($prontus_varglb::FORM_PLTS{$fid} =~ /(^|;)$plt_file(;|$)/) {
                    $options_select .= '<option value="' . $plt_file . '" selected="selected">' . $plt_file . '</option>';
                    $options_selected{$plt_file} = 1;
                    $num_options_selected++;
                } else {
                    $options_select .= '<option value="' . $plt_file . '">' . $plt_file . '</option>';
                };
            };
        };

        if ($num_options_selected gt 1) {
            $temp =~ s/%%multiple%%/ multiple="multiple"/isg;
            $temp =~ s/%%multiple_img%%/men_of/isg;
        } else {
            $temp =~ s/%%multiple%%//isg;
            $temp =~ s/%%multiple_img%%/mas_of/isg;
        }

        $temp =~ s/%%plantillasfid%%/$options_select/isg;

        # Paralelas.
        $options_select = "";
        $num_options_selected = 0;
        foreach my $plt_file (sort @plts_listado) {
            if ($plt_file =~ /(.*?)\.(.*?)/ && $plt_file ne '.' && $plt_file ne '..' && $plt_file !~ /^\./) {
                next if ($options_selected{$plt_file});
                if ($prontus_varglb::FORM_PLTS_PARALELAS{$fid_info[0]} =~ /(^|;)$plt_file(;|$)/) {
                    $options_select .= '<option value="' . $plt_file . '" selected="selected">' . $plt_file . '</option>';
                    $num_options_selected++;
                } else {
                    $options_select .= '<option value="' . $plt_file . '">' . $plt_file . '</option>';
                };
            };
        };

        if ($num_options_selected gt 1) {
            $temp =~ s/%%multiple_pla%%/ multiple="multiple"/isg;
            $temp =~ s/%%multiple_pla__img%%/men_of/isg;
        } else {
            $temp =~ s/%%multiple_pla%%//isg;
            $temp =~ s/%%multiple_pla_img%%/mas_of/isg;
        }

        $temp =~ s/%%plantillasfid_pla%%/$options_select/isg;

        $buffer = $buffer . $temp;
        $cont++;
    };

    $pagina =~ s/%%num_ultimo_fid%%/$cont/isg;

    $pagina =~ s/<!--loop_fid_item-->.*?<!--\/loop_fid_item-->/$buffer/sig;

    # Armar select de fids, sin los fids que est�n siendo utilizados.
    $buffer = '';
    $pagina =~ /<!--loop_fids-->(.*?)<!--\/loop_fids-->/s;
    $loop = $1;

    my $dir_fid = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/cpan/fid/';
    &glib_fildir_02::check_dir($dir_fid);
    my @fids_listado = &glib_fildir_02::lee_dir($dir_fid);
    foreach my $fid_file (sort @fids_listado) {
        $temp = $loop;
        if ($fid_file =~ /fid_(.*?)\.html/) {
            my $fid_name = "fid_$1";
            if (!exists $fids_utilizados{$fid_file}) {
                $temp =~ s/%%valor%%/$fid_name/isg;
                $temp =~ s/%%nombre%%/$fid_name/isg;
                $buffer = $buffer . $temp;
            };
        };
    };
    # parsea los fids disponibles.
    $pagina =~ s/<!--loop_fids-->.*?<!--\/loop_fids-->/$buffer/sig;

    $buffer = '';
    $pagina =~ /<!--loop_plts-->(.*?)<!--\/loop_plts-->/s;
    $loop = $1;

    foreach my $plt_file (sort @plts_listado) {
        $temp = $loop;
        if ($plt_file =~ /(.*?)\.(.*?)/ && $plt_file ne '.' && $plt_file ne '..') {
            $temp =~ s/%%valor%%/$plt_file/isg;
            $temp =~ s/%%nombre%%/$plt_file/isg;
            $buffer = $buffer . $temp;
        };
    };

    $pagina =~ s/<!--loop_plts-->.*?<!--\/loop_plts-->/$buffer/sig;

    # -------------------------------------------------------------------------------
    # -bd.cfg
    if ($prontus_varglb::ADMIN_BASEDATOS eq 'SI') {
        $pagina =~ s/%%ADMIN_BASEDATOS%%/ checked="checked"/ig;
    } else {
        $pagina =~ s/%%ADMIN_BASEDATOS%%//ig;
    };

    $pagina =~ s/%%NOM_BD%%/$prontus_varglb::NOM_BD/ig;
    $pagina =~ s/%%USER_BD%%/$prontus_varglb::USER_BD/ig;
    $pagina =~ s/%%PWD_BD%%/$prontus_varglb::PWD_BD/ig;
    $pagina =~ s/%%SERVER_BD%%/$prontus_varglb::SERVER_BD/ig;

    # -------------------------------------------------------------------------------
    # -port.cfg
    if ($prontus_varglb::EDICBASE_INI_SELECTED eq 'SI') {
        $pagina =~ s/%%EDICBASE_INI_SELECTED_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%EDICBASE_INI_SELECTED_NO%%//ig;
    } else {
        $pagina =~ s/%%EDICBASE_INI_SELECTED_SI%%//ig;
        $pagina =~ s/%%EDICBASE_INI_SELECTED_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::ADMIN_PORT eq 'SI') {
        $pagina =~ s/%%ADMIN_PORT_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%ADMIN_PORT_NO%%//ig;
    } else {
        $pagina =~ s/%%ADMIN_PORT_SI%%//ig;
        $pagina =~ s/%%ADMIN_PORT_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::MULTI_EDICION eq 'SI') {
        $pagina =~ s/%%MULTIEDICION_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%MULTIEDICION_NO%%//ig;
    } else {
        $pagina =~ s/%%MULTIEDICION_SI%%//ig;
        $pagina =~ s/%%MULTIEDICION_NO%%/ checked="checked"/ig;
        $pagina =~ s/<!--multiedicion-->(.*?)<!--\/multiedicion-->//sig;
    };


    $buffer = '';
    $pagina =~ /<!--loop_portadas-->(.*?)<!--\/loop_portadas-->/s;
    $loop = $1;

    foreach my $port (sort {lc($PORTS_TO_ORDER{$a}) cmp lc($PORTS_TO_ORDER{$b})} keys %PORTS_TO_ORDER) {
        next if ($port =~ /^\./);
        my $name = $port;
        $name = $prontus_varglb::PORT_PLTS_NOM{$port} if ($prontus_varglb::PORT_PLTS_NOM{$port} ne '');
        $temp = $loop;
        $temp =~ s/%%value%%/$port/isg;
        $temp =~ s/%%name%%/$name/isg;

        if ($port eq $prontus_varglb::PORT_INI_SELECTED) {
            $temp =~ s/%%selected%%/ selected="selected"/isg;
        } else {
            $temp =~ s/%%selected%%//isg;
        };

        $buffer = $buffer . $temp;
    };

    $pagina =~ s/<!--loop_portadas-->.*?<!--\/loop_portadas-->/$buffer/sig;

    # Loop para combo de portada de inicio.
    $buffer = '';
    $pagina =~ /<!--loop_portadas_port_home-->(.*?)<!--\/loop_portadas_port_home-->/s;
    $loop = $1;


    foreach my $port (sort {lc($PORTS_TO_ORDER{$a}) cmp lc($PORTS_TO_ORDER{$b})} keys %PORTS_TO_ORDER) {
        next if ($port =~ /^\./);
        my $name = $port;
        $name = $prontus_varglb::PORT_PLTS_NOM{$port} if ($prontus_varglb::PORT_PLTS_NOM{$port} ne '');
        $temp = $loop;
        $temp =~ s/%%value%%/$port/isg;
        $temp =~ s/%%name%%/$name/isg;

        if ($port eq $prontus_varglb::PORT_HOME) {
            $temp =~ s/%%selected%%/ selected="selected"/isg;
        } else {
            $temp =~ s/%%selected%%//isg;
        };

        $buffer = $buffer . $temp;
    };

    $pagina =~ s/<!--loop_portadas_port_home-->.*?<!--\/loop_portadas_port_home-->/$buffer/sig;

    $buffer = '';
    $pagina =~ /<!--loop_port_plts-->(.*?)<!--\/loop_port_plts-->/s;
    $loop = $1;

    # Leer directorio de portadas.
    my $dir_portadas = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/plantillas/edic/nroedic/port/';
    &glib_fildir_02::check_dir($dir_portadas);
    my @ports_listado = &glib_fildir_02::lee_dir($dir_portadas);

    # Leer directorio de containers de previews.
    my $dir_preview = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/stat/preview_containers/';
    &glib_fildir_02::check_dir($dir_preview);
    my @preview_listado = &glib_fildir_02::lee_dir($dir_preview);

    # $prontus_varglb::PORT_PLTS_EXTRA{$port}
    # $prontus_varglb::PORT_PLTS_PREVIEW{$port}
    my $cont = 1;

    # Se revisan las portadas que estan siendo utilizadas
    my %ports_utilizadas;
    foreach my $port (sort keys %prontus_varglb::PORT_PLTS) {
        next if ($port =~ /^\./);
        $ports_utilizadas{$port} = 1;
        if ($prontus_varglb::PORT_PLTS_EXTRA{$port}) {
            my @arrayports = split /;/, $prontus_varglb::PORT_PLTS_EXTRA{$port};
            foreach my $port2 (@arrayports) {
                $ports_utilizadas{$port2} = 1;
            }
        }
    }
    # Se arma la combo de portadas NO utilizadas
    my $strcombo = '';
    foreach my $port_file (sort @ports_listado) {
        next if ($port_file =~ /^\./);
        if ($port_file =~ /(.*?)\.(.*?)/ && $port_file ne '.' && $port_file ne '..') {
            if($ports_utilizadas{$port_file} != 1) {
                $strcombo = $strcombo . '<option value="' . $port_file . '">' . $port_file . '</option>';
            };
        };
    };

    foreach my $port (sort keys %prontus_varglb::PORT_PLTS) {
        next if ($port =~ /^\./);
        $temp = $loop;
        my $option_select = '';
        my $num_options_selected = 0;

        # Portadas paralelas
        my @arrayalt = split /;/, $prontus_varglb::PORT_PLTS_EXTRA{$port};
        foreach my $alt (sort @arrayalt) {
            $num_options_selected++;
            $option_select = $option_select . '<option value="' . $alt . '" selected="selected">' . $alt . '</option>';
        }
        $option_select = $option_select . $strcombo;

        if ($num_options_selected gt 1) {
            $temp =~ s/%%multiple%%/ multiple="multiple"/isg;
        } else {
            $temp =~ s/%%multiple%%//isg;
        };

        # Marca para seleccionar el option "Ninguna" en caso que no haya ninguna seleccionada.
        if ($num_options_selected eq 0) {
            $temp =~ s/%%ninguna_paralela%%/ selected="selected"/isg;
        } else {
            $temp =~ s/%%ninguna_paralela%%//isg;
        };

        $temp =~ s/%%paralelas%%/$option_select/isg;

        my $option_select = '';
        my $num_options_selected = 0;

        # Portadas preview.
        foreach my $prev_file (sort @preview_listado) {
            if ($prev_file =~ /(.*?)\.(.*?)/ && $prev_file ne '.' && $prev_file ne '..') {
                if ($prontus_varglb::PORT_PLTS_PREVIEW{$port} =~ $prev_file) {
                    # Marcar option como selected.
                    $option_select = $option_select . '<option value="' . $prev_file . '" selected="selected">' . $prev_file . '</option>';
                    $num_options_selected++;
                } else {
                    $option_select = $option_select . '<option value="' . $prev_file . '">' . $prev_file . '</option>';
                };
            };
        };

        if ($num_options_selected eq 0) {
            $temp =~ s/%%ninguna_preview%%/ selected="selected"/isg;
        } else {
            $temp =~ s/%%ninguna_preview%%//isg;
        };

        $temp =~ s/%%plt_preview%%/$option_select/isg;
        $temp =~ s/%%portada%%/$port/isg;
        $temp =~ s/%%num%%/$cont/isg;

        my $name = $port;
        $name = $prontus_varglb::PORT_PLTS_NOM{$port} if ($prontus_varglb::PORT_PLTS_NOM{$port} ne '');
        $name = ($name);
        $temp =~ s/%%portada_nom%%/$name/isg;

        $buffer = $buffer . $temp;
        $cont++;
    };

    $pagina =~ s/%%num_last_port%%/$cont/sig;

    $pagina =~ s/<!--loop_port_plts-->.*?<!--\/loop_port_plts-->/$buffer/sig;

    $buffer = '';
    $pagina =~ /<!--loop_base_ports-->(.*?)<!--\/loop_base_ports-->/s;
    $loop = $1;
    my $cont = 1;

    my %baseports_utilizadas;
    foreach my $port (sort @prontus_varglb::BASE_PORTS) {
        if ($port ne '') {
            $temp = $loop;
            my $name = $port;
            $name = $prontus_varglb::PORT_PLTS_NOM{$port} if ($prontus_varglb::PORT_PLTS_NOM{$port} ne '');
            $name = ($name);
            $temp =~ s/%%name%%/$name/isg;
            $temp =~ s/%%base_ports_name%%/$name/isg;
            $temp =~ s/%%base_ports_valor%%/$port/isg;
            $temp =~ s/%%num%%/$cont/isg;
            $baseports_utilizadas{$port} = 1;
            $buffer = $buffer . $temp;
            $cont++;
        };
    };


    $pagina =~ s/<!--loop_base_ports-->.*?<!--\/loop_base_ports-->/$buffer/sig;

    # Listado de portadas, para agregar una.
    # %%listado_portadas%%
    #~ my $option_select = '';
    #~ my $option_select_paralelas = '';
    #~ my $option_select_base = '';
    #~ foreach my $port_file (sort @ports_listado) {
        #~ if ($port_file =~ /(.*?)\.(.*?)/ && $port_file ne '.' && $port_file ne '..') {
            #~ if (!exists $ports_utilizadas{$port_file}) {
                #~ $option_select = $option_select . '<option value="' . $port_file . '">' . $port_file . '</option>';
            #~ };
            #~ $option_select_paralelas = $option_select_paralelas . '<option value="' . $port_file . '">' . $port_file . '</option>';
        #~ };
    #~ };
    my $option_select_paralelas = $strcombo;
    my $option_select = $strcombo;
    my $option_select_base = '';
     foreach my $port (sort {lc($PORTS_TO_ORDER{$a}) cmp lc($PORTS_TO_ORDER{$b})} keys %PORTS_TO_ORDER) {
        my $name = $prontus_varglb::PORT_PLTS_NOM{$port} if ($prontus_varglb::PORT_PLTS_NOM{$port} ne '');
        $name = $port if ($name eq '');
        if (!exists $baseports_utilizadas{$port}) {
            $temp =~ s/%%name%%/$name/isg;
            $option_select_base = $option_select_base . '<option value="' . $port . '">' . $name . '</option>';
        };
    };

    my $option_select_prev = '';
    foreach my $prev_file (sort @preview_listado) {
        if ($prev_file =~ /(.*?)\.(.*?)/ && $prev_file ne '.' && $prev_file ne '..') {
            $option_select_prev = $option_select_prev . '<option value="' . $prev_file . '">' . $prev_file . '</option>';
        };
    };


    $pagina =~ s/%%listado_previews%%/$option_select_prev/sig;
    $pagina =~ s/%%listado_portadas%%/$option_select/sig;
    $pagina =~ s/%%listado_baseports%%/$option_select_base/sig;
    $pagina =~ s/%%listado_paralelas%%/$option_select_paralelas/sig;


    # portadas drag & drop.

    $buffer = '';
    $pagina =~ /<!--loop_ports_dragnadndrop-->(.*?)<!--\/loop_ports_dragnadndrop-->/s;
    $loop = $1;
    my $cont = 1;

    my %portdd_habilitadas;
    foreach my $port (keys (%prontus_varglb::PORT_DRAGANDROP)) {
        if ($port ne '') {
            $temp = $loop;
            my $name = $port;
            $name = $prontus_varglb::PORT_PLTS_NOM{$port} if ($prontus_varglb::PORT_PLTS_NOM{$port} ne '');
            $name = ($name);
            $temp =~ s/%%port_name%%/$name/isg;
            $temp =~ s/%%port_valor%%/$port/isg;
            $temp =~ s/%%num%%/$cont/isg;
            $portdd_habilitadas{$port} = 1;
            $buffer = $buffer . $temp;
            $cont++;
        };
    };


    $pagina =~ s/<!--loop_ports_dragnadndrop-->.*?<!--\/loop_ports_dragnadndrop-->/$buffer/sig;

    $buffer = '';
    $pagina =~ /<!--loop_portadas_dd-->(.*?)<!--\/loop_portadas_dd-->/s;
    $loop = $1;

    foreach my $port (sort {lc($PORTS_TO_ORDER{$a}) cmp lc($PORTS_TO_ORDER{$b})} keys %PORTS_TO_ORDER) {
        my $name = '';
        $name = $prontus_varglb::PORT_PLTS_NOM{$port} if ($prontus_varglb::PORT_PLTS_NOM{$port} ne '');
        next if ($port =~ /^\./);
        next if ($portdd_habilitadas{$port});
        $name = $port if ($name eq '');
        $temp = $loop;
        $temp =~ s/%%value%%/$port/isg;
        $temp =~ s/%%name%%/$name/isg;

        $buffer = $buffer . $temp;
    };

    $pagina =~ s/<!--loop_portadas_dd-->.*?<!--\/loop_portadas_dd-->/$buffer/sig;

    # -------------------------------------------------------------------------------
    # -usr.cfg
    if ($prontus_varglb::PERIODISTA_VER_ARTICULOS_AJENOS eq 'SI') {
        $pagina =~ s/%%REDACTOR_VER_ARTICULOS_AJENOS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%REDACTOR_VER_ARTICULOS_AJENOS_NO%%//ig;
    } else {
        $pagina =~ s/%%REDACTOR_VER_ARTICULOS_AJENOS_SI%%//ig;
        $pagina =~ s/%%REDACTOR_VER_ARTICULOS_AJENOS_NO%%/ checked="checked"/ig;
    };
    if ($prontus_varglb::PERIODISTA_EDITAR_ARTICULOS_AJENOS eq 'SI') {
        $pagina =~ s/%%REDACTOR_EDITAR_ARTICULOS_AJENOS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%REDACTOR_EDITAR_ARTICULOS_AJENOS_NO%%//ig;
    } else {
        $pagina =~ s/%%REDACTOR_EDITAR_ARTICULOS_AJENOS_SI%%//ig;
        $pagina =~ s/%%REDACTOR_EDITAR_ARTICULOS_AJENOS_NO%%/ checked="checked"/ig;
    };
    if ($prontus_varglb::EDITOR_VER_ARTICULOS_AJENOS eq 'SI') {
        $pagina =~ s/%%EDITOR_VER_ARTICULOS_AJENOS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%EDITOR_VER_ARTICULOS_AJENOS_NO%%//ig;
    } else {
        $pagina =~ s/%%EDITOR_VER_ARTICULOS_AJENOS_SI%%//ig;
        $pagina =~ s/%%EDITOR_VER_ARTICULOS_AJENOS_NO%%/checked="checked"/ig;
    };
    if ($prontus_varglb::EDITOR_EDITAR_ARTICULOS_AJENOS eq 'SI') {
        $pagina =~ s/%%EDITOR_EDITAR_ARTICULOS_AJENOS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%EDITOR_EDITAR_ARTICULOS_AJENOS_NO%%//ig;
    } else {
        $pagina =~ s/%%EDITOR_EDITAR_ARTICULOS_AJENOS_SI%%//ig;
        $pagina =~ s/%%EDITOR_EDITAR_ARTICULOS_AJENOS_NO%%/ checked="checked"/ig;
    };
    if ($prontus_varglb::EDITOR_ADMINISTRAR_EDICIONES eq 'SI') {
        $pagina =~ s/%%EDITOR_ADMINISTRAR_EDICIONES_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%EDITOR_ADMINISTRAR_EDICIONES_NO%%//ig;
    } else {
        $pagina =~ s/%%EDITOR_ADMINISTRAR_EDICIONES_SI%%//ig;
        $pagina =~ s/%%EDITOR_ADMINISTRAR_EDICIONES_NO%%/ checked="checked"/ig;
    };

    # -tax.cfg
    if ($prontus_varglb::TAXONOMIA_NIVELES eq '0') {
        $pagina =~ s/%%TAXONOMIA_NIVELES_0%%/ selected="selected"/ig;
    } else {
        $pagina =~ s/%%TAXONOMIA_NIVELES_0%%//ig;
    };
    if ($prontus_varglb::TAXONOMIA_NIVELES eq '1') {
        $pagina =~ s/%%TAXONOMIA_NIVELES_1%%/ selected="selected"/ig;
    } else {
        $pagina =~ s/%%TAXONOMIA_NIVELES_1%%//ig;
    };
    if ($prontus_varglb::TAXONOMIA_NIVELES eq '2') {
        $pagina =~ s/%%TAXONOMIA_NIVELES_2%%/ selected="selected"/ig;
    } else {
        $pagina =~ s/%%TAXONOMIA_NIVELES_2%%//ig;
    };
    if ($prontus_varglb::TAXONOMIA_NIVELES eq '3') {
        $pagina =~ s/%%TAXONOMIA_NIVELES_3%%/ selected="selected"/ig;
    } else {
        $pagina =~ s/%%TAXONOMIA_NIVELES_3%%//ig;
    };
    $pagina =~ s/%%TAXONOMIA_NIVELES%%/$prontus_varglb::TAXONOMIA_NIVELES/ig;

    $pagina =~ s/%%NUM_RELAC_DEFAULT%%/$prontus_varglb::NUM_RELAC_DEFAULT/ig;
    $pagina =~ s/%%TAXPORT_ARTXPAG%%/$prontus_varglb::TAXPORT_ARTXPAG/ig;
    #~ $pagina =~ s/%%TAXPORT_REFRESH_SEGS%%/$prontus_varglb::TAXPORT_REFRESH_SEGS/ig;
    $pagina =~ s/%%TAXPORT_MAXARTICS%%/$prontus_varglb::TAXPORT_MAXARTICS/ig;
    $pagina =~ s/%%TAXPORT_MAX_WORKERS%%/$prontus_varglb::TAXPORT_MAX_WORKERS/ig;

    my $txport_orden = $prontus_varglb::TAXPORT_ORDEN;
    my $direccion = '';

    if ($txport_orden =~ /ART_FECHAP (DESC|ASC), ART_HORAP (DESC|ASC)/i) {
        $direccion = $1;
        $pagina =~ s/%%TAXPORT_ORDEN_TIT%%//ig;
        $pagina =~ s/%%TAXPORT_ORDEN_CRE%%//ig;
        $pagina =~ s/%%TAXPORT_ORDEN_PUB%%/ selected="selected"/ig;
    } elsif ($txport_orden =~ /ART_TITU (DESC|ASC)/i) {
        $direccion = $1;
        $pagina =~ s/%%TAXPORT_ORDEN_TIT%%/ selected="selected"/ig;
        $pagina =~ s/%%TAXPORT_ORDEN_CRE%%//ig;
        $pagina =~ s/%%TAXPORT_ORDEN_PUB%%//ig;
    } elsif ($txport_orden =~ /ART_AUTOINC (DESC|ASC)/i) {
        $direccion = $1;
        $pagina =~ s/%%TAXPORT_ORDEN_TIT%%//ig;
        $pagina =~ s/%%TAXPORT_ORDEN_CRE%%/ selected="selected"/ig;
        $pagina =~ s/%%TAXPORT_ORDEN_PUB%%//ig;
    } else {
        $pagina =~ s/%%TAXPORT_ORDEN_TIT%%//ig;
        $pagina =~ s/%%TAXPORT_ORDEN_CRE%%//ig;
        $pagina =~ s/%%TAXPORT_ORDEN_PUB%%//ig;
    };

    $direccion = lc($direccion);

    if ($direccion eq 'desc') {
        $pagina =~ s/%%TAXPORT_ORDEN_DESC%%/ selected="selected"/ig;
        $pagina =~ s/%%TAXPORT_ORDEN_ASC%%//ig;
    } elsif ($direccion eq 'asc') {
        $pagina =~ s/%%TAXPORT_ORDEN_DESC%%//ig;
        $pagina =~ s/%%TAXPORT_ORDEN_ASC%%/ selected="selected"/ig;
    } else {
        $pagina =~ s/%%TAXPORT_ORDEN_DESC%%//ig;
        $pagina =~ s/%%TAXPORT_ORDEN_ASC%%//ig;
    };

    if ($prontus_varglb::TAXPORT_TIPO_PAGINACION eq '0') {
        $pagina =~ s/%%TAXPORT_TIPO_PAGINACION_V0%%/ checked="checked"/ig;
        $pagina =~ s/%%TAXPORT_TIPO_PAGINACION_V1%%//ig;
    } else {
        $pagina =~ s/%%TAXPORT_TIPO_PAGINACION_V0%%//ig;
        $pagina =~ s/%%TAXPORT_TIPO_PAGINACION_V1%%/ checked="checked"/ig;
    };

    $pagina =~ s/%%TAXPORT_PAGCORTA_MAXPAGS%%/$prontus_varglb::TAXPORT_PAGCORTA_MAXPAGS/ig;

    #~ if ($prontus_varglb::TAXPORT_REFRESH eq 'SI') {
        #~ $pagina =~ s/%%TAXPORT_REFRESH_SI%%/ checked="checked"/ig;
        #~ $pagina =~ s/%%TAXPORT_REFRESH_NO%%//ig;
    #~ } else {
        #~ $pagina =~ s/%%TAXPORT_REFRESH_SI%%//ig;
        #~ $pagina =~ s/%%TAXPORT_REFRESH_NO%%/ checked="checked"/ig;
    #~ };

    # -tag.cfg

    $pagina =~ s/%%TAGPORT_ARTXPAG%%/$prontus_varglb::TAGPORT_ARTXPAG/ig;
    $pagina =~ s/%%TAGPORT_MAXARTICS%%/$prontus_varglb::TAGPORT_MAXARTICS/ig;
    $pagina =~ s/%%MAX_LAST_TAGS_4FID%%/$prontus_varglb::MAX_LAST_TAGS_4FID/ig;
    my $tgport_orden = $prontus_varglb::TAGPORT_ORDEN;
    my $direccion = '';

    if ($tgport_orden =~ /ART_FECHAP (DESC|ASC), ART_HORAP (DESC|ASC)/i) {
        $direccion = $1;
        $pagina =~ s/%%TAGPORT_ORDEN_TIT%%//ig;
        $pagina =~ s/%%TAGPORT_ORDEN_CRE%%//ig;
        $pagina =~ s/%%TAGPORT_ORDEN_PUB%%/ selected="selected"/ig;
    } elsif ($tgport_orden =~ /ART_TITU (DESC|ASC)/i) {
        $direccion = $1;
        $pagina =~ s/%%TAGPORT_ORDEN_TIT%%/ selected="selected"/ig;
        $pagina =~ s/%%TAGPORT_ORDEN_CRE%%//ig;
        $pagina =~ s/%%TAGPORT_ORDEN_PUB%%//ig;
    } elsif ($tgport_orden =~ /ART_AUTOINC (DESC|ASC)/i) {
        $direccion = $1;
        $pagina =~ s/%%TAGPORT_ORDEN_TIT%%//ig;
        $pagina =~ s/%%TAGPORT_ORDEN_CRE%%/ selected="selected"/ig;
        $pagina =~ s/%%TAGPORT_ORDEN_PUB%%//ig;
    } else {
        $pagina =~ s/%%TAGPORT_ORDEN_TIT%%//ig;
        $pagina =~ s/%%TAGPORT_ORDEN_CRE%%//ig;
        $pagina =~ s/%%TAGPORT_ORDEN_PUB%%//ig;
    };

    $direccion = lc($direccion);

    if ($direccion eq 'desc') {
        $pagina =~ s/%%TAGPORT_ORDEN_DESC%%/ selected="selected"/ig;
        $pagina =~ s/%%TAGPORT_ORDEN_ASC%%//ig;
    } elsif ($direccion eq 'asc') {
        $pagina =~ s/%%TAGPORT_ORDEN_DESC%%//ig;
        $pagina =~ s/%%TAGPORT_ORDEN_ASC%%/ selected="selected"/ig;
    } else {
        $pagina =~ s/%%TAGPORT_ORDEN_DESC%%//ig;
        $pagina =~ s/%%TAGPORT_ORDEN_ASC%%//ig;
    };


    # -list.cfg
    if ($prontus_varglb::LIST_PROCESO_INTERNO eq 'SI') {
        $pagina =~ s/%%LIST_PROCESO_INTERNO_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%LIST_PROCESO_INTERNO_NO%%//ig;
    } else {
        $pagina =~ s/%%LIST_PROCESO_INTERNO_SI%%//ig;
        $pagina =~ s/%%LIST_PROCESO_INTERNO_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::LIST_PORT_PPROC eq 'SI') {
        $pagina =~ s/%%LIST_PORT_PPROC_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%LIST_PORT_PPROC_NO%%//ig;
    } else {
        $pagina =~ s/%%LIST_PORT_PPROC_SI%%//ig;
        $pagina =~ s/%%LIST_PORT_PPROC_NO%%/ checked="checked"/ig;
    };

    $pagina =~ s/%%LIST_MAXARTICS%%/$prontus_varglb::LIST_MAXARTICS/ig;
    #~ $pagina =~ s/%%LIST_ARTXPAG%%/$prontus_varglb::LIST_ARTXPAG/ig;
    my $list_orden = $prontus_varglb::LIST_ORDEN;
    my $direccion2 = '';
    if ($list_orden =~ /ART_FECHAP (DESC|ASC), ART_HORAP (DESC|ASC)/i) {
        $direccion2 = $1;
        $pagina =~ s/%%LIST_ORDEN_TIT%%//ig;
        $pagina =~ s/%%LIST_ORDEN_CRE%%//ig;
        $pagina =~ s/%%LIST_ORDEN_PUB%%/ selected="selected"/ig;
    } elsif ($list_orden =~ /ART_TITU (DESC|ASC)/i) {
        $direccion2 = $1;
        $pagina =~ s/%%LIST_ORDEN_TIT%%/ selected="selected"/ig;
        $pagina =~ s/%%LIST_ORDEN_CRE%%//ig;
        $pagina =~ s/%%LIST_ORDEN_PUB%%//ig;
    } elsif ($list_orden =~ /ART_AUTOINC (DESC|ASC)/i) {
        $direccion2 = $1;
        $pagina =~ s/%%LIST_ORDEN_TIT%%//ig;
        $pagina =~ s/%%LIST_ORDEN_CRE%%/ selected="selected"/ig;
        $pagina =~ s/%%LIST_ORDEN_PUB%%//ig;
    } else {
        $pagina =~ s/%%LIST_ORDEN_TIT%%//ig;
        $pagina =~ s/%%LIST_ORDEN_CRE%%//ig;
        $pagina =~ s/%%LIST_ORDEN_PUB%%//ig;
    };

    $direccion2 = lc($direccion2);

    if ($direccion2 eq 'desc') {
        $pagina =~ s/%%LIST_ORDEN_DESC%%/ selected="selected"/ig;
        $pagina =~ s/%%LIST_ORDEN_ASC%%//ig;
    } elsif ($direccion2 eq 'asc') {
        $pagina =~ s/%%LIST_ORDEN_DESC%%//ig;
        $pagina =~ s/%%LIST_ORDEN_ASC%%/ selected="selected"/ig;
    } else {
        $pagina =~ s/%%LIST_ORDEN_DESC%%//ig;
        $pagina =~ s/%%LIST_ORDEN_ASC%%//ig;
    };

    # -var.cfg
    if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
        $pagina =~ s/%%CONTROL_FECHA_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%CONTROL_FECHA_NO%%//ig;
    } else {
        $pagina =~ s/%%CONTROL_FECHA_SI%%//ig;
        $pagina =~ s/%%CONTROL_FECHA_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS eq 'SI') {
        $pagina =~ s/%%CONTROLAR_ALTA_ARTICULOS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%CONTROLAR_ALTA_ARTICULOS_NO%%//ig;
    } else {
        $pagina =~ s/%%CONTROLAR_ALTA_ARTICULOS_SI%%//ig;
        $pagina =~ s/%%CONTROLAR_ALTA_ARTICULOS_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::ACTUALIZACIONES eq 'SI') {
        $pagina =~ s/%%ACTUALIZACIONES_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%ACTUALIZACIONES_NO%%//ig;
    } else {
        $pagina =~ s/%%ACTUALIZACIONES_SI%%//ig;
        $pagina =~ s/%%ACTUALIZACIONES_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::ACTUALIZACION_MASIVA eq 'SI') {
        $pagina =~ s/%%ACTUALIZACION_MASIVA%%/ checked="checked"/ig;
    } else {
        $pagina =~ s/%%ACTUALIZACION_MASIVA%%//ig;
    };

    if ($prontus_varglb::COMENTARIOS eq 'SI') {
        $pagina =~ s/%%COMENTARIOS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%COMENTARIOS_NO%%//ig;
    } else {
        $pagina =~ s/%%COMENTARIOS_SI%%//ig;
        $pagina =~ s/%%COMENTARIOS_NO%%/ checked="checked"/ig;
        $pagina =~ s/<!--comentarios-->(.*?)<!--\/comentarios-->//sig;
    };

    if ($prontus_varglb::DROPBOX eq 'SI') {
        $pagina =~ s/%%DROPBOX_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%DROPBOX_NO%%//ig;
    } else {
        $pagina =~ s/%%DROPBOX_SI%%//ig;
        $pagina =~ s/%%DROPBOX_NO%%/ checked="checked"/ig;
        $pagina =~ s/<!--dropbox-->(.*?)<!--\/dropbox-->//sig;
    };

    $buffer = '';
    $temp = '';
    $loop = '';
    $pagina =~ /<!--loop_dropbox_customdir-->(.*?)<!--\/loop_dropbox_customdir-->/s;
    $loop = $1;

    foreach my $customdir (keys %prontus_varglb::DROPBOX_CUSTOM_DIR) {
        $temp = $loop;
        $temp =~ s/%%customdir%%/$customdir/isg;
        $buffer = $buffer . $temp;
    };

    $pagina =~ s/<!--loop_dropbox_customdir-->.*?<!--\/loop_dropbox_customdir-->/$buffer/sig;

    $pagina =~ s/%%DROPBOX_ACCESS_TOKEN%%/$prontus_varglb::DROPBOX_ACCESS_TOKEN/ig;
    $pagina =~ s/%%DROPBOX_FILEXT_EXCLUDE%%/$prontus_varglb::DROPBOX_FILEXT_EXCLUDE/ig;

    # CloudFlare.
    if ($prontus_varglb::CLOUDFLARE eq 'SI') {
        $pagina =~ s/%%CLOUDFLARE_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%CLOUDFLARE_NO%%//ig;
    } else {
        $pagina =~ s/%%CLOUDFLARE_SI%%//ig;
        $pagina =~ s/%%CLOUDFLARE_NO%%/ checked="checked"/ig;
        $pagina =~ s/<!--cloudflare-->(.*?)<!--\/cloudflare-->//sig;
    };

    $pagina =~ s/%%CLOUDFLARE_API_KEY%%/$prontus_varglb::CLOUDFLARE_API_KEY/ig;
    $pagina =~ s/%%CLOUDFLARE_EMAIL%%/$prontus_varglb::CLOUDFLARE_EMAIL/ig;
    $pagina =~ s/%%CLOUDFLARE_ZONE%%/$prontus_varglb::CLOUDFLARE_ZONE/ig;

    if ($prontus_varglb::CLOUDFLARE_API_URL eq 'https://www.cloudflare.com/api_json.html') {
        $pagina =~ s/%%CLOUDFLARE_API_URL_v1%%/ selected="selected"/ig;
        $pagina =~ s/%%CLOUDFLARE_API_URL_v4%%//ig;
    } elsif ($prontus_varglb::CLOUDFLARE_API_URL eq 'https://api.cloudflare.com/client/v4') {
        $pagina =~ s/%%CLOUDFLARE_API_URL_v4%%/ selected="selected"/ig;
        $pagina =~ s/%%CLOUDFLARE_API_URL_v1%%//ig;
    } else {
        $pagina =~ s/%%CLOUDFLARE_API_URL_v1%%/ selected="selected"/ig;
        $pagina =~ s/%%CLOUDFLARE_API_URL_v4%%//ig;
    }

    $pagina =~ s/%%CLOUDFLARE_GLOBAL_PURGE%%/$prontus_varglb::CLOUDFLARE_GLOBAL_PURGE/ig;

    $pagina =~ s/%%FRIENDLY_URLS_LARGO_TITULAR%%/$prontus_varglb::FRIENDLY_URLS_LARGO_TITULAR/ig;

    if ($prontus_varglb::FRIENDLY_URLS eq 'SI') {
        $pagina =~ s/%%FRIENDLY_URLS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%FRIENDLY_URLS_NO%%//ig;
    } else {
        $pagina =~ s/%%FRIENDLY_URLS_SI%%//ig;
        $pagina =~ s/%%FRIENDLY_URLS_NO%%/ checked="checked"/ig;
    };


    if ($prontus_varglb::FRIENDLY_URL_IMAGES eq 'SI') {
        $pagina =~ s/%%FRIENDLY_URL_IMAGES_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%FRIENDLY_URL_IMAGES_NO%%//ig;
    } else {
        $pagina =~ s/%%FRIENDLY_URL_IMAGES_SI%%//ig;
        $pagina =~ s/%%FRIENDLY_URL_IMAGES_NO%%/ checked="checked"/ig;
    };

    # variables para configurar recaptcha google
    $pagina =~ s/%%RECAPTCHA_API_URL%%/$prontus_varglb::RECAPTCHA_API_URL/ig;
    $pagina =~ s/%%RECAPTCHA_SECRET_CODE%%/$prontus_varglb::RECAPTCHA_SECRET_CODE/ig;


    if ($prontus_varglb::BLOQUEO_EDICION eq '0' || $prontus_varglb::BLOQUEO_EDICION eq '') {
        $pagina =~ s/%%BLOQUEO_EDICION_V0%%/ checked="checked"/ig;
        $pagina =~ s/%%BLOQUEO_EDICION_V1%%//ig;
        $pagina =~ s/%%BLOQUEO_EDICION_V2%%//ig;
    } elsif ($prontus_varglb::BLOQUEO_EDICION eq '1') {
        $pagina =~ s/%%BLOQUEO_EDICION_V0%%//ig;
        $pagina =~ s/%%BLOQUEO_EDICION_V1%%/ checked="checked"/ig;
        $pagina =~ s/%%BLOQUEO_EDICION_V2%%//ig;
    } elsif ($prontus_varglb::BLOQUEO_EDICION eq '2') {
        $pagina =~ s/%%BLOQUEO_EDICION_V0%%//ig;
        $pagina =~ s/%%BLOQUEO_EDICION_V1%%//ig;
        $pagina =~ s/%%BLOQUEO_EDICION_V2%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::FRIENDLY_URLS_VERSION eq '1') {
        $pagina =~ s/%%FRIENDLY_URLS_V1%%/ checked="checked"/ig;
        $pagina =~ s/%%FRIENDLY_URLS_V2%%//ig;
        $pagina =~ s/%%FRIENDLY_URLS_V3%%//ig;
    } elsif ($prontus_varglb::FRIENDLY_URLS_VERSION eq '2') {
        $pagina =~ s/%%FRIENDLY_URLS_V2%%/ checked="checked"/ig;
        $pagina =~ s/%%FRIENDLY_URLS_V1%%//ig;
        $pagina =~ s/%%FRIENDLY_URLS_V3%%//ig;
    } elsif ($prontus_varglb::FRIENDLY_URLS_VERSION eq '3') {
        $pagina =~ s/%%FRIENDLY_URLS_V3%%/ checked="checked"/ig;
        $pagina =~ s/%%FRIENDLY_URLS_V1%%//ig;
        $pagina =~ s/%%FRIENDLY_URLS_V2%%//ig;
    } else {
        # Dejar la versi�n 1 por defecto.
        $pagina =~ s/%%FRIENDLY_URLS_V1%%/ checked="checked"/ig;
        $pagina =~ s/%%FRIENDLY_URLS_V2%%//ig;
    };

    if ($prontus_varglb::PRONTUS_LOG eq 'SI') {
        $pagina =~ s/%%PRONTUS_LOG%%/ checked="checked"/ig;
    } else {
        $pagina =~ s/%%PRONTUS_LOG%%//ig;
    };

    if ($prontus_varglb::ARTIC_ACTUALIZA_PORTS eq 'SI') {
        $pagina =~ s/%%ARTIC_ACTUALIZA_PORTS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%ARTIC_ACTUALIZA_PORTS_NO%%//ig;
    } else {
        $pagina =~ s/%%ARTIC_ACTUALIZA_PORTS_SI%%//ig;
        $pagina =~ s/%%ARTIC_ACTUALIZA_PORTS_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::VERIFICAR_INSTALACION eq 'SI') {
        $pagina =~ s/%%VERIFICAR_INSTALACION%%/ checked="checked"/ig;
    } else {
        $pagina =~ s/%%VERIFICAR_INSTALACION%%//ig;
    };

    $pagina =~ s/%%SERVER_SMTP%%/$prontus_varglb::SERVER_SMTP/ig;
    $pagina =~ s/%%PUBLIC_SERVER_NAME%%/$prontus_varglb::PUBLIC_SERVER_NAME/ig;

    my $permitidos_vista = $prontus_varglb::UPLOADS_PERMITIDOS;
    $permitidos_vista =~ s/(,)/, /ig;
    $pagina =~ s/%%UPLOADS_PERMITIDOS%%/$permitidos_vista/ig;
#   $pagina =~ s/%%UPLOADS_EXTRAS%%/$prontus_varglb::UPLOADS_EXTRAS/ig;

    if ($prontus_varglb::VTXT_PASTE_NEWLINES_AS_P eq 'SI') {
        $pagina =~ s/%%VTXT_PASTE_NEWLINES_AS_P_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%VTXT_PASTE_NEWLINES_AS_P_NO%%//ig;
    } else {
        $pagina =~ s/%%VTXT_PASTE_NEWLINES_AS_P_SI%%//ig;
        $pagina =~ s/%%VTXT_PASTE_NEWLINES_AS_P_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::VTXT_DTD eq 'STRICT') {
        $pagina =~ s/%%VTXT_DTD_S%%/ selected="selected"/ig;
        $pagina =~ s/%%VTXT_DTD_T%%//ig;
    } elsif ($prontus_varglb::VTXT_DTD eq 'TRANSITIONAL') {
        $pagina =~ s/%%VTXT_DTD_S%%//ig;
        $pagina =~ s/%%VTXT_DTD_T%%/ selected="selected"/ig;
    } else {
        $pagina =~ s/%%VTXT_DTD_S%%//ig;
        $pagina =~ s/%%VTXT_DTD_T%%//ig;
    };

    if ($prontus_varglb::VTXT_ENCODE_CHARS eq 'SI') {
        $pagina =~ s/%%VTXT_ENCODE_CHARS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%VTXT_ENCODE_CHARS_NO%%//ig;
    } else {
        $pagina =~ s/%%VTXT_ENCODE_CHARS_SI%%//ig;
        $pagina =~ s/%%VTXT_ENCODE_CHARS_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::VTXT_MEDIA_SCRIPT eq 'SI') {
        $pagina =~ s/%%VTXT_MEDIA_SCRIPT_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%VTXT_MEDIA_SCRIPT_NO%%//ig;
    } else {
        $pagina =~ s/%%VTXT_MEDIA_SCRIPT_SI%%//ig;
        $pagina =~ s/%%VTXT_MEDIA_SCRIPT_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::FORM_CSV_CHARSET eq 'iso-8859-1') {
        $pagina =~ s/%%FORM_CSV_CHARSET_1%%//ig;
        $pagina =~ s/%%FORM_CSV_CHARSET_2%%/ selected="selected"/ig;
    } else {
        $pagina =~ s/%%FORM_CSV_CHARSET_1%%/ selected="selected"/ig;
        $pagina =~ s/%%FORM_CSV_CHARSET_2%%//ig;
    };


    my $post_proceso = $prontus_varglb::POST_PROCESO{'ART-BORRAR'};
    $post_proceso =~ s/^\((.*?)\)$//ig;
    $post_proceso = $1;
    $pagina =~ s/%%POST_PROCESO%%/$post_proceso/ig;

    $pagina =~ s/%%SCRIPT_QUOTA%%/$prontus_varglb::SCRIPT_QUOTA/ig;

    $pagina =~ s/%%FOTO_MAX_PIXEL%%/$prontus_varglb::FOTO_MAX_PIXEL/ig;

    $buffer = '';
    $pagina =~ /<!--loop_multivista-->(.*?)<!--\/loop_multivista-->/s;
    $loop = $1;
    my $cont = 1;
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        $temp = $loop;
        $temp =~ s/%%mv_valor%%/$mv/isg;
        $temp =~ s/%%num%%/$cont/isg;
        $buffer = $buffer . $temp;
        $cont++;
    };

    $pagina =~ s/<!--loop_multivista-->.*?<!--\/loop_multivista-->/$buffer/sig;

    # Para indicar si se usar� HTTPS
    if ($prontus_varglb::SERVER_PROTOCOLO_HTTPS eq 'SI') {
        $pagina =~ s/%%SERVER_PROTOCOLO_HTTPS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%SERVER_PROTOCOLO_HTTPS_NO%%//ig;
    } else {
        $pagina =~ s/%%SERVER_PROTOCOLO_HTTPS_SI%%//ig;
        $pagina =~ s/%%SERVER_PROTOCOLO_HTTPS_NO%%/ checked="checked"/ig;
    };

    $buffer = '';
    $pagina =~ /<!--loop_varnish-->(.*?)<!--\/loop_varnish-->/s;
    $loop = $1;

    foreach my $port (keys %prontus_varglb::VARNISH_SERVER_NAME) {
        $temp = $loop;
        $temp =~ s/%%varnish_valor%%/$port/isg;
        $buffer = $buffer . $temp;
    };

    $pagina =~ s/<!--loop_varnish-->.*?<!--\/loop_varnish-->/$buffer/sig;

    if ($prontus_varglb::ABRIR_FIDS_EN_POP eq 'SI') {
        $pagina =~ s/%%ABRIR_FIDS_EN_POP_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%ABRIR_FIDS_EN_POP_NO%%//ig;
    } else {
        $pagina =~ s/%%ABRIR_FIDS_EN_POP_SI%%//ig;
        $pagina =~ s/%%ABRIR_FIDS_EN_POP_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::USAR_PUBLIC_SERVER_NAME_VER_ARTIC eq 'SI') {
        $pagina =~ s/%%USAR_PUBLIC_SERVER_NAME_VER_ARTIC_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%USAR_PUBLIC_SERVER_NAME_VER_ARTIC_NOP%%//ig;
    } else {
        $pagina =~ s/%%USAR_PUBLIC_SERVER_NAME_VER_ARTIC_SI%%//ig;
        $pagina =~ s/%%USAR_PUBLIC_SERVER_NAME_VER_ARTIC_NO%%/ checked="checked"/ig;
    };

    $pagina =~ s/%%VARNISH_GLOBAL_PURGE%%/$prontus_varglb::VARNISH_GLOBAL_PURGE/ig;

    # Servidor de actualizaciones.
    $pagina =~ s/%%UPDATE_SERVER%%/$prontus_varglb::UPDATE_SERVER/ig;

    # parametros generales transcodificacion
    $pagina =~ s/%%DIR_FFMPEG%%/$prontus_varglb::DIR_FFMPEG/ig;
    $pagina =~ s/%%FFMPEG_PARAMS%%/$prontus_varglb::FFMPEG_PARAMS/ig;
    $pagina =~ s/%%MAX_XCODING%%/$prontus_varglb::MAX_XCODING/ig;

    if ($prontus_varglb::USAR_LIB_FDK eq 'SI') {
        $pagina =~ s/%%USAR_LIB_FDK_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%USAR_LIB_FDK_NO%%//ig;
    } else {
        $pagina =~ s/%%USAR_LIB_FDK_SI%%//ig;
        $pagina =~ s/%%USAR_LIB_FDK_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::PRECISION_HLS eq 'SI') {
        $pagina =~ s/%%PRECISION_HLS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%PRECISION_HLS_NO%%//ig;
    } else {
        $pagina =~ s/%%PRECISION_HLS_SI%%//ig;
        $pagina =~ s/%%PRECISION_HLS_NO%%/ checked="checked"/ig;
    };

    if ($prontus_varglb::ADVANCED_XCODING eq 'SI') {
        $pagina =~ s/%%ADVANCED_XCODING_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%ADVANCED_XCODING_NO%%//ig;
    } else {
        $pagina =~ s/%%ADVANCED_XCODING_SI%%//ig;
        $pagina =~ s/%%ADVANCED_XCODING_NO%%/ checked="checked"/ig;
        $pagina =~ s/<!--xcoding-->(.*?)<!--\/xcoding-->//sig;
    };

    # -xcoding.cfg
    if ($prontus_varglb::LIMIT_BITRATE eq 'SI') {
        $pagina =~ s/%%LIMIT_BITRATE_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%LIMIT_BITRATE_NO%%//ig;
    } else {
        $pagina =~ s/%%LIMIT_BITRATE_SI%%//ig;
        $pagina =~ s/%%LIMIT_BITRATE_NO%%/ checked="checked"/ig;
    };
    if ($prontus_varglb::GEN_HLS eq 'SI') {
        $pagina =~ s/%%GEN_HLS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%GEN_HLS_NO%%//ig;
    } else {
        $pagina =~ s/%%GEN_HLS_SI%%//ig;
        $pagina =~ s/%%GEN_HLS_NO%%/ checked="checked"/ig;
    };
    if ($prontus_varglb::MODO_PARALELO eq 'SI') {
        $pagina =~ s/%%MODO_PARALELO_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%MODO_PARALELO_NO%%//ig;
    } else {
        $pagina =~ s/%%MODO_PARALELO_SI%%//ig;
        $pagina =~ s/%%MODO_PARALELO_NO%%/ checked="checked"/ig;
    };
    $pagina =~ s/%%MAX_VIDEO_BITRATE%%/$prontus_varglb::MAX_VIDEO_BITRATE/ig;
    $pagina =~ s/%%MAX_AUDIO_BITRATE%%/$prontus_varglb::MAX_AUDIO_BITRATE/ig;
    $pagina =~ s/%%XCODE_MAX_PIXEL%%/$prontus_varglb::XCODE_MAX_PIXEL/ig;
    $pagina =~ s/%%RUTA_TEMPORAL_XCODING%%/$prontus_varglb::RUTA_TEMPORAL_XCODING/ig;
    $pagina =~ s/%%N_THREADS%%/$prontus_varglb::N_THREADS/ig;
    $pagina =~ s/%%XCODING_PPROC%%/$prontus_varglb::XCODING_PPROC/ig;
    $pagina =~ s/%%XCODE_MAX_PARALELO%%/$prontus_varglb::XCODE_MAX_PARALELO/ig;

    # configuracion de transcodificador externo
    if ($prontus_varglb::USAR_XCODER_EXTERNO eq 'SI') {
        $pagina =~ s/%%USAR_XCODER_EXTERNO_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%USAR_XCODER_EXTERNO_NO%%//ig;
    } else {
        $pagina =~ s/%%USAR_XCODER_EXTERNO_SI%%//ig;
        $pagina =~ s/%%USAR_XCODER_EXTERNO_NO%%/ checked="checked"/ig;
    };
    $pagina =~ s/%%XCODER_HOST%%/$prontus_varglb::XCODER_HOST/ig;
    $pagina =~ s/%%XCODER_PORT%%/$prontus_varglb::XCODER_PORT/ig;

    # -clustering.cfg

    $buffer = '';
    $pagina =~ /<!--loop_clustering-->(.*?)<!--\/loop_clustering-->/s;
    $loop = $1;

    foreach my $cluster (keys %prontus_varglb::CLUSTERING_SERVER) {
        $temp = $loop;
        $temp =~ s/%%cluster_valor%%/$cluster/isg;
        $buffer = $buffer . $temp;
    };

    $pagina =~ s/<!--loop_clustering-->.*?<!--\/loop_clustering-->/$buffer/sig;

    # -coment.cfg

    # Cargar datos de cfg de coment.
    my ($options_tipo, $msg_err, $hash_tipos_ref) = &lib_coment::get_objtipos($coment_varglb::DIR_SERVER, 'articulo', $prontus_varglb::PRONTUS_ID);
    my %HASH_TIPOS;
    # Se debe chequear si hay error, de otra forma se cae
    if ($msg_err) {
        print STDERR "error coments[$msg_err]\n";
    } else {
        %HASH_TIPOS = %$hash_tipos_ref;
    };

    $pagina =~ s/%%NOM%%/$HASH_TIPOS{'articulo'}{'NOM'}/ig;
    $pagina =~ s/%%ARTIC_EXTENSION%%/$HASH_TIPOS{'articulo'}{'ARTIC_EXTENSION'}/ig;
    $pagina =~ s/%%MSG_MODER%%/$HASH_TIPOS{'articulo'}{'MSG_MODER'}/ig;
    $pagina =~ s/%%MSG_NOMODER%%/$HASH_TIPOS{'articulo'}{'MSG_NOMODER'}/ig;
    $pagina =~ s/%%LIMIT_CHARS%%/$HASH_TIPOS{'articulo'}{'LIMIT_CHARS'}/ig;
    $pagina =~ s/%%FILASXPAG_PUBLIC%%/$HASH_TIPOS{'articulo'}{'FILASXPAG_PUBLIC'}/ig;
    $pagina =~ s/%%MAIL_PUBLICACION_FROM%%/$HASH_TIPOS{'articulo'}{'MAIL_PUBLICACION_FROM'}/ig;
    $pagina =~ s/%%MAIL_PUBLICACION_ASUNTO%%/$HASH_TIPOS{'articulo'}{'MAIL_PUBLICACION_ASUNTO'}/ig;
    $pagina =~ s/%%MAIL_PUBLICACION_SMTP%%/$HASH_TIPOS{'articulo'}{'MAIL_PUBLICACION_SMTP'}/ig;
    $pagina =~ s/%%PHP_SESSION_PATH%%/$HASH_TIPOS{'articulo'}{'PHP_SESSION_PATH'}/ig;
    $pagina =~ s/%%PHP_SESSION_NAME%%/$HASH_TIPOS{'articulo'}{'PHP_SESSION_NAME'}/ig;

    if ($HASH_TIPOS{'articulo'}{'ENVIAR_MAIL_PUBLICACION'} eq 'SI') {
        $pagina =~ s/%%ENVIAR_MAIL_PUBLICACION_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%ENVIAR_MAIL_PUBLICACION_NO%%//ig;
        $pagina =~ s/%%ENVIAR_MAIL_PUBLICACION_style%%//ig;
    } else {
        $pagina =~ s/%%ENVIAR_MAIL_PUBLICACION_SI%%//ig;
        $pagina =~ s/%%ENVIAR_MAIL_PUBLICACION_NO%%/ checked="checked"/ig;
        $pagina =~ s/%%ENVIAR_MAIL_PUBLICACION_style%%/ display: none;/ig;
    };

    if ($HASH_TIPOS{'articulo'}{'CAPTCHA'} eq 'SI') {
        $pagina =~ s/%%CAPTCHA_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%CAPTCHA_NO%%//ig;
    } else {
        $pagina =~ s/%%CAPTCHA_SI%%//ig;
        $pagina =~ s/%%CAPTCHA_NO%%/ checked="checked"/ig;
    };

    if ($HASH_TIPOS{'articulo'}{'MODERACION'} eq 'SI') {
        $pagina =~ s/%%MODERACION_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%MODERACION_NO%%//ig;
    } else {
        $pagina =~ s/%%MODERACION_SI%%//ig;
        $pagina =~ s/%%MODERACION_NO%%/ checked="checked"/ig;
    };

    # buscador_prontus.cfg

    my $dir_cpan = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/cpan';
    my %cfg_buscador = &lib_search::get_config("$dir_cpan/buscador_prontus.cfg");

    $buffer = '';
    $pagina =~ /<!--loop_prontus_dir-->(.*?)<!--\/loop_prontus_dir-->/s;
    $loop = $1;
    foreach my $variable (keys %cfg_buscador) {
        next unless($variable =~ /^PRONTUS_DIR_(\d+)$/);
        my $cont = $1;
        my $valor = $cfg_buscador{$variable};
        $temp = $loop;
        $temp =~ s/%%prontusdir_valor%%/$valor/isg;
        $temp =~ s/%%num%%/$cont/isg;
        $buffer = $buffer . $temp;
        $cont++;
    };
    $pagina =~ s/<!--loop_prontus_dir-->.*?<!--\/loop_prontus_dir-->/$buffer/sig;


    $buffer = '';
    $pagina =~ /<!--loop_rawdir-->(.*?)<!--\/loop_rawdir-->/s;
    $loop = $1;
    foreach my $variable (keys %cfg_buscador) {
        next unless($variable =~ /^RAW_DIR_(\d+)$/);
        my $cont = $1;
        my $valor = $cfg_buscador{$variable};
        $temp = $loop;
        $temp =~ s/%%rawdir_valor%%/$valor/isg;
        $temp =~ s/%%num%%/$cont/isg;
        $buffer = $buffer . $temp;
        $cont++;
    };
    $pagina =~ s/<!--loop_rawdir-->.*?<!--\/loop_rawdir-->/$buffer/sig;


    $buffer = '';
    $pagina =~ /<!--loop_rawfiletypes-->(.*?)<!--\/loop_rawfiletypes-->/s;
    $loop = $1;
    my $cont = 1;
    my @rawfiletypes = split(/ +/, $cfg_buscador{'RAW_FILETYPES'});
    foreach my $ftype (@rawfiletypes) {
        $temp = $loop;
        $temp =~ s/%%filetype_valor%%/$ftype/isg;
        $temp =~ s/%%num%%/$cont/isg;
        $buffer = $buffer . $temp;
        $cont++;
    };
    $pagina =~ s/<!--loop_rawfiletypes-->.*?<!--\/loop_rawfiletypes-->/$buffer/sig;
    $pagina =~ s/%%RAW_FILETYPES%%/$cfg_buscador{'RAW_FILETYPES'}/ig;


    $buffer = '';
    $pagina =~ /<!--loop_urlfiletypes-->(.*?)<!--\/loop_urlfiletypes-->/s;
    $loop = $1;
    my $cont = 1;
    my @rawfiletypes = split(/ +/, $cfg_buscador{'URL_FILETYPES'});
    foreach my $ftype (@rawfiletypes) {
        $temp = $loop;
        $temp =~ s/%%filetype_valor%%/$ftype/isg;
        $temp =~ s/%%num%%/$cont/isg;
        $buffer = $buffer . $temp;
        $cont++;
    };

    $pagina =~ s/<!--loop_urlfiletypes-->.*?<!--\/loop_urlfiletypes-->/$buffer/sig;

    $buffer = '';
    my $dir_fid = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/cpan/fid/';
    &glib_fildir_02::check_dir($dir_fid);
    my @fids_listado = &glib_fildir_02::lee_dir($dir_fid);

    # Generar arreglo de hash para checkboxs.
    my @fidlist;
    foreach my $fid_file (@fids_listado) {
        if ($fid_file =~ /fid_(.*?)\.html/) {
            my $fid_name = "fid_$1";
            if ($cfg_buscador{'FIDS'} =~ /( |^)$fid_file( |$)/) {
                push @fidlist, {label    => $fid_name, value   => $fid_file, checked => 1};
            } else {
                push @fidlist, {label    => $fid_name, value   => $fid_file, checked => 0};
            };
        };
    };

    my $filas_tabla_checkbox = &glib_html_02::generar_filas_tabla_checkbox(\@fidlist, 'INPUT_FIDS[]', 'buscador');

    # parsea los fids disponibles.
    $pagina =~ s/%%buscador_fids%%/$filas_tabla_checkbox/sig;

    $pagina =~ s/%%URL_FILETYPES%%/$cfg_buscador{'URL_FILETYPES'}/ig;
    $pagina =~ s/%%URL_MAXPAGS%%/$cfg_buscador{'URL_MAXPAGS'}/ig;
    $pagina =~ s/%%FIDS%%/$cfg_buscador{'FIDS'}/ig;
    $pagina =~ s/%%RESUMEN%%/$cfg_buscador{'RESUMEN'}/ig;
    $pagina =~ s/%%MAXCARS%%/$cfg_buscador{'MAXCARS'}/ig;
    $pagina =~ s/%%RATIO%%/$cfg_buscador{'RATIO'}/ig;
    $pagina =~ s/%%MINTEXT%%/$cfg_buscador{'MINTEXT'}/ig;
    $pagina =~ s/%%TITLEVAR%%/$cfg_buscador{'TITLEVAR'}/ig;

    $pagina =~ s/%%SEARCHTIPS_MAXRESULT%%/$cfg_buscador{'SEARCHTIPS_MAXRESULT'}/ig;
    $pagina =~ s/%%SEARCHTIPS_MINLEN%%/$cfg_buscador{'SEARCHTIPS_MINLEN'}/ig;
    $pagina =~ s/%%SEARCHTIPS_DURACION_CACHE%%/$cfg_buscador{'SEARCHTIPS_DURACION_CACHE'}/ig;
    $pagina =~ s/%%SEARCHTIPS_MAXREQUESTXIP%%/$cfg_buscador{'SEARCHTIPS_MAXREQUESTXIP'}/ig;

    $pagina =~ s/%%META1%%/$cfg_buscador{'META1'}/ig;
    $pagina =~ s/%%META2%%/$cfg_buscador{'META2'}/ig;
    $pagina =~ s/%%META3%%/$cfg_buscador{'META3'}/ig;

    $pagina =~ s/%%METADATA1%%/$cfg_buscador{'METADATA1'}/ig;
    $pagina =~ s/%%METADATA2%%/$cfg_buscador{'METADATA2'}/ig;
    $pagina =~ s/%%METADATA3%%/$cfg_buscador{'METADATA3'}/ig;
    $pagina =~ s/%%METADATA4%%/$cfg_buscador{'METADATA4'}/ig;
    $pagina =~ s/%%METADATA5%%/$cfg_buscador{'METADATA5'}/ig;
    $pagina =~ s/%%METADATA6%%/$cfg_buscador{'METADATA6'}/ig;
    $pagina =~ s/%%METADATA7%%/$cfg_buscador{'METADATA7'}/ig;
    $pagina =~ s/%%METADATA8%%/$cfg_buscador{'METADATA8'}/ig;
    $pagina =~ s/%%METADATA9%%/$cfg_buscador{'METADATA9'}/ig;
    $pagina =~ s/%%METADATA10%%/$cfg_buscador{'METADATA10'}/ig;
    $pagina =~ s/%%METADATA11%%/$cfg_buscador{'METADATA11'}/ig;
    $pagina =~ s/%%METADATA12%%/$cfg_buscador{'METADATA12'}/ig;
    $pagina =~ s/%%METADATA13%%/$cfg_buscador{'METADATA13'}/ig;
    $pagina =~ s/%%METADATA14%%/$cfg_buscador{'METADATA14'}/ig;
    $pagina =~ s/%%METADATA15%%/$cfg_buscador{'METADATA15'}/ig;
    $pagina =~ s/%%METADATA16%%/$cfg_buscador{'METADATA16'}/ig;
    $pagina =~ s/%%METADATA17%%/$cfg_buscador{'METADATA17'}/ig;
    $pagina =~ s/%%METADATA18%%/$cfg_buscador{'METADATA18'}/ig;
    $pagina =~ s/%%METADATA19%%/$cfg_buscador{'METADATA19'}/ig;
    $pagina =~ s/%%METADATA20%%/$cfg_buscador{'METADATA20'}/ig;

    if ($cfg_buscador{'USEFRIENDLYURLS'} eq '1') {
        $pagina =~ s/%%USEFRIENDLYURLS_SI%%/ checked="checked"/ig;
        $pagina =~ s/%%USEFRIENDLYURLS_NO%%//ig;
    } else {
        $pagina =~ s/%%USEFRIENDLYURLS_SI%%//ig;
        $pagina =~ s/%%USEFRIENDLYURLS_NO%%/  checked="checked"/ig;
    };

    $buffer = '';
    $pagina =~ /<!--loop_textvars-->(.*?)<!--\/loop_textvars-->/s;
    $loop = $1;
    my $cont = 1;
    my @rawfiletypes = split(/ +/, $cfg_buscador{'TEXTVARS'});
    foreach my $ftype (@rawfiletypes) {
        $temp = $loop;
        $temp =~ s/%%textvar_valor%%/$ftype/isg;
        $temp =~ s/%%num%%/$cont/isg;
        $buffer = $buffer . $temp;
        $cont++;
    };

    $pagina =~ s/<!--loop_textvars-->.*?<!--\/loop_textvars-->/$buffer/sig;

    $pagina =~ s/%%TEXTVARS%%/$cfg_buscador{'TEXTVARS'}/ig;
    $pagina =~ s/%%RESPERPAG%%/$cfg_buscador{'RESPERPAG'}/ig;
    $pagina =~ s/%%MAXPAGS%%/$cfg_buscador{'MAXPAGS'}/ig;

    if ($cfg_buscador{'SEARCH_TIPO_PAGINACION'} eq '0') {
        $pagina =~ s/%%SEARCH_TIPO_PAGINACION_V0%%/ checked="checked"/ig;
        $pagina =~ s/%%SEARCH_TIPO_PAGINACION_V1%%//ig;
    } else {
        $pagina =~ s/%%SEARCH_TIPO_PAGINACION_V0%%//ig;
        $pagina =~ s/%%SEARCH_TIPO_PAGINACION_V1%%/ checked="checked"/ig;
    };
    $pagina =~ s/%%SEARCH_PAGCORTA_MAXPAGS%%/$cfg_buscador{'SEARCH_PAGCORTA_MAXPAGS'}/ig;

    $pagina =~ s/%%SEARCH_MAXEXEC%%/$cfg_buscador{'SEARCH_MAXEXEC'}/ig;
    $pagina =~ s/%%SEARCH_MAXEXEC%%/$cfg_buscador{'SEARCH_MAXEXEC'}/ig;

    return $pagina;
};

# --------------------------------------------------------------------------------------------------
sub parseRegen {
    my ($pagina) = $_[0];

    #~ CVI - 17/08/2012 - Se muestran solo los que estan configurados
    my @fidlist;
    foreach my $strfid (sort keys %prontus_varglb::FORM_PLTS) {
        #~ print STDERR "strfid[$strfid]\n";
        if($strfid =~ /^(.*?):(.*?)$/) {
            push @fidlist, {label    => $2, value   => $1, checked => 1};
        }
    };

    #~ CVI - 13/05/2013 - Para el tema del regenerador de portadas
    if ($prontus_varglb::MULTI_EDICION eq 'NO') {
        $pagina =~ s/<!--admin_ediciones-->.*<!--\/admin_ediciones-->//isg;
    } else {
        my $dir_edics = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EDIC";
        #~ print STDERR "dir_edics[$dir_edics]\n";
        my $html_ediciones = &get_html_ediciones($dir_edics);
        $pagina =~ s/<!--admin_ediciones-->(.*?)<!--\/admin_ediciones-->/\1/isg;
        $pagina =~ s/%%_edic%%/$html_ediciones/;
    };

    my $filas_tabla_checkbox_fids = &glib_html_02::generar_filas_tabla_checkbox(\@fidlist, 'INPUT_FIDS_REGEN[]', 'regen');
    $pagina =~ s/%%filas_tabla_checkbox_fids%%/$filas_tabla_checkbox_fids/sig;

    # MVS.
    my @mvlist;
    push @mvlist, {label    => 'Vista Principal', value   => '@normal', checked => 1};

    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        push @mvlist, {label    => $mv, value   => $mv, checked => 1};
    };

    my $filas_tabla_checkbox_mvs = &glib_html_02::generar_filas_tabla_checkbox(\@mvlist, 'INPUT_MVS_REGEN[]', 'regen');
    $pagina =~ s/%%filas_tabla_checkbox_mvs%%/$filas_tabla_checkbox_mvs/sig;

    # Listado de secciones.
    my %secciones = &lib_tax::carga_tabla_seccion($DB);
    my $secciones_list;

    foreach my $secc (sort keys %secciones) {
      my @info_secc = split(/\t\t/, $secciones{$secc});
      $secciones_list .= "<option value=\"$secc\">$info_secc[0]</option>";
    };

    $pagina =~ s/%%secciones%%/$secciones_list/sig;

    return $pagina;

};
# ---------------------------------------------------------------
sub get_html_ediciones {
    my $dir_edics = shift;
    # Generar cod. html correspondiente a la combo de ediciones
    my $html_ediciones = &lib_prontus::generar_popupdirs_from_dir($dir_edics, 'cmb_edic', '', 1, '', '', '', $prontus_varglb::NRO_EDICS_WORK, 'STRDESC');
    my $qty_base_ports = @prontus_varglb::BASE_PORTS;
    # warn "qty_base_ports[$qty_base_ports]";
    $html_ediciones =~ s/(<select.*?>)/\1<option value="">  <\/option>/is; # eliminar de la combo la edic. base.
    return $html_ediciones;
};
