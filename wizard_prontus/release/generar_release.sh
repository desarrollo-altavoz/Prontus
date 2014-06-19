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
# Ve si el modelo debe ser actualizado o no
function check_modelo_actualizado {

    modelo=$1
    modelosactual="$BASEDIR/wizard_prontus/models"
    rutamodelo="$modelosactual/$modelo"
    
    # Si el directoio no existe, nada que hacer
    if [ ! -d "$rutamodelo" ] ; then
        echo "0"
        return
    fi

    # Se chequea si el modelo ya está actualizado
    if [ ! -f "$rutamodelo" ] ; then
        urlmodelo="$URLPRONTUS/$modelo"
        wget -nv "$urlmodelo/$modelo.cfg" -O "$rutamodelo/$modelo-new.cfg";
        
        version1=$(cat $rutamodelo/$modelo.cfg | grep -e 'MODELO_VERSION' | grep -o "[0-9\.]*")
        version2=$(cat $rutamodelo/$modelo-new.cfg | grep -e 'MODELO_VERSION' | grep -o "[0-9\.]*")
        rm "$rutamodelo/$modelo-new.cfg"
        if [ "$version1" == "$version2" ] ; then
            echo "1"
        else 
            echo "0"   
        fi

    else
        echo 0;
    fi
}

