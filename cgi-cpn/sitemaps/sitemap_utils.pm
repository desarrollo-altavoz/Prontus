#!/usr/bin/perl

# -------------------------------COMENTARIO GLOBAL---------------
# PROPOSITO.
# -----------
# Funciones utilitarias para la creaciÛn de Site Maps y News Site Maps

# HISTORIAL DE VERSIONES.
# ---------------------------
# Revisar historial en la release

# -------------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

package sitemap_utils;

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

# Chequea directorio. Si no existe, lo crea.
# Param. de entrada :
# 0) ruta al CFG a Leer
# Retorna: Hash con los datos
sub datosConf {
    my ($pathtocfg) = $_[0];
    my %miConf;
    my $buffer = &sitemap_glib_fildir_02::read_file($pathtocfg);

    while($buffer =~ /([a-z0-9_]+)\s*=\s*(['|"])(.*?)\2/ig) {
        $miConf{$1} = $3;
    }
    return %miConf;
}

# Devuelve la fecha actual
#   0) Time o numero de segundos desde 1970. Si no viene, se usa el time actual
#   Retorna: La fecha en formato yyyymmddhhmmss
sub getFechaHora {
    my ($mytime) = $_[0];
    my (@mylocaltime);

    if($mytime) {
        @mylocaltime = localtime($mytime);
    } else {
        @mylocaltime = localtime;
    }
    my $year    = $mylocaltime[5] + 1900;
    my $month   = $mylocaltime[4] + 1;
    my $day     = $mylocaltime[3];
    my $hour    = $mylocaltime[2];
    my $min     = $mylocaltime[1];
    my $sec     = $mylocaltime[0];

    $month = '0'.$month if($month<10);
    $day = '0'.$day if($day<10);

    $hour = '0'.$hour if($hour<10);
    $min = '0'.$min if($min<10);
    $sec = '0'.$sec if($sec<10);
    return "$year$month$day$hour$min$sec";
}

# Devuelve la fecha actual
#   0) Time o numero de segundos desde 1970. Si no viene, se usa el time actual
#   Retorna: La fecha en formato yyyy-mm-dd
sub getFecha {
    my ($mytime) = $_[0];
    my (@mylocaltime);

    if($mytime) {
        @mylocaltime = localtime($mytime);
    } else {
        @mylocaltime = localtime;
    }

    my $year    = $mylocaltime[5] + 1900;
    my $month   = $mylocaltime[4] + 1;
    my $day     = $mylocaltime[3];

    $month = '0'.$month if($month<10);
    $day = '0'.$day if($day<10);
    return "$year-$month-$day";
}

# Devuelve la fecha limite
#   0) Time o numero de segundos desde 1970. Si no viene, se usa el time actual
#   Retorna: La fecha en formato yyyy-mm-dd
sub getDesfaseHoras {
    my ($horas) = $_[0];
    my $hoursago = time - $horas*60*60;
    my @mylocaltime = localtime($hoursago);

    my $year    = $mylocaltime[5] + 1900;
    my $month   = $mylocaltime[4] + 1;
    my $day     = $mylocaltime[3];
    my $h       = $mylocaltime[2];
    my $m       = $mylocaltime[1];

    $month = '0'.$month if($month<10);
    $day = '0'.$day if($day<10);
    $h = '0'.$h if($h<10);
    $m = '0'.$m if($m<10);

    return "$year$month$day$h$m";
}

# Devuelve el limite 2 dias atras segun google
#   Retorna: La fecha en formato yyyymmddhhmm
sub getMaxHoursLimit {
    my $hoursago = time - 48*60*60;
    my @mylocaltime = localtime($hoursago);

    my $year    = $mylocaltime[5] + 1900;
    my $month   = $mylocaltime[4] + 1;
    my $day     = $mylocaltime[3];
    my $h       = $mylocaltime[2];
    my $m       = $mylocaltime[1];

    $month = '0'.$month if($month<10);
    $day = '0'.$day if($day<10);
    $h = '0'.$h if($h<10);
    $m = '0'.$m if($m<10);

    return "$year$month$day$h$m";
}

# Devuelve la fecha del archivo
#   0) Path al archivo
#   Retorna: La fecha en formato yyyy-mm-dd
sub getFechaArchivo {
    my ($filename) = $_[0];
    if(-f $filename) {
        my $mtime = (stat($filename))[9];
        return &getFecha($mtime);
    }
    return;
}

# Calcula el Timezone real
sub getOffsetGMT {
    use Time::Local;
    my @t = localtime(time);
    my $gmt_offset_in_seconds = timegm(@t) - timelocal(@t);
    my $offset = $gmt_offset_in_seconds/3600;

    if($offset =~ /^(-?)(\d+)$/) {
        my $sign = $1;
        my $num = $2;
        if($num >= 10) {
            $sitemap_varglb::offset = $sign . $num . ':00';
        } else {
            $sitemap_varglb::offset = $sign . '0' . $num . ':00';
        }
    } else {
        $sitemap_varglb::offset = '-04:00';
    }
    #print "$sitemap_varglb::offset\n";
}

# Devuelve la fecha/hora de publicaciÛn del articulo en formato
# "News": 2008-06-07T22:41:45-04:00
#   0) Fecha de PublicaciÛn
#   1) Hora de PublicaciÛn
#   Retorna: La fecha en el formato descrito
sub getFechaNews {
    my ($fechap, $horap, $flagsegs) = ($_[0], $_[1], $_[2]);
    my $mydate;

    if($fechap ne '' && $horap ne '') {

        return unless($fechap =~ /^(\d\d\d\d)(\d\d)(\d\d)$/);
        my $year    = $1;
        my $month   = $2;
        my $day     = $3;
        my $sec;

        return unless($horap =~ /^(\d\d)(\d\d)$/);
        my $hour    = $1;
        my $min     = $2;
        if($flagsegs) {
            $sec    = int(rand(60));
            $sec = '0'.$sec if($sec < 10);
        } else {
            $sec    = '00';
        }

        if($sitemap_varglb::offsetGMT eq '') {
            $sitemap_varglb::offsetGMT = &sitemap_utils::getOffsetGMT();
        }

        $mydate = "$year-$month-${day}T$hour:$min$sitemap_varglb::offset";
    }
    return $mydate
}

# Devuelve la fecha de modificaciÛn del archivo en formato
# "News": 2008-06-07T22:41:45-04:00
#   0) Path al archivo
#   Retorna: La fecha en el formato descrito
sub getFechaArchivoNews {
    my ($filename) = $_[0];
    my $mydate;

    if(-f $filename) {
        my @mylocaltime = localtime((stat($filename))[9]);
        my $year    = $mylocaltime[5] + 1900;
        my $month   = $mylocaltime[4] + 1;
        my $day     = $mylocaltime[3];
        my $hour     = $mylocaltime[2];
        my $min     = $mylocaltime[1];
        my $sec     = $mylocaltime[0];

        $month  = '0'.$month    if($month<10);
        $day    = '0'.$day      if($day<10);
        $hour   = '0'.$hour     if($hour<10);
        $min    = '0'.$min      if($min<10);
        $sec    = '0'.$sec      if($sec<10);

        $mydate = "$year-$month-${day}T$hour:$min:$sec-04:00";
    }
    return $mydate
}

# Devuelve la frecuencia seg˙n fecha de modificaciÛn
#   0) Path al archivo
#   Retorna: La frecuencia. daily, weekly, monthly, yearly
sub getFrecuencia {
    my ($filename) = $_[0];

    my $onedayago = 60*60*24;
    my $oneweekago = $onedayago*7;
    my $onemonthago = $onedayago*30;

    if(-f $filename) {
        my $diff = (time) - (stat($filename))[9];
        if($diff < $onedayago) {
            return "daily";
        } elsif($diff < $oneweekago) {
            return "weekly";
        } elsif($diff < $onemonthago) {
            return "monthly";
        } else {
            return "yearly";
        }
    }
    return "";
}

# Obtiene las KeyWords asociadas al ArtÌculo, escapeadas.
#   0) Nombre de la secciÛn del ArtÌculo
#   1) Nombre del tema asociado al ArtÌculo
#   2) Nombre del subtema del ArtÌculo
#   Retorna: Las Keywords del ArtÌculo, escapeadas
sub getKeyWords {
    my ($secc, $tema, $stema) = (@_);
    my ($texto);
    if($secc ne '') {
        $texto = &encodeEntities($secc);
        if($tema ne '') {
            $texto = $texto .', '. &encodeEntities($tema);
            if($stema ne '') {
                $texto = $texto .', '. &encodeEntities($stema);
            }
        }
    }
    return $texto;
}

# Si el Prontus tiene Multiedicion, Obtiene la Edicion Vigente.
# Si no, devuelve 'base'
sub getEdicVigente {
    my ($docroot, $prontusid) = ($_[0], $_[1]);

    my %CONF_BD = &datosConf($docroot .'/'. $prontusid . '/cpan/'.$prontusid.'-port.cfg');
    my $rutaEdicFile = $docroot .'/'. $prontusid . '/cpan/data/ed_vigente.txt';
    my $multiedicion = $CONF_BD{'MULTI_EDICION'};

    if($multiedicion =~ /SI/i) {
        $NomEdic = &sitemap_glib_fildir_02::read_file($rutaEdicFile);
        if($NomEdic =~ /^\d{4}_\d{2}_\d{2}_\d{1,}$/) {
            return $NomEdic;
        } else {
            return 'base';
        }
    } else {
            return 'base';
    }
}

# Codifica a entidades para el sistema de News
#   0) Texto a codificar
#   Retorna: Texto ya codificado
sub encodeEntities {
    my ($texto) = $_[0];

    $texto =~ s/&/&amp;/ig;
    $texto =~ s/'/&apos;/ig;
    $texto =~ s/"/&quot;/ig;
    $texto =~ s/>/&gt;/ig;
    $texto =~ s/</&lt;/ig;

    return $texto;
}

# Obtiene friendly url en un buffer dado.
#   0) titular del artic
#   1) ts del artic
#   2) prontus id
#   3) path al articulo, relativo al document root.
#      Se utiliza para obtener la extension del artic.
#   Retorna: buffer con los reemplazos realizados
sub getFilef {
    # my ($titular, $ts, $prontus_id, $relpath_artic) = @_;
    my ($titular, $ts, $prontus_id, $relpath_artic, $nom_seccion1, $nom_tema1, $nom_subtema1) = @_;
    return '' if (!$ts || !$prontus_id || !$titular);
    my $ext;
    my $friendly;

    $ext = $1 if ($relpath_artic =~ /\.(\w+)$/);
    $titular = &sacaTagsRets($titular);
    $titular = &noTildes($titular);
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
    }

    if ($sitemap_varglb::FRIENDLY_URLS_VERSION eq '2') {
        # Formato: /prontus/seccion/tema/subtema/titular/aaaa-mm-dd/hhnnss.extension
        $friendly = "/$prontus_id/";

        if ($nom_seccion1 ne '') {
            $nom_seccion1 = &despulgarTextoFriendly($nom_seccion1);
            $friendly .= "$nom_seccion1/";
        }

        if ($nom_tema1 ne '') {
            $nom_tema1 = &despulgarTextoFriendly($nom_tema1);
            $friendly .= "$nom_tema1/";
        }

        if ($nom_subtema1 ne '') {
            $nom_subtema1 = &despulgarTextoFriendly($nom_subtema1);
            $friendly .= "$nom_subtema1/";
        }

        $friendly .= "$titular/$fecha4friendly/$hora.$ext";

    } else {
        # Deja por defecto la versiÛn 1, en caso de que no exista la variable o estÈ vacia.
        $friendly = "/$titular/$prontus_id/$fecha4friendly/$hora.$ext";
    }

    return $friendly;
}

# Elimina tags y ret. de carro.
#   0) String a procesar
#   Retorna: String procesado.
sub sacaTagsRets {
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
    my $inclinada = "¥";
    utf8::encode($inclinada) if($sitemap_varglb::PRONTUS11_UTF8);
    $toencode =~ s/'/$inclinada/sg; # cambia comilla vertical por comilla inclinada, para compatib. JS
    $toencode =~ s/&#39;/$inclinada/sg; # cambia comilla vertical por comilla inclinada, para compatib. JS

    $toencode = &encodeEntities($toencode);

    return $toencode;

}

# Reemplaza tildes por letras normales.
sub noTildes {
    my($toencode) = $_[0];

    # convierte a latin1 para poder aplicar la er
    utf8::decode($toencode);

    $toencode =~ tr/·ÈÌÛ˙¡…Õ”⁄¸‹Ò—/aeiouaeiouuunn/; # Destilda ISO.

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
    utf8::encode($toencode) if($sitemap_varglb::PRONTUS11_UTF8);
    return $toencode;
}

sub despulgarTextoFriendly {
    my $texto = $_[0];
    $texto = &sacaTagsRets($texto);
    $texto = &noTildes($texto);
    $texto = lc $texto;
    $texto =~ s/[^a-z0-9]/-/sg;
    $texto =~ s/-+/-/g;
    $texto =~ s/^-//sg;
    $texto =~ s/-$//sg;

    return $texto;
}

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
sub getCamposXml {
    my ($xmlData, $campos) = @_;
    my %camposHash;
    my @camposLista = split(/, */, $campos);
    if ($campos) {
        foreach my $nombreCampo (@camposLista) {
            if ($xmlData =~ /<($nombreCampo)>(.+?)<\/\1>/is) {
                my $campoValor = $2;
                if ($campoValor =~ /<!\[CDATA\[(.*?)\]\]>/is) {
                    $campoValor = $1;
                }
                $camposHash{lc $nombreCampo} = $campoValor;
            }
        }
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
                }
                if ($campoValor =~ /<(_h$nombreCampo)>(.+?)<\/\1>/) {
                    $camposHash{lc "_h$nombreCampo"} = $2;
                }
            }

            if ($campoValor =~ /<!\[CDATA\[(.*?)\]\]>/is) {
                $campoValor = $1;
            }

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
                    }
                    if ($campoValor =~ /<(_w$nombreCampo)>(.+?)<\/\1>/) {
                        $camposHash{lc "_W$nombreCampo"} = $2;
                    }
                    if ($campoValor =~ /<(_h$nombreCampo)>(.+?)<\/\1>/) {
                        $camposHash{lc "_H$nombreCampo"} = $2;
                    }
                }
            } else {
                $camposHash{lc $nombreCampo} = $campoValor;
            }
        }
    }

    return %camposHash;
}

#-------------------------------END LIBRERIA------------------
return 1;
