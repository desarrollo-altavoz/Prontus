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
# Funciones para Servidor de Contactos.

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 01   : 28/11/2001 - MCO - Primera version.
# 01.1 : 11/01/2002 - MCO - Nueva funcion 'gen_arch_bitac', recibe texto y lo graba en archivo de bitacora
#                           junto con hora y usuario que hizo la accion (cookie). Devuelve nada.
#                           Si el archivo no existe lo crea, sino agrega en una nueva fila la informacion.
#                           Guarda archivo con nombre dd.log en directorio aaaamm (si directorio no existe, lo crea).

#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package lib_setbd;

use glib_dbi_02;
use glib_html_02;
use glib_fildir_02;

use strict;
our $ENGINE = "MYISAM";

#---------------------------------------------------------------
# SUB-RUTINAS.
#---------------------------------------------------------------
sub crear_tabla_secc {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'SECC', $motor)) {

        # MYSQL
        if ($motor eq 'MYSQL') {
            my $sql = "
                    CREATE TABLE SECC (
                    SECC_ID int(5) NOT NULL auto_increment,
                    SECC_NOM varchar(128) NOT NULL default '',
                    SECC_MOSTRAR char(1) NOT NULL default '1',
                    SECC_PORT varchar(255) NOT NULL default '',
                    SECC_ORDEN int(5) NOT NULL default 0,
                    SECC_NOM4VISTAS text,
                    PRIMARY KEY  (SECC_ID),
                    KEY SECC_NOM (SECC_NOM)
                    )
                        CHARACTER SET utf8
                        COLLATE utf8_general_ci
                        ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla SECC:" . $base->errstr, 1);
            $msg_ret = "- Tabla 'SECC' creada OK.";
        };
    }
    else {
        $msg_ret = '- Error: La tabla SECC ya existe.';
        $hay_error = 1;
    };
    return ($msg_ret, $hay_error);
};

#---------------------------------------------------------------
sub crear_tabla_temas {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'TEMAS', $motor)) {

        # MYSQL
        if ($motor eq 'MYSQL') {
            my $sql = "
                    CREATE TABLE TEMAS (
                    TEMAS_ID int(5) NOT NULL auto_increment,
                    TEMAS_NOM varchar(128) NOT NULL default '',
                    TEMAS_IDSECC int(5) NOT NULL default '0',
                    TEMAS_MOSTRAR char(1) NOT NULL default '1',
                    TEMAS_PORT varchar(255) NOT NULL default '',
                    TEMAS_ORDEN int(5) NOT NULL default 0,
                    TEMAS_NOM4VISTAS text,
                    PRIMARY KEY  (TEMAS_ID),
                    KEY TEMAS_IDSECC (TEMAS_IDSECC),
                    KEY TEMAS_NOM (TEMAS_NOM)
                    )
                        CHARACTER SET utf8
                        COLLATE utf8_general_ci
                        ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla TEMAS:" . $base->errstr, 1);
            $msg_ret = "- Tabla TEMAS creada OK.";
        };
    }
    else {
        $msg_ret = '- Error: La tabla TEMAS ya existe.';
        $hay_error = 1;
    };
    return ($msg_ret, $hay_error);
};
#---------------------------------------------------------------

sub crear_tabla_subtemas {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'SUBTEMAS', $motor)) {

        # MYSQL
        if ($motor eq 'MYSQL') {
            my $sql = "
                    CREATE TABLE SUBTEMAS (
                    SUBTEMAS_ID int(5) NOT NULL auto_increment,
                    SUBTEMAS_NOM varchar(128) NOT NULL default '',
                    SUBTEMAS_IDTEMAS int(5) NOT NULL default '0',
                    SUBTEMAS_MOSTRAR char(1) NOT NULL default '1',
                    SUBTEMAS_PORT varchar(255) NOT NULL default '',
                    SUBTEMAS_ORDEN int(5) NOT NULL default 0,
                    SUBTEMAS_NOM4VISTAS text,
                    PRIMARY KEY  (SUBTEMAS_ID),
                    KEY SUBTEMAS_IDTEMAS (SUBTEMAS_IDTEMAS),
                    KEY SUBTEMAS_NOM (SUBTEMAS_NOM)
                    )
                        CHARACTER SET utf8
                        COLLATE utf8_general_ci
                        ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla SUBTEMAS:" . $base->errstr, 1);
            $msg_ret = "- Tabla SUBTEMAS creada OK.";
        };
    }
    else {
        $msg_ret = '- Error: La tabla SUBTEMAS ya existe.';
        $hay_error = 1;
    };
    return ($msg_ret, $hay_error);
};
#---------------------------------------------------------------

