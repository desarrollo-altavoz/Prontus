// ------------- Manipulacion del cambio de imagen de articulo ---------------

var verok = 1; //version adecuada del navigator.

browserName = navigator.appName;
browserVer = parseInt(navigator.appVersion);
if ((browserName == "Netscape" && browserVer >= 3)
   || (browserName == "Microsoft Internet Explorer" && browserVer >= 4) ) {
  verok = 1;
} else {
  verok = 0;
};


// Precarga las imagenes.
if (verok == 1) {

  // Define los identificadores de las imagenes.
  // *** Aqui debes colocar los prefijos de las imagenes que usaras
  // en el menu.
  botID = new Array('tipart');
  var imagidx = 'tipart'; // Imagen inicialmente seleccionada.

  // Define el path (relativo) donde se encuentran las imagenes.
  // *** Aqui debes colocar el directorio donde se encuentran las imagenes,
  // relativo al lugar donde se encuentra esta pagina.
  var path = '../wizard_prontus/imag/';

  // Define y carga las imagenes correspondientes a los estados de
  // los botones.
  for (var i=0;i<botID.length;i++) {
    eval(botID[i] + '_fotoleft_recright = new Image()');
    eval(botID[i] + '_fotoleft_recright.src = "' + path + botID[i] + '_fotoleft_recright.gif"');

    eval(botID[i] + '_fotocenter_recright = new Image()');
    eval(botID[i] + '_fotocenter_recright.src = "' + path + botID[i] + '_fotocenter_recright.gif"');

    eval(botID[i] + '_fotoright_recright = new Image()');
    eval(botID[i] + '_fotoright_recright.src = "' + path + botID[i] + '_fotoright_recright.gif"');



    eval(botID[i] + '_fotoleft_recbottom = new Image()');
    eval(botID[i] + '_fotoleft_recbottom.src = "' + path + botID[i] + '_fotoleft_recbottom.gif"');

    eval(botID[i] + '_fotocenter_recbottom = new Image()');
    eval(botID[i] + '_fotocenter_recbottom.src = "' + path + botID[i] + '_fotocenter_recbottom.gif"');

    eval(botID[i] + '_fotoright_recbottom = new Image()');
    eval(botID[i] + '_fotoright_recbottom.src = "' + path + botID[i] + '_fotoright_recbottom.gif"');



    eval(botID[i] + '_sinfoto_recbottom = new Image()');
    eval(botID[i] + '_sinfoto_recbottom.src = "' + path + botID[i] + '_sinfoto_recbottom.gif"');

    eval(botID[i] + '_sinfoto_recright = new Image()');
    eval(botID[i] + '_sinfoto_recright.src = "' + path + botID[i] + '_sinfoto_recright.gif"');

    eval(botID[i] + '_sinfoto_sinrec = new Image()');
    eval(botID[i] + '_sinfoto_sinrec.src = "' + path + botID[i] + '_sinfoto_sinrec.gif"');

  };


};

// -----------------------------------------------------------------
function cambia_img(nom, imagen) {
  var imgOn = eval(nom + "_" + imagen + ".src");
  document[nom].src = imgOn;
};

// -----------------------------------------------------------------
function check_estructura_recuadro() {
  if ( (window.document.form1.Chk_TITREC.status) || (window.document.form1.Chk_TEXTOREC.status) ) {
    if (window.document.form1.ESTRUCTURA.value == 'sinfoto_sinrec') {
      alert("La estructura de artículo seleccionada no soporta Recuadro.");
      window.document.form1.Chk_TITREC.status = false;
      window.document.form1.Chk_TEXTOREC.status = false;
    };
  };
};

// -----------------------------------------------------------------
function check_estructura_fotoart() {
  if (window.document.form1.Chk_FOTOART.status) {
    if  (  (window.document.form1.ESTRUCTURA.value == 'sinfoto_sinrec')
        || (window.document.form1.ESTRUCTURA.value == 'sinfoto_recright')
        || (window.document.form1.ESTRUCTURA.value == 'sinfoto_recbottom') ) {
      alert("La estructura de artículo seleccionada no soporta Foto.");
      window.document.form1.Chk_FOTOART.status = false;
    };
  };
};
// -----------------------------------------------------------------

