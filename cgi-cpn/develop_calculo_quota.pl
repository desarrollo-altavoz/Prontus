#!/usr/bin/perl

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO .
# -----------
# Script de ejemplo para el calculo custom de quota
# Para evitar errores innecesarios en los error logs
#
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Ninguna
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# Ninguna
#
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

my $LIMITE_QUOTA = '2684354560';

main: {

    #~ my $df = `df -T | grep -v tmpfs`;
    #~ if($df =~ /ext3\s+\d+\s+(\d+)\s+(\d+)\s+(\d+)%\s+\/var\/www/) {
        #~ $usado = $1;
        #~ $quota_asig = $LIMITE_QUOTA;
    #~
    #~ } elsif($df =~ /simfs\s+.*?\s+\d+\s+(\d+)\s+(\d+)\s+(\d+)\%\s+/s) {
        #~ $usado = $1;
        #~ $quota_asig = $LIMITE_QUOTA;
    #~
    #~ } else {
        #~ print STDERR "procesa_quota_vps[Bad df: $df]\n";
        #~ exit;
    #~ }
    print "500000|1200000";
};