sub crear_tabla_tags {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'TAGS', $motor)) {

        # MYSQL
        if ($motor eq 'MYSQL') {
            my $sql = "
                    CREATE TABLE TAGS (
                    TAGS_ID int(10) NOT NULL auto_increment,
                    TAGS_TAG varchar(255) not null default '',
                    TAGS_COUNT FLOAT NOT NULL default 0,
                    TAGS_MOSTRAR char(1) NOT NULL default 1,
                    TAGS_NOM4VISTAS text,
                    PRIMARY KEY  (TAGS_ID),
                    KEY TAG (TAGS_TAG),
                    KEY COUNT (TAGS_COUNT)
                    )
                        CHARACTER SET utf8
                        COLLATE utf8_general_ci
                        ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla TAGS:" . $base->errstr, 1);
            $msg_ret = "- Tabla TAGS creada OK.";
        };
    }
    else {
        $msg_ret = '- Error: La tabla TAGS ya existe.';
        $hay_error = 1;
    };
    return ($msg_ret, $hay_error);
};
#---------------------------------------------------------------

sub crear_tabla_tagsart {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'TAGSART', $motor)) {

        # MYSQL
        if ($motor eq 'MYSQL') {
            my $sql = "
                CREATE TABLE TAGSART (
                TAGSART_IDTAGS int(10) NOT NULL auto_increment,
                TAGSART_IDART char(14) not null default '' ,
                PRIMARY KEY  (TAGSART_IDART, TAGSART_IDTAGS),
                KEY IDART (TAGSART_IDART),
                KEY IDTAGS (TAGSART_IDTAGS)
                )
                    CHARACTER SET utf8
                    COLLATE utf8_general_ci
                    ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla TAGSART:" . $base->errstr, 1);
            $msg_ret = "- Tabla TAGSART creada OK.";
        };
    }
    else {
        $msg_ret = '- Error: La tabla TAGSART ya existe.';
        $hay_error = 1;
    };
    return ($msg_ret, $hay_error);
};
#---------------------------------------------------------------

sub crear_tabla_coment {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'COMENT', $motor)) {

        # MYSQL
        if ($motor eq 'MYSQL') {
            my $sql = "
                create table COMENT (
                COMENT_ID         int(16) not null auto_increment,
                COMENT_OBJTIPO    varchar(32) not null default '',
                COMENT_OBJID      varchar(64) not null default '',
                COMENT_OBJTIT     varchar(64) not null default '',
                COMENT_DATETIME   char(14) not null default '',
                COMENT_TEXTO      text,
                COMENT_NICK       varchar(80) not null default '',
                COMENT_STATUS     int(1) not null default 0,
                COMENT_EMAIL      varchar(100) not null default '',
                primary key (COMENT_ID),
                KEY COMENT_OBJTIPO (COMENT_OBJTIPO),
                KEY COMENT_OBJTIPO_ID (COMENT_OBJTIPO, COMENT_OBJID),
                KEY COMENT_NICK (COMENT_NICK),
                KEY ID_ST (COMENT_OBJID, COMENT_STATUS)
                )
                    CHARACTER SET utf8
                    COLLATE utf8_general_ci
                    ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla COMENT:" . $base->errstr, 1);
            $msg_ret = "- Tabla COMENT creada OK.";
        };
    }
    else {
        $msg_ret = '- Error: La tabla COMENT ya existe.';
        $hay_error = 1;
    };
    return ($msg_ret, $hay_error);
};

#---------------------------------------------------------------
sub crear_tabla_asset {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'ASSET', $motor)) {

        # MYSQL
        if ($motor eq 'MYSQL') {
            my $sql = "
                create table ASSET (
                ASSET_ART_ID char(14) not null,
                ASSET_FILE varchar(50) not null,
                ASSET_TYPE enum('foto', 'video', 'audio') not null,
                ASSET_SEARCH_WORDKEY varchar(255) not null,
                ASSET_SEARCH_TEXTO varchar(255) not null,
                ASSET_SEARCH_FOTO varchar(512) not null,
                ASSET_ART_FID varchar(30) not null,
                ASSET_ART_FILE varchar(30) not null,
                ASSET_ART_WFOTO int,
                ASSET_ART_HFOTO int,
                PRIMARY KEY  (ASSET_FILE, ASSET_ART_ID),
                FULLTEXT WK (ASSET_SEARCH_WORDKEY)
                )
                    CHARACTER SET utf8
                    COLLATE utf8_general_ci
                    ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla ASSET:" . $base->errstr, 1);
            $msg_ret = "- Tabla ASSET creada OK.";
        };
    }
    else {
        $msg_ret = '- Error: La tabla ASSET ya existe.';
        $hay_error = 1;
    };
    return ($msg_ret, $hay_error);
};

