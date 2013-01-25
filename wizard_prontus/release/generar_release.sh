#!/bin/sh

#~ A futuro, leer esto desde el prontus_varglb.pm
echo "Ingrese la release (ej: 11.2.31):"
read -r release

if [ "$release" = "" ] ; then
    echo "Debe especificar una release"
    exit
fi

SCRIPT=`readlink -f $0`
SCRIPTPATH=`dirname $SCRIPT`
SCRIPTPATH=`dirname $SCRIPTPATH`
BASEDIR=`dirname $SCRIPTPATH`
RELEASEPATH="$BASEDIR/release"

if [ ! -d "$RELEASEPATH" ] ; then
    mkdir "$RELEASEPATH";
else
    rm -rf "$RELEASEPATH/*";
fi

echo "Generando archivo tgz"
cd $BASEDIR
tar czf "$RELEASEPATH/files.$release.tgz" \
	--exclude=*.log \
	--exclude=cgi-cpn/develop_calculo_quota.pl \
	--exclude=*.orig \
	cgi-bin/ \
	cgi-cpn/ \
	wizard_prontus/core/ \
	wizard_prontus/prontus_dir/cpan/core/
	
echo "Generando md5"
cd $RELEASEPATH
if [ -x /sbin/md5 ] ; then
    /sbin/md5 "files.$release.tgz" > "$RELEASEPATH/files.$release.tgz.md5"
else
    /usr/bin/openssl dgst -md5 "files.$release.tgz" > "$RELEASEPATH/files.$release.tgz.md5"
fi

#~ Por ahora no se distribuiran mas los modelos
#~ if [ ! -f "models.$release.tgz" ] ; then
    #~ echo "Generando modelos"
    #~ tar czf "models.$release.tgz" wizard_prontus/models wizard_prontus/models_lib
#~ fi

echo "Archivos generados ok"
