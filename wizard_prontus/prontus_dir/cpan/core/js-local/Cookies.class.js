// Funciones para el manejo de Formularios
// 1.0.0 - 2008/05/13 - CVI - Primera Versión
// 1.1.0 - 2008/11/12 - YCC - La convierte en una clase estatica.

// Sinopsis:
// Cookies.createCookie(nomCookie, valCookie, '', '');

// ---------------------------------------------------------
// Crea una cookie en un determinado host
//    name: Nombre que tendrá la cookie
//    value: Valor que se le asignará a la cookie
//    days: Dias que estará vigente. Si viene nulo, durará sólo la sesión
//    path: Ruta de la Cookie. Si vienen nulo, se asume la raiz del sitio

var Cookies = {

    createCookie: function(name, value, days, path) {
        var expires = "";
        if(typeof days !== 'undefined' && days !== null && days !== '') {
            var date = new Date();
            date.setTime(date.getTime()+(days*24*60*60*1000));
            expires = "; expires="+date.toGMTString();
        }
        if(typeof path === 'undefined' || path === null || path === '') {
            path = '/';
        }
        document.cookie = name + "=" + value + expires + "; path=" + path;
        //alert(name + "=" + value + expires + "; path=" + path);
    },

    // ---------------------------------------------------------
    // Lee el valor de una cookie
    //    name: Nombre de la cookie a leer
    readCookie: function(name) {
        var nameEQ = name + "=";
        var ca = document.cookie.split(';');
        for(var i=0;i < ca.length;i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') {
                c = c.substring(1,c.length);
            }
            if (c.indexOf(nameEQ) === 0) {
                return c.substring(nameEQ.length,c.length);
            }
        }
        return null;
    },

    // ---------------------------------------------------------
    // Eliminar una cookie
    //    name: Nombre de la cookie a leer
    eraseCookie: function(name) {
        Cookies.createCookie(name,"",-1);
    }
};