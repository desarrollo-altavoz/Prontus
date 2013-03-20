/**
Utiles.class.js

Descripcion:
Contiene funciones basicas y utiles para el uso comun.
Próximamente podría quedar obsoleto o ser modificado masivamente, por lo tanto,
la documentación es básica

Dependencias:
Ninguna

Versión:
3.0.6 - 03/06/2010
Más información en Utiles.txt

**/

var Utiles = {

    /**
     * Zona de Configuraciones
     */
    prontusName: '/prontus_modelo_vacio',
    configWinDefault: 'scrollbars=1,resizable=1,toolbar=0,status=0,menubar=0,location=0,directories=0',
    msgWin: 'Debes habilitar las ventanas emergentes en tu navegador para acceder a esta funcionalidad.',

    /**
     * Abre una ventana pop generica
     * @param loc Url de la pagina que se abrira en la pop
     * @param nom nombre de la ventana
     * @param ancho ancho de la ventana
     * @param alto alto de la ventana
     * @param posx posicion X de la ventana
     * @param posy posicion Y de la ventana
     */
    subWin: function (loc, nom, ancho, alto, posx, posy, options) {

        var thisposx = (typeof posx !== 'undefined') ? posx : 20;
        var thisposy = (typeof posy !== 'undefined') ? posy : 10;

        if ((typeof loc === 'undefined') || (loc === "")){
           return false;
        }

        options = (typeof options === 'undefined') ? this.configWinDefault : options;
        options = 'width=' + ancho + ',height=' + alto
                + ',top=' + thisposy + ',left=' + thisposx
                + ',screenX=' + thisposx + ',screenY=' + thisposy
                + ',' + options;

        // Internet Explorer arroja error cuando el nombre de la ventana trae, por ejemplo, puntos.
        if((typeof nom === 'undefined') || (nom === "")) {
            nom = "New Window";
        } else {
            nom = nom.replace(/[^\w\d]/i,'');
        }

        var win = window.open(loc, nom, options);
        if(win) {
            win.focus();
        } else {
            alert(Utiles.msgWin);
            return;
        }
        //~ win.moveTo(thisposx, thisposy);
    },

    /**
     * Agrega una Funcion al onload de la pagina
     * @param func funcion que se desea agregar
     * @param params parametros de la funcion
     */
    addLoadEvent: function (func, params) {
        var oldonload = window.onload;
        window.onload = function() {
            if (oldonload) {
                oldonload();
            }
            func(params);
        };
    },

    /**
     * Obtiene un parametro del querystring.
     * @param nom Nmobre del parametro a leer
     */
    getParam: function (nom) {
        var request = window.location.href;
        if ((nom !== null) && (nom !== 'undefined') && (nom !== '')) {
            var re = new RegExp(nom + '=([^&]*)');
            var found = request.match(re);
            if(found.length >= 2) {
                return found[1];
            } else {
                return '';
            }
        }
        return '';
    },

    /**
     * Abre la ventana POP para el Zoom de Imágenes
     * @param loc url de la pagina que se abrira en la pop
     * @param nom nombre de la ventana
     * @param ancho ancho de la ventana
     * @param alto alto de la ventana
     * @param posx posicion X de la ventana
     * @param posy posicion Y de la ventana
     */
    popZoom: function (loc, nom, ancho, alto, posx, posy) {
        var thisposx = posx;
        var thisposy = posy;
        if(typeof thisposx === 'undefined') {
            thisposx = 20;
        }
        if(typeof thisposy === 'undefined') {
            thisposy = 10;
        }
        if ((typeof loc === 'undefined') || (loc === "")){
           return false;
        }
        var options='width='+ancho+',height='+alto+',scrollbars=0,resizable=1'+Utiles.configComun;
        var winzoom = window.open(loc, nom, options);
        if(winzoom) {
            winzoom.focus();
        } else {
            alert(Utiles.msgWin);
            return;
        }
        winzoom.focus();
        winzoom.moveTo(thisposx, thisposy);
    },

    /**
     * Destilda un String
     * @param texto String que se desea destildar
     */
    destilda: function (texto) {
        if(typeof texto === 'undefined' || texto === null || texto === '') {
            return '';
        }
        texto = texto.replace(/Á/g,'a');
        texto = texto.replace(/É/g,'e');
        texto = texto.replace(/Í/g,'i');
        texto = texto.replace(/Ó/g,'o');
        texto = texto.replace(/Ú/g,'u');
        texto = texto.replace(/á/g,'a');
        texto = texto.replace(/é/g,'e');
        texto = texto.replace(/í/g,'i');
        texto = texto.replace(/ó/g,'o');
        texto = texto.replace(/ú/g,'u');
        texto = texto.replace(/Ñ/g,'n');
        texto = texto.replace(/ñ/g,'n');
        texto = texto.replace(/Ü/g,'u');
        texto = texto.replace(/ü/g,'u');
        texto = texto.replace(/á/g,'a');
        texto = texto.toLowerCase();
        texto = texto.replace(/[^0-9a-z\_\-,\. ]/g,'');
        return texto;
    },

    /**
     * Funcion utilitaria para tirar a string un objeto
     * @param obj Objeto que se desea "serializar"
     */
    objectToString: function(obj) {
        if(typeof obj !== 'object') {
            return 'No Object';
        }
        var str = '';
        var x;
        for(x in obj) {
            if(typeof obj[x] === 'object' || typeof obj[x] === 'function') {
                str = str + x + ' --> ' + typeof obj + "\n";
            } else {
                str = str + x + ' --> ' + obj[x] + "\n";
            }
        }
        return str;

    },

    /**
     * Funcion utilitaria para poner handlers a los campos de busqueda
     * @param theid ID del campo input
     * @param texto Texto por default del campo input
     */
    instalaHandlerBuscador: function(theid, texto) {

        if($(theid).val() === '') {
            $(theid).val(texto).addClass('texto-ayuda');
        }
        $(theid).live('focus', function() {
            if($(this).val() == texto) {
                $(this).val('').removeClass('texto-ayuda');
            }
        }).live('blur', function() {
            if($(this).val() === '') {
                $(this).val(texto).addClass('texto-ayuda');
            }
        });
    },

    getFecha: function(thetime, human) {
        var date = new Date(thetime);
        var d = date.getDate();
        var m = date.getMonth();
        var y = date.getFullYear();
        var fecha;
        if(human) {
            var arr = ['enero', 'febrero', 'marzo', 'abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
            fecha = d+" de "+arr[m]+' de '+y;
            
        } else {
            d = (d<=9?'0'+d:d);
            m = m + 1;
            m = (m<=9?'0'+m:m);                   
            fecha = d+'/'+m+'/'+y;
        }
        return fecha;
    },
    
    getHora: function(thetime, sinsegundos) {
        
        var date = new Date(thetime);
        var h = date.getHours();
        h = (h<=9?'0'+h:h);
        
        var m = date.getMinutes()+1;
        m = (m<=9?'0'+m:m);        
        
        var s = date.getSeconds();
        s = (s<=9?'0'+s:s);       
        if(sinsegundos) {
            return h+':'+m;
        } else {
            return h+':'+m+':'+s;
        }
        
        
    }
};
