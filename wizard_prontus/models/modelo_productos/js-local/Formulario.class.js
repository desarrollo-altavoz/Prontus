/**
Formulario.class.js

Descripcion:
Contiene funciones basicas y utiles para el el manejo de Formularios.
No usa jQuery.

Dependencias:
Ninguna

Versión:
1.0.0 - 15/12/2009 - CVI - Primera Versión orientada a objetos
**/

var Formulario = {


    // ---------------------------------------------------------
    // Devuelve si hay algún valor chequeado de un grupo de Checkbox
    // formu: Referencia al objeto formulario
    // nomb:  Nombre del grupo de radio buttons
    getRadioValue: function(formu, nomb) {
        var radios = formu.elements[nomb];
        for(var i=0, len = radios.length; i < len ; i++ ) {
            if(radios[i].checked) {
                return radios[i].value;
            }
        }
        return '';
    },

    // ---------------------------------------------------------
    // Para chequear todos los checkbox.
    // formu:   Referencia al objeto formulario
    // prefijo: Prefijo de los checks. Si es nulo o vacio, chequea todos.
    checkAll: function (formu, prefijo) {
        if(typeof prefijo == 'undefined' || prefijo==null) {
            return;
        }
        var elems = formu.elements;
        for(var i=0, len=elems.length; i<len; i++) {
            if(elems[i].type=='checkbox') {
                if(prefijo=='' || elems[i].name.indexOf(prefijo)==0) {
                    elems[i].checked = true;
                }
            }
        }
    },

    // ---------------------------------------------------------
    // Para deschequear todos los checkbox
    // formu:   Referencia al objeto formulario
    // prefijo: Prefijo de los checks. Si es nulo o vacio, deschequea todos.
    uncheckAll: function(formu, prefijo) {
        if(typeof prefijo == 'undefined' || prefijo==null) {
            return;
        }
        var elems = formu.elements;
        for(var i=0, len=elems.length; i<len; i++) {
            if(elems[i].type=='checkbox') {
                if(prefijo=='' || elems[i].name.indexOf(prefijo)==0) {
                    elems[i].checked = false;
                }
            }
        }
    },

    // ---------------------------------------------------------
    // Invierte el esteado de un grupo de checkbox
    // formu:   Referencia al objeto formulario
    // prefijo: Prefijo de los checks. Si es nulo o vacio, chequea/deschequea todos.
    toggle: function(formu, prefijo) {
        if(typeof prefijo == 'undefined' || prefijo==null) {
            return;
        }
        var elems = formu.elements;
        for(var i=0, len=elems.length; i<len; i++) {
            if(elems[i].type=='checkbox') {
                if(prefijo=='' || elems[i].name.indexOf(prefijo)==0) {
                    elems[i].checked = (elems[i].checked) ? false : true;
                }
            }
        }
    },

    // -----------------------------------------------------------------
    // Permite selecc o desselecc una col completa de checkboxes usando la de la cabecera
    // que es de la sgte. forma:
    // <input type="checkbox" name="selAll" value="1" onclick="MantenedorGenerico.handleMultiCheck(this, 'sel_')">
    // y cada uno de los checks de la columna es del tipo:
    // <input type="checkbox" name="sel_0018950f587c" value="1" />
    // Params:
    // masterCheckObject: el objeto checkbox usado como master
    // checkPrefix: prefijo de los name de los checkboxes a manipular
    handleMultiCheck: function(masterCheckObject, checkPrefix) {
       var formObject = masterCheckObject.form
       var numFormElements = formObject.elements.length;
       var nomField = '';

       for (var i = 0; numFormElements > i; i++) {
           nomField = formObject.elements[i].name;

           if (nomField.indexOf(checkPrefix) >= 0) {
               formObject[nomField].checked = masterCheckObject.checked;
           }
       }
    }
};