
var Megalupa = {

    formMegalupa: '#formMegalupa',

    // -------------------------------------------------------------------------
    iniciaMegalupa: function() {

        // Se obtiene el formulario sobre el que se trabajara
        CombosTax.objFormFid = document.getElementById('formMegalupa');

        // Los handlers para el onchange
        $('select[name="_SECCION1"]').bind('change', function() {
            CombosTax.generaTemas(1);
        });
        $('select[name="_TEMA1"]').bind('change', function() {
            CombosTax.generaSubtemas(1);
        });

        // Se inicializan los calendarios
        $.datepicker.setDefaults($.datepicker.regional.es);
        $('.main-megalupa .fecha').datepicker({
            dateFormat: 'dd/mm/yy',
            buttonImage: '/'+Admin.prontus_id+'/cpan/core/imag/boto/calendar.gif',
            buttonImageOnly: true,
            showOn: 'both'
        });

        // Se precargan los datos de la búsqueda actual
        Megalupa.cargaCamposMegalupa();
    },

    // -------------------------------------------------------------------------
    devuelveFiltros: function() {

        var formSel = $(Megalupa.formMegalupa + ' select');
        var formInp = $(Megalupa.formMegalupa + ' input');

        if (! Megalupa.validaFecha(formInp.filter('[name="DIA"]').val(), "de creación")) {
            return false;
        }

        if (! Megalupa.validaFecha(formInp.filter('[name="DIAPUB"]').val(), "de publicación")) {
            return false;
        }

        if (! Megalupa.validaFecha(formInp.filter('[name="DIAEXP"]').val(), "de expiración")) {
              return false;
        }

        var tipart = '';
        var seccion = '';
        var tema = '';
        var subtema = '';

        var nom_tipart = '';
        var nom_seccion = '';
        var nom_tema = '';
        var nom_subtema = '';

        var autor = '';
        var titu = '';
        var baja = '';
        var dia = '';
        var autoinc = '';
        var diapub = '';
        var diaexp = '';

        var alta = '';
        var nom_alta = '';

        autoinc = formInp.filter('[name="AUTOINC"]').val();
        if (autoinc !== '' && isNaN(autoinc)) {
            alert("Código de artículo no es válido.");
            return false;
        }

        tipart = formSel.filter('[name="TIPART"]').val();
        nom_tipart = formSel.filter('[name="TIPART"]').find('option:selected').text();

        seccion = formSel.filter('[name="_SECCION1"]').val();
        nom_seccion = formSel.filter('[name="_SECCION1"]').find('option:selected').text();

        tema = formSel.filter('[name="_TEMA1"]').val();
        nom_tema = formSel.filter('[name="_TEMA1"]').find('option:selected').text();

        subtema = formSel.filter('[name="_SUBTEMA1"]').val();
        nom_subtema = formSel.filter('[name="_SUBTEMA1"]').find('option:selected').text();

        alta = formSel.filter('[name="_ALTA"]').val();
        nom_alta = formSel.filter('[name="_ALTA"]').find('option:selected').text();

        autor = formInp.filter('[name="AUTOR"]').val();
        titu = formInp.filter('[name="TITU"]').val();
        baja = formInp.filter('[name="BAJA"]').val();
        dia = formInp.filter('[name="DIA"]').val();
        diapub = formInp.filter('[name="DIAPUB"]').val();
        diaexp = formInp.filter('[name="DIAEXP"]').val();

        // Se verifica el candado
        if(Listartic.cargandoNoPub === true) {
            return;
        }
        // Se aplica el candado y se guarda el search
        Listartic.cargando = true;

        // Se construye objeto para la búsqueda
        BuscadorFields = {};
        Listartic.searchFlag = 1;

        BuscadorFields.seccion = seccion;
        BuscadorFields.tema = tema;
        BuscadorFields.subtema = subtema;
        BuscadorFields.autor = autor;
        BuscadorFields.titu = titu;

        BuscadorFields.baja = baja;
        BuscadorFields.dia = dia;
        BuscadorFields.autoinc = autoinc;
        BuscadorFields.diapub = diapub;
        BuscadorFields.diaexp = diaexp;

        BuscadorFields.tipart = tipart;
        BuscadorFields.nom_tipart = nom_tipart;
        BuscadorFields.nom_seccion = nom_seccion;
        BuscadorFields.nom_tema = nom_tema;
        BuscadorFields.nom_subtema = nom_subtema;

        BuscadorFields.nom_alta = nom_alta;
        BuscadorFields.alta = alta;

        LoadDiv.refrescaListadoNoPub();
        $.fn.colorbox.close();
    },

    // -------------------------------------------------------------------------
    validaFecha: function(dateStr, tipo) {

        // Si el campo está vacío, no valida nada
        if(typeof dateStr === 'undefined' || dateStr === '') {
            return true;
        }

        var datePat = /^(\d{1,2})(\/|-)(\d{1,2})(\/|-)(\d{4})$/;
        var matchArray = dateStr.match(datePat); // chequea formato.
        if (matchArray === null) {
              alert("La fecha " + tipo + " no tiene un formato válido. (dd/mm/aaaa)");
              return false;
        }

        var month = matchArray[3]; // parsea fecha en las variables.
        var day = matchArray[1];
        var year = matchArray[5];

        if (month < 1 || month > 12) { // chequea mes.
              alert("El Mes (fecha " + tipo + ") debe estar entre 1 y 12.");
              return false;
        }

        if (day < 1 || day > 31) {
              alert("El dia (fecha " + tipo + ") debe estar entre 1 y 31.");
              return false;
        }

        if ((month==4 || month==6 || month==9 || month==11) && day==31) {
              alert("El Mes " + month + " (fecha " + tipo + ") no tiene 31 días!");
              return false;
        }

        if (month == 2) { // chequea 29 febrero.
            var isleap = (year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0));
            if ( (day > 29) || (day==29 && !isleap) ) {
                  alert("Febrero " + year + " (fecha " + tipo + ") no tiene " + day + " días!");
                  return false;
            }
        }
        return true; // fecha valida.
    },

    // -------------------------------------------------------------------------
    resetForm: function() {

        $(Megalupa.formMegalupa).get(0).reset();
    },

    // -------------------------------------------------------------------------
    cargaCamposMegalupa: function() {

        if(typeof BuscadorFields.tipart !== 'undefined' && BuscadorFields.tipart !== null && BuscadorFields.tipart !== '') {
            $('select[name="TIPART"] option').each(function() {
                if($(this).val() == BuscadorFields.tipart) {
                    $(this).attr('selected', 'selected');
                }
            });
        }

        if(typeof BuscadorFields.seccion !== 'undefined' && BuscadorFields.seccion !== null && BuscadorFields.seccion !== '') {
            $('select[name="_SECCION1"] option').each(function() {
                if($(this).val() == BuscadorFields.seccion) {
                    $(this).attr('selected', 'selected');
                }
            });
            $('select[name="_SECCION1"]').trigger('change');

        }
        if(typeof BuscadorFields.tema !== 'undefined' && BuscadorFields.tema !== null && BuscadorFields.tema !== '') {
            $('select[name="_TEMA1"] option').each(function() {
                if($(this).val() == BuscadorFields.tema) {
                    $(this).attr('selected', 'selected');
                }
            });
            $('select[name="_TEMA1"]').trigger('change');

        }
        if(typeof BuscadorFields.subtema !== 'undefined' && BuscadorFields.subtema !== null && BuscadorFields.subtema !== '') {
            $('select[name="_SUBTEMA1"] option').each(function() {
                if($(this).val() == BuscadorFields.subtema) {
                    $(this).attr('selected', 'selected');
                }
            });
            $('select[name="_SUBTEMA1"]').trigger('change');

        }

        if(typeof BuscadorFields.autor !== 'undefined' && BuscadorFields.autor !== null && BuscadorFields.autor !== '') {
            $('input[name="AUTOR"]').val(BuscadorFields.autor);
        }
        if(typeof BuscadorFields.titu !== 'undefined' && BuscadorFields.titu !== null && BuscadorFields.titu !== '') {
            $('input[name="TITU"]').val(BuscadorFields.titu);
        }
        if(typeof BuscadorFields.baja !== 'undefined' && BuscadorFields.baja !== null && BuscadorFields.baja !== '') {
            $('input[name="BAJA"]').val(BuscadorFields.baja);
        }

        if(typeof BuscadorFields.dia !== 'undefined' && BuscadorFields.dia !== null && BuscadorFields.dia !== '') {
            $('input[name="DIA"]').val(BuscadorFields.dia);
        }
        if(typeof BuscadorFields.diapub !== 'undefined' && BuscadorFields.diapub !== null && BuscadorFields.diapub !== '') {
            $('input[name="DIAPUB"]').val(BuscadorFields.diapub);
        }
        if(typeof BuscadorFields.diaexp !== 'undefined' && BuscadorFields.diaexp !== null && BuscadorFields.diaexp !== '') {
            $('input[name="DIAEXP"]').val(BuscadorFields.diaexp);
        }

        if(typeof BuscadorFields.autoinc !== 'undefined' && BuscadorFields.autoinc !== null && BuscadorFields.autoinc !== '') {
            $('input[name="AUTOINC"]').val(BuscadorFields.autoinc);
        }
        if(typeof BuscadorFields.alta !== 'undefined' && BuscadorFields.alta !== null && BuscadorFields.alta !== '') {
            $('select[name="_ALTA"] option').each(function() {
                if($(this).val() == BuscadorFields.alta) {
                    $(this).attr('selected', 'selected');
                }
            });
        }
    }


};