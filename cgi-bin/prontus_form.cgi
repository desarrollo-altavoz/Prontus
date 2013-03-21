#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# El Formulario Prontus (prontus_form.cgi) es una aplicacion cgi que permite procesar el contenido
# de un formulario publicado a traves de un articulo Prontus.
# De esta manera, el operador Prontus crear formularios de contacto, encuestas y otros a voluntad,
# tal como lo hace con cualquier otro articulo Prontus.
# Al recibir como parametros ocultos las variables _TS (timestamp), _PRONTUS_ID y _FILE,
# prontus_form lee desde el xml del articulo todos los datos que requiere para el procesamiento
# del formulario.
#
# Los Formularios Prontus funcionan tomando datos publicados como parte del articulo y en base
# a ellos envia y opcionalmente almacena la informacion (respaldo de datos).
#
# El proceso de un Formulario Prontus se realiza mediante los siguientes pasos:
#
# 1.Se leen los datos submitidos y se ubica el articulo Prontus correspondiente.
# 2.Se leen los datos del articulo Prontus.
# 3.Se validan los datos y se leen las plantillas de respuesta.
# 4.Se construye la pagina de respuesta unica para el visitante y se envian los correos electronicos de datos y autorrespuesta.
# 5.Si es pertinente, se respaldan los datos.
# 6.Se redirige el browser hacia la pagina de respuesta a traves de un header Location.
# 7.Se limpia el directorio de paginas de respuesta eliminando las que tienen mas de 10 minutos de antigüedad.
#
# Configuracion
# -------------
# El Formulario Prontus se configura mediante variables Prontus estandar, a las que se agregan
# otras de uso reservado.
#
# * Variables Prontus Estandar
#   _TS          Timestamp de Prontus.
#   _FILE        Path completo al articulo Prontus.
#   _PRONTUS_ID  Identificador de la instancia de Prontus.
#   _form_vista  Identifica la vista que debe usarse para el proceso.
#                Si no existe esta variable, se asume la vista por defecto.
#
# * Variables Prontus Reservadas
# Para que el Formulario Prontus funcione correctamente, existe una serie de variables
# Prontus que deben definirse. Estas variables seran almacenadas en el archivo XML
# correspondiente, siendo leidas desde el por la cgi prontus_form.
#
# form_admin           E-mails de destino del formulario, separadas por comas.
#                      Si como parte del formulario se envia un dato con el nombre _admin,
#                      entonces ese dato sustituira a form_admin.
#                      El dato _admin puede tener un gato (#) en vez del @ para enganar a los spiders.
#                      Si el dato _admin es un numero, entonces el formulario se enviara al mail
#                      que esta en ese lugar de la lista separada por comas. !!! 1.5*
#                      1.6: Si el dato _admin es numerico, entonces se usara el mail correspondiente
#                           a ese numero de orden, partiendo de 1.
# form_from            E-mail del remitente. Esta variable es sustituida por el dato email,
#                      si es que existe en el formulario.
#                      Si el dato email no existe en el formulario, entonces no se enviara un
#                      mail de autorrespuesta.
#
# form_subject<_vista> Subject (asunto) del mensaje que llegara al administrador.
# form_subject_auto<_vista> Subject (asunto) del mensaje de autorrespuesta que se envia al remitente.
# form_signature<_vista> Firma del mail de salida
# form_msg_auto<_vista>  Mensaje de autorrespuesta que se envia al remitente.
# form_msg_exito<_vista> Mensaje de exito del sistema, en formato html.
# form_msg_error<_vista> Mensaje de error del sistema, en formato html.
#
# CHK_form_required_<nombre>   Indica que el dato <nombre> es obligatorio en el formulario.
# CHK_form_captcha_enable      Indica si se validará el captcha o no
# CHK_form_backup_datos        Si existe, realiza una copia de los datos recibidos en
#                                el directorio de respaldo, incluyendo los archivos adjuntos.
# Validacion de datos
# -------------------
# El Formulario Prontus validara automaticamente los datos que comiencen con:
#   - email o e-mail (se asume que es una direccion de correo electronico)
#   - rut            (se asume que es un RUT)
#   - telefono, phone, fax, celular o cellphone (se asume que es un numero telefonico)
#
# Los datos que comiencen con un underscore (_) no seran enviados ni almacenados.
#
# Plantillas
# ----------
# Las plantillas a utilizar se especifican en el formulario mediante los datos:
# _pag_exito = Plantilla de exito del sistema (solo el nombre del archivo, sin extension).
# _pag_error = Plantilla de error del sistema (solo el nombre del archivo, sin extension).
#
# Si estos datos no son incluidos, el Formulario Prontus empleara las plantillas:
#
# /<prontus_id>/plantillas/extra/form/pags/exito.<ext> - Plantilla de exito por defecto.
# /<prontus_id>/plantillas/extra/form/pags/error.<ext> - Plantilla de error por defecto.
#
# La extension debe ser la misma usada en el formulario, ya que se deduce de este.
#
# Dentro de ellos, la marca %%MSG%% sera sustituida por el mensaje del sistema.
#
# Servidor SMTP
# -------------
# El Formulario Prontus utiliza el servidor SMTP de prontus_nn-var.cfg
#
# Archivos temporales
# -------------------
# Los archivos temporales utilizados para entregar la respuesta al visitante se encuentran en:
#
# /<prontus_id>/site/cache/form/pags

