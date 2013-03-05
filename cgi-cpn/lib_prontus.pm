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
# Rutinas genericas para auto-publicador tipo PRONTUS-01, PRONTUS-02, PRONTUS-03 y PRONTUS-04
# Libreria derivada de glib_ap_01.pm (construida para www.mercuriovalpo.cl)
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# -----------------------
# 01 : Primera version at Viernes 02/06/2000
# 1.1 23/06/2000 - Agrega parseo / desparseo de BOLD (%b%).
#                - Corrije parseo de URLs para que se acepte cualquier caracter
#                  dentro del parentesis y permita anidar URLs dentro de tags <B>.

# 1.2 30/06/2000 - Agrega opcion de parsear urls en target blank o por defecto.
# 1.3 05/07/2000 - Agrega segmento de codigo a funcion 'parser_area' para parsear archivos realmedia en la portada.
# 1.4 28/07/2000 - Se corrige expresion regular (no estaba funcionando la anterior)
# 1.5 05/07/2000 - Agrega capacidad de parsear archivos asociados en la portada.
# 1.6 18/08/2000 - Soporte para PRONTUS-04NA y PRONTUS-03NA.
# 1.7 15/09/2000 - Se incorpora capacidad para que se parseen en las portadas marcas de campo del tipo %%varx(clase, nrochars)%%.
# 1.8 20/09/2000 - Si la URL comienza con _http implica target = self, si no se pone el '_' implica target='_blank'.
# 1.9 21/09/2000 - correccion de bug (declaracion repetida 2 veces).
# 1.91 22/09/2000 - Incorporacion de tag %%FIL%% en las portadas, el que corresponde al nombre del archivo pero sin extension.
# 1.10 07/11/2000 - Correccion de bug al ordenar por prioridad.
# 1.11 24/11/2000 - En la carga del archivo de configuracion (funcion load_config() ) se elimina parametro 'cliente' y se agregan los serv. permitidos para validacion de referers.
# Ademas se agrega al cfg el parametro PRONTUS_KEY el cual se chequea primero para ver si es valido
# usando la funcion check_prontus_key() y luego para ver si el octavo digito coincide con el nro. del prontus
# indicado en el parametro TIPO_PRONTUS.
# Ademas se valida la existencia del arch. de cfg.
# Ademas se valida el referer aqui mismo.
# 1.12 24/11/2000 - Antes de escribir la portada, se agrega al final del head un meta tag con el prontus_key.
# 1.13 24/11/2000 - Se agrega rutina check_prontus_key();
# 1.14 05/12/2000 - Modificaciones en rutina mini_escape_html para soportar marcas del tipo %HTML%...%/HTML%.
# 1.15 06/12/2000 - Correcciones en retorno de parametros de la funcion Load_config()
# 1.16 06/12/2000 - Correcciones en timbraje del PRONTUS_KEY.
# 1.17 06/12/2000 - Se eliminan pies de fotos y tablas insertadas entre medio del texto, al momento de desplegar este texto en la portada.
# 1.18 29/12/2000 - Se cambian los &nbsp; por \s antes de realizar el conteo de palabras.
# 1.19 02/01/2001 - Correccion a mini_escape_html para soportar caracteres del tipo &#0987;
# 1.20 02/01/2001 - Nueva validacion al cargar arch. de conf. prontus.
# 1.21 15/05/2001 - Correccion a parser_area para soportar caracteres del tipo &#0987; en las portadas.
# 1.22 15/05/2001 - Extensiones para Prontus 5. Estas modificaciones se aplicaron antes de escribir este comentario.
# 1.23 16/05/2001 - Modificaciones para parametrizacion del protocolo (http o https) a traves del arch. de conf.
# 1.24 16/05/2001 - Revision general de detalles de forma.

# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0

# 7.0 - 20/12/2001 - Extensiones p7 :
#   . "- Agrega marca a la portada para que inserte los menús de páginas con subtítulos.<br>"
#     . "- Perfilación de periodistas en lista de artículos para permitir artículos personales<br>"
#     . "- Capacidad para borrar fotos, asocfile y realmedia<br>"
#     . "- Linkeo de URLs https<br>"

# Prontus 8.0 - 01/08/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# Prontus 8.1 - 09/09/2002 - YCH - Soporte windows media. Ver detalles en /release_prontus81.txt
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN LIBRERIA-------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

package lib_prontus;

use glib_html_02; # Prontus 6.0
use glib_fildir_02;
use glib_hrfec_02;
use glib_str_02;
use glib_dbi_02;
use prontus_varglb;
use File::Copy;
use XML::Parser; # rotulos tax
use Artic;
use lib_cookies;
use Session;

our $CRLF = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/; # usar asi: $buffer =~ s/$CRLF/<p>/sg;
our $IF_OPERATORS = qr/>=|<=|!=|==|=|>|<| le | ge | ne | eq | gt | lt |~/;


our $DEBUG_FECHAS = 0;

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

sub setUtf8 {
# Setea utf8 para ambiente web
    if ($ENV{'DOCUMENT_ROOT'}) {
        binmode(STDOUT, ":utf8");
    };
};
# ---------------------------------------------------------------
sub check_dirs {
my ($dir);


  # TEMPLATES ARTICULOS
  # Dir. de tpl de las pags de los articulos
  $dir = $prontus_varglb::DIR_SERVER .
         $prontus_varglb::DIR_TEMP .
         $prontus_varglb::DIR_ARTIC .
         $prontus_varglb::DIR_FECHA .
         $prontus_varglb::DIR_PAG;



  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de plantillas de articulos no es válido");
    exit;
  };

  if (!(&check_contenido_dir($dir))) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de plantillas de artículos está vacío, éste debe contener al menos una plantilla");
    exit;
  };



  # DESTINO ARTICULOS -----------------------------
  # Dir a los articulos existentes hasta antes de la fecha
  $dir = $prontus_varglb::DIR_SERVER .
         $prontus_varglb::DIR_CONTENIDO .
         $prontus_varglb::DIR_ARTIC;

  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio destino de artículos no es válido");
    exit;
  };


  # TEMPLATES TAXONOMIA
  if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^[1-3]$/) {
    $dir = $prontus_varglb::DIR_SERVER .
           $prontus_varglb::DIR_TEMP .
           $prontus_varglb::DIR_TAXONOMIA;

    if ( ! (&glib_fildir_02::check_dir($dir)) ) {
      print "Content-Type: text/html\n\n";
      &glib_html_02::print_pag_result("Error","El directorio de plantillas de art. relacionados no es válido");
      exit;
    };
    if ( ! (&check_contenido_dir($dir)) ) {
      print "Content-Type: text/html\n\n";
      &glib_html_02::print_pag_result("Error","El directorio de plantillas de art. relacionados está vacío. Debe haber a lo menos una plantilla.");
      exit;
    };

  };

  # DESTINO TAXONOMIA
  if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^[1-3]$/) {
    $dir = $prontus_varglb::DIR_SERVER .
           $prontus_varglb::DIR_CONTENIDO .
           $prontus_varglb::DIR_TAXONOMIA;

    if ( ! (&glib_fildir_02::check_dir($dir)) ) {
      print "Content-Type: text/html\n\n";
      &glib_html_02::print_pag_result("Error","El directorio de destino de art. relacionados no es válido");
      exit;
    };
  };

  # TEMPLATE portada tipo tema
  if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^[1-3]$/) {
    $dir = $prontus_varglb::DIR_SERVER .
           $prontus_varglb::DIR_TEMP .
           $prontus_varglb::DIR_PTEMA;

    if ( ! (&glib_fildir_02::check_dir($dir)) ) {
      print "Content-Type: text/html\n\n";
      &glib_html_02::print_pag_result("Error","El directorio de plantillas de portadas tipo tema no es válido");
      exit;
    };

  };

  # DESTINO portadas tipo tema
  if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^[1-3]$/) {
    $dir = $prontus_varglb::DIR_SERVER .
           $prontus_varglb::DIR_CONTENIDO .
           $prontus_varglb::DIR_PTEMA;

    if ( ! (&glib_fildir_02::check_dir($dir)) ) {
      print "Content-Type: text/html\n\n";
      &glib_html_02::print_pag_result("Error","El directorio de destino de portadas tipo tema no es válido");
      exit;
    };
  };

  # DIRS. DE USO INTERNO  -----------------------------
  # Dir de los dbm
  if ( ! (&glib_fildir_02::check_dir($prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_DBM)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de data de usuarios no es válido");
    exit;
  };

  # Dir de los logs
  if ( ! (&glib_fildir_02::check_dir($prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CPAN . '/log')) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de logs de Prontus no es válido");
    exit;
  };

  # Escribe htaccess en el dir de los LOGs para permitir listar directorio
  # &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/log/.htaccess", "Options +Indexes");



  if ( ! (&glib_fildir_02::check_dir($prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CPAN . '/procs')) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de logs de procesos masivos de Prontus no es válido");
    exit;
  };



  # Dir cpan
  if ( ! (&glib_fildir_02::check_dir($prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CPAN)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio cpan no es válido");
    exit;
  };

  # Dir cpan/fid
  if ( ! (&glib_fildir_02::check_dir($prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CPAN . '/fid')) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de FIDs no es válido");
    exit;
  };
  if (!(&check_contenido_dir($prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CPAN . '/fid'))) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error", "El directorio de FIDs está vacío, éste debe contener al menos un FID");
    exit;
  };

  # Escribe htaccess en el dir de los FIDs para prohibir acceso http a este.
  &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/fid/.htaccess", "Order Allow,Deny\nDeny from all");

  # Escribe htaccess para prohibir acceso http a TODO CFG QUE HAYA EN pRONTUS.
  if (! -s "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/.htaccess") {
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/.htaccess", "<FilesMatch \"\\\.(cfg)\$\">\nDeny from all\n</FilesMatch>");
  };


  # Dir CORE
  $core_dir = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE;
  if ( ! (&glib_fildir_02::check_dir($core_dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio cpan no es válido");
    exit;
  };


#  # Archivos del CORE
#  my ($core_file) = "$core_dir/prontus_edi_admin.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Form. de Administrador de Ediciones no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_edi_ficha.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Form. de Ficha de Edición no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_edi_otras.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Form. de Ediciones anteriores no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_art_admin.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Form. de lista de artículos no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_art_fset.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Frameset de lista de artículos no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_art_head.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Head de lista de artículos no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_index.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Página de control de acceso no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_menu.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Página de Menu principal no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_copy_spare_confirm.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Página de confirmación de copia de port. recambio no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_show_spares.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Página de despliegue de port. recambio no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_usr_admin.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Página de Adm. de usuarios no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_usr_ficha.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Página de Ficha de usuario no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_waiting.html";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","Página de espera no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/prontus_detect.js";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","JS no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/popup_port.js";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","JS no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/popup_tipart.js";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","JS no existe");
#    exit;
#  };
#
#  $core_file = "$core_dir/fechas.js";
#  if ( ! (-f $core_file) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","JS no existe");
#    exit;
#  };
#
#
#
#  # Dir imag
#  if ( ! (&glib_fildir_02::check_dir("$core_dir/imag")) ) {
#    print "Content-Type: text/html\n\n";
#    &glib_html_02::print_pag_result("Error","El directorio de imagenes no es válido");
#    exit;
#  };


  # TEMPLATES DE PORTADAS
  $dir = $prontus_varglb::DIR_SERVER .
         $prontus_varglb::DIR_TEMP .
         $prontus_varglb::DIR_EDIC .
         $prontus_varglb::DIR_NROEDIC .
         $prontus_varglb::DIR_SECC;

  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de plantillas de portadas no es válido");
    exit;
  };

  if (!(&check_contenido_dir($dir))) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error", "El directorio de plantillas de portadas está vacío, éste debe contener al menos un template");
    exit;
  };

  # DIR TEMPLATES DE PORTADAS RECAMBIO
  $dir = $prontus_varglb::DIR_SERVER .
         $prontus_varglb::DIR_TEMP .
         $prontus_varglb::DIR_EDIC .
         $prontus_varglb::DIR_NROEDIC .
         $prontus_varglb::DIR_SPARE;

  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de plantillas de portadas de recambio no es válido");
    exit;
  };




  # Tpls. repetidos.
  if (&tpls_duplicados($dir)) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","Una o más plantillas de portada está repetida dentro del mismo directorio pero con extensión distinta");
    exit;
  };

  # Dir de TEMPLATE de homepages.
  $dir = $prontus_varglb::DIR_SERVER .
         $prontus_varglb::DIR_TEMP .
         $prontus_varglb::DIR_EDIC .
         $prontus_varglb::DIR_NROEDIC .
         $prontus_varglb::DIR_HPAGES;

  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de plantilla de la home page de ediciones no es válido");
    exit;
  };

  # Archivo Template de homepage de edicion.
  my $nom_tpl_home = "$dir/$prontus_varglb::INDEX_EDIC"; # 8.0
  if (! -f $nom_tpl_home) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","Plantilla de homepage de edicion no existe");
    exit;
  };






  # DESTINO EDICIONES
  $dir = $prontus_varglb::DIR_SERVER .
         $prontus_varglb::DIR_CONTENIDO .
         $prontus_varglb::DIR_EDIC;

  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de destino de ediciones no es válido");
    exit;
  };



  # Pagina de inicializacion para las portadas en construccion.
  if ( ! (-f "$prontus_varglb::DIR_SERVER$prontus_varglb::RELDIR_BASE/$prontus_varglb::PRONTUS_ID/$prontus_varglb::PAG_WORKING") ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","Pagina para portada 'en construcción' no existe");
    exit;
  };



  # Dir. destino de Edicion unica
  $dir = $prontus_varglb::DIR_SERVER .
         $prontus_varglb::DIR_CONTENIDO .
         $prontus_varglb::DIR_EDIC .
         $prontus_varglb::DIR_UNICAEDIC;

  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de edición única no es válido");
    exit;
  };

  $dir .= $prontus_varglb::DIR_SECC;
  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de destino de las portadas de la edición única no es válido");
    exit;
  };

  # Dir destino de los xml de portada de la ed. unica
  $dir =~ s/$prontus_varglb::DIR_SECC$/\/xml/;
  # print STDERR "alfa[$dir]\n";
  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de destino del xml de las portadas de la edición única no es válido");
    exit;
  };

  # Dir destino de los rss de portada de la ed. unica
  $dir =~ s/\/xml$/\/rss/;
  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de destino de los rss de las portadas de la edición única no es válido");
    exit;
  };

  # Escribe htaccess en el dir de plantillas para prohibir acceso http a este.
  &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_TEMP/.htaccess", "Order Allow,Deny\nDeny from all");

};

# ---------------------------------------------------------------
sub check_contenido_dir {
# Chequea que dentro del dir pasado por paramtero haya por lo menos 1 archivo.
my ($ruta_dir) = $_[0];
my (@lisdir, $k);

  @lisdir = &glib_fildir_02::lee_dir($ruta_dir);
  @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

  foreach $k (@lisdir) {
    if (-f "$ruta_dir/$k") {
      return 1; # encuentra a lo menos un archivo valido dentro del directorio.
    };
  };

  return 0;

};

# ---------------------------------------------------------------
sub tpls_duplicados {
# Chequea que dentro del dir pasado por paramtero, si hay mas de un tpl, no tengan el mismo nombre y distinta extension.
my ($ruta_dir) = $_[0];
my (@lisdir, $k, %existentes);

  @lisdir = &glib_fildir_02::lee_dir($ruta_dir);
  @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

  foreach $k (@lisdir) {
    if (-f "$ruta_dir/$k") {
      $nombre = '';
      if ($k =~ /(.+)\..+$/) {
        $nombre = $1;
        $existentes{$nombre}++;
      };
      if ($existentes{$nombre} > 1) {
        return 1; # hay tpls duplicados.
      };
    };
  };

  return 0;

};


# --------------------------------------------------------------------
sub parse_param_edi {
# Sustituye en el texto las variables correspondientes a los parametros de la edicion.

  my $buf = $_[0]; $buf =~ s/%25%25/%%/sg; # Prontus 6.0
  my $edic = $_[1];

  # Rescatar extension del tpl. de homepage, con punto.
  my $ext_hp = &get_ext_hpage(); # 8.0

  my $dir_homepages = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_HPAGES;
  my $text_html = &glib_fildir_02::read_file("$dir_homepages/$edic" . $ext_hp); # 8.0
  if ($text_html !~ /\n/) { # 8.0
    $text_html =~ s/\r/\n/sg;
  };



  my $nro_params =  scalar @prontus_varglb::EDPARAM;
  my ($nom_campo, $i, $valor, $marca_izq, $marca_der, $sustit);

  for ($i=2; $i < $nro_params; $i=$i+1) {
    $nom_campo = $prontus_varglb::EDPARAM[$i];
    $nom_campo =~ s/,.*//; # sacar el indicador NOLISTAR en caso que venga.
    $valor = &get_valcampo_html($nom_campo, $text_html);

    # Sustituir marcas tipo <!--xx-->yy<!--/xx-->
    $marca_izq = '<!--' . $nom_campo . '-->';
    $marca_der = '<!--/' . $nom_campo . '-->';
    $sustit = $marca_izq . $valor . $marca_der;
    $buf =~ s/$marca_izq.*?$marca_der/$sustit/isg;

    # Sustituir marcas tipo %%xx%%
    $buf =~ s/%%$nom_campo%%/$valor/ig;

  };

  return $buf;
};

# ---------------------------------------------------------------
sub remove_front_string {
# Elimina un substring al comienzo de un string
    my $string = shift;
    my $substring = shift;
    $string =~ s/^$substring//is;
    return $string;
};

# ---------------------------------------------------------------
# 8.0
sub get_nomfile {
# Obtener el nombre del primer archivo que figura en el directorio.
# Param: 0) Path al Directorio
# Retorna : el nombre del archivo correspondiente  sin path y c/extension o '' en caso de que no se encuentre ningun archivo.

    my $dir = shift;

    my (@entries, $entry);

    @entries = &glib_fildir_02::lee_dir($dir);

    foreach $entry (@entries) {

        if (($entry !~ /^\./g) and ($entry !~ /^preview/ig) and (-f "$dir/$entry")) {
            return $entry;
        };
    };
    return '';
};

# ---------------------------------------------------------------
# 8.0
sub get_ext_hpage {
# retorna extension del tpl. de homepage de edicion, con punto.
    my $nom_tpl_home = &get_nomfile($prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_TEMP . $prontus_varglb::DIR_EDIC . $prontus_varglb::DIR_NROEDIC . $prontus_varglb::DIR_HPAGES);
    my $ext = &get_file_extension($nom_tpl_home);
    if ($ext) {
        return ".$ext";
    };
    return '';
};

# ---------------------------------------------------------------
sub get_file_extension {
# Obtiene extension sin punto
    my $nomfile = shift;
    return $1 if ($nomfile =~ /\.(\w+)$/);
    return '';
};
# ---------------------------------------------------------------
sub check_extension {
# checkea la extension contra un string (separados por coma)
    my $nomfile = shift;
    my $str2check = shift;

    my $file_extension = lc &lib_prontus::get_file_extension($nomfile);
    return 0 if ($str2check !~ /(^|,)$file_extension($|,)/);
    return 1;
};

# ---------------------------------------------------------------
sub split_nom_y_extension {
    my $nomfile = shift;
    return ($1, $2) if ($nomfile =~ /([\w\-\d]+)\.(\w+)$/);
    return '';
};
# ---------------------------------------------------------------
sub get_dirfecha_by_ts {
    my $ts = shift;
    if ($ts =~ /^(\d{8})/) {
        return $1;
    };
    return '';
};

# ---------------------------------------------------------------
# Prontus 6.0
sub open_dbm_files {
  # Cargar en los hash desde los archivos de textos
  # USERS
  my ($users_id, $users_nom, $users_usr, $users_psw, $users_perfil, $users_email);

  if (!(-f "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/users.txt")) {
    open (ARCHIVO,">$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/users.txt") || return 'no_ok';
    print ARCHIVO "||\n";
    close ARCHIVO;
  };

  if (!(-f "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/artusers.txt")) {
    open (ARCHIVO,">$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/artusers.txt") || return 'no_ok';
    print ARCHIVO "||\n";
    close ARCHIVO;
  };

  if (!(-f "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/portusers.txt")) {
    open (ARCHIVO,">$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/portusers.txt") || return 'no_ok';
    print ARCHIVO "||\n";
    close ARCHIVO;
  };

  # print "Content-Type: text/html\n\n"; # debug
  open (ARCHIVO,"<$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/users.txt") || return 'no_ok';
  while (<ARCHIVO>) {
    if ($_ !~ /^\|\|/) {
      $_ =~ s/\n$//;
      # print "pesosraya[$_]<br>";
      ($users_id, $users_nom, $users_usr, $users_psw, $users_perfil, $users_email) = split(/\|/, $_);
      $prontus_varglb::USERS{$users_id} = $users_nom . '|' . $users_usr . '|' . $users_psw . '|' . $users_perfil . '|' . $users_email;
      # print "linea cargada[$users_id y $prontus_varglb::USERS{$users_id}]<br>"
    };
  };
  close ARCHIVO;

  # ARTUSERS
  my ($tipart, $usr1);
  open (ARCHIVO,"<$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/artusers.txt") || return 'no_ok';
  while (<ARCHIVO>) {
    if ($_ !~ /^\|\|/) {
      $_ =~ s/\n$//;
      ($tipart, $usr1) = split(/\|/, $_);
      $prontus_varglb::ARTUSERS{$tipart . '|' . $usr1} = 'filler';
    };
  };
  close ARCHIVO;

  # PORTUSERS
  my ($port, $usr2);
  open (ARCHIVO,"<$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/portusers.txt") || return 'no_ok';
  while (<ARCHIVO>) {
    if ($_ !~ /^\|\|/) {
      $_ =~ s/\n$//;
      ($port, $usr2) = split(/\|/, $_);
      $prontus_varglb::PORTUSERS{$port . '|' . $usr2} = 'filler';
    };
  };
  close ARCHIVO;

  return 'ok';
};
# ---------------------------------------------------------------
# Prontus 6.0
sub close_dbm_files {
my ($k);
my ($users_id, $users_nom, $users_usr, $users_psw, $users_perfil, $users_email, $linea);
my ($tipart, $port, $usr1, $usr2, $buffer);

  # Salvar los hash a los archivos de texto.
  # USERS
  $linea = '';
  $buffer = '';
  foreach $k (sort { $a <=> $b } keys %prontus_varglb::USERS) {
    $users_id = $k;
    ($users_nom, $users_usr, $users_psw, $users_perfil, $users_email) = split /\|/, $prontus_varglb::USERS{$k};
    $linea = $users_id . '|' . $users_nom . '|' . $users_usr . '|' . $users_psw . '|' . $users_perfil . '|' . $users_email . "\n";
    $buffer .= $linea;
  };
  if ($buffer) {
    &File::Copy::copy("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/users.txt", "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/users.bak");
    open (ARCHIVO,">$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/users.txt") || return 'no_ok';
    print ARCHIVO $buffer;
    close ARCHIVO;
  };

  # ARTUSERS
  $linea = '';
  $buffer = '';
  foreach $k (keys %prontus_varglb::ARTUSERS) {
    ($tipart, $usr1) = split /\|/, $k;
    $linea = $tipart . '|' . $usr1 . "\n";
    $buffer .= $linea;
  };
  if ($buffer) {
    &File::Copy::copy("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/artusers.txt", "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/artusers.bak");
    open (ARCHIVO,">$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/artusers.txt") || return 'no_ok';
    print ARCHIVO $buffer;
    close ARCHIVO;
  };


  # PORTUSERS
  $linea = '';
  $buffer = '';
  foreach $k (keys %prontus_varglb::PORTUSERS) {
    ($port, $usr2) = split /\|/, $k;
    $linea = $port . '|' . $usr2 . "\n";
    $buffer .= $linea;
  };
  if ($buffer) {
    &File::Copy::copy("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/portusers.txt", "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/portusers.bak");
    open (ARCHIVO,">$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/portusers.txt") || return 'no_ok';
    print ARCHIVO $buffer;
    close ARCHIVO;
  };

};
# ---------------------------------------------------------------
# Prontus 6.0
sub get_glosa_perfil {
  if ($prontus_varglb::USERS_PERFIL eq 'P') { return 'Redactor';}
  elsif ($prontus_varglb::USERS_PERFIL eq 'E') { return 'Editor';}
  elsif ($prontus_varglb::USERS_PERFIL eq 'A') { return 'Administrador';}
  else { return '';};
};
# ---------------------------------------------------------------
# Prontus 6.0
sub ed_vigente {
# Verifica si la ed. consultada es o no la vigente, revisando si el nro
# de esta es el q figura en el archivo ed_vigente.txt

  my $nombre_ed = $_[0];
  my $pag;

  $pag = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/ed_vigente.txt");

  if ($pag =~ /$nombre_ed/s) {
    return 'SI';
  }
  else {
    return 'NO';
  }
}
# ---------------------------------------------------------------

# 1.22
sub check_user {
    # Chequea que el username pasado por parametro exista en el hash de USERS y retorna el USERS_ID y el USERS_PERFIL.
    # Si no se logra autenticar, retorna el id vacio y en el perfil retorna el mesnaje de error.
    my ($username, $crypted_pass);
    my ($key, $value, %cookies);
    my ($id, $perfil);

    my $redir = $_[0]; # redireccion en caso de que no se detecte una sesion activa.

    %cookies = &lib_cookies::get_cookies();
    $username = $cookies{'USERS_USR_' . $prontus_varglb::PRONTUS_ID};
    $crypted_pass = $cookies{'KEY_' . $prontus_varglb::PRONTUS_ID}; # CLAVE PRONTUS ENCRIPTADA
    $prontus_varglb::USERS_USR = $username;

    my $sess_obj = Session->new(
                    'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                    'document_root'     => $prontus_varglb::DIR_SERVER)
                    || die("Error inicializando objeto Session: $Session::ERR\n");
    if ($sess_obj->{id_session} eq '') {
        if ($redir) {
            # redirecciona al login.
            #~ print "Location: ../$prontus_varglb::PRONTUS_ID/cpan/core/prontus_index.html\n\n";
            print "Content-Type: text/html\n\n";
            print "<script type='text/javascript'>window.location.href='/$prontus_varglb::PRONTUS_ID/cpan/core/prontus_index.html';</script>";
            exit;
        } else {
            return ('', 'No se detectó una sesión activa');
        };
    };

    # Si esta este archivo, solo deja pasar con user admin y la pass contenida en el.
    # Los demas usuarios son bloqueados.
    my ($flag_sysadmin) = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/users/prontus_flag_sysadmin.txt";
    if (-f $flag_sysadmin) { # sysadmin
        my $pass_sysadmin = &glib_fildir_02::read_file($flag_sysadmin);
        # CVI - 05/07/2012 - Ahora se usa md5 para encriptar la contraseña
        my $crypted_sys_pass;
        if(length($crypted_pass) == 32) {
            $crypted_sys_pass = md5_hex($pass_sysadmin);
        } else {
            $crypted_sys_pass = crypt($pass_sysadmin, 'Av');
        }
        if ( ($username eq 'admin') && ($crypted_pass eq $crypted_sys_pass) ) {
            return (1, 'A');
        } else {
            return ('', $prontus_varglb::MSG_BLOQUEOSYSADMIN); # sysadmin es para mostrar mensaje mas amigable
        };
    } else { # users normales
        if (&lib_prontus::open_dbm_files() ne 'ok') {
            return ('', 'No fue posible cargar archivos de privilegios de usuario');
            print STDERR "No fue posible cargar archivos de privilegios de usuario.\n";
        };

        foreach $key (keys %prontus_varglb::USERS) {
            # print "key[$key] y value[$value]<br>";
            $value = $prontus_varglb::USERS{$key};
            my ($users_nom, $users_usr, $users_psw, $users_perfil) = split /\|/, $value;
            if (($users_usr eq $username) && ($crypted_pass eq $users_psw)) {
                ($id, $perfil) = ($key, $users_perfil);
                last;
            };
        };
        $perfil = 'Usuario o Contraseña no válida.' if (!$id);
        return ($id, $perfil);
    };

};

# ---------------------------------------------------------------
sub check_fotos_from_ts {
# Chequea si el articulo tiene fotos o no
    my ($ts) = shift;
    my $dirfecha = $ts;
    $dirfecha =~ s/\d{6}$//;

    my $fullpath_xml = $prontus_varglb::DIR_SERVER .
                       $prontus_varglb::DIR_CONTENIDO .
                       $prontus_varglb::DIR_ARTIC .
                       "/$dirfecha" .
                       "/xml" .
                       "/$ts.xml";
    # warn($fullpath_xml);
    my $buff_xml_data = lib_prontus::get_xml_data($fullpath_xml);
    if($buff_xml_data =~ /<foto_(\d+)>(.*?)<\/foto_\1>/is) {
        my $num = $1;
        my $buff = $2;
        if($buff =~ /<_nomfoto_$num>(.+?)<\/_nomfoto_$num>/) {
            my $foto = $1;
            my $fulldir_fotos = $this->{dst_pags};
            # warn "fulldir_vista1[$fulldir_vista]";
            no warnings 'syntax'; # para evitar el msg "\1 better written as $1"
            $fulldir_fotos =~ s/(\/site\/artic\/\d{8}\/)pags/\1imag/;
            # warn "se encontro foto [$fulldir_fotos$foto]";
            return 1;
        }
    }
    return 0;
};

# ---------------------------------------------------------------
sub check_artic_pub {
# Chequea si el articulo esta publicado en alguna portada
    my ($ts, $hash) = @_;

#    my @array = keys %hash;
#    warn('Portadas: ['.$ts.']['.$#array.']');

    if($hash->{$ts}) {
        my $ediciones;
        foreach my $edic (keys %{$hash->{$ts}}) {
            # warn('edic: '.$edic.', edics: '.$hash->{$ts}->{$edic});
            $ediciones = $ediciones . "<h3>Edici&oacute;n $edic:</h3><ul>";
            my $portadas;
            foreach my $port (keys %{$hash->{$ts}->{$edic}}) {
                $portadas = $portadas . '<li>' . $port . '</li>';
            }
            $ediciones = $ediciones . $portadas . '</ul><br/>';
        }

#        foreach my $clave (@ports) {
#            $portadas =
#        }
        #~ warn('Ediciones: '.$ediciones);
        return $ediciones;
    }
    return '';
};

# ---------------------------------------------------------------
sub load_artic_pubs {
# Carga un hash con los articulos publicados en las últimas portadas

    # procesa edicion, vigente, la ultima y la base.
    my (@ediciones) = &lib_prontus::get_edics4update();
    my %hash_artics;

    # Solo si la edicion es base, se guardan sólo las portadas base
    my %ports_base;
    if($prontus_varglb::MULTI_EDICION eq 'SI') {
        foreach my $port_base (@prontus_varglb::BASE_PORTS) {
            $ports_base{$port_base} = 1;
            #~ print STDERR "Base: $port_base\n";
        }
    } else {
        %ports_base = %prontus_varglb::PORT_PLTS;
    }

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

            # No se toman en cuenta las que no esten en el CFG
            next unless ($prontus_varglb::PORT_PLTS{$port});

            if($prontus_varglb::MULTI_EDICION eq 'SI' && $edic eq 'base') {
                next unless($ports_base{$port});
            }

            # portada en el site
            $arch_seccion = "$pathdir_seccs/$port";

            my ($arch_xml) = $arch_seccion;
            $arch_xml =~ s/\/port\/(\w+?)\.\w*$/\/xml\/\1\.xml/;

            next if ((! -f $arch_xml) || ($port =~ /^preview/i));

            $text_seccion = &glib_fildir_02::read_file($arch_xml);
            $text_seccion = &lib_prontus::ajusta_crlf($text_seccion);

            # Rescatar la info de c/artic de la port actual
            while ($text_seccion =~ /<rowartic>[ \n]*?<dir>(\d+?)<\/dir>[ \n]*?<file>(.*?)<\/file>[ \n]*?<area>(\d*?)<\/area>[ \n]*?<ord>(\d*?)<\/ord>[ \n]*?(<vb>(\w*?)<\/vb>)?[ \n]*?<?i?n?>?([\w\/\-]*?)<?\/?i?n?>?[ \n]*?<?o?u?t?>?([\w\/\-]*?)<?\/?o?u?t?>?[ \n]*?<?p?u?b?>?(\d?)<?\/?p?u?b?>?[ \n]*?<\/rowartic>/isg) {

                my ($dirfecha,$art,$area,$prio,$pub,$ext_art,$vb) = '';
                ($dirfecha,$art,$area,$prio,$vb,$pub) = ($1,$2,$3,$4,$6,$9);

                $hash_artics{$art}{$edic}{$port} = 1;
            };

        };
    };

    return %hash_artics;
};



