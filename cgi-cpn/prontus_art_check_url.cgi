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
# PROPOSITO .
# -----------
# Verifica si ya existe un articulo con la misma url
#
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 04/10/2016 - EAG - Primera version
# 1.0.1 - 18/01/2017 - EAG - Se cambia mensaje sobre titular o slug vacío
#
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

use utf8;
use strict;
# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use glib_cgi_04;
use DBI;
use glib_dbi_02;
use JSON;


my $BD;
my %FORM;

# ---------------------------------------------------------------
# MAIN.
# -------------

main: {
    # Rescatar parametros recibidos.
    &glib_cgi_04::new();
    $FORM{'_prontus_id'} = &glib_cgi_04::param('_prontus_id');
    $FORM{'_ts'} = &glib_cgi_04::param('_ts');
    $FORM{'_txt_titular'} = &glib_cgi_04::param('_txt_titular');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'_prontus_id'});

    # Carga variables de configuracion.
    &lib_prontus::load_config(&lib_prontus::ajusta_pathconf($FORM{'_path_conf'}));  # Prontus 6.0

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    print "Cache-Control: no-cache, must-revalidate\r\n";
    print "Cache-Control: max-age=0\r\n";
    print "Cache-Control: no-store\r\n";
    print "Content-type: application/json; charset=utf-8\r\n\r\n";

    if ($prontus_varglb::FRIENDLY_URLS_VERSION eq '4') {
        if ($FORM{'_txt_titular'} eq '') {
            &glib_html_02::print_json_result('Error','El campo titular o slug no pueden ser vacíos', 'exit=1,ctype=0');
        };
        if ($FORM{'_ts'} !~ /^\d+$/ && $FORM{'_ts'} ne '') {
            &glib_html_02::print_json_result('Error','TS no es válido', 'exit=1,ctype=0');
        };

        # Conectar a BD
        my $msg_err_bd;
        ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
        if (! ref($BD)) {
            &glib_html_02::print_json_result('Error', $msg_err_bd, 'exit=1,ctype=0');
        };
        # se convierte el titular a friendly 4
        my $titular = &lib_prontus::ajusta_titular_f4($FORM{'_txt_titular'});
        if (length($titular) < 5) {
            print '{"status":"Error","msg":"La url generada es muy corta, debe tener al menos 5 caracteres","url":"'.$titular.'"}';
            exit;
        }

        my $sql = "select URL_ART_ID, URL_ART_URI from URL where URL_ART_URI = \"$titular\" ";

        if ($FORM{'_ts'} ne '') {
            $sql .= "AND URL_ART_ID <> \"$FORM{'_ts'}\"";
        }

        # los campos obtenidos corresponden a:
        # id correlativo de la tabla, TS del articulo, url friendly 4 del articulo
        my ($artId, $artUri);
        my $salida = &glib_dbi_02::ejecutar_sql($BD, $sql);
        $salida->bind_columns(undef, \($artId, $artUri));
        $salida->fetch;
        $salida->finish;

        my %data;
        # si encontramos un articulo necesitamos el titular real
        if ($artId ne '') {
            $sql = "select convert(cast(convert(ART_TITU using latin1) as binary) using utf8), ART_AUTOINC, ART_TIPOFICHA, ART_EXTENSION from ART where ART_ID = \"$artId\"";
            my ($artTitu, $artAutoInc, $artFid, $artExt);
            $salida = &glib_dbi_02::ejecutar_sql($BD, $sql);
            $salida->bind_columns(undef, \($artTitu, $artAutoInc, $artFid,$artExt));
            $salida->fetch;
            $salida->finish;

            %data = ('msg' => "Ya existe un artículo con este titular",
                        'status'=> "Error",
                        'ts' => $artId,
                        'id' => $artAutoInc,
                        'fid' => $artFid,
                        'uri_titular' => $artUri,
                        'ext' => $artExt,
                        'titular' => $artTitu);
        } else {
            %data = ('msg' => "Titular nuevo",
                     'status'=> "OK",
                     'uri_titular' => $titular);
        }

        if($JSON::VERSION =~ /^1\./) {
            my $json = new JSON;
            print $json->objToJson(\%data);
        } else {
            print encode_json(\%data);
        }
    } else {
        print '{"status":"OK","msg":"Friendly V4 no activa","url":""}';
    }
}

# -------------------------------END SCRIPT----------------------
