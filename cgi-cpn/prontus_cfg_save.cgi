#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 08/04/2011 - JOR - Primera versión
# ---------------------------------------------------------------


# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------------------------------------------

BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);

    # Incluir path de coment/
    use FindBin '$Bin';
};

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use glib_fildir_02;
use glib_hrfec_02;
use glib_dbi_02;
use File::Copy;
use lib_prontus;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my (%FORM);

main: {
    # Rescatar parametros recibidos.

    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # user no valido
    if ($prontus_varglb::USERS_ID eq '') {
        #~ &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    # Variables de configuracion validas.
    my %hash_defaultvars;

    # -art.cfg
    $hash_defaultvars{'art'}{'FORM_PLTS'} = 'FORM_PLTS;(.*?);;M';

    # -id.cfg
    $hash_defaultvars{'id'}{'PRONTUS_ID'} = 'PRONTUS_ID;(.*?);' . $prontus_varglb::PRONTUS_ID . ';U';
    $hash_defaultvars{'id'}{'RELDIR_BASE'} = 'RELDIR_BASE;(\/.*?);/;U';

    # -bd.cfg
    $hash_defaultvars{'bd'}{'NOM_BD'} = 'NOM_BD;(\w+);' . $prontus_varglb::NOM_BD . ';U';
    $hash_defaultvars{'bd'}{'USER_BD'} = 'USER_BD;(\w+);' . $prontus_varglb::USER_BD . ';U';
    $hash_defaultvars{'bd'}{'PWD_BD'} = 'PWD_BD;(\w+);' . $prontus_varglb::PWD_BD . ';U';
    $hash_defaultvars{'bd'}{'SERVER_BD'} = 'SERVER_BD;(\w+);' . $prontus_varglb::SERVER_BD . ';U';
    #$hash_defaultvars{'bd'}{'ADMIN_BASEDATOS'} = 'ADMIN_BASEDATOS;(SI|NO);NO;U';
    $hash_defaultvars{'bd'}{'MOTOR_BD'} = 'MOTOR_BD;(MYSQL|PRONTUS);MYSQL;U';

    # -var.cfg
    $hash_defaultvars{'var'}{'ACTUALIZACIONES'} = 'ACTUALIZACIONES;(SI|NO);SI;U';
    $hash_defaultvars{'var'}{'SERVER_SMTP'} = 'SERVER_SMTP;(\w+);localhost;U';
    $hash_defaultvars{'var'}{'PUBLIC_SERVER_NAME'} = 'PUBLIC_SERVER_NAME;(\w+);;U';
    $hash_defaultvars{'var'}{'CONTROL_FECHA'} = 'CONTROL_FECHA;(SI|NO);NO;U';
    $hash_defaultvars{'var'}{'CONTROLAR_ALTA_ARTICULOS'} = 'CONTROLAR_ALTA_ARTICULOS;(SI|NO);NO;U';
    #$hash_defaultvars{'var'}{'ACTUALIZACION_MASIVA'} = 'ACTUALIZACION_MASIVA;(SI|NO);NO;U';
    $hash_defaultvars{'var'}{'FRIENDLY_URLS'} = 'FRIENDLY_URLS;(SI|NO);NO;U';
    $hash_defaultvars{'var'}{'FRIENDLY_URLS_VERSION'} = 'FRIENDLY_URLS_VERSION;(1|2);1;U';
    $hash_defaultvars{'var'}{'COMENTARIOS'} = 'COMENTARIOS;(SI|NO);NO;U';
    $hash_defaultvars{'var'}{'ARTIC_ACTUALIZA_PORTS'} = 'ARTIC_ACTUALIZA_PORTS;(SI|NO);NO;U';
    #$hash_defaultvars{'var'}{'VERIFICAR_INSTALACION'} = 'VERIFICAR_INSTALACION;(SI|NO);NO;U';
    $hash_defaultvars{'var'}{'VTXT_PASTE_NEWLINES_AS_P'} = 'VTXT_PASTE_NEWLINES_AS_P;(SI|NO);NO;U';
    $hash_defaultvars{'var'}{'VTXT_DTD'} = 'VTXT_DTD;(STRICT|TRANSITIONAL);STRICT;U';
    $hash_defaultvars{'var'}{'VARNISH_SERVER_NAME'} = 'VARNISH_SERVER_NAME;(\w+);;M';
    $hash_defaultvars{'var'}{'POST_PROCESO'} = 'POST_PROCESO;(\w+);;U';
    $hash_defaultvars{'var'}{'MULTIVISTA'} = 'MULTIVISTAS;(\w+);;M';
    $hash_defaultvars{'var'}{'UPLOADS_PERMITIDOS'} = 'UPLOADS_PERMITIDOS;(\w+);' . $prontus_varglb::UPLOADS_PERMITIDOS . ';U';
    $hash_defaultvars{'var'}{'UPLOADS_EXTRAS'} = 'UPLOADS_EXTRAS;(\w+);;U';
    $hash_defaultvars{'var'}{'DIR_FFMPEG'} = 'DIR_FFMPEG;(\w+);/usr/local/bin;U';
    $hash_defaultvars{'var'}{'ABRIR_FIDS_EN_POP'} = 'ABRIR_FIDS_EN_POP;(SI|NO);NO;U';
    $hash_defaultvars{'var'}{'SCRIPT_QUOTA'} = 'SCRIPT_QUOTA;(\w+);;U';
    $hash_defaultvars{'var'}{'FOTO_MAX_PIXEL'} = 'FOTO_MAX_PIXEL;(.*?);;U';
    $hash_defaultvars{'var'}{'FFMPEG_PARAMS'} = 'FFMPEG_PARAMS;(.*?);;U';
    $hash_defaultvars{'var'}{'BLOQUEO_EDICION'} = 'BLOQUEO_EDICION;(\d+);;U';
    $hash_defaultvars{'var'}{'MAX_XCODING'} = 'MAX_XCODING;(\d+);50;U';

    # -port.cfg
    $hash_defaultvars{'port'}{'MULTI_EDICION'} = 'MULTI_EDICION;(SI|NO);NO;U';
    $hash_defaultvars{'port'}{'ADMIN_PORT'} = 'ADMIN_PORT;(SI|NO);NO;U';
    $hash_defaultvars{'port'}{'EDICBASE_INI_SELECTED'} = 'EDICBASE_INI_SELECTED;(SI|NO);NO;U';
    $hash_defaultvars{'port'}{'BASE_PORTS'} = 'BASE_PORTS;(.*?);;M';
    $hash_defaultvars{'port'}{'PORT_DRAGANDROP'} = 'PORT_DRAGANDROP;(.*?);;M';
    $hash_defaultvars{'port'}{'PORT_PLTS'} = 'PORT_PLTS;(.*?);;M';
    $hash_defaultvars{'port'}{'PORT_INI_SELECTED'} = 'PORT_INI_SELECTED;(.*?);;U';
    $hash_defaultvars{'port'}{'PORT_HOME'} = 'PORT_HOME;(.*?);;U';

    # -usr.cfg
    $hash_defaultvars{'usr'}{'REDACTOR_VER_ARTICULOS_AJENOS'} = 'REDACTOR_VER_ARTICULOS_AJENOS;(SI|NO);SI;U';
    $hash_defaultvars{'usr'}{'REDACTOR_EDITAR_ARTICULOS_AJENOS'} = 'REDACTOR_EDITAR_ARTICULOS_AJENOS;(SI|NO);SI;U';
    $hash_defaultvars{'usr'}{'EDITOR_VER_ARTICULOS_AJENOS'} = 'EDITOR_VER_ARTICULOS_AJENOS;(SI|NO);SI;U';
    $hash_defaultvars{'usr'}{'EDITOR_EDITAR_ARTICULOS_AJENOS'} = 'EDITOR_EDITAR_ARTICULOS_AJENOS;(SI|NO);SI;U';
    $hash_defaultvars{'usr'}{'EDITOR_ADMINISTRAR_EDICIONES'} = 'EDITOR_ADMINISTRAR_EDICIONES;(SI|NO);SI;U';

    # -tax.cfg
    $hash_defaultvars{'tax'}{'TAXONOMIA_NIVELES'} = 'TAXONOMIA_NIVELES;[0-3];0;U';
    $hash_defaultvars{'tax'}{'NUM_RELAC_DEFAULT'} = 'NUM_RELAC_DEFAULT;^(\d+)$;5;U';
    $hash_defaultvars{'tax'}{'TAXPORT_ARTXPAG'} = 'TAXPORT_ARTXPAG;^(\d+)$;20;U';
    #~ $hash_defaultvars{'tax'}{'TAXPORT_REFRESH_SEGS'} = 'TAXPORT_REFRESH_SEGS;^(\d+)$;1800;U';
    #~ $hash_defaultvars{'tax'}{'TAXPORT_REFRESH'} = 'TAXPORT_REFRESH;(SI|NO);NO;U';
    $hash_defaultvars{'tax'}{'TAXPORT_MAXARTICS'} = 'TAXPORT_MAXARTICS;^(\d+)$;500;U';
    $hash_defaultvars{'tax'}{'TAXPORT_ORDEN'} = 'TAXPORT_ORDEN;^(PUBLICACION|TITULAR|CREACION)\((ASC|DESC)\)$;PUBLICACION(DESC);U';

    # -tag.cfg
    $hash_defaultvars{'tag'}{'TAGPORT_ARTXPAG'} = 'TAGPORT_ARTXPAG;^(\d+)$;20;U';
    $hash_defaultvars{'tag'}{'TAGPORT_MAXARTICS'} = 'TAGPORT_MAXARTICS;^(\d+)$;500;U';
    $hash_defaultvars{'tag'}{'TAGPORT_ORDEN'} = 'TAGPORT_ORDEN;^(PUBLICACION|TITULAR|CREACION)\((ASC|DESC)\)$;PUBLICACION(DESC);U';
    $hash_defaultvars{'tag'}{'MAX_LAST_TAGS_4FID'} = 'MAX_LAST_TAGS_4FID;^(\d+)$;15;U';

    # -list.cfg
    $hash_defaultvars{'list'}{'LIST_PROCESO_INTERNO'} = 'LIST_PROCESO_INTERNO;(SI|NO);SI;U';
    $hash_defaultvars{'list'}{'LIST_MAXARTICS'} = 'LIST_MAXARTICS;^(\d+)$;20;U';
    $hash_defaultvars{'list'}{'LIST_ORDEN'} = 'LIST_ORDEN;^(PUBLICACION|TITULAR|CREACION)\((ASC|DESC)\)$;PUBLICACION(DESC);U';
    #~ $hash_defaultvars{'list'}{'LIST_ARTXPAG'} = 'LIST_ARTXPAG;^(\d+)$;20;U';

    # -coment.cfg
    $hash_defaultvars{'coment'}{'NOM'} = 'NOM;(\w+);Artículos;U';
    $hash_defaultvars{'coment'}{'ARTIC_EXTENSION'} = 'ARTIC_EXTENSION;(\w+);html;U';
    $hash_defaultvars{'coment'}{'MSG_MODER'} = 'MSG_MODER;(\w+);Su comentario fue recibido y será publicado en las siguientes horas;U';
    $hash_defaultvars{'coment'}{'MSG_NOMODER'} = 'MSG_NOMODER;(\w+);Gracias por enviar su comentario;U';
    $hash_defaultvars{'coment'}{'LIMIT_CHARS'} = 'LIMIT_CHARS;^(\d+)$;1000;U';
    $hash_defaultvars{'coment'}{'FILASXPAG_PUBLIC'} = 'FILASXPAG_PUBLIC;^(\d+)$;8;U';
    $hash_defaultvars{'coment'}{'CAPTCHA'} = 'CAPTCHA;(SI|NO);NO;U';
    $hash_defaultvars{'coment'}{'ENVIAR_MAIL_PUBLICACION'} = 'ENVIAR_MAIL_PUBLICACION;(SI|NO);NO;U';
    $hash_defaultvars{'coment'}{'MAIL_PUBLICACION_FROM'} = 'MAIL_PUBLICACION_FROM;(\w+);;U';
    $hash_defaultvars{'coment'}{'MAIL_PUBLICACION_ASUNTO'} = 'MAIL_PUBLICACION_ASUNTO;(\w+);;U';
    $hash_defaultvars{'coment'}{'MAIL_PUBLICACION_SMTP'} = 'MAIL_PUBLICACION_SMTP;(\w+);localhost;U';
    $hash_defaultvars{'coment'}{'PHP_SESSION_PATH'} = 'PHP_SESSION_PATH;(\w+);;U';
    $hash_defaultvars{'coment'}{'PHP_SESSION_NAME'} = 'PHP_SESSION_NAME;(\w+);PHPSESSID;U';
    $hash_defaultvars{'coment'}{'MODERACION'} = 'MODERACION;(SI|NO);SI;U';

    # buscador_prontus.cfg
    $hash_defaultvars{'buscador'}{'RAW_FILETYPES'} = 'RAW_FILETYPES;(\w+);html htm shtml php asp;U';
    $hash_defaultvars{'buscador'}{'URL_FILETYPES'} = 'URL_FILETYPES;(\w+);html htm shtml php asp jsp;U';
    $hash_defaultvars{'buscador'}{'URL_MAXPAGS'} = 'URL_MAXPAGS;^(\d+)$;100;U';
    $hash_defaultvars{'buscador'}{'FIDS'} = 'FIDS;(\w+);;U';
    $hash_defaultvars{'buscador'}{'RESUMEN'} = 'RESUMEN;^(\d+)$;200;U';
    $hash_defaultvars{'buscador'}{'MAXCARS'} = 'MAXCARS;^(\d+)$;100000;U';
    $hash_defaultvars{'buscador'}{'RATIO'} = 'RATIO;^(\d+)$;98;U';
    $hash_defaultvars{'buscador'}{'MINTEXT'} = 'MINTEXT;^(\d+)$;5;U';
    $hash_defaultvars{'buscador'}{'TITLEVAR'} = 'TITLEVAR;(\w+);_TXT_TITULAR;U';
    $hash_defaultvars{'buscador'}{'TEXTVARS'} = 'TEXTVARS;(\w+);_TXT_bajada VTXT_CUERPO;U';
    $hash_defaultvars{'buscador'}{'RESPERPAG'} = 'RESPERPAG;^(\d+)$;50;U';
    $hash_defaultvars{'buscador'}{'MAXPAGS'} = 'MAXPAGS;^(\d+)$;20;U';
    $hash_defaultvars{'buscador'}{'PRONTUS_VER'} = 'PRONTUS_VER;^(\d+)$;10;U';
    $hash_defaultvars{'buscador'}{'SEARCH_MAXEXEC'} = 'SEARCH_MAXEXEC;^(\d+)$;5;U';

    $hash_defaultvars{'buscador'}{'USEFRIENDLYURLS'} = 'USEFRIENDLYURLS;(1|0);0;U';

    $hash_defaultvars{'buscador'}{'META1'} = 'META2;(\w+);;U';
    $hash_defaultvars{'buscador'}{'META2'} = 'META2;(\w+);;U';
    $hash_defaultvars{'buscador'}{'META3'} = 'META3;(\w+);;U';

    $hash_defaultvars{'buscador'}{'METADATA1'} = 'METADATA1;(\w+);;U';
    $hash_defaultvars{'buscador'}{'METADATA2'} = 'METADATA2;(\w+);;U';
    $hash_defaultvars{'buscador'}{'METADATA3'} = 'METADATA3;(\w+);;U';
    $hash_defaultvars{'buscador'}{'METADATA4'} = 'METADATA4;(\w+);;U';
    $hash_defaultvars{'buscador'}{'METADATA5'} = 'METADATA5;(\w+);;U';
    $hash_defaultvars{'buscador'}{'METADATA6'} = 'METADATA6;(\w+);;U';
    $hash_defaultvars{'buscador'}{'METADATA7'} = 'METADATA7;(\w+);;U';
    $hash_defaultvars{'buscador'}{'METADATA8'} = 'METADATA8;(\w+);;U';
    $hash_defaultvars{'buscador'}{'METADATA9'} = 'METADATA9;(\w+);;U';
    $hash_defaultvars{'buscador'}{'METADATA10'} = 'METADATA10;(\w+);;U';

    # Verificar tipo de CFG.
    $FORM{'_cfg'} = &glib_cgi_04::param('_cfg');
    if ($FORM{'_cfg'} !~ /^(id|art|port|var|bd|usr|tax|coment|buscador|tag|list)$/) {
        &glib_html_02::print_json_result(0, 'Tipo de CFG inválido.', 'exit=1,ctype=1');
    };

    my @campos = &glib_cgi_04::param();

    my $msg;
    my $buffer;

    my %hash_vars = %{ $hash_defaultvars{$FORM{'_cfg'}} };

    foreach my $var_valida (keys %hash_vars) {
        my @var_info = split(/;/, $hash_vars{$var_valida});
        if (&glib_cgi_04::param($var_valida)) {
            # El input es una variable de configuracion valida.
            my $re = qr/$var_info[1]/;
            my $input_value = &glib_cgi_04::param($var_valida);
            if ($input_value ne '') {
                if ($var_info[3] eq 'M') { # Los valores del input vienen separados por |, son multiples.
                    # Validar cada valor.
                    my @input_value_array = split(/\|/, $input_value);
                    if ((scalar @input_value_array) gt 0) {
                        foreach my $item (@input_value_array) {
                            if ($item !~ /$re/) {
                                &glib_html_02::print_json_result(0, 'La variable ' . $var_valida . ' tiene caracteres inválidos.', 'exit=1,ctype=1');
                            } else {
                                &validarArt($item) if ($FORM{'_cfg'} eq 'art');
                                &validarPort($var_valida, $item) if ($FORM{'_cfg'} eq 'port');
                                &validarVar($var_valida, $item) if ($FORM{'_cfg'} eq 'var');
                                # Concideracion especial para el buscador.... ya que los valores van sin ''.
                                if ($FORM{'_cfg'} eq 'buscador') {
                                    $buffer = $buffer . "$var_valida = $item\n";
                                } else {
                                    # Si la variable es multivista, no guardar vacia.
                                    if ($var_valida eq 'MULTIVISTA') {
                                        if ($item ne '') {
                                            $buffer = $buffer . "$var_valida = '$item'\n";
                                        };
                                    } else {
                                        # Seguir curso normal.
                                        $buffer = $buffer . "$var_valida = '$item'\n";
                                    };
                                };
                            };
                        };
                    } else {
                        # No viene nada, tomar valor por defecto.
                        # Concideracion especial para el buscador.... ya que los valores van sin ''.
                        if ($FORM{'_cfg'} eq 'buscador') {
                            $buffer = $buffer . "$var_valida = $var_info[2]\n";
                        } else {
                            # Si la variable es multivista, no guardar vacia.
                            if ($var_valida eq 'MULTIVISTA') {
                                if ($var_info[2] ne '') {
                                    $buffer = $buffer . "$var_valida = '$var_info[2]'\n";
                                };
                            } else {
                                # Seguir curso normal.
                                $buffer = $buffer . "$var_valida = '$var_info[2]'\n";
                            };
                        };
                    };
                } elsif ($var_info[3] eq 'U') { # Es un solo valor.
                    if ($input_value !~ /$re/) {
                        &glib_html_02::print_json_result(0, 'La variable ' . $var_valida . ' tiene caracteres inválidos.', 'exit=1,ctype=1');
                    } else {
                        &validarPort($var_valida, $input_value) if ($FORM{'_cfg'} eq 'port');
                        &validarTax($var_valida, $input_value) if ($FORM{'_cfg'} eq 'tax');
                        &validarVar($var_valida, $input_value) if ($FORM{'_cfg'} eq 'var');

                        if ($FORM{'_cfg'} eq 'var' && $var_valida eq 'UPLOADS_PERMITIDOS') {
                            # Quitar espacios.
                            $input_value =~ s/, /,/ig
                        };

                        if ($FORM{'_cfg'} eq 'var' && $var_valida eq 'POST_PROCESO') {
                            # Quitar espacios.
                            $input_value = "ART-BORRAR($input_value)";
                        };

                        # Concideracion especial para el buscador.... ya que los valores van sin ''.
                        if ($FORM{'_cfg'} eq 'buscador') {
                            $buffer = $buffer . "$var_valida = $input_value\n";
                        } else {
                            # Si la variable es multivista, no guardar vacia.
                            if ($var_valida eq 'MULTIVISTA') {
                                if ($input_value ne '') {
                                    $buffer = $buffer . "$var_valida = '$input_value'\n";
                                };
                            } else {
                                # Seguir curso normal.
                                $buffer = $buffer . "$var_valida = '$input_value'\n";
                            };
                        };

                    };
                };
            } else {
                # Validar vacios.
                # Si el input esta vacio, tomar valor por defecto.
                # Concideracion especial para el buscador.... ya que los valores van sin ''.
                if ($FORM{'_cfg'} eq 'buscador') {
                    &validarSearch($var_valida);
                    $buffer = $buffer . "$var_valida = $var_info[2]\n";
                } else {
                    # Si la variable es multivista, no guardar vacia.
                    if ($var_valida eq 'MULTIVISTA') {
                        if ($var_info[2] ne '') {
                            $buffer = $buffer . "$var_valida = '$var_info[2]'\n";
                        };
                    } else {
                        # Seguir curso normal.
                        $buffer = $buffer . "$var_valida = '$var_info[2]'\n";
                    };
                };
            };
        } else {
            # El campo no viene, guardarlo con el valor por default.
            # Concideracion especial para el buscador.... ya que los valores van sin ''.
            if ($FORM{'_cfg'} eq 'buscador') {
                &validarSearch($var_valida);
                $buffer = $buffer . "$var_valida = $var_info[2]\n";
            } else {
                # $buffer = $buffer . "$var_valida = '$var_info[2]'\n";
                my $utf8_value = $var_info[2];
                utf8::encode($utf8_value); # en caso de que los valores por defecto contenga tildes

                # Si la variable es multivista, no guardar vacia.
                if ($var_valida eq 'MULTIVISTA') {
                    if ($var_info[2] ne '') {
                        $buffer = $buffer . "$var_valida = '$utf8_value'\n";
                    };
                } else {
                    # Seguir curso normal.
                    $buffer = $buffer . "$var_valida = '$utf8_value'\n";
                };
            };
        };
    };

    # Si el cfg es coment, hay que agregar algo especial.
    if ($FORM{'_cfg'} eq 'coment') {
        $buffer = "[articulo]\n" . $buffer . "[/articulo]\n";
    };

    # Para el caso del cfg 'art', es necesario reordenar la lista, para dejar primero el fid por defecto. (radio)
    if ($FORM{'_cfg'} eq 'art') {
        my $fid_default = &glib_cgi_04::param('form_plts_ini');
        my $first_fid = '';
        if ($buffer =~ /($fid_default):(.*?)\((.*?)\)/) {
            $first_fid = "FORM_PLTS = '$1:$2($3)'";
        };
        my @buff_split = split(/\n/, $buffer);
        my $new_buffer = "$first_fid\n";
        foreach my $buffer_line (@buff_split) {
            if ($buffer_line ne $first_fid) {
                $new_buffer = $new_buffer . $buffer_line . "\n";
            };
        };
        $buffer = $new_buffer;
    };

    #print STDERR $buffer;

    # Validaciones antes de guardar.
    &validarArtEliminacion() if ($FORM{'_cfg'} eq 'art');
    &probarConexionBD() if ($FORM{'_cfg'} eq 'bd');

    # Guardar CFG.
    &guardarCFG($FORM{'_path_conf'}, $FORM{'_cfg'}, $buffer);

    # Borra cache de no publicados
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");

    &glib_html_02::print_json_result(1, 'La configuración se guardó con éxito.', 'exit=1,ctype=1');

};

sub guardarCFG {
    my ($path_conf) = shift;
    my ($cfg) = shift;
    my ($buffer) = shift;

    #$cfg = $cfg . "-TST";

    my ($nomcfg);
    if ($path_conf =~ /(.*)\.cfg$/) {
        $nomcfg = $1;
    };

    # Verificar que exista el archivo.
    #my $errcfg;
    #$errcfg = "[$nomcfg-$cfg.cfg]" if (! -f  $prontus_varglb::DIR_SERVER . $nomcfg . '-' . $cfg . '.cfg');
    #if ($errcfg) {
    #    &glib_html_02::print_json_result(0, "No se pudo localizar el Archivo de Configuración PRONTUS $errcfg", 'exit=1,ctype=1');
    #};

    $nomcfg = $nomcfg . '-' . $cfg . '.cfg';

    # Concideracion especial para el buscador.
    if ($cfg eq 'buscador') {
        $nomcfg = '/' . $prontus_varglb::PRONTUS_ID . '/cpan/buscador_prontus.cfg';
    };

    # Guardar respaldo del archivo.
    my $dir_backup = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/cpan/_unused';
    &glib_fildir_02::check_dir($dir_backup);

    #print STDERR "Copia: $prontus_varglb::DIR_SERVER$nomcfg => $dir_backup/$prontus_varglb::PRONTUS_ID-$cfg.bak\n";
    &File::Copy::copy("$prontus_varglb::DIR_SERVER$nomcfg", "$dir_backup/$prontus_varglb::PRONTUS_ID-$cfg.bak");

    # Armar buffer a guardar.
    my ($last_buffer);
    $last_buffer = "[MODIFICADO EN GUI - " . &glib_hrfec_02::get_dtime_pack4() . "]\n\n";
    $last_buffer = $last_buffer . $buffer;

    # Escribir archivo.
    &glib_fildir_02::write_file($prontus_varglb::DIR_SERVER . $nomcfg, $last_buffer);

};

sub validarTax {
    my ($var) = shift;
    my ($item) = shift;

    if ($var eq 'TAXPORT_MAXARTICS') {
        if ($item > $prontus_varglb::TAXPORT_MAXARTICS_SECURITY) {
            &glib_html_02::print_json_result(0, "La variable $var no puede superar los $prontus_varglb::TAXPORT_MAXARTICS_SECURITY artículos.", 'exit=1,ctype=1');
        };
    };

};

sub validarSearch { # solo vacios.
    my ($var) = shift;
    print STDERR "var[$var]\n";
    if ($var eq 'FIDS') {
        &glib_html_02::print_json_result(0, "La variable $var debe tener seleccionado al menos 1 FID.", 'exit=1,ctype=1');
    }
};

sub validarVar {
    my ($var) = shift;
    my ($item) = shift;

    if ($var eq 'POST_PROCESO') {
        if ( ($item =~ /^\w/) || ($item =~ /^\.\.(\/|\\)\w/) ) {
            # Verificar que exista archivo.
            if (! -f $Bin .'/'. $item) {
                &glib_html_02::print_json_result(0, "El archivo [$Bin/$item] del Post Proceso no existe.", 'exit=1,ctype=1');
            };
        } else {
            &glib_html_02::print_json_result(0, "El Post proceso debe ubicarse en el mismo directorio de cgis de prontus o como máximo un nivel hacia arriba.\nPor ejemplo: pproc/prontus_pdel_artic.cgi", 'exit=1,ctype=1');
        };
    };

    # Validar existencia directorio de FFMPEG. (DIR_FFMPEG)
    if ($var eq 'DIR_FFMPEG') {
        if (! -d $item) {
            &glib_html_02::print_json_result(0, "Para la variable DIR_FFMPEG, el directorio [$item] no existe.", 'exit=1,ctype=1');
        };
    };

    # Validar existencia de script para cuota
    if ($var eq 'SCRIPT_QUOTA') {
        if (!-e $prontus_varglb::DIR_SERVER . $item) {
            &glib_html_02::print_json_result(0, "No existe el script [$item] definido en la variable SCRIPT_QUOTA.", 'exit=1,ctype=1');
        };
    };

    # El formato debe ser wXh
    if ($var eq 'FOTO_MAX_PIXEL') {
        if ($item !~ /^\d+x\d+$/) {
            &glib_html_02::print_json_result(0, "La variable FOTO_MAX_PIXEL tiene datos inválidos. El valor debe ser, por ejemplo: 1920x1080", 'exit=1,ctype=1');
        };
    };

    # Los parámetros no pueden tener " o '
    if ($var eq 'FFMPEG_PARAMS') {
        if ($item =~ /["|']/) {
            &glib_html_02::print_json_result(0, "La variable FFMPEG_PARAMS tiene datos inválidos. No puede contener caracteres como \" o '.", 'exit=1,ctype=1');
        };
    };

};

sub validarArt {
    my ($item) = shift;

    # validar existencia de fids y plantillas.
    $item =~ /(.*?):(.*?)\((.*?)\)/;

    my $dir_fid = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/cpan/fid/';
    if (! -f $dir_fid . $1 . '.html') {
        &glib_html_02::print_json_result(0, "No se pudo localizar el FID [$prontus_varglb::PRONTUS_ID/cpan/fid/$1.html].", 'exit=1,ctype=1');
    };

    # Validar que venga el nombre del FID.
    if ($2 eq '') {
        &glib_html_02::print_json_result(0, "Debe ingresar el Nombre para el FID [$1].", 'exit=1,ctype=1');
    };

    # Validar que vengan alguna plantilla.
    if ($3 eq '') {
        &glib_html_02::print_json_result(0, "Debe seleccionar al menos una plantilla para el FID [$1].", 'exit=1,ctype=1');
    };

    my $dir_plantilla = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/plantillas/artic/fecha/pags/';
    my @plantillas = split(/;/, $3);
    foreach my $plt (@plantillas) {
        if (! -f $dir_plantilla . $plt) {
            &glib_html_02::print_json_result(0, "No se pudo localizar la Plantilla de Artículo [$prontus_varglb::PRONTUS_ID/plantillas/artic/fecha/pags/$plt]", 'exit=1,ctype=1');
        };
    };

};

sub validarArtEliminacion {
    # No se puede quitar un FID que tenga artículos asociados.

    my @quitar = &glib_cgi_04::param('quitar[]');
    my $base;

    # Conectar a BD si es que no viene la conexion
    if (! ref($base)) {
        # print STDERR "connect a BD dentro\n";
        my $msg_err_bd;
        ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
        if (! ref($base)) {
            &glib_html_02::print_json_result(0, "ERROR: $msg_err_bd\n", 'exit=1,ctype=1');
            exit;
        };
    };

    my $msgerr = '';

    foreach my $fid (@quitar) {
        if ($fid ne '') {
            my $sql = "SELECT COUNT(*) as EXISTE FROM ART WHERE ART_TIPOFICHA = '$fid'";
            my $existe;
            my $salida = &glib_dbi_02::ejecutar_sql($base, $sql);
            $salida->bind_columns(undef, \($existe));
            $salida->fetch;
            $salida->finish;
            if ($existe gt 0) {
                $msgerr = $msgerr . "El FID [$fid] no se puede quitar, porque está siendo utilizado por $existe artículos.\n";
            };
        };
    };

    if ($msgerr ne '') {
        &glib_html_02::print_json_result(0, $msgerr, 'exit=1,ctype=1');
    };

};

sub probarConexionBD {
    # Probar conexion a la BD con los datos ingresados por el usuario.
    my $USER_BD = &glib_cgi_04::param('USER_BD');
    my $MOTOR_BD = &glib_cgi_04::param('USER_BD');
    my $NOM_BD = &glib_cgi_04::param('NOM_BD');
    my $SERVER_BD = &glib_cgi_04::param('SERVER_BD');
    my $PWD_BD = &glib_cgi_04::param('PWD_BD');

    my $msg_ret = '';
    my $base = DBI->connect("DBI:mysql:$NOM_BD:$SERVER_BD", $USER_BD, $PWD_BD, {'PrintError'=>1})
            || warn "DBI Error Code: [$DBI::err][$DBI::errstr] ";

    if ($DBI::err) {
        $msg_ret = "No fue posible conectar con base de datos Prontus MySQL, utilizando los datos ingresados.\nOcurrió el siguiente error:\n\n";
        $msg_ret .= "Cod[$DBI::err][$DBI::errstr]\n";
        &glib_html_02::print_json_result(0, $msg_ret, 'exit=1,ctype=1');
    };

};

sub validarPort {
    my ($var) = shift;
    my ($item) = shift;

    my $dir_portada = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/plantillas/edic/nroedic/port/';
    my $dir_portada_site = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/site/edic/base/port/';

    if ($var eq 'PORT_PLTS') {
        my ($item1, $item3, $item4) = '';

        if ($item =~ /(.*?)\((.*?)\)\((.*?)\)\((.*?)\)/) {
           $item1 = $1;
           $item3 = $3;
           $item4 = $4;
        };

        if ($item1 ne '') {
            if (! -f $dir_portada . $item1) {
                &glib_html_02::print_json_result(0, "No se pudo localizar la Plantilla de Portada [$prontus_varglb::PRONTUS_ID/plantillas/edic/nroedic/$item1]", 'exit=1,ctype=1');
            };
        };

        # validar portadas paralelas.
        if ($item3 ne '') {
            my @paralelas = split(/;/, $item3);
            foreach my $var (@paralelas) {
                if (! -f $dir_portada . $var) {
                    &glib_html_02::print_json_result(0, "No se pudo localizar la Plantilla de Portada Paralela [$prontus_varglb::PRONTUS_ID/plantillas/edic/nroedic/$item3]", 'exit=1,ctype=1');
                };
            };
        };

        # validar portadas de preview.
        my $dir_preview = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/stat/preview_containers/';
        if ($item4 ne '') {
            if (! -f $dir_preview . $item4) {
                &glib_html_02::print_json_result(0, "No se pudo localizar la Plantilla de Portada de Preview [$prontus_varglb::PRONTUS_ID/stat/preview_containers/$item4]", 'exit=1,ctype=1');
            };
        };
    } elsif ($var eq 'PORT_INI_SELECTED') {
        if (! -f $dir_portada . $item) {
            &glib_html_02::print_json_result(0, "No se pudo localizar la Plantilla de Portada que aparecerá seleccionada [$prontus_varglb::PRONTUS_ID/plantillas/edic/nroedic/port/$item]", 'exit=1,ctype=1');
        };
    } elsif ($var eq 'BASE_PORTS') {
        if (! -f $dir_portada . $item) {
            &glib_html_02::print_json_result(0, "No se pudo localizar la Plantilla de Portada que se utilizará en edición base [$prontus_varglb::PRONTUS_ID/plantillas/edic/nroedic/port/$item]", 'exit=1,ctype=1');
        };
    } elsif ($var eq 'PORT_HOME') {

        #~ print STDERR "item[$item]\n";

        if (! -f $dir_portada_site . $item) {
            &glib_html_02::print_json_result(0, "No se pudo localizar la portada que se utilizará como página de inicio [$prontus_varglb::PRONTUS_ID/site/edic/base/port/$item]", 'exit=1,ctype=1');
        } else {
            # Crear link simbólico hacia la portada.
            my $path_home_index = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/site/edic/base/home/index.html';
            my $cmd = "ln -s $dir_portada_site$item $path_home_index";

            if (-f $path_home_index && -l $path_home_index) {
                unlink $path_home_index;
            };

            #~ print STDERR "cmd[$cmd]\n";
            system $cmd;
        };
    };

};