function aceptavalor(valor) {
  // Devuelve valor de la ventana popup de sel. de estructura de articulo.
  window.document.form1.ESTRUCTURA.value = valor;

  // Cambia la imagen ilustrativa
  cambia_img('tipart', valor);
  check_estructura_recuadro();
  check_estructura_fotoart();
};

// -----------------------------------------------------------------

function valida_campos() {
  var expr;
  var found;
  var result;

  expr = /^[a-z][a-z0-9\_]+$/;
  found = expr.exec(window.document.form1.NOMART.value);
  if (! found) {
    alert('Nombre de artículo no válido. Debe comenzar con letra minúscula seguida de letras minúsculas o números o _.');
    window.document.form1.NOMART.focus();
    window.document.form1.NOMART.select();
    return false;
  };


  if (window.document.form1.ESTRUCTURA.value == '') {
    alert('Estructura de artículo no válida.');
    window.document.form1.Bot_ACCION.focus();
    return false;
  };

  // Campos adicionales ----------------------------------------------------

  // Dejar en blanco los no chequeados.
  if (window.document.form1.Chk_OTROSCAMPOS1.status == false) {
    window.document.form1.NOM_OTROSCAMPOS1.value = '';
  };
  if (window.document.form1.Chk_OTROSCAMPOS2.status == false) {
    window.document.form1.NOM_OTROSCAMPOS2.value = '';
  };
  if (window.document.form1.Chk_OTROSCAMPOS3.status == false) {
    window.document.form1.NOM_OTROSCAMPOS3.value = '';
  };


  // Validar Nombres repetidos
  if ( (window.document.form1.NOM_OTROSCAMPOS1.value != '') && (window.document.form1.NOM_OTROSCAMPOS1.value == window.document.form1.NOM_OTROSCAMPOS2.value) ) {
    alert('Nombre de campo repetido.');
    window.document.form1.NOM_OTROSCAMPOS2.focus();
    window.document.form1.NOM_OTROSCAMPOS2.select();
    return false;
  };
  if ( (window.document.form1.NOM_OTROSCAMPOS1.value != '') && (window.document.form1.NOM_OTROSCAMPOS1.value == window.document.form1.NOM_OTROSCAMPOS3.value) ) {
    alert('Nombre de campo repetido.');
    window.document.form1.NOM_OTROSCAMPOS3.focus();
    window.document.form1.NOM_OTROSCAMPOS3.select();
    return false;
  };
  if ( (window.document.form1.NOM_OTROSCAMPOS2.value != '') && (window.document.form1.NOM_OTROSCAMPOS2.value == window.document.form1.NOM_OTROSCAMPOS3.value) ) {
    alert('Nombre de campo repetido.');
    window.document.form1.NOM_OTROSCAMPOS3.focus();
    window.document.form1.NOM_OTROSCAMPOS3.select();
    return false;
  };


  // Validacion tipografica de los que esten chequeados

  result = valida_campo(window.document.form1.Chk_OTROSCAMPOS1, window.document.form1.NOM_OTROSCAMPOS1);
  if (result == false) {
    return false;
  };
  result = valida_campo(window.document.form1.Chk_OTROSCAMPOS2, window.document.form1.NOM_OTROSCAMPOS2);
  if (result == false) {
    return false;
  };
  result = valida_campo(window.document.form1.Chk_OTROSCAMPOS3, window.document.form1.NOM_OTROSCAMPOS3)
  if (result == false) {
    return false;
  };

  // Fin Campos de texto adicionales ------------------------------------------------

  // IMAGENES
  if (window.document.form1.Chk_FOTOART.status) {
    expr = /^[0-9]+$/;
    found = expr.exec(window.document.form1.FOTOART_SIZEMAX.value);
    if (! found) {
      alert('Foto de artículo : Peso máximo no válido.');
      window.document.form1.FOTOART_SIZEMAX.focus();
      window.document.form1.FOTOART_SIZEMAX.select();
      return false;
    };
  };

  if ((window.document.form1.Chk_FOTOART.status == false) && (window.document.form1.Chk_PIEFOTO.status)) {
      alert('Pie de Foto de artículo : Para seleccionar este item primero debe seleccionar Foto Artículo.');
      window.document.form1.Chk_PIEFOTO.focus();
      return false;
  };

  if (window.document.form1.Chk_FOTOART.status) {
    expr = /^[0-9]+$/;
    found = expr.exec(window.document.form1.FOTOART_SIZEMAX.value);
    if (! found) {
      alert('Foto de artículo : Peso máximo no válido.');
      window.document.form1.FOTOART_SIZEMAX.focus();
      window.document.form1.FOTOART_SIZEMAX.select();
      return false;
    };
  };


  if (window.document.form1.Chk_FOTOPORT != null) {
    if (window.document.form1.Chk_FOTOPORT.status) {
      expr = /^[0-9]+$/;
      found = expr.exec(window.document.form1.FOTOPORT_SIZEMAX.value);
      if (! found) {
        alert('Foto de Portada : Peso máximo no válido.');
        window.document.form1.FOTOPORT_SIZEMAX.focus();
        window.document.form1.FOTOPORT_SIZEMAX.select();
        return false;
      };
    };
  };

  // TABLA
//  if (window.document.form1.Chk_TABLA.status) {
//    expr = /^[1-9][0-9]*$/;
//    found = expr.exec(window.document.form1.TABLA_ANCHO.value);
//    if ( (! found) || (window.document.form1.TABLA_ANCHO.value > 100) ) {
//      alert('Ancho de tabla no válido.');
//      window.document.form1.TABLA_ANCHO.focus();
//      window.document.form1.TABLA_ANCHO.select();
//      return false;
//    };
//
//    expr = /^[1-6]$/;
//    found = expr.exec(window.document.form1.TABLA_PADDING.value);
//    if (! found) {
//      alert('Padding de tabla no válido.');
//      window.document.form1.TABLA_PADDING.focus();
//      window.document.form1.TABLA_PADDING.select();
//      return false;
//    };
//
//    expr = /^[0-1]$/;
//    found = expr.exec(window.document.form1.TABLA_BORDE.value);
//    if (! found) {
//      alert('Borde de tabla no válido.');
//      window.document.form1.TABLA_BORDE.focus();
//      window.document.form1.TABLA_BORDE.select();
//      return false;
//    };
//
//    expr = /^[1-6]$/;
//    found = expr.exec(window.document.form1.TABLA_SPACING.value);
//    if (! found) {
//      alert('Spacing de tabla no válido.');
//      window.document.form1.TABLA_SPACING.focus();
//      window.document.form1.TABLA_SPACING.select();
//      return false;
//    };
//
//  };

  return true;
};

// -----------------------------------------------------------------
function valida_campo(chk, textbox) {
// Valida los campos adicionales.
  var expr;
  var found;

  if (chk.status) {
    // repeticion con campos estandar
    if ( (textbox.value == 'fecha') || (textbox.value == 'titular') || (textbox.value == 'epig') || (textbox.value == 'baja') || (textbox.value == 'texto') || (textbox.value == 'titrec') || (textbox.value == 'textorec') ) {
      alert('Nombre de campo repetido.');
      textbox.focus();
      textbox.select();
      return false;
    };

    // validacion tipografica
    expr = /^[a-z][a-z0-9]+$/;
    found = expr.exec(textbox.value);
    if (! found) {
      alert('Nombre de campo no válido. Debe comenzar con letra minúscula seguida de letras minúsculas o números.');
      textbox.focus();
      textbox.select();
      return false;
    };
  };
  return true;
};
// -----------------------------------------------------------------