# Historia de versiones.
# 1.0   17/03/2007 - ALD - Primera version.
# 1.1   17/04/2007 - ALD - Agrega posibilidad de parsear distintas paginas de exito o error.
#                       - Parsea datos en los subjects de los mensajes.
#                       - Parsea multivistas.
# 1.2   15/05/2007 - ALD - Procesa IFs y NIFs.
# 1.2.1 15/05/2007 - ALD - Elimina marcas no parseadas.
# 1.3   18/08/2007 - ALD - Corrige bug en regexp de nombre de archivo adjunto.
# 1.3.1 28/09/2007 - ALD - Corrige llamadas a rutinas aborta (faltaba el &).
# 1.3.2 02/10/2007 - ALD - Agrega retornos de carro despues del body para buen transporte de archivos adjuntos.
# 1.4   18/10/2007 - YCH - Determina DIR_SERVER usando funcion Prontus
#
# *** Actualizacion no publicada en release. Aplicada el 13/03/208.
# 1.5*  07/12/2007 - ALD - Agrega compatibilidad con multivistas.
#                        - Usa sendmail en caso de que no existe Mail::Sender. En ese caso solo envia mensajes simples, sin attach.
#
# 1.5   26/12/2007 - ALD - Corrige formato CSV.
# 1.6   03/01/2008 - ALD - Permite dato _admin numerico para indicar uno de los mails de administracion.
#                        - Permite que el mail del remitente sea vacio. En ese caso no se envia mail de autorrespuesta.
# 1.7   25/01/2008 - ALD - Hace que los datos CHK_form_required y CHK_form_backup_datos no sean enviados ni respaldados.
# 1.8   21/11/2008 - CVI - Se agrega variable form_signature<vista> para la firma de los mails. Por omisión va la antigua.
# 1.9   29/05/2009 - CVI - Se agrega validación de captcha
# 1.10  05/11/2009 - YCC - Elimina vulnerabilidades XSS
#                        - Elimina la cabecera HTML repetida en algunas invocaciones a &lib_form::aborta()
#                        - Valida extensiones de archivos a subir, usando lista blanca.
# 1.11  31/11/2009 - YCC - Cambia a minusculas refrencias a campos prontus, para 10.14.
# To-Do:
# - Revisar sensibilidad a las mayusculas.

