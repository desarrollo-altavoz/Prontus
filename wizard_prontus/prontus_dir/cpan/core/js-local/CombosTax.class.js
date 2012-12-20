/***** Manejo combos tax ******/


var CombosTax = {

    spaces: '                                ', // son 32

    objFormFid: '', // se setea en el doc. ready

    // ---------------------------------------------
    generaTemas: function(num, temapos_id) {

        var theForm = CombosTax.objFormFid;

        if ((typeof(theForm['_SECCION' + num]) == 'undefined') || (typeof(theForm['_TEMA' + num]) == 'undefined')) {
            return false;
        }

        var secciones = theForm['_SECCION' + num];
        var indice = secciones.selectedIndex;

        if (indice < 0) {
            return false;
        }

        var id_secciones = secciones.options[indice].value;
        var temas = theForm['_TEMA' + num];

        // borra combo temas
        var len = temas.options.length;
        var i;
        for(i = (len-1); i >= 0 ; i--) {
            temas.options[i] = null;
        }

        if ((id_secciones  > 0) && (typeof window['arreglo_temas_' + id_secciones + '_valor'] != 'undefined')) {
            // alert(1)
            var cant_temas = window['arreglo_temas_' + id_secciones + '_texto'].length;
            temas.options[0] = new Option(CombosTax.spaces, '0');
            for (i = 0; cant_temas > i; i++) {
                var txt = window['arreglo_temas_' + id_secciones + '_texto'][i];
                var val = window['arreglo_temas_' + id_secciones + '_valor'][i];
                temas.options[i + 1] = new Option(txt, val);
                temas.options[i + 1].title = txt;
            }

            // Posicionar combo tema
            if (temapos_id > 0) {
                var seleccionado = 0;
                for (i=0; i < temas.length; i++) {
                    if (temapos_id == temas[i].value) {
                        seleccionado = i;
                    }
                }
                temas.options[seleccionado].selected = true;
            }


            if (id_secciones <= 0) {
                var cargo = theForm['_SUBTEMA' + num];
                var len2 = cargo.options.length;
                for(i = (len2-1); i >= 0 ; i--) {
                    cargo.options[i] = null;
                }
            }
        } else {
            // alert(2)
            temas.options[0] = new Option(CombosTax.spaces, '0');
        }
        CombosTax.generaSubtemas(num);
    },

    // ---------------------------------------------
    generaSubtemas: function(num, subtemapos_id) {

        var theForm = CombosTax.objFormFid;
        if ((typeof(theForm['_TEMA' + num]) == 'undefined') || (typeof(theForm['_SUBTEMA' + num]) == 'undefined')) {
            return false;
        }

        var temas = theForm['_TEMA' + num];
        var indice = temas.selectedIndex;

        if (indice < 0) {
            return false;
        }

        var id_temas = temas.options[indice].value;
        var subtemas = theForm['_SUBTEMA' + num];
        var len = subtemas.options.length;
        var i;
        for(i = (len-1); i >= 0 ; i--) {
            subtemas.options[i] = null;
        }

        var val1 = 0;
        if(typeof window['arreglo_subtemas_' + id_temas + '_valor'] !== 'undefined') {
            val1 = window['arreglo_subtemas_' + id_temas + '_valor'][0];
        }
        if ((id_temas > 0) && (val1 !== 0)) {
            var cant_subtemas = window['arreglo_subtemas_' + id_temas + '_texto'].length;
            // subtemas.options[0] = new Option(CombosTax.spaces, '0');
            subtemas.options[0] = new Option(CombosTax.spaces, '0');
            for (i = 0; cant_subtemas > i; i++) {
                var txt = window['arreglo_subtemas_' + id_temas + '_texto'][i];
                var val = window['arreglo_subtemas_' + id_temas + '_valor'][i];
                subtemas.options[i + 1] = new Option(txt, val);
                subtemas.options[i + 1].title = txt;
            }

            // Posicionar combo tema
            if (subtemapos_id > 0) {
                var seleccionado = 0;
                for (i=0; i < subtemas.length; i++) {
                    if (subtemapos_id == subtemas[i].value) {
                        seleccionado = i;
                    }
                }
                subtemas.options[seleccionado].selected = true;
            }
        } else {
            subtemas.options[0] = new Option(CombosTax.spaces, '0');
        }
    },

    // ---------------------------------------------
    fillSeccTemStem: function() {

        var theForm = CombosTax.objFormFid;

        var cmb, nom;
        // var asignacion = "nom.value = (cmb.options[cmb.selectedIndex].text == CombosTax.spaces) ? '' : cmb.options[cmb.selectedIndex].text";
        // TRIPLETA 1
        if (typeof(theForm._SECCION1) !== 'undefined') {
            cmb = theForm._SECCION1;
            nom = theForm._NOM_SECCION1;
            if (cmb.selectedIndex >= 0) {
                nom.value = (cmb.options[cmb.selectedIndex].value <= 0) ? '' : cmb.options[cmb.selectedIndex].text;
            } else {
                nom.value = '';
            }

            cmb = theForm._TEMA1;
            nom = theForm._NOM_TEMA1;
            if (cmb.selectedIndex >= 0) {
                nom.value = (cmb.options[cmb.selectedIndex].value <= 0) ? '' : cmb.options[cmb.selectedIndex].text;
            } else {
                nom.value = '';
            }

            cmb = theForm._SUBTEMA1;
            nom = theForm._NOM_SUBTEMA1;
            if (cmb.selectedIndex >= 0) {
                nom.value = (cmb.options[cmb.selectedIndex].value <= 0) ? '' : cmb.options[cmb.selectedIndex].text;
            } else {
                nom.value = '';
            }

        }

        // TRIPLETA 2

        if (typeof(theForm._SECCION2) !== 'undefined') {
            cmb = theForm._SECCION2;
            nom = theForm._NOM_SECCION2;
            if (cmb.selectedIndex >= 0) {
                nom.value = (cmb.options[cmb.selectedIndex].value <= 0) ? '' : cmb.options[cmb.selectedIndex].text;
            } else {
                nom.value = '';
            }

            cmb = theForm._TEMA2;
            nom = theForm._NOM_TEMA2;
            if (cmb.selectedIndex >= 0) {
                nom.value = (cmb.options[cmb.selectedIndex].value <= 0) ? '' : cmb.options[cmb.selectedIndex].text;
            } else {
                nom.value = '';
            }

            cmb = theForm._SUBTEMA2;
            nom = theForm._NOM_SUBTEMA2;
            if (cmb.selectedIndex >= 0) {
                nom.value = (cmb.options[cmb.selectedIndex].value <= 0) ? '' : cmb.options[cmb.selectedIndex].text;
            } else {
                nom.value = '';
            }

        }

        // TRIPLETA 3
        if (typeof(theForm._SECCION3) !== 'undefined') {
            cmb = theForm._SECCION3;
            nom = theForm._NOM_SECCION3;
            if (cmb.selectedIndex >= 0) {
                nom.value = (cmb.options[cmb.selectedIndex].value <= 0) ? '' : cmb.options[cmb.selectedIndex].text;
            } else {
                nom.value = '';
            }

            cmb = theForm._TEMA3;
            nom = theForm._NOM_TEMA3;
            if (cmb.selectedIndex >= 0) {
                nom.value = (cmb.options[cmb.selectedIndex].value <= 0) ? '' : cmb.options[cmb.selectedIndex].text;
            } else {
                nom.value = '';
            }

            cmb = theForm._SUBTEMA3;
            nom = theForm._NOM_SUBTEMA3;
            if (cmb.selectedIndex >= 0) {
                nom.value = (cmb.options[cmb.selectedIndex].value <= 0) ? '' : cmb.options[cmb.selectedIndex].text;
            } else {
                nom.value = '';
            }

        }
    }

};