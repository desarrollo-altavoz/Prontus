#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

package lib_dam;

# ----------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Para agregar funciones genéricas al DAM
# 1.0.0 - 14/12/2011 - CVI - Primera Version
#
# --------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ---------------------------------------------------------------
use prontus_varglb; &prontus_varglb::init();
use lib_thumb;
use dam_varglb;
use glib_fildir_02;
use lib_prontus;

# ---------------------------------------------------------------
sub procesa_artic {

    my ($ts_artic, $prontus_id, $dir_server, $ip_server, $base) = @_;

    # Recupera datos del articulo
    my $artic_obj = Artic->new(
                  'prontus_id'=>$prontus_id,
                  'public_server_name'=>$ip_server,
                  'cpan_server_name'=>$ip_server,
                  'document_root'=>$dir_server,
                  'ts'=>$ts_artic,
                  'campos'=>{}) || die "Error inicializando objeto articulo: $Artic::ERR\n";
    my %campos_xml = $artic_obj->get_xml_content();

    # Elimina assets asociado al articulo
    my $elimina = &elimina_all_asset($ts_artic, \$base);
    if (!$elimina) {
        warn('No se pudieron eliminar los asset asociados a articulo [' . $ts_artic . ']');
        exit;
    };

    # Recupera datos base de asset para insercion
    my (%asset, $titular, $nombre_campo);
    $titular = $artic_obj->{'xml_content'}->{'_txt_titular'};
    $titular =~ s/\|/ /sg;
    $asset{'asset_search_wordkey'} = '|' . $titular . '|' . $campos_xml{'keywords'};
    $asset{'asset_art_id'} = $ts_artic;
    $asset{'asset_art_fid'} = $artic_obj->{'xml_content'}->{'_fid'};
    my $artic_ext = &lib_prontus::get_file_extension($artic_obj->{'xml_content'}->{'_plt'});
    $asset{'asset_art_file'} = $ts_artic . '.' . $artic_ext;
    foreach $nombre_campo (keys %campos_xml) {

        # Recupera fotos
        if ($nombre_campo =~ /^(foto_[0-9]+)$/i) {
            $asset{'asset_type'}      = 'foto';
            $asset{'asset_file'}      = $campos_xml{'_NOM'.$nombre_campo};
            $asset{'asset_art_wfoto'} = $campos_xml{'_w'.$nombre_campo};
            $asset{'asset_art_hfoto'} = $campos_xml{'_h'.$nombre_campo};
            $asset{'asset_search_texto'} = '';
            $asset{'asset_search_foto'} = '';

            if (($asset{'asset_file'} ne '') && ($asset{'asset_art_wfoto'} ne '') && ($asset{'asset_art_hfoto'} ne '')) {
                &guarda_asset(\%asset, \$base);
                # TODO: Generar un thumbnail de la foto, si es que es mas grande
                # my $lafoto = $dir_server . '/'.$prontus_id.'/site/artic/'.$fechap.'/imag/'.$asset{'asset_file'};
                # &lib_dam::genera_thumbnail_for_dam($lafoto);
            };
        }
        # Recupera multimedias
        elsif ($nombre_campo =~ /^multimedia_[0-9a-zA-Z\_\-]+$/i) {
            # Videos
            if ($campos_xml{$nombre_campo} =~ /(rm|rmvb|rts|m1v|m2v|m4e|mp4|mpe|mpeg|mpg|mpv2|ogm|asf|wm|wmv|flv)$/i) {
                $asset{'asset_type'} = 'video';
                $nombre_campo =~ /^multimedia_(.*?)$/i;
                my $nombre_corto = $1;
                if($campos_xml{'txt_texto_' . $nombre_corto}) {
                  $asset{'asset_search_texto'} = $campos_xml{'txt_texto_' . $nombre_corto};
                } else {
                  $asset{'asset_search_texto'} = '';
                };
                # print STDERR "buscando: ".$campos_xml{'fotofija_' . $nombre_corto};
                if($campos_xml{'fotofija_' . $nombre_corto}) {
                  $asset{'asset_search_foto'} = $campos_xml{'fotofija_' . $nombre_corto};
                } else {
                  $asset{'asset_search_foto'} = '';
                };
            }
            # Audios
            elsif ($campos_xml{$nombre_campo} =~ /(ra|aac|aif|aiff|m4a|mid|midi|mp2|mp3|mpa|mpu|msv|ogg|wav|wave|wma)$/i) {
                $asset{'asset_type'} = 'audio';
                $nombre_campo =~ /^multimedia_(.*?)$/i;
                my $nombre_corto = $1;
                if($campos_xml{'txt_texto_' . $nombre_corto}) {
                  $asset{'asset_search_texto'} = $campos_xml{'txt_texto_' . $nombre_corto};
                } else {
                  $asset{'asset_search_texto'} = '';
                };
                $asset{'asset_search_foto'} = '';
            }
            else {
                next;
            };

            # Guarda en BD
            if ($asset{'asset_type'} ne '') { # 1.0.2
                $asset{'asset_file'} = $campos_xml{$nombre_campo};
                $asset{'asset_art_wfoto'} = '';
                $asset{'asset_art_hfoto'} = '';
                &guarda_asset(\%asset, \$base);
            };
        };
    };

}
# ---------------------------------------------------------------
sub elimina_all_asset {
    my $ts_artic = $_[0];
    my $base = ${$_[1]};

    # Elimina asset asociado a articulo
    my $consulta = $base->do('delete from ASSET where ASSET_ART_ID = "' . $ts_artic .'"');

    if (!$consulta) {
        return 0;
    };
    return 1;
};