#---------------------------------------------------------------
sub crear_tabla_art {
  my $base = $_[0];
  my $motor = $_[1]; # PRONTUS | MYSQL
  my ($msg_ret, $hay_error);

  if (!&existe_tabla($base, 'ART', $motor)) {

    # MYSQL
    if ($motor eq 'MYSQL') {
        my $sql = "create table ART (
                ART_AUTOINC int(18) auto_increment not null,
                ART_ID char(14) not null default '' ,

                ART_IDSECC1 int(5) not null default 0,
                ART_IDTEMAS1 int(5) not null default 0,
                ART_IDSUBTEMAS1 int(5) not null default 0,

                ART_IDSECC2 int(5) not null default 0,
                ART_IDTEMAS2 int(5) not null default 0,
                ART_IDSUBTEMAS2 int(5) not null default 0,

                ART_IDSECC3 int(5) not null default 0,
                ART_IDTEMAS3 int(5) not null default 0,
                ART_IDSUBTEMAS3 int(5) not null default 0,

                ART_AUTOR varchar(32) not null default '',

                ART_TITU varchar(255) not null default '',
                ART_BAJA varchar(200) not null default '',
                ART_FECHAP char(8) not null default '',
                ART_HORAP char(4) not null default '',
                ART_FECHAPHORAP char(12) not null default '',
                ART_DIRFECHA char(8) not null default '' ,
                ART_EXTENSION varchar(4) not null default '' ,

                ART_TIPOFICHA varchar(64) not null default '' ,
                ART_ALTA varchar(1) not null default '',
                ART_IDUSR int(5) not null default 0,

                ART_FECHAE char(8) not null default '99999999',
                ART_HORAE char(4) not null default '0000',
                ART_SOLOPORTADAS varchar(1) not null default '1',
                ART_FECHAEHORAE char(12) not null default '',

                PRIMARY KEY (ART_AUTOINC),
                UNIQUE INDEX TS (ART_ID),
                INDEX SEC1 (ART_IDSECC1),
                INDEX SEC2 (ART_IDSECC2),
                INDEX SEC3 (ART_IDSECC3),
                INDEX SECTST1 (ART_IDSECC1, ART_IDTEMAS1, ART_IDSUBTEMAS1),
                INDEX FP(ART_FECHAP),
                INDEX FH (ART_FECHAPHORAP),
                INDEX FHE (ART_FECHAEHORAE),
                INDEX TF (ART_TIPOFICHA),
                INDEX AL (ART_ALTA),
                INDEX DF (ART_DIRFECHA),
                FULLTEXT AU (ART_AUTOR),
                FULLTEXT TI (ART_TITU),
                FULLTEXT BA (ART_BAJA),
                INDEX FEHE (ART_FECHAE, ART_HORAE),
                INDEX FPHP (ART_FECHAP, ART_HORAP)

            )
                CHARACTER SET utf8
                COLLATE utf8_general_ci
                ENGINE = $ENGINE;";
      $base->do($sql) || return("Error al crear la tabla ART:" . $base->errstr, 1);
      $msg_ret = "- Tabla ART creada OK.";
    };

  }
  else {
    $msg_ret = '- Error: La tabla ART ya existe.';
    $hay_error = 1;
  };
  return ($msg_ret, $hay_error);
};

