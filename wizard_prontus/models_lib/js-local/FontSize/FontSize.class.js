/**
FontSize.class.js
Descripcion:
    Cambia el tamaño de la fuenta para los estilos que coincidan con cierto patrones
    como titular, bajada, cuerpo, etc. Véase la sección de configuración más abajo
    para cambiar dichos parámetros.
    OJO: Cambia el estilo de la primera hoja de estilos definida en la página
    Próximamente podría quedar obsoleto, por lo que la documentación es básica

Dependencias:
    Ninguna

Versión:
    ----------------------------------------------------------------------------
    2.0.0 - 11/11/2009 - CVI - Primera Versión coa Orientación a Objetos
                Basada en la version 1.10 de cambia_tam_fonts.js
**/

var FontSize = {

    /**
     * Zona de Configuraciones
     */

    // Tamaño actual En porcentaje
    size_actual: 100,

    // Arreglo con los tamaños a los que se podrá cambiar
    tamanos: [70,80,90,100,130,180,250],

    // patrones que se buscarán para cambiar el estilo
    estilos: ['titular','bajada','epigrafe','cuerpo'],

    // indice del arrglo de tamanos (3 = 4to elemento)
    size_actual_i: 3,

    // Mensaje cuando no se puede usar esta opcion
    msgError: 'Este Navegador no soporta aumento/disminución de tamaño de texto.',

    // En el caso de que se quiera procesar otro CSS y no el primero
    indice_hoja_estilos: 0,


    /** ----------
     * Propiedades de la clase
     */
    fontWeight_default: '',
    fontFamily_default: '',
    fontSize_default: '',
    color_default: '',
    fontweight: [],
    fontfamily: [],
    fontsize: [],
    fontcolor: [],
    initiated: false,
    firstsheet: null,
    therules: null,
    var_elements: [],


    /**
     * Funcion que inicializa los tamaños de fuentes
     * Se llama automaticamente al intentar cambiar de tamaño
     */
    init: function () {

        if (! document.styleSheets) { // 1.8 Funciona solo para browsers capaces.
            return false;
        }

        // Inicializa arreglos de estilos. V1.7.
        FontSize.firstsheet = document.styleSheets[FontSize.indice_hoja_estilos];
        if(FontSize.firstsheet.cssRules) {
            FontSize.therules = FontSize.firstsheet.cssRules;
        } else {
            FontSize.therules = FontSize.firstsheet.rules;
        }

        // Rescata los atributos de los css del primer archivo de estilos de la
        // pagina html (por eso se usa el subindice 0).
        var theruleslen = FontSize.therules.length;
        for (var j=0; j < theruleslen; j++) { // 1.2
            FontSize.fontweight[j] = FontSize.therules[j].style.fontWeight;
            FontSize.fontfamily[j] = FontSize.therules[j].style.fontFamily;
            FontSize.fontsize[j]   = FontSize.therules[j].style.fontSize;
            FontSize.fontcolor[j]  = FontSize.therules[j].style.color;
        }

        // Busca los elementos a modificar (css). Estos son fijos y hay que
        // agregarlos directamente en este archivo.

        for (var i=0; i < theruleslen; i++) {
            var aux = FontSize.therules[i].selectorText;
            var found = 0;
            if (aux == '*') {
                FontSize.fontWeight_default = FontSize.therules[i].style.fontWeight;
                FontSize.fontFamily_default = FontSize.therules[i].style.fontFamily;
                FontSize.fontSize_default   = FontSize.therules[i].style.fontSize;
                FontSize.color_default      = FontSize.therules[i].style.color;
            }
            // 1.8 Encuentra estilos a afectar.
            for (var k=0; k < FontSize.estilos.length; k++) {
                if ( (aux.indexOf(FontSize.estilos[k]) >= 0) && (aux.indexOf(':hover') < 0) ) {
                    found = 1;
                }
            }
            if (found == 1) {
                FontSize.var_elements[FontSize.var_elements.length] = i;
            }
        }
        return true;
    },

    /**
     * Esta funcion en la que cambia los tamaños
     * @param signo Signo para cambiar, puede se 'mas' o 'menos'
     */
    cambiaSize: function (signo) {
        if (! document.styleSheets) { // 1.8 Funciona solo para browsers capaces.
            alert(FontSize.msgError);
            return;
        }
        if(! FontSize.initited) {
            var resp = FontSize.init();
            if(! resp) {
                alert(FontSize.msgError);
                return;
            }
            FontSize.initited = true;
        }

        if ( signo == 'mas' ) {// 1.3
            if (FontSize.size_actual_i >= (FontSize.tamanos.length - 1)) {
                return;
            }
            FontSize.size_actual_i++;
        } else {
            if (FontSize.size_actual_i <= 0) {
                return;
            }
            FontSize.size_actual_i--;
        }
        FontSize.size_actual = FontSize.tamanos[FontSize.size_actual_i];

        // 1.5 Solo aplica cambios a elementos preseleccionados.
        var varelemlen = FontSize.var_elements.length;
        for (var i=0; i < varelemlen; i++) {
            var j = FontSize.var_elements[i];
            if (FontSize.fontsize[j] == '') {
                if (FontSize.fontSize_default != '') {
                    FontSize.fontsize[j] = FontSize.fontSize_default;
                } else {
                    FontSize.fontsize[j] = 12;
                }
            } // V1.7.
            var tam_final = parseInt((parseInt(FontSize.fontsize[j], 10) * FontSize.size_actual)/100, 10);

            if (tam_final - parseInt(tam_final, 10) > 0) {
                // Si resultado da con decimal, se agrega uno al entero.
                tam_final = parseInt(tam_final, 10) + 1;
            }
            FontSize.therules[j].style.fontSize = tam_final+'px'; // 1.8
        }
    }
};