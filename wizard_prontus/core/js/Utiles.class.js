/**
Utiles.class.js

Descripcion:
Contiene funciones basicas y utiles para el uso comun.
Próximamente podría quedar obsoleto o ser modificado masivamente, por lo tanto,
la documentación es básica

Dependencias:
Ninguna

Versión:
3.0.0 - 11/11/2009 - CVI - Primera Versión orientada a objetos
**/

var Utiles = {

    /**
     * Zona de Configuraciones
     */
    dirCgiBin: '/cgi-bin',
    prontusName: '/prontus_modelo_vacio',
    cgiNameImprimir: 'prontus_imprimir.cgi',
    formEnviar: '/stat/enviar/formulario.html',
    configComun: 'toolbar=0,status=0,menubar=0,location=0,directories=0',
    msgWin: 'Debes habilitar las ventanas emergentes en tu navegador para acceder a esta funcionalidad.',

    /**
     * Para el Envio de noticia por e-mail.
     * Sólo abre el formulario, no llama directamente a la CGI
     */
    enviarArticulo: function () {
        var url = document.URL;
        var loc = Utiles.prontusName + Utiles.formEnviar+'?_URL=' + window.escape(url);
        var config = 'width=400,height=455,scrollbars=0,resizable=0,' + Utiles.configComun;
        var envia = window.open(loc,'enviar', config);
        if(envia) {
            envia.focus();
        } else {
            alert(Utiles.msgWin);
            return;
        }
        envia.focus();
    },

    /**
     * Abre la ventana para imprimir el artículo actual.
     * Con soporte para multivistas
     * @param mv nombre de la multivista
     */
    imprimirArticulo: function (mv) {
        var url = document.URL;
        var mvcookie;
        if(typeof mv !== 'undefined' && mv!='') {
            mvcookie = '_MV='+mv+'&';
        } else {
            mvcookie = '';
        }
        var loc = Utiles.dirCgiBin+'/'+Utiles.cgiNameImprimir+'?'+mvcookie+'_URL=' + window.escape(url);
        var w = screen.availWidth/2;
        var h = screen.availHeight*0.9;
        var config = 'width='+w+',height='+h+',scrollbars=1,resizable=0,'+Utiles.configComun;
        var imprimir = window.open(loc,'imprimir', config);
        if(imprimir) {
            imprimir.focus();
        } else {
            alert(Utiles.msgWin);
            return;
        }
        imprimir.focus();
    },

    /**
     * Abre una ventana pop generica
     * @param loc Url de la pagina que se abrira en la pop
     * @param nom nombre de la ventana
     * @param ancho ancho de la ventana
     * @param alto alto de la ventana
     * @param posx posicion X de la ventana
     * @param posy posicion Y de la ventana
     */
    subWin: function (loc, nom, ancho, alto, posx, posy) {
        var thisposx = posx;
        var thisposy = posy;
        if(typeof thisposx === 'undefined') {
            thisposx = 20;
        }
        if(typeof thisposy === 'undefined') {
            thisposy = 10;
        }

        var options = 'width=' + ancho + ',height=' + alto + ',scrollbars=1,resizable=1,' +
                Utiles.configComun;
        var win = window.open(loc, nom, options);
        if(win) {
            win.focus();
        } else {
            alert(Utiles.msgWin);
            return;
        }
        win.focus();
        win.moveTo(thisposx, thisposy);
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
        var txt = texto;
        txt = txt.replace(/Á/g,'a');
        txt = txt.replace(/É/g,'e');
        txt = txt.replace(/Í/g,'i');
        txt = txt.replace(/Ó/g,'o');
        txt = txt.replace(/Ú/g,'u');
        txt = txt.replace(/á/g,'a');
        txt = txt.replace(/é/g,'e');
        txt = txt.replace(/í/g,'i');
        txt = txt.replace(/ó/g,'o');
        txt = txt.replace(/ú/g,'u');
        txt = txt.replace(/Ñ/g,'n');
        txt = txt.replace(/ñ/g,'n');
        txt = txt.replace(/Ü/g,'u');
        txt = txt.replace(/ü/g,'u');
        txt = txt.replace(/á/g,'a');
        txt = txt.toLowerCase();
        txt = txt.replace(/[^0-9a-z\_\-]/g,'');
        return txt;
    }

};