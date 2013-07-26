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
# prontus_secc_admin.pl.
#
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /prontus/.
#
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Administrador de Secciones de noticias.
#
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------------
# prontus_temas_admin.pl (link Ver en columna Temas).
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde /prontus4_nots/cpan/core/prontus_menu.html
#
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# Plantillas:
#   /prontus4_nots/cpan/core/mant_seccs/prontus_secc_admin.html.
#   /prontus4_nots/cpan/core/mant_seccs/mensajes.html (para mensajes de error).
#
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# Paginas web: No registra. El resultado se imprime directamente hacia el browser.
#
# ---------------------------------------------------------------
# Tablas.
# -------------------
# SECC - # PERSEMP.
# ---------------------------------------------------------------


# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 16/10/2003 - YCH - Primera version.
# 1.1 - 16/10/2007 - YCH - Elimina link mapa del sitio (segun instruccion de ald).
# ---------------------------------------------------------------


# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------

BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

use DBI;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_dbi_02;
use glib_fildir_02;

use lib_prontus;
use strict;
use glib_cgi_04;
use lib_secc;

$| = 1; # Sin buffer. Despliega a medida que va leyendo.

# ---------------------------------------------------------------
# MAIN.
# -------------

my ($BD, %FORM,);
my (%XML_VISTAS, %HASH_FS_TAX);

main:{


    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});


    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    $FORM{'_entidad'} = &glib_cgi_04::param('_entidad');
    $FORM{'_entidad'} = 'seccion' if ($FORM{'_entidad'} eq '');
    if ($FORM{'_entidad'} !~ /^(seccion|tema|subtema)$/) {
        &glib_html_02::print_json_result(0, 'Tipo de entidad no es válida', 'exit=1,ctype=1');
    };


    # Para "guardar y nuevo"
    $FORM{'_newitem'} = &glib_cgi_04::param('_newitem');
    if ($FORM{'_newitem'} !~ /^[01]?$/) {
        &glib_html_02::print_json_result(0, 'Indicador para [guardar y nuevo] no es válido', 'exit=1,ctype=1');
    };