#----------------------------------------------------
#Trae los modelos del server publico de prontus
function traerModelo {

    modelo=$1;

    modelosactual="$BASEDIR/wizard_prontus/models"
    rutamodelo="$modelosactual/$modelo"
    urlmodelo="$URLPRONTUS/$modelo"

    resp=$(check_modelo_actualizado $modelo)
    
    # Si la respuesta es cero, se debe descargar el modelo
    if [ "$resp" == "0" ] ; then
        echo "Modelo [$modelo] desactualizado";
        echo "Limpiando y descargando en: $rutamodelo";

        limpiarDirectorio "$rutamodelo"
        wget -nv "$urlmodelo/$modelo.cfg" -O "$rutamodelo/$modelo.cfg";
        wget -nv "$urlmodelo/$modelo-big.png" -O "$rutamodelo/$modelo-big.png";
        wget -nv "$urlmodelo/$modelo-thumb.png" -O "$rutamodelo/$modelo-thumb.png";
        wget -nv "$urlmodelo/$modelo.tgz.md5" -O "$rutamodelo/$modelo.tgz.md5";
        wget -nv "$urlmodelo/$modelo.tgz" -O "$rutamodelo/$modelo.tgz";
        wget -nv "$urlmodelo/release_notes.txt" -O "$rutamodelo/release_notes.txt";

        # Se lee el md5 del modelo descargado
        md5a=$(cat $rutamodelo/$modelo.tgz.md5)
        md5a=`expr match "$md5a" '.*= \([a-z0-9]*\)'`

        # Se calcula el md5 del archivo tgz
        cd $rutamodelo    
        if [ -x /sbin/md5 ] ; then
            md5b=`/sbin/md5 "$modelo.tgz"`
        else
            md5b=`/usr/bin/openssl dgst -md5 "$modelo.tgz"`
        fi
        md5b=`expr match "$md5b" '.*= \([a-z0-9]*\)'`

        # Se comparan los md5 a ver si coinciden
        if [ "$md5a" == "$md5b" ] ; then
            echo "Modelo descargado correctamente"
            tar xfz "$rutamodelo/$modelo.tgz" -C "$rutamodelo"
            rm -rf "$modelo.tgz"
            rm -rf "$modelo.tgz.md5"
        else
            echo "Modelo con errores, se borra lo descargado"
            echo "[$md5a] [$md5b]"
            rm -rf "$rutamodelo"
            return
        fi
    else
        echo "Modelo [$modelo] actualizado no se descarga";
    fi

    # Si todo sale bien con la descarga, copiamos el modelo
    rutamodelos="$RELEASEPATH/wizard_prontus/models"
    if [ ! -d "$rutamodelos" ] ; then
        mkdir -p "$rutamodelos"
    fi
    echo "Copiando [$rutamodelo] hacia [$rutamodelos]"
    cp -rf "$rutamodelo" "$rutamodelos"


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
BASEDIRTEMP="$RELEASEPATH/temporal"
URLPRONTUS="http://www.prontus.cl/release/models/"

#~ Se verifica directorio de destino.
limpiarDirectorio "$RELEASEPATH"

#~ Copiando archivos para comprimir
echo "Copiando archivos para comprimir"
cd $BASEDIR
mkdir $BASEDIRTEMP
cd $BASEDIRTEMP
cp -rf "$BASEDIR/cgi-bin" .
cp -rf "$BASEDIR/cgi-cpn" .
mkdir "$BASEDIRTEMP/wizard_prontus"
cp -rf "$BASEDIR/wizard_prontus/core" "$BASEDIRTEMP/wizard_prontus"
mkdir "$BASEDIRTEMP/wizard_prontus/prontus_dir"
mkdir "$BASEDIRTEMP/wizard_prontus/prontus_dir/cpan"
cp -rf "$BASEDIR/wizard_prontus/prontus_dir/cpan/core" "$BASEDIRTEMP/wizard_prontus/prontus_dir/cpan"
rm -rf "$BASEDIRTEMP/cgi-bin/prontus_error_log" "$BASEDIRTEMP/cgi-bin/prontus_temp"
rm -rf "$BASEDIRTEMP/cgi-bin/encuesta"
rm -rf "$BASEDIRTEMP/cgi-cpn/coment/prontus_error_log" "$BASEDIRTEMP/cgi-cpn/coment/prontus_temp"
rm -rf "$BASEDIRTEMP/cgi-cpn/dam/prontus_error_log" "$BASEDIRTEMP/cgi-cpn/dam/prontus_temp"
rm -rf "$BASEDIRTEMP/cgi-cpn/xcoding/prontus_error_log" "$BASEDIRTEMP/cgi-cpn/xcoding/prontus_temp"
rm -rf "$BASEDIRTEMP/cgi-cpn/prontus_error_log" "$BASEDIRTEMP/cgi-cpn/prontus_temp"
rm -rf "$BASEDIRTEMP/cgi-cpn/pproc"
rm -rf "$BASEDIRTEMP/cgi-cpn/encuesta"
rm -rf "$BASEDIRTEMP/cgi-cpn/develop"

#~ Se copia el change_log.txt al core del prontus
if [ ! -d "$BASEDIRTEMP/wizard_prontus/prontus_dir/cpan/core/version" ] ; then
    mkdir "$BASEDIRTEMP/wizard_prontus/prontus_dir/cpan/core/version"
fi
cp "$BASEDIR/wizard_prontus/release/change_log.txt"  "$BASEDIRTEMP/wizard_prontus/prontus_dir/cpan/core/version/change_log.txt"

#~ Generando el TGZ para el update de Prontus
echo "Generando archivo tgz en: $RELEASEPATH/files.$release.tgz"
cd $BASEDIRTEMP
tar czf "$RELEASEPATH/files.$release.tgz" . \
        --exclude=*.orig
rm -rf "$BASEDIRTEMP"

#~ Generando md5 del TGZ
echo "Generando md5"
cd $RELEASEPATH
if [ -x /sbin/md5 ] ; then
    /sbin/md5 "files.$release.tgz" > "$RELEASEPATH/files.$release.tgz.md5"
else
    /usr/bin/openssl dgst -md5 "files.$release.tgz" > "$RELEASEPATH/files.$release.tgz.md5"
fi

#~ Copiando TXTs del change_log y del release_notes
echo "Copiando change_log y release_notes"
cp "$BASEDIR/wizard_prontus/release/change_log.txt" "$RELEASEPATH/change_log.txt"
cp "$BASEDIR/wizard_prontus/release/release_notes.txt" "$RELEASEPATH/release_notes.txt"

#~ Creando el descriptor de la release
echo "Creando archivo last.11.2.txt"
echo "$release - $fecha" > "last.$rama.txt"

#~ Se descomprime el directorio y se copian algunos archivos
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
