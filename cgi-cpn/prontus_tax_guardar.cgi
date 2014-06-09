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
# prontus_secc_guardar.cgi.
#
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /prontus/.
#
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Mantencion Secciones. Crea, actualiza y/o elimina.
#
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------------
# Location: prontus_secc_admin.cgi (Administrador de Secciones).
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde pagina 'Administrador de Secciones' (/prontus4_nots/cpan/core/mant_seccs/prontus_secc_admin.html) boton 'Guardar'.
#
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# Plantillas: /prontus4_nots/cpan/core/mant_seccs/mensajes.html (para mensajes de error).
#
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# Paginas web: No registra.
#
# ---------------------------------------------------------------
# Tablas.
# -------------------
# SECC - TEMAS - SUBTEMAS.
# ---------------------------------------------------------------


# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 16/10/2003 - YCH - Primera version.
# ---------------------------------------------------------------


# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use DBI;

use prontus_varglb; &prontus_varglb::init();
use glib_dbi_02;
use glib_html_02;
use glib_cgi_04;
use glib_str_02;
use lib_secc;

use lib_prontus;
use strict;



# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM, $BD);


my %DATA_VISTAS;

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

    # Acceso permitido solo para admin o editor
    if ($prontus_varglb::USERS_PERFIL eq 'P') {
      &glib_html_02::print_pag_result('Acceso a Area Restringida','La funcionalidad requerida no está disponible para perfil Redactor',1,'exit=1,ctype=1');
    };

    $FORM{'_entidad'} = &glib_cgi_04::param('_entidad');
    $FORM{'_entidad'} = 'seccion' if ($FORM{'_entidad'} eq '');
    if ($FORM{'_entidad'} !~ /^(seccion|tema|subtema)$/) {
        &glib_html_02::print_json_result(0, 'Tipo de entidad no es válida', 'exit=1,ctype=1');
    };

    if ($FORM{'_entidad'} eq 'tema') {
        $FORM{'_secc_id'} = &glib_cgi_04::param('_secc_id');
        if ($FORM{'_secc_id'} !~ /^[0-9]+$/) {
            &glib_html_02::print_json_result(0, 'Sección no es válida', 'exit=1,ctype=1');
        };
    };

    if ($FORM{'_entidad'} eq 'subtema') {
        $FORM{'_tema_id'} = &glib_cgi_04::param('_tema_id');
        if ($FORM{'_tema_id'} !~ /^[0-9]+$/) {
            &glib_html_02::print_json_result(0, 'Tema no es válido', 'exit=1,ctype=1');
        };
    };


    $FORM{'_id'}= &glib_cgi_04::param('_id');
    if ($FORM{'_id'} ne '') {
        if (($FORM{'_id'} !~ /^[0-9]+$/) || (!$FORM{'_id'})) {
            &glib_html_02::print_json_result(0, 'Id no válido', 'exit=1,ctype=1');
        };
    };

    $FORM{'_nom'} = &glib_str_02::trim(&glib_cgi_04::param('_nom'));
    $FORM{'_nom'} = &lib_prontus::despulga_item_tax($FORM{'_nom'});
    if ($FORM{'_nom'} eq '') {
        &glib_html_02::print_json_result(0, 'Por favor, ingresa el nombre del ítem', 'exit=1,ctype=1');
    };
    $FORM{'_port'}= &glib_str_02::trim(&glib_cgi_04::param('_port'));
    $FORM{'_port'} = &lib_prontus::despulga_item_tax($FORM{'_port'});

    # Conectar a BD
    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &glib_html_02::print_json_result(0, $msg_err_bd, 'exit=1,ctype=1');
    };

    my $new_id;
    my $msg;
    if ($FORM{'_id'}) {
        $msg = &do_update();
    } else {
        ($msg, $new_id) = &do_insert();
    };
    &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1') if ($msg);

    # &actualiza_xml_vistas($new_id);

    &lib_prontus::make_mapa('', $BD);

    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        &lib_prontus::make_mapa($mv, $BD);
    };

    # Genera tax en arch. JS, para ser incluido en FIDs
    my $arr_tst = &lib_secc::genera_array_temas_subtemas($BD, '', 'solo habilitadas');
    my $dir_tax4fids = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CPAN . '/procs/tax4fids';
    &glib_fildir_02::check_dir($dir_tax4fids);
    &glib_fildir_02::write_file($dir_tax4fids . '/tax4fids.js', $arr_tst);

    $BD->disconnect;

    &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');

}; # main.

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------



