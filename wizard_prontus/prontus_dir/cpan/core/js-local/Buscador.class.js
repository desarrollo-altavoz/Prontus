
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
    altoMegalupa: '580px',
    urlMegaLupa: './prontus_art_megalupa.cgi',
    textoBuscador: 'Buscar por Titular',

    // -------------------------------------------------------------------------
    showMegalupa: function(path_conf) {
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