# ---------------------------------------------------------------
sub guarda_asset {
    my $aux = $_[0];
    my %asset = %$aux;
    my $base = ${$_[1]};

    #use Data::Dumper;
    #warn('--asset--');
    #warn(Dumper(%asset)) ;

    # my $motor_bd = &lib_prontus::get_motor_from_bdhandler($base);
    %asset = &lib_prontus::escapea_bd(\%asset, $base);

    # 1.0.3
    my $sql_fields = "$asset{'asset_art_id'},
                           $asset{'asset_file'},
                           $asset{'asset_type'},
                           $asset{'asset_search_wordkey'},
                           $asset{'asset_search_texto'},
                           $asset{'asset_search_foto'},
                           $asset{'asset_art_fid'},
                           $asset{'asset_art_file'},
                           $asset{'asset_art_wfoto'},
                           $asset{'asset_art_hfoto'}";

    my $sql = 'insert into ASSET values(' . $sql_fields .')';

    my $res = $base->do($sql);
    if (!$res) {
        warn('Error procesando en tabla de ASSET: asset_art_id['. $asset{'asset_art_id'}. ']'
             . 'asset_file[' . $asset{'asset_file'} . ']');
        return 0;
    };

    return 1;

};
# ---------------------------------------------------------------
sub genera_thumbnail_for_dam {

    my ($lafoto) = @_;
    my ($maxw, $maxh) = ($dam_varglb::FOTOS_WIDTH_MAX, $dam_varglb::FOTOS_HEIGHT_MAX);

    print STDERR "generando thumb: $lafoto [$maxw, $maxh]\n";
    my ($binfoto, $anchofinal, $altofinal) = &lib_thumb::make_thumbnail($maxw, $maxh, $lafoto, 0);
    $lafoto =~ s/(\.\w+)$/-dam\1/;

    &glib_fildir_02::write_file($lafoto, $binfoto);
    return;
};

# ---------------------------------------------------------------
sub get_proporcion_imagen {

    my ($maxw, $maxh, $actualw, $actualh) = @_;
    my ($neww, $newh);

    if($maxh == 0 || $actualh == 0) {
        return ($maxw, $maxh);
    };
    #print STDERR "hola cvi...";
    my $factorIdeal = $maxw / $maxh;
    my $factorImagen = $actualw / $actualh;

    if($factorIdeal <= $factorImagen) {
        $neww = $maxw;
        $neww = $actualw if($maxw > $actualw);
        $newh = ($actualh * $neww) / $actualw;
    } else {
        $newh = $maxh;
        $newh = $actualh if($maxh > $actualh);
        $neww = ($actualw * $newh) / $actualh;
    };
    return ($neww, $newh);
};

return 1;