#sub actualiza_xml_vistas {
## Actualiza xml que contienen los nombres de la seccion (tema o subtema, segun corresponda) en cada vista.
## Los XML son:
#
## Seccion:
## prontus_toolbox\cpan\data\tax_multivista\$mv\seccion.xml
#
## Tema:
## prontus_toolbox\cpan\data\tax_multivista\$mv\tema-$idsecc.xml
#
## STema:
## prontus_toolbox\cpan\data\tax_multivista\$mv\subtema-$idtema.xml
#
#
#  my $saved_id = $_[0];
#
## para nuevo o update
#if ($saved_id) {
#    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
#      my $k = '_nom' . "-$mv"; # ej: _nom-pda
#      my $nom = &glib_cgi_04::param($k);
#      $nom = &lib_prontus::despulga_item_tax(&glib_str_02::trim($nom));
#      $nom = $FORM{'_nom'} if (!$nom);
#      $DATA_VISTAS{$mv} = "$saved_id\t$nom\n";
#    };
#};
#
#
#  # Recupera todos los demas items del XML respectivo
#  my $nom_xml;
#  $nom_xml = if ($FORM{'_entidad'} eq 'seccion')
#  my $path_xml_vista = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/tax_multivista/$mv/";
#
#
#
#
#
#  my ($id_item, $nom_item);
#  my $sql = "select SECC_ID, SECC_NOM from SECC where SECC_ID <> \"$saved_id\" order by SECC_NOM";
#
#my $sql;
#if ($FORM{'_entidad'} eq 'seccion') {
#    $sql = "select SECC_ID, SECC_NOM from SECC "
#         . "where SECC_ID <> \"$saved_id\" order by SECC_ORDEN";
#};
#if ($FORM{'_entidad'} eq 'tema') {
#    $sql = "select TEMAS_ID, TEMAS_NOM from TEMAS "
#         . "where TEMAS_IDSECC = $FORM{'_secc_id'} and where TEMAS_ID <> \"$saved_id\" order by TEMAS_ORDEN";
#};
#if ($FORM{'_entidad'} eq 'subtema') {
#    $sql = "select SUBTEMAS_ID, SUBTEMAS_NOM from SUBTEMAS "
#         . "where SUBTEMAS_IDTEMAS = $FORM{'_tema_id'} and where SUBTEMAS_ID <> \"$saved_id\" order by SUBTEMAS_ORDEN";
#};
#
#
#  my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id_item, $nom_item));
#  while($salida->fetch){
#    foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
#
#      my $k = '_nom' . $id_item . "-$mv";
#      my $nom = &glib_cgi_04::param($k);
#
#      # warn "nom[$nom] - k[$k]\n";
#      $nom = $FORM{'Txt_NOM' . $id_item} if (!$nom);
#      $DATA_VISTAS{$mv} .= "$id_item\t$nom\n";
#    };
#  };
#
#  # Dumpea los datos a los xml de cada vista
#  my $xml_buf = "<?xml version='1.0' encoding='utf-8'?>\n<ROTULOS>\n%%ITEMS%%</ROTULOS>";
#
#  foreach $mv (keys %DATA_VISTAS) {
#    my $items;
#    while ($DATA_VISTAS{$mv} =~ /(\d+)\t(.+?)\n/sg) {
#      ($id_item, $nom_item) = ($1, $2);
#
#      my $item = "<ITEM>\n<ID>$id_item</ID>\n<NOM>$nom_item</NOM>\n</ITEM>\n";
#      $items .= $item;
#    };
#    my $xml_out = $xml_buf;
#    $xml_out =~ s/%%ITEMS%%/$items/;
#    my $dir_xml_vista = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/tax_multivista/$mv";
#    &glib_fildir_02::check_dir($dir_xml_vista);
#    &glib_fildir_02::write_file($dir_xml_vista . '/seccion.xml', $xml_out);
#  };
#
#};
# ---------------------------------------------------------------
sub do_insert {

    # Comprobar si el nombre ya existe.
    my $msg = &tit_repetido(0, $FORM{'_nom'});
    return ($msg, 0) if ($msg ne '');
    my $nom4vistas = &get_nom4vistas();

    # Inserta registro en la tabla.
    my $nom_quoted = $BD->quote($FORM{'_nom'});
    my $port_quoted = $BD->quote($FORM{'_port'});

    if ($nom4vistas ne '') {
        $nom4vistas = $BD->quote($nom4vistas);
    } else {
        $nom4vistas = "''";
    };

    my $sql;
    $sql = "insert into SECC values(NULL, $nom_quoted, '1', $port_quoted, 1, $nom4vistas)" if ($FORM{'_entidad'} eq 'seccion');
    $sql = "insert into TEMAS values(NULL, $nom_quoted, $FORM{'_secc_id'}, '1', $port_quoted, 1, $nom4vistas)" if ($FORM{'_entidad'} eq 'tema');
    $sql = "insert into SUBTEMAS values(null, $nom_quoted, $FORM{'_tema_id'}, '1', $port_quoted, 1, $nom4vistas)" if ($FORM{'_entidad'} eq 'subtema');

    my $id = &lib_prontus::insert_dev_id($sql, $BD, $prontus_varglb::MOTOR_BD);
    return ('', $id);

};# guardar_new_entidad.

