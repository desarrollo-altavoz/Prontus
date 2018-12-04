
var BuscadorFields = {

    //    _rec_ini:   '',
    //
    //    tipart:     '',
    //    seccion:    '',
    //    tema:       '',
    //    subtema:    '',
    //    autor:      '',
    //    titu:       '',
    //
    //    baja:       '',
    //    dia:        '',
    //    autoinc:    '',
    //    diapub:     '',
    //    diaexp:     '',
    //
    //    nom_tipart:     '',
    //    nom_seccion:    '',
    //    nom_tema:       '',
    //    nom_subtema:    '',
    //
    //    nom_alta:   '',
    //    alta:       '',
    //
    //    ts: ''

};


var Buscador = {

    anchoMegalupa: '530px',
    altoMegalupa: '640px',
    urlMegaLupa: './prontus_art_megalupa.cgi',
    urlCargaMisBusquedas: './prontus_art_megalupa_cargar.cgi',
    urlBorraMisBusquedas: './prontus_art_megalupa_borrar.cgi',
    textoBuscador: ProntusLangController.getString('_search_by_title'),

    refreshMisBusquedas: true,
    arrMisBusquedas: null,

    // -------------------------------------------------------------------------
    showMegalupa: function(path_conf) {
        Buscador.showMisBusquedas(path_conf, false);
        var url = Buscador.urlMegaLupa + '?_path_conf=' + path_conf;
        $.fn.colorbox({
                open: true,
                href: url,
                width: Buscador.anchoMegalupa,
                height: Buscador.altoMegalupa,
                opacity: 0.8,
                // iframe: true,
                onComplete: function() {
                    Megalupa.iniciaMegalupa();
                }
        });
        return false;
    },

    // -------------------------------------------------------------------------
    showMisBusquedas: function(path_conf, flag) {
        if(flag) {
            if(Buscador.refreshMisBusquedas) {
                Buscador.cargarMisBusquedas(path_conf);
            } else {
                $('#layer_mis_busquedas .content').show('fast');
            }
        } else {
            $('#layer_mis_busquedas .content').hide();
        };
    },

    // -------------------------------------------------------------------------
    cargarMisBusquedas: function(path_conf) {
        var url = Buscador.urlCargaMisBusquedas + '?_path_conf=' + path_conf;
        $('#layer_mis_busquedas').load(url, function() {
            Buscador.refreshMisBusquedas = false;
            Buscador.showMisBusquedas(path_conf, true);
        });
    },
    // -------------------------------------------------------------------------
    aplicarBusqueda: function(link) {
        var myid = $(link).attr('id');
        var myts = myid.replace('search', '');

        BuscadorFields = {};
        Listartic.searchFlag = 1;
        var obj = Buscador.arrMisBusquedas['ts'+myts];
        for(x in obj) {
            if(x != 'name_search') {
                BuscadorFields[x] = obj[x];
            }
        };
        Buscador.showMisBusquedas(Admin.path_conf, false);
        LoadDiv.refrescaListadoNoPub();
    },

    // -------------------------------------------------------------------------
    borrarBusqueda: function(obj) {
        var myid = $(obj).attr('id');
        var myts = myid.replace('borrar', '');

        var data = {_id_busqueda: myts, _path_conf: Admin.path_conf};
        jQuery.get(Buscador.urlBorraMisBusquedas, data, function(json, textStatus, jqXHR) {
            Buscador.refreshMisBusquedas = true;
            // Si hubo un error, se maneja error, pero no se hace nada mas
            if (typeof json.error !== 'undefined' && json.error == '1') {
                $('#search'+myts).parent().before('<li class="alert">'+json.msg+'</li>');
                setTimeout(function() {
                    $('#search'+myts).parent().prev().fadeOut(function() {
                        $(this).remove();
                    });
                }, 2000);
                return false;
            }
            // Si no hubo error, se borra la busqueda
            $('#search'+myts).parent().fadeOut(function() {
                var ul = $(this).parent();
                $(this).remove();
                if($(ul).find('li').size() <= 0  &&  json.extra) {
                    $(ul).append(json.extra);
                };
            });
        }, 'json');
    },

    // -------------------------------------------------------------------------
    addBusqueda: function(myts, json) {
        if(Buscador.arrMisBusquedas === null) {
            Buscador.arrMisBusquedas = new Array();
        };
        Buscador.arrMisBusquedas['ts'+myts] = json;
    },

    // -------------------------------------------------------------------------
    limpiaFiltros: function() {
        // Se verifica el candado
        if(Listartic.cargandoNoPub === false) {
            Listartic.cargandoNoPub = true;
            Listartic.searchFlag = 0;
            BuscadorFields = {};
            LoadDiv.refrescaListadoNoPub();
        }
    },

    // -------------------------------------------------------------------------
    instalaHandlers: function() {

        Utiles.instalaHandlerBuscador('#search_texto', Buscador.textoBuscador);
    },

    // -------------------------------------------------------------------------
    buscarTit: function() {
        var search_texto = $('#search_texto').val();
        if(search_texto === '' || search_texto == Buscador.textoBuscador) {
            return;
        }

        // Se verifica el candado
        if(Listartic.cargandoNoPub === true) {
            return;
        }
        // Se aplica el candado y se guarda el search
        Listartic.cargando = true;

        // Se construye objeto para la búsqueda
        BuscadorFields = {};
        Listartic.searchFlag = 1;

        var regxp = /^\d{14}$/;
        if(regxp.test(search_texto)) {
            // Se ingresó un TS
            BuscadorFields.titu = '';
            BuscadorFields.ts = search_texto;
        } else {
            // Se ingresó un titular
            BuscadorFields.titu = search_texto;
            BuscadorFields.ts = '';
        }

        LoadDiv.refrescaListadoNoPub();
    }
};