#---------------------------------------------------------------
sub crear_tabla_url {
  my $base = $_[0];
  my $motor = $_[1]; # PRONTUS | MYSQL
  my ($msg_ret, $hay_error);

  if (!&existe_tabla($base, 'URL', $motor)) {

    # MYSQL
    if ($motor eq 'MYSQL') {
        my $sql = "create table URL (
                URL_ID int(18) auto_increment not null,
                URL_ART_ID char(14) not null default '' ,
                URL_ART_URI varchar(100) not null default '',

                PRIMARY KEY (URL_ID),
                UNIQUE INDEX TS (URL_ART_ID),
                UNIQUE (URL_ART_URI),
                FULLTEXT UA (URL_ART_URI)
            )
                CHARACTER SET utf8
                COLLATE utf8_general_ci
                ENGINE = $ENGINE;";
      $base->do($sql) || return("Error al crear la tabla URL:" . $base->errstr, 1);
      $msg_ret = "- Tabla URL creada OK.";
    };

  }
  else {
    $msg_ret = '- Error: La tabla URL ya existe.';
    $hay_error = 1;
  };
  return ($msg_ret, $hay_error);
};

#---------------------------------------------------------------
sub crear_tabla_multitag_s {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'MULTITAG_S', $motor)) {
        if ($motor eq 'MYSQL') {
            my $sql = "CREATE TABLE IF NOT EXISTS `MULTITAG_S` (
                `MULTITAG_S_ID` INT NOT NULL AUTO_INCREMENT,
                `MULTITAG_S_NOMBRE` VARCHAR(128) NOT NULL,
                `MULTITAG_S_FRIENDLY` VARCHAR(64) NOT NULL,
                `MULTITAG_S_ESTADO` TINYINT NOT NULL DEFAULT 1,
                PRIMARY KEY (`MULTITAG_S_ID`),
                INDEX `index2` (`MULTITAG_S_FRIENDLY`))
                ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla MULTITAG_S:" . $base->errstr, 1);
            $msg_ret = "- Tabla MULTITAG_S creada OK.";
        }
    } else {
        $msg_ret = '- Error: La tabla MULTITAG_S ya existe.';
        $hay_error = 1;
    }
    return ($msg_ret, $hay_error);
};

#---------------------------------------------------------------
sub crear_tabla_multitag_t {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'MULTITAG_T', $motor)) {
        if ($motor eq 'MYSQL') {
            my $sql = "CREATE TABLE IF NOT EXISTS `MULTITAG_T` (
                `MULTITAG_T_ID` INT NOT NULL AUTO_INCREMENT,
                `MULTITAG_T_NOMBRE` VARCHAR(128) NOT NULL,
                `MULTITAG_T_FRIENDLY` VARCHAR(64) NOT NULL,
                `MULTITAG_T_ESTADO` TINYINT NOT NULL DEFAULT 1,
                PRIMARY KEY (`MULTITAG_T_ID`),
                INDEX `index2` (`MULTITAG_T_FRIENDLY`))
                ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla MULTITAG_T:" . $base->errstr, 1);
            $msg_ret = "- Tabla MULTITAG_T creada OK.";
        }
    } else {
        $msg_ret = '- Error: La tabla MULTITAG_T ya existe.';
        $hay_error = 1;
    }
    return ($msg_ret, $hay_error);
};

#---------------------------------------------------------------
sub crear_tabla_multitag_st {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'MULTITAG_ST', $motor)) {
        if ($motor eq 'MYSQL') {
            my $sql = "CREATE TABLE IF NOT EXISTS `MULTITAG_ST` (
                `MULTITAG_ST_ID` INT NOT NULL AUTO_INCREMENT,
                `MULTITAG_ST_NOMBRE` VARCHAR(128) NOT NULL,
                `MULTITAG_ST_FRIENDLY` VARCHAR(64) NOT NULL,
                `MULTITAG_ST_ESTADO` TINYINT NOT NULL DEFAULT 1,
                PRIMARY KEY (`MULTITAG_ST_ID`),
                INDEX `index2` (`MULTITAG_ST_FRIENDLY`))
                ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla MULTITAG_ST:" . $base->errstr, 1);
            $msg_ret = "- Tabla MULTITAG_ST creada OK.";
        }
    } else {
        $msg_ret = '- Error: La tabla MULTITAG_ST ya existe.';
        $hay_error = 1;
    }
    return ($msg_ret, $hay_error);
};