# ---------------------------------------------------------------
sub port_asoc {
  # Ve si la portada esta asignada al usuario.
  # Se requiere que ya se haya pasado por la funcion &lib_prontus::check_user()
  my ($p) = $_[0]; # nombre de la portada, con exte pero sin path.
  my ($key2);
  foreach $key2 (keys %prontus_varglb::PORTUSERS) {
    my ($port, $usr) = split /\|/, $key2;
    # print STDERR "\n usr[$usr] y prontus_varglb::USERS_ID[$prontus_varglb::USERS_ID] y port[$port] y p[$p]"; # debug
    if ( ($usr eq $prontus_varglb::USERS_ID) and ($port eq $p) ) {
      # print STDERR "\n ok";
      return 1;
    };
  };
  # print STDERR "\n NO ok";
  return 0;
};
# ---------------------------------------
sub check_prontus_key { # 8.0
  # Funcion que checkea el numero de serie prontus a partir de la IP o URL del sitio + version prontus + numero random sacado del lugar octavo de la serie.
  # Param entrada:
  # 0) url o ip
  # 0) version prontus (1-4)
  # 0) Nro. random original (1-9)
  # Param salida:
  # Param salida:
  # 0) key generada de 16 digitos (xxxx-xxxx-xxxx-xxxx).


  my ($entrada, $input_prontus, $random) = ($_[0], $_[1], $_[2]); # variable que debe contener 8 digitos.
  my (@input, @output, @factor, $cont_input, $cont_factor, @letras);


  @letras = ('Z', 'Y', 'X', 'W', 'A', 'B', 1, 'C', 'D', 2, 'E', 'I', 'M', 'T', 'P', 'V', 'J', 5, 'K', 'L', 6, 'S', 'N', 7, 'O', 'R', 3, 'G', 'H', 4, 'U', 8, 'Q', 'F', 9); # 35 elementos.


  for ($cont_input = 0; length($entrada) >= $cont_input; $cont_input+= 7) {
    $input[0] += ord(substr($entrada, $cont_input + 0, 1));
    $input[1] += ord(substr($entrada, $cont_input + 1, 1));
    $input[2] += ord(substr($entrada, $cont_input + 2, 1));
    $input[3] += ord(substr($entrada, $cont_input + 3, 1));
    $input[4] += ord(substr($entrada, $cont_input + 4, 1));
    $input[5] += ord(substr($entrada, $cont_input + 5, 1));
    $input[6] += ord(substr($entrada, $cont_input + 6, 1));
    $input[7] += ord(substr($entrada, $cont_input + 7, 1));
  };


  for ($cont_input = 0; 7 >= $cont_input; $cont_input++) {
    $input[$cont_input] *= $random; # 01a.
  };


  $input[4] = $random;
  $input[3] = $input_prontus; # Numero version prontus.


  # print "\n\n"; # debug
  @factor = (
                [329.1, 13.87, 0.17, 4.65, 27.3, 83, 2, 37.7],
                [436, 45.07, 13, 22.22, 0.1, 21, 4, 7],
                [901.7, 17.17, 5.7, 45, 27.98, 30, 94, 14],
                [6.9, 195.87, 87, 14.5, 200.17, 77, 60, 113],
                [8.3, 23, 12, 13, 2.17, 120, 694, 47],
                [4161.3, 0.35, 50, 45, 27, 777, 1, 15],
                [2213.4, 0.87, 29, 1.45, 4.99, 24, 19, 36],
                [7710.9, 3157, 33, 5.21, 79.1, 79, 34.34, 62]
  );


  for ($cont_input = 0; $cont_input <= 7; $cont_input++) {
    for ($cont_factor = 0; $cont_factor <= 7; $cont_factor++) {
      $output[$cont_input] += $input[$cont_input] * $factor[$cont_input][$cont_factor];
    };


    # print "in $cont_input ---$input[$cont_input]---\n";
    $input[$cont_input] = $input[$cont_input] % 29 if $input[$cont_input] > 34;


    while ($input[$cont_input] > 34) {
      $input[$cont_input] = $input[$cont_input] - 17;
    };


    $input[$cont_input] = $letras[$input[$cont_input]];




    $output[$cont_input] = $output[$cont_input] % 40;


    while ($output[$cont_input] > 34) {
      $output[$cont_input] = $output[$cont_input] - 35;
    };


    $output[$cont_input] = $letras[$output[$cont_input]];
    $output[$cont_input] = 0 if $output[$cont_input] eq '';


    # print "in $cont_input ---$input[$cont_input]---\n";
  };

  return "$input[6]$input[1]$input[0]$input[5]" . '-' . "$input[7]$input[2]$input[4]$input[3]" . '-' . "$output[0]$output[1]$output[2]$output[3]" . '-' . "$output[4]$output[5]$output[6]$output[7]";

};

