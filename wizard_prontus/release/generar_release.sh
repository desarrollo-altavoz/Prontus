#!/bin/bash

#~ ----------------------------------------------------
#~ Se verifica directorio de destino. Si ya existe, se hace limpieza
function limpiarDirectorio {
    dir=$1
    if [ ! -d "$dir" ] ; then
        #~ echo "Creando directorio release"
        mkdir "$dir"
    else
        #~ echo "Borrando contenido anterior"
        rm -rf "$dir"
        mkdir "$dir"
    fi
}

#----------------------------------------------------
#Trae los modelos del server publico de prontus
function traerModelo {
    modelo=$1;
    url="http://www.prontus.cl/release/models/"
    
    rutamodelos="$RELEASEPATH/wizard_prontus/modelos"
    if [ ! -d "$rutamodelos" ] ; then
        mkdir "$rutamodelos"
    fi
    
    rutamodelo="$rutamodelos/$modelo"
    limpiarDirectorio "$rutamodelo"
    urlmodelo="$url/$modelo"
    
    limpiarDirectorio "$rutamodelo"
    wget -nv "$urlmodelo/$modelo.cfg" -O "$rutamodelo/$modelo.cfg";
    wget -nv "$urlmodelo/$modelo-big.png" -O "$rutamodelo/$modelo-big.png";
    wget -nv "$urlmodelo/$modelo-thumb.png" -O "$rutamodelo/$modelo-thumb.png";
    wget -nv "$urlmodelo/$modelo.tgz.md5" -O "$rutamodelo/$modelo.tgz.md5";
    wget -nv "$urlmodelo/$modelo.tgz" -O "$rutamodelo/$modelo.tgz";
    wget -nv "$urlmodelo/release_notes.txt" -O "$rutamodelo/release_notes.txt";
    
    md5a=$(cat $rutamodelo/$modelo.tgz.md5)
    md5a=`expr match "$md5a" '.*= \([a-z0-9]*\)'`
    
    cd $rutamodelo
    if [ -x /sbin/md5 ] ; then
        md5b=`/sbin/md5 "$modelo.tgz"`
    else
        md5b=`/usr/bin/openssl dgst -md5 "$modelo.tgz"`
    fi
    md5b=`expr match "$md5b" '.*= \([a-z0-9]*\)'`
    
    if [ "$md5a" == "$md5b" ] 
    then
        echo "Modelo descargado correctamente"
        tar xfz "$rutamodelo/$modelo.tgz" -C "$rutamodelo"
        rm -rf "$modelo.tgz"
        rm -rf "$modelo.tgz.md5"
    else
        echo "Modelo con errores, se borra lo descargado"
        echo "[$md5a] [$md5b]"
        rm -rf "$rutamodelo"
    fi
}


#~ A futuro, leer esto desde el prontus_varglb.pm
echo "Ingrese la release (ej: 11.2.31):"
read -r release
fecha=$(date +"%d/%m/%Y");
rama=`expr match "$release" '\([0-9]*\.[0-9]*\)\.[0-9]*'`

if [ "$release" = "" ] ; then
    echo "Debe especificar una release"
    exit
fi

#~ Se definen las rutas a utilizar
SCRIPT=`readlink -f $0`
SCRIPTPATH=`dirname $SCRIPT`
SCRIPTPATH=`dirname $SCRIPTPATH`
BASEDIR=`dirname $SCRIPTPATH`
RELEASEPATH="$BASEDIR/release"

#~ Se verifica directorio de destino.
limpiarDirectorio "$RELEASEPATH"

#~ Generando el TGZ
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
    
#~ Generando md5
echo "Generando md5"
cd $RELEASEPATH
if [ -x /sbin/md5 ] ; then
    /sbin/md5 "files.$release.tgz" > "$RELEASEPATH/files.$release.tgz.md5"
else
    /usr/bin/openssl dgst -md5 "files.$release.tgz" > "$RELEASEPATH/files.$release.tgz.md5"
fi

#~ Generando copiando TXTs
echo "Copiando change_log y release_notes"
cp "$BASEDIR/wizard_prontus/release/change_log.txt" "$RELEASEPATH/change_log.txt"
cp "$BASEDIR/wizard_prontus/release/release_notes.txt" "$RELEASEPATH/release_notes.txt"
echo "Creando archivo last.11.2.txt"
echo "$release - $fecha" > "last.$rama.txt"

#~ Se descomprime el directorio y se copia algunos archivos
tar xfz "$RELEASEPATH/files.$release.tgz" -C "$RELEASEPATH"
cp "$BASEDIR/wizard_prontus/dir_cgi.js" "$RELEASEPATH/wizard_prontus/dir_cgi.js"
cp "$BASEDIR/wizard_prontus/index.html" "$RELEASEPATH/wizard_prontus/index.html"

#~ Se traen los modelos
traerModelo "modelo_minimo"
traerModelo "modelo_productos"
traerModelo "modelo_simple"
traerModelo "modelo_vacio"

#~ Finalmente se comprime todo y se deja dentro de release
cd $RELEASEPATH 
tar czf "$BASEDIR/release.$release.tgz" *
mv "$RELEASEPATH" "$BASEDIR/backup"
limpiarDirectorio "$RELEASEPATH"
mv "$BASEDIR/backup" "$RELEASEPATH"
mv "$BASEDIR/release.$release.tgz" "$RELEASEPATH"

echo "Archivos generados ok"
echo "El archivo generado de encuentra en:"
echo "$RELEASEPATH/release.$release.tgz"
