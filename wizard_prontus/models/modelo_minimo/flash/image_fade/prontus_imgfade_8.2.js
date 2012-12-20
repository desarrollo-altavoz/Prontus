// Historia de versiones.
// 2.0 - 02/05/2003 - Permite reconocer url para extraer de ahi la identificacion del articulo.
// 2.1 - 16/03/2004 - Linkea cualquier extension, no solo .html.
// 4.0 - 01/06/2004 - Acepta el url del articulo mediante FlashVars.
//                    La variable es urlartic.
// 4.1 - 01/09/2004 - Sustituye onLoad por un if, ya que con la version 7 del
//                    plug in esto dejo de funcionar.
// 5.0 - 03/12/2004 - Agrega parametros "nolink" y "target".
//                    nolink=1 => no linkea los articulos. target = el target a usar.
// 6.0 - 13/02/2005 - Agrega el parametro "linkurl", que permite linkear a un url arbitrario.
// 7.0 - 20/02/2005 - Compatibiliza con Prontus X. Acepta los parametros fotoi (i=1..4).
//                  - En modalidad Prontus X acepta una cantidad de fotos < 4.
// 8.0 - 19/04/2005 - Cambia cursor de layer "button" si no hay link.
// 8.1 - 31/07/2007 - Agrega variable para controlar el tiempo que dura expuesta cada foto.

var maxfotos = 4;
var newmaxfotos = maxfotos; // 7.0
var intervalo = 100; // 8.1 Valor por defecto.
if (showsecs != null) {
  intervalo = 10 * showsecs; // 8.1 showsecs es la variable del flashvars.
};
var	baseurl, ts, theurl, extension, tiempo, nolinkear, eltarget;
var index;  // Foto actual.
var index2; // Indice de la proxima foto.
var adjusted = new Array(maxfotos + 1); // Arreglo de flags para el ajuste de tamaño de las imagenes.
var fotos = new Array(maxfotos + 1); // 7.0 Arreglo de fotos.
var started = false;
var initialized = false; // 4.1

// 4.1 this.onLoad = function() {
if (not initialized) { // 4.1
	tiempo = 11; // Para partir con una foto estatica.
	if (urlartic != null) { // 4.0
		theurl = urlartic; // 4.0
	}else{
		theurl = this._url;
	};
	if (nolink != null) { // 5.0
		nolinkear = true; // 5.0
		overallinstance.useHandCursor = false; // 8.0
	}else{
		nolinkear = false;
	};
	if (target != null) { // 5.0
		eltarget = target; // 5.0
	}else{
		eltarget = '_self';
	};
	if (foto1 != null) { // 7.0 !!! Hay que parametrizar esto !!!
	  fotos[1] = foto1;
	  fotos[2] = foto2;
	  fotos[3] = foto3;
	  fotos[4] = foto4;
	};
	ts = getSWFTimeStamp(theurl);
	baseurl = getSWFbaseurl(theurl);
	extension = getSWFExtension(theurl); // 2.1
	// txtdebug = ts + ' * ' + baseurl; // debug
	// Crea maxfotos instancias de la costion, e intenta cargar las fotos correspondientes.
	adjusted[0] = false;
	for (i=1; i<=maxfotos; i++) {
		duplicateMovieClip(picHolderInstance, 'picHolderInstance' + i, i);
		// setProperty('picHolderInstance' + i, _x,0);
		// setProperty('picHolderInstance' + i, _y,0);
		if (foto1 != null) { // 7.0
		  if ((fotos[i] != '') && (fotos[i].indexOf('/site/artic') > 0)) { // Verifica que las fotos provengan de Prontus.
	      loadMovie(fotos[i], 'picHolderInstance' + i);
	    }else{
	      newmaxfotos = i - 1; // 7.0
	    };
		}else{
	    loadMovie(baseurl + '../imag/foto' + i + ts + '.jpg', 'picHolderInstance' + i);
	  };
		adjusted[i] = false;
	};
	// Setea el alpha en 0 para todas las fotos.
	for (i=1; i<=maxfotos; i++) {
		setProperty("picHolderInstance" + i, _alpha,0);
	};
	// Inicializa indice de la foto actual.
	index = 1;
	initialized = true;
	maxfotos = newmaxfotos;
}; // 4.1 if (not initialized) // this.onLoad = function()