# ---------------------------------------------------------------
sub get_nom4vistas {
    my $nom4vistas;
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        my $k = '_nom' . "-$mv"; # ej: _nom-pda
        my $nom = &glib_cgi_04::param($k);
        $nom = &lib_prontus::despulga_item_tax(&glib_str_02::trim($nom));
        $nom = $FORM{'_nom'} if (!$nom);
        $nom4vistas .= "$mv\t$nom\n";
    };
    $nom4vistas =~ s/\n$//; # elimina \n sobrante
    return $nom4vistas;
};

# ---------------------------------------------------------------
sub tit_repetido {
  # Verifica que el nombre no exista en la tabla.
  my ($id_entidad, $nombre) = ($_[0], $_[1]);

  my $sql;
  $sql = "select SECC_ID from SECC where lower(SECC_NOM) = lower(\"$nombre\") and SECC_ID != $id_entidad" if ($FORM{'_entidad'} eq 'seccion');
  $sql = "select count(*) from TEMAS where lower(TEMAS_NOM) = lower(\"$nombre\") and TEMAS_ID != $id_entidad and TEMAS_IDSECC = $FORM{'_secc_id'}" if ($FORM{'_entidad'} eq 'tema');
  $sql = "select SUBTEMAS_ID from SUBTEMAS where lower(SUBTEMAS_NOM) = lower(\"$nombre\") and SUBTEMAS_ID != $id_entidad and SUBTEMAS_IDTEMAS = $FORM{'_tema_id'}" if ($FORM{'_entidad'} eq 'subtema');
  my $cant;
  my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \$cant);
  $salida->fetch;
  $salida->finish;

  if ($cant > 0){
    return 'Nombre de ítem ya existe.';
  };

  return '';
}; # tit_repetido.