#---------------------------------------------------------------
sub crear_tabla_multitag_art_s {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'MULTITAG_ART_S', $motor)) {
        if ($motor eq 'MYSQL') {
            my $sql = "CREATE TABLE IF NOT EXISTS `MULTITAG_ART_S` (
                `MULTITAG_ART_S_ID` INT NOT NULL,
                `MULTITAG_ART_S_FRIENDLY` VARCHAR(64) NOT NULL,
                `MULTITAG_ART_S_ART_ID` CHAR(14) NOT NULL,
                PRIMARY KEY (`MULTITAG_ART_S_ID`),
                INDEX `index1` (`MULTITAG_ART_S_ID`),
                INDEX `index2` (`MULTITAG_ART_S_ART_ID`),
                INDEX `index3` (`MULTITAG_ART_S_ART_ID`, `MULTITAG_ART_S_ID`))
                ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla MULTITAG_ART_S:" . $base->errstr, 1);
            $msg_ret = "- Tabla MULTITAG_ART_S creada OK.";
        }
    } else {
        $msg_ret = '- Error: La tabla MULTITAG_ART_S ya existe.';
        $hay_error = 1;
    }
    return ($msg_ret, $hay_error);
};

#---------------------------------------------------------------
sub crear_tabla_multitag_art_t {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'MULTITAG_ART_T', $motor)) {
        if ($motor eq 'MYSQL') {
            my $sql = "CREATE TABLE IF NOT EXISTS `MULTITAG_ART_T` (
                `MULTITAG_ART_T_ID` INT NOT NULL,
                `MULTITAG_ART_T_FRIENDLY` VARCHAR(64) NOT NULL,
                `MULTITAG_ART_T_ART_ID` CHAR(14) NOT NULL,
                PRIMARY KEY (`MULTITAG_ART_T_ID`),
                INDEX `index1` (`MULTITAG_ART_T_ID`),
                INDEX `index2` (`MULTITAG_ART_T_ART_ID`),
                INDEX `index3` (`MULTITAG_ART_T_ART_ID`, `MULTITAG_ART_T_ID`))
                ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla MULTITAG_ART_T:" . $base->errstr, 1);
            $msg_ret = "- Tabla MULTITAG_ART_T creada OK.";
        }
    } else {
        $msg_ret = '- Error: La tabla MULTITAG_ART_T ya existe.';
        $hay_error = 1;
    }
    return ($msg_ret, $hay_error);
};

#---------------------------------------------------------------
sub crear_tabla_multitag_art_st {
    my $base = $_[0];
    my $motor = $_[1]; # PRONTUS | MYSQL
    my ($msg_ret, $hay_error);

    if (!&existe_tabla($base, 'MULTITAG_ART_ST', $motor)) {
        if ($motor eq 'MYSQL') {
            my $sql = "CREATE TABLE IF NOT EXISTS `MULTITAG_ART_ST` (
                `MULTITAG_ART_ST_ID` INT NOT NULL,
                `MULTITAG_ART_ST_FRIENDLY` VARCHAR(64) NOT NULL,
                `MULTITAG_ART_ST_ART_ID` CHAR(14) NOT NULL,
                PRIMARY KEY (`MULTITAG_ART_ST_ID`),
                INDEX `index1` (`MULTITAG_ART_ST_ID`),
                INDEX `index2` (`MULTITAG_ART_ST_ART_ID`),
                INDEX `index3` (`MULTITAG_ART_ST_ART_ID`, `MULTITAG_ART_ST_ID`))
                ENGINE = $ENGINE;";
            $base->do($sql) || return("Error al crear la tabla MULTITAG_ART_ST:" . $base->errstr, 1);
            $msg_ret = "- Tabla MULTITAG_ART_ST creada OK.";
        }
    } else {
        $msg_ret = '- Error: La tabla MULTITAG_ART_ST ya existe.';
        $hay_error = 1;
    }
    return ($msg_ret, $hay_error);
};

# ---------------------------------------------------------------
sub existe_tabla {
  # SQLITE
  my ($base) = $_[0];
  my ($tabla) = $_[1];
  my ($motor) = $_[2];
  my ($sql, $salida, $nom);

  $nom = 0;

  # MYSQL
  if ($motor eq 'MYSQL') {
    $sql = "show tables";
    $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($nom));
    while ($salida->fetch) {
      # print STDERR "nom[$nom] - tabla[$tabla]\n";
      if ($nom eq $tabla) {
        $salida->finish;
        return $nom;
      };
    };
    $salida->finish;
    return '';
  };
  # SQLITE
  if ($motor eq 'PRONTUS') {
    $sql = "SELECT name from sqlite_master where type = 'table' and name='$tabla'";
    $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($nom));
    $salida->fetch;
    $salida->finish;
    return $nom;
  };
};

return 1;

# -------------------------------END LIBRERIA--------------------