#    $FORM{'_secc_id'} = &glib_cgi_04::param('_secc_id');
#    if ($FORM{'_secc_id'} !~ /^[0-9]+$/) {
#        &glib_html_02::print_json_result(0, 'Sección no es válida', 'exit=1,ctype=1');
#    };


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

    # Control de usuarios obligatorio
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(0);

    if ($prontus_varglb::USERS_ID eq '') {
        if ($FORM{'_entidad'} eq 'tema' || $FORM{'_entidad'} eq 'subtema') {
            print "Content-Type: text/html\n\n";
            print "No se detect&oacute; una sesi&oacute;n activa.\n\n";
            exit;
        } else {
            print "Location: /$prontus_varglb::PRONTUS_ID/cpan/core/prontus_index.html\n\n";
            exit;
        };
    };

    # Acceso permitido solo para admin o editor
    if ($prontus_varglb::USERS_PERFIL eq 'P') {
      &glib_html_02::print_pag_result('Acceso a Area Restringida','La funcionalidad requerida no está disponible para perfil Redactor',1,'exit=1,ctype=1');
    };

    print "Content-Type: text/html\n\n";

    # Conectar a BD
    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &glib_html_02::print_pag_result("Error",$msg_err_bd,1,'exit=1');
    };

    # Ver si existe col *_NOM4VISTAS y si no, crearla. (compatib 10.15 a 11.0)
    &check_col('SECC', 'SECC_NOM4VISTAS', "text");
    &check_col('TEMAS', 'TEMAS_NOM4VISTAS', "text");
    &check_col('SUBTEMAS', 'SUBTEMAS_NOM4VISTAS', "text");

    # Carga la plantilla
    my $pagina = &glib_fildir_02::read_file($prontus_varglb::DIR_SERVER . "$prontus_varglb::RELDIR_BASE/$prontus_varglb::PRONTUS_ID/cpan/core/mant_seccs/prontus_" . $FORM{'_entidad'} . "_admin.html");

    $pagina = &lib_prontus::set_coreplt_ppal($pagina);

    # !!!!
    # &load_data_multivistas($FORM{'_entidad'});

   %HASH_FS_TAX = &cache_dirs_tax($FORM{'_entidad'});

    my $sql;
    $sql = "select SECC_ID, SECC_NOM, SECC_MOSTRAR, SECC_PORT, SECC_ORDEN, SECC_NOM4VISTAS  from SECC order by SECC_ORDEN ASC, SECC_ID ASC" if ($FORM{'_entidad'} eq 'seccion');
    $sql = "select TEMAS_ID, TEMAS_NOM, TEMAS_MOSTRAR, TEMAS_PORT, TEMAS_ORDEN, TEMAS_NOM4VISTAS from TEMAS where TEMAS_IDSECC = $FORM{'_secc_id'} order by TEMAS_ORDEN ASC, TEMAS_ID ASC" if ($FORM{'_entidad'} eq 'tema');
    $sql = "select SUBTEMAS_ID, SUBTEMAS_NOM, SUBTEMAS_MOSTRAR, SUBTEMAS_PORT, SUBTEMAS_ORDEN, SUBTEMAS_NOM4VISTAS from SUBTEMAS where SUBTEMAS_IDTEMAS = $FORM{'_tema_id'} order by SUBTEMAS_ORDEN ASC, SUBTEMAS_ID ASC" if ($FORM{'_entidad'} eq 'subtema');

    $pagina =~ /<!--item_loop-->(.*)<!--\/item_loop-->/is;
    my $loop = $1;

    my $lista = &make_lista($sql, $loop);
    $pagina =~ s/<!--item_loop-->.*<!--\/item_loop-->/$lista/s;

    $pagina = &parse_multivistas($pagina, '', 'vista_loop_new');
    $pagina = &parse_multivistas($pagina, '', 'vista_loop_edit');

    $BD->disconnect;

    $pagina =~ s/%%_path_conf%%/$FORM{'_path_conf'}/ig;
    $pagina =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/isg;

    $pagina =~ s/%%_secc_id%%/$FORM{'_secc_id'}/isg;
    $pagina =~ s/%%_tema_id%%/$FORM{'_tema_id'}/isg;
    $pagina =~ s/%%_newitem%%/$FORM{'_newitem'}/isg;


    print $pagina;
}; # main

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
# rotulos tax
#sub load_data_multivistas {
#    my $tipo = shift;
#    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
#        # r:\prontus_development\web\prontus_toolbox\cpan\data\tax_multivista\pda\seccion.xml
#        my $path_xml_vista = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/tax_multivista/$mv/$tipo.xml";
#        $XML_VISTAS{$mv} = &glib_fildir_02::read_file($path_xml_vista);
#
#    };
#};
# ---------------------------------------------------------------
sub check_col {
    my ($tabla, $colname, $coldef) = @_;
    my $res_check_col = &glib_dbi_02::check_table_column($BD, $tabla, $colname, $coldef);
    &glib_html_02::print_pag_result("Error","No se pudo crear la columna $colname",1,'exit=1') if (!$res_check_col);
};
# ---------------------------------------------------------------
# rotulos tax
sub parse_multivistas {
    my ($fila, $nom4vistas, $nom_loop) = @_;

    # nom4vistas --> $mv\t$nom\n$mv\t$nom\n$mv\t$nom

    my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d| |\s/;
    my $mv;
    $fila =~ /<!--$nom_loop-->(.*?)<!--\/$nom_loop-->/s;
    my $loop_mv = $1;
    my $loops;
    my $hide = ' style="display: none;"';
    my $count = 0;
    foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
        # parsea nombre de la vista
        my $loop = $loop_mv;
        $loop =~ s/%%_nom_vista%%/$mv/g;

        # Parsea nombre de la categ, para esta vista
        my $nom = &lib_prontus::get_nomtax_envista($mv, $nom4vistas);
        $nom = &lib_prontus::escape_html($nom);

        $loop =~ s/%%_nom_item_vista%%/$nom/g;
        if ($count > 0) {
            $loop =~ s/%%_vista_style%%/$hide/g;
        } else {
            $loop =~ s/%%_vista_style%%//g;
        }
        $count++;
        $loops .= $loop;
    };
    if ($count == 1) {
        $fila =~ s/<!--vista_flechas-->.*?<!--\/vista_flechas-->//sg;
    }
    $fila =~ s/<!--$nom_loop-->.*?<!--\/$nom_loop-->/$loops/sg;
    return $fila;
};
# ---------------------------------------------------------------
sub make_lista {
    # Genera y retorna las filas de la tabla.
    my ($sentencia) = shift;
    my ($loop) = shift;


    my ($id, $nom, $mostrar, $port, $orden, $num_subniveles, $nom4vistas);
    my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sentencia, \($id, $nom, $mostrar, $port, $orden, $nom4vistas));
    my ($filas);
    while($salida->fetch){
        my $sql_count;
        $sql_count = "select count(TEMAS_ID) from TEMAS where TEMAS_IDSECC = $id" if ($FORM{'_entidad'} eq 'seccion');
        $sql_count = "select count(SUBTEMAS_ID) from SUBTEMAS where SUBTEMAS_IDTEMAS = $id" if ($FORM{'_entidad'} eq 'tema');
        $num_subniveles = &lib_prontus::existe_registro($sql_count, $BD) if ($sql_count);
        $nom = &lib_prontus::escape_html($nom);
        $port = &lib_prontus::escape_html($port) if ($port ne '');
        my $taxports;
        $taxports = &get_url_taxports($id, $FORM{'_entidad'}) if ($port eq '');
        $filas .= &generar_fila($loop, $id, $nom, $mostrar, $port, $orden, $num_subniveles, $nom4vistas, $taxports);
    };

    $salida->finish;

    return $filas;
};
# ---------------------------------------------------------------
#sub get_url_taxports {
## /<prontus_dir>/site/tax/port/(all|<fid>)[-<vista>]/taxport_<s>_<t>_<st>_<nropag>.<ext>
    #my ($id, $entidad) = @_;
    #my ($reldir_port_dst) = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_PTEMA"; # /<prontus_dir>/site/tax/port

    #my @lisdir = &glib_fildir_02::lee_dir("$prontus_varglb::DIR_SERVER$reldir_port_dst");
    #@lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..


    #my $urls;
    #foreach my $subdir (@lisdir) {
        #next if (!-d "$prontus_varglb::DIR_SERVER$reldir_port_dst/$subdir");
        #my @lisdir_files = &glib_fildir_02::lee_dir("$prontus_varglb::DIR_SERVER$reldir_port_dst/$subdir");
        #@lisdir_files = grep !/^\./, @lisdir_files;
        #foreach my $arch (@lisdir_files) {
            #next if (!-f "$prontus_varglb::DIR_SERVER$reldir_port_dst/$subdir/$arch");

            #if ($entidad eq 'seccion') {
                #$urls .= "&raquo; <a href=\"$reldir_port_dst/$subdir/$arch\" target=\"_blank\">$subdir/$1</a><br/>" if ($arch =~ /([^\/]+)_$id\_\_\_1\.\w+$/);
            #} elsif ($entidad eq 'tema') {
                #$urls .= "&raquo; <a href=\"$reldir_port_dst/$subdir/$arch\" target=\"_blank\">$subdir/$1</a><br/>" if ($arch =~ /([^\/]+)_[0-9]+\_$id\_\_1\.\w+$/);
            #} elsif ($entidad eq 'subtema') {
                #$urls .= "&raquo; <a href=\"$reldir_port_dst/$subdir/$arch\" target=\"_blank\">$subdir/$1</a><br/>" if ($arch =~ /([^\/]+)_[0-9]+\_[0-9]+\_$id\_1\.\w+$/);
            #};
        #};
    #};

    #$urls =~ s/<br\/>$//;
    #if ($urls) {


        #$urls = "<a href=\"#\" onclick=\" if (!\$('#tp_div$id$entidad').hasClass('visible$id$entidad')) {  \$('#tp_div$id$entidad').slideDown(); \$('#tp_div$id$entidad').addClass('visible$id$entidad'); } else { \$('#tp_div$id$entidad').slideUp(); \$('#tp_div$id$entidad').removeClass('visible$id$entidad'); }\" >"
              #. "URLs taxon&oacute;micas</a>"
              #. "<div id=\"tp_div$id$entidad\" class=\"oculto\">$urls</div>";
    #};


    #return $urls;

