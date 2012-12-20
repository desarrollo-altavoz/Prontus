//Inicializa validaciones
var validator = new Validador('coment','one','#FDF8C1');
validator.addconstraint('NOMBRE','obligatorio','','Debe indicar Nombre.');
validator.addconstraint('NOMBRE','cminimo','2','Nombre demasiado corto (mínimo 2 caracteres).');
validator.addconstraint('NOMBRE','texto','','Error en caracteres ingresados en nombre.\n(Solo letras, número, guión, punto, blanco, coma o apóstrofe)');
validator.addconstraint('PROCEDENCIA','obligatorio','','Debe indicar su procedencia.');
validator.addconstraint('PROCEDENCIA','cminimo','2','Procedencia demasiado corta (mínimo 2 caracteres).');
validator.addconstraint('PROCEDENCIA','regex',new RegExp(/^[0-9a-zA-ZñÑáéíóúäëïöüÁÉÍÓÚÄËÏÖÜ\.,;:\-& ]{2,}$/),'Error en caracteres ingresados en procedencia.\n(Solo letras, número, punto, comas, punto y coma, dos puntos, guiones y espacios)');

// validator.addconstraint('NICK','obligatorio','','Debes indicar Email.');
// validator.addconstraint('NICK','email','','Debes ingresar un Email válido.');
validator.addconstraint('COMENT_TEXTO','obligatorio','','Por favor, ingresa tu comentario.');
validator.addconstraint('COMENT_TEXTO','regex',new RegExp(/^[0-9a-zA-ZñÑáéíóúäëïöüÁÉÍÓÚÄËÏÖÜ\r\n\-\.\, \'\¿\?\¡\!\"\$\%\&\/\(\)\+\*\_\;\:]{2,}$/),'Error en caracteres ingresados en el Comentario');

function enviar_coment(theform) {
    var DIR_CGI = 'cgi-bin';
    var ruta_cgi = "/"+ DIR_CGI +"/coment/coment_enviar.cgi";
    var coment_obj = theform.COMENT_TEXTO;

    // valida nombre e email
    if (!validator.validar()) return;
    var nombre_sintilde = theform.NOMBRE.value;

    //escapear valores del formulario
    nombre_sintilde = nombre_sintilde.replace(/á/g,"a");
    nombre_sintilde = nombre_sintilde.replace(/é/g,"e");
    nombre_sintilde = nombre_sintilde.replace(/í/g,"i");
    nombre_sintilde = nombre_sintilde.replace(/ó/g,"o");
    nombre_sintilde = nombre_sintilde.replace(/ú/g,"u");
    nombre_sintilde = nombre_sintilde.replace(/ñ/g,"n");

    nombre_sintilde = nombre_sintilde.replace(/Á/g,"A");
    nombre_sintilde = nombre_sintilde.replace(/É/g,"E");
    nombre_sintilde = nombre_sintilde.replace(/Í/g,"I");
    nombre_sintilde = nombre_sintilde.replace(/Ó/g,"O");
    nombre_sintilde = nombre_sintilde.replace(/Ñ/g,"n");

    nombre_sintilde = nombre_sintilde.replace(/ +/g,".");
    nombre_sintilde = nombre_sintilde.replace(/[^a-zA-Z]/g,".");

    theform.NICK.value = nombre_sintilde;
    var div_numchars = document.getElementById('numchars');
    if (coment_obj.value == "") return;
    if (coment_obj.value.length > LIMIT_CHARS) {
        div_numchars.innerHTML = '0';
        // coment_obj.value = coment_obj.value.substring(0, LIMIT_CHARS) + "\n\n" + theform.NOMBRE.value + "\n" + theform.PROCEDENCIA.value;
        alert('El número máximo de caracteres permitidos es ' + LIMIT_CHARS);
    } else {
        var firma = "\n\n" + theform.NOMBRE.value + "\n" + theform.PROCEDENCIA.value;
        if (coment_obj.value.indexOf(firma) <= 0) {
            coment_obj.value = coment_obj.value + firma;
        }
//        if(window.sst7_lomas_coment) {
//            sst7_lomas_coment();
//        }
        var recargar_current_pag_coment = false; // solo requerido cuando es sin moderacion, para lograr q la pag aparezca actualizada de inmediato.
        ajax_post(ruta_cgi, recargar_current_pag_coment, theform._prontus_id.value); // from: ajax_send.js
    }
};