# -------------------------------------------------------------------------#
# 1.11
sub load_config {
# Carga variables de configuracion del autopublicador desde un archivo de texto.
# Param :
# 0) Path completo absoluto al archivo.
# Retorna los valores de c/u.


  my ($path_conf) = $_[0];

  my ($area_menu, $area_cont, $buffer, $tipo_prontus, $dir_contenido);
  my ($dir_temp, $dir_cpan, $i, $server, $prontus_key, $oct_dig, $oct_dig_tipoprontus, $sept_dig, $nro_prontus);
  my ($cfecha, $dir_dbm); # 1.22
  my ($prontus_id, $multied, $reldir_base, $dir_log); # Prontus 6.0
  my ($rtext); # rc15


  my $nomcfg;
  if ($path_conf =~ /(.*)\.cfg$/) {
    $nomcfg = $1;
  };

  if (not(-f "$nomcfg-id.cfg")) { # 1.22
    print STDERR "No se pudo localizar el Archivo de Configuración PRONTUS\n";
    print "Content-Type: text/html\n\n";
    print "<P>No se pudo localizar el Archivo de Configuraci&oacute;n PRONTUS";
    exit;
  };

  # Lee archivo de configuracion.
  my $errcfg;
  $errcfg = "[$nomcfg-art.cfg]" if (! -f $nomcfg . '-art.cfg');
  $errcfg = "[$nomcfg-port.cfg]" if (! -f $nomcfg . '-port.cfg');
  $errcfg = "[$nomcfg-bd.cfg]" if (! -f $nomcfg . '-bd.cfg');
  $errcfg = "[$nomcfg-var.cfg]" if (! -f $nomcfg . '-var.cfg');
  if ($errcfg) {
    print STDERR "No se pudo localizar el Archivo de Configuración PRONTUS $errcfg\n";
    print "Content-Type: text/html\n\n";
    print "<P>No se pudo localizar el Archivo de Configuraci&oacute;n PRONTUS $errcfg";
    exit;
  };

  $buffer = &glib_fildir_02::read_file($nomcfg . '-id.cfg') . "\n"
          . &glib_fildir_02::read_file($nomcfg . '-art.cfg') . "\n"
          . &glib_fildir_02::read_file($nomcfg . '-port.cfg') . "\n"
          . &glib_fildir_02::read_file($nomcfg . '-bd.cfg') . "\n"
          . &glib_fildir_02::read_file($nomcfg . '-tax.cfg') . "\n"
          . &glib_fildir_02::read_file($nomcfg . '-tag.cfg') . "\n"
          . &glib_fildir_02::read_file($nomcfg . '-list.cfg') . "\n"
          . &glib_fildir_02::read_file($nomcfg . '-usr.cfg') . "\n"
          . &glib_fildir_02::read_file($nomcfg . '-var.cfg') . "\n"
          . &glib_fildir_02::read_file($nomcfg . '-clustering.cfg') . "\n";

  $buffer =~ s/\r/\n/sg;
  # print STDERR "buffer[$buffer]";

  if ($buffer !~ /\w/) {
    print STDERR "Archivos de Configuración PRONTUS están vacíos.\n";
    print "Content-Type: text/html\n\n";
    print "<P>Archivos de Configuración PRONTUS están vacíos.";
    exit;
  };

  if ($buffer =~ m/\s*PRONTUS\_ID\s*=\s*("|')(.*?)("|')/) { # Prontus 6.0
    $prontus_id = $2;
  };

  $tipo_prontus = 'PRONTUS-04'; # AL FINAL SON TODOS PRONTUS 4 !!
#  if ($buffer =~ m/\s*TIPO\_PRONTUS\s*=\s*("|')(PRONTUS-\d\d)("|')/) { # 1.6
#    $tipo_prontus = $2;
#  };


  # Direcotrio relativo al sitio web donde se instalara el publicador.
  # Si no se especifica, se asume la raiz.
  if ($buffer =~ m/\s*RELDIR\_BASE\s*=\s*("|')(\/.*?)("|')/) {
    $reldir_base = $2;
    if ($reldir_base eq '/') {
      $reldir_base = '';
    };
  };

  my $prontus_log = 'SI'; # valor por defecto. # 7.0
  if ($buffer =~ m/\s*PRONTUS_LOG\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $prontus_log = $2;
  };

  my $friendly_urls = 'NO'; # valor por defecto.
  if ($buffer =~ m/\s*FRIENDLY_URLS\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $friendly_urls = $2;
  };

  my $friendly_urls_version = '1'; # valor por defecto.
  if ($buffer =~ m/\s*FRIENDLY_URLS_VERSION\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $friendly_urls_version = $2;
  };

  my $comentarios = 'NO'; # valor por defecto.
  if ($buffer =~ m/\s*COMENTARIOS\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $comentarios = $2;
  };
  $prontus_varglb::COMENTARIOS = $comentarios;


  # extensiones permitidas para uploads
  my $uploads_permitidos = $prontus_varglb::UPLOADS_PERMITIDOS_ORIG;
  my $uploads_permitidos_custom = '';
  if ($buffer =~ m/\s*UPLOADS_PERMITIDOS\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $uploads_permitidos_custom = $2;
  };
  if ($uploads_permitidos_custom =~ /^\w+(,\w+)*$/) {
    $prontus_varglb::UPLOADS_PERMITIDOS = $uploads_permitidos_custom;
  } else {
    $prontus_varglb::UPLOADS_PERMITIDOS = $uploads_permitidos;
  };


  my $uploads_extras = ''; # valor por defecto.
  if ($buffer =~ m/\s*UPLOADS_EXTRAS\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $uploads_extras = $2;
    if ($uploads_extras =~ /^\w+(,\w+)*$/) {
      $prontus_varglb::UPLOADS_PERMITIDOS .= '|' . $uploads_extras;
    };
  };

  while ($buffer =~ m/\s*MULTIVISTA\s*=\s*("|')(.+?)("|')/g) {
     $clave = $2;
     $prontus_varglb::MULTIVISTAS{$clave} = 1;
  };


  while ($buffer =~ m/\s*FORM\_PLTS\s*=\s*("|')(.*?:.*?)\((.*?)\)("|')/g) {
     $clave = $2;
     $valor = $3;
     $prontus_varglb::FORM_PLTS{$clave} = $valor;
     $prontus_varglb::FID_DEFAULT = $clave if (!$prontus_varglb::FID_DEFAULT);

  };

  # PORT_PLTS = 'inicio.html(vacante para portadas intercambiables, aca antes iba las spare, deprecatear eso)(plantillas paralelas)(portada para preview)'
  while ($buffer =~ m/\s*PORT\_PLTS\s*=\s*("|')(.+?)(\((.*?)\))?(\((.*?)\))?(\((.*?)\))?("|')/g) {
     $clave = $2;
     $valor = $4; # contenido del primer parentesis de la linea del cfg, donde iban las spare y ahora las intercambiables, NO SE USA POR MIENTRAS
     my $extra_ports = $6; # segundo (): portadas paralelas, ej: inicio2.php;inicio3.php
     my $port4preview = $8; # tercer (): portada para preview, por ejemplo, si la portada ppal es footer.html, entonces la port para preview podria ser inicio.html
     if ($clave !~ /^\w+\.\w+$/) {
        print STDERR "Error en CFG: Nombre de Portada [$clave] no es válido, debe contener sólo caracteres alfanuméricos, incluido el underscore. Además, debe tener una extensión válida.\n";
        print "Content-Type: text/html\n\n";
        print "<P>Error en CFG: Nombre de Portada [$clave] no es válido, debe contener sólo caracteres alfanuméricos, incluido el underscore. Además, debe tener una extensión válida.";
        exit;
     };
     $prontus_varglb::PORT_PLTS{$clave} = 1;
     $prontus_varglb::PORT_PLTS_NOM{$clave} = $valor; # el nombre de la portada.
     $prontus_varglb::PORT_PLTS_EXTRA{$clave} = $extra_ports; # las port paralelas
     $prontus_varglb::PORT_PLTS_PREVIEW{$clave} = $port4preview; # portada para preview
     # warn("[$clave]($valor)($extra_ports)($port4preview)");
  };

  if (keys(%prontus_varglb::PORT_PLTS) <= 0) {
    print STDERR "Error en CFG: No hay portadas definidas\n";
    print "Content-Type: text/html\n\n";
    print "<P>Error en CFG: No hay portadas definidas";
    exit;
  };

  while ($buffer =~ m/\s*BASE\_PORTS\s*=\s*("|')(.*?)("|')/g) {
     $valor = $2;
     push @prontus_varglb::BASE_PORTS, $valor;
  };

  # ports dd habilitadas.
  while ($buffer =~ m/\s*PORT\_DRAGANDROP\s*=\s*("|')(.*?)("|')/g) {
     $valor = $2;
     $prontus_varglb::PORT_DRAGANDROP{$valor} = 1;
  };


  my $server_name;
  if ($buffer =~ m/\s*PUBLIC\_SERVER\_NAME\s*=\s*("|')(.*?)("|')/) {
     $server_name = $2;
  };
  if (!$server_name) {
    $server_name = $ENV{'HTTP_HOST'};
  };
  $prontus_varglb::PUBLIC_SERVER_NAME = $server_name;
  if (!$prontus_varglb::IP_SERVER) {
    $prontus_varglb::IP_SERVER = $prontus_varglb::PUBLIC_SERVER_NAME
  };


  # Chequeo de prontus key.
  my ($novalid_key) = 1;
  my ($rtext_enabled);
  # print STDERR "\n buffer[$buffer]";
  while (($buffer =~ /\s*PRONTUS\_KEY\s*=\s*("|')(.*?)("|')/ig) and ($novalid_key)){
    # print STDERR "IN";
    # Si se esta ejecutando el editor de archivos prontus no chequea la key. # 8.0
    # Si no esta en ambiente web no cheqea la key.
    if (($ENV{'SCRIPT_NAME'} =~ /^prontus_edit_/) or ($ENV{'SERVER_NAME'} eq '')) {
      $novalid_key = 0;
      last;
    };
    # print STDERR "IN2";

    $prontus_key = $2;
    # print STDERR "\nprontus_key[$prontus_key]\n";

    $prontus_key =~ s/[^0-9A-Z]//g;


    # Ver si coincide el octavo digito con la version del prontus.
    $oct_dig = 'OC';
    if ($prontus_key =~ /\w\w\w\w\w\w\w(\w)/) {
      $oct_dig = $1;
    };
    $nro_prontus = '4'; # al final son todos prontus 4 !
#    $nro_prontus = '0';
#    if ($tipo_prontus =~ /PRONTUS-\d(\d)/) {
#      $nro_prontus = $1;
#    };
    $rtext_enabled = '';
    ($oct_dig_tipoprontus, $oct_dig, $rtext_enabled)  = &get_oct_dig($oct_dig);

    if ($oct_dig_tipoprontus ne $nro_prontus) {
      print STDERR "Requerimiento de Versión PRONTUS no autorizada, contáctese con AltaVoz SA.\n";
      print "Content-Type: text/html\n\n";
      print "<P>Requerimiento de Versión PRONTUS no autorizada, contáctese con AltaVoz SA.";
      exit;
    };

    # Validar autenticidad del serial. # 8.0
    $sept_dig = 'OC'; # random en el que se baso la key
    if ($prontus_key =~ /\w\w\w\w\w\w(\w)\w/) {
      $sept_dig = $1;
    };
    $sept_dig = &get_sept_dig($sept_dig);

    my ($k_name, $k_ip, $k_saddr, $k_laddr) = '';
    $k_name = &check_prontus_key(lc $ENV{'SERVER_NAME'}, $oct_dig, $sept_dig);
    $k_name =~ s/[^0-9A-Z]//g;

    $k_ip = &check_prontus_key($ENV{'HTTP_HOST'}, $oct_dig, $sept_dig);
    $k_ip =~ s/[^0-9A-Z]//g;

    if ($ENV{'SERVER_ADDR'} ne '') { # Solo Apache
      $k_saddr = &check_prontus_key($ENV{'SERVER_ADDR'}, $oct_dig, $sept_dig);
      $k_saddr =~ s/[^0-9A-Z]//g;
    };

    if ($ENV{'LOCAL_ADDR'} ne '') {
      $k_laddr = &check_prontus_key($ENV{'LOCAL_ADDR'}, $oct_dig, $sept_dig); # Solo IIS
      $k_laddr =~ s/[^0-9A-Z]//g;
    };

#    print STDERR "\n prontus_key[$prontus_key]";
#    print STDERR "\n k_name[$k_name]";
#    print STDERR "\n k_ip[$k_ip]";

    if (($k_name ne $prontus_key) and ($k_ip ne $prontus_key) and ($k_saddr ne $prontus_key) and ($k_laddr ne $prontus_key)) {
      $novalid_key = 1;
    }
    else {
      # print STDERR "valid\n";
      # clave valida
      $novalid_key = 0;
    };

  }; # while p.key




  if ($novalid_key) {
      # Clave no valida --> entonces es demo.
      # 8.0
      my $veces1 = abs(rand(5));
      if ($veces1 <= 0) { $veces1 = 1; };
      my $veces2 = abs(rand(5));
      if ($veces2 <= 0) { $veces2 = 1; };
      my $espacios = ' ' x $veces2;

      $prontus_varglb::STAMP_DEMO = '';
      $prontus_varglb::STAMP_DEMO_RSS = '';

      # 8.0
#      $prontus_varglb::STAMP_DEMO = 'Prontus X - ';
#
#      $prontus_varglb::STAMP_DEMO_RSS = "<item>\n"
#                                       . "<title>Prontus CMS (r)</title>\n"
#                                       . "<link>http://www.prontus.cl</link>\n"
#                                       . "<description>Contenido generado por Prontus</description>\n"
#                                       . "</item>\n";
      # print STDERR "No se encontro ninguna PK valida para este sitio. SERVER_NAME[$ENV{'SERVER_NAME'}] HTTP_HOST[$ENV{'HTTP_HOST'}]\n";
  }
  else {
    # clave valida
    $prontus_varglb::STAMP_DEMO = '';
    $prontus_varglb::STAMP_DEMO_RSS = '';
  };



  if ($buffer =~ m/\s*CONTROL\_FECHA\s*=\s*("|')(.*?)("|')/) { # 1.22 valores posibles : SI | NO
    $cfecha = $2;
  };

  $multied = 'NO'; # valor por defecto.
  if ($buffer =~ m/\s*MULTI\_EDICION\s*=\s*("|')(.*?)("|')/) { # 1.22 valores posibles : SI | NO
    $multied = $2;
  };



  my $peditor = 'SI'; # valor por defecto. # 7.0
  # if ($buffer =~ m/\s*PRONTUS_EDITOR\s*=\s*("|')(.*?)("|')/) { # SI | NO
  #  $peditor = $2;
  # };

  my $admin_port = 'NO'; # valor por defecto. # 7.0
  if ($buffer =~ m/\s*ADMIN_PORT\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $admin_port = $2;
  };

  my $verifinst = 'NO'; # valor por defecto. # 7.0
  if ($buffer =~ m/\s*VERIFICAR_INSTALACION\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $verifinst = $2;
  };

  my $actmasiva = 'NO'; # valor por defecto. # 7.0
  if ($buffer =~ m/\s*ACTUALIZACION_MASIVA\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $actmasiva = $2;
  };

  my $admin_basedatos = 'NO'; # valor por defecto. # 7.0
  if ($buffer =~ m/\s*ADMIN_BASEDATOS\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $admin_basedatos = $2;
  };

  my $admin_buscador = 'NO'; # valor por defecto. # 7.0
  if ($buffer =~ m/\s*ADMIN_BUSCADOR\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $admin_buscador = $2;
  };

  my $admin_tax = 'SI'; # valor por defecto. # 7.0
  if ($buffer =~ m/\s*ADMIN_TAX\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $admin_tax = $2;
  };

  my $p_edit_art_ajenos = 'SI'; # valor por defecto. # 7.0
  if ($buffer =~ m/\s*REDACTOR_EDITAR_ARTICULOS_AJENOS\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $p_edit_art_ajenos = $2;
  };

  my $p_ver_art_ajenos = 'SI'; # valor por defecto. # 8.0
  if ($buffer =~ m/\s*REDACTOR_VER_ARTICULOS_AJENOS\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $p_ver_art_ajenos = $2;
  };


  my $e_edit_art_ajenos = 'SI'; # valor por defecto. # 7.0
  if ($buffer =~ m/\s*EDITOR_EDITAR_ARTICULOS_AJENOS\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $e_edit_art_ajenos = $2;
  };

  my $e_ver_art_ajenos = 'SI'; # valor por defecto. # 8.0
  if ($buffer =~ m/\s*EDITOR_VER_ARTICULOS_AJENOS\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $e_ver_art_ajenos = $2;
  };

  my $e_adm_ediciones = 'SI'; # valor por defecto. # 8.0
  if ($buffer =~ m/\s*EDITOR_ADMINISTRAR_EDICIONES\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $e_adm_ediciones = $2;
  };

  my $port_ini_selected = ''; # valor por defecto. # 7.0
  if ($buffer =~ m/\s*PORT_INI_SELECTED\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $port_ini_selected = $2;
  };

  my $port_home = '';
  if ($buffer =~ m/\s*PORT_HOME\s*=\s*("|')(.*?)("|')/) { # SI | NO
    $port_home = $2;
  };



  my $orden_lista_articulos = 'DATETIME'; # valor por defecto. # 8.0

  # Maximo de art. no pub. a desplegar en la lista de articulos
  my $max_nro_artic = '50'; # valor por defecto.
  if ($buffer =~ m/\s*MAX_NRO_ARTIC\s*=\s*("|')(\d+)("|')/) { # p. ej. 200
    $max_nro_artic = $2;
  };

  # Parametros de conexion a la BD MySQL
  my ($motor_bd, $server_bd,$nom_bd,$user_bd,$pwd_bd) = '-undefined-';

  if ($buffer =~ m/\s*MOTOR_BD\s*=\s*("|')(.*?)("|')/) { # MYSQL | PRONTUS
    $motor_bd = uc $2;

    if ($motor_bd eq 'MYSQL') {
      if ($buffer =~ m/\s*SERVER_BD\s*=\s*("|')(.*?)("|')/) {
        $server_bd = $2;
      };
      if ($buffer =~ m/\s*NOM_BD\s*=\s*("|')(.*?)("|')/) {
        $nom_bd = $2;
      };
      if ($buffer =~ m/\s*USER_BD\s*=\s*("|')(.*?)("|')/) {
        $user_bd = $2;
      };
      if ($buffer =~ m/\s*PWD_BD\s*=\s*("|')(.*?)("|')/) {
        $pwd_bd = $2;
      };
      if ((! $server_bd) || (! $nom_bd) || (! $user_bd) || (! $pwd_bd)) {
        print STDERR "Error en CFG: Faltan parametros de conexion a la base de datos MySQL. Los parámetros son: SERVER_BD, NOM_BD, USER_BD y PWD_BD\n";
        print "Content-Type: text/html\n\n";
        print "<P>Error en CFG: Faltan parametros de conexion a la base de datos MySQL. Los parámetros son: SERVER_BD, NOM_BD, USER_BD y PWD_BD";
        exit;
      };

    };

    if (($motor_bd ne 'MYSQL') && ($motor_bd ne 'PRONTUS')) {
      print STDERR "Error en CFG: Motor de base de datos no válido, la variable MOTOR_BD debe ser 'MYSQL' o 'PRONTUS'.\n";
      print "Content-Type: text/html\n\n";
      print "<P>Error en CFG: Motor de base de datos no válido, la variable MOTOR_BD debe ser 'MYSQL' o 'PRONTUS'.";
      exit;
    };

  }
  else {
    print STDERR "Error en CFG: Debe indicar Motor de base de datos, la variable MOTOR_BD debe ser 'MYSQL' o 'PRONTUS'.\n";
    print "Content-Type: text/html\n\n";
    print "<P>Error en CFG: Debe indicar Motor de base de datos, la variable MOTOR_BD debe ser 'MYSQL' o 'PRONTUS'.";
    exit;
  };



  # Taxonomia
  # CVI - Deprecated - Ya no se usa esto
  #~ my $taxport_refresh = 'SI'; # valor por defecto. Si es NO, entonces no se regenera el cache de las taxports, sino que se actualizan masivamente via CRON
  #~ if ($buffer =~ m/\s*TAXPORT_REFRESH\s*=\s*("|')(.*?)("|')/) { # SI | NO
    #~ $taxport_refresh = $2;
  #~ };
  #~ $prontus_varglb::TAXPORT_REFRESH = $taxport_refresh;


  my $taxport_maxartics = '500'; # valor por defecto.
  if ($buffer =~ m/\s*TAXPORT_MAXARTICS\s*=\s*("|')([0-9]+?)("|')/) {
    $taxport_maxartics = $2;
  };
  $prontus_varglb::TAXPORT_MAXARTICS = $taxport_maxartics;
  $prontus_varglb::TAXPORT_MAXARTICS = $prontus_varglb::TAXPORT_MAXARTICS_SECURITY if ($prontus_varglb::TAXPORT_MAXARTICS > $prontus_varglb::TAXPORT_MAXARTICS_SECURITY);

  my ($tax_niv, $control_alta);
  if ($buffer =~ m/\s*TAXONOMIA_NIVELES\s*=\s*("|')([0-3])("|')/) {
   $tax_niv = $2;
  };
  if ($buffer =~ m/\s*CONTROLAR_ALTA_ARTICULOS\s*=\s*("|')(.*?)("|')/) { # SI | NO
   $control_alta = $2;
  };

  my $artic_actualiza_ports = 'NO';
  if ($buffer =~ m/\s*ARTIC_ACTUALIZA_PORTS\s*=\s*("|')(.*?)("|')/) { # SI | NO
   $artic_actualiza_ports = $2;
  };

  $prontus_varglb::TAXONOMIA_NIVELES = $tax_niv;
  $prontus_varglb::CONTROLAR_ALTA_ARTICULOS = $control_alta;
  $prontus_varglb::ARTIC_ACTUALIZA_PORTS = $artic_actualiza_ports;

  # tagonomicas

  # tagonomicas.TAGPORT_MAXARTICS
  my $tagport_maxartics = '500'; # valor por defecto.
  if ($buffer =~ m/\s*TAGPORT_MAXARTICS\s*=\s*("|')([0-9]+?)("|')/) {
    $tagport_maxartics = $2;
  };
  $prontus_varglb::TAGPORT_MAXARTICS = $tagport_maxartics;
  $prontus_varglb::TAGPORT_MAXARTICS = 1000 if ($prontus_varglb::TAGPORT_MAXARTICS > 1000);

  # tagonomicas.TAGPORT_MAXARTICS
  my $tags_max_last_fid = '15'; # valor por defecto.
  if ($buffer =~ m/\s*MAX_LAST_TAGS_4FID\s*=\s*("|')([0-9]+?)("|')/) {
    $tags_max_last_fid = $2;
  };
  $prontus_varglb::MAX_LAST_TAGS_4FID = $tags_max_last_fid;
  $prontus_varglb::MAX_LAST_TAGS_4FID = 500 if ($prontus_varglb::MAX_LAST_TAGS_4FID > 500);

  # tagonomicas.TAGPORT_ARTXPAG
  my $tagport_artxpag = 20; # valor default
  if ($buffer =~ m/\s*TAGPORT_ARTXPAG\s*=\s*("|')([0-9]+?)("|')/) {
    $tagport_artxpag = $2;
  };
  $prontus_varglb::TAGPORT_ARTXPAG = $tagport_artxpag;

  # tagonomicas.TAGPORT_ORDEN
  $prontus_varglb::TAGPORT_ORDEN = 'ART_FECHAP desc, ART_HORAP desc'; # valor por defecto.
  my $tagport_orden;
  my $tagport_orden_new;
  my $tagport_orden_err;
  if ($buffer =~ m/\s*TAGPORT_ORDEN\s*=\s*("|')(\w+?\(\w+\))("|')/) {
    $tagport_orden = $2;
    if ($tagport_orden =~ /^(PUBLICACION|TITULAR|CREACION)\((ASC|DESC)\)$/) {
      if ($1 eq 'PUBLICACION') {
        $tagport_orden_new = "ART_FECHAP $2, ART_HORAP $2";
      }
      elsif ($1 eq 'TITULAR') {
        $tagport_orden_new = "ART_TITU $2";
      }
      elsif ($1 eq 'CREACION') {
        $tagport_orden_new = "ART_AUTOINC $2";
      }
      else {
        $tagport_orden_err = 1;
      };
    }
    else {
      $tagport_orden_err = 1;
    };
  };

  if ($tagport_orden_err) {
    print STDERR "Error en CFG: seteo de variable TAGPORT_ORDEN contiene un valor no v&aacute;lido.<br>Valores posibles: 'PUBLICACION(ASC|DESC)', 'TITULAR(ASC|DESC)', 'CREACION(ASC|DESC)'<br>Por omisi&oacute;n es: 'PUBLICACION(DESC)'\n";
    print "Content-Type: text/html\n\n";
    print "<P>Error en CFG: seteo de variable TAGPORT_ORDEN contiene un valor no v&aacute;lido.<br>Valores posibles: 'PUBLICACION(ASC|DESC)', 'TITULAR(ASC|DESC)', 'CREACION(ASC|DESC)'<br>Por omisi&oacute;n es: 'PUBLICACION(DESC)'";
    exit;
  };
  $prontus_varglb::TAGPORT_ORDEN = $tagport_orden_new if ($tagport_orden_new);

  # ---------
  # list.LIST_PROCESO_INTERNO
  my $proc_int = 'SI'; # valor por defecto.
  if ($buffer =~ m/\s*LIST_PROCESO_INTERNO\s*=\s*("|')(.*?)("|')/) { # 1.22 valores posibles : SI | NO
    $proc_int = $2;
  };
  $prontus_varglb::LIST_PROCESO_INTERNO = $proc_int;

  #~ # list.LIST_ARTXPAG
  #~ $prontus_varglb::LIST_ARTXPAG = '20'; # valor por defecto.
  #~ if ($buffer =~ m/\s*LIST_ARTXPAG\s*=\s*("|')([0-9]+?)("|')/) {
    #~ $prontus_varglb::LIST_ARTXPAG = $2;
  #~ };

  # list.LIST_MAXARTICS
  $prontus_varglb::LIST_MAXARTICS = '20'; # valor por defecto.
  if ($buffer =~ m/\s*LIST_MAXARTICS\s*=\s*("|')([0-9]+?)("|')/) {
    $prontus_varglb::LIST_MAXARTICS = $2;
  };
  $prontus_varglb::LIST_MAXARTICS = 1000 if ($prontus_varglb::LIST_MAXARTICS > 1000);

  # list.LIST_ORDEN
  $prontus_varglb::LIST_ORDEN = 'ART_FECHAP desc, ART_HORAP desc'; # valor por defecto.
  my $list_orden;
  my $list_orden_new;
  my $list_orden_err;
  if ($buffer =~ m/\s*LIST_ORDEN\s*=\s*("|')(\w+?\(\w+\))("|')/) {
    $list_orden = $2;
    if ($list_orden =~ /^(PUBLICACION|TITULAR|CREACION)\((ASC|DESC)\)$/) {
      if ($1 eq 'PUBLICACION') {
        $list_orden_new = "ART_FECHAP $2, ART_HORAP $2";
      }
      elsif ($1 eq 'TITULAR') {
        $list_orden_new = "ART_TITU $2";
      }
      elsif ($1 eq 'CREACION') {
        $list_orden_new = "ART_AUTOINC $2";
      }
      else {
        $list_orden_err = 1;
      };
    }
    else {
      $list_orden_err = 1;
    };
  };

  if ($list_orden_err) {
    print STDERR "Error en CFG: seteo de variable LIST_ORDEN contiene un valor no v&aacute;lido.<br>Valores posibles: 'PUBLICACION(ASC|DESC)', 'TITULAR(ASC|DESC)', 'CREACION(ASC|DESC)'<br>Por omisi&oacute;n es: 'PUBLICACION(DESC)'\n";
    print "Content-Type: text/html\n\n";
    print "<P>Error en CFG: seteo de variable LIST_ORDEN contiene un valor no v&aacute;lido.<br>Valores posibles: 'PUBLICACION(ASC|DESC)', 'TITULAR(ASC|DESC)', 'CREACION(ASC|DESC)'<br>Por omisi&oacute;n es: 'PUBLICACION(DESC)'";
    exit;
  };
  $prontus_varglb::LIST_ORDEN = $list_orden_new if ($list_orden_new);
  # ---------

  # path del ffmpeg
  my $default_dir_ffmpeg;

  # detecta ubicacion ffmpeg en el sistema
  my @dirs_ffmpeg;
  push @dirs_ffmpeg, '/usr/local/bin';
  push @dirs_ffmpeg, '/usr/bin';
  my $found_path_ffmpeg = 0;
  foreach my $dir_ffmpeg (@paths_ffmpeg) {
    if (-f "$dir_ffmpeg/ffmpeg") {
        $default_dir_ffmpeg = $dir_ffmpeg;
        last;
    };
  };
  # si no se detecta ninguno, asigna el primero que se probo, para que la var no quede en blanco
  $default_dir_ffmpeg = $dirs_ffmpeg[0] if (!$default_dir_ffmpeg);

  # si el dir se define por cfg, usa ese en lugar del por defecto
  if ($buffer =~ m/\s*DIR_FFMPEG\s*=\s*("|')(.*?)("|')/) {
   $dir_ffmpeg = $2;
  } else {
   $dir_ffmpeg = $default_dir_ffmpeg;
  };
  $prontus_varglb::DIR_FFMPEG = $dir_ffmpeg;
  $prontus_varglb::DIR_FFMPEG =~ s/[^\w\-\/]//sg;
  $prontus_varglb::DIR_FFMPEG =~ s/\/$//sg;

  if (!-d $prontus_varglb::DIR_FFMPEG) {
      print STDERR "Error en CFG: variable DIR_FFMPEG no corresponde a un directorio existente en el sistema.\n";
      print "Content-Type: text/html\n\n";
      print "<P>Error en CFG: variable DIR_FFMPEG no corresponde a un directorio existente en el sistema.";
      exit;
  };
  #print STDERR "DIR_FFMPEG[$prontus_varglb::DIR_FFMPEG]\n";



  # customizacion de paste mode en vtxt
  my $vtxt_paste_newlines_as_p = 'NO';
  if ($buffer =~ m/\s*VTXT_PASTE_NEWLINES_AS_P\s*=\s*("|')(.*?)("|')/) {
   $vtxt_paste_newlines_as_p = $2;
  };
  $prontus_varglb::VTXT_PASTE_NEWLINES_AS_P = $vtxt_paste_newlines_as_p;


  # actualizaciones automaticas
  my $actualizaciones = 'SI';
  if ($buffer =~ m/\s*ACTUALIZACIONES\s*=\s*("|')(.*?)("|')/) { # SI | NO
   $actualizaciones = $2;
  };
  $prontus_varglb::ACTUALIZACIONES = $actualizaciones;


  # Para saber si el FID se abre en pop o no
  my $abrir_fids_en_pop = 'NO';
  if ($buffer =~ m/\s*ABRIR_FIDS_EN_POP\s*=\s*("|')(.*?)("|')/) { # SI | NO
   $abrir_fids_en_pop = $2;
  };
  $prontus_varglb::ABRIR_FIDS_EN_POP = $abrir_fids_en_pop;

  $num_relac_default = 5; # valor default
  if ($buffer =~ m/\s*NUM_RELAC_DEFAULT\s*=\s*("|')(\d+?)("|')/) {
   $num_relac_default = $2;

   if (($num_relac_default =~ /\d+/) && (! $tax_niv)) {
       #~ 12/12/2012 - CVI - Para evitar el error al guardar TAXONOMIA_NIVELES = 0
        #~ print STDERR "Error en CFG: seteo de variable NUM_RELAC_DEFAULT='n' requiere de seteo de variable TAXONOMIA_NIVELES='N' (N=1,2,3)\n";
        #~ print "Content-Type: text/html\n\n";
        #~ print "<P>Error en CFG: seteo de variable NUM_RELAC_DEFAULT='n' requiere de seteo de variable TAXONOMIA_NIVELES='N' (N=1,2,3)";
        #~ exit;
   };
  };
  $prontus_varglb::NUM_RELAC_DEFAULT = $num_relac_default;


  my $taxport_artxpag = 20; # valor default
  if ($buffer =~ m/\s*TAXPORT_ARTXPAG\s*=\s*("|')(\d+?)("|')/) {
    $taxport_artxpag = $2;
    if (($taxport_artxpag =~ /\d+/) && (! $tax_niv)) {
      #~ 12/12/2012 - CVI - Para evitar el error al guardar TAXONOMIA_NIVELES = 0
      #~ print STDERR "Error en CFG: seteo de variable TAXPORT_ARTXPAG='n' requiere de seteo de variable TAXONOMIA_NIVELES='N' (N=1,2,3)\n";
      #~ print "Content-Type: text/html\n\n";
      #~ print "<P>Error en CFG: seteo de variable TAXPORT_ARTXPAG='n' requiere de seteo de variable TAXONOMIA_NIVELES='N' (N=1,2,3)";
      #~ exit;
    };
  };
  $prontus_varglb::TAXPORT_ARTXPAG = $taxport_artxpag;

  # CVI - DEPRECATED - Esta marca ya no se usa
  #~ my $taxport_refresh_segs = 1800; # valor default  media hora
  #~ if ($buffer =~ m/\s*TAXPORT_REFRESH_SEGS\s*=\s*("|')(\d+?)("|')/) {
    #~ $taxport_refresh_segs = $2;
    #~ if (($taxport_refresh_segs =~ /\d+/) && (! $tax_niv)) {
      # 12/12/2012 - CVI - Para evitar el error al guardar TAXONOMIA_NIVELES = 0
      # print STDERR "Error en CFG: seteo de variable TAXPORT_REFRESH_SEGS='n' requiere de seteo de variable TAXONOMIA_NIVELES='N' (N=1,2,3)\n";
      # print "Content-Type: text/html\n\n";
      # print "<P>Error en CFG: seteo de variable TAXPORT_REFRESH_SEGS='n' requiere de seteo de variable TAXONOMIA_NIVELES='N' (N=1,2,3)";
      # exit;
    #~ };
  #~ };
  #~ $prontus_varglb::TAXPORT_REFRESH_SEGS = $taxport_refresh_segs;

  # TAXPORT_ORDEN
  $prontus_varglb::TAXPORT_ORDEN = 'ART_FECHAP desc, ART_HORAP desc'; # valor por defecto.
  my $taxport_orden;
  my $taxport_orden_new;
  my $taxport_orden_err;
  if ($buffer =~ m/\s*TAXPORT_ORDEN\s*=\s*("|')(\w+?\(\w+\))("|')/) {
    $taxport_orden = $2;
    if ($taxport_orden =~ /^(PUBLICACION|TITULAR|CREACION)\((ASC|DESC)\)$/) {
      if ($1 eq 'PUBLICACION') {
        $taxport_orden_new = "ART_FECHAP $2, ART_HORAP $2";
      }
      elsif ($1 eq 'TITULAR') {
        $taxport_orden_new = "ART_TITU $2";
      }
      elsif ($1 eq 'CREACION') {
        $taxport_orden_new = "ART_AUTOINC $2";
      }
      else {
        $taxport_orden_err = 1;
      };
    }
    else {
      $taxport_orden_err = 1;
    };
  };

  if ($taxport_orden_err) {
    print STDERR "Error en CFG: seteo de variable TAXPORT_ORDEN contiene un valor no v&aacute;lido.<br>Valores posibles: 'PUBLICACION(ASC|DESC)', 'TITULAR(ASC|DESC)', 'CREACION(ASC|DESC)', Por omisi&oacute;n es: 'PUBLICACION(DESC)'\n";
    print "Content-Type: text/html\n\n";
    print "<P>Error en CFG: seteo de variable TAXPORT_ORDEN contiene un valor no v&aacute;lido.<br>Valores posibles: 'PUBLICACION(ASC|DESC)', 'TITULAR(ASC|DESC)', 'CREACION(ASC|DESC)'<br>Por omisi&oacute;n es: 'PUBLICACION(DESC)'";
    exit;
  };
  $prontus_varglb::TAXPORT_ORDEN = $taxport_orden_new if ($taxport_orden_new);


  # EDICION BASE SELECCIONADA POR DEFECTO
  my $edicbase_ini_selected = 'NO'; # valor por defecto, se selecciona la ultima edic
  if ($buffer =~ m/\s*EDICBASE_INI_SELECTED\s*=\s*("|')(.*?)("|')/) { # 1.22 valores posibles : SI | NO
    $edicbase_ini_selected = $2;
  };
  $prontus_varglb::EDICBASE_INI_SELECTED = $edicbase_ini_selected;


  # smtp
  my $server_smtp = ''; # valor por defecto
  if ($buffer =~ m/\s*SERVER_SMTP\s*=\s*("|')(.*?)("|')/) {
    $server_smtp = $2;
  };
  $prontus_varglb::SERVER_SMTP = $server_smtp;


  # Nubetags
  my $nubetags_factor_olvido = 0.9; # valor por defecto
  if ($buffer =~ m/\s*NUBETAGS_FACTOR_OLVIDO\s*=\s*("|')(.*?)("|')/) {
    $nubetags_factor_olvido = $2;
  };
  $nubetags_factor_olvido =~ s/\,/\./;
  if ($nubetags_factor_olvido !~ /^[0-9]+(\.[0-9]+)?$/) {
      print STDERR "Error en CFG: seteo de variable NUBETAGS_FACTOR_OLVIDO contiene un valor no v&aacute;lido.<br>Debe contener un número entero o decimal, por ejemplo: '0.95'<br>Por omisi&oacute;n es: '0.9'\n";
      print "Content-Type: text/html\n\n";
      print "<P>Error en CFG: seteo de variable NUBETAGS_FACTOR_OLVIDO contiene un valor no v&aacute;lido.<br>Debe contener un número entero o decimal, por ejemplo: '0.95'<br>Por omisi&oacute;n es: '0.9'";
      exit;
  };
  $prontus_varglb::NUBETAGS_FACTOR_OLVIDO = $nubetags_factor_olvido;

  # max tags
  my $nubetags_max_tags = 30; # valor por defecto
  if ($buffer =~ m/\s*NUBETAGS_MAX_TAGS\s*=\s*("|')(.*?)("|')/) {
    $nubetags_max_tags = $2;
  };
  if ($nubetags_max_tags !~ /^[0-9]+$/) {
      print STDERR "Error en CFG: seteo de variable NUBETAGS_MAX_TAGS contiene un valor no v&aacute;lido.<br>Debe contener un número entero, por ejemplo: '10'<br>Por omisi&oacute;n es: '30'\n";
      print "Content-Type: text/html\n\n";
      print "<P>Error en CFG: seteo de variable NUBETAGS_MAX_TAGS contiene un valor no v&aacute;lido.<br>Debe contener un número entero, por ejemplo: '10'<br>Por omisi&oacute;n es: '30'";
      exit;
  };
  $prontus_varglb::NUBETAGS_MAX_TAGS = $nubetags_max_tags;

  # Varnish purge
  %prontus_varglb::VARNISH_SERVER_NAME = ();
  my $varnish_server_name;
  while ($buffer =~ m/\s*VARNISH\_SERVER\_NAME\s*=\s*("|')(.+?)("|')/g) {
     $varnish_server_name = $2;
     $prontus_varglb::VARNISH_SERVER_NAME{$varnish_server_name} = 1;
  };


  # clustering servers    # CLUSTERING_SERVER = '192.168.1.6(cluster1000)(passcluster1)'
  my $num_server;
  while ($buffer =~ m/\s*CLUSTERING\_SERVER\s*=\s*("|')(.+?)\((.+?)\)\((.+?)\)("|')/g) {
     $num_server++;
     $prontus_varglb::CLUSTERING_SERVER{$num_server}{'ip'} = $2;
     $prontus_varglb::CLUSTERING_SERVER{$num_server}{'user'} = $3;
     $prontus_varglb::CLUSTERING_SERVER{$num_server}{'pass'} = $4;
  };

  # clustering params
  if (keys(%prontus_varglb::CLUSTERING_SERVER) > 0) {
      # clustering_debug_level
      my $clustering_debug_level = 1; # valor por defecto
      if ($buffer =~ m/\s*CLUSTERING_DEBUG_LEVEL\s*=\s*("|')(.*?)("|')/) {
        $clustering_debug_level = $2;
      };
      if ($clustering_debug_level !~ /^[0-2]$/) {
         my $msg = "<P>Error en CFG: seteo de variable CLUSTERING_DEBUG_LEVEL contiene un valor no v&aacute;lido."
                  . "<br>Valores posibles: '0', '1' o '2'."
                  . "<br>'0':Sólo errores | '1': Errores e información básica | '2': Todo lo anterior y además debug específico de FTP"
                  . "<br>Por omisi&oacute;n es: '1'";
          &glib_html_02::print_pag_result('Error', $msg, 0, 'exit=1,ctype=1');
      };
      $prontus_varglb::CLUSTERING_DEBUG_LEVEL = $clustering_debug_level;

      # clustering_timeout_connect_segs
      my $clustering_timeout_connect_segs = 15; # valor por defecto
      if ($buffer =~ m/\s*CLUSTERING_TIMEOUT_CONNECT_SEGS\s*=\s*("|')(.*?)("|')/) {
        $clustering_timeout_connect_segs = $2;
      };
      if ($clustering_timeout_connect_segs !~ /^[0-9]+$/) {
          my $msg = "<P>Error en CFG: seteo de variable CLUSTERING_TIMEOUT_CONNECT_SEGS contiene un valor no v&aacute;lido."
                  . "<br>Debe contener un número entero de segundos, por ejemplo: '10'"
                  . "<br>Por omisi&oacute;n es: '15'";
          &glib_html_02::print_pag_result('Error', $msg, 1, 'exit=1,ctype=1');
      };
      $prontus_varglb::CLUSTERING_TIMEOUT_CONNECT_SEGS = $clustering_timeout_connect_segs;

      # clustering_log_duration_segs # segs tras los cuales se resetea el log, default=86400 --> 24hrs
      my $clustering_log_duration_segs = 86400; # valor por defecto
      if ($buffer =~ m/\s*CLUSTERING_LOG_DURATION_SEGS\s*=\s*("|')(.*?)("|')/) {
        $clustering_log_duration_segs = $2;
      };
      if ($clustering_log_duration_segs !~ /^[0-9]+$/) {
          my $msg = "<P>Error en CFG: seteo de variable CLUSTERING_LOG_DURATION_SEGS contiene un valor no v&aacute;lido."
                  . "<br>Debe contener un número entero de segundos, por ejemplo: '3600'"
                  . "<br>Por omisi&oacute;n es: '86400' (24 horas)";
          &glib_html_02::print_pag_result('Error', $msg, 1, 'exit=1,ctype=1');
      };
      $prontus_varglb::CLUSTERING_LOG_DURATION_SEGS = $clustering_log_duration_segs;

      # clustering_file_update_segs # MINIMA ANTIGUEDAD DEL ARCHIVO REQUERIDA PARA TRANSMITIRLO
      my $clustering_file_update_segs = 15; # valor por defecto
      if ($buffer =~ m/\s*CLUSTERING_FILE_UPDATE_SEGS\s*=\s*("|')(.*?)("|')/) {
        $clustering_file_update_segs = $2;
      };
      if ($clustering_file_update_segs !~ /^[0-9]+$/) {
          my $msg = "<P>Error en CFG: seteo de variable CLUSTERING_FILE_UPDATE_SEGS contiene un valor no v&aacute;lido."
                  . "<br>Debe contener un número entero de segundos, por ejemplo: '10'"
                  . "<br>Por omisi&oacute;n es: '15'";
          &glib_html_02::print_pag_result('Error', $msg, 1, 'exit=1,ctype=1');
      };
      $prontus_varglb::CLUSTERING_FILE_UPDATE_SEGS = $clustering_file_update_segs;
  };


  # Configuracion de DTD a usar en VTXT
  my $vtxt_dtd = 'STRICT'; # TRANSITIONAL | STRICT
  if ($buffer =~ m/\s*VTXT_DTD\s*=\s*("|')(.*?)("|')/) {
    $vtxt_dtd = $2;
    if ($vtxt_dtd !~ /^(STRICT|TRANSITIONAL)$/) {
      print STDERR "Error en CFG: seteo de variable VTXT_DTD\n";
      print "Content-Type: text/html\n\n";
      print "<P>Error en CFG: seteo de variable VTXT_DTD contiene un valor no v&aacute;lido.<br>Valores posibles: 'STRICT', 'TRANSITIONAL'<br>Por omisi&oacute;n es: 'STRICT'";
      exit;
    };
  };
  $prontus_varglb::VTXT_DTD = $vtxt_dtd;


#  my $pp;
#  my $pp_tipo;
#  while ($buffer =~ m/\s*POST\_PROCESO\s*=\s*("|')(.*?)(\((.*?)\))?\((.*?)\)("|')/g) {
#     $pp_tipo = $2; # ART-BORRAR | ART-GUARDAR | ART-EDITAR | PORT_GUARDAR | etc
#     $pp_context = $4;
#     $pp = $5;
#
#     $prontus_varglb::POST_PROCESO{$pp_tipo}{} = $pp;
#  };

  my $pp;
  my $pp_tipo;
  while ($buffer =~ m/\s*POST\_PROCESO\s*=\s*("|')(.*?)(\(.*?)("|')/g) {
     $pp = $3;
     $pp_tipo = $2; # ART-BORRAR | ART-GUARDAR | ART-EDITAR | PORT_GUARDAR | etc
     $prontus_varglb::POST_PROCESO{$pp_tipo} = $pp;
  };

  # El valor por defecto es vacio
  if ($buffer =~ m/\s*SCRIPT_QUOTA\s*=\s*("|')(.*?)("|')/) {
    $prontus_varglb::SCRIPT_QUOTA = $2;
  };

  # El valor por defecto es vacio
  if ($buffer =~ m/\s*FOTO_MAX_PIXEL\s*=\s*("|')(.*?)("|')/) {
    $prontus_varglb::FOTO_MAX_PIXEL = $2;
  };
  
  if ($buffer =~ m/\s*FFMPEG_PARAMS\s*=\s*("|')(.*?)("|')/) {
    $prontus_varglb::FFMPEG_PARAMS = $2;
  };

  # El valor por defecto es vacio
  if ($buffer =~ m/\s*MAX_XCODING\s*=\s*("|')(\d*)("|')/) {
    if ($2 eq '') {
        $prontus_varglb::MAX_XCODING = '50';
    } else {
        $prontus_varglb::MAX_XCODING = $2;
    };
  } else {
      $prontus_varglb::MAX_XCODING = '50';
  };

  # El valor por defecto es 0
  if ($buffer =~ m/\s*BLOQUEO_EDICION\s*=\s*("|')(.*?)("|')/) {
    $prontus_varglb::BLOQUEO_EDICION = $2;
  };


  # Prontus 6.0
  $prontus_varglb::PRONTUS_ID = $prontus_id;
  $prontus_varglb::RELDIR_BASE = $reldir_base;
  $prontus_varglb::TIPO_PRONTUS = $tipo_prontus;

  $prontus_varglb::DIR_CONTENIDO = "$reldir_base/$prontus_id$prontus_varglb::DIR_CONTENIDO";

  $prontus_varglb::DIR_TEMP = "$reldir_base/$prontus_id$prontus_varglb::DIR_TEMP";
  $prontus_varglb::DIR_CPAN = "$reldir_base/$prontus_id$prontus_varglb::DIR_CPAN";

  $prontus_varglb::DIR_DBM = "$prontus_varglb::DIR_CPAN/data";


  $prontus_varglb::AREA_MENU = $area_menu;
  $prontus_varglb::AREA_CONT = $area_cont;
  $prontus_varglb::PRONTUS_KEY = $prontus_key;


  $prontus_varglb::CONTROL_FECHA = $cfecha;
  $prontus_varglb::MULTI_EDICION = $multied;
  $prontus_varglb::DIR_LOG = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/log";
  $prontus_varglb::PRONTUS_LOG = $prontus_log;

  $prontus_varglb::FRIENDLY_URLS = $friendly_urls;
  $prontus_varglb::FRIENDLY_URLS_VERSION = $friendly_urls_version;

  $prontus_varglb::MAX_NRO_ARTIC = $max_nro_artic;

  $prontus_varglb::MOTOR_BD = $motor_bd;
  $prontus_varglb::SERVER_BD = $server_bd;
  $prontus_varglb::NOM_BD = $nom_bd;
  $prontus_varglb::USER_BD = $user_bd;
  $prontus_varglb::PWD_BD = $pwd_bd;


  $prontus_varglb::PERIODISTA_EDITAR_ARTICULOS_AJENOS = $p_edit_art_ajenos;
  $prontus_varglb::PERIODISTA_VER_ARTICULOS_AJENOS = $p_ver_art_ajenos;

  $prontus_varglb::EDITOR_EDITAR_ARTICULOS_AJENOS = $e_edit_art_ajenos;
  $prontus_varglb::EDITOR_VER_ARTICULOS_AJENOS = $e_ver_art_ajenos;
  $prontus_varglb::EDITOR_ADMINISTRAR_EDICIONES = $e_adm_ediciones;


  $prontus_varglb::PRONTUS_EDITOR = $peditor;
  $prontus_varglb::ACTUALIZACION_MASIVA = $actmasiva;

  $prontus_varglb::VERIFICAR_INSTALACION = $verifinst;

  $prontus_varglb::ADMIN_BASEDATOS = $admin_basedatos;

  $prontus_varglb::ADMIN_BUSCADOR = $admin_buscador;
  $prontus_varglb::ADMIN_TAX = $admin_tax;

  $prontus_varglb::ADMIN_PORT = $admin_port;

  $prontus_varglb::RTEXT_ENABLED = $rtext_enabled;

  $prontus_varglb::PORT_INI_SELECTED = $port_ini_selected;
  $prontus_varglb::PORT_HOME = $port_home;


  $prontus_varglb::ORDEN_LISTA_ARTICULOS = $orden_lista_articulos;     # 8.0

  my $path = "$prontus_varglb::RELDIR_BASE/$prontus_varglb::PRONTUS_ID/imag";

  $prontus_varglb::WMEDIA_LINK =~ s/%%path%%/$path/; # 8.1
  $prontus_varglb::RMEDIA_LINK =~ s/%%path%%/$path/;
  $prontus_varglb::ASOCFILE_LINK =~ s/%%path%%/$path/;
  $prontus_varglb::LINK_MAS =~ s/%%path%%/$path/;

  $prontus_varglb::FECHA_HOY = &glib_hrfec_02::get_date_pack4();


  $prontus_varglb::DIR_CORE = "$reldir_base/$prontus_id$prontus_varglb::DIR_CORE";

  # Solo ambiente web.

#   if ($ENV{'SERVER_NAME'} ne '') {
#
#     my $core_dir = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE;
#     my $js_buf = &glib_fildir_02::read_file("$core_dir/secciones_tmp.js");
#     my $secciones_js;
#     while ($buffer =~ m/\s*SECCIONES\s*=\s*("|')(.*?)("|')/g) {
#        $valor = $2;
#        $secciones_js .= ",'$valor'";
#     };
#     $js_buf =~ s/%%secciones%%/$secciones_js/g;
#     &glib_fildir_02::write_file("$core_dir/secciones.js", $js_buf);
#   };

  &check_dirs();


}

# -------------------------------------------------------------------------#
# 8.0
sub get_oct_dig {
  # del 1-4 es valido
  my ($caracter) = $_[0];
  my ($dig);

  # Asi es la cosa: @letras = ('Z', 'Y', 'X', 'W', 'A', 'B', 1, 'C', 'D', 2, 'E', 'F', 3, 'G', 'H', 4, 'I', 'J', 5, 'K', 'L', 6, 'M', 'N', 7, 'O', 'P', 8, 'Q', 'R', 9, 'S', 'T', 'U', 'V'); # 35 elementos.

  if ($caracter eq 'Y') {
    return ('1','1',0);
  }
  elsif ($caracter eq 'X') {
    return ('2','2',0);
  }
  elsif ($caracter eq 'W') {
    return ('3','3',0);
  }
  elsif ($caracter eq 'A') {
    return ('4','4',0);
  }

  elsif ($caracter eq 'B') {
    return ('1','5',1); # p01+rtext
  }
  elsif ($caracter eq '1') {
    return ('2','6',1); # p02+rtext
  }
  elsif ($caracter eq 'C') {
    return ('3','7',1); # p03+rtext
  }
  elsif ($caracter eq 'D') {
    return ('4','8',1); # p04+rtext
  }

  else {
    return ('0','0',0);
  };
};
# -------------------------------------------------------------------------#
# 8.0
sub get_sept_dig {
  # del 1-9 es valido
  my ($caracter) = $_[0];
  my ($dig);


  if ($caracter eq 'Y') {
    return '1';
  }
  elsif ($caracter eq 'X') {
    return '2';
  }
  elsif ($caracter eq 'W') {
    return '3';
  }
  elsif ($caracter eq 'A') {
    return '4';
  }
  elsif ($caracter eq 'B') {
    return '5';
  }
  elsif ($caracter eq '1') {
    return '6';
  }
  elsif ($caracter eq 'C') {
    return '7';
  }
  elsif ($caracter eq 'D') {
    return '8';
  }
  elsif ($caracter eq '2') {
    return '9';
  }
  else {
    return '0';
  };
};

# -------------------------------------------------------------------------#
sub write_log {
  my ($accion, $objeto, $path) = @_;
  my ($linea, $fecha, $hora, $buf, $nom_file, $usr);
  $prontus_varglb::DIR_LOG =~ s/\\/\//g;

  $prontus_varglb::DIR_LOG =~ s/(\w)\/$/\1/; # Borrar posible ultimo slash.


  if ((-d $prontus_varglb::DIR_LOG) && ($prontus_varglb::PRONTUS_LOG eq 'SI')) {
    # <nombre del publicador>_aaaammdd.log
    $fecha = &glib_hrfec_02::get_date_pack4();
    $nom_file = $prontus_varglb::PRONTUS_ID . '_' . $fecha . '.txt';

    # dd/mm/aaaa hh:mm:ss - <ip> - <accion> - <user> - <ente afectado> - <path>
    $fecha = &glib_hrfec_02::des_normaliza_fecha($fecha);
    $hora = &glib_hrfec_02::get_date_time('','' , '', '', 1, '', time);
    if ($prontus_varglb::USERS_USR) {
      $usr = $prontus_varglb::USERS_USR;
    }
    else {
      $usr = 'Proceso Control Fecha';
    };

    if ($accion !~ /login/i) {
      $path =~ s/^$prontus_varglb::DIR_SERVER//;
      $linea = $fecha . "\t" . $hora . "\t" . $ENV{'REMOTE_ADDR'} . "\t" . $usr . "\t" . $accion . "\t" . $objeto . "\t" . $path . "\n";
    }
    else {
      $linea = $fecha . "\t" . $hora . "\t" . $ENV{'REMOTE_ADDR'} . "\t" . $objeto . "\t" . $accion . "\t" . $path . "\n";
    };

    $buf = &glib_fildir_02::read_file($prontus_varglb::DIR_LOG . '/' . $nom_file);
    $buf = $buf . $linea;
    &glib_fildir_02::write_file($prontus_varglb::DIR_LOG . '/' . $nom_file, $buf);
  };

};
# -------------------------------------------------------------------------#


# Genera la portada de acuerdo al template escogido.

sub make_portada {
    my($dest_file, $path_tpl, $dir_server, $prontus_id, $mv, $public_server_name,
    $prontus_key, $stamp_demo, $nom_edic, $sin_regen_xml, $stamp_demo_rss,
    $control_fecha, $ts_preview, $controlar_alta_articulos, $users_perfil) = @_;

    # $dest_file: full path de la portada a generar, incluyendo extension
    # $path_tpl: full path de la plantilla de portada, incluyendo extension

    # print STDERR "path_tpl[$path_tpl]\n";

    my %plts4port;
    my %port_nom_clones;
    my %port_ext_clones;


    # Agregar la portada principal tambien
    $plts4port{$path_tpl} = $dest_file;

    # Agregar las portadas secundarias
    foreach my $nomport (keys %prontus_varglb::PORT_PLTS_EXTRA) {
        next if ($path_tpl !~ /(.*)\/$nomport$/); # obtiene las portadas extras solo para la portada actual
        my $dir_tpl = $1;
        my $extra_ports = $prontus_varglb::PORT_PLTS_EXTRA{$nomport}; # contiene los spare separados por ;
        # warn "nomport[$nomport]   extra_ports[$extra_ports]";
        while ($extra_ports =~ /([\w\-\.]+) *;?/g) {
            my $extra_port = $1;
            # warn "dir_tpl[$dir_tpl] extra_port[$extra_port]";
            next if (!-f "$dir_tpl/$extra_port");
            my $my_dest_file = $dest_file;
            $my_dest_file =~ s/\/$nomport$/\/$extra_port/;
            $plts4port{"$dir_tpl/$extra_port"} = $my_dest_file;

            my ($nom_clon, $ext) = &split_nom_y_extension($extra_port);
            $port_nom_clones{"$dir_tpl/$extra_port"} = $nom_clon;
            $port_ext_clones{"$dir_tpl/$extra_port"} = $ext;
        };
    };


    # Parsear la portada principal y sus clones
    foreach my $path_tpl_clon (keys %plts4port) {
        my $dest_file_clon = $plts4port{$path_tpl_clon};
        # print STDERR "path_tpl_clon[$path_tpl_clon]\n";
        # Carga plantilla y realiza parseos normales
        my $buffer = &generic_parse_port($path_tpl_clon, $dir_server, $prontus_id, $public_server_name, $nom_edic,
        $control_fecha, $ts_preview, $controlar_alta_articulos, $users_perfil, $mv);
        # print STDERR "buffer[$buffer]\n";
        # Parseos especificos
        # $buffer =~ s/<\/head>/\n<!--prontus_key=$prontus_key-->\n<\/head>/is;  # 1.16
        $buffer = &lib_prontus::add_generator_tag($buffer);

        # Escribe portada html
        $dest_file_clon =~ s/\/port\//\/port-$mv\// if ($mv);
        my $destdir = $dest_file_clon;
        $destdir =~ s/\/[\w\.]+$//;
        &glib_fildir_02::check_dir($destdir);
        my $nom_clon = $port_nom_clones{$path_tpl_clon};
        my $ext_clon = $port_ext_clones{$path_tpl_clon};
        # Si es un clon el que se esta previsualizando, le pongo preview_<nomclon>_<port>.<ext>
        if (($dest_file_clon =~ /\/port(-$mv)?\/preview_/) && ($path_tpl ne $path_tpl_clon)) {
            $dest_file_clon =~ s/\/port(-$mv)?\/preview_/\/port\1\/preview_$nom_clon\_/;
        };

        # print STDERR "dest_file_clon[$dest_file_clon]\n";

        # En los preview, poner links a los demas previews
        my $cual_viendo = $path_tpl_clon;
        $cual_viendo =~ /([^\/\\]+\.\w+)$/;
        $cual_viendo = $1;
        if ((%port_nom_clones) && ($dest_file_clon =~ /\/port\/preview/)) {
            my $links_previews;
            my $paralela = '';
            foreach my $k (keys %plts4port) {
                my $k_dst = $plts4port{$k};
                if ($path_tpl ne $k) {
                    my $nom_k = $port_nom_clones{$k};
                    $k_dst =~ s/\/port\/preview_/\/port\/preview_$nom_k\_/;
                    $paralela = 'paralela';
                };
                $k =~ /([^\/\\]+\.\w+)$/;
                $k = $1;
                $k_dst =~ /([^\/\\]+\.\w+)$/;
                $k_dst = $1;

                $links_previews = "<div><a href='$k_dst'>Ver preview de portada $paralela '$k'</a></div>" . $links_previews;
            };
            $buffer = "<div>Previsualizando '$cual_viendo'.</div> $links_previews <hr>" . $buffer;
        };
        $buffer =~ s/%%.+?%%//g;
        &glib_fildir_02::write_file($dest_file_clon, $buffer);
        &lib_prontus::purge_cache($dest_file_clon);
    };

    # Escribe xml de la portada ppal.
    &write_xml_port($dest_file, &generar_rows_xml_port($control_fecha, $controlar_alta_articulos)) if (! $sin_regen_xml);


    # -------------------------------------------------
    # Genera xml para RSS, para todas las vistas
    # -------------------------------------------------

    # Lee archivo de template rss.
    # Se llama igual a la portada pero esta en vez de /port en /rss y tiene extension .xml
    # $path_tpl =~ s/\/port\/(\w+)\.\w+?$/\/rss\/\1\.xml/;
    $path_tpl =~ s/\/port(\-\w+)?\/(\w+)\.\w+?$/\/rss\1\/\2\.xml/;

    if ((-s $path_tpl) && (-f $path_tpl)) {
        my $buffer = &generic_parse_port($path_tpl, $dir_server, $prontus_id, $public_server_name, $nom_edic,
        $control_fecha, $ts_preview, $controlar_alta_articulos, $users_perfil, '');

        # Parseos especificos
        $buffer =~ s/<\/channel>/$stamp_demo_rss\n<\/channel>/is;

        # Escribe RSS.
        $buffer =~ s/%%.+?%%//g;
        &write_rss_port($dest_file, $nom_edic, $buffer);
    };

    # Borra cache de no publicados
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");

};

# -------------------------------------------------------------------------
sub write_rss_port {
# Escribe el xml del rss de portada prontus

  my ($destrss, $nom_edic, $buffer) = @_;
  # $destrss =~ s/\/port\/(\w+)\.\w+?$/\/rss\/\1\.xml/; # Deduce del path completo de la portada, el del rss.
  $destrss =~ s/\/port(\-\w+)?\/(\w+)\.\w+?$/\/rss\1\/\2\.xml/; # Deduce del path completo de la portada, el del rss.

  $destrss =~ s/$nom_edic/base/ig; # si es una edicion normal, igual no mas escribe en el dir de la edic base, ya que los rss deben estar en una ubicacion fija: toma cachito e goma!
  $buffer = &mini_unescape_html($buffer); # parche heredado de subsecmar para el flash

  my $destdir_rss = $destrss;
  $destdir_rss =~ s/\/[\w\.]+$//;

  &glib_fildir_02::check_dir($destdir_rss);
  &glib_fildir_02::write_file($destrss, $buffer);
  &lib_prontus::purge_cache($destrss);
};
# -------------------------------------------------------------------------
sub write_xml_port {
# Escribe el xml de portada prontus

  my $dest_xml = $_[0]; # Deduce del path completo de la portada, el del xml.
  my $rowartics_xml = $_[1];
  if ($dest_xml !~ /\.xml$/) {
    $dest_xml =~ s/\/port\/(\w+)(\.\w+)?$/\/xml\/\1\.xml/;
  };
  # antes de escribir el nuevo xml, saca una copia de respaldo.
  if ($dest_xml =~ /^(.*\/xml)\/(.*\.xml)$/) {
    my $dirxml = $1;
    my $nomxml = $2;
    &glib_fildir_02::check_dir("$dirxml/bak");

    unlink "$dirxml/bak/$nomxml.9" if(-f "$dirxml/bak/$nomxml.9");
    for(my $i = 9; $i > 0; $i--) {
      &File::Copy::copy("$dirxml/bak/$nomxml.".($i-1), "$dirxml/bak/$nomxml.".($i));
    }
    &File::Copy::copy("$dirxml/bak/$nomxml", "$dirxml/bak/$nomxml.0");
    &File::Copy::copy($dest_xml, "$dirxml/bak/$nomxml");
  };
  # escribe el nuevo xml
  &glib_fildir_02::write_file($dest_xml, "<?xml version='1.0' encoding='iso-8859-1'?>\n<PORT_DATA>\n$rowartics_xml</PORT_DATA>");
};

# ---------------------------------------------------------------
sub carga_buffer_plt {
# Carga plantilla de articulo incluyendo las macros que contenga.

    my $fullpath_plt = shift; # path de la plantilla de la vista estandar
    my $pathdir_plt_macros = shift;
    my $mv = shift;

    $fullpath_plt =~ s/(.+)\/([^\/]+)$/\1-$mv\/\2/  if ($mv ne '');
    # warn "cargando plantilla[$fullpath_plt]";
    my $buffer = &glib_fildir_02::read_file($fullpath_plt);
    if ($buffer !~ /\w/) {
        return '';
    };
    $buffer = &lib_prontus::ajusta_crlf($buffer);
    # agrega macros.
    $buffer = &lib_prontus::add_macros($buffer, $pathdir_plt_macros, '', '');
    $buffer =~ s/%25%25/%%/sg;
    return $buffer;
};

# -------------------------------------------------------------------------
sub generic_parse_port {
# carga plantilla de portada y realiza parseos genericos, comunes a port normal y a rss

  my ($path_tpl, $dir_server, $prontus_id, $public_server_name, $nom_edic,
      $control_fecha, $ts_preview, $controlar_alta_articulos, $users_perfil, $mv) = @_;

#  if ($path_tpl =~ /\/inicio\.html/) {
#    $DEBUG_FECHAS = 1;
#    print STDERR "\n****************************** path_tpl[$path_tpl] ******************************\n";
#  } else {
#    $DEBUG_FECHAS = 0;
#  };

  my ($dir_macros) = "$dir_server/$prontus_id/plantillas/edic/nroedic/macros";
  my $buffer = &lib_prontus::carga_buffer_plt($path_tpl, $dir_macros, $mv);

  my $doblegato_string = &glib_str_02::random_string(30);
  $buffer =~ s/##/$doblegato_string/g;

  # Marcas globales
  $buffer = &parse_globals($buffer, $nom_edic, $public_server_name, $prontus_id);

  # Encuentra los tags de area dentro del template (%%LOOPi%%...%%/LOOP%%),
  # y produce los contenidos.
  #~ my $repet_areas = '1';
  my %areas;
  my %area_cont;
  # while ($buffer =~ /%%LOOP(\d+)%%(.*?)%%\/LOOP%%/isg) {
  while ($buffer =~ /%%LOOP(\d+)(\([^)]+?\))?%%(.*?)%%\/LOOP%%/isg) {
    my ($are,$tmp) = ($1,$3);
    my $pure_are = $are;
    if (!exists $area_cont{$pure_are}) {
        $area_cont{$pure_are} = 1;
    };
    if (exists $areas{$are}) {
      $are .= '_' . $area_cont{$pure_are};
      $area_cont{$pure_are}++;
    };
    # Parsea el area usando $2 como template parcial.
    $areas{$are} = &parser_area($pure_are,$tmp, $dir_server, $prontus_id,
                                                  $control_fecha, $ts_preview,
                                                  $controlar_alta_articulos, $users_perfil);
  };


  # Sustituye las areas parseadas.
  foreach my $key (sort{$a cmp $b}(keys %areas)) {
    my $aux = $areas{$key};
    $key =~ s/_\d+$//;
    $buffer =~ s/%%LOOP$key(\([^)]+?\))?%%(.*?)%%\/LOOP%%/$aux/is;
  };


  # Borra todos los tags IFV que quedaron en la pagina.
  $buffer =~ s/%%IFVC?\(\d+\, *\d+\)%%//isg;
  $buffer =~ s/%%\/IFVC?%%//isg;

  # Borra todos los tags NIFV que quedaron en la pagina.
  $buffer =~ s/%%NIFV\(\d+\, *\d+\)%%//isg;
  $buffer =~ s/%%\/NIFV%%//isg;

  $buffer =~ s/$doblegato_string/##/g;

  $buffer = &lib_prontus::parser_custom_function($buffer);

  $buffer = &lib_prontus::parse_includes($dir_server, $buffer);

  $buffer =~ s/%%[^_].+?%%//g;
  $buffer =~ s/<!--POST_PROCESO=.+?-->//ig;

  return $buffer;

};

# -------------------------------------------------------------------------
sub generar_rows_xml_port {
    my $control_fecha = shift;
    my $controlar_alta_articulos = shift;
    # Ordenar ascendentemente por area / orden / id articulo.
    my @arr_art = sort {$lib_prontus::AREA{$a} <=> $lib_prontus::AREA{$b}
                        || $lib_prontus::PRIO{$a} <=> $lib_prontus::PRIO{$b}
                        || $b <=> $a}
                        (keys %lib_prontus::AREA);

    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        die "ERROR: $msg_err_bd\n";
        exit;
    };

    my $rowartics_xml;
    foreach my $key (@arr_art) {
        my $prio = $lib_prontus::PRIO{$key};
        my $dir_fecha = &lib_prontus::get_dirfecha_by_ts($key);
        my $area = $lib_prontus::AREA{$key};
        my $vb = $lib_prontus::VB{$key};

        my $pub = &get_status_pub($key, $control_fecha, $controlar_alta_articulos, $base);

        next if (!$area);
        $prio = 1 if ((!$prio) && ($area));

        my $stamp = "  <rowartic>\n"
        . "    <dir>$dir_fecha</dir>\n"
        . "    <file>$key</file>\n"
        . "    <area>$area</area>\n"
        . "    <ord>$prio</ord>\n"
        . "    <vb>$vb</vb>\n"
        . "    <pub>$pub</pub>\n"
        . "  </rowartic>\n";

        # print STDERR "$stamp\n\n";

        if (($rowartics_xml !~ /$stamp/) && ($key ne 'filler')) {
            $rowartics_xml .= $stamp;
        };

    };

    $base->disconnect;
    return $rowartics_xml;
};


# -------------------------------------------------------------------------
sub parse_globals {
    my $buffer = shift;
    my $nom_edic = shift;
    my $public_server_name = shift;
    my $prontus_id = shift;

    $buffer =~ s/%%_NOM_EDIC%%/$nom_edic/ig;
    $buffer =~ s/%%_SERVER_NAME%%/$public_server_name/ig;
    $buffer =~ s/%%_PRONTUS_ID%%/$prontus_id/ig;
    return $buffer;
};

# -------------------------------------------------------------------------
sub get_nom_prontus {
    # prontus_xxx -->Prontus Xxx
    my $prontus_id = shift;

    while ($prontus_id =~ /( |^)([a-z])/g) {
        my $inicial = $2;
        if ($inicial) {
            my $inicial_uc = uc $inicial;
            my $char_prev = $1;
            $prontus_nom =~ s/$char_prev$2/$char_prev$inicial_uc/;
        };
    };

    return $prontus_nom;
};

# -------------------------------------------------------------------------
sub ajusta_crlf {
  my $buffer = $_[0];
  my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
  $buffer =~ s/$crlf/\x0a/sg;
  return $buffer;
};
# -------------------------------------------------------------------------
sub add_macros {
  # Incluye en el tpl las macros señaladas en el con la marca
  # %%MACRO(<nomfilemacro>)%%
  # <nomfilemacro> : Nombre del archivo de la macro (con extension y sin path), ubicado dentro del dir macros

  my ($textpag) = $_[0]; # buffer de la plantilla conteniendo invocaciones a macros
  my ($dir_macros) = $_[1]; # dir. fisico completo, sin slash al final
  my ($profundidad) = $_[2]; # solo para invocaciones internas, para manejar recursividad
  my ($prefijo) = $_[3]; # optativo, para considerar solo las macros q comiencen con cierto prefijo
  my ($pag_aux, $nomfile, $body, $nroloop, $buffer_macro);

  $pag_aux = $textpag;

  # Recorre tpl y parsea macros.
  while ($pag_aux =~ /%%MACRO\((.+?)\)%%/isg) {

    $nomfile = $1;
    if ($prefijo ne '') {
        next if ($nomfile !~ /^$prefijo/);
    };
    $buffer_macro = &glib_fildir_02::read_file("$dir_macros/$nomfile");
    if (! -f "$dir_macros/$nomfile") {
        my $relpath_macro = &remove_front_string("$dir_macros/$nomfile", $prontus_varglb::DIR_SERVER);
        $buffer_macro = "Macro '$relpath_macro' no existe";
        $textpag =~ s/%%MACRO\($nomfile\)%%/$buffer_macro/is;
        next;
    };

    $buffer_macro = &ajusta_crlf($buffer_macro);

    $body = '';
    if ($buffer_macro =~ /<body.*?>(.*)<\/body *>/is) {
      $body = $1;
    };
    $buffer_macro = $body if ($body);
    $profundidad++;

    if ($profundidad > 10) {
      $buffer_macro = '<b>[Error: Se alcanzó el nivel máximo de anidamiento de macros (max=10)]</b>';
      $textpag =~ s/%%MACRO\($nomfile\)%%/$buffer_macro/is;
      $profundidad = 0;
      next;
    }
    else {
      if ($buffer_macro =~ /%%MACRO\(.+?\)%%/is) {
        $buffer_macro = &add_macros($buffer_macro, $dir_macros, $profundidad, $prefijo);
      };
    };

    $profundidad = 0;
    $textpag =~ s/%%MACRO\($nomfile\)%%/$buffer_macro/is;

  };

  # parsear SERVER_NAME --> sacar despues de aca y poner en una funcion onda init_plantilla
  $textpag =~ s/%%_SERVER_NAME%%/$prontus_varglb::PUBLIC_SERVER_NAME/ig;

  return $textpag;



};



# -------------------------------------------------------------------------#
# Genera un area de acuerdo al template suministrado.
# Retorna el buffer parseado y el nro. de articulos en el area
# %AREA = ();
# %PRIO = ();
sub parser_area {

    my($area, $theloop, $dir_server, $prontus_id, 
            $control_fecha, $ts_preview, $controlar_alta_articulos, $users_perfil) = @_;
        
    # Obtiene lista de articulos de esta area.
    my $num_artics_in_area = 0;
    my (%articulos) = (); # Articulos que pertenecen a esta area.
    foreach my $key (sort{$b cmp $a}(keys %lib_prontus::AREA)) {
        if ($lib_prontus::AREA{$key} eq $area) {
            $articulos{$key} = $lib_prontus::AREA{$key};
        };
    };

    # Ordena los art. de esta area por prioridad y timestamp
    my @keys_articulos = sort {$lib_prontus::PRIO{$a} <=> $lib_prontus::PRIO{$b} or $b <=> $a} keys %articulos;
    my @filtered_keys;

    my $ultimo;
    my %hash_ifvs;
    my $totartics = 0;
    my $salida_html;

    # Aca se calculan los articulos que efectivamente serán publicados
    my %array_artics;
    foreach my $key (@keys_articulos) {
        
        my $ts_artic = $key;
        $ts_artic =~ s/\..*//; # borra extension al nombre del archivo
        
        # Revisar VoBo de publicacion
        my $vb_key = $lib_prontus::VB{$ts_artic};
        $vb_key = 1 if ($vb_key eq '');
        if ($vb_key eq '0') {
            next;
        };
        
        my $artic_obj = Artic->new(
                'prontus_id'=>$prontus_id,
                'public_server_name'=>$prontus_varglb::PUBLIC_SERVER_NAME,
                'cpan_server_name'=>$prontus_varglb::IP_SERVER,
                'document_root'=>$dir_server,
                'ts'=>$ts_artic, # si no va, asigna uno nuevo
                'campos'=>{}) || die "Error inicializando objeto articulo: $Artic::ERR\n";
        my %campos_xml = $artic_obj->get_xml_content();
        
        # Filtro por fechap/horap y fechae/horae del artic
        if ($control_fecha eq 'SI') {
            if (! &fechas_ok($ts_preview, $campos_xml{'_fechap'}, $campos_xml{'_horap'}, $campos_xml{'_fechae'}, $campos_xml{'_horae'})) {
                next;
            };
        };

        # Filtro por alta
        if ($controlar_alta_articulos eq 'SI') {
            my $alta_key = $campos_xml{'_alta'};
            if (! $alta_key) { # sin alta
                next;
            };
        };
        # Se guarda el objeto para usarlo mas abajo
        $filtered_keys[$totartics] = $key;
        $array_artics{$ts_artic} = \%campos_xml;
        $totartics++;
    };

    # Aca se asume que todos los artículos serán parseados
    my $stop_loop = 0;
    my $loopcounter = 0;
    while (($loopcounter <= $#filtered_keys) && ($stop_loop < 1)) {    
        
        my $key = $filtered_keys[$loopcounter];
        my $ts_artic = $key;
        $ts_artic =~ s/\..*//; # borra extension al nombre del archivo
        if($ts_artic !~ /\d{14}/) {
            $ts_artic = '';
        };        
        
        my $artic_obj = Artic->new(
                'prontus_id'=>$prontus_id,
                'public_server_name'=>$prontus_varglb::PUBLIC_SERVER_NAME,
                'cpan_server_name'=>$prontus_varglb::IP_SERVER,
                'document_root'=>$dir_server,
                'ts'=>$ts_artic, # si no va, asigna uno nuevo
                'campos'=>{}) || die "Error inicializando objeto articulo: $Artic::ERR\n";
        my %campos_xml;
        if(ref $array_artics{$ts_artic}) {
            my $ref = $array_artics{$ts_artic};
            %campos_xml = %$ref;
        } else {
            %campos_xml = $artic_obj->get_xml_content();
        };

        $loopcounter++;
        my $localbuf = $theloop; # Copia sub-template para generar instancia.

        # ------------- IFVs.
        # Si el contador de articulos para este loop MOD div != res entonces borrar contenido
        my $buf_aux = $localbuf;
        my ($div, $res, $mod, $instancias);
        if (($buf_aux =~ /%%IFVC\((\d+)\, *(\d+)\)%%.+?%%\/IFVC%%/is) and ($buf_aux !~ /%%IFV\((\d+)\, *(\d+)\)%%.+?%%\/IFV%%/is)) {
            return ('Error en Loop: Sentencia IFVC debe ir acompañada de a lo menos un IFV', $loopcounter);
        };
        while ($buf_aux =~ /%%IFV(C?)\((\d+)\, *(\d+)\)%%.+?%%\/IFV\1%%/isg) {
            my $ifvc = $1;
            #~ print STDERR "pesouno[$1]\n";
            $div = $2;
            $res = $3;
            $mod = $loopcounter % $div;
            #~ print STDERR "var[$loopcounter] % div[$div] = mod[$mod] y res[$res] y ifvc[$ifvc]\n"; # DEBUG
            # elimina los segmentos q no corresponden, dejando solo uno de acuerdo a la iteracion q toca.
            if ($mod == $res) {
                if ($ifvc) {
                    $ultimo = 'ifvc';
                } else {
                    $ultimo = 'ifv';
                };
                #~ print STDERR "CALZA EN [%%IFV$ifvc($div,$res)%%.+?%%/IFV%%] EN instancias_x_area[$loopcounter]\n";
                #~ print STDERR "ultimo[$ultimo]\n";
                $hash_ifvs{$loopcounter} = $ultimo;

                $localbuf =~ s/%%(IFV$ifvc\($div\, *$res\))%%(.+?)%%\/(IFV$ifvc)%%/##\1##\2##\/\3##/is; # try again (enmascarar)
                last; # try

            };
            if (($key eq 'filler') && ($loopcounter == $div)) {
                #~ print STDERR "STOP LOOP - INSTANCIAS == DIV\n";
                $stop_loop = 1;
            };
        }; # while %%IFV...

        $localbuf =~ s/%%IFV(C?)\(\d+\, *\d+\)%%.+?%%\/IFV\1%%//isg;
        $localbuf =~ s/##/%%/g; # try sian

        # elimino los tags del if que quedo.
        $localbuf =~ s/%%IFVC?\(\d+\, *\d+\)%%//isg;
        $localbuf =~ s/%%\/IFVC?%%//isg;
        # ------------- /IFVs.

        # ------------- NIFVs.
        # Si el contador de articulos para este loop MOD div == res entonces borrar contenido
        $buf_aux = $localbuf;
        ($div, $res, $mod) = '';
        while ($buf_aux =~ /%%NIFV\((\d+)\, *(\d+)\)%%.+?%%\/NIFV%%/isg) {
            $div = $1;
            $res = $2;
            $mod = $loopcounter % $div;
            # print "var[$loopcounter] % div[$div] = mod[$mod] y res[$res]<br>"; # DEBUG

            if ($mod == $res) {
                $localbuf =~ s/%%NIFV\($div\, *$res\)%%.+?%%\/NIFV%%//isg;
            };
        };
        # elimino los tags del if que quedo.
        $localbuf =~ s/%%NIFV\(\d+\, *\d+\)%%//isg;
        $localbuf =~ s/%%\/NIFV%%//isg;
        # ------------- /NIFVs.

        # Parsea datos del artic
        if ($key eq 'filler') {
            #~ print STDERR "Haciendo filler de la iteracion\n";
            my %nodata;
            my %fillerdata;
            $fillerdata{_ts} = $ts_artic;
            $localbuf = &procesa_condicional($localbuf, \%fillerdata, \%nodata);
            $localbuf =~ s/%%.*?%%//g;
        } else {
            # Recupera marcas externas (desde /xdata)
            my %claves_adicionales = $artic_obj->get_xdata($buffer);

            # Procesa condicionales mas algunas variables adicionales
            if ($localbuf ne '') {
                # warn "entra";
                $claves_adicionales{_ts} = $ts_artic;
                $claves_adicionales{_loopcounter} = $loopcounter;
                $claves_adicionales{_totartics} = $totartics;
                $claves_adicionales{_area} = $area;
                # warn $localbuf;
                $localbuf = &procesa_condicional($localbuf, \%campos_xml, \%claves_adicionales);
            };
            my $fullpath_vista = $artic_obj->get_fullpath_artic($mv, $campos_xml{'_plt'});
            $localbuf = $artic_obj->parse_artic_data($fullpath_vista, $localbuf, \%campos_xml, \%claves_adicionales);
        };
        $salida_html .= $localbuf;

        if ($loopcounter >= $totartics) {
            #~ print STDERR "-- Instancias_x_area[$loopcounter] - FINALMENTE TOCO UN[$hash_ifvs{$loopcounter}]\n";
            if ($hash_ifvs{$loopcounter} eq 'ifvc') {
                push @filtered_keys, 'filler';
                if ($loopcounter > 10000) {
                    $stop_loop = 1;
                    #~ print STDERR "STOPLOOP forced\n";
                };
            } else {
                $stop_loop = 1;
                #~ print STDERR "STOPLOOP\n";
            };
        };
        
        #~ print STDERR "Fin de la iteracion $loopcounter / $totartics\n\n";
    };
    #~ print STDERR "Fin del area $area\n------------------ \n\n\n";
    return $salida_html;

}; # parserArea

# ---------------------------------------------------------------
sub procesa_condicional {
    my($buffer) = shift;
    my($vars_common) = shift;
    my($vars_adicionales) = shift;
    my($inicio,$fin,$otro,$aux1,$aux2,$elif,$cont, $marca_ini, $marca_fin, $cont1, $cont2);


    # Agrega algunas claves reservadas que no vienen en el XML, para poder usarlas en los if con operadores
    if (ref $vars_adicionales) {
        foreach my $k (keys %$vars_adicionales) {
            $$vars_common{lc $k} = $$vars_adicionales{$k};
        };
        undef $vars_adicionales;
    };

    # Almacena las claves, pero solo las cque tengan if/nif en la plantilla
    my (%claves);
    while ($buffer =~ /%%(IF|NIF)\(([^\)]+?)\)%%/ig) {
        my $clave = lc $2; # esta clave no es siempre el nombre del campo, ya que puede contener operadores >, =, etc.
        my $nom_campo = $clave;
        $nom_campo = $1 if ($clave =~ /(\w+) *$lib_prontus::IF_OPERATORS/);
        if ($$vars_common{$nom_campo} ne '') {
            $claves{$clave} = $$vars_common{$nom_campo};
        };
        # warn "clave[$clave] y value[$$vars_common{$clave}]";
    };
    undef $vars_common;


    $buffer = &lib_prontus::parser_condicional('IF', $buffer, \%claves);
    $buffer = &lib_prontus::parser_condicional('NIF', $buffer, \%claves);

    return $buffer;

};

# ---------------------------------------------------------------
sub replace_hash_fields {
    my $buffer = shift;
    my $vars2replace = shift;
    my $prontus_style = shift;
    $prontus_style = 1 if ($prontus_style eq ''); # default

    foreach my $k (keys %$vars2replace) {
        my $marca = $k;
        $marca = '%%' . $k . '%%' if ($prontus_style);
        $value = $$vars2replace{$k};
        $buffer =~ s/$marca/$value/isg;
    };
    return $buffer;
};

# ---------------------------------------------------------------
sub fechas_ok {
# Chequea que el rango definido por la fechap/horap y la fechae/horae del artic.
# incluyan la fecha actual, para saber si hay q publicarlo o no.

    my ($ts_preview, $fechap, $horap, $fechae, $horae) = @_;

    $fechap = '9' x 8 if ($fechap eq '');
    $fechae = '9' x 8 if ($fechae eq '');
    $horap = '0' x 6 if ($horap eq '');
    $horae = '0' x 6 if ($horae eq '');

    $horap = $1 . $2 . '00' if ($horap =~ /^(\d\d):?(\d\d)$/);
    if ($horae =~ /^(\d\d):?(\d\d)$/) {
        $horae = $1 . $2 . '00';
    } else {
        print STDERR "horae undef[$horae]\n" if ($DEBUG_FECHAS);
    };


    # ts_now
    my $ts_now;
    if ($ts_preview ne '') {
        $ts_now = $ts_preview;
    }
    else {
        $ts_now = &glib_hrfec_02::get_dtime_pack4(); # TS de AHORA.
        # $ts_now = '20110112000000'; # TS 0 de la mañana
    };

    # ts_p
    my $ts_p = "$fechap$horap";

    # ts_e
    my $ts_e = "$fechae$horae";

    print STDERR "ts_preview[$ts_preview] ts_now[$ts_now] ts_p[$ts_p] ts_e[$ts_e]\n" if ($DEBUG_FECHAS);

    if ( ($ts_p > $ts_now) || ($ts_e < $ts_now) ) {
        return 0; # no publicar articulo # 1.22
    };
    return 1;
};

# ---------------------------------------------------------------
sub replace_mtime {
    my $buf = shift;
    my $path_artic = shift;

    my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,
        $mtime, $ctime,  $blksize,  $blocks)= stat $path_artic;
    my $ts_lastmodif = &glib_hrfec_02::time2ts($mtime);
    # warn("mtime[$mtime]ts_lastmodif[$ts_lastmodif]\n");

    if ($ts_lastmodif =~ /^(\d{8})(\d{6})$/) {
        my $fecham = $1;
        my $horam = $2;
        $buf =~ s/%%_fecham%%/$fecham/ig;

        my $flong = &glib_hrfec_02::expande_fecha($fecham);
        $buf =~ s/%%_FECHAMLONG%%/$flong/ig;

        my $fshrt = &glib_hrfec_02::des_normaliza_fecha($fecham);
        $buf =~ s/%%_FECHAMSHRT%%/$fshrt/isg;

        if ($horam =~ /(\d{2})(\d{2})(\d{2})$/) {
            $horam = $1 . ':' . $2 . ':' . $3;
        };
        $buf =~ s/%%_horam%%/$horam/ig;
        # warn("horam[$horam]");
    } else {

        $buf =~ s/%%_FECHAMLONG%%//ig;
        $buf =~ s/%%_FECHAMSHRT%%//ig;
        $buf =~ s/%%_FECHAM%%//is;
        $buf =~ s/%%_horam%%//ig;
    };
    return $buf;
};


# ---------------------------------------------------------------
sub replace_tsdata {
# Reemplaza TS, FECHAC, FECHACLONG, FECHACSHRT, a partir del TS
    my $buf = $_[0];
    my $ts = $_[1];

    # Timestamp
    if ($ts =~ /^(\d{8})(\d{6})$/) {

        my $fechac = $1;
        my $horac = $2;

        $buf =~ s/%%_TS%%/$ts/isg;

        my $fechaclong = &glib_hrfec_02::expande_fecha($fechac);
        $buf =~ s/%%_FECHACLONG%%/$fechaclong/isg;

        my $fechacshrt = &glib_hrfec_02::des_normaliza_fecha($fechac);
        $buf =~ s/%%_FECHACSHRT%%/$fechacshrt/isg;

        $buf =~ s/%%_FECHAC%%/$fechac/isg;



        if ($horac =~ /(\d{2})(\d{2})(\d{2})$/) {
            $horac = $1 . ':' . $2 . ':' . $3;
        };
        $buf =~ s/%%_horac%%/$horac/isg;


    } else {
        $buf =~ s/%%_TS%%//isg;
        $buf =~ s/%%_FECHACLONG%%//isg;
        $buf =~ s/%%_FECHACSHRT%%//isg;
        $buf =~ s/%%_FECHAC%%//isg;
        $buf =~ s/%%_horac%%//isg;
    };
    return $buf;
};


# ---------------------------------------------------------------
sub parsea_texto {
# Parsea textos en localbuf de portada, ajustando nro. de caracteres.
  my $nomcampo = $_[0];
  # warn "nom_campo enpt[$nomcampo]\n";
  my $valcampo = $_[1];
  my $localbuf = $_[2];
  my $localbuf_aux = $localbuf;
  while ($localbuf_aux =~ /%%$nomcampo\(?\s*([0-9]*)[)]?%%/isg) {   # 1.7
    my $maxchars = $1;
    my $val_campo_ajustado = $valcampo;
    # ajusta el nro de caracteres
    if ( ($valcampo ne '') && ($maxchars > 0) ) {
      $val_campo_ajustado = &ajusta_nchars($valcampo, $maxchars);
    };

    $localbuf = &lib_prontus::replace_in_port($val_campo_ajustado, $nomcampo, $localbuf, $maxchars);
  };
  return $localbuf;
};

# ---------------------------------------------------------------
#sub ajusta_nchars {
## Ajusta el valor del campo de texto al max. nro. de caracteres para publicacion en la portada.
#
#  my ($val_campo, $nchars) = @_;
#  # Saltar los objetos HTMLFILE
#  $val_campo =~ s/<!--(HTMLFILE\w+?)-->.*<!--\/\1-->//isg;
#
#  $val_campo =~ s/<.*?>//sg; # elimino los tags para que no interfieran en el conteo de palabras.
#  $val_campo =~ s/&nbsp\;/ /sg; # elimina los &nbsp; insertados al formateasr el texto (estos marcaban los saltos de linea.) # 1.18
#  # Corta al nro. de caracteres especificado
#  my $val_campo_aux = '';
#
#  $val_campo_aux = $val_campo;
#  $val_campo = '';
#  # Recorrer por palabras.
#  # while ($val_campo_aux =~ /([^\s\b\r\n\t\/=\|@\}\*\[\]\+\{\_\\~]+)/g) {         # 1.21
#  while ($val_campo_aux =~ /([^\s]+)/g) {
#    $val_campo .= $1 . ' ';
#
#    if (length($val_campo) >= $nchars) {
#      last;
#    };
#  };
#  $val_campo =~ s/\s*$//;  # remueve espacio sobrante.
#
#  # Si el texto era mas largo entonces agrego los '...' y el icono 'mas'.
#  if ( length($val_campo_aux) > length($val_campo) ) {
#    $val_campo .= '...';
#  };
#  return $val_campo;
#};
# ---------------------------------------------------------------
sub ajusta_nchars {
    # Ajusta el valor del campo de texto al max. nro. de caracteres para publicacion en la portada.

    my ($val_campo, $nchars, $mode_bytes) = @_;

    # $mode_bytes : 1|0, default 0
    # si es en mode_bytes = 1, ajusta a n bytes
    # si es en mode_bytes = 0, ajusta a n chars (independiente de cuantos bytes sea un char)



    # Saltar los objetos HTMLFILE
    $val_campo =~ s/<!--(HTMLFILE\w+?)-->.*<!--\/\1-->//isg;
    my $val_campo_con_tags = $val_campo;
    $val_campo =~ s/<.*?>//sg; # elimino los tags para que no interfieran en el conteo de palabras.
    $val_campo =~ s/&nbsp\;/ /sg; # elimina los &nbsp; insertados al formateasr el texto (estos marcaban los saltos de linea.) # 1.18
    # Corta al nro. de caracteres especificado



    my $val_campo_original = $val_campo;

    if (length($val_campo_original) <= $nchars ) {
        if ($val_campo_con_tags =~ /^\s*<p>.*<\/p>\s*$/is) {
            $val_campo_original = '<p>' . $val_campo_original . '</p>';
        };
        return $val_campo_original;
    };

    utf8::decode($val_campo_original) if (!$mode_bytes);
    $val_campo = '';
    # Recorrer por palabras.
    my $string_ajustado;
    while ($val_campo_original =~ /([^\s]+)/g) {
    $string_ajustado = $val_campo;
    $val_campo .= ' ' if ($val_campo);
    $val_campo .= $1;

    # print STDERR "val_campo[$val_campo] largo[" . length($val_campo) . "]\n";
    if (length($val_campo) > ($nchars - 3)) { # se restan 3 para que quede espacio para los puntos suspensivos
      last;
    };
    };
    $string_ajustado =~ s/\s*$//;  # remueve espacio sobrante.
    $string_ajustado .= '...' if ($string_ajustado);
    utf8::encode($string_ajustado) if (!$mode_bytes);
    if ($val_campo_con_tags =~ /^\s*<p>.*<\/p>\s*$/is) {
      $string_ajustado = '<p>' . $string_ajustado . '</p>';
    };
    return $string_ajustado;
};

# ---------------------------------------------------------------
sub parser_fechap {
# Parsea fechaplong y fechapshrt en base a fechap en el articulo.
  my ($buffer, $val_campo, $nom_campo) = @_;
  # %%FECHAPLONG%% = Fecha de publicación, en formato largo
  # %%FECHAPSHRT%% = Fecha de publicación, en formato corto
  # %%FECHAP%%     = Fecha de publicación, en formato ISO --> Calza con el 2o. tipo de sustitucion estandar por tanto no se hace nada especial.
  # funciona igual para _fechae

  my $marca_shrt = $nom_campo . 'SHRT';
  my $marca_long = $nom_campo . 'LONG';

  if ($val_campo) {
    $buffer =~ s/%%$nom_campo%%/$val_campo/isg;
    my $fechaplong = &glib_hrfec_02::expande_fecha($val_campo);

    $buffer =~ s/%%$marca_long%%/$fechaplong/isg;

    my $fechapshrt = &glib_hrfec_02::des_normaliza_fecha($val_campo);
    $buffer =~ s/%%$marca_shrt%%/$fechapshrt/isg;
  }
  else {
    $buffer =~ s/%%$marca_shrt%%//isg;
    $buffer =~ s/%%$marca_long%%//isg;
  };

  return $buffer;


};

# ---------------------------------------------------------------
sub get_status_pub {
# Obtiene status de publicacion del articulo.
    my $art = shift;
    my $control_fecha = shift;
    my $controlar_alta_articulos = shift;
    my $base = shift;

    return 1 if (($control_fecha ne 'SI') && ($controlar_alta_articulos ne 'SI'));

    # Conectar a BD si es que no viene la conexion
    if (! ref($base)) {
        # print STDERR "connect a BD dentro\n";
        my $msg_err_bd;
        ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
        if (! ref($base)) {
            die "ERROR: $msg_err_bd\n";
            exit;
        };
    };

    # Obtener datos necesarios del articulo DE LA bd
    my $id = $art;
    $id =~ s/\.\w*$//; # saca extension
    $sql = "select ART_ALTA, ART_FECHAP, ART_HORAP, ART_FECHAE, ART_HORAE from ART where ART_ID = \"$id\"";
    my ($alta, $fechap, $horap, $fechae, $horae);
    my $salida = &glib_dbi_02::ejecutar_sql($base, $sql);
    $salida->bind_columns(undef, \($alta, $fechap, $horap, $fechae, $horae));
    $salida->fetch;
    $salida->finish;

    # Filtro por fechap/horap y fechae/horae del artic
    my $pub = 1; # indicador de si el artic. quedo publicado en el html o no.
    if ($control_fecha eq 'SI') {
        if (! &fechas_ok('', $fechap, $horap, $fechae, $horae)) {
            $pub = 0;
        };
    };
    # Filtro por alta
    if ($controlar_alta_articulos eq 'SI') {
        if (!$alta) {
            $pub = 0;
        };
    };

    return $pub;
};
# ---------------------------------------------------------------
sub parser_condicional {
    my $sentencia = shift;
    my $buffer = shift;
    my $refhash_campos = shift;

    my $cont_condicionales_begin = 0;
    my $cont_condicionales_end = 0;
    my %claves = %$refhash_campos;

    # traduce a mayusculas todos los if y nif del buffer
    $sentencia = uc $sentencia;
    $buffer =~ s/\%\%$sentencia\(/\%\%$sentencia\(/ig;
    $buffer =~ s/\%\%\/$sentencia\%\%/\%\%\/$sentencia\%\%/ig;

    # Cuenta condicionales
    # while ($buffer =~ /\%\%$sentencia\(/g) {
    # 07/10/2011 - CVI - Se mejora deteccion de cierres = aperturas
    while ($buffer =~ /\%\%$sentencia\([^\)]+\)%%/g) {
        $cont_condicionales_begin++;
    };
    while ($buffer =~ /\%\%\/$sentencia\%\%/g) {
        $cont_condicionales_end++;
    };

    if ($cont_condicionales_begin != $cont_condicionales_end) {
        my $err = "Error en marcas $sentencia: la cantidad de aperturas=$cont_condicionales_begin es distinta de la cantidad de cierres=$cont_condicionales_end\n";
        $buffer = $err . $buffer;
        print STDERR $err;
    };


    # Convierte el hash de claves - q se usa para procesar los condicionales - a minusculas
    my %claves_lc;
    my ($kclaves, $kclaves_lc);
    foreach $kclaves (keys %claves) {
        $kclaves_lc = lc $kclaves;
        $claves_lc{$kclaves_lc} = lc $claves{$kclaves};
        # next if ($kclaves =~ /vtxt/); # debug
        # warn "kclaves[$kclaves] valor[$claves{$kclaves}]";
    };

    # Parsea el condicional
    my $cont1 = 0;
    my $inicio;
    my $fin;
    do {
        $cont1++;

        # Busca el primer %%IF( y el primer %%/IF%% desde el principio del string.
        my $marca_ini = '%%' . $sentencia . '(';
        $inicio = index $buffer, $marca_ini;
        my $marca_fin = '%%/' . $sentencia . '%%';
        $fin = index $buffer, $marca_fin;

        if ($cont1 >= 1000) {
            #~ print STDERR "[1] $sentencia : condicionales_begin[$cont_condicionales_begin] condicionales_end[$cont_condicionales_end]\n";
            #~ print STDERR "inicio[$inicio] fin[$fin] elif[$elif]\n";
            return $buffer;
        };

        # $cont_condicionales_begin++ if ($inicio >= 0);
        # $cont_condicionales_end++ if ($fin >= 0);

        # Si encontró ambos, prosigue.
        if (($inicio >= 0) && ($fin >= 0) && ($fin > $inicio)) {

            # Busca otro comienzo de IF que este despues del recien
            # encontrado, pero antes del fin de IF.
            my $cont2 = 0;
            my $otro;
            do {
                $cont2++;
                if ($cont2 >= 1000) {
                    return $buffer;
                };
                $otro = index $buffer, $marca_ini, $inicio + 1;
                # Cada vez que encuentra uno, lo toma como el verdadero comienzo del IF.
                if (($otro > $inicio) && ($otro < $fin)) { $inicio = $otro; };
            } until (($otro < 0) || ($otro > $fin));
            # Ahora tenemos un IF sin ningun otro IF adentro.
            # Rescata el IF, lo que hay antes y lo que hay despues.

            my $elif = substr $buffer, $inicio, ($fin - $inicio + length $marca_fin);
            my $aux1 = substr $buffer, 0, $inicio;
            my $aux2 = substr $buffer, $fin + length $marca_fin;
            # print STDERR "$inicio $fin $elif\n"; # debug
            # Rescata la variable por la que se ha preguntado.
            if ($elif =~ /%%$sentencia\(([^\)]+?)\)%%(.+?)%%\/$sentencia%%/s) {
                my $var = lc $1;  # Variable de control.
                my $contenido = $2; # Contenido del IF

                my $esta = 0;
                if ($sentencia eq 'IF') {
                    if ($var =~ /($lib_prontus::IF_OPERATORS)/) {
                        my $operador = $1;
                        # warn "var[$var] operador[$operador]";
                        my ($nombre,$valor) = split(/ *$operador */,$var,2);
                        # warn "nombre[$nombre] valor[$valor]";
                        $operador = '==' if ($operador eq '=');
                        my $expresion;
                        if ($operador eq '~') {
                            $expresion = '$esta = 1 if ($claves_lc{$var} =~ /$valor/is);';
                        } else {
                            $expresion = '$esta = 1 if ($claves_lc{$var} ' . $operador . ' $valor);';
                        };
                        eval($expresion);
                        # esta = 1 => Deja el contenido, sin poner las marcas.
                        # warn $expresion;
                        # warn "campo[$var] valorizq[$claves_lc{$var}] operador[$operador] valorder[$valor]\n\n";
                    } else {
                        $esta = 1 if ($claves_lc{$var} ne '');
                    };
                };

                if ($sentencia eq 'NIF') {
                    if ($var =~ /($lib_prontus::IF_OPERATORS)/) {
                        my $operador = $1;
                        my ($nombre,$valor) = split(/ *$operador */,$var,2);
                        $operador = '==' if ($operador eq '=');
                        my $expresion;
                        if ($operador eq '~') {
                            $expresion = '$esta = 1 if (!($claves_lc{$var} =~ /$valor/is));';
                        } else {
                            $expresion = '$esta = 1 if (!($claves_lc{$var} ' . $operador . ' $valor));';
                        };
                        eval($expresion);

                    } else {
                        $esta = 1 if ($claves_lc{$var} eq '');
                    };
                };

                if ($esta) {
                    # Deja el contenido, sin poner las marcas.
                    $buffer = $aux1 . $contenido . $aux2;
                }
                else {
                    # Borra el NIF, o sea, concatena el antes con el despues.
                    $buffer = $aux1 . $aux2;
                };

            };
        };
        # print STDERR "inicio[$inicio] fin[$fin] elif[$elif]\n" if ($cont1 == 1000);
    # Repite todo esto hasta que no encuentra ningun otro IF.
    } until (($inicio < 0) || ($fin < 0) || ($fin < $inicio));

    # Borra todos los tags condicionales que quedaron en el buffer.
    $buffer =~ s/%%$sentencia\([^\)]+?\)%%//sg;
    $buffer =~ s/%%\/$sentencia%%//sg;

    if ($cont_condicionales_begin != $cont_condicionales_end) {
        print STDERR "[3] $sentencia : condicionales_begin[$cont_condicionales_begin] condicionales_end[$cont_condicionales_end]\n";
    };


    return $buffer;
};

# ---------------------------------------------------------------
sub get_valcampo_html {
# Dado un texto, obtiene el valor del campo pasado como parametro, considerando
# que esta almacenado de la forma <!--campo=valor--!>
  my $nom_campo = $_[0];
  my $texto_html = $_[1];

  my ($texto, $delimitador_inicio, $delimitador_fin, $valor_campo);

  $texto = $texto_html;
  $texto =~ /<!--\s*$nom_campo\s*=\s*(.*?)\s*-->/;
  $valor_campo = $1;

  return $valor_campo;

};


# --------------------------------------------------------------------#
sub test_servers {
# Prueba que el request provenga de alguno de los servidores permitidos.

  my($referer) = $_[0];
  my($server);
  my($proto) = $prontus_varglb::PROTOCOLO; # 1.23


  return; # referer no sirve con ie6


  foreach $server (@prontus_varglb::SERVER_NAME) {
    if ($referer =~ /^(http|https):\/\/$server\//ig) { # 1.23
      return; # El request proviene de un server habilitado.
    };
  };
  # El request no proviene de ningun server habilitado.
  print "Content-Type: text/html\n\n";
  print "<P>Error de Ejecución - Falta el parámetro requerido. [$referer]";
  exit;

};

# --------------------------------------------------------------------#
sub formatea_lista {
# Formatea el texto submitido como una lista de un elemento por linea,
# aplicando la clase pasada como parametro.
#
# Goodies:
# Sustituye primer %b% por <B> y segundo %b% por </B>.
# Detecta URLs, aplicando un link hacia ellos.

  my($buffer, $class) = ($_[0],$_[1]);
  my($salida,$i) = ('',0);

  # Extrae TODAS las lineas y las pone en el arreglo @LINEAS.
  my(@LINEAS) = split(/<P[^>]*?>/i,$buffer);

  # Formatea las lineas de acuerdo a su contexto.
  for ($i=0; $i<=$#LINEAS; $i++) {
    if ($LINEAS[$i] =~ /^\s*$/) {
      # Inserta espacios para que aparezcan las lineas usadas como separador.
      $LINEAS[$i] = '&nbsp;';
    };
    # Si la linea no esta en blanco, la procesa.
    if ($LINEAS[$i] ne '&nbsp;') {
      # Formatea item reconociendo patrones estandar.
      $LINEAS[$i] =~ s/%b%(.*?)%b%/<B>$1<\/B>/igs; # Bold.
      $LINEAS[$i] =~ s/(\w+?)\W*?[(]*(https?:\/\/[^ ]+[\w\/])[)]*/<A HREF="$2" target="_blank">$1<\/A>/gs; # Linkea URLs. # 7.0
      $LINEAS[$i] =~ s/([^ ]+@[^ ]+) */<A HREF="mailto:$1">$1<\/A>/gs; # Linkea emails.
      # Agrega parrafo a la salida.
      $salida .= "<LI $class>" . $LINEAS[$i] . "</LI>\n";
    }else{
      # Agrega separador a la salida.
      $salida .= "<BR>" . $LINEAS[$i] . "\n";
    };
  };

  return "<UL>$salida</UL>";
};


# --------------------------------------------------------------------#
sub parrafea_texto {
# Formatea el texto submitido, linea a linea.
#

  my($buffer) = ($_[0]);
  my($salida,$i) = ('',0);


  $buffer =~ s/$CRLF/<p>/sg;

  # Extrae TODAS las lineas y las pone en el arreglo @LINEAS.
  my(@LINEAS) = split(/<P[^>]*?>/i,$buffer);

  # Formatea las lineas de acuerdo a su contexto.
  for ($i=0; $i<=$#LINEAS; $i++) {
    # print STDERR "LINEA: $LINEAS[$i]\n\n";
    if ($LINEAS[$i] =~ /^\s*$/) {
      # Inserta espacios para que aparezcan las lineas usadas como separador.
      $LINEAS[$i] = '&nbsp;';
    };
    # Agrega parrafo a la salida.
    $salida .= $LINEAS[$i] . "</p>\n<p>";
  };

  # Saca ult. ret.
  $salida =~ s/<\/p>\n<p>$/<\/p>/i;
  $salida = '<p>' . $salida if ($salida =~ /\w/); # esto es para asegurarse que el texto quede rodeado de <p>...</p>

  return $salida;
};
# ---------------------------------------------------------------
sub get_xml_data {
  # Cargar xml del articulo a partir del path a su html o bien del mismo xml.
  my ($path_final_xml) = $_[0];
  if ($path_final_xml !~ /\.xml$/) {
    $path_final_xml =~ s/\/pags\/(\w+)(\.\w+)?$/\/xml\/\1\.xml/;
  };

  my $xml = &glib_fildir_02::read_file($path_final_xml);

  $xml = &ajusta_crlf($xml);


  my ($priv, $pub);
  if ($xml =~ /<_PRIVATE>(.*?)<\/_PRIVATE>/isg) {
    $priv = $1;
  };
  if ($xml =~ /<_PUBLIC>(.*?)<\/_PUBLIC>/isg) {
    $pub = $1;
  };
  return "$priv\n$pub";
};

# --------------------------------------------------------------------#
sub formatea_texto_simple {
# Formatea el texto submitido, linea a linea, aplicando la clase pasada como parametro.
#
# Goodies:
# Sustituye primer %e1% por <span class=e1> y segundo por </span>. El estilo debe estar definido como css.
# Si la linea consiste en cuatro o m‡s ----, la sustituye por un <HR>.
# Detecta URLs (de la forma '(http://..)'), aplicando un link sobre la palabra anterior
# al string http.

  my($buffer) = ($_[0]);
  my($salida,$i) = ('',0);



  # Extrae TODAS las lineas y las pone en el arreglo @LINEAS.
  my(@LINEAS) = split(/<p[^>]*?>/i,$buffer);

  # Formatea las lineas de acuerdo a su contexto.
  for ($i=0; $i<=$#LINEAS; $i++) {
    # print STDERR "LINEA: $LINEAS[$i]\n\n";
    if ($LINEAS[$i] =~ /^\s*$/) {
      # Inserta espacios para que aparezcan las lineas usadas como separador.
      $LINEAS[$i] = '&nbsp;';
    };
    # Si la linea no esta en blanco, la clasifica como titulo o parrafo.
    if ($LINEAS[$i] ne '&nbsp;') {
      # Formatea parrafo reconociendo patrones estandar.

      $LINEAS[$i] =~ s/%b%(.*?)%b%/<b>\1<\/b>/igs; # 1.1 Bold. %b%hola%b%mmmmmm%b%hola%b% 8.0 se realiza 1o. este parseo antes del estilo.
      $LINEAS[$i] =~ s/%i%(.*?)%i%/<i>\1<\/i>/igs; # 1.1 Italic. %i%hola%i%mmmmmm%i%hola%i% 8.0 se realiza 1o. este parseo antes del estilo.

      # estilo cualquiera menos %t% que se reserva para subtitulos y %b% que se reserva para el bold.
      $LINEAS[$i] =~ s/%([^tbi%].+?)%(.*?)%\1%/<span class=\1>\2<\/span>/gs;

      $LINEAS[$i] =~ s/<span class=(d|D)(.*?)>(.*?)<\/span>/<div class=\1\2>\3<\/div>/isg;

      # Linkea urls. Linkea el conjunto de palabras ubicadas dentro del parentesis anterior al de la url.
      # Si no se especifica parentesis antes de la url, linkea la palabra inmediatamente anterior.
      # 1.8 Si la URL comienza con _http implica target = self, si no se pone el '_' implica target='_blank'.

      # 1.1 modificado en # 1.8
      if ($LINEAS[$i] !~ s/\(([^)]+?)\)\s*?[(](https?:\/\/[^ )<]+[\w\/])[)]*/<A HREF="\2" target="_blank">\1<\/A>/igs) { # 7.0
        $LINEAS[$i] =~ s/([\w¿\-ÿ\?]+?)\s*?[(](https?:\/\/[^ )<]+[\w\/])[)]*/<A HREF="\2" target="_blank">\1<\/A>/igs;  # 7.0
      };

      # 1.2 modificado en # 1.8
      if ($LINEAS[$i] !~ s/\(([^)]+?)\)\s*?[(]\_(https?:\/\/[^ )<]+[\w\/])[)]*/<A HREF="\2">\1<\/A>/igs) { # 7.0
        $LINEAS[$i] =~ s/([\w¿\-ÿ\?]+?)\s*?[(]\_(https?:\/\/[^ )<]+[\w\/])[)]*/<A HREF="\2">\1<\/A>/igs;   # 7.0
      };


      $LINEAS[$i] =~ s/([^ ]+@[^ ]+)/<A HREF="mailto:\1">\1<\/A>/igs; # Linkea emails.
      $LINEAS[$i] =~ s/(<A HREF="mailto:)(.+?)\.?(">)/\1\2\3/igs; # sacar posible ultimo punto.
    };

    $salida .= $LINEAS[$i];

  };

  return $salida;
};

# -------------------------------------------------------------------------#
sub reverse_format {
# Sustituye <span class=xx> y </span> por %xx%.
# Sustituye <HR> por una linea de cinco '-' (-----).
# Detecta URLs, volviendo a la notacion de edicion (palabra(http://..))
# Cambia los mailto:...., dejando solo la direccion electronica.

my($buffer) = $_[0];

  # Cambiar URLs.


  # 1.2
  # Si no resulta el parseo con target, aplicar el sin target.
  $buffer =~ s/<A HREF="(https?:\/\/[^"]+?)" *>(.+?)<\/A>/\(\2\)\(\_\1\)/igs; # 1.8 # 7.0

  $buffer =~ s/<A HREF=\"(https?:\/\/[^"]+?)\" *target=\"(\_)blank\".*?>(.+?)<\/A>/\(\3\)\(\1\)/igs;

  # Cambiar subtitulos a %t%...%t%. Dejo un espacio para que no se peguen los tags de sustitucion y formen un'%%xxx%%' que depues sera borrado.
  # $buffer =~ s/<A NAME=T\d+?>\s*?([^\s].*?)\s*?<\/A>/%t% $1 %t%/igs;
  $buffer =~ s/<!---_SUBTIT_HTML--->.*?<!---_SUBTIT--->(.*?)<!---\/_SUBTIT--->.*?<!---\/_SUBTIT_HTML--->/%t% $1 %t%/isg;


  # 1.1 Bold.
  $buffer =~ s/<B>([^<].*?)<\/B>/%b%\1%b%/igs;
  $buffer =~ s/<I>([^<].*?)<\/I>/%i%\1%i%/igs;

  # Cambiar estilo.
  $buffer =~ s/<span class=(.+?)>(.*?)<\/span>/%\1%\2%\1%/igs;
  $buffer =~ s/<div class=(.+?)>(.*?)<\/div>/%\1%\2%\1%/igs;



  # Cambiar <hr>
  $buffer =~ s/<HR.*?>/-----/isg;

  # Cambia mailto:...
  $buffer =~ s/<A HREF="mailto:.+?".*?>(.+?)<\/A>/\1/igs;

  return $buffer;

}
# -------------------------------------------------------------------------#
sub escape_html {
# Escapea lo minimo para que el texto no interfiera con los tags HTML.

    my($toencode) = $_[0];
    my($i, $conte, $toencode_aux, @html_puro);

    # 1.14
    # Dentro del buffer se sustituyen los segmentos html por marcas del tipo %%HTML[1]%%
    # las que despues del miniescape seran sustituidas por los contenidos reales.
#    $i = 0;
#    $toencode_aux = $toencode;
#    while ($toencode_aux =~ /%HTML%(.*?)%\/HTML%/isg) {
#      $html_puro[$i] = $1;
#
#      $paso = $html_puro[$i];
#      # print "<br>paso:$paso";       # debug
#      # print "<br>toencode antes de la ER:$toencode";       # debug
#      $toencode =~ s/%HTML%\Q$paso\E%\/HTML%/%%HTML\[$i\]%%/is;
#      # print "<br>html_puro : $html_puro[$i] y toencode:$toencode";       # debug
#      $i++;
#    };


    $toencode=~s/&([^#][^0-9]+)/&amp;\1/g;             # Antes que nada, traduce los ampersands. # 1.19 correccion a e.r.
    $toencode=~s/>/&gt;/g;              # >
    $toencode=~s/"/&quot;/g;            # " # 8.0
    $toencode=~s/'/&#39;/g;
    $toencode=~s/</&lt;/g;              # <

    # print STDERR "toencode1[$toencode]\n";
    # $toencode = &tildes2html($toencode);
    # print STDERR "toencode2[$toencode]\n\n";
    # 1.14
    # Ahora restituye los contenidos de html puro.
#    for ($i=0; $i<=$#html_puro; $i++) {
#      # print "<br>paso y toencode antes:[$toencode]"; # debug
#      $conte = $html_puro[$i];
#
#      # 8.0
#      # Si en el html viene el tag body, se asume que es una pagina, por lo que se toma solo lo de adentro.
#      if ($conte =~ /<body.*?>(.*)<\/body *>/is) {
#        $conte = $1;
#      };
#
#      $toencode =~ s/%%HTML\[$i\]%%/%HTML%$conte%\/HTML%/is;
#      # print "<br>y toencode despues:[$toencode]"; # debug
#    };

    return $toencode;

};

# -------------------------------------------------------------------------#
# Detecta y pone en html los caracteres con tildes.

sub tildes2html {
    my($to_encode) = $_[0];

    $to_encode=~s/\x86/&Yacute;/g;
    $to_encode=~s/\x87/&brvbar;/g;
    $to_encode=~s/\x8B/&eth;/g;
    $to_encode=~s/\x95/&middot;/g;
    $to_encode=~s/\x96/&shy;/g;


    $to_encode=~s/\xA6/&#166;/g;
    $to_encode=~s/\xAF/&#175;/g;
    $to_encode=~s/\xB2/&#178;/g;
    $to_encode=~s/\xB3/&#179;/g;
    $to_encode=~s/\xB9/&#185;/g;
    $to_encode=~s/\xBC/&#188;/g;
    $to_encode=~s/\xBD/&#189;/g;
    $to_encode=~s/\xBE/&#190;/g;
    $to_encode=~s/\xD7/&#215;/g;

    $to_encode=~s/\xA1/&iexcl;/g;
    $to_encode=~s/\xA2/&cent;/g;
    $to_encode=~s/\xA3/&pound;/g;
    $to_encode=~s/\xA4/&curren;/g;
    $to_encode=~s/\xA5/&yen;/g;
    $to_encode=~s/\xA7/&sect;/g;
    $to_encode=~s/\xA8/&uml;/g;
    $to_encode=~s/\xA9/&copy;/g;
    $to_encode=~s/\xAA/&ordf;/g;
    $to_encode=~s/\xAC/&not;/g;
    $to_encode=~s/\xAD/&shy;/g;
    $to_encode=~s/\xAE/&reg;/g;
    $to_encode=~s/\xB0/&deg;/g;
    $to_encode=~s/\xB1/&plusmn;/g;
    $to_encode=~s/\xB4/&acute;/g;
    $to_encode=~s/\xB5/&micro;/g;
    $to_encode=~s/\xB6/&para;/g;
    $to_encode=~s/\xB7/&middot;/g;
    $to_encode=~s/\xB8/&cedil;/g;
    $to_encode=~s/\xBA/&ordm;/g;
    $to_encode=~s/\xBB/&raquo;/g;
    $to_encode=~s/\xBF/&iquest;/g;
    $to_encode=~s/\xC0/&Agrave;/g;
    $to_encode=~s/\xC1/&Aacute;/g;
    $to_encode=~s/\xC2/&Acirc;/g;
    $to_encode=~s/\xC3/&Atilde;/g;
    $to_encode=~s/\xC4/&Auml;/g;
    $to_encode=~s/\xC5/&Aring;/g;
    $to_encode=~s/\xC6/&AElig;/g;
    $to_encode=~s/\xC7/&Ccedil;/g;
    $to_encode=~s/\xC8/&Egrave;/g;
    $to_encode=~s/\xC9/&Eacute;/g;
    $to_encode=~s/\xCA/&Ecirc;/g;
    $to_encode=~s/\xCB/&Euml;/g;
    $to_encode=~s/\xCC/&Igrave;/g;
    $to_encode=~s/\xCD/&Iacute;/g;
    $to_encode=~s/\xCE/&Icirc;/g;
    $to_encode=~s/\xCF/&Iuml;/g;
    $to_encode=~s/\xD1/&Ntilde;/g;
    $to_encode=~s/\xD2/&Ograve;/g;
    $to_encode=~s/\xD3/&Oacute;/g;
    $to_encode=~s/\xD4/&Ocirc;/g;
    $to_encode=~s/\xD5/&Otilde;/g;
    $to_encode=~s/\xD6/&Ouml;/g;

    $to_encode=~s/\xD8/&Oslash;/g;
    $to_encode=~s/\xD9/&Ugrave;/g;
    $to_encode=~s/\xDA/&Uacute;/g;
    $to_encode=~s/\xDB/&Ucirc;/g;
    $to_encode=~s/\xDC/&Uuml;/g;
    $to_encode=~s/\xDD/&Yacute;/g;
    $to_encode=~s/\xDE/&THORN;/g;
    $to_encode=~s/\xDF/&szlig;/g;
    $to_encode=~s/\xE0/&agrave;/g;
    $to_encode=~s/\xE1/&aacute;/g;
    $to_encode=~s/\xE2/&acirc;/g;
    $to_encode=~s/\xE3/&atilde;/g;
    $to_encode=~s/\xE4/&auml;/g;
    $to_encode=~s/\xE5/&aring;/g;
    $to_encode=~s/\xE6/&aelig;/g;
    $to_encode=~s/\xE7/&ccedil;/g;
    $to_encode=~s/\xE8/&egrave;/g;
    $to_encode=~s/\xE9/&eacute;/g;
    $to_encode=~s/\xEA/&ecirc;/g;
    $to_encode=~s/\xEB/&euml;/g;
    $to_encode=~s/\xEC/&igrave;/g;
    $to_encode=~s/\xED/&iacute;/g;
    $to_encode=~s/\xEE/&icirc;/g;
    $to_encode=~s/\xEF/&iuml;/g;
    $to_encode=~s/\xF0/&eth;/g;
    $to_encode=~s/\xF1/&ntilde;/g;
    $to_encode=~s/\xF2/&ograve;/g;
    $to_encode=~s/\xF3/&oacute;/g;
    $to_encode=~s/\xF4/&ocirc;/g;
    $to_encode=~s/\xF5/&otilde;/g;
    $to_encode=~s/\xF6/&ouml;/g;
    $to_encode=~s/\xF7/&divide;/g;
    $to_encode=~s/\xF8/&oslash;/g;
    $to_encode=~s/\xF9/&ugrave;/g;
    $to_encode=~s/\xFA/&uacute;/g;
    $to_encode=~s/\xFB/&ucirc;/g;
    $to_encode=~s/\xFC/&uuml;/g;
    $to_encode=~s/\xFD/&brvbar;/g;
    $to_encode=~s/\xFE/&thorn;/g;
    $to_encode=~s/\xFF/&yuml;/g;


    $to_encode=~s/\x83/&#131;/g;

    $to_encode=~s/\x85/&#133;/g;

    $to_encode=~s/\x88/&#136;/g;
    $to_encode=~s/\x89/&#137;/g;
    $to_encode=~s/\x8A/&#138;/g;

    $to_encode=~s/\x8C/&#140;/g;

    $to_encode=~s/\x8E/&#142;/g;


    $to_encode=~s/\x91/&#145;/g;
    $to_encode=~s/\x92/&#146;/g;

    $to_encode=~s/\x97/&#151;/g;

    $to_encode=~s/\x99/&#153;/g;
    $to_encode=~s/\x9A/&#154;/g;

    $to_encode=~s/\x9C/&#156;/g;

    $to_encode=~s/\x9E/&#158;/g;
    $to_encode=~s/\x9F/&#159;/g;

    return $to_encode;
};



# -------------------------------------------------------------------------#
sub escape_cdata {
# Realiza escapeos minimos para poder guardar el campo tipo txt dentro de un cdata
# al interior de un XML.
  my $valor = $_[0];
  $valor =~ s/]]>/]] >/sg; # para q no interfiera con cdata
  # No realiza ningun escapeo adicional para efectos de compatibilidad HTML!!

  return $valor;
};

# -------------------------------------------------------------------------#
sub replace_in_port {
  my $valor = $_[0];
  my $nom_campo = $_[1];
  my $buffer = $_[2];
  my $maxchars = $_[3]; # \d

  # warn "replace: nom_campo[$nom_campo] valor[$valor] maxchars[$maxchars]\n";

  if ($maxchars) {
    $buffer =~ s/%%$nom_campo[(]$maxchars[)]%%/$valor/isg;
  }
  else {
    # $buffer =~ s/%%$nom_campo([(]\w+?\,?\s*[0-9]*[)])?%%/$valor/isg;
    $buffer =~ s/%%$nom_campo%%/$valor/isg;
  };

  # deprecated: Ahora parsear en la pagina la version minitext del campo TXT_identif --> identif
  # Esto ahora se hace directamente al detectar el campo.



  return $buffer;
};
# -------------------------------------------------------------------------#
sub replace_in_artic {
    my $valor_campo = shift;
    my $nom_campo = shift;
    my $buffer = shift;
    # print STDERR "nom_campo[$nom_campo] - valor_campo[$valor_campo]\n";

    $valor_campo =~ s/< *\?/< &#63;/g; # elimina secuencias <?
    $valor_campo =~ s/%%/&#37;&#37;/sg; # para poder poner nombres de marcas

    # Cambia rets carro por <p>
    $valor_campo = &parrafea_texto($valor_campo) if ($nom_campo =~ /^_?TXT_/i);

    # sustitucion en la pagina
    $buffer =~ s/%%$nom_campo%%/$valor_campo/isg;

    # parsea marcas con ajuste de chars
    if ($nom_campo !~ /^asocfile_|^swf_|^multimedia_|^fotofija_|^_hfoto|^_wfoto|^chk_cuadrar_fotofija|^_NOMfoto_|^foto_\d+/i) {
        $buffer = &parse_maxchars($nom_campo, $valor_campo, $buffer);
    };

    # Ahora parsear en la pagina la version minitext del campo TXT_identif --> identif
    if ($nom_campo =~ /^(_)?V?TXT_(\w+?)$/i) {
        my $nom_minitext = $1 . $2;

        # parse minitext
        my $minitext = &get_minitext_value($valor_campo);
        $buffer =~ s/%%$nom_minitext%%/$minitext/isg;

        # parse minitext con max chars
        $buffer = &parse_maxchars($nom_minitext, $minitext, $buffer);

        # parse codetext
        my $nom_codetext = $nom_minitext . '.code';
        my $codetext = &get_codetext_value($valor_campo);
        $buffer =~ s/%%$nom_codetext%%/$codetext/isg;

        # parse codetext con max chars
        $buffer = &parse_maxchars($nom_codetext, $codetext, $buffer);

        # parse rss text (es un minitext, pero escapeado para xml)
        my $nom_rsstext = $nom_minitext . '.xml';
        my $rsstext = &escape_xml($minitext);
        $buffer =~ s/%%$nom_rsstext%%/$rsstext/isg;
        # print STDERR "nom_minitext[$nom_minitext] - minitext[$minitext]\n";

        # parse strip.
        my $nom_striptext = $nom_minitext . '.strip';
        my $striptext = &strip_text($valor_campo);
        $buffer =~ s/%%$nom_striptext%%/$striptext/isg;

    };

    return $buffer;
};
# -------------------------------------------------------------------------#
sub strip_text {
    my $toencode = $_[0];

    $toencode = &saca_tags_rets($toencode);
    $toencode = &notildes($toencode);
    $toencode = lc $toencode;
    $toencode =~ s/[^a-z0-9_ ]//sg;
    $toencode =~ s/ {2,}//sg;
    $toencode =~ s/\s/_/sg;

    return $toencode;
}
# -------------------------------------------------------------------------#
sub get_minitext_value {

    my($toencode) = $_[0];

    $toencode =~ s/\r\n/ /sg;
    $toencode =~ s/\n/ /sg;
    $toencode =~ s/\r/ /sg;
    $toencode =~ s/<.*?>/ /sg;
    $toencode =~ s/ {2,}/ /sg;
    $toencode =~ s/ $//sg;
    $toencode =~ s/^ //sg;
    return $toencode;
};
# -------------------------------------------------------------------------#
sub get_codetext_value {

    my($toencode) = $_[0];
    $toencode = &get_minitext_value($toencode);

    # convierte a latin1 para poder aplicar la er
    utf8::decode($toencode);
    # caracteres imprimibles, del 33(dec) en adealnte, exceptuando caracteres no imprimibles.
    $toencode =~ s/[^\x20-\x7e\x80\x82-\x9c\x9e-\xff]//sg;
    # restaura a utf8
    utf8::encode($toencode);

    $toencode =~ s/\\/\\\\/sg;
    $toencode=~ s/"/\\"/sg;
    $toencode=~ s/&quot;/\\"/sg;
    $toencode =~ s/'/\\'/sg;
    $toencode =~ s/&#39;/\\'/sg;


    return $toencode;
};
# -------------------------------------------------------------------------#
sub parse_maxchars {
    my $nom_campo = shift;
    my $valor_campo = shift;
    my $buffer = shift;

    my $buffer_aux = $buffer;
    while ($buffer_aux =~ /%%$nom_campo(\(\s*([0-9]*)\))%%/isg) {   # 1.7
        my $marca_maxchars = $1;
        my $maxchars = $2;
        if (($maxchars > 0) && ($valor_campo)) {
            $valor_campo = &ajusta_nchars($valor_campo, $maxchars);
        };
        $buffer =~ s/%%$nom_campo\Q$marca_maxchars\E%%/$valor_campo/ig;
    };
    return $buffer;
};
# -------------------------------------------------------------------------#
sub parsea_subtits {
  # Parsea subtits en campos TXT en articulos

  my $valor = $_[0];
  my $tithtml = $_[1];
  my $reldir_art = $_[2];
  my $artic = $_[3];
  my $looptit = $_[4];
  my $nom_campo = $_[5];
  my $nrotit = $_[6];

  my $subtits = $_[7]; # hash con items del menu de subtits listos para ser incluidos en el menu.

  if ($tithtml eq '') {
    $tithtml = $prontus_varglb::DEFAULT_TITHTML; # $DEFAULT_TITHTML = '<A NAME=%%TITANAME%%><h2>%%TIT%%</h2></A>';
  };

  # Manejar marcas de titulos
  $nrotit = '0' if ($nrotit eq '');
  while ($valor =~ s/%t%(.*?)%t%/<!---_SUBTIT_HTML--->$tithtml<!---\/_SUBTIT_HTML--->/s) {
    my $tit = $1;
    # print STDERR "tit[$tit]\n";
    $tit =~ s/\s*$//; # Sacar posibles espacios al final.
    $tit =~ s/^\s*//; # Sacar posibles espacios al ppio.
    my $looptit_aux = $looptit;
    # $looptit_aux =~ s/%%_SUBTIT_KEY%%/$reldir_art\/$artic#T$nrotit/ig;
    $looptit_aux =~ s/%%_SUBTIT_KEY%%/#T$nrotit/ig;
    $looptit_aux =~ s/%%_SUBTIT%%/$tit/ig;
    $$subtits{$nrotit} = $looptit_aux; # acumula item para ponerlo despues en el menu

    $valor =~ s/%%_SUBTIT%%/<!---_SUBTIT--->$tit<!---\/_SUBTIT--->/i;
    $valor =~ s/%%_SUBTIT_ANAME%%/T$nrotit/i;

    $nrotit = $nrotit + 1;
  };

  return ($valor, $nrotit, %$subtits);
};
# -------------------------------------------------------------------------#
sub parsea_subtits_port {
  # Obtiene subtits de campos del articulo para poner el menu en un area de la portada

  my ($cont_xml, $reldir_art, $artic, $looptit) = @_;

  my $nrotit = '0';

  my %subtits;


  # Rescata de los vtxt
  while ($cont_xml =~ /(<[^<>]*? class=["']?subtit(\d?)["']?[ >][^<]*?<\/\w+?>)/isg) {
    my $stit = $1;
    my $level_subtit = $2;
    my $tag = $stit;
    $stit =~ s/<.+?>//isg;
    $stit =~ s/<\/.+?>//isg;

    $stit =~ s/\s*$//; # Sacar posibles espacios al final.
    $stit =~ s/^\s*//; # Sacar posibles espacios al ppio.

    next if ($stit !~ /\w/);


    my $looptit_aux = $looptit;

    # print STDERR "stit[$stit]\n";

    # $looptit_aux =~ s/%%_SUBTIT_KEY%%/$reldir_art\/$artic#T$nrotit/ig;
    $looptit_aux =~ s/%%_SUBTIT_KEY%%/#T$nrotit/ig;
    $looptit_aux =~ s/%%_SUBTIT%%/$stit/ig;
    $looptit_aux =~ s/%%_level_subtit%%/$level_subtit/ig;
    $subtits{$nrotit} = $looptit_aux; # acumula item para ponerlo despues en el menu

    $nrotit = $nrotit + 1;
  };




  # Rescata marcas de subtits de los txt
  while ($cont_xml=~ /<!---_SUBTIT--->(.*?)<!---\/_SUBTIT--->/sg) {
    my $tit = $1;
    # print STDERR "tit[$tit]\n";
    $tit =~ s/\s*$//; # Sacar posibles espacios al final.
    $tit =~ s/^\s*//; # Sacar posibles espacios al ppio.
    my $looptit_aux = $looptit;
    # $looptit_aux =~ s/%%_SUBTIT_KEY%%/$reldir_art\/$artic#T$nrotit/ig;
    $looptit_aux =~ s/%%_SUBTIT_KEY%%/#T$nrotit/ig;
    $looptit_aux =~ s/%%_SUBTIT%%/$tit/ig;
    $looptit_aux =~ s/%%_level_subtit%%//ig; # sin compatibilidad
    $subtits{$nrotit} = $looptit_aux; # va armando el menu
    $nrotit = $nrotit + 1;
  };



  # Generar menu de subtits ordenado
  my $st;
  my $str_subtits;
  foreach $st (sort{$a <=> $b}(keys %subtits)) {
    $str_subtits .= $subtits{$st} . "\n";
  };

  return $str_subtits;
};

# -------------------------------------------------------------------------#
sub replace_in_xml { # tal vez esto debiera estar en Artic
    my ($xml_base, $nom_campo, $valor, $parse_as_cdata) = @_;

    # esto es necesario en html, no en xml
    # $valor =~ s/< *\?/< &#63;/g; # elimina secuencias <?


    if ($parse_as_cdata) {
        $valor = &lib_prontus::escape_cdata($valor);
    } else {
        $valor = &lib_prontus::escape_xml($valor);
    };

    if ($nom_campo =~ /^fotofija_/) {
        if ($valor =~ /^https?\:\/\/$prontus_varglb::IP_SERVER/i) {
            $valor =~ s/^https?\:\/\/$prontus_varglb::IP_SERVER//i; # foto local, asi q saca el server name.
        };
        if ($valor =~ /^https?\:\/\/$prontus_varglb::PUBLIC_SERVER_NAME/i) {
            $valor =~ s/^https?\:\/\/$prontus_varglb::PUBLIC_SERVER_NAME//i; # foto local, asi q saca el server name.
        };
    };


    if ($parse_as_cdata) {
        if (!($xml_base =~ s/<$nom_campo>.*?<\/$nom_campo>/<$nom_campo>\n<!\[CDATA\[$valor\]\]>\n<\/$nom_campo>/is)) {
            $xml_base =~ s/<\/_public>/<$nom_campo>\n<!\[CDATA\[$valor\]\]>\n<\/$nom_campo>\n<\/_public>/i;
        };
    }
    else {
        if (!($xml_base =~ s/<$nom_campo>.*?<\/$nom_campo>/<$nom_campo>$valor<\/$nom_campo>/is)) {
            $xml_base =~ s/<\/_public>/<$nom_campo>$valor<\/$nom_campo>\n<\/_public>/i;
        };
    };

    return $xml_base;
};


# -------------------------------------------------------------------------#
sub saca_tags_rets {
# Elimina tags y ret. de carro.

    my($toencode) = $_[0];

    $toencode =~ s/\r\n/ /sg;
    $toencode =~ s/\n/ /sg;
    $toencode =~ s/\r/ /sg;
    $toencode =~ s/<.*?>/ /sg;
    $toencode =~ s/ {2,}/ /sg;
    $toencode =~ s/ $//sg;
    $toencode =~ s/^ //sg;
    $toencode=~ s/"/'/g;
    $toencode=~ s/&quot;/'/g;
    my $inclinada = "´";
    utf8::encode($inclinada);
    $toencode =~ s/'/$inclinada/sg; # cambia comilla vertical por comilla inclinada, para compatib. JS
    $toencode =~ s/&#39;/$inclinada/sg; # cambia comilla vertical por comilla inclinada, para compatib. JS

    return $toencode;

};
# -------------------------------------------------------------------------
sub get_last_edic {
# Retorna el nombre del directorio de ediciones mas nuevo, el que corresp. al nombre de
# la edicion mas nueva.
# Param: 0) Path absoluto al dir de ediciones
my $dir_hpage = $_[0];
my (@entries, $entry);

  @entries = &glib_fildir_02::lee_dir($dir_hpage);

  #  Utiliza un hash auxiliar con las fecha de las ediciones en iso + el correlativo para ordenar.
  my %aux_sort;
  foreach $entry (@entries) {
    $entry =~ /^(\d\d\d\d)\_(\d\d)\_(\d\d)\_(\d+)$/;
    my $aaaammddnro = $1 . $2 . $3 . $4;
    $aux_sort{$entry} = $aaaammddnro;
  };

  # Ordena numericamente de mayor a menor.
  @entries = sort { $aux_sort{$b} <=> $aux_sort{$a} } @entries;

  # Ordenar descendentemente.
  foreach $entry (@entries) {
    if ($entry !~ /^\./g) {
      # Si es un dir valido
      if ( -d "$dir_hpage/$entry" ) {
        return $entry;
      };
    };
  };
};
# ---------------------------------------------------------------
sub check_dirs_edic() {
# Chequea existencia de dirs. de trabajo de la edicion seleccionada.

  my ($dir_dest_edic) = $_[0];
  my ($dir);

  # Dir de la edicion.
  if ( ! (&glib_fildir_02::check_dir($dir_dest_edic)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de la edicion no es válido");
    exit;
  };

  # Dir de portadas de la edicion.
  $dir = $dir_dest_edic . $prontus_varglb::DIR_SECC;
  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de portadas de la edición no es válido");
    exit;
  };

  # destino del xml de las portadas de la edicion
  $dir =~ s/$prontus_varglb::DIR_SECC$/\/xml/;
  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio del xml de portadas de la edición no es válido");
    exit;
  }
  else {
    # Escribe htaccess en el dir de xml para prhibir acceso http a este.
    &glib_fildir_02::write_file("$dir/.htaccess", "Order Allow,Deny\nDeny from all");
  };

  # Dir de hpage de la edicion
  $dir = $dir_dest_edic . $prontus_varglb::DIR_HPAGES;
  if ( ! (&glib_fildir_02::check_dir($dir)) ) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","El directorio de homepage de la edición no es válido");
    exit;
  };


};

#---------------------------------------------------------------
sub generar_popupdirs_from_dir {
# Genera un objeto de lista de seleccion html con la lista de DIRECTORIOS
# de un directorio dado, ordenados alfabeticamente.
# La lista generada utiliza el nombre del arch. s/path tanto para el valor de display
# como para los valores clave del combo.

# Parametros :
# 0) Path absoluto al directorio
# 1) Name que se le dara al popup generado
# 2) Valor clave en el que hay que dejar posicionado el combo.
# 3) Nro. de items visibles simultaneamente.
# 4) Indicador de seleccion multiple ('' o 'MULTIPLE')

# 5) Registro adicional con clave '', por ej. 'Todos'.
# 6) Codigo javascript a invocar con el objeto.
# 7) Nro. maximo de elementos a cargar.
# 8) Criterio de orden ('NUMASC' | 'STRASC' | 'NUMDESC' | 'STRDESC' | 'NOSORT') si es 'NOSORT', enonces no se aplica ordenamiento.
#    Equivalencias : NUMERICO ASCENDENTE | STRING ASCENDENTE | NUMERICO DESCENDENTE | STRING DESCENDENTE

# Retorna : Lista de seleccion con datos, lista para imprimirla.

  my($path_dir) = $_[0];
  my($name_obj) = $_[1];
  my($valor_clave) = $_[2];
  my($items_visibles) = $_[3];
  my($ind_multiple) = $_[4];
  my($adicional) = $_[5];
  my($javascript) = $_[6];
  my($max_elem) = $_[7];
  my($criterio_orden) = $_[8];

  my(@entries, $lista, $nom_arch, $seleccionado, $nro_elem, $entry);


  # Abre directorio.
  opendir(DIR, $path_dir) || die "Can't opendir" . $path_dir . $!;
  @entries = readdir(DIR);
  closedir DIR;

  # Ordena entries
  if ($criterio_orden eq 'NUMASC') {
    # Ascendentemente.
    @entries = sort {$a <=> $b} (@entries);
  }
  elsif ($criterio_orden eq 'NUMDESC') {
    # Descendentemente.
    @entries = sort {$b <=> $a} (@entries);
  }
  elsif ($criterio_orden eq 'STRASC') {
    # Descendentemente.
    @entries = sort {$a cmp $b} (@entries);
  }
  elsif ($criterio_orden eq 'STRDESC') {
    # Descendentemente.
    @entries = sort {$b cmp $a} (@entries);
  };


  # Generar la lista de seleccion en html
  $lista = '<select id="' . $name_obj . '" name="' . $name_obj . '" size="' . $items_visibles . '" ' . $ind_multiple . ' ' . $javascript . '>';

  if ($adicional ne '') {
    $lista = $lista . '<option value="" ' . $seleccionado . '>';
    $lista = $lista . $adicional;
  }

  $nro_elem = 0;
  foreach $entry (@entries) {
    if ($entry !~ /^\./g) {
      if ((-d("$path_dir/$entry")) and ($nro_elem < $max_elem)) {
        $nom_arch = $entry;

        $seleccionado = '';
        if ( $nom_arch eq $valor_clave ) {
           $seleccionado = 'selected="selected"';
        }
        $lista = $lista . '<option value="' . $nom_arch . '" ' . $seleccionado . '>';
        if ($ind_extension eq 'SIN_EXT') {
          $nom_arch =~ s/\..*//; # borrar extension en el display.
        }
        $lista = $lista . $nom_arch . '</option>'; # 01.i
        $nro_elem = $nro_elem + 1;
      }
    }
  }


  $lista = $lista . q{</select>};
  return $lista;

};

# ---------------------------------------------------------------
sub dev_tam_img {
  my ($file) = $_[0];
  my ($ancho, $alto, $msg);

  if (! -e $file) {
    return ('Archivo no existe', 0, 0);
  }
  else {
    if ($file =~ /.*\.(jpg|jpe|jpeg)$/i) {
      ($msg, $ancho, $alto) = &ancho_alto_jpg($file);
      # print STDERR "FILE[$file] ancho[$ancho] alto[$alto] MSG[$msg]\n";
    }
    elsif ($file =~ /.*\.(gif)$/i) {
      ($msg, $ancho, $alto) = &ancho_alto_gif($file);
    }
    elsif ($file =~ /.*\.(png)$/i) {
      ($msg, $ancho, $alto) = &ancho_alto_png($file);
    }
    else {
      return ('Archivo no tiene extensión JPG/JPE/JPEG/PNG/GIF/BMP', 0, 0);
    };

    return ($msg, $ancho, $alto);
  };

  return ('Archivo no existe', 0, 0);
}; # dev_tam_img.
# ---------------------------------------------------------------
sub ancho_alto_png {
  # Adaptacion de http://www.la-grange.net/2000/05/04-png.html
  my($file) = $_[0];
  my($head) = "";

  (open my $png, "<$file") || return ("No se puede abrir archivo PNG!", 0, 0);
  binmode $png;

  my($a, $b, $c, $d, $e, $f, $g, $h)=0;

  if(defined($png)       &&
     read( $png, $head, 8 ) == 8   &&
     $head eq "\x89\x50\x4e\x47\x0d\x0a\x1a\x0a" &&
     read($png, $head, 4) == 4     &&
     read($png, $head, 4) == 4     &&
     $head eq "IHDR"        &&
     read($png, $head, 8) == 8       ){
    ($a,$b,$c,$d,$e,$f,$g,$h)=unpack("C"x8,$head);
    close $png;
    return ('', $a<<24|$b<<16|$c<<8|$d, $e<<24|$f<<16|$g<<8|$h);
  };
  close $png;
  return ('', 0,0);
};
# ---------------------------------------------------------------
sub ancho_alto_jpg {
  my ($file) = $_[0];
  my ($c1, $c2, $ch, $s, $junk, $a, $b, $c, $d, $length);
  (open my $jpeg, "<$file") || return ("No se puede abrir archivo JPEG!", 0, 0);
  binmode $jpeg;
  read($jpeg, $c1, 1);
  read($jpeg, $c2, 1);
  ((ord($c1) == 0xFF) && (ord($c2) == 0xD8)) || return ("Este archivo no es un JPEG!", 0, 0);

  my ($done) = 0;
  my ($dummy);

  # while (ord($ch) != 0xDA) { # ych
  while (ord($ch) != 0xDA) {
    # Find next marker (JPEG markers begin with 0xFF)
    while (ord($ch) != 0xFF) {
      # read(JPEG, $ch, 1); # ych
      return('error reading jpg', 0, 0 ) unless read($jpeg, $ch, 1);
    };
    # JPEG markers can be padded with unlimited 0xFF's
    while (ord($ch) == 0xFF) {
      # read(JPEG, $ch, 1); # ych
      return('error reading jpg', 0, 0 ) unless read($jpeg, $ch, 1);
    };
    # Now, $ch contains the value of the marker.
# # ych
#     if ( (ord($ch) >= 0xC0) && (ord($ch) <= 0xCF) ) {
#       read (JPEG, $s, 2); ($c1, $c2) = unpack("C"x2,$s);
#       $length = $c1<<8|$c2;
#       read(JPEG, $junk, 1);
#       read(JPEG, $s, 4);
#       ($a,$b,$c,$d)=unpack("C"x4,$s);
#       close(JPEG);
#       return ('', ($c<<8|$d), ($a<<8|$b));
    if( ( ord( $ch ) >= 0xC0 ) && ( ord( $ch ) <= 0xC3 ) ) {
      return('Error de formato en jpg', 0, 0 ) unless read( $jpeg, $dummy, 3 );
      return('Error de formato en jpg', 0, 0 ) unless read( $jpeg, $s, 4 );
      ( $a, $b, $c, $d ) = unpack( "C"x4, $s );
      return('', $c<<8|$d, $a<<8|$b );

    }
    else {
      # We **MUST** skip variables, since FF's within variable
      # names are NOT valid JPEG markers
      # read (JPEG, $s, 2); # ych
      return('error reading jpg', 0, 0 ) unless read ($jpeg, $s, 2);
      ($c1, $c2) = unpack("C"x2,$s);
      $length = $c1<<8|$c2;
      # if ($length < 2) { # ych
      if( !defined( $length ) || $length < 2 ) {
        close($jpeg);
        return ("Longitud del marcador JPEG errónea!", 0, 0);
      };

      read($jpeg, $dummy, $length-2);
    };
  };
}; # ancho_alto_jpg.
# ---------------------------------------------------------------
sub ancho_alto_gif {
  my ($file) = $_[0];
  my ($a,$b,$c,$d, $s, $type);
  (open my $gif, "<$file") || return ("No se puede abrir archivo GIF!", 0, 0);
  binmode $gif;
  read($gif, $type, 6);
  $type =~ /GIF8[7,9]a/ || return ("Archivo GIF inválido!", 0, 0);
  read($gif, $s, 4) == 4 || return ("Archivo GIF corrupto!", 0, 0);
  close($gif);
  ($a,$b,$c,$d)=unpack("C"x4,$s);
  return ('', ($b<<8|$a), ($d<<8|$c));
}; # ancho_alto_gif.
# ---------------------------------------------------------------
sub ancho_alto_bmp {
  my ($file) = $_[0];
  my ($a,$b,$c,$d,$e,$f,$g,$h, $s, $type);
  (open $bmp, "<$file") || return ("No se puede abrir archivo BMP!", 0, 0);
  binmode $bmp;
  read($bmp, $type, 2);
  $type =~ /BM/ || return ("Archivo BMP inválido!", 0, 0);
  read($bmp, $type, 12);
  read($bmp, $s, 4) == 4 || return ("Archivo BMP corrupto!", 0, 0);
  $a=unpack("C"x1,$s);
  if ($a-4 == 12) {
    read($bmp, $s, 4) == 4 || return ("Archivo BMP corrupto!", 0, 0);
    ($a,$b,$c,$d)=unpack("C"x4,$s);
    close($bmp);
    return ('', ($b<<8|$a), ($d<<8|$c));
  }
  elsif ($a-4 > 12) {
    read($bmp, $s, 8) == 8 || return ("Archivo BMP corrupto!", 0, 0);
    ($a,$b,$c,$d,$e,$f,$g,$h)=unpack("C"x8,$s);
    close($bmp);
    return ('', ($b<<8|$a|$d<<8|$c), ($f<<8|$e|$h<<8|$g));
  }
  else {
    close($bmp);
    return ("Archivo BMP inválido!", 0, 0);
  };
}; # ancho_alto_bmp.

# ---------------------------------------------------------------
sub get_edics4update {
# Obtiene un arreglo con las ediciones cuyas portadas es necesario actualizar por haberse modificado o eliminado
# articulos publicados en ellas.
# Estas ediciones corresponden a:
# - ed. base
# - ed. vigente
# - ultima edicion
# - la de hoy

  my (@ediciones);

  # Siempre procesa la ed. base.
  my $edic_base = $prontus_varglb::DIR_UNICAEDIC;
  $edic_base =~ s/^\///;
  push @ediciones, $edic_base;

  if ($prontus_varglb::MULTI_EDICION eq 'SI') {

    # Obtener ed. vigente.
    my $ed_vigente = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/ed_vigente.txt");
    if ($ed_vigente) {
      push @ediciones, $ed_vigente;
    };

    # Obtener ultima edicion
    my $ed_newer = &get_newer_edic();
    if (($ed_newer) && ($ed_newer ne $ed_vigente)) {
      push @ediciones, $ed_newer;
    };

    # Obtener la de hoy
    my $edic_hoy; # aaaammdd
    if ($prontus_varglb::FECHA_HOY =~ /^(\d{4})(\d{2})(\d{2})/) {
      $edic_hoy = $1 . '_' . $2 . '_' . $3 . '_1';
      if (-d "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EDIC/$edic_hoy") {
        push @ediciones, $edic_hoy if (($edic_hoy ne $ed_newer) && ($edic_hoy ne $ed_vigente));
      };
    };

  };

  return @ediciones;

};

# ---------------------------------------------------------------
sub actualizar_portadas_byartic {
# Re-genera todas las secciones de la edicion correspondiente,
# donde el articulo referido este presente.
# Se considera la ed. base, la ultima y la vigente.

  my ($ts) = $_[0]; # Nombre del articulo SIN extension y sin path, a dejar sin VoBo en las secciones donde aparezca.
  my ($accion) = $_[1]; # ALTA_CONTROL | BORRAR



  my ($pathdir_seccs, @entries, $entry, $arch_seccion, $text_seccion, $parametros, $path_tsec);

  # procesa edicion, vigente, la ultima y la base.
  my (@ediciones) = &get_edics4update();

  my $edic;
  foreach $edic (@ediciones) {
    # print STDERR "edic[$edic]\n";
    # Dir destino de las portadas de la ed.
    $pathdir_seccs = $prontus_varglb::DIR_SERVER .
                     $prontus_varglb::DIR_CONTENIDO .
                     $prontus_varglb::DIR_EDIC .
                     "/$edic" .
                     $prontus_varglb::DIR_SECC;


    @entries = &glib_fildir_02::lee_dir($pathdir_seccs);

    # Para cada seccion.
    foreach $entry (@entries) {
      $requiere_actualizar = 0;

      next if ($entry =~ /^\./);

      # portada en el site
      $arch_seccion = "$pathdir_seccs/$entry";

      my ($arch_xml) = $arch_seccion;
      $arch_xml =~ s/\/port\/(\w+?)\.\w*$/\/xml\/\1\.xml/;

      # template de la portada
      $path_tsec = $prontus_varglb::DIR_SERVER .
                    $prontus_varglb::DIR_TEMP .
                    $prontus_varglb::DIR_EDIC .
                    $prontus_varglb::DIR_NROEDIC .
                    $prontus_varglb::DIR_SECC . "/$entry";

      # print STDERR "arch_xml[$arch_xml]\n";

      next if ((! -f $arch_xml) || ($entry =~ /^preview/i));

      %lib_prontus::AREA = ();
      %lib_prontus::PRIO = ();
      %lib_prontus::DIR_FECHA = ();
      $prontus_varglb::XML_PORT_BASE =~ s/<PORT_DATA>.*<\/PORT_DATA>/<PORT_DATA>\n<\/PORT_DATA>/is;
      $text_seccion = &glib_fildir_02::read_file($arch_xml);
      $text_seccion = &ajusta_crlf($text_seccion);

      # Rescatar la info de c/artic de la seccion actual
      #~ CVI - 06/08/2012
      #~ Solo carga la info de portada si el articulo esta publicado en ella
      if ($text_seccion =~ /<rowartic>\s*<dir>\d+?<\/dir>\s*<file>$ts<\/file>.*?<\/rowartic>/is) {
        #~ while ($text_seccion =~ /(<rowartic>[ \n]*?<dir>(\d+?)<\/dir>[ \n]*?<file>(.*?)<\/file>[ \n]*?<area>(\d*?)<\/area>[ \n]*?<ord>(\d*?)<\/ord>[ \n]*?(<vb>(\w*?)<\/vb>)?[ \n]*?<?i?n?>?([\w\/\-]*?)<?\/?i?n?>?[ \n]*?<?o?u?t?>?([\w\/\-]*?)<?\/?o?u?t?>?[ \n]*?<?p?u?b?>?(\d?)<?\/?p?u?b?>?[ \n]*?<\/rowartic>/isg) {
        while ($text_seccion =~ /(<rowartic>\s*<dir>(\d+?)<\/dir>\s*<file>(.*?)<\/file>.*?<\/rowartic>)/isg) {
            my $rowartic = $1;
            my $dirfecha = $2;
            my $art = $3;

            #~ print STDERR "$entry -> $rowartic\n";
            my ($area,$prio,$pub,$vb) = '';

            $area = $1 if($rowartic =~ /<area>(\d*?)<\/area>/);
            $prio = $1 if($rowartic =~ /<ord>(\d*?)<\/ord>/);
            $pub = $1 if($rowartic =~ /<pub>(\d*?)<\/pub>/);
            $vb = $1 if($rowartic =~ /<vb>(\d*?)<\/vb>/);
            # print STDERR "ENTRA con[$dirfecha,$ts,$area,$prio,$vb,$in,$out]";

            $lib_prontus::AREA{$art} = $area;      # Asocia area al articulo.
            $lib_prontus::PRIO{$art} = $prio;      # Asocia prioridad correspondiente.
            $lib_prontus::VB{$art} = $vb;      # Asocia vobo del articulo en la portada.
            $lib_prontus::DIR_FECHA{$art} = $dirfecha;
        }
        if ($accion eq 'BORRAR') {
            # warn "borrar[$art]\n";
            delete $lib_prontus::AREA{$ts};
            delete $lib_prontus::PRIO{$ts};
            delete $lib_prontus::VB{$ts};
            delete $lib_prontus::DIR_FECHA{$ts};
        };
        # indico que hay que regenerar la portada
        $requiere_actualizar = 1;
      }; # while art. de esta portada

      # Re-Genera la portada si en ella esta el articulo en cuestion
      if ($requiere_actualizar) {

        my $mv = '';
        my $sin_regen_xml = 0;
        my $ts_preview = '';
        &lib_prontus::make_portada($arch_seccion, $path_tsec, $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
                                 $mv, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
                                 $edic, $sin_regen_xml, $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
                                 $ts_preview, $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $prontus_varglb::USERS_PERFIL);

        # Ahora proceso multivistas
        $sin_regen_xml = 1;
        foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
          &lib_prontus::make_portada($arch_seccion, $path_tsec, $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
                                   $mv, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
                                   $edic, $sin_regen_xml, $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
                                   $ts_preview, $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $prontus_varglb::USERS_PERFIL);

        };
      };

    }; # foreach portadas de la edicion

  }; # foreach

};

# ---------------------------------------------------------------
sub borra_taxport {
# Borra caches de portadas taxonomicas asociadas al art.
# para forzar que se vuelvan a generar.

  my ($secc, $tem, $stem, $vista) = @_;
  # elimina portadas taxonomicas
  if ($secc) {
    my $dir_taxport = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_PTEMA";
    if ($vista) { # nombre de la vista.
      $dir_taxport = $dir_taxport . '-' . $vista;
    };

    my $taxport = $dir_taxport . "/$secc" . '_' . $tem . '_' . $stem . '_';
    unlink glob($taxport . '*');
  };
};



# ---------------------------------------------------------------
# 20120723 - JOR - Los ultimos 3 parametros corresponden al nombre de la seccion, tema y subtema para construir la version 2.0 de las friendly url.
sub parse_filef {
  my ($buffer, $titular, $ts, $prontus_id, $relpath_artic, $nom_seccion1, $nom_tema1, $nom_subtema1) = @_;
  return $buffer if (!$ts || !$prontus_id || !$titular);
  my $ext;
  $ext = $1 if ($relpath_artic =~ /\.(\w+)$/);
  $titular = &saca_tags_rets($titular);
  $titular = &notildes($titular);
  $titular = lc $titular;
  $titular =~ s/[^a-z0-9]/-/sg;
  $titular =~ s/-+/-/g;
  $titular =~ s/^-//sg;
  $titular =~ s/-$//sg;
  my $fecha4friendly;
  my $fecha;
  my $hora;
  if ($ts =~ /^(\d{4})(\d{2})(\d{2})(\d{6})/) {
    $fecha4friendly = $1 . '-' . $2 . '-' . $3;
    $fecha = "$1$2$3";
    $hora = $4;
  };

  if ($prontus_varglb::FRIENDLY_URLS eq 'SI') {
    my $fileurl = '';
    if ($prontus_varglb::FRIENDLY_URLS_VERSION eq '1') {
        $fileurl = "/$titular/$prontus_id/$fecha4friendly/$hora.$ext";
    } elsif ($prontus_varglb::FRIENDLY_URLS_VERSION eq '2') {
        # Formato: /prontus/seccion/tema/subtema/titular/aaaa-mm-dd/hhnnss.extension
        $fileurl = "/$prontus_id/";

        if ($nom_seccion1 ne '') {
            $nom_seccion1 = &despulgar_texto_friendly($nom_seccion1);
            $fileurl .= "$nom_seccion1/";
        };

        if ($nom_tema1 ne '') {
            $nom_tema1 = &despulgar_texto_friendly($nom_tema1);
            $fileurl .= "$nom_tema1/";
        };

        if ($nom_subtema1 ne '') {
            $nom_subtema1 = &despulgar_texto_friendly($nom_subtema1);
            $fileurl .= "$nom_subtema1/";
        };

        $fileurl .= "$titular/$fecha4friendly/$hora.$ext";
    } else {
        # Deja por defecto la versión 1, en caso de que no exista la variable o esté vacia.
        $fileurl = "/$titular/$prontus_id/$fecha4friendly/$hora.$ext";
    };

    #~ print STDERR "fileurl[$fileurl]\n";

      $buffer =~ s/%%_FILEURL%%/$fileurl/isg; # Links friendly

  } else {
      my $file = "/$prontus_id/site/artic/$fecha/pags/$ts.$ext";
      $buffer =~ s/%%_FILEURL%%/$file/isg; # Links normal, no friendly
  };

  return $buffer;
};

# ---------------------------------------------------------------
sub despulgar_texto_friendly {
    my $texto = $_[0];
    $texto = &saca_tags_rets($texto);
    $texto = &notildes($texto);
    $texto = lc $texto;
    $texto =~ s/[^a-z0-9]/-/sg;
    $texto =~ s/-+/-/g;
    $texto =~ s/^-//sg;
    $texto =~ s/-$//sg;

    return $texto;
};

# ---------------------------------------------------------------
sub ajusta_pathconf {
# Ajusta path_conf agregandole el dir_server en caso de q no lo tenga y corrigiendo
# backslashes
  my ($path_conf) = $_[0];
  my ($dir_server) = $prontus_varglb::DIR_SERVER;
  $dir_server =~ s/\\/\//g; # cambia \ por /
  $path_conf =~ s/\\/\//g; # cambia \ por /
  if ($path_conf !~ /.*$dir_server.*/) {
    $path_conf = $dir_server . $path_conf;
  };
  return $path_conf;
};
#------------------------------------------------------------------------------#
sub bytes2kb {
  my $bytes = $_[0];
  $bytes = $bytes / 1024;
  $bytes = 1 if ($bytes < 1);
  $bytes = &format_miles_dec($bytes, 0);
  $bytes .= ' KB';
  return $bytes;
};

#------------------------------------------------------------------------------#
sub format_miles_dec {
  # Recibe numero real y lo formatea con separadores de miles y cant. de decimales deseada.
  my ($valor1, $valor2, $dec) = ($_[0], $_[0], $_[1]);
  my ($signo);

  # print "valor1 s/f:[$valor1]"; # debug

  $signo = '';
  if ($valor1 < 0) {
    $signo = '-';
  };

  $valor1 = $valor2 = abs $valor1;
  # Si el valor hay que devolverlo como entero sin decimales.
  # $valor1 += 1 if ($valor2 - int($valor2) and $dec == 0) >= 0.5;  # 03.2

  # 03.2
  if ($dec == 0) {
    if ($valor1 =~ /\.(\d)/) {
      my $d = $1;
      $valor1 += 1 if ($d >= 5);
    };
  };

  # Si el valor hay que devolverlo como entero con decimales.
  $valor1 += '0.' . '0' x ($dec - 1) . (1 - ($valor2 - int($valor2))) if ($valor2 - int($valor2) and $dec > 0) >= 0.5;
  $valor2 = sprintf("%.${dec}f", $valor2);
  $valor2 =~ s/^\d+\.//g;

  $valor1 =~ s/\..*//g;

  $valor1 = &glib_str_02::format_miles($valor1);  # 03.2

  if ($dec > 0) {
    $valor1 .= ',' . $valor2;
  };

  if ($signo eq '-') {
    $valor1 = '-' . $valor1;
  };

  # print "valor1 c/f:[$valor1]<br>"; # debug
  return $valor1;
};

# ---------------------------------------------------------------
sub get_dtime_rfc822 {
  # aaaammddhhmmss  -> Mon, 24 Apr 2006 16:52:32 GMT
  my ($aaaammddhhmmss) = shift;
  return '' if ($aaaammddhhmmss =~ /^9999/);
  if ($aaaammddhhmmss =~ /^(\d{8})(\d{2})(\d{2})(\d{2})/) {
    my ($aaaammdd, $hh, $mm, $ss) = ($1, $2, $3, $4);
    my $dtime_rfc822 = &fecha2rfc822($aaaammdd, $hh, $mm, $ss);
    return $dtime_rfc822;
  }
  else {
    return '';
  };

};

# ---------------------------------------------------------------
sub get_hora_iso {
# Obtiene hhmmss a partir de hh:mm
    my $horap = shift;
    my $horap_iso;
    if ($horap =~ /^(\d\d):(\d\d)$/) {
      $horap_iso = $1 . $2 . '00';
    }
    else {
      $horap_iso = '0' x 6;
    };
    return $horap_iso;
};
# ---------------------------------------------------------------
 sub fecha2rfc822 {
   use Time::Local qw(timelocal_nocheck timegm_nocheck);
   # Toma una fecha en iso y la pone como "Mon, 24 Apr 2006 16:52:32 GMT"
   # Param : string con la fecha ISO.

   my($fecha, $hh, $mm, $ss) = @_;

   my(@dias) = ('Sun','Mon','Tue','Wed','Thu','Fri','Sat');
   my(@meses) = ('Jan','Feb','Mar','Apr','May','Jun','Jul',
                    'Aug','Sep','Oct','Nov','Dec');
   $fecha =~ /(\d\d\d\d)(\d\d)(\d\d)/;
   my($dia,$mes,$ano) = ($3,$2,$1);
   my ($tiempo, $tiempo2);

   $tiempo = &Time::Local::timelocal_nocheck($ss,$mm,$hh,$dia,($mes - 1),($ano - 1900)) || return '';
   $tiempo2 = &Time::Local::timegm_nocheck($ss,$mm,$hh,$dia,($mes - 1),($ano - 1900)) || return '';

   $tiempo = $tiempo + ($tiempo - $tiempo2);

   my($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($tiempo);
   # $dia = $dia + 0; # Para extraer los ceros de adelante.
   $year = $year + 1900;

   $sec = &glib_str_02::format_n($sec,2);
   $min = &glib_str_02::format_n($min,2);
   $hour = &glib_str_02::format_n($hour,2);

   return $dias[$wday] . ", $mday " . $meses[$mon] . " $year $hour:$min:$sec GMT";
 };

# -------------------------------------------------------------------------#
sub mini_unescape_html {
# Detecta y pone en ISO los caracteres escapeados en html, pero solo para las letras con tildes.
    my($toencode) = $_[0];

    $toencode=~s/&Agrave;/\xC0/g;
    $toencode=~s/&Aacute;/\xC1/g;
    $toencode=~s/&Acirc;/\xC2/g;
    $toencode=~s/&Atilde;/\xC3/g;
    $toencode=~s/&Auml;/\xC4/g;
    $toencode=~s/&Aring;/\xC5/g;
    $toencode=~s/&AElig;/\xC6/g;
    $toencode=~s/&Ccedil;/\xC7/g;
    $toencode=~s/&Egrave;/\xC8/g;
    $toencode=~s/&Eacute;/\xC9/g;
    $toencode=~s/&Ecirc;/\xCA/g;
    $toencode=~s/&Euml;/\xCB/g;
    $toencode=~s/&Igrave;/\xCC/g;
    $toencode=~s/&Iacute;/\xCD/g;
    $toencode=~s/&Icirc;/\xCE/g;
    $toencode=~s/&Iuml;/\xCF/g;
    $toencode=~s/&Ntilde;/\xD1/g;
    $toencode=~s/&Ograve;/\xD2/g;
    $toencode=~s/&Oacute;/\xD3/g;
    $toencode=~s/&Ocirc;/\xD4/g;
    $toencode=~s/&Otilde;/\xD5/g;
    $toencode=~s/&Ouml;/\xD6/g;

    $toencode=~s/&Oslash;/\xD8/g;
    $toencode=~s/&Ugrave;/\xD9/g;
    $toencode=~s/&Uacute;/\xDA/g;
    $toencode=~s/&Ucirc;/\xDB/g;
    $toencode=~s/&Uuml;/\xDC/g;
    $toencode=~s/&Yacute;/\xDD/g;
    $toencode=~s/&szlig;/\xDF/g;
    $toencode=~s/&agrave;/\xE0/g;
    $toencode=~s/&aacute;/\xE1/g;
    $toencode=~s/&acirc;/\xE2/g;
    $toencode=~s/&atilde;/\xE3/g;
    $toencode=~s/&auml;/\xE4/g;
    $toencode=~s/&aring;/\xE5/g;
    $toencode=~s/&aelig;/\xE6/g;
    $toencode=~s/&ccedil;/\xE7/g;
    $toencode=~s/&egrave;/\xE8/g;
    $toencode=~s/&eacute;/\xE9/g;
    $toencode=~s/&ecirc;/\xEA/g;
    $toencode=~s/&euml;/\xEB/g;
    $toencode=~s/&igrave;/\xEC/g;
    $toencode=~s/&iacute;/\xED/g;
    $toencode=~s/&icirc;/\xEE/g;
    $toencode=~s/&iuml;/\xEF/g;
    $toencode=~s/&eth;/\xF0/g;
    $toencode=~s/&ntilde;/\xF1/g;
    $toencode=~s/&ograve;/\xF2/g;
    $toencode=~s/&oacute;/\xF3/g;
    $toencode=~s/&ocirc;/\xF4/g;
    $toencode=~s/&otilde/\xF5;/g;
    $toencode=~s/&ouml;/\xF6/g;
    $toencode=~s/&oslash;/\xF8/g;
    $toencode=~s/&ugrave/\xF9;/g;
    $toencode=~s/&uacute;/\xFA/g;
    $toencode=~s/&ucirc;/\xFB/g;
    $toencode=~s/&uuml;/\xFC/g;
    $toencode=~s/&brvbar;/\xFD/g;
    $toencode=~s/&yuml;/\xFF/g;

    return $toencode;
};

# ---------------------------------------------------------------
sub generar_popup_multivistas {
# Generar combo de multivistas, obteniendo la informacion desde
# el hash global definido en el arch. de configuracion.
# Retorna : Lista de seleccion con datos, lista para imprimirla.

  my($name_obj) = '_CMB_MV';
  my($valor_clave) = '';
  my($items_visibles) = '1';
  my($ind_multiple) = '';
  my($javascript) =  '';
  my($lista) = '';

  my($val_display, $key, $clave);
  my($key2); # 1.11

  # Generar la lista de seleccion en html
  $lista = q{<select name="} . $name_obj . q{" SIZE="} . $items_visibles . q{" } . $ind_multiple . ' ' . $javascript . q{>};

  # 8.0
  $lista = $lista . "\n<option value=\"$key\">-Default-</option>";
  foreach $key (sort {$a cmp $b} keys %prontus_varglb::MULTIVISTAS) {
    $lista = $lista . "\n<option value=\"$key\">$key</option>";
  };

  $lista = $lista . "\n</select>";

  return $lista;

};

# ---------------------------------------------------------------
sub make_mapa {

# genera mapa del sitio en base a taxonomia
  my ($mv) = $_[0]; # nombre de la vista
  my ($bd) = $_[1];
  my $dir_plt = 'pags'; # rotulos tax
  $dir_plt .= "-$mv" if ($mv); # rotulos tax


  my $ruta_dir = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_TEMP/extra/mapa/$dir_plt";
  my (@lisdir) = &glib_fildir_02::lee_dir($ruta_dir) if (-d $ruta_dir);
  @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
  foreach my $k (@lisdir) {
    next if (! -f "$ruta_dir/$k");

    my $mapa_plt = &glib_fildir_02::read_file("$ruta_dir/$k");
    $mapa_plt = &ajusta_crlf($mapa_plt);
    my ($loop_mapa_s, $loop_mapa_t, $loop_mapa_st);
    if ($mapa_plt =~ /%%(LOOP_SECCION)%%(.*?)%%\/\1%%/s) {
      $loop_mapa_s = $2;
    };
    if ($mapa_plt =~ /%%(LOOP_TEMA)%%(.*?)%%\/\1%%/s) {
      $loop_mapa_t = $2;
    };
    if ($mapa_plt =~ /%%(LOOP_SUBTEMA)%%(.*?)%%\/\1%%/s) {
      $loop_mapa_st = $2;
    };
    my $base_indent = '15';
    my ($mapa) = &get_arbol_mapa($loop_mapa_s, $loop_mapa_t, $loop_mapa_st, $mv, $base_indent, $bd);
    $mapa_plt =~ s/%%(LOOP_SECCION)%%.*?%%\/\1%%/$mapa/is;
    $mapa_plt =~ s/%%(LOOP_TEMA)%%.*?%%\/\1%%//is;
    $mapa_plt =~ s/%%(LOOP_SUBTEMA)%%.*?%%\/\1%%//is;
    $mapa_plt = &parser_custom_function($mapa_plt);
    &glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/extra/mapa/$dir_plt");
    my $dst_mapa = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/extra/mapa/$dir_plt/$k";
    &glib_fildir_02::write_file($dst_mapa, $mapa_plt);
    &lib_prontus::purge_cache($dst_mapa);

  };

};
# ---------------------------------------------------------------
sub get_arbol_mapa {
  my ($loop_mapa_s) = $_[0];
  my ($loop_mapa_t) = $_[1];
  my ($loop_mapa_st) = $_[2];
  my ($mv) = $_[3];
  my ($indent) = $_[4];
  my ($bd) = $_[5];

  my $local_indent;
  my $mapa;
  # print STDERR "loop_mapa[$loop_mapa]\n";
  # secc
  my $sql = "select SECC_ID, SECC_NOM, SECC_PORT, SECC_NOM4VISTAS from SECC where SECC_ORDEN > 0 order by SECC_ORDEN";
  my ($secc_id, $secc_nom, $secc_port, $secc_nom4vistas);
  my ($salida) = &glib_dbi_02::ejecutar_sql($bd, $sql);
  $salida->bind_columns(undef, \($secc_id, $secc_nom, $secc_port, $secc_nom4vistas));
  while ($salida->fetch) {
    # Cambia nom para la vista.
    $secc_nom = &lib_prontus::get_nomtax_envista($mv, $secc_nom4vistas) if ($mv); # rotulos tax

    $secc_nom = &lib_prontus::escape_html($secc_nom);
    $secc_port = &lib_prontus::escape_html($secc_port);

    $local_indent = $indent;
    $local_indent -= $indent;

    $mapa .= $loop_mapa_s;
    $mapa =~ s/%%_id%%/$secc_id/ig;
    $mapa =~ s/%%_nom%%/$secc_nom/ig;
    $mapa =~ s/%%_indent%%/$local_indent/ig;
    my $tax_fixedurl = &lib_prontus::get_tax_link($secc_port, $mv);
    $mapa =~ s/%%_FIXED_URL%%/$tax_fixedurl/isg;
    $mapa =~ s/%%_SECCION[1-3]%%/$secc_id/isg;
    $mapa =~ s/%%_TEMA[1-3]%%//isg;
    $mapa =~ s/%%_SUBTEMA[1-3]%%//isg;


    # temas
    $sql = "select TEMAS_ID, TEMAS_NOM, TEMAS_PORT, TEMAS_NOM4VISTAS from TEMAS where TEMAS_ORDEN > 0 AND TEMAS_IDSECC = '$secc_id' order by TEMAS_ORDEN";
    my ($temas_id, $temas_nom, $temas_port, $temas_nom4vistas);
    my ($salida_t) = &glib_dbi_02::ejecutar_sql($bd, $sql);
    $salida_t->bind_columns(undef, \($temas_id, $temas_nom, $temas_port, $temas_nom4vistas));
    while ($salida_t->fetch) {
      $temas_nom = &lib_prontus::get_nomtax_envista($mv, $temas_nom4vistas) if ($mv); # rotulos tax
      $temas_nom = &lib_prontus::escape_html($temas_nom);

      $local_indent = $indent * 2;
      $local_indent -= $indent;

      $mapa .= $loop_mapa_t;
      $mapa =~ s/%%_id%%/$temas_id/ig;
      $mapa =~ s/%%_nom%%/$temas_nom/ig;
      $mapa =~ s/%%_indent%%/$local_indent/ig;


      $tax_fixedurl = &lib_prontus::get_tax_link($temas_port, $mv);
      $mapa =~ s/%%_FIXED_URL%%/$tax_fixedurl/isg;
      $mapa =~ s/%%_SECCION[1-3]%%/$secc_id/isg;
      $mapa =~ s/%%_TEMA[1-3]%%/$temas_id/isg;
      $mapa =~ s/%%_SUBTEMA[1-3]%%//isg;


      # subtemas
      $sql = "select SUBTEMAS_ID, SUBTEMAS_NOM, SUBTEMAS_PORT, SUBTEMAS_NOM4VISTAS from SUBTEMAS where SUBTEMAS_ORDEN > 0 AND SUBTEMAS_IDTEMAS = '$temas_id' order by SUBTEMAS_ORDEN";
      my ($subtemas_id, $subtemas_nom, $subtemas_port, $subtemas_nom4vistas);
      my ($salida_st) = &glib_dbi_02::ejecutar_sql($bd, $sql);
      $salida_st->bind_columns(undef, \($subtemas_id, $subtemas_nom, $subtemas_port, $subtemas_nom4vistas));
      while ($salida_st->fetch) {
        $subtemas_nom = &lib_prontus::get_nomtax_envista($mv, $subtemas_nom4vistas) if ($mv); # rotulos tax
        $subtemas_nom = &lib_prontus::escape_html($subtemas_nom);
        $local_indent = $indent * 3;
        $local_indent -= $indent;

        $mapa .= $loop_mapa_st;
        $mapa =~ s/%%_id%%/$subtemas_id/ig;
        $mapa =~ s/%%_nom%%/$subtemas_nom/ig;
        $mapa =~ s/%%_indent%%/$local_indent/ig;

        $tax_fixedurl = &lib_prontus::get_tax_link($subtemas_port, $mv);
        $mapa =~ s/%%_FIXED_URL%%/$tax_fixedurl/isg;
        $mapa =~ s/%%_SECCION[1-3]%%/$secc_id/isg;
        $mapa =~ s/%%_TEMA[1-3]%%/$temas_id/isg;
        $mapa =~ s/%%_SUBTEMA[1-3]%%/$subtemas_id/isg;

      };
      $salida_st->finish;

    };
    $salida_t->finish;

  };
  $salida->finish;
  return $mapa;
};

# ---------------------------------------------------------------
sub get_tax_link {
# entrega link a portada prontus o url para un nivel taxonomico.
  my ($nom) = $_[0];
  my ($mv) = $_[1]; # nombre de la vista

  if ($nom){
    if ($nom =~ /^(https?:\/\/|\/)/i) { # url
      return $nom;
    }
    else { # nombre de una port => linkear a port de la edic. vigente o bien de la base.
      my $edic;
      if ($prontus_varglb::MULTI_EDICION eq 'SI') {
        $edic = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/ed_vigente.txt");
      }
      else {
        $edic = 'base';
      };
      my $dir_port = $prontus_varglb::DIR_SECC;
      if ($mv) { # nombre de la vista.
        $dir_port = $dir_port . '-' . $mv;
      };
      return $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_EDIC . "/$edic" . $dir_port . "/$nom";
    };
  }
  else {
    return '';
  };

};
# --------------------------------------------------------------------
sub parser_custom_function {
  # parsea invocacion a funciones definidas en lib_custom.pm
  my $buffer = $_[0];
  my $path_include = $_[1];
  #~ unshift @INC, $path_include if ($path_include); # comentado por JOR - 09/10/2012
  eval "require lib_custom;";
  if ($@) {
    # Avisa del error solo en caso de que las p functions se esten utilizando.
    if ($buffer =~ /%%_PF_\w+\(.*?\)%%/is) {
        print STDERR "Error cargando lib_custom.pm : $@\n";
        $buffer =~ s/%%_PF_\w+\(.*?\)%%//isg;
    };
  }
  else {
    while ($buffer =~ /%%_PF_(\w+\(.*?\))%%/isg) {
      my $function = $1;
      my $newfunction = $function;

      # CVI - Para escapear los parametros de entrada
      if($newfunction =~ /^\w+\((.*?)\)$/s) {
        my $params = $1;
        $params =~ s/^\s*["|']//;
        $params =~ s/["|']\s*$//;
        # print STDERR "PARAMS: $params\n";

        # CVI - Se corrige regexp
        # my @arrparams = split(/(["|'])\s*,\s*\1/, $params);
        my @arrparams = split(/"\s*,\s*"|'\s*,\s*'/, $params);
        my @newarr;
        foreach my $keys (@arrparams) {
          # $keys =~ s/(["|'])([^\\])"/\1\\"/g;
          $keys =~ s/([^\\])"/\1\\"/g;
          # print STDERR "keys: $keys... ";
          push(@newarr, $keys);
        }
        $params = join('","', @newarr);
        $params = '"' . $params . '"';
        # print STDERR "\nPARAMS: $params\n\n";
        $newfunction =~ s/^(\w+)\((.*?)\)$/\1($params)/s;
      };

      my $result;
      my $sentencia = '$result = &lib_custom::' . $newfunction;
      $sentencia .= ';' if ($sentencia !~ /;$/);
      eval($sentencia);
      if ($@) {
        print STDERR 'Error ejecutando &lib_custom::' . $newfunction . " : $@\n";
      };

      if (!($buffer =~ s/%%_PF_\Q$function\E%%/$result/is)) {
        print STDERR "reemp[%%_PF_$function%%] x result[$result]\n";
        print STDERR "reemp[fail]\n";
      };
    };
  };
  return $buffer;
};
# --------------------------------------------------------------------
sub insert_dev_id {
# Inserta registro y devuelve nuevo ID.

# Parametros :
# 0) base de datos abierta
# 1) sentencia insert
# 1) MOTOR bd : PRONTUS/SQLITE/MYSQL

# Retorna : Nuevo ID.


  my ($sql) = $_[0];
  my ($basedatos) = $_[1];
  my ($motor_bd) = $_[2];
  my ($res, $idvalue);

  # print STDERR "sql[$sql]\n";
  # print STDERR "basedatos[$basedatos]\n";
  # print STDERR "motor_bd[$motor_bd]\n";

  $basedatos->do($sql) || return 0;

  if ($motor_bd eq 'MYSQL') {
    $sql = 'select last_insert_id()'; # mysql
  };

  # SQLITE
  if (($motor_bd eq 'PRONTUS') || ($motor_bd eq 'SQLITE')) {
    $sql = 'select last_insert_rowid()'; # sqlite
  };

  $res = &glib_dbi_02::ejecutar_sql($basedatos, $sql);

  $res->bind_columns(undef, \($idvalue));
  $res->fetch;
  $res->finish;

  return $idvalue;
};
# ---------------------------------------------------------------
sub despulga_item_tax { # rotulos tax
  my $str = $_[0];
  $str =~ s/["']//g;
  $str =~ s/[\t\r\n\,\|\>\<]/ /sg; # la [,|<>] se estripean por req. de la gestion de tags en el FID
  $str =~ s/\\/ /sg;
  $str =~ s/ +/ /g;
  $str =~ s/^ +//g;
  $str =~ s/ +$//g;
  return $str;
};

# ---------------------------------------------------------------
sub get_nomtax_envista {
  my ($mv) = shift;
  my ($nom4vistas) = shift;

    my $nom;
    if ($nom4vistas =~ /(^|\n)$mv\t(.*?)($|\n)/s) {
        $nom = $2;
    };
    return $nom; # necesita ser escapeada html en destino antes de usar.

#  my $path_xml_vista = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/tax_multivista/$mv/$tipo.xml";
#  my $xml = &glib_fildir_02::read_file($path_xml_vista);
#  my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d| |\s/;
#  my $nom;
#  $nom = $1 if ($xml =~ /<ITEM>$crlf*?<ID>$id<\/ID>$crlf*?<NOM>(.*?)<\/NOM>$crlf*?<\/ITEM>/is);
#  return $nom;

};

# ---------------------------------------------------------------
sub get_nom4vistas {
    my ($mv, $id_s, $id_t, $id_st) = @_;

    my $key = $id_s.'/'.$id_t.'/'.$id_st.'/'.$mv;
    if($prontus_varglb::cache_nom4vista{$key}) {
        return $prontus_varglb::cache_nom4vista{$key};
    }

    # Conectar a BD si es que no viene la conexion
    if (! ref($prontus_varglb::BD_CONN)) {
        # print STDERR "connect a BD dentro\n";
        my $msg_err_bd;
        ($prontus_varglb::BD_CONN, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
        if (! ref($prontus_varglb::BD_CONN)) {
            die "ERROR: $msg_err_bd\n";
        };
    };

    my ($nom_s, $nom_t, $nom_st); # nombres en la vista dada

    if (!$mv) {
        # Vista principal.
        if ($id_s) {
            $nom_s = &existe_registro("select SECC_NOM from SECC where SECC_ID='$id_s'", $prontus_varglb::BD_CONN);
        };

        if ($id_t) {
            $nom_t = &existe_registro("select TEMAS_NOM from TEMAS where TEMAS_ID='$id_t'", $prontus_varglb::BD_CONN);
        };

        if ($id_st) {
            $nom_st = &existe_registro("select SUBTEMAS_NOM from SUBTEMAS where SUBTEMAS_ID='$id_st'", $prontus_varglb::BD_CONN);
        };

        return ($nom_s, $nom_t, $nom_st);
    };

    if ($id_s) {
        my $secc_nom4vistas = &existe_registro("select SECC_NOM4VISTAS from SECC where SECC_ID='$id_s'", $prontus_varglb::BD_CONN);
        if ($secc_nom4vistas) {
            $nom_s = &lib_prontus::get_nomtax_envista($mv, $secc_nom4vistas);
        };
    };

    if ($id_t) {
        my $temas_nom4vistas = &existe_registro("select TEMAS_NOM4VISTAS from TEMAS where TEMAS_ID='$id_t'", $prontus_varglb::BD_CONN);
        if ($temas_nom4vistas) {
            $nom_t = &lib_prontus::get_nomtax_envista($mv, $temas_nom4vistas);
        };
    };

    if ($id_st) {
        my $subtemas_nom4vistas = &existe_registro("select SUBTEMAS_NOM4VISTAS from SUBTEMAS where SUBTEMAS_ID='$id_st'", $prontus_varglb::BD_CONN);
        if ($subtemas_nom4vistas) {
            $nom_st = &lib_prontus::get_nomtax_envista($mv, $subtemas_nom4vistas);
        };
    };

    $prontus_varglb::cache_nom4vista{$key} = ($nom_s, $nom_t, $nom_st);
    return ($nom_s, $nom_t, $nom_st);
};

# ---------------------------------------------------------------
sub escape_xml { # rotulos tax
  my $toencode = $_[0];
  $toencode=~s/&/&amp;/g;             # Antes que nada, traduce los ampersands. # 1.19 correccion a e.r.
  $toencode=~s/>/&gt;/g;              # >
  $toencode=~s/</&lt;/g;              # <
  $toencode=~s/"/&quot;/g;            # " # 8.0
  $toencode=~s/'/&#39;/g;
  return $toencode;
};
# ---------------------------------------------------------------
sub unescape_xml { # rotulos tax
  my $toencode = $_[0];
  $toencode=~s/&gt;/>/g;              # >
  $toencode=~s/&lt;/</g;              # <
  $toencode=~s/&quot;/"/g;            # " # 8.0
  $toencode=~s/&#39;/'/g;
  $toencode=~s/&apos;/'/g;
  $toencode=~s/&amp;/&/g;
  return $toencode;
};
# ---------------------------------------------------------------
sub valid_xml { # rotulos tax
# Valida xml bien formado.

  my ($buffer) = $_[0];
  my $p = new XML::Parser();
  eval { $p->parse($buffer) };
  if ($@) {
    $@ =~ s/ at \/.*$//;
    $@ =~ s/^(\n|\r)*//;
    return $@;
  };
  return ''; # xml esta ok

};
# ---------------------------------------------------------------
sub valid_xml_import {
# Valida xml bien formado para la importacion

  my ($buffer) = $_[0];
  $buffer =~ s/&/&amp;/isg;
  my $p = new XML::Parser();
  eval { $p->parse($buffer) };
  if ($@) {
    $@ =~ s/ at \/.*$//;
    $@ =~ s/^(\n|\r)*//;
    return $@;
  };
  return ''; # xml esta ok

};

#------------------------------------------------------------------------#
sub call_system_and_location {
  my ($dir_server, $nom_script_detachado, $location, $params) = @_;
  # ruta_script:
  #   En unix queda algo asi como /sites/misitio.cl/web/cgi-cpn/
  #   En win queda algo asi como c:\sites\misitio.cl\web\cgi-cpn\
  my $ruta_script;
  if ($dir_server =~ /^\//) {
    $ruta_script = $ENV{'SCRIPT_FILENAME'}; # unix
  }
  else {
    $ruta_script = $dir_server . $ENV{'SCRIPT_NAME'}; # win, ej: SCRIPT_NAME = /cgi-cpn/env.cgi
    $ruta_script =~ s/\//\\/g; # si es win, cambio / por \
  };
  $ruta_script =~ s/\w+\.\w+$//;
  print STDERR "DETECTANDO...\n";
  # SI WIN--> generar link para q el user ejecute manualmente la cgi
  if ($dir_server =~ /^\w:/) {
    print STDERR "win!\n";
    my $script = "$nom_script_detachado.cgi";
    my @parametros = split(/ /, $params);
    my $path_conf = $parametros[1];
    $path_conf =~ s/"//g;
    $path_conf =~ s/^$dir_server//;
    $script .= "?path_conf=$path_conf";
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Ejecutar Proceso","Para completar la ejecución del proceso requerido, haga click <a href=\"$script\">aquí</a>.");
  }
  # SI UNIX
  else {
    print STDERR "unix!\n";
    my $script = $ruta_script . "$nom_script_detachado.cgi "; # EN UNIX ES .cgi
    my $cmd = "$script $params &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
    print "Location: $location\n\n";
  };

};
# ---------------------------------------------------------------
sub asigna_fecha_default {
# Asigna valores por defecto a la fechap y fechae cuando estos vienen vacios desde el fid.
# Para fechap vacio:
#    Si hay control fecha => poner 99999999
#    Si no hay control fecha => poner fecha de hoy en iso
# Para fechae vacio:
#    Siempre poner 99999999 (independiente del ctrl fecha)

  my ($nom_campo) = lc $_[0];
  my ($fecha_default);

  if ($nom_campo eq '_fechap') {
    if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
      $fecha_default = '9' x 8;
    }
    else {
      $fecha_default = &glib_hrfec_02::get_date_pack4();
    };
  };

  if ($nom_campo eq '_fechae') {
    $fecha_default = '9' x 8;
  };
  return $fecha_default;
};

# ---------------------------------------------------------------
sub artic_parser_fechas {
    my ($buffer, $fechap, $fechae) = @_;

    my %fechas;
    $fechas{'_FECHAP'} = $fechap;
    $fechas{'_FECHAE'} = $fechae;
    my ($iso_fechap, $iso_fechae);

    foreach my $nom_campo (keys %fechas) {
        my $val_campo = $fechas{$nom_campo};
        $val_campo = &lib_prontus::asigna_fecha_default($nom_campo) if ($val_campo eq '');

        # Replace en artic
        $buffer = &lib_prontus::replace_in_artic($val_campo, $nom_campo, $buffer);

        # Realizar sustituciones especiales.
        $buffer = &lib_prontus::parser_fechap($buffer, $val_campo, $nom_campo);

        # Parsear _NOM_EDIC en base a la fechap
        if (uc $nom_campo eq '_FECHAP') {
            if ($val_campo =~ /^(\d\d\d\d)(\d\d)(\d\d)/) {
                my $nomedic_mula = $1 . '_' . $2 . '_' . $3 . '_1';
                $buffer = &lib_prontus::replace_in_artic($nomedic_mula, '_NOM_EDIC', $buffer);
            };
        };

    }; # foreach fechas

    return $buffer;

};



# --------------------------------------------------------------------#
sub escapea_bd {
  # Escapea asumiendo que los valores de los campos estan encerrados entre comillas dobles, no simples.
  # Se prefiere esto en vez de quote(), ya que este ultimo encierra entre comillas simples y las simples
  # las tranasforma en tildes
  my $refhash_campos = $_[0]; # hash con nombres de campos y sus valores
  my $base = $_[1];
  my %campos = %$refhash_campos;

  foreach my $k (keys %campos) {

    if ($campos{$k} ne '') {
        $campos{$k} = $base->quote($campos{$k});
    } else {
        $campos{$k} = "''";
    };
    # print STDERR "CAMPO[$k] value[$campos{$k}]\n";

#    $campos{$k} =~ s/"/\\"/sg;
#    $campos{$k} =~ s/'/\\'/sg;
#    $campos{$k} =~ s/%\w+%//g;   # remueve marcas de formateo especiales.
#    if (&get_motor_from_bdhandler($base) eq 'PRONTUS') {
#        $campos{$k} =~ s/\?/\&#63;/sg;
#    };
  };
  return %campos;
};
# ---------------------------------------------------------------
sub existe_registro {
# Revisa si el reg. ya existe en la BD.
my ($sql) = $_[0];
my ($basedat) = $_[1];
my ($salida, $campo);

  $salida = &glib_dbi_02::ejecutar_sql($basedat, $sql);
  $salida->bind_columns(undef, \($campo));
  $salida->fetch;
  if ($campo ne '') {
    return $campo;
  }
  else {
    return 0;
  };
};
#---------------------------------------------------------------------
sub is_win32 {
  my $pesoscero = $0;
  return 1 if ($pesoscero =~ /^\w:/);
  return 0;
};

# --------------------------------------------------------------------
sub get_rowartics {
# Lee el xml de una portada prontus y retorna su contenido en un hash
# indexado por el articulo (<ts>.<ext>)
# Los rowartics son de la forma:
#   <rowartic>
#    <dir>20070125</dir>
#    <file>20070125195234</file>
#    <area>2</area>
#    <ord>2</ord>
#    <pub>0</pub>
#  </rowartic>

  my $full_path_xmlport = $_[0];
  my $buffer_port_xml = &glib_fildir_02::read_file($full_path_xmlport);
  my %rowartics;
  while ($buffer_port_xml =~ /<rowartic>(.*?)<\/rowartic>/sg) {
    my $rowartic = $1;
    if ($rowartic =~ /<file>(\d{14})<\/file>/) {
      my $artic_file = $1;
      while ($rowartic =~ /<(\w+?)>(.*?)<\/\1>/sg) {
        my $nom_campo = $1;
        my $valor_campo = $2;
        $rowartics{$artic_file}{$nom_campo} = $valor_campo;
      };
    };
  };
  return %rowartics;
};


# --------------------------------------------------------------------
sub getCamposXml {
# Descripcion:
# Retorna un hash con pares (<nombre_del_campo>, <valor_del_campo>)
# en base a un buffer xml dado.
#
# Parametros de entrada:
# $xmlData : buffer xml, obligatorio
# $campos  : lista de campos a cargar, separados por comas, optativo
#            Si no viene, se cargan todos los campos en el hash.
#
# Retorna:
# %camposHash : hash con los campos cargados.

    my ($xmlData, $campos) = @_;
    my %camposHash;
    my @camposLista = split(/, */, $campos);
    if ($campos) {
        foreach my $nombreCampo (@camposLista) {
            if ($xmlData =~ /<($nombreCampo)>(.+?)<\/\1>/is) {
                my $campoValor = $2;
                if ($campoValor =~ /<!\[CDATA\[(.*?)\]\]>/is) {
                    $campoValor = $1;
                };
                $camposHash{lc $nombreCampo} = $campoValor;
            };
        };
    } else {
        while ($xmlData =~ /<(\w+?)>(.+?)<\/\1>/sg) {
            my $nombreCampo = $1;
            my $campoValor = $2;

            if ($nombreCampo =~ /^fotofija_\w+$/) {
                #<fotofija_art200>
                #<_wfotofija_art200>468</_wfotofija_art200>
                #<_hfotofija_art200>60</_hfotofija_art200>
                #<![cdata[http://es.lipsum.com/images/black_468x60.gif]]>
                #</fotofija_art200>

                if ($campoValor =~ /<(_w$nombreCampo)>(.+?)<\/\1>/) {
                    $camposHash{lc "_w$nombreCampo"} = $2;
                };
                if ($campoValor =~ /<(_h$nombreCampo)>(.+?)<\/\1>/) {
                    $camposHash{lc "_h$nombreCampo"} = $2;
                };
            };

            if ($campoValor =~ /<!\[CDATA\[(.*?)\]\]>/is) {
                $campoValor = $1;
            };

            if ($nombreCampo =~ /^foto_\w+$/) {
                if ($campoValor) {
                    $camposHash{lc $nombreCampo} = 1;
                    #<foto_01>
                    #<_nomfoto_01>foto_0120090428105243.gif</_nomfoto_01>
                    #<_wfoto_01>20</_wfoto_01>
                    #<_hfoto_01>20</_hfoto_01>
                    #</foto_01>

                    if ($campoValor =~ /<(_nom$nombreCampo)>(.+?)<\/\1>/) {
                        $camposHash{"_NOM$nombreCampo"} = $2;
                    };
                    if ($campoValor =~ /<(_w$nombreCampo)>(.+?)<\/\1>/) {
                        $camposHash{lc "_W$nombreCampo"} = $2;
                    };
                    if ($campoValor =~ /<(_h$nombreCampo)>(.+?)<\/\1>/) {
                        $camposHash{lc "_H$nombreCampo"} = $2;
                    };
                };
            } else {
                $camposHash{lc $nombreCampo} = $campoValor;
            };
        };
    };

    return %camposHash;
};

# -------------------------------------------------------------------------#
# Reemplaza tildes por letras normales.
sub notildes {
  my($toencode) = $_[0];

  # convierte a latin1 para poder aplicar la er
  utf8::decode($toencode);

  $toencode =~ tr/áéíóúÁÉÍÓÚüÜñÑ/aeiouaeiouuunn/; # Destilda ISO.

  $toencode =~ s/&(.)acute;/$1/g;
  $toencode =~ s/&(.)tilde;/$1/g;
  $toencode =~ s/&(.)uml;/$1/g;
  $toencode =~ s/&(.)circ;/$1/g;
  $toencode =~ s/&(.)grave;/$1/g;

  $toencode =~ s/&[^;]+;//g; # Elimina toda otra entidad.

  $toencode=~s/\xC0/A/g;
  $toencode=~s/\xC1/A/g;
  $toencode=~s/\xC2/A/g;
  $toencode=~s/\xC3/A/g;
  $toencode=~s/\xC4/A/g;
  $toencode=~s/\xC5/A/g;
  $toencode=~s/\xC6/A/g;
  $toencode=~s/\xC7/C/g;
  $toencode=~s/\xC8/E/g;
  $toencode=~s/\xC9/E/g;
  $toencode=~s/\xCA/E/g;
  $toencode=~s/\xCB/E/g;
  $toencode=~s/\xCC/I/g;
  $toencode=~s/\xCD/I/g;
  $toencode=~s/\xCE/I/g;
  $toencode=~s/\xCF/I/g;
  $toencode=~s/\xD1/N/g;
  $toencode=~s/\xD2/O/g;
  $toencode=~s/\xD3/O/g;
  $toencode=~s/\xD4/O/g;
  $toencode=~s/\xD5/O/g;
  $toencode=~s/\xD6/O/g;

  $toencode=~s/\xD8/O/g;
  $toencode=~s/\xD9/U/g;
  $toencode=~s/\xDA/U/g;
  $toencode=~s/\xDB/U/g;
  $toencode=~s/\xDC/U/g;
  $toencode=~s/\xDD/Y/g;
  $toencode=~s/\xE0/a/g;
  $toencode=~s/\xE1/a/g;
  $toencode=~s/\xE2/a/g;
  $toencode=~s/\xE3/a/g;
  $toencode=~s/\xE4/a/g;
  $toencode=~s/\xE5/a/g;
  $toencode=~s/\xE6/a/g;
  $toencode=~s/\xE7/c/g;
  $toencode=~s/\xE8/e/g;
  $toencode=~s/\xE9/e/g;
  $toencode=~s/\xEA/e/g;
  $toencode=~s/\xEB/e/g;
  $toencode=~s/\xEC/i/g;
  $toencode=~s/\xED/i/g;
  $toencode=~s/\xEE/i/g;
  $toencode=~s/\xEF/i/g;
  $toencode=~s/\xF1/n/g;
  $toencode=~s/\xF2/o/g;
  $toencode=~s/\xF3/o/g;
  $toencode=~s/\xF4/o/g;
  $toencode=~s/\xF5/o/g;
  $toencode=~s/\xF6/o/g;
  $toencode=~s/\xF8/o/g;
  $toencode=~s/\xF9/u/g;
  $toencode=~s/\xFA/u/g;
  $toencode=~s/\xFB/u/g;
  $toencode=~s/\xFC/u/g;
  $toencode=~s/\xFF/y/g;

  # restaura a utf8
  utf8::encode($toencode);
  return $toencode;
}; # notildes


# ---------------------------------------------------------------
sub get_newer_edic {
    # Obtiene nombre de la edic mas nueva
    my (@entries, $entry);
    my ($dir) = $prontus_varglb::DIR_SERVER .
    $prontus_varglb::DIR_CONTENIDO .
    $prontus_varglb::DIR_EDIC;

    my $edic_base = 'base';

    @entries = &glib_fildir_02::lee_dir($dir);
    @entries = sort {$b cmp $a} (@entries);
    foreach $entry (@entries) {
        if ( ($entry ne $edic_base) && (-d "$dir/$entry") && ($entry =~ /^[0-9_]+$/)) {
            return $entry;
        };
    };
    return '';
};

# ---------------------------------------------------------------
sub conectar_prontus_bd() {

    my ($motor_bd, $nom_bd, $server_bd, $user_bd, $pwd_bd, $pathfile_sqlite) = @_;

    $motor_bd   = $prontus_varglb::MOTOR_BD if ($motor_bd eq '');
    $nom_bd     = $prontus_varglb::NOM_BD if ($nom_bd eq '');
    $server_bd  = $prontus_varglb::SERVER_BD if ($server_bd eq '');
    $user_bd    = $prontus_varglb::USER_BD if ($user_bd eq '');
    $pwd_bd     = $prontus_varglb::PWD_BD if ($pwd_bd eq '');

    $pathfile_sqlite = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/prontus_db.db" if ($pwd_bd eq '');

    my ($msg_ret, $base);

    # MYSQL
    if ($motor_bd eq 'MYSQL') {
        # $base = DBI->connect("DBI:mysql:$nom_bd:$server_bd", $user_bd, $pwd_bd, {'PrintError'=>1, mysql_enable_utf8 => 1 })
        $base = DBI->connect("DBI:mysql:$nom_bd:$server_bd", $user_bd, $pwd_bd, {'PrintError'=>1})
                || warn "DBI Error Code: [$DBI::err][$DBI::errstr] ";
        $msg_ret = "No es posible conectar con base de datos Prontus MySQL. Cod[$DBI::err][$DBI::errstr]" if ($DBI::err);
        $base->{mysql_auto_reconnect} = 1; # para evitar los MySQL server has gone away
    };

    # SQLITE
    if ($motor_bd eq 'PRONTUS') {
        if (!-f $pathfile_sqlite) {
            warn "Error: Archivo de Base de datos SQLite no existe [$pathfile_sqlite]";
            $msg_ret = "Archivo de Base de Datos no existe."
        } else {
            $base = DBI->connect("dbi:SQLite2:dbname=$pathfile_sqlite","","")
                    || warn "DBI Error Code: $DBI::err";
            $msg_ret = "No es posible conectar con base de datos Prontus SQLite. Cod[$DBI::err]" if ($DBI::err);
        };
    };

    # my $database_name = $base->get_info( 17 ); # nombre del motor
    # my $database_version = $base->get_info( 18 ); # version del motor
    # print STDERR "Motor BD: $database_name $database_version\n";

    return ($base, $msg_ret);

};

# ---------------------------------------------------------------
sub get_motor_from_bdhandler {
    my $base = shift;
    return 'MYSQL' if (uc $base->get_info(17) eq 'MYSQL');
    return 'PRONTUS';
};
# ---------------------------------------------------------------
sub read_file4include {
# Lee un archivo por completo para efectos de parsearlo como ssi simulada en los FIDs

# Param. de entrada :
# 0) Path real del archivo.

# Retorna : El texto leido | '' en caso que el archivo no exista.

    my ($archivo) = shift;
    my ($dir_server) = shift;

    my ($buffer) = '';

    if ( ($archivo !~ /^$dir_server\//) || ($archivo =~ /\.\./) ) {
        return '';
    };

    if (-f $archivo) {
        my ($size) = (-s $archivo);
        open (ARCHIVO,"<$archivo")
        || die "Fail Open file $archivo \n $!\n";
        binmode ARCHIVO;
        read ARCHIVO,$buffer,$size;
        close ARCHIVO;
    };

    return $buffer;

};
# ---------------------------------------------------------------
sub parse_includes {
  my $dir_server = shift;
  my $buffer = shift;

  $buffer =~ s/%%include\((.+?)\)%%/&read_file4include($dir_server . $1, $dir_server)/ige;
  return $buffer;
};
# ---------------------------------------------------------------
sub get_path_croncgi {
    use FindBin '$Bin';
    my $rutaScript = $Bin;
    return $rutaScript; # sin slash al final
};
#-----------------------------------------------------------------------
sub arch_antiguo {
# Determina si el archivo es mas antiguo que N segundos, de acuerdo a fecha/hora de modificacion.
    my ($pathArch) = shift;
    my ($n_segs) = shift;

    # Obtener estadisticas del arch.
    my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,
        $mtime, $ctime,  $blksize,  $blocks)= stat $pathArch;

    # Si los seg. de antiguedad de la pagina son mayores que $taxport_refresh_segs
    if ((time - $mtime) > $n_segs) {
      return 1; # es mas antiguo que N segundos
    };
    return 0;
};
# ---------------------------------------------------------------
sub get_relpathconf_by_prontus_id {
    my $prontus_id = shift;
    if ($prontus_id =~ /^[\w\-]+$/) {
        return "/$prontus_id/cpan/$prontus_id.cfg";
    };
    return '';
};
# ---------------------------------------------------------------
sub get_path_nice {

    my $pathnice = '/usr/bin/nice';
    if (! -f $pathnice) {
      $pathnice = '/usr/local/bin/nice';
      if (! -f $pathnice) {
        $pathnice = '/usr/nice';
        if (! -f $pathnice) {
          $pathnice = '';
        }
      }
    }
    return $pathnice;
};
# ---------------------------------------------------------------
sub handle_internal_error {
    # Imprime error al STDERR y retorna un msg amistoso para el usuario, o bien, hace un exit sin mas tramite
    my $msg_internal = shift;
    my $msg_external = shift;
    my $options = shift;
    my $exit;
    $exit = 1 if ($options =~ /(^|,) *exit *= *1 *(,|$)/);
    print STDERR $msg;
    exit if ($exit);
    return 'Error actualizando posiciones en la base de datos';
};
# ---------------------------------------------------------------
sub set_coreplt_ppal {
# Parsea plantilla de nivel principal en el core con reemplazos comunes.
# Asume que ya se paso por el load_config de prontus y se autentico al user.

    my ($buffer, $pathdir_macros) = @_; # el 2o es optativo, en caso de necesitar usar otro dir de macros

    # En primer lugar, agrega macros
    my ($dir_macros) = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/macros";   # ubicacion default
    $dir_macros = $pathdir_macros if (($pathdir_macros) && (-d $pathdir_macros)); # para sobreescribir ubic default

    $buffer = &lib_prontus::add_macros($buffer, $dir_macros, '', '');
    $buffer =~ s/%25%25/%%/sg;

    # oculta html correspondiente solo a admin
    $buffer =~ s/<!--admin_only-->.*?<!--\/admin_only-->//sg if ($prontus_varglb::USERS_PERFIL ne 'A');

    # oculta html prohibido para redactores
    $buffer =~ s/<!--hide_to_redactor-->.*?<!--\/hide_to_redactor-->//sg if ($prontus_varglb::USERS_PERFIL eq 'P');

    # oculta a html al admin
    $buffer =~ s/<!--hide_to_admin-->.*?<!--\/hide_to_admin-->//sg if ($prontus_varglb::USERS_PERFIL eq 'A');

    # oculta sistema comentarios
    $buffer =~ s/<!--comentarios-->.*?<!--\/comentarios-->//sg if ($prontus_varglb::COMENTARIOS ne 'SI');

    # quita la opcion de editar ediciones si el usuario no es admin o editor.
    if ($prontus_varglb::USERS_PERFIL ne 'A' && $prontus_varglb::USERS_PERFIL ne 'E') {
        $buffer =~ s/<!--admin_ediciones-->.*?<!--\/admin_ediciones-->//sg;
    };

    # quita la opcion de editar ediciones si esta deshabilitado y el usuario es editor.
    if ($prontus_varglb::EDITOR_ADMINISTRAR_EDICIONES eq 'NO' && $prontus_varglb::USERS_PERFIL eq 'E') {
        $buffer =~ s/<!--admin_ediciones-->.*?<!--\/admin_ediciones-->//sg;
    };


    # parseos comunes
    $buffer =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/ig;

    return $buffer;

};
# ---------------------------------------------------------------
sub get_url {
use LWP::UserAgent;
use HTTP::Response;

  my($url) = $_[0];
  my ($espera_segs) = $_[1];
  my ($type) = $_[2];


  $espera_segs = 30 if ($espera_segs eq '');
  $type = 'GET' if ($type eq '');

  return '' if (($url eq '') or ($url !~ /^https?/i));
  my($ua) = new LWP::UserAgent;
  $ua->timeout($espera_segs); # segs # default es 180
  $ua->agent('Mozilla/5.0 (Windows; U; Windows NT 5.1; es-ES; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'); # default es "libwww-perl/#.##"
  my($request) = new HTTP::Request($type, $url) || return ('', $!);
  my($response) = $ua->request($request) || return ('', $!);
  if ($response->is_success) {
    return ($response->content, '');
  } else {
    return ('', $response->status_line);
  };

}; # getHTML

# ---------------------------------------------------------------
sub add_generator_tag {
    my $buffer = shift;
    if ($buffer !~ /<meta name *= *["']Generator["']/i) {
        my $gen_content = "Prontus $prontus_varglb::RAMA_INSTALADA";
        $buffer =~ s/<\/head>/\n<meta name="Generator" content="$gen_content" \/>\n<\/head>/is;
    };
    return $buffer;
};

# ---------------------------------------------------------------
sub purge_cache {
    my ($path_file) = shift;
    my $relpath = &remove_front_string($path_file, $prontus_varglb::DIR_SERVER);

    if ($relpath !~ /\/site\/tax\/port\//is) {
        my $dir_pend = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/purgepend";
        &glib_fildir_02::check_dir($dir_pend) if (! -d $dir_pend);
        my $pid = $$;
        open(PURGEFILE, ">>$dir_pend/$^T_$pid.txt");
        print PURGEFILE $relpath . "\n";
        close PURGEFILE;
    };
};

# ---------------------------------------------------------------
sub cerrar_sesion {

    # Mata session
    my $sess_obj = Session->new(
                    'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                    'document_root'     => $prontus_varglb::DIR_SERVER)
                    || die("Error inicializando objeto Session: $Session::ERR\n");

    # Ver user logueado
    my %cookies = &lib_cookies::get_cookies();
    my $user_anterior = $cookies{'USERS_USR_' . $prontus_varglb::PRONTUS_ID};

    # Setear cookie en blanco para dar por terminada la sesion.
    &lib_cookies::set_simple_cookie('USERS_USR_' . $prontus_varglb::PRONTUS_ID, ''); # pa q no pueda navegar
    &lib_cookies::set_simple_cookie('KEY_' . $prontus_varglb::PRONTUS_ID, '');

    # libera recursos para info de concurrencia
    &lib_multiediting::free_concurrency( $prontus_varglb::DIR_SERVER,
                                          $prontus_varglb::PRONTUS_ID,
                                          'port',
                                          $user_anterior,
                                          $sess_obj->{id_session});

    &lib_multiediting::free_concurrency( $prontus_varglb::DIR_SERVER,
                                          $prontus_varglb::PRONTUS_ID,
                                          'art',
                                          $user_anterior,
                                          $sess_obj->{id_session});

    &lib_multiediting::free_lock( $prontus_varglb::DIR_SERVER,
                                          $prontus_varglb::PRONTUS_ID,
                                          'art',
                                          $user_anterior,
                                          $sess_obj->{id_session});

    &lib_multiediting::free_lock( $prontus_varglb::DIR_SERVER,
                                          $prontus_varglb::PRONTUS_ID,
                                          'port',
                                          $user_anterior,
                                          $sess_obj->{id_session});

    $sess_obj->end_session();
};

sub call_purge_proc {
    my $file_pend = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/purgepend/$^T_$$.txt";
    if (-f $file_pend) {
        my $cmd = "/usr/bin/perl $prontus_varglb::DIR_SERVER/$prontus_varglb::DIR_CGI_CPAN/prontus_purge_cache.cgi $prontus_varglb::PRONTUS_ID $file_pend >/dev/null 2>&1 &";
        #~ print STDERR "cmd[$cmd]\n";
        system $cmd;
    };
};


END {
    &call_purge_proc();
};

$SIG{INT} = \&call_purge_proc;
# -------------------------------END LIBRERIA------------------

return 1;
