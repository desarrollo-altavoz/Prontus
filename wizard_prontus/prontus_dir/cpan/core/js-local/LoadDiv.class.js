
var LoadDiv = {

    urlNoPub: './prontus_art_listnopub.cgi',
    urlPub: './prontus_art_listpub.cgi',

    //cargandoNoPub: false,
    //cargandoPub: false,

    // -------------------------------------------------------------------------
    refrescaListadoPub: function() {
        Listartic.cargandoPub = true;
        var portada = $('#cmb_port').val();
        var edicion = $('#cmb_edic').val();
        var nom_portada = $('#cmb_port option:selected').text();
        var opts1 = {
            _path_conf: Listartic.path_conf,
            _port: portada,
            _edic: edicion,
            nom_port: nom_portada
        };
        Listartic.areaActiva = '';
        LoadDiv.loadPub(opts1);
    },

    // -------------------------------------------------------------------------
    loadPub: function(opts) {

        // Se aplica el Loading
        var alto = $(Listartic.idDivPub).height();
        if(alto < 200) {
            alto = 200;
        }
        $(Listartic.idDivPub).hide().html('<div style="height:'+alto+'px;"><div class="list-loading">&nbsp;</div></div>').show();
        $.ajax({
            url: LoadDiv.urlPub,
            data: opts,
            dataType: 'html',
            cache: false,
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                SubmitForm.handleError(LoadDiv.urlPub, XMLHttpRequest, textStatus, errorThrown);
            },
            success: function(resp, textStatus) {

                $('#cmb_edic option[value="'+opts._edic+'"]').attr('selected', 'selected').change();
                $('#cmb_port option[value="'+opts._port+'"]').attr('selected', 'selected').change();
                $('#nomPortada').text(opts.nom_port);
                $('#filePortada').text(opts._port);

                $(Listartic.idDivPub).hide().html(resp).fadeIn(300);
                Listartic.instalaDragAndDrop(Listartic.idUlPub);
                Listartic.procesarListado(Listartic.idUlPub, 'li');
                Listartic.instalaMouseover();
                Preview.startPreview();
                Listartic.cargandoPub = false;
            }
        });
    },

    // -------------------------------------------------------------------------
    refrescaListadoNoPub: function() {
        Listartic.cargandoNoPub = true;
        var portada = $('#cmb_port').val();
        var edicion = $('#cmb_edic').val();
        var opts2 = {
            _path_conf: Listartic.path_conf,
            _port: portada,
            _edic: edicion,
            _orden_lista: Listartic.ordenLista,
            _filas_x_pag: Listartic.itemsPerPage,
            _search: Listartic.searchFlag
        };

        $.extend(opts2, BuscadorFields);
        LoadDiv.loadNoPub(opts2);
    },

    // -------------------------------------------------------------------------
    loadNoPub: function(opts) {

        // Se aplica el Loading
        var alto = $(Listartic.idDivNoPub).height();
        if(alto < 200) {
            alto = 200;
        }
        $(Listartic.idDivNoPub).hide().html('<div style="height:'+alto+'px;"><div class="list-loading">&nbsp;</div></div>').show();
        $.ajax({
            url: LoadDiv.urlNoPub,
            data: opts,
            dataType: 'html',
            cache: false,
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                SubmitForm.handleError(LoadDiv.urlNoPub, XMLHttpRequest, textStatus, errorThrown);
            },
            success: function(resp, textStatus) {
                $(Listartic.idDivNoPub).hide().html(resp).fadeIn(100);
                Listartic.instalaDragAndDrop(Listartic.idUlNoPub);
                Listartic.procesarListado(Listartic.idUlNoPub, 'li');
                Listartic.instalaMouseover();
                Listartic.cargandoNoPub = false;
            }
        });
    }
};
