// -----------------------------------------------------------
// Para que los subtitulos no queden debajo de la barra.
  function escrol(estop) {
    setTimeout("window.scrollBy(0,-30)",500);
    window.location = estop;
  };



// Script para efecto onMouseOver.
var BROWSER_VALIDO = false;
// alert(navigator.appName + ' ' + parseInt(navigator.appVersion) + ' ' + navigator.userAgent + ' ' + navigator.userAgent.indexOf('MSIE 5'));
if ( (navigator.appName == "Netscape") || (navigator.appName == "Microsoft Internet Explorer") ) {
	if ( (parseInt(navigator.appVersion) >= 5) || (navigator.userAgent.indexOf('MSIE 5') > 0) || (navigator.userAgent.indexOf('MSIE 6') > 0) ) {
	  BROWSER_VALIDO = true;
	};
};


  var verok = 1; //version adecuada del navigator.
  browserName = navigator.appName;
  browserVer = parseInt(navigator.appVersion);
  if ((browserName == "Netscape" && browserVer >= 3)
     || (browserName == "Microsoft Internet Explorer" && browserVer >= 4) ) {
    verok = 1;
  } else {
    verok = 0;
  };

  var path    = '/wizard_prontus/core/imag/';
  var imagidx = 'none'; // Imagen inicialmente seleccionada.
  var img_portada = 'none'; // Imagen de la portada.

  function findIMG(nom) {
    var i;
//    if (parent.headdrs.document[nom]) { // Comentado por MCO.
//      return parent.headdrs.document[nom];
//    };
    if (document[nom]) {
      return document[nom];
    };
    if (document.layers) {
      for(i=0; i < document.layers.length; i++) {
        // alert('entro find ' + eval('document.bodyNode.document.' + nom.substring(1, nom.length) + '.document.' + nom + '.src') + ' ' + nom);
        if (document.layers[i].document[nom]) {
          return document.layers[i].document[nom];
        }
        else if (eval('document.bodyNode.document.' + nom.substring(1, nom.length) + '.document.' + nom)) {
          return eval('document.bodyNode.document.' + nom.substring(1, nom.length) + '.document.' + nom);
        };
      };
    }
    else{
      if (document.all) {if (document.all[nom]) { return document.all[nom]; }; };
      if (document.getElementById(nom)) { return document.getElementById(nom); };
    };
  }; // findIMG

  function ima_ck(nom, dir) {
    var aux = imagidx;
    imagidx = nom;
    ima_of(aux, dir);
    ima_on(imagidx, dir);
    return true;
  };

  function ima_on(nom, dir, tipo) {
    var x;
    if ((verok == 1) && (nom != 'none') && (nom != imagidx)) {
      x = findIMG(nom);
      if (x) {
        x.src = '';
        if (tipo) {
          x.src = path + dir + '/'+ tipo + '_on.gif';
        }
        else {
          x.src = path + dir + '/'+ nom + '_on.gif';
        };
        
        return true;
      };
    };
  };

  function ima_ac(nom, dir) {
    var x;

    if ((verok == 1) && (nom != 'none')) {
      x = findIMG(nom);
      if (x) {
        nom = nom.substring(0, 2) + 1;
        x.src = path + dir + '/'+ nom + '_on.gif';

        return true;
      };
    };
  };

  function ima_of(nom, dir, tipo) {
    var x;
    if ((verok == 1) && (imagidx != nom) && (nom != 'none')) {
      x = findIMG(nom);
      if (x) {
        // Para que quede la portada actual con el boton activo. Se configura al final de la portada antes de la funcion
        // initialize().
        // Ejemplo (portada.html):
        // top.parent.headdrs.img_portada = 'po1';
        
        // top.parent.headdrs.ima_of('opi', 'head');
        // top.parent.headdrs.ima_of('cro', 'head');
        // top.parent.headdrs.ima_of('eco', 'head');
        // top.parent.headdrs.ima_of('dep', 'head');
        // top.parent.headdrs.ima_of('esp', 'head');
        // top.parent.headdrs.ima_of('rep', 'head');
        // top.parent.headdrs.ima_of('elm', 'head');
        
        // top.parent.headdrs.ima_ac('por', 'head');
        
        if (img_portada.substring(0, 2) == nom.substring(0, 2)) {
          x.src = path + dir + '/'+ img_portada + '_on.gif';
        }
        else {
          if (tipo) {
            x.src = path + dir + '/'+ tipo + '_of.gif';
          }
          else {
            x.src = path + dir + '/'+ nom + '_of.gif';
          };
        };
        
        return true;
      };
    };
  };

// funcion para ventana pop-up con scroll.

  function subWin(loc, nom, ancho, alto, posx, posy) {
    var options="toolbar=0,status=0,menubar=0,scrollbars=1,resizable=0,location=0,directories=0,width=" + ancho + ",height=" + alto + ",left=" + posx + ",top=" + posy + ",screenX=" + posx + ",screenY=" + posy;

    window.name = 'top';
    var win = window.open(loc,nom,options);
    win.focus();
    // win.moveTo(posx, posy);
  };

// -----------------------------------------------------------
// Script para ventana popup sin scroll.
function subWin2(loc, nom, ancho, alto, posx, posy) {
  var options="toolbar=0,status=0,menubar=0,scrollbars=0,resizable=0,location=0,directories=0,width=" + ancho + ",height=" + alto + ",left=" + posx + ",top=" + posy + ",screenX=" + posx + ",screenY=" + posy;

  var win = window.open(loc, nom, options);
  win.focus();
  if ( (posx > 0) && (posy > 0) ) {
    // win.moveTo(posx, posy);
  };
};
  
