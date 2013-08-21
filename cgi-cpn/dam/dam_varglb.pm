#!/usr/bin/perl

package dam_varglb;

# ----------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Definir e inicializar variables globales utilizadas en sistema DAM.
# 1.0.0 - 15/07/2009 - PRB
# 1.0.1 - 25/03/2010 - CVI
# 1.1.0 - 02/03/2010 - CPN
# 2.0.0 - 09/09/2010 - CVI - Se integra a Prontus
# --------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ---------------------------------------------------------------

# $VERSION = '2.0.0 - 09/09/2010';

# Ancho maximo de fotos
$FOTOS_WIDTH_MAX = 220;
$FOTOS_HEIGHT_MAX = 150;

# Icono multimedias
$ICON_VIDEO = '/cpan/core/dam/imag/video.gif';
$ICON_AUDIO = '/cpan/core/dam/imag/audio.gif';
$FILASXPAG = 16;

$DIR_TMPL = '/cpan/core/dam/plantillas/';
$TMPL_SEARCH = 'prontus_dam_search.html';
$TMPL_ASSET_LIST = 'prontus_dam_asset_list.html';

@TIPOS = ('foto', 'video', 'audio');

return 1;