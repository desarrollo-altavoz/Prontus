#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Manejo cookies
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ------------------------

# ---------------------------------------------------------------

# -------------------------------BEGIN LIBRERIA-------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
package lib_cookies;

use strict;

# ---------------------------------------------------------------#
# SUB-RUTINAS.
# ---------------------------------------------------------------#


#-------------------------------------------------------------------------#
# 1.2
sub set_simple_cookie {
# Setea una cookie temporal para la sesion.
	my($name, $value) = @_;
	print 'Set-Cookie: ';
	print ("$name=$value; path=/; \n"); # 1.10
};

#-------------------------------------------------------------------------#
# 1.2
sub get_cookies {
# Get Cookies desde la variable de ambiente ENV.
	# Las cookies estan separadas por ";" y un espacio,
	# esto las esplitea y retorna un hash de cookies.

	my(@rawCookies) = split (/; /,$ENV{'HTTP_COOKIE'});
	my(%cookies);
	my($key, $val); # 1.3

	foreach(@rawCookies){
	    ($key, $val) = split (/=/,$_);
	    $cookies{$key} = $val;
	};

	return %cookies;
};
#--------------------------------------------------------------------#
return 1;
#-------------------------------END LIBRERIA---------------------
