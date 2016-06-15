#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

#-------------------------------COMENTARIO GLOBAL---------------
#---------------------------------------------------------------
# PROPOSITO.
#-----------
# Funciones centralizadas para el sistema de tags

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 1.0.0 - XX/05/2011 - CVI - Primera version.
# 1.1.0 - 18/04/2016 - MPG - Agrega funciones para regeneraciÛn masiva.

#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package lib_tags;
use glib_dbi_02;

use lib_prontus;
use glib_fildir_02;

#use glib_hrfec_02;

use prontus_varglb;

#use Artic;
use DBI;

our $MAX_ARTICS_PER_SEARCH = 20;

our $MAX_TAGS_SEARCH_RESULT = 50;

$TMPL_4FIDS = '/cpan/core/prontus_tags4fids.html';
$SITE_4FIDS = '/cpan/procs/tags4fids/tags4fids.html';

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub limpiar_nom {

    my ($tag_name) = ($_[0]);
    # convierte tags a latin1 para poder aplicar la er
    utf8::decode($tag_name);
    $tag_name =~ s/[^\w\,\-·ÈÌÛ˙¸Ò¡…Õ”⁄‹— \.]//g;
    $tag_name =~ tr/¡…Õ”⁄‹—/·ÈÌÛ˙¸Ò/;
    $tag_name = lc($tag_name);
    # restaura a utf8
    utf8::encode($tag_name);
    return $tag_name;
}


# ---------------------------------------------------------------
sub check_nom {
  # Verifica que el nombre no exista en la tabla.
  my ($db, $id, $nombre) = ($_[0], $_[1], $_[2]);

  my $sql;
  if($id) {
    $sql = "select count(TAGS_TAG) from TAGS where lower(TAGS_TAG) = lower(\"$nombre\") and TAGS_ID <> $id";
  } else {
    $sql = "select count(TAGS_TAG) from TAGS where lower(TAGS_TAG) = lower(\"$nombre\")";
  }
  my $cant;
  my $salida = &glib_dbi_02::ejecutar_sql_bind($db, $sql, \$cant);
  $salida->fetch;
  $salida->finish;
  if ($cant > 0){
    return 'Nombre de Ìtem ya existe.';
  };
  return '';
}; # tit_repetido.

# ---------------------------------------------------------------
sub get_tags_for_fid {
    my ($base) = $_[0];
    my ($ts) = $_[1];

    # tags asignados
    my $sql = "select TAGSART_IDTAGS,TAGS_TAG from TAGSART join TAGS on TAGS_ID=TAGSART_IDTAGS where TAGSART_IDART = '$ts' order by TAGS_TAG asc;";
    # warn("ts[$ts]");
    my $tab_output = &glib_dbi_02::ejecutar_sql($base, $sql);
    my ($idtag_asignado, $tag_name);
    $tab_output->bind_columns(undef, \($idtag_asignado, $tag_name));
    # Se leen los tags de la BD
    my %hash_tags;
    while($tab_output->fetch) {
        $tag_name = &lib_prontus::escape_xml($tag_name);
        $hash_tags{$idtag_asignado} = $tag_name;
        # warn("sin ordenar[$tagid -> $tagname]");
    };
    # Se ordenan alfabeticamente los tags
    my $options = '';
    foreach my $tagid (sort {&lib_tags::normalize4sort($hash_tags{$a}) cmp &lib_tags::normalize4sort($hash_tags{$b})} keys %hash_tags) {
        my $shortname = $hash_tags{$tagid};
        $options = $options . "$tagid|$shortname,";
    }

    $options =~ s/,$//;
    $tab_output->finish;
    # Agrega a la combo los tags que esten asignados al articulo
    # warn("options[$options]");
    return $options;
};

# ---------------------------------------------------------------
sub get_last_tags {

    my ($base, $last_tags_max) = ($_[0], $_[1]);

    # los ultimos tags ingresados
    my $sql = "select TAGS_ID,TAGS_TAG from TAGS where TAGS_MOSTRAR = 1 order by TAGS_ID desc limit $last_tags_max";
    # print STDERR $sql;

    my $tab_output = &glib_dbi_02::ejecutar_sql($base, $sql);
    my ($idtag, $tag_name);

    $tab_output->bind_columns(undef, \($idtag, $tag_name));
    my %hash_tags;
    while($tab_output->fetch) {
        $tag_name = &lib_prontus::escape_xml($tag_name);
        $hash_tags{$idtag} = $tag_name;
        # warn("sin ordenar[$tagid -> $tagname]");
    };

    my $last_tags = '';
    foreach my $tagid (sort {&lib_tags::normalize4sort($hash_tags{$a}) cmp &lib_tags::normalize4sort($hash_tags{$b})} keys %hash_tags) {
        my $shortname = $hash_tags{$tagid};
        if(length($shortname) > 18) {
            $shortname = substr($shortname, 0, 18). '...';
        }
        $last_tags = $last_tags . '<div class="unused"><a href="#tag' .$tagid. '" rel="item' .$tagid. '" title="Agregar Tag: ' .$hash_tags{$tagid}. '" alt="' .$hash_tags{$tagid}. '">' .$shortname. '</a></div> ';
    }

    return $last_tags;
};

# ---------------------------------------------------------------
sub get_all_tags {

  my ($base) = $_[0];
  my %hash_tags;

  my $sql = "select TAGS_ID,TAGS_TAG from TAGS where TAGS_MOSTRAR = 1 order by TAGS_TAG asc";
  my $tab_output = &glib_dbi_02::ejecutar_sql($base, $sql);

  my ($idtag, $tag_name);
  $tab_output->bind_columns(undef, \($idtag, $tag_name));

  while($tab_output->fetch) {
    $hash_tags{$idtag} = $tag_name;
  }
  return %hash_tags;
}

# ---------------------------------------------------------------
sub normalize4sort {
    my $in = $_[0];
    utf8::decode($in);
    $in = lc($in);
    $in =~ tr/—/Ò/; # lc probably didn't catch this
    $in =~ tr/·ÈÌÛ˙¸/aeiouu/;
    $in =~ tr< abcdefghijklmnÒopqrstuvwxyz >
    < \x01-\x1B >; # 1B = 27
    utf8::encode($in);
    return $in;
};

# ---------------------------------------------------------------
sub make_cache {

    my ($base, $prontus) = ($_[0], $_[1]);
    my $path_conf = "/$prontus/cpan/$prontus.cfg";

    my $rutatmpl = "$prontus_varglb::DIR_SERVER/$prontus$lib_tags::TMPL_4FIDS";
    my $rutacache = "$prontus_varglb::DIR_SERVER/$prontus$lib_tags::SITE_4FIDS";

    my $buffer = &glib_fildir_02::read_file($rutatmpl);
    if($buffer =~ /%%LOOP_TAGS%%(.*?)%%\/LOOP_TAGS%%/is) {

      my $loop = $1;
      my ($loop_tot, $loop_tmp);
      # los ultimos tags ingresados
      my $sql = "select TAGS_ID,TAGS_TAG from TAGS where TAGS_MOSTRAR = 1 order by TAGS_TAG asc";
      # print STDERR $sql;

      my %hash_tags = &get_all_tags($base);

      foreach my $tagid (sort {&normalize4sort($hash_tags{$a}) cmp &normalize4sort($hash_tags{$b})} keys %hash_tags) {
        my $tag_name = $hash_tags{$tagid};
        $tag_name = &lib_prontus::escape_xml($tag_name);

        my $shortname = $hash_tags{$tagid};
        if(length($shortname) > 22) {
          $shortname = substr($shortname, 0, 22). '...';
        }
        $loop_tmp = $loop;
        $loop_tmp =~ s/%%_tags_shrttag%%/$shortname/ig;
        $loop_tmp =~ s/%%_tags_tag%%/$tag_name/ig;
        $loop_tmp =~ s/%%_tags_id%%/$tagid/ig;
        $loop_tot = $loop_tot . $loop_tmp;
      }
      $buffer =~ s/%%LOOP_TAGS%%.*?%%\/LOOP_TAGS%%/$loop_tot/isg;
    }
    $buffer =~ s/%%_path_conf%%/$path_conf/ig;
    $buffer =~ s/%%_prontus_id%%/$prontus/ig;
    $buffer =~ s/%%_server_name%%/$prontus_varglb::IP_SERVER/ig;

    &glib_fildir_02::write_file($rutacache, $buffer);
};

# ---------------------------------------------------------------
sub clear_cache {

    my ($prontus) = ($_[0]);
    my $rutacache = "$prontus_varglb::DIR_SERVER/$prontus$lib_tags::SITE_4FIDS";
    if(-f $rutacache) {
        unlink($rutacache);
    }
};

# ---------------------------------------------------------------
sub get_tag_noms {
    my $base = shift;
    my $tag_id = shift;
    my %tag_noms;

    my $sql = "select TAGS_TAG, TAGS_NOM4VISTAS from TAGS where TAGS_ID = '$tag_id'";
    my $tag;
    my $nom4vistas;
    my $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($tag, $nom4vistas));
    while ($salida->fetch) {
        $tag_noms{''} = &lib_prontus::escape_html($tag); # nombre en la vista default o ppal
        while ($nom4vistas =~ /(^|\n)(\w+)\t(.*?)($|\n)/sg) {
            my $vista = $2;
            my $nom = $3;
            $tag_noms{$vista} = &lib_prontus::escape_html($nom); # nombre en cada vista
        };
    };
    $salida->finish;
    return %tag_noms;
};



# ---------------------------------------------------------------

return 1;

# -------------------------------END LIBRERIA--------------------