#};
# ---------------------------------------------------------------
sub get_url_taxports {
# /<prontus_dir>/site/tax/port/(all|<fid>)[-<vista>]/taxport_<s>_<t>_<st>_<nropag>.<ext>
    my ($id, $entidad) = @_;


    my $urls;
    foreach my $reldir (keys %HASH_FS_TAX) {
        my $nom_subdir;
        if ($reldir =~ /([^\/]+)$/) {
            $nom_subdir = $1;
        } else {
            next;
        };
        my @lisdir_files = split(/;/, $HASH_FS_TAX{$reldir});
        foreach my $arch (@lisdir_files) {
            if ($entidad eq 'seccion') {
                $urls .= "&raquo; <a href=\"$reldir/$arch\" target=\"_blank\">$nom_subdir/$1</a><br/>" if ($arch =~ /([^\/]+)_$id\_\_\_1\.\w+$/);
            } elsif ($entidad eq 'tema') {
                $urls .= "&raquo; <a href=\"$reldir/$arch\" target=\"_blank\">$nom_subdir/$1</a><br/>" if ($arch =~ /([^\/]+)_[0-9]+\_$id\_\_1\.\w+$/);
            } elsif ($entidad eq 'subtema') {
                $urls .= "&raquo; <a href=\"$reldir/$arch\" target=\"_blank\">$nom_subdir/$1</a><br/>" if ($arch =~ /([^\/]+)_[0-9]+\_[0-9]+\_$id\_1\.\w+$/);
            };

        };
    };

    $urls =~ s/<br\/>$//;
    if ($urls) {
        $urls = "<a href=\"#\" class=\"showurls\" rel=\"show$entidad$id\">URLs taxon&oacute;micas</a>"
              . "<div id=\"tp_div$entidad$id\" class=\"oculto\">$urls</div>";
    };


    return $urls;

};

