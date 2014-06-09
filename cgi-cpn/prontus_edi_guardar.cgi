#!/usr/bin/perl

# ----------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ----------------------------------------------------------------

# --------------------------------COMENTARIO GLOBAL---------------
# ----------------------------------------------------------------
# PROPOSITO .
# ------------
# Procesar 'submit' de la pagina de ingreso/modif. de edicion.
# Botones procesados :
# 1) Guardar : crea o guarda los cambios de la edicion.
# 2) Borrar : elimina la edicion actual.

# ----------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# -------------------------------
# 1) Despues de Borrar / Guardar, llama a la pag. de Adm. de Ediciones
# (ap_edi_admin.SHTML sin param.).

# ----------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# -------------------------
# 1) Desde la pag. de ingreso/modif. de edicion, via submit.
# ----------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# -------------------------
# No registra.
# ----------------------------------------------------------------
# Version  oficial 1.0 at 04/10/2000
# 1.1 - 06-11-2000 soporte chupoptero (se agrega manejo de hiddens de la forma name = SITEREFpaismundo.html y value=http://www.mercuriovalpo.cl)
# y campo texto con name EDIREFpaismundo.html el que indica el nro de la edicion en el sitio de referencia.
# 1.2 - 16/11/2000 - soporte chupoptero verdadero.
# 2.0 - 21/12/2000 - Chupopterea solo si viene la checkbox Chk_SINC con value SINC
# 2.1 - 26/12/2000 - Modifica para que la generacion de la pagina index.shtml sea ahora a partir de un template /web/index_tmp.shtml
# En este template, se sustituye la marca %%PATH_HOMEPAGE%% por el path a la edicion vigente.
# 2.2 - 27/12/2000 - Correcciones a 1.2 (problemas con e.r. y parseo de marca %%TITPAG%%).

# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0
# 6.1 - 21/11/2001 - Correccion en lectura del working.html
# Prontus 8.0 - 23/05/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# Prontus 8.1 - 09/09/2002 - YCH - Soporte windows media. Ver detalles en /release_prontus81.txt
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# Especial DRs - 08/01/2004 - YCH - Agrega soporte Antialone (parseo de antialone_tmp.html) analogo a lanacion.cl.
# --------------------------------BEGIN SCRIPT--------------------
# ----------------------------------------------------------------
# DECLARACIONES GLOBALES.
# -------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use glib_fildir_02;
use glib_hrfec_02;
use glib_html_02;
use lib_prontus;

use glib_cgi_04;

use strict;

my (%FORM); # 8.0

my ($RELDIR_EDICIONES);

my ($RELDIR_CONT_EDIC);


my ($RELDIR_CONT_SECC);

my ($RELDIR_CONT_HPAGE);



my ($RELDIR_TEMP_EDIC);


my ($RELDIR_TEMP_SECC);

my ($RELDIR_TEMP_HPAGE);


