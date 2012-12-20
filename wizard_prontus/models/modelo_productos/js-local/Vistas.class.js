/**
Vistas.class.js

Descripcion:
Contiene funciones utiles para el manejo de vistas.
OJO: cno la funcion para el taxportlista para funciones mayores
a la 10.12, ya que podria cambiar dicha cgi

Dependencias:
Ninguna

Versión:
2.0.0 - 11/11/2009 - CVI - Primera Versión orientada a objetos
2.0.1 - 13/04/2011 - CPN - Se agrega funcion para ir a la vista de accesibilidad
**/

var Vistas = {

    /**
     * Zona de Configuraciones
     */
    dirCgiBin: '/cgi-bin',
    coockiename: 'vista',

    /**
     * Para cambiar entre una vista y otra. Se le entrega la vista a la
     * que se desea ir.
     * @param lang vista a la que se desea ir
     */
    change: function (lang) {
        if(lang=='es') {
	        Vistas.goSpanish();
        } else if(lang=='en') {
	        Vistas.goEnglish();
        } else if(lang=='acc') {
            Vistas.goAccesibilidad();
        } else {
            Vistas.goSpanish();
        }
    },

    /**
     * Para seteo de la cookie. Se deja con tiempo de
     * expiración muy alto, para que cuando la persona vuelva,
     * encuentra la misma vista
     * @param value Valor que tendrá, por ejemplo: esp o eng
     */
    setMultivista: function (value) {
        var name = Vistas.coockiename;
        var path = '/';
        var expires = new Date();
        expires.setDate(expires.getDate() + 365);
        document.cookie = name + "=" + window.escape(value)+";expires="+expires.toGMTString()+";path="+path;
    },



    /**
     * Lee el valor de la cookie de multivistas y lo retorna
     */
    readMultivista: function () {
        var name = Vistas.coockiename;
        var nameEQ = name + "=";
        var ca = document.cookie.split(';');
        for(var i=0;i < ca.length;i++) {
            var c = ca[i];
            while (c.charAt(0)===' ') {
                c = c.substring(1,c.length);
            }
            if (c.indexOf(nameEQ) === 0) {
                return c.substring(nameEQ.length,c.length);
            }
        }
        return null;
    },

    /**
     * Va a la vista español
     */
    goSpanish: function () {
        Vistas.setMultivista('es');
        var url = document.URL;
        if (url.indexOf('/site/cache/nroedic/taxport') > 0) {
            var urltotax = Vistas.getUrlTaxport(url, '');
            if(urltotax == '') {
                window.location.href = '/';
            }
            window.location.href = urltotax;
        } else if (url.indexOf(Vistas.dirCgiBin) > 0) {
            // Caso pagina dinamica vuelve a la home.
            window.location.href = '/';
        } else {
            window.location.reload();
        }
    },
    
     /**
     * Va a la vista de accesibilidad CPN
     */
    goAccesibilidad: function () {
        Vistas.setMultivista('acc');
        var url = document.URL;
        if (url.indexOf('/site/cache/nroedic/taxport') > 0) {
            var urltotax = Vistas.getUrlTaxport(url, 'acc');
            if(urltotax == '') {
                window.location.href = '/';
            }
            window.location.href = urltotax;
        } else if (url.indexOf(Vistas.dirCgiBin) > 0) {
            // Caso pagina dinamica vuelve a la home.
            window.location.href = '/';
        } else {
            window.location.reload();
        }
    },

    /**
     * Va a la vista ingles
     */
    goEnglish: function () {
        Vistas.setMultivista('en');
        var url = document.URL;
        if (url.indexOf('/site/cache/nroedic/taxport') > 0) {
            var urltotax = Vistas.getUrlTaxport(url, 'en');
            if(urltotax == '') {
                window.location.href = '/';
            }
            window.location.href = urltotax;
        } else if (url.indexOf(Vistas.dirCgiBin) > 0) {
            // Caso pagina dinamica vuelve a la home.
            window.location.href = '/';
        } else {
            window.location.reload();
        }
    },

    /**
     * Obtiene la url de la portada taxonomica a la que se tiene que ir
     * dada la url actual y la vista actual.
     * @param url Url de la portada taxonomica
     * @param vista Vista actual.
     */
    getUrlTaxport: function (url, vista) {
        var prontus = url.match(/(\/[a-zA-Z_0-9]+)\/site\//);
        if(typeof prontus[1] === 'undefined' || prontus[1]==='') {
            return '';
        }
        var indices = url.match(/\/(\d+)_(\d+)_(\d+)_(\d+)\./);
        var urltotax = Vistas.dirCgiBin + '/prontus_taxport_lista.cgi?_MV='+vista+'&_REL_PATH_PRONTUS='+prontus[1];
        if(indices[1]>0) {
            urltotax = urltotax + '&seccion=' + indices[1];
        }
        if(indices[2]>0) {
            urltotax = urltotax + '&tema=' + indices[2];
        }
        if(indices[3]>0) {
            urltotax = urltotax + '&subtema=' + indices[3];
        }
        if(indices[4]>0) {
            urltotax = urltotax + '&nropag=' + indices[4];
        }
        return urltotax;
    },

    /**
     * Función utilizada para cambiar el formato de una fecha del tipo dd/mm/aaaa a mm/dd/aaaa
     * según el String lang, utilizado por el idioma devuelve la cadena en otro orden
     * @param lang Idioma
     * @param fecha Fecha en formato dd/mm/aaaa
     */
    convertFecha: function (lang, fecha) {
        if(lang == 'en') {
            var trozos = fecha.split ("/");
            return trozos[1]+'/'+trozos[0]+'/'+trozos[2];
        } else {
            return fecha;
	    }
	}
};

// -----------------------------------------------------------------------------
// Para setear la vista por defecto. Descomentar para utilizar
// var thismv = Vistas.readMultivista();
// if (thismv==null) {
//     Vistas.goSpanish();
// };