this.onEnterFrame = function() {
  if (not initialized) { return; }; // 4.1
	// return; // debug
	var counter;
	var i;
	if ( (tiempo == 0) or (not started) ) {
    // Confirma foto actual y busca la siguiente.
  	counter = 0;
  	while ((getProperty("picHolderInstance" + index,_height) == 0) && (counter <= maxfotos)) {
	  	counter++;
			index++;
			if (index > maxfotos) { index = 1; };
	  };
  	counter = 0;
		i = index + 1;
		if (i > maxfotos) { i = 1; };
  	while ((getProperty("picHolderInstance" + i,_height) == 0) && (counter <= maxfotos)) {
	  	counter++;
			i++;
			if (i > maxfotos) { i = 1; };
	  };
  	index2 = i;
		// Ajusta tamaños.
		sizeadjust(index);
		sizeadjust(index2);
	};
	// Aplica slope alpha para transición suave.
	if (tiempo < 10) {
	// Si la actual es la misma que la siguiente, o no hay fotos, no hace nada.
		if ((index != index2) && (counter <= maxfotos)) {
	    if (adjusted[index]) { setProperty('picHolderInstance' + index, _alpha,100 - tiempo * 10); };
		  if (adjusted[index2]) { setProperty('picHolderInstance' + index2, _alpha,tiempo * 10); };
		};
	};
	// Fin de la transición.
	if (tiempo == 10) {
	// Si la actual es la misma que la siguiente, o no hay fotos, no hace nada.
		if ((index != index2) && (counter <= maxfotos)) {
			if ( adjusted[index] && adjusted[index2] ) {
		    setProperty('picHolderInstance' + index, _alpha,0);
			  setProperty('picHolderInstance' + index2, _alpha,100);
	    	index = index2; // Asigna nueva foto actual.
			};
		};
  };
	// Visibilización de la imagen que debe verse (esto para la primera vez).
	if (tiempo > 10) {
		if ( (adjusted[index]) && (not started) ) {
	    setProperty('picHolderInstance' + index, _alpha,100);
	    started = true;
		};
  };
	tiempo++;
	if (tiempo == intervalo) { tiempo = 0; };
}; // this.onEnterFrame = function()

this.onMouseUp = function() {
  if (nolinkear) { return; }; // 5.0
  if (not initialized) { return; }; // 4.1
	// 2.1 getURL(baseurl + '../pags/' + ts + '.html','_self');
	// 5.0 getURL(baseurl + '../pags/' + ts + extension,'_self');
	if (linkurl != null) { // 6.0
	  getURL(linkurl,eltarget);
	}else{
	  getURL(baseurl + '../pags/' + ts + extension,eltarget);
	};
}; // this.onMouseUp = function()

// Ajusta el tamaño de las imágenes.
function sizeadjust(i) {
	var elholder,ancho,alto,anchof,altof,escala;
	if (adjusted[i]) { return true; }; // No hace nada si ya ajustó el tamaño.
	setProperty("picHolderInstance" + i, _xscale,100);
	setProperty("picHolderInstance" + i, _yscale,100);
	elholder = eval("picHolderInstance" + i);
	if ( (elholder._height > 0) && (elholder._width > 0) && (elholder.getBytesLoaded() == elholder.getBytesTotal()) && (elholder.getBytesLoaded() > 100) ) {
   	// Ajusta tamaño de la imagen detectada.
    ancho = elholder._width;
		alto = elholder._height;
    anchof = 200 / ancho; // 200 es porque el ancho original son 200 pixeles.
		altof = 200 / alto;
		// Escoge el lado que tiene mayor escalamiento para llenar el canvas del flash.
		if (anchof > altof) {
  		escala = anchof;
		}else{
			escala = altof;
		};
		setProperty('picHolderInstance' + i, _width,elholder._width * escala);
		setProperty('picHolderInstance' + i, _height,elholder._height * escala);
		setProperty('picHolderInstance' + i, _x,(200 - ancho * escala)/2);
		setProperty('picHolderInstance' + i, _y,(200 - alto * escala)/2);
		adjusted[i] = true;
		return true;
	}else{
		return false;
	};
}; // sizeadjust

// Obtiene el timestamp deduciendolo del url del archivo Flash.
function getSWFTimeStamp(theurl) {
	var dotpos;
	// var lastslash;
	var timestamp;
	// ?/prontus_demo/site/artic/20030408/pags/20030408145800.html
	// lastslash = theurl.lastIndexOf('/');
	dotpos = theurl.lastIndexOf('.');
	timestamp = theurl.substring(dotpos - 14, dotpos);
	return timestamp;
}; // getSWFTimeStamp

// Obtiene el URL base deduciendolo del url del archivo Flash.
function getSWFbaseurl(theurl) {
	var baseurl;
	var lastslash;
	var questionmark;
	if (theurl.indexOf('prontus_imgfade') > 0) {
		// Se esta usando en ubicacion fija.
		// ?/prontus_demo/site/artic/20030408/pags/20030408145800.html
		questionmark = theurl.lastIndexOf('?');
		lastslash = theurl.lastIndexOf('/');
		baseurl = theurl.substring(questionmark + 1,lastslash + 1);
	}else{
		// Se esta usando en ubicacion variable.
		lastslash = theurl.lastIndexOf('/');
		baseurl = theurl.substr(0, lastslash + 1);
	};
	return baseurl;
}; // getSWFTimeStamp

// 2.1 Obtiene la extension de un URL.
function getSWFExtension(theurl) {
	var extension;
	var lastdot;
	lastdot = theurl.lastIndexOf('.');
	extension = theurl.substr(lastdot);
	return extension;
}; // getSWFExtension
