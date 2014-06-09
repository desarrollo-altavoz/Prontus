#!/usr/bin/perl

# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Hacer un chequeo de sintaxis de todas las CGIs de Prontus.
# Util para usarlo antes de generar una release o cuando se
# hacen cambios en muchas CGIs al mismo tiempo
# 
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ------------------------
#  1.0.0    - 09/04/2002 - CVI - Primera Version.
# 

use strict;

use FindBin '$Bin';
my $nuevopath = $Bin;
$nuevopath =~ s/\/release//;
$nuevopath =~ s/\/wizard_prontus//;

my $DOCUMENT_ROOT = $nuevopath;
my @DIRS;

# Acá se configuran los directorios que se van a chequear
unshift(@DIRS, '/cgi-cpn');
unshift(@DIRS, '/cgi-cpn/coment');
unshift(@DIRS, '/cgi-cpn/dam');
unshift(@DIRS, '/cgi-cpn/xcoding');

unshift(@DIRS, '/cgi-bin');
unshift(@DIRS, '/cgi-bin/coment');

main: {


	foreach my $dir (@DIRS) {

		next unless (-d "$DOCUMENT_ROOT$dir");
		print STDOUT "Chequeando [$dir]\n"
		&procesar_directorio("$DOCUMENT_ROOT$dir");
	}
}

# -----------------------------------------------------------------------------
sub procesar_directorio {

	my $dir = shift;
	next unless(-d $dir);

	opendir(my $dh, $dir) || die;
    while(readdir $dh) {
    	my $archivo = $_;
    	next unless(-f "$dir/$archivo");

    	next unless($archivo =~ /(\.cgi|\.pl)$/);
        my $check = `perl -c "$dir/$archivo" 2>&1`;
        if($check !~ /syntax OK/) {
        	print "Error de Sintaxis [$dir/$archivo]\n";
        	print "Respuesta[$check]\n-----------------------------\n";
        }
    }
}