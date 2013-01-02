#!/bin/sh

echo "Ingrese la release (ej: 11.2.31):"
read -r release

if [ "$release" = "" ] ; then
    echo "Debe especificar una release"
    exit
fi

cd "prontus.$release/"

echo "Generando archivo tgz"
tar czf "files.$release.tgz"  cgi-bin/ cgi-cpn/ wizard_prontus/core/ wizard_prontus/prontus_dir/cpan/core/

echo "Generando md5"
/sbin/md5 "files.$release.tgz" > "files.$release.tgz.md5"

if [ ! -f "models.$release.tgz" ] ; then
    echo "Generando modelos"
    tar czf "models.$release.tgz" wizard_prontus/models wizard_prontus/models_lib
fi

echo "Archivos generados ok"