# ----------------------------------------------------------------
# MAIN.
# --------------



  # Rescatar parametros recibidos
  &glib_cgi_04::new();
  $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
  
  #print STDERR "antes: _path_conf[$FORM{'_path_conf'}]";
  
  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});


  # Rescatar valores de campos fijos
  $FORM{'ED_NOM'} = &glib_cgi_04::param('ED_NOM');# Campo hidden con el nombre de la edicion


  $FORM{'ED_VIGENTE'} = &glib_cgi_04::param('ED_VIGENTE');  # Checkbox indicador de vigencia
  if ($FORM{'ED_VIGENTE'} eq '') {
    $FORM{'ED_VIGENTE'} = 'NO';
  };

  #print STDERR "despues: _path_conf[$FORM{'_path_conf'}]";
  
  # Carga variables de configuracion.
  &lib_prontus::load_config($FORM{'_path_conf'});
  $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

  if ($prontus_varglb::IP_SERVER ne '') { # implica llamada desde ambiente web. # 1.23
    &lib_prontus::test_servers($ENV{'HTTP_REFERER'}); # Autentifica request.  con SERVER_PERM.
  };


  ($RELDIR_EDICIONES) = $prontus_varglb::DIR_CONTENIDO .
                         $prontus_varglb::DIR_EDIC;

  ($RELDIR_CONT_EDIC) = $RELDIR_EDICIONES .
                         "/%%ED_NOM%%";


  ($RELDIR_CONT_SECC) = $RELDIR_CONT_EDIC .
                         $prontus_varglb::DIR_SECC;

  ($RELDIR_CONT_HPAGE) = $RELDIR_CONT_EDIC .
                          $prontus_varglb::DIR_HPAGES;



  ($RELDIR_TEMP_EDIC) = $prontus_varglb::DIR_TEMP .
                         $prontus_varglb::DIR_EDIC .
                         $prontus_varglb::DIR_NROEDIC;


  ($RELDIR_TEMP_SECC) = $RELDIR_TEMP_EDIC .
                         $prontus_varglb::DIR_SECC;

  ($RELDIR_TEMP_HPAGE) = $RELDIR_TEMP_EDIC .
                          $prontus_varglb::DIR_HPAGES;


  # Valida conf. multi-ed
  if ($prontus_varglb::MULTI_EDICION ne 'SI') {
    &glib_html_02::print_json_result(0, 'Este Prontus no está configurado como multi edición', 'exit=1,ctype=1');
  };

    # user check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };


    if ($prontus_varglb::EDITOR_ADMINISTRAR_EDICIONES eq 'NO' && $prontus_varglb::USERS_PERFIL eq 'E') {
        &glib_html_02::print_json_result(0, 'La funcionalidad requerida está disponible sólo para el administrador del sistema', 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL ne 'A' && $prontus_varglb::USERS_PERFIL ne 'E') {
        &glib_html_02::print_json_result(0, 'La funcionalidad requerida está disponible sólo para el administrador del sistema y editores', 'exit=1,ctype=1');
    };

# ---------BOTON GUARDAR--------------------------------------------------



    # Nueva edicion
  	if ($FORM{'ED_NOM'} eq '') {
  	  # Fecha corta.
  	  $FORM{'ED_FECCORTA'} = &glib_cgi_04::param('ED_FECCORTA'); # parametro obligatorio,

      # Generar nombre de edicion en base a fecha corta
      $FORM{'ED_NOM'} = &make_nom_edic();


      # Combo con ediciones anteriores, para escoger en base a cual se creará la nueva. Puede setar vacia
      $FORM{'Cmb_EDIC'} = &glib_cgi_04::param('Cmb_EDIC');
      if ($FORM{'Cmb_EDIC'}) {
        my ($padre_orig) = $prontus_varglb::DIR_SERVER . $RELDIR_EDICIONES;
        my ($padre_dest) = $padre_orig;
        my ($orig) = $FORM{'Cmb_EDIC'};
        my ($dest) = $FORM{'ED_NOM'};
        &glib_fildir_02::copy_tree($padre_orig, $orig, $padre_dest, $dest);

        # elimina archivos de directorios <nom_edic>/port, <nom_edic>/port-<vista> y <nom_edic>/xml
        # que no correspondan a portadas definidas en el cfg.
        # Lo anterior es para no ir replicando basura.
        &limpia_dir_edic("$padre_dest/$dest/port");
        &limpia_dir_edic("$padre_dest/$dest/xml", "xml");
        foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
          &limpia_dir_edic("$padre_dest/$dest/port-$mv");
        };

      }
      else {
        # Crear directorios de la edicion desde cero.
        &lib_prontus::check_dirs_edic($prontus_varglb::DIR_SERVER . $RELDIR_EDICIONES . "/$FORM{'ED_NOM'}");
        &parse_dirs_edic();

        # Inicializa las portadas (o secciones) de la edicion con paginas en construccion.
        &init_seccs();

      };
    };

    # hasta aca es nuevo, lo demas rige para nuevo y modificar.
    &parse_dirs_edic();

    # Generar hp de la edicion
    &generar_homepage_edicion();

    # &generar_menus();

    # Escribir/actualizar homepage del sitio web
    &generar_homepage_sitio(); # 8.0

    &lib_prontus::write_log('Guardar', 'Edicion', $prontus_varglb::DIR_SERVER . $RELDIR_CONT_HPAGE . "/$prontus_varglb::INDEX_EDIC");

    &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');






# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub parse_dirs_edic {

  $RELDIR_CONT_EDIC =~ s/%%ED_NOM%%/$FORM{'ED_NOM'}/;

  $RELDIR_CONT_SECC =~ s/%%ED_NOM%%/$FORM{'ED_NOM'}/;

  $RELDIR_CONT_HPAGE =~ s/%%ED_NOM%%/$FORM{'ED_NOM'}/;

};

# ---------------------------------------------------------------
sub limpia_dir_edic {
  my $dir = $_[0];
  my $is_xml_dir = $_[1];

  my %port_plts;
  if ($is_xml_dir) {
    foreach my $entry (keys %prontus_varglb::PORT_PLTS) {
      $entry =~ s/\.\w+$/\.xml/;
      $port_plts{$entry} = 1;
    };
  }
  else {
    %port_plts = %prontus_varglb::PORT_PLTS;
    # Agregar las portadas secundarias
    my @paralel_ports;
    foreach my $nomport_in_cfg (keys %prontus_varglb::PORT_PLTS_EXTRA) {
        my $extra_ports = $prontus_varglb::PORT_PLTS_EXTRA{$nomport_in_cfg}; # contiene los items separados por ;
        while ($extra_ports =~ /([\w\-\.]+) *;?/g) {
            my $extra_port = $1;
            $port_plts{$extra_port} = 1;
        };
    };
  };


  my @entries_dir = &glib_fildir_02::lee_dir($dir);
  foreach my $entry (@entries_dir) {
    if (($entry !~ /^\./g) && (-f "$dir/$entry")) {
      if (! exists $port_plts{$entry}) {
        unlink "$dir/$entry";
      };
    };
  };

};

# ---------------------------------------------------------------

sub make_nom_edic {

  # Compone nombre de la edicion en base a fecha corta.
  my ($nom_edic, $dir, $entry);
  if ($FORM{'ED_FECCORTA'} =~ /(\d\d?)[\-\/](\d\d?)[\-\/](\d{4})/) {
    my ($aaaa, $mm, $dd) = ($3, $2, $1);
    $dd = '0' . $dd if (($dd < 10) and ((length $dd) < 2));
    $mm = '0' . $mm if (($mm < 10) and ((length $mm) < 2));

    my ($correl) = '1';
    $nom_edic = $aaaa . '_' . $mm . '_' . $dd . '_' . $correl;

    while (-d $prontus_varglb::DIR_SERVER . $RELDIR_EDICIONES . "/$nom_edic") {
      $correl++;

      $nom_edic = $aaaa . '_' . $mm . '_' . $dd . '_' . $correl;
    };


    return $nom_edic;
  }
  else {
    &glib_html_02::print_json_result(0, 'Fecha Corta inválida. Debe ser del tipo dd/mm/aaaa', 'exit=1,ctype=1');
  };

};
# ---------------------------------------------------------------

sub generar_homepage_sitio {
my ($path_homesitio, $tpl_index_sitio, $homesitio, $url_homepage, $path_antialone, $antialone);

  $path_homesitio = $prontus_varglb::DIR_SERVER . "$prontus_varglb::RELDIR_BASE/$prontus_varglb::PRONTUS_ID/$prontus_varglb::INDEX_SITIO";
  $path_antialone = $prontus_varglb::DIR_SERVER . "$prontus_varglb::RELDIR_BASE/$prontus_varglb::PRONTUS_ID/$prontus_varglb::ANTIALONE";

  # 2.1 cargar template de la pag.
  $homesitio = &glib_fildir_02::read_file($prontus_varglb::DIR_SERVER . "$prontus_varglb::RELDIR_BASE/$prontus_varglb::PRONTUS_ID/$prontus_varglb::TPL_INDEX_SITIO");
  $homesitio =~ s/%25%25/%%/sg;

  # 9.0 Carga template Antialone. $TPL_ANTIALONE
  $antialone = &glib_fildir_02::read_file($prontus_varglb::DIR_SERVER . "$prontus_varglb::RELDIR_BASE/$prontus_varglb::PRONTUS_ID/$prontus_varglb::TPL_ANTIALONE");
  $antialone =~ s/%25%25/%%/sg;


  # Si se desea establecer como vigente.
  if ($FORM{'ED_VIGENTE'} eq 'SI') {

    $url_homepage = $RELDIR_CONT_HPAGE . "/$prontus_varglb::INDEX_EDIC";

    $homesitio =~ s/%%PATH_HOMEPAGE%%/$url_homepage/;   # 2.1
    $homesitio =~ s/%%_NOM_EDIC%%/$FORM{'ED_NOM'}/isg;
    $homesitio =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;

    &glib_fildir_02::write_file($path_homesitio, $homesitio);
    &lib_prontus::purge_cache($path_homesitio);

    # Ademas escribe arch de texto con el nro de la ed. vigente
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/ed_vigente.txt", $FORM{'ED_NOM'});

    # Actualiza antialone.
    $antialone =~ s/%%ED_NOM%%/$FORM{'ED_NOM'}/sg;
    $antialone =~ s/%%_NOM_EDIC%%/$FORM{'ED_NOM'}/isg;
    $antialone =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
    &glib_fildir_02::write_file($path_antialone, $antialone);
    &lib_prontus::purge_cache($path_antialone);
  }
  else {
    # Si esta es la actualmente vigente borrar tag refresh de index.html.
    if (&lib_prontus::ed_vigente($FORM{'ED_NOM'}) eq 'SI') {
      $homesitio = '<HTML>
                    <HEAD>
                      <TITLE>No hay edicion vigente</TITLE>
                    </HEAD>
                    <BODY>No hay edicion vigente
                    </BODY>
                  </HTML>';

      &glib_fildir_02::write_file($path_homesitio, $homesitio);
      &lib_prontus::purge_cache($path_homesitio);

      # Ademas escribe arch de texto con el nro de la ed. vigente
      &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/ed_vigente.txt", '');
    };
  };

};
# ---------------------------------------------------------------
sub generar_homepage_edicion {

my ($tpl_hpage, $nro_campos);
my ($atributos_edi, $hpage);


  # Cargar tpl de la homepage.
  $tpl_hpage = &glib_fildir_02::read_file($prontus_varglb::DIR_SERVER . $RELDIR_TEMP_HPAGE . "/$prontus_varglb::INDEX_EDIC");

  $tpl_hpage =~ s/%25%25/%%/sg;

  # Generar texto conteniendo los pares <!--param=valor--> a incluir en el head de la homepage (atributos de la edicion)
  $atributos_edi = "";

  # Reemplazar la marca en el tpl correspondiente.
  $tpl_hpage =~ s/%%ATRIBUTOS_EDI%%/$atributos_edi/;

  $hpage = $tpl_hpage;

  # Escribirla en disco.
  &glib_fildir_02::write_file($prontus_varglb::DIR_SERVER . $RELDIR_CONT_HPAGE . "/$prontus_varglb::INDEX_EDIC", $hpage);
  &lib_prontus::purge_cache($prontus_varglb::DIR_SERVER . $RELDIR_CONT_HPAGE . "/$prontus_varglb::INDEX_EDIC");
};




