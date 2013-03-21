/**
Botones.class.js

Descripcion:
    sirve para cambiar entre im�genes, prirncipalmente
    para hacer botones que cambien con el mouseover.
    Pr�ximamente podr�a quedar obsoleto, por lo que la documentaci�n es b�sica

Dependencias:
    Ninguna

Versi�n:
    2.0.0 - 11/11/2009 - CVI - Primera versi�n orientada a objetos.
        Basada en la versi�n 1.1 de botones.js
**/

var Botones = {

    /**
     * Funcion que se encarga de cambiar una imagen por otra.
     * Ver documentacion para ver como se usa.
     * @param imag Objeto DOM que representa a la imagen
     */
    toogle: function (imag, estado) {
        if(typeof imag === 'undefined') {
            return;
        }
        var thesrc = imag.src;
        if(!thesrc) {
            return;
        }
        var ind = thesrc.lastIndexOf('.');
        var before = thesrc.substr(0, ind-2);
        var state = thesrc.substr(ind-2, 2);
        var after = thesrc.substr(ind, thesrc.length - ind);
        var newstate = '';

        if(typeof estado !== 'undefined') {
            newstate = estado;
        } else {
            if(state == 'on') {
                newstate = 'of';
            } else if(state == 'of') {
                newstate = 'on';
            } else {
                return;
            }
        }

        imag.src = before + newstate + after;
        return;
    },

    /**
     * Funcion que se encarga de agregar nuevos eventos a una determinada imagen
     * @param idImag Id de la imagen
     */
    addEvent: function(idImag) {
        if(typeof idImag === 'undefined') {
            return;
        }
        if(document.getElementById && document.getElementById(idImag)) {
            var theImag = document.getElementById(idImag);
            theImag.onmouseover = function() {
                Botones.toogle(this, 'on');
            };
            theImag.onmouseout = function() {
                Botones.toogle(this, 'of');
            };
        }
    }

};


$(document).ready(function() {
    $('img.cambia-boton').live('mouseover', function() {
        Botones.toogle(this, 'on');
    }).live('mouseout click', function() {
        Botones.toogle(this, 'of');
    });
    $('a.cambia-boton').live('mouseover', function() {
        Botones.toogle($(this).find('img').get(0), 'on');
    }).live('mouseout click', function() {
        Botones.toogle($(this).find('img').get(0), 'of');
    });

});
