// ****************************************************
// función que arma tira de pares name=valor de acuerdo a los campos del form
// para ser usada por el post ajax
function prep_params(theform) {
  var cant_elem = theform.elements.length;
  var str_params = '';
  var nombre;
  for (var i = 0; cant_elem > i; i++) {
    nombre = theform.elements[i].name;
    if (nombre != 'ANULA_ENTER' && nombre !== '') { // campo con display hidden puesto en los forms para anular key enter press
        //eval('str_params = str_params + "&' + nombre + '=" + escape(theform["' + nombre + '"].value)');
        eval('str_params = str_params + "&' + nombre + '=" + Url.encode(theform["' + nombre + '"].value)');
    }
  }
  var str_params = str_params.replace(/^&/, "");
  return str_params;
};

// ****************************************************
// Submite form via ajax, para guardar un registro.
// cgi: relative path a la cgi que hay q invocar
// nom_campo_id: Nombre del campo hidden utilizado para almacenar el id del registro.
// accion: new | update
// thennew: thennew | ''  --> si viene, indica "save & new"
function ajax_post(cgi, recargar_current_pag_coment, prontus_id) {
  ajax = make_ajax_object();
  var urlparams = prep_params(document.coment);
  ajax.open("POST", cgi, true);
  ajax.onreadystatechange=function() {
      if (ajax.readyState==4) {
          var resp = ajax.responseText;
          var resp_arr = resp.split('|'); // status|msg
          var id = resp_arr[0];
          var msg = resp_arr[1];
          if ((id > 0) && (id != null)) {
              show_msg(msg);
              if (recargar_current_pag_coment) {
                recarga_coment(FILE_OPINIONES);
              }
              callback_recibido_comentario(document.coment, prontus_id); /* eliminar session del artículo posteado.*/
              if(window.sst7_lomas_coment) {
                sst7_lomas_coment();
              };
              AGREGAR_FIRMA = true;
          } else {
              show_msg(msg);
              show_formdata();
          }
      }
	}

	ajax.setRequestHeader("Content-Type","application/x-www-form-urlencoded");
	ajax.send(urlparams);
	hide_formdata();
	show_reloj();

};

// ****************************************************
function recarga_coment(file){
  divResultado = document.getElementById('opiniones');

  ajax = make_ajax_object();
  ajax.open("GET", file);
  ajax.onreadystatechange=function() {
    if (ajax.readyState==4) {
      divResultado.innerHTML = ajax.responseText;
      window.location.href = "#inicio_lista";
      FILE_OPINIONES = file;
    }
  }
  ajax.send(null);

};


// ****************************************************
//recibido el comentario elimina la variable de sesion del articulo usado en elsistema de comentarios
function callback_recibido_comentario(theform, prontus_id){
  var ts = theform.OBJID.value;
  ajax = make_ajax_object();
  ajax.open("GET", "/" + prontus_id + "/coment/php/_session.php?_sid=" + "_COMENT_CAPTCHA_" + ts);
  ajax.onreadystatechange=function() {
    if (ajax.readyState==4) {
      var ot = ajax.responseText;
    }
}
ajax.send(null);
};

// ****************************************************
// Oculta form
function hide_formdata() {
  document.getElementById('coment').style.display = 'none';
};

// ****************************************************
// Visibiliza form
function show_formdata() {
  document.getElementById('coment').style.display = '';
};

// ****************************************************
// Visibiliza y muestra mensaje
function show_msg(mensaje) {
  document.getElementById('msg').style.display = '';
  document.getElementById('msg').innerHTML = mensaje;
};

// ****************************************************
// Visibiliza mensaje y le asigna el html del reloj
function show_reloj() {
  document.getElementById('msg').style.display = '';
  document.getElementById('msg').innerHTML = document.getElementById('reloj').innerHTML;
};
// ****************************************************
function hide_msg() {
  // Visibiliza mensaje y le asigna el html del reloj
  document.getElementById('msg').style.display = 'none';
};