# ---------------------------------------------------------------
sub init_seccs{
# Inicializa las portadas (o secciones) de la edicion con paginas en construccion.

my ($dir_secc_edic, $dir_secc_tpl, @entries, $text_working, $path_secc, $entry);

  # Path absoluto al dir. donde se generaran las portadas de la edicion.
  $dir_secc_edic = $prontus_varglb::DIR_SERVER .
                   $RELDIR_CONT_SECC;

  # Path absoluto al dir. donde residen los templates de portadas del sitio web, comunes para todas las ediciones.
  $dir_secc_tpl = $prontus_varglb::DIR_SERVER .
                  $RELDIR_TEMP_SECC;

  # Para c/ template de portada, generar la portada correspondiente en la edicion, pero con
  # el contenido 'Pagina en Construccion'.

  # Leer pagina en construccion. # 6.1
  $text_working = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::RELDIR_BASE/$prontus_varglb::PRONTUS_ID/$prontus_varglb::PAG_WORKING");

  # Inicializar secciones
  @entries = &glib_fildir_02::lee_dir($dir_secc_tpl);
  foreach $entry (@entries) {
    if ($entry !~ /^\./g) {
      $path_secc = "$dir_secc_tpl/$entry";
      # Si es un arch valido
      if ( -f $path_secc ) {
        # Escribir en el directorio de portadas de la edicion recien creada.
        &glib_fildir_02::write_file($dir_secc_edic . "/$entry" , $text_working);
      };
    };
  };

};



# ---------------------------------------------------------------
# USAR ESTA FUNCION EN EL PUBLIC, AL ACTUALIZAR LA PORTADA.
sub actualizar_secciones {
# Actualiza las secciones de la edicion con la fechap.
my ($nom_campo, $val_campo, $dir_secc, @entries, $entry, $text_secc, $path_secc, $marca_izq, $marca_der, $sustit);

  @entries = &glib_fildir_02::lee_dir($prontus_varglb::DIR_SERVER . $RELDIR_CONT_SECC);

  foreach $entry (@entries) {
    if ($entry !~ /^\./g) {
      $path_secc = "$dir_secc/$entry";
      if (-f $path_secc) {
        $text_secc = &glib_fildir_02::read_file($path_secc);
        $text_secc =~ s/%25%25/%%/sg;
        $FORM{'ED_NOM'} =~ /^(\d\d\d\d)\_(\d\d)\_(\d\d)/;
        my $aaammdd = $1 . $2 . $3;

        my $fechaplong = &glib_hrfec_02::expande_fecha($aaammdd);
        $text_secc =~ s/%%FECHAPLONG%%/$fechaplong/isg;

        my $fechapshrt = &glib_hrfec_02::des_normaliza_fecha($aaammdd);
        $text_secc =~ s/%%FECHAPSHRT%%/$fechapshrt/isg;

        &glib_fildir_02::write_file($path_secc, $text_secc);
      };
    };
  };

};

# -------------------------------END SCRIPT----------------------