# -------------------------------BEGIN SCRIPT--------------------
BEGIN {
    require 'dir_cgi.pm';
    my ($ROOTDIR) = $ENV{'DOCUMENT_ROOT'};  # Desde el web.
    $ROOTDIR .= '/' . $DIR_CGI_CPAN;
    unshift(@INC,$ROOTDIR); # Para dejar disponibles las librerias
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

# ##############################################
# DECLARACIONES GLOBALES.

use strict;

use File::Copy;
# use POSIX; # (manejo de fechas).

use prontus_varglb; &prontus_varglb::init(); # 1.4
use glib_fildir_02;
use glib_cgi_04;
use glib_html_02;
use glib_str_02;

use lib_captcha;
use lib_captcha2;
use lib_form;
use lib_validator;
use lib_mail;
use lib_maxrunning;

my $DEBUG = 0;    # 1.6 Flag para debug.

# Directorios de trabajo, dentro de la instancia de Prontus.
my $DATA_DIR = 'cpan/procs/form'; # Directorio para el almacenamiento de los datos de respaldo.
my $TMP_DIR   = 'plantillas/extra/form'; # /pags-vvv Directorio de las plantillas de exito y fracaso.
my $CACHE_DIR = 'site/cache/form'; # /pags-vvv Directorio de las paginas generadas.
my $VISTADIR = ''; # 1.5* Vista a utilizar en directorios.
my $VISTAVAR = ''; # 1.5* Sufijo de vista para variables.
my $SEPARADOR = ';'; # 1.5 Separador de campos del formato csv.
my $TS;           # Timestamp del articulo que contiene al formulario.
my $PRONTUS_ID;   # Nombre del Prontus.
my %PRONTUS_VARS; # Variables del xml Prontus.
my @DATOS;        # Nombres de los datos del formulario.
my @DATOS4IF;     # 1.2 Nombres de los datos del formulario que vienen completos. Usado para procesar los IFs.
my @ADMIN_MAILS;  # E-Mails de administracion (donde hay que dirigir la data del formulario).
my $TMP_EXITO;    # Plantilla de exito.
my $TMP_ERROR;    # Platilla de error.
my $ANSWERS_DIR;  # Directorio de las paginas de respuesta.
my $ANSWERID;     # Identificacion de la respuesta.
my $FECHA;        # Fecha de creacion del formulario. Usada para acceder a los datos xml.
my $EXT;          # Extension usada por Prontus. Se deduce del path del formulario.
my %MSGS;         # Mensajes de error.

# Para mostrar de inmediato la pagina de resultados.
$|=1;
# Una sola \n porque despues viene un header location.
print "Content-type: text/html\n";

binmode(STDOUT, ":utf8");

# ##############################################
# Inicializaciones varias.

# Inicializacion de mensajes de error.
$MSGS{'out_of_service'} = 'Sistema fuera de servicio. Intente otra vez m&aacute;s tarde ...';
$MSGS{'required_data'} = 'Este dato es obligatorio:';
$MSGS{'wrong_data'} = 'Este dato es incorrecto:';
$MSGS{'wrong_captcha'} = 'El c&oacute;digo de validaci&oacute;n ingresado no es v&aacute;lido';

#~ &lib_form::max_running(5); # Soporta un maximo de 5 copias corriendo.
# Soporta un maximo de n copias corriendo.
if (&lib_maxrunning::maxExcedido(5)) {
    &aborta("Error: Servidor ocupado. Intente otra vez m&aacute;s tarde."); # 1.3.1 # 1.10
};
    
# Variables globales.
my $ROOTDIR = $prontus_varglb::DIR_SERVER; # 1.4


# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

main: {
    if ($DEBUG) { print "\n<html><body><pre>Debug Mode\n"; };
    # Lee datos del chorro.
    &glib_cgi_04::new();

    # Inicializa las variables de invocacion.
    &get_form_data();

    # Valida las variables Prontus y las del formulario.
    &valida_data();

    # Envia mails y guarda datos si es pertinente.
    my $result = &data_management();
    if ($DEBUG) { print $result; };

    # Limpia el directorio de archivos temporales.
    &lib_form::garbage_collection("$ROOTDIR$ANSWERS_DIR");

    # Finaliza mostrando la pagina de exito.
    &salida('',$PRONTUS_VARS{'form_msg_exito'.$VISTAVAR},$TMP_EXITO);
}; # main

# ###################################################
# Funciones

# ------------------------------------------------------------------------- #
# Envia mails y guarda datos si es pertinente.
sub data_management {
    my($body,$data,$backupdir,$backupdata,$backupheaders,$buffer);
    my ($to,$from,$subj,$body,$filename,$filedata,$fecha,$hora,$ip);
    # my (@datos) = &glib_cgi_04::param();
    my ($result);
    my (%files);
    my ($random) = time . $$; # Mejor usamos el numero de proceso y listo. time . rand(1000000);
    # Detecta informacion de fecha, hora e IP.
    $fecha = &glib_hrfec_02::fecha_human();
    $hora = &glib_hrfec_02::hora_human();
    $ip = $ENV{'REMOTE_ADDR'};

    $backupdir = "$ROOTDIR/$PRONTUS_ID/$DATA_DIR/$TS";
    &glib_fildir_02::check_dir($backupdir);
    # Se obtiene el TS del envío
    my $TSENVIO = &glib_hrfec_02::get_dtime_pack4();
    while(-f $backupdir.'/'.$TSENVIO.'.json') {
        $TSENVIO = &glib_hrfec_02::suma_segs($TSENVIO, 1);
    }
    my $filejson = "$backupdir/$TSENVIO.json";
    &glib_fildir_02::check_dir($backupdir);
    &glib_fildir_02::write_file($filejson, 'lock... :)');

    my $data_json;
    $data_json->{'_fecha'} = $fecha;
    $data_json->{'_hora'} = $hora;
    $data_json->{'_ip'} = $ip;

    my $order_data;
    my $counter = 1;
    # Forma cuerpo para el administrador.
    # Lee formulario para determinar el orden de los datos.
    $buffer = &glib_fildir_02::read_file($ROOTDIR.&glib_cgi_04::param('_FILE'));
    $body = "Los datos recibidos son los siguientes:\n\n";
    $backupheaders .= "\"Fecha\"$SEPARADOR\"Hora\"$SEPARADOR\"IP\"$SEPARADOR";
    $backupdata .= "\"$fecha\"$SEPARADOR\"$hora\"$SEPARADOR\"$ip\"$SEPARADOR";
    foreach my $key (sort{index($buffer,"\"$a\"") <=> index($buffer,"\"$b\"")} @DATOS) {
        next if (($key =~ /^_/) || ($key =~ /CHK_form_required/) || ($key =~ /CHK_form_backup_datos/)); # 1.7
        $backupheaders .= '"' . $key . '"' . $SEPARADOR;
        # Determino si el dato es un archivo o no.
        # Si son varios, se adjuntara el ultimo.
        if (&glib_cgi_04::real_paths($key) ne '') { # Es un archivo.
            $filename = &glib_cgi_04::real_paths($key);
            $filename =~ s/.+[\/\\]([^\/\\]+)/$1/; # 1.3 Extrae path por si lo trae.
            $filedata = &glib_cgi_04::param($key);
            $files{$key}{'_name'} = 'file_' . $random.'--'.$filename;
            $files{$key}{'_temp'} = $filedata;
            $body .= sprintf('%-15s',$key) . " = $filename\n";
            $backupdata .= "\"file_$random--$filename\"$SEPARADOR"; # Pega el random para que el nombre sea unico.
        } else {
            $order_data->{$counter} = $key;
            $counter++;
            $data_json->{$key} = &glib_cgi_04::param($key);
            $data = &glib_str_02::trim(&glib_cgi_04::param($key)); # Elimina espacios para que no molesten.
            $body .= sprintf('%-15s',$key) . " = $data\n";
            $data =~ s/\"/\'\'/gs; # Convierte comillas para que no arruinen el archivo csv.
            $data =~ s/\r//gs;     # 1.5 Elimina retornos de carro para que no arruinen el archivo csv.
            $backupdata .= "\"$data\"$SEPARADOR";
        };
    };

    &glib_fildir_02::write_file("$backupdir/order.json", &JSON::to_json($order_data));

    # 1.8 - firma configureable CVI
    my $msg_signature = "\r\nRecibido el $fecha a las $hora desde el IP $ip\n";
    $msg_signature .= "\nAtentamente,\nProntus CMS\r\n\r\n";
    if($PRONTUS_VARS{'form_signature'.$VISTAVAR}) {
        $msg_signature = "\r\n" . $PRONTUS_VARS{'form_signature'.$VISTAVAR};
    }
    $body .= $msg_signature;

    # Envia mail a el o los administradores.
    if (&glib_cgi_04::param('email') ne '') {
        $from = &glib_cgi_04::param('email');
    } else {
        $from = $PRONTUS_VARS{'form_from'};
    };
    $subj = $PRONTUS_VARS{'form_subject'.$VISTAVAR};
    # 1.1    
    $subj = &procesaIFs($subj,1);
    foreach my $key (@DATOS) {
        # Elimina espacios para que no molesten.
        $data = &glib_str_02::trim(&glib_cgi_04::param($key));
        # 1.1 Reemplaza datos en subject.
        utf8::decode($data);
        $data =~ s/[^\w\-áéíóúüñÁÉÍÓÚÜÑ\, ]//g; # Elimina todo caracter extrano.
        utf8::encode($data);
        $subj =~ s/\%$key\%/$data/sg;
    };
    $subj =~ s/%\w+%//sg; # 1.2.1 Elimina tags no parseados.
    foreach my $email (@ADMIN_MAILS) {
        $to = $email;
        $result .= ' 1 ' . &lib_form::envia_mail($to,$from,$subj,$body,$filename,$filedata);

    };
    # Forma cuerpo para el remitente (autorrespuesta).
    if ($PRONTUS_VARS{'form_from'} ne '') {
        $result .= ' 2 ';
        $from = $PRONTUS_VARS{'form_from'};
        if (&glib_cgi_04::param('email') ne '') {
            $result .= ' 3 ';
            $to = &glib_cgi_04::param('email');
            $subj = $PRONTUS_VARS{'form_subject_auto'.$VISTAVAR};
            $body = $PRONTUS_VARS{'form_msg_auto'.$VISTAVAR};
            # 1.2 Procesa IFs y NIFs.
            $subj = &procesaIFs($subj,1);
            $body = &procesaIFs($body,1);
            foreach my $key (@DATOS) {
                # Elimina espacios para que no molesten.
                $data = &glib_str_02::trim(&glib_cgi_04::param($key));
                # 1.1 Reemplaza datos en subject y body.
                $body =~ s/\%$key\%/$data/sg;
                $data =~ s/[^\w\- ]//g; # Elimina todo caracter extrano en el subject.
                $subj =~ s/\%$key\%/$data/sg;
            };
            $body =~ s/%\w+%//sg; # Elimina tags no parseados.
            $subj =~ s/%\w+%//sg; # 1.2.1 Elimina tags no parseados.
            $result .= ' 5 ' . &lib_form::envia_mail($to,$from,$subj,$body,'','');
        };
    };
    # Sólo se incluyen los archivos en el JSON, si hay respaldo
    my $files_json;

    # Genera el backup, si es pertinente.
    if ($PRONTUS_VARS{'chk_form_backup_datos'} ne '') {
        if (-e "$backupdir/backup.csv") { # Si existe ya el archivo, no inserta la linea de encabezados.
            &glib_fildir_02::append_file("$backupdir/backup.csv","$backupdata\r\n");
        } else {
            &glib_fildir_02::append_file("$backupdir/backup.csv","$backupheaders\r\n$backupdata\r\n");
        };
        #if (keys %files) {
            # Mueve todos los archivos adjuntos.
            foreach my $file (keys %files) {
                my $name = $files{$file}{'_name'};
                my $temp = $files{$file}{'_temp'};
                File::Copy::move($temp,"$backupdir/$name");
                my $newfile = "$backupdir/$name";
                $newfile =~ s/^$prontus_varglb::DIR_SERVER//;
                $files_json->{$file} = $newfile;
            };
        #};
    };
    # Se escribe la respuesta json
    if($data_json) {
        my $resp;
        foreach my $llave (keys %{$data_json}) {
            # $data = &glib_str_02::trim(&glib_cgi_04::param($llave));
            $resp->{$llave} = $data_json->{$llave};
            # print $json->to_json($resp);
        };
        if (keys %{$files_json}) {
            $resp->{'_files'} = $files_json;;
        }
        &glib_fildir_02::write_file($filejson, &JSON::to_json($resp));

    } else {
        unlink($filejson);
    };
    return $result; # $result es solo para debug.
}; # dataManagement

# ------------------------------------------------------------------------- #
# Valida las variables Prontus y las del formulario.
sub valida_data {
    my($email,$file,$key,$nombre,$buffer,$dato,$form_admin,$plantilla); # 1.1
    my(@mails); # 1.6

    @DATOS = &glib_cgi_04::param();

    # 1.5 Determina la vista que se usara.
    $VISTADIR = &glib_cgi_04::param('_form_vista');
    $VISTADIR =~ s/[^a-z]//sg;
    if ($VISTADIR ne '') {
        $VISTAVAR = '_' . $VISTADIR; # Variable queda lista para ser inserta en los ids de variables.
        $VISTADIR = '-' . $VISTADIR; # Variable queda lista para ser inserta en los paths.
    };
    # Determina cuales seran los emails de destino (administrador).
    $form_admin = &glib_cgi_04::param('_admin');
    if ($form_admin eq '') {
        $form_admin = $PRONTUS_VARS{'form_admin'};
    } elsif ($form_admin =~ /^\d+$/) { # 1.6 Escoge el mail correlativo.
        @mails = split(/,/,$PRONTUS_VARS{'form_admin'});
        $form_admin = $mails[$form_admin - 1];
    };
    if ($form_admin eq '') {
        &lib_form::aborta("Error: no existe E-mail de destino."); # 1.10
    };
    $form_admin =~ s/\#/\@/g; # Sustituye # por @.
    $form_admin =~ s/\s+//g;  # Elimina espacios.
    # Validacion de las variables Prontus.
    @ADMIN_MAILS = split(/,/,$form_admin);
    foreach $email (@ADMIN_MAILS) {
        if ($email !~ /[\w\.\-\,\']+\@[\w\-\.]+\.[\w]+/) {
            &lib_form::aborta("Error: E-mail de destino incorrecto"); # 1.10
        };
    };
    # 1.6 Permite que el mail del remitente sea vacio. En ese caso no se envia mail de autorrespuesta.
    if ($PRONTUS_VARS{'form_from'} ne '') {
        if ($PRONTUS_VARS{'form_from'} !~ /[\w\.\-\,\']+\@[\w\-\.]+\.[\w]+/) {
            &lib_form::aborta("Error: E-mail del remitente incorrecto [" . $PRONTUS_VARS{'form_from'} . "]"); # 1.10
        };
    };
    # Deduce la extension del formulario.
    $file = &glib_cgi_04::param('_FILE');
    if ($file =~ /\.([\w]+)$/) {
        $EXT = $1;
    } else {
        &lib_form::aborta("Archivo inv&aacute;lido"); # 1.10
    };
    # 1.1 Establece cuales son y verifica que existen las plantillas basicas.
    if (&glib_cgi_04::param('_pag_exito') ne '') {
        $plantilla = &glib_cgi_04::param('_pag_exito');
        $plantilla =~ s/[^\w\-]//g; # Solo caracteres alfanumericos y - y _.
        $TMP_EXITO = &glib_fildir_02::read_file("$ROOTDIR/$PRONTUS_ID/$TMP_DIR/pags$VISTADIR/$plantilla\.$EXT");
    } else {
        $TMP_EXITO = &glib_fildir_02::read_file("$ROOTDIR/$PRONTUS_ID/$TMP_DIR/pags$VISTADIR/exito\.$EXT");
    };
    if ( $TMP_EXITO eq '') {
        &lib_form::aborta("No existe plantilla de exito.");
    };
    if (&glib_cgi_04::param('_pag_error') ne '') {
        $plantilla = &glib_cgi_04::param('_pag_error');
        $plantilla =~ s/[^\w\-]//g; # Solo caracteres alfanumericos y - y _.
        # Lee la plantilla del directorio de la vista.
        $TMP_ERROR = &glib_fildir_02::read_file("$ROOTDIR/$PRONTUS_ID/$TMP_DIR/pags$VISTADIR/$plantilla\.$EXT");
    } else {
        $TMP_ERROR = &glib_fildir_02::read_file("$ROOTDIR/$PRONTUS_ID/$TMP_DIR/pags$VISTADIR/error\.$EXT");
    };
    if ( $TMP_ERROR eq '' ) {
        &lib_form::aborta("No existe plantilla de error.");
    };
    &inicializaMensajes(\$TMP_ERROR);
    # Define directorio de las respuestas y la identificacion de esta.
    $ANSWERS_DIR = "/$PRONTUS_ID/$CACHE_DIR";
    if (! (-d "$ROOTDIR/$ANSWERS_DIR") ) {
        if (&glib_fildir_02::check_dir("$ROOTDIR/$ANSWERS_DIR") == 0) {
            &lib_form::aborta("No se puede crear directorio de respuestas [$ANSWERS_DIR].");
        };
    };

  # YCC: esto se comenta porque esta demas, el p.form escribe en la raiz de site/cache/form
  # if (! (-d "$ROOTDIR/$ANSWERS_DIR/pags") ) {
    # if (&crea_dir("$ROOTDIR/$ANSWERS_DIR/pags") == 0) {
      # &lib_form::aborta("No se puede crear directorio de respuestas [$ANSWERS_DIR/pags].");
    # };
  # };

    $ANSWERID = $PRONTUS_ID . $TS . time . $$; # rand(1000000000);
    # Lee el servidor SMTP definido para Prontus.
    # SERVER_SMTP= 'localhost'
    $buffer = &glib_fildir_02::read_file("$ROOTDIR/$PRONTUS_ID/cpan/$PRONTUS_ID-var.cfg");
    my $server_smtp;
    if ($buffer =~ /SERVER_SMTP\s*=\s*\'(.+?)\'/s) {
        $server_smtp = $1;
    };
    if ($server_smtp eq '') {
        &salida($MSGS{'out_of_service'},$PRONTUS_VARS{'form_msg_error'.$VISTAVAR},$TMP_ERROR);
    };
    $lib_form::SERVER_SMTP = $server_smtp;

    # 1.9
    # Chequea Captcha si es que es requerido
    if($PRONTUS_VARS{'chk_form_captcha_enable'} ne '') {

        # Usando la nueva lib_captcha se manejan ambos formatos
        my $captcha_input = &glib_cgi_04::param('_CAPTCHA_FORM');
        my $captcha_type = 'form'; # custom
        my $captcha_img = &glib_cgi_04::param('_captcha_img');
        my $captcha_code = &glib_cgi_04::param('_captcha_code');
        $captcha_input = &glib_cgi_04::param('_captcha_text') unless($captcha_input);
        #~ require 'dir_cgi.pm';
        &lib_captcha2::init($prontus_varglb::DIR_SERVER, $prontus_varglb::DIR_CGI_CPAN);
        my $msg_err_captcha = &lib_captcha2::valida_captcha($captcha_input, $captcha_code, $captcha_type, $captcha_img);
        if ($msg_err_captcha ne '') {
            &salida($MSGS{'wrong_captcha'}, $PRONTUS_VARS{'form_msg_error'.$VISTAVAR}, $TMP_ERROR);
        };
    };

    # Chequea campos requeridos.
    foreach $key (keys %PRONTUS_VARS) {
        if ($key =~ /chk_form_required_(\w+)/) {
            $nombre = $1;
            $MSGS{$nombre} = &glib_html_02::text2html($nombre) unless($MSGS{$nombre});
            if (&glib_cgi_04::param($nombre) eq '') {
                &salida($MSGS{'required_data'} .' '. $MSGS{$nombre}, $PRONTUS_VARS{'form_msg_error'.$VISTAVAR}, $TMP_ERROR);
            };
        };
    };

    # Valida los datos segun el tipo, el cual se deduce del nombre.
    foreach $nombre (@DATOS) {
        $dato = &glib_str_02::trim(&glib_cgi_04::param($nombre)); # Elimina espacios para que no molesten.
        next if ($dato eq ''); # Solo valida datos ingresados.
        push @DATOS4IF, $nombre;
        if ($nombre =~ /^rut/i) { # Valida RUTs.
            if (! &lib_validator::chequea_rut($dato)) {
                my $nombre_dato = $MSGS{$nombre};
                $nombre_dato = &glib_html_02::text2html($nombre) unless($nombre_dato);
                &salida($MSGS{'wrong_data'} .' '. $nombre_dato,$PRONTUS_VARS{'form_msg_error'.$VISTAVAR},$TMP_ERROR);
            };
        };
        if (($nombre =~ /^telefono/i) || ($nombre =~ /^fono/i)
                || ($nombre =~ /^phone/i) || ($nombre =~ /^celular/i)
                || ($nombre =~ /^fax/i) || ($nombre =~ /^cellphone/i) ) { # Valida telefonos.
            if (! &lib_validator::chequea_telefono($dato)) {
                my $nombre_dato = $MSGS{$nombre};
                $nombre_dato = &glib_html_02::text2html($nombre) unless($nombre_dato);
                &salida($MSGS{'wrong_data'} .' '. $nombre_dato,$PRONTUS_VARS{'form_msg_error'.$VISTAVAR},$TMP_ERROR);
            };
        };
        if (($nombre =~ /^email/i) || ($nombre =~ /^e-mail/i)) { # Valida emails.
            if (! &lib_validator::chequea_email($dato)) {
                my $nombre_dato = $MSGS{$nombre};
                $nombre_dato = &glib_html_02::text2html($nombre) unless($nombre_dato);
                &salida($MSGS{'wrong_data'} .' '. $nombre_dato,$PRONTUS_VARS{'form_msg_error'.$VISTAVAR},$TMP_ERROR);
            };
        };

        # Aprovecha de validar las extensiones de los archivos que se esten intentando subir. # 1.10
        if (&glib_cgi_04::real_paths($nombre) ne '') { # Es un archivo.
            my $upload_filename = &glib_cgi_04::real_paths($nombre);
            if ($upload_filename !~ /(\.pdf|\.doc|\.docx|\.rtf|\.xls|\.xlsx|\.csv|\.zip|\.rar|\.jpg|\.jpeg|\.gif|\.png|\.bmp|\.txt|\.ppt|\.pptx|\.swf)$/i) {
                &salida('El tipo de archivo que est&aacute; intentando subir no es v&aacute;lido',$PRONTUS_VARS{'form_msg_error'.$VISTAVAR},$TMP_ERROR);
            };
        };
    };
}; # validaData

# ------------------------------------------------------------------------- #
# Inicializa las variables de invocacion.
sub get_form_data {
    my($xmlpath);
    $TS = &glib_cgi_04::param('_TS'); # Timestamp.
    if ($TS !~ /\d{14}/) {
        &lib_form::aborta("Error: Formulario no identificado."); # 1.3.1 # 1.10
    };
    $FECHA = substr($TS,0,8);
    $PRONTUS_ID = &glib_cgi_04::param('_PRONTUS_ID'); # Nombre del Prontus.
    if ($PRONTUS_ID eq '') {
        &lib_form::aborta("Error: Prontus no identificado."); # 1.3.1 # 1.10
    };
    # Busca y lee las variables Prontus del articulo.
    $xmlpath = "$ROOTDIR/$PRONTUS_ID/site/artic/$FECHA/xml/$TS\.xml";
    &get_prontus_vars($xmlpath);
}; # getFormData

# ------------------------------------------------------------------------- #
# Lee las variables Prontus del articulo a partir de su xml.
# Por simplicidad lo carga todo en el hash %PRONTUS_VARS.
sub get_prontus_vars {
    my ($path_final_xml) = $_[0];
    my $xml = &glib_fildir_02::read_file($path_final_xml);
    while ($xml =~ /<([^>]+)>[\s\n\r]+<\!\[CDATA\[(.+?)\]\]>[\s\n\r]+<\/\1>/gis) {
        $PRONTUS_VARS{$1} = &glib_str_02::trim($2); # Elimina espacios para que no molesten.
    };
}; # get_prontus_vars

# ------------------------------------------------------------------------- #
# Finaliza con un mensaje de exito o error entregado utilizando la plantilla
# de exito o error.
# Los parametros son: mensaje, plantilla de mensaje y plantilla de pagina.
sub salida {
    my ($msg,$err,$plantilla) = @_;
    # Lee la plantilla del directorio de la vista.
    # $plantilla = &glib_fildir_02::read_file("$ROOTDIR/$PRONTUS_ID/$TMP_DIR/pags$VISTADIR/$template");
    if ($plantilla ne '') {
        # 1.2 Procesa IFs y NIFs.
        $plantilla = &procesaIFs($plantilla,2);
        $err = &procesaIFs($err,1);
        # Parsea los datos dentro de la plantilla y dentro del mensaje de exito.
        foreach my $key (@DATOS) {
            my $valor = &glib_html_02::text2html(&glib_str_02::trim(&glib_cgi_04::param($key)));
            $plantilla =~ s/%%$key%%/$valor/sieg;
            $err =~ s/%$key%/$valor/sieg;
        };
        # Inserta mensaje de error.
        $err =~ s/%err%/$msg/si;
        # Elimina tags no parseados en el mensaje.
        $err =~ s/%\w+%//sg;

        # Sustituye mensaje en la plantilla.
        $plantilla =~ s/%%MSG%%/$err/si;
        $plantilla =~ s/%%_referer%%/$ENV{'HTTP_REFERER'};/si;
        $plantilla =~ s/%%_answerpage%%/$ANSWERS_DIR\/$ANSWERID\.$EXT/si;

        # Elimina tags no parseados en la plantilla.
        $plantilla =~ s/%%\w+%%//sg; # 1.2.1
        $plantilla =~ s/%\w+%//sg;
        # Verifica que existe el directorios de cache y los crea si no es asi.
        if (! (-d "$ROOTDIR/$ANSWERS_DIR") ) {
            if (&glib_fildir_02::check_dir("$ROOTDIR/$ANSWERS_DIR") == 0) {
                &lib_form::aborta("No se puede crear directorio de respuestas [$ANSWERS_DIR].");
            };
        };

        # Escribe el archivo de respuesta.
        my $archivo = "$ROOTDIR/$ANSWERS_DIR/$ANSWERID\.$EXT";
        open (ARCHIVO,">$archivo")
                || die "Content-Type: text/plain\n\n Fail Open file $archivo \n $!\n";
        #binmode(ARCHIVO, ":utf8");
        print ARCHIVO $plantilla; #Escribe buffer completo
        close ARCHIVO;

        # Redirige al visitante hacia la pagina de respuesta.
        # print "Location: /$ANSWERS_DIR/$ANSWERID\.$EXT\n\n";
        # 02/01/2012 - CVI - se quita slash del comienzo para evitar // con error en nginx
        print "Location: $ANSWERS_DIR/$ANSWERID\.$EXT\n\n";
        exit;
    } else {
        &lib_form::aborta("Error: NO existe directorio de plantillas."); # 1.10
    };
}; # salida

# ------------------------------------------------------------------------- #
# Procesa los IFs y los NIFs en el string pasado como parametro, de acuerdo
# a si las variables estan o no presentes en @DATOS.
sub procesaIFs {
    my($buffer) = $_[0];
    my($numpers) = $_[1];
    my($regexp1,$regexp2,$pre,$post,$cuerpo,$tipo,$variable,$esta,$nombre,$valor);
    if ($numpers == 1) {
        $regexp1 = '%(n?if)\(([\w\=]+)\)%(.+?)%\/n?if%';
        $regexp2 = '%(n?if)\(([\w\=]+)\)%';
    } else {
        $regexp1 = '%%(n?if)\(([\w\=]+)\)%%(.+?)%%\/n?if%%';
        $regexp2 = '%%(n?if)\(([\w\=]+)\)%%';
    };
    # Busca el inicio y el fin de un IF o NIF.
    while ($buffer =~ /$regexp1/isg) {
        $pre = $`;
        $post = $';
        $tipo = lc $1;
        $variable = $2;
        $cuerpo = $3;
        # Avanza hasta el ultimo nivel de inicio de IF para permitir anidamiento.
        while($cuerpo =~ /$regexp2/isg) {
            $cuerpo = $';
            $pre .= "%$tipo($variable)%" . $`;
            $tipo = $1;
            $variable = $2;
        };
        # Determina y ejecuta el tipo de chequeo sobre la variable.
        if ($variable =~ /=/) {
            ($nombre,$valor) = split(/=/,$variable);
            if (&glib_cgi_04::param($nombre) eq $valor) {
                $esta = 1;
            } else {
                $esta = 0;
            };
        } else {
            if (grep {$_ eq $variable} @DATOS4IF) {
                $esta = 1;
            } else {
                $esta = 0;
            };
        };
        # Reconstruye buffer de acuerdo a la logica.
        if ($tipo eq 'if') {
            if ($esta) {
                $buffer = $pre . $cuerpo . $post;
            } else {
                $buffer = $pre . $post;
            };
        } else {
            if ($esta) {
                $buffer = $pre . $post;
            } else {
                $buffer = $pre . $cuerpo . $post;
            };
        };
    };
    return $buffer;
}; # procesaIFs

# -------------------------------------------------------------------------#
# Busca, inicializa y elimina mensajes dentro de la plantilla.
# Carga hash de mensajes (%MSGS).
#     <!-- MSG xxx = xxx -->
sub inicializaMensajes {
    my($plantilla) = $_[0];
    while ($$plantilla =~ /<!--\s*MSG\s*(\w+)\s*=\s*(.+?)\s*-->/sg) {
        $MSGS{$1} = $2;
    };
    # Elimina mensajes de la plantilla.
    $$plantilla =~ s/<!--\s*MSG\s*(\w+)\s*=\s*(.+?)\s*-->//sg;
}; # inicializaMensajes