# ---------------------------------------------------------------
sub do_update {
    # Comprobar si el nombre ya existe.
    my $msg = &tit_repetido($FORM{'_id'}, $FORM{'_nom'});
    return ($msg, 0) if ($msg ne '');

    my $nom4vistas = &get_nom4vistas();
    $nom4vistas = $BD->quote($nom4vistas);

    # Upd registro en la tabla.
    my $nom_quoted = $BD->quote($FORM{'_nom'});
    # my $nom_quoted = $FORM{'_nom'};
    my $port_quoted = $BD->quote($FORM{'_port'});
    my $sql;
    $sql = "update SECC set SECC_NOM = $nom_quoted, SECC_PORT = $port_quoted, SECC_NOM4VISTAS = $nom4vistas where SECC_ID = $FORM{'_id'}" if ($FORM{'_entidad'} eq 'seccion');
    $sql = "update TEMAS set TEMAS_NOM = $nom_quoted, TEMAS_PORT = $port_quoted, TEMAS_NOM4VISTAS = $nom4vistas where TEMAS_ID = $FORM{'_id'}" if ($FORM{'_entidad'} eq 'tema');
    $sql = "update SUBTEMAS set SUBTEMAS_NOM = $nom_quoted, SUBTEMAS_PORT = $port_quoted, SUBTEMAS_NOM4VISTAS = $nom4vistas where SUBTEMAS_ID = $FORM{'_id'}" if ($FORM{'_entidad'} eq 'subtema');
    # print STDERR "sql-u[$sql]\n";
    $BD->do($sql) || return &lib_prontus::handle_internal_error($BD->errstr, 'Error actualizando ítem en la base de datos', 'exit=0');
    return '';
};