# ---------------------------------------------------------------
sub generar_fila {
    # Genera y retorna cada fila de la lista de Areas de Cargo.
    my ($loop_row, $id, $nom, $mostrar, $port, $orden, $num_subniveles, $nom4vistas, $taxports) = @_;



    $orden = '' if ($orden == 0);

    $loop_row =~ s/%%_id%%/$id/g;
    $loop_row =~ s/%%_nombre%%/$nom/g;

    if ($mostrar) {
        $mostrar = 'btn_ticket_green';
    } else {
        $mostrar = 'btn_ticket_red';
    };
    $loop_row =~ s/%%_mostrar%%/$mostrar/g;
    $loop_row =~ s/%%_port%%/$port/g;
    $loop_row =~ s/%%_taxports%%/$taxports/g;
    $loop_row =~ s/%%_pos%%/$orden/g;
    $loop_row =~ s/%%_num_subniveles%%/$num_subniveles/g;

    $loop_row = &parse_multivistas($loop_row, $nom4vistas, 'vista_loop_row'); # rotulos tax
    $loop_row = &parse_multivistas($loop_row, $nom4vistas, 'vista_edit_loop_row'); # rotulos tax

    return $loop_row;
}; # generar_fila.

# ---------------------------------------------------------------
sub cache_dirs_tax  {
    my ($entidad) = shift;
    my ($reldir_port_dst) = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_PTEMA"; # /<prontus_dir>/site/tax/port

    my @lisdir = &glib_fildir_02::lee_dir("$prontus_varglb::DIR_SERVER$reldir_port_dst");
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

    my $urls;
    my %hash_fs;
    foreach my $subdir (@lisdir) {
        next if (!-d "$prontus_varglb::DIR_SERVER$reldir_port_dst/$subdir");
        my @lisdir_files = &glib_fildir_02::lee_dir("$prontus_varglb::DIR_SERVER$reldir_port_dst/$subdir");
        @lisdir_files = grep !/^\./, @lisdir_files;
        foreach my $arch (@lisdir_files) {
            next if (!-f "$prontus_varglb::DIR_SERVER$reldir_port_dst/$subdir/$arch");
            next if (!-s "$prontus_varglb::DIR_SERVER$reldir_port_dst/$subdir/$arch");

            if ($entidad eq 'seccion') {
                $hash_fs{"$reldir_port_dst/$subdir"} .= "$arch;" if ($arch =~ /([^\/]+)_[0-9]+\_\_\_1\.\w+$/);
            } elsif ($entidad eq 'tema') {
                $hash_fs{"$reldir_port_dst/$subdir"} .= "$arch;" if ($arch =~ /([^\/]+)_[0-9]+\_[0-9]+\_\_1\.\w+$/);
            } elsif ($entidad eq 'subtema') {
                $hash_fs{"$reldir_port_dst/$subdir"} .= "$arch;" if ($arch =~ /([^\/]+)_[0-9]+\_[0-9]+\_[0-9]+\_1\.\w+$/);
            };
        };
    };
    return %hash_fs;
}
# ----------------------------------------------------------------
# -------------------------END SCRIPT----------------------
