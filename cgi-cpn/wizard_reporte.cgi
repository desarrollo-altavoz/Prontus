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
# Genera el arbol de directorios y archivos instalados para el prontus.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# No registra.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# wizard_deploy.cgi
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# /wizard_prontus/core/reporte.html
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
# No utiliza
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 12/2005 - YCH - Primera Version.
# ---------------------------------------------------------------

# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
use glib_cgi_04;
use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_prontus;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ------

my (%FORM, $LOOP, %PRONTUS); # Variable global uno.
my ($INF_DIR) = "$prontus_varglb::DIR_SERVER/wizard_prontus/_data";
my ($INF_FILE) = "$INF_DIR/inf.txt";
my ($CRLF) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;

main:{
    print "Content-Type: text/html\n\n";
    my ($plantilla, $pagina, $lista, $aux, $lnk_cpan);

    $PRONTUS{'RELDIR_BASE'} = '' if ($PRONTUS{'RELDIR_BASE'} eq '/');             # 8.0
    &glib_cgi_04::new();

    $FORM{'DIR'} = &glib_cgi_04::param('DIR');
    $FORM{'TOPE'} = &glib_cgi_04::param('TOPE');
    $FORM{'TOPE'} = '' if ($FORM{'TOPE'} eq '/');
    $FORM{'DIR'} = '' if ($FORM{'DIR'} eq '/');
    if ($FORM{'DIR'} !~ /^$FORM{'TOPE'}/) {
        $FORM{'DIR'} = $FORM{'TOPE'};
    };
    $FORM{'DIR'} =~ s/\/$//; # borra ultimo slash si es que viene.

    if ((!(-d "$prontus_varglb::DIR_SERVER$FORM{'DIR'}")) || ($FORM{'DIR'} =~ /\.\./)) {
        $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
        &glib_html_02::print_pag_result('Error', 'Directorio no válido', 0, "exit=1, ctype=0");
    };
    
    my ($msgerr, $prontus_id, $extension) = &get_model_data();
    if ($msgerr) {
        $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
        &glib_html_02::print_pag_result('Error', $msgerr, 0, "exit=1, ctype=0");
    };

    if ($FORM{'DIR'} !~ /^\/$prontus_id/) {
        $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
        &glib_html_02::print_pag_result('Error', '[2]Directorio no válido', 0, "exit=1, ctype=0");
    };

    $lnk_cpan = "/$prontus_id/cpan/index.html";
    # Generar pagina final (loopeando una fila modelo)
    $plantilla = "$prontus_varglb::DIR_SERVER/wizard_prontus/core/reporte.html";
    $pagina = &glib_fildir_02::read_file($plantilla);

    $pagina =~ /<!--LOOP-->(.*?)<!--\/LOOP-->/isg;
    $LOOP = $1;
    $lista = &make_lista("$prontus_varglb::DIR_SERVER$FORM{'DIR'}", $LOOP);
    $pagina =~ s/<!--LOOP-->(.*?)<!--\/LOOP-->/$lista/isg;
    $pagina =~ s/%%DIR_ACTUAL%%/\//g if ($FORM{'DIR'} eq '');
    $pagina =~ s/%%DIR_ACTUAL%%/$FORM{'DIR'}/g if ($FORM{'DIR'} ne '');
    $pagina =~ s/%%dir_sup%%// if ($FORM{'DIR'} eq '');
    $aux = $FORM{'DIR'};
    $aux =~ s/(.*)\/.+$/\1/;
    $pagina =~ s/%%dir_sup%%/\// if ($FORM{'DIR'} eq '');
    $pagina =~ s/%%dir_sup%%/$aux/ if ($FORM{'DIR'} ne '');
    $pagina =~ s/%%tope%%/$FORM{'TOPE'}/;

    if ($FORM{'TOPE'} eq $FORM{'DIR'} || $FORM{'DIR'} eq "/$prontus_id") {
        $pagina =~ s/<!--ATRAS-->.*<!--\/ATRAS-->//s;
    };

    $pagina =~ s/%%lnk_cpan%%/$lnk_cpan/;
    my $lnk_sitio = "/$prontus_id/index.$extension";
    $pagina =~ s/%%lnk_sitio%%/$lnk_sitio/ig;

    # Eliminar archivo inf.
    #~ unlink $INF_FILE;
    print $pagina;
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub get_model_data {
    # Obtiene extension del modelo

    if (! -f $INF_FILE) {
        return "[errInfFile] Solicitud de ejecución no válida.";
    };

    # Leer y cargar y validar contenido del INF.
    my $buffer = &glib_fildir_02::read_file($INF_FILE);

    # prontus_id en paso1
    my $prontus_id;
    if ($buffer =~ /(\[PRONTUS\].*\[\/PRONTUS\]\n\n)/s) {
        my $buffer_prontus = $1;
        # Validar id
        if ($buffer_prontus !~ /PRONTUS_ID=(\w+)\n/) {
            return 'Información de paso 1 está corrupta.';
        } else {
            $prontus_id = $1;
        };
    } else {
        return 'Información de paso 1 está corrupta';
    };


    # valida q se haya pasado por paso2
    my $extension;
    if ($buffer =~ /(\[MODEL\].*\[\/MODEL\]\n\n)/s) {
        my $buffer_model = $1;
        if ($buffer_model =~ /MODEL_EXT=(\w+)\n/) {
            $extension = $1;
        };
    };

    return 'Información de paso 2 está corrupta' if (!$extension);
    return ('', $prontus_id, $extension);
};
# ---------------------------------------------------------------
sub make_lista {
    
    my ($dir_desde) = $_[0];
    my ($theloop) = $_[1];
    my (@entries, $entry, $local_loop, $filas);

    @entries = &glib_fildir_02::lee_dir($dir_desde);

    # Un truco para dejar los archivos primero y los dirs. despues.
    my @aux;
    my @aux2;
    foreach $entry (@entries) {
        if (-f "$dir_desde/$entry") {
            push @aux2, $entry;
        } else {
            push @aux, $entry;
        };
    };

    @entries = ();
    @entries = (@aux2, @aux);

    foreach $entry (@entries) {
        # Solo dirs. validos.
        if ( ($entry !~ /^\./g) and ((-d "$dir_desde/$entry") or (-f "$dir_desde/$entry")) and ($entry !~ /^cgi/) and ($entry !~ /^wizard/) ) {

            $local_loop = $theloop;
            if (-d "$dir_desde/$entry") {
                $local_loop =~ s/%%icono%%/folder/;
            } else {
                $local_loop =~ s/%%icono%%/file/;
                my $reldir_desde = $dir_desde;
                $reldir_desde =~ s/^$prontus_varglb::DIR_SERVER//;
                $local_loop =~ s/href=".*?"/href="$reldir_desde\/$entry"/;
            };
            my $reldir_desde = $dir_desde;
            $reldir_desde =~ s/^$prontus_varglb::DIR_SERVER//;
            $local_loop =~ s/%%nomdir%%/$entry/;
            $local_loop =~ s/%%dir%%/$reldir_desde\/$entry/;

            $local_loop =~ s/%%dir_actual%%/\// if ($reldir_desde eq '');
            $local_loop =~ s/%%dir_actual%%/$reldir_desde/ if ($reldir_desde ne '');
            $local_loop =~ s/%%tope%%/$FORM{'TOPE'}/;

            $filas .= $local_loop;
            if (-d "$dir_desde/$entry") {
                my $lp = $theloop;
                $lp =~ s/<td>/<td><img src="\/wizard_prontus\/core\/imag\/blank.gif" width="20" height="22" border="0">/;
                # se comenta para que no muestre el arbol extendido
                # $filas .= &make_lista("$dir_desde/$entry", $lp);
            };
        };
    };
    return $filas;
};

# -------------------------------END SCRIPT----------------------