# ---------------------------------------------------------------
#sub actualiza_entidad {
#  # Actualiza o elimina los datos ya existentes.
#  my (%datos) = &glib_cgi_04::param(); # Asigna todos los objetos a un hash.
#  my ($msg, $campo, $id_entidad, $borrar, $id_temas);
#  my ($sql, $salida);
#  my ($nombre);
#
#
#
#  # Busca todos los objetos para actualizar o eliminar.
#  foreach $campo (%datos) {
#    if ($campo =~ /^Txt_NOM(\d+)/) {
#      $id_entidad = $1;
#      $borrar = &glib_cgi_04::param("Chk_BOR$id_entidad");
#
#      $sql = "select SECC_NOM from SECC where SECC_ID = $id_entidad";
#      $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \$nombre);
#      $salida->fetch;
#      $salida->finish;
#
#      $FORM{'Chk_BOR' . $id_entidad} = &glib_cgi_04::param('Chk_BOR' . $id_entidad);
#      $FORM{'Chk_MOSTRAR' . $id_entidad} = &glib_cgi_04::param('Chk_MOSTRAR' . $id_entidad);
#      $FORM{'Txt_NOM' . $id_entidad} = &glib_str_02::trim(&glib_cgi_04::param('Txt_NOM' . $id_entidad));
#      $FORM{'Txt_NOM' . $id_entidad} = &lib_prontus::despulga_item_tax($FORM{'Txt_NOM' . $id_entidad});
#
#
#      $FORM{'Txt_PORT' . $id_entidad} = &glib_str_02::trim(&glib_cgi_04::param('Txt_PORT' . $id_entidad));
#      $FORM{'Txt_PORT' . $id_entidad} = &lib_prontus::despulga_item_tax($FORM{'Txt_PORT' . $id_entidad});
#
#      $FORM{'Txt_ORDEN' . $id_entidad} = &glib_str_02::trim(&glib_cgi_04::param('Txt_ORDEN' . $id_entidad));
#      $FORM{'Txt_ORDEN' . $id_entidad} =~ s/[^\d]//sig;
#
#      if ($borrar ne 'S') { # Si actualizar y no borrar.
#
#        # Verifica nombre.
#        if ($FORM{'Txt_NOM' . $id_entidad} eq '') {
#            print "Content-Type: text/html\n\n";
#            &lib_secc::print_pag_html($PLANTILLA_MSG, 'ERROR', 'Existe una fila que no tiene nombre digitado', 'pagina');
#            $BD->disconnect;
#            exit;
#        };
#
#        # Comprobar si el nombre ya existe.
#
#        # if ($nombre ne $FORM{'Txt_NOM' . $id_entidad}) {
#
#          $msg = &tit_repetido($id_entidad, $FORM{'Txt_NOM' . $id_entidad});
#          if ($msg ne '') {
#            print "Content-Type: text/html\n\n";
#            &lib_secc::print_pag_html($PLANTILLA_MSG, 'ERROR', 'Nombre de secci&oacute;  (' . $FORM{'Txt_NOM' . $id_entidad} . ') ya existe en otra fila', 'pagina');
#            $BD->disconnect;
#            exit;
#          };
#
#          my $nom_quoted = $BD->quote($FORM{'Txt_NOM' . $id_entidad});
#          my $port_quoted = $BD->quote($FORM{'Txt_PORT' . $id_entidad});
#
#          # $sql = "update SECC set SECC_NOM = \"$FORM{'Txt_NOM' . $id_entidad}\", SECC_MOSTRAR = \"$FORM{'Chk_MOSTRAR' . $id_entidad}\", SECC_PORT = \"$FORM{'Txt_PORT' . $id_entidad}\", SECC_ORDEN = \"$FORM{'Txt_ORDEN' . $id_entidad}\" where SECC_ID = $id_entidad";
#          $sql = "update SECC set SECC_NOM = $nom_quoted, SECC_MOSTRAR = \"$FORM{'Chk_MOSTRAR' . $id_entidad}\", SECC_PORT = $port_quoted, SECC_ORDEN = \"$FORM{'Txt_ORDEN' . $id_entidad}\" where SECC_ID = $id_entidad";
#          $BD->do($sql) || print STDERR $BD->errstr;
#
#
#        # };
#      } # Si borrar.
#      else { # Entonces borrar.
#        # Si el item no se puede borrar por estar siendo utilizado, entonces mensajear.
#        if (! &no_referenciada($id_entidad)) {
#          print "Content-Type: text/html\n\n";
#          &lib_secc::print_pag_html($PLANTILLA_MSG, 'ERROR', "<b>$FORM{'Txt_NOM' . $id_entidad}</b>: Item está siendo utilizado en algún artículo. No se puede borrar.", 'pagina');
#          $BD->disconnect;
#          exit;
#        };
#
#        # Selecciona todos los temas de la seccion a eliminar.
#        $sql = "select TEMAS_ID from TEMAS where TEMAS_IDSECC = $id_entidad";
#        $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \$id_temas);
#
#        while ($salida->fetch) {
#          # Elimina subtema.
#          $sql = " delete from SUBTEMAS where SUBTEMAS_IDTEMAS = $id_temas";
#          $BD->do($sql) || print STDERR $BD->errstr;
#        };
#
#        $salida->finish;
#
#        # Elimina Temas.
#        $sql = " delete from TEMAS where TEMAS_IDSECC = $id_entidad";
#        $BD->do($sql) || print STDERR $BD->errstr;
#
#        # Elimina Secc.
#        $sql = " delete from SECC where SECC_ID = $id_entidad";
#        $BD->do($sql) || print STDERR $BD->errstr;
#
#      }; # if Borrar
#    }; # $campo =~ /Chk.
#  }; # foreach.
#}; # actualiza_entidad.
#
## ---------------------------------------------------------------
#sub no_referenciada {
#
#  # Verifica que el registro actual no este referenciado en alguna de las tablas principales correspondientes.
#  my ($id) = $_[0];
#  my ($sql, $salida, $id_ref);
#
#  $sql = "select ART_ID from ART where ART_IDSECC1 = $id or ART_IDSECC2 = $id or ART_IDSECC3 = $id";
#  # print STDERR "sql SECC NOREF[$sql]\n\n";
#  $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \$id_ref);
#  $salida->fetch;
#  if ($salida->rows <= 0) {
#    return 1; # No referenciada.
#  };
#
#  return 0; # Referenciada.
#}; # no_referenciada.

# ----------------------------END SCRIPT---------------------
