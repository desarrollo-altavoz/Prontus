var PortDD = {
    _path_conf: '',
    _prontus_id: '',
    _port: '',
    _edic: '',
    portlevels: '',
    grid_status: 'on',
    inProccess: 0,
    init: function () {
        Listartic.path_conf = PortDD._path_conf;
        Admin.prontus_id = PortDD._prontus_id;
        Admin.path_conf  = PortDD._path_conf;

        // Deshabilitar articulos duplicados en portadas.
        PortDD.deshabilitaArticDup();

        PortDD._findPortlLevels();
        
        PortDD.pingRecurso();
        Listartic.itemsPerPage = 10;
        PortDD._instalaSortable();
        PortDD.cargarArticulosNoPub();
        Listartic.instalaAgrandaFila();
        Listartic.instalaMouseover();
        Listartic.instalaDragAndDrop(Listartic.idUlNoPub);
        Listartic.procesarListado(Listartic.idUlNoPub, 'li');
        Listartic.instalaTooltipPublic();

        // Si se han activado las Pop
        $('a.open_in_pop').live('click', function() {
            Admin.openArtic(this);
            return false;
        });

        PortDD.modificaLinksEditArtic();

        // Sobreescirbir funcion.
        LoadDiv.refrescaListadoNoPub = PortDD.cargarArticulosNoPub;

    },

    // ------------------------------------------------------
    _instalaSortable: function () {
        $(".area").sortable({
            revert: true,
            connectWith: '.area',
            //~ placeholder: "item-area-placeholder",
            forcePlaceholderSize: true,
            dropOnEmpty: true,
            handle: '.tools, .tools-subitem',
            cancel: '.nohandler',
            toleranceElement: '> div',
            update: function (event, ui) {
                if ($(ui.item).is('li')) { // viene del listado de art. no pub.
                    PortDD._procesarReceiveFromNoPub(ui);
                } else {
                    PortDD._procesarReceive(ui);
                };
            },
            stop: function (event, ui) {
                PortDD._procesarStop(ui);
            },
            start: function(e, ui){
                //~ ui.placeholder.height(ui.item.height());
                //~ $( this ).sortable( 'refreshPositions' )
            }
        });

        $(".area").disableSelection();
        $('#prontusportdd-listnopub').draggable({
            handle: '#listarticnopub'
        });
    },

    // ------------------------------------------------------
    _procesarReceive: function (ui) {
        var sender_id = $(ui.sender).attr("id");
        var port = $(ui.sender).attr("rel");
        if (sender_id != null) {
            var matchs = sender_id.match(/area_(\d+)_(.*?)/);
            var area = matchs[1];
            $('input[name="_from_area_mod"]').val(area);
            $('input[name="_from_port_mod"]').val(port);
        }
        if (PortDD.inProccess == 1) return;
        var ts = $(ui.item).attr("rel");
        //~ console.log($(ui.item).parent().attr("id"));
        var area = ($(ui.item).parent().attr("id")).replace("area_", "");
        var ord = (ui.item.index()) + 1;
        if (typeof $(ui.item).find('.updating').attr("class") == 'undefined') {
            $(ui.item).append("<div class=\"updating\"><span><img src=\"/" + PortDD._prontus_id + "/cpan/core/imag/loader/ajax-loader.gif\" /></span></div>");
        }
        //~ $(".area").sortable("disable");
        //~ $(Listartic.idUlNoPub).sortable("disable");
    },

    _procesarReceiveFromNoPub: function (ui) {
        if (PortDD.inProccess == 1) return;
        // Es un li desde la lista de artics no publicados.
        var ts = $(ui.item).attr("title");
        ts = ts.substr(ts.length - 14);
        var strid = ui.item.parent().attr("id");
        if (strid) {
            var matchs = (strid).match(/area_(\d+)_(.*?)$/);
            var area = matchs[1];
            var port = matchs[2];
            var portfile =  $(ui.item).parent().attr("rel");
            var ord = (ui.item.index()) + 1;
            var parent = $(ui.item).parent();
            $(ui.item).remove(); // eliminar li para crear div.
            var html = '<div class="item-area" rel="' + ts + '">';
             html += '<input type="hidden" name="_area_' + ts + '" value="' + area + '" />';
             html += '<input type="hidden" name="_orden_' + ts + '" value="' + ord + '" />';
             html += '<input type="hidden" name="_port_' + ts + '" value="' + portfile + '" />';
             html += '<input type="hidden" name="_vb_' + ts + '" value="1" />';
             html += '<div class=\"updating2\"><span> <img src=\"/' + PortDD._prontus_id + '/cpan/core/imag/loader/ajax-loader.gif\" /></span></div>'
             html += '</div>';

            var sizeof = $("#area_" + area + "_" + port + " .item-area").size();
            if (sizeof > 0) {
                if (sizeof == (ord-1)) {
                    $("#area_" + area + "_" + port).append(html);
                } else {
                    $("#area_" + area + "_" + port + " .item-area").eq(ord - 1).before(html);
                };
            } else {
                $("#area_" + area + "_" + port).append(html);
                //~ console.log("append 2");
            }
                //~ $(".area").sortable("disable");
                //~ $(Listartic.idUlNoPub).sortable("disable");
        }
    },

    // ------------------------------------------------------
    _procesarStop: function (ui) {
        var matchs = ($(ui.item).parent().attr("id")).match(/area_(\d+)_(.*?)$/);
        var area = matchs[1];
        var port = matchs[2];
        $('input[name="_area_mod"]').val(area);
        $('input[name="_port_mod"]').val($(ui.item).parent().attr("rel"));
        $(ui.item).parent().children('.item-area').each(function () {
            var ts = $(this).attr("rel");
            var ord = $(this).index() + 1;
            //~ console.log("area = " + area + ", ts = " + ts + ", ord = " + ord);
            $('input[name="_area_' + ts + '"]').val(area);
            $('input[name="_orden_' + ts + '"]').val(ord);
            $('input[name="_port_' + ts + '"]').val($(ui.item).parent().attr("rel"));
        });
        PortDD._actualizarPreview();
    },
    
    // ------------------------------------------------------
    _procesarStopNoPub: function (ui) {
        //~ console.log("stop2");
        var ts = $(ui.item).attr("title");
        ts = ts.substr(ts.length - 14);
        var id = $('div[rel="' + ts + '"]').parent().attr("id");
        if (typeof id != 'undefined') {
            var matchs = (id).match(/area_(\d+)_(.*?)$/);
            //~ var port = (id).attr("rel");
            var area = matchs[1];
            $('div[rel="' + ts + '"]').parent().children('.item-area').each(function () {
                var ts = $(this).attr("rel");
                var ord = $(this).index() + 1;
                //~ console.log("area = " + area + ", ts = " + ts + ", ord = " + ord);
                $('input[name="_area_' + ts + '"]').val(area);
                $('input[name="_orden_' + ts + '"]').val(ord);
                //~ $('input[name="_port_' + ts + '"]').val(port);
            });
            PortDD.cargarArticulosNoPub();
            PortDD._actualizarPreview();
        }
    },
    
    _actualizarPreview: function () {
        var container = $('#prontusportddportada #portpreview');
        var w = container.width();
        var h = container.height();
        var html = '<div id="prontusportddloading" style="width: '+w+'px; height: '+h+'px;background:white;opacity:0.6;position: absolute;z-index:120;"></div>';
        container.prepend(html);
        PortDD.mostrarBotones(false);
        var url = $('#portpreview').attr("action");
        var data = $('#portpreview').serialize();
        var portlevels = '&_port_levels=' + PortDD.portlevels;
        data += portlevels;
        PortDD.inProccess = 1;
        PortDD._findPortlLevels();
        $('#port-modified').val(1);
        $.ajax({
            url: url,
            data: data,
            type: 'POST',
            dataType: 'json',
            cache: false,
            success: function (data) {
                if (data.status == 1) {
                    // Actualizar.
                    $('#prontusportddportada').html(data.html);
                } else if (data.status == 2) {
                    // recargar solo 1 area.
                    $('#area_' + data.area + '_' + data.portname).html(data.html);
                    $('#prontusportddloading').remove();

                    if (data.portname_from != '' && data.html_from != '' && data.area_from != '') {
                        $('#area_' + data.area_from + '_' + data.portname_from).html(data.html_from);
                    }
                    $('input[name="_area_mod"]').val('');
                    $('input[name="_from_area_mod"]').val('');
                    $('input[name="_port_mod"]').val('');
                    $('input[name="_from_port_mod"]').val('');
                }

                if (PortDD.grid_status == 'off') {
                    $('#prontusportddportada .area .item-area .tools').hide();
                }

                PortDD._instalaSortable();
                PortDD.instalaDragAndDropArtics(Listartic.idUlNoPub);
                PortDD.detectarAreasVacias();
                PortDD.modificaLinksEditArtic();
                PortDD.mostrarBotones(true);
                
            },
            error: function () {
            }
        });
        PortDD.inProccess = 0;
    },

    despublicarArticulo: function (obj) {
        if (PortDD.inProccess == 0) {
            PortDD.inProccess = 1;
            $(obj).parent().parent().fadeOut('fast', function () {
                var padre= $(this).parent();
                var items = padre.length;
                $(this).remove();
                items = items - 1;
                if (items == 0) {
                    padre.addClass("area-empty");
                    //~ var id = padre.attr("id");
                    //~ var inputname = '_no_upd_' + id;
                    //~ if ($('input[name="' + inputname + '"]').length == 0) {
                        //~ padre.append('<input type="hidden" name="' + inputname + '" value="1"/>');
                    //~ }
                }
                PortDD.inProccess = 0;
                PortDD._actualizarPreview();
                PortDD.cargarArticulosNoPub();
            });
        } else {
            alert(ProntusLangController.getString('_portdd_wait_for_process'));
        }
    },

    detectarAreasVacias: function () {
       $('#prontusportddportada').find('div[id^="area_"]').each(function () {
           var num_elem = $(this).find('.item-area').length;
           if (num_elem == 0) {
               $(this).addClass('area-empty');
           }
        }); 
    },

    cargarArticulosNoPub: function () {
        // Se aplica el Loading
        var alto = $(Listartic.idDivNoPub).height();
        if(alto < 200) {
            alto = 200;
        }
        var opts = {
            _path_conf: PortDD._path_conf,
            _port: PortDD._port,
            _edic: PortDD._edic,
            _orden_lista: Listartic.ordenLista,
            _filas_x_pag: Listartic.itemsPerPage,
            _search: Listartic.searchFlag
        };

        $.extend(opts, BuscadorFields);
        
        $(Listartic.idDivNoPub).hide().html('<div class="div-loading" style="height:'+alto+'px;"><div class="list-loading">&nbsp;</div></div>').show();
        $.ajax({
            url: '/' + DIR_CGI_CPAN + '/prontus_art_listnopub.cgi',
            data: opts,
            dataType: 'html',
            cache: false,
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                SubmitForm.handleError(LoadDiv.urlNoPub, XMLHttpRequest, textStatus, errorThrown);
            },
            success: function(resp, textStatus) {
                $(Listartic.idDivNoPub).hide().html(resp).fadeIn(100);
                PortDD.instalaDragAndDropArtics(Listartic.idUlNoPub);
                PortDD.procesarListado(Listartic.idUlNoPub, 'li');
                Listartic.instalaMouseover();
                Listartic.cargandoNoPub = false;
                PortDD.modificaLinksEditArtic();
            }
        });
    },

    procesarListado: function(listado, elementos) {
        $(listado).each(function() {
            var theId = $(this).attr('id');
            var patt = /^(area-)(\d+)$/gi;
            var res = theId.match(patt);
            if(res === null) {
                $('#prontusportddportada').find('.item-area').each(function(orden) {
                    var theTS = $(this).attr('rel');
                    // Para ocultar los ya publicados
                    $(Listartic.idUlNoPub + ' li[title="artic'+theTS+'"]').addClass('disabled');
                });
            } else {
                var arr = res[0].split('-');
                var area = arr[1];
                $(this).find(elementos).each(function(orden) {
                    if(!$(this).parent().hasClass('area-list')) {
                        return;
                    }
                    var theId = $(this).attr('title');
                    var theTS = theId.substr(theId.length - 14);
                    orden++;
                    if($(this).find(Listartic.controlClass + ' input.area').size() > 0) {
                        $(this).find('input.area').val(area);
                        $(this).find('input.orden').val(orden);
                        //alert($(this).find('input[name="_orden_'+theTS+'"]').val());
                    } else {
                        var controls = Listartic.generaControles(theTS, area, orden);
                        $(this).find(Listartic.controlClass).html(controls);
                    }

                    // Para ocultar los ya publicados
                    $(Listartic.idUlNoPub + ' li[title="artic'+theTS+'"]').addClass('disabled');
                });
            }
        });
        if(Listartic.areaActiva !== '') {
            $('#artics').removeClass('disable-flecha');
        } else {
            $('#artics').addClass('disable-flecha');
        };
        Listartic.procesarCorruptos(listado, elementos);
        Listartic.limpiarControles();
    },

    instalaDragAndDropArtics: function(selector) {
        $(selector).sortable({
            // items: 'li:not(".disabled")',
            cancel: '.disabled, ._artic_sin_file, .editable_list0',
            connectWith: '.area',
            dropOnEmpty: true,
            //~ placeholder: "item-area-placeholder",
            handle: '.mover .handler',
            cursorAt: {left: 235},
            revert: true,
            stop: function (event, ui) {
                PortDD._procesarStopNoPub(ui);
            }
        });
    },
    
    modificaLinksEditArtic: function () {
        $('a.editar_item').each(function () {
            var href = $(this).attr("href");
            if (href.search(/&_port_dd=1/) < 0) {
                href += '&_port_dd=1';
            }
            eval("var expre = /\\/" + DIR_CGI_CPAN + "\\//;");
            if (href.search(expre) < 0) {
                href = '/' + DIR_CGI_CPAN + '/' + href;
            }
            
            $(this).attr("href", href);
            $(this).removeClass('open_normally');
            $(this).addClass('open_in_pop');
        });
    },

    guardarPortada: function () {
        PortDD.mostrarBotones(false);
        var data = $('#portpreview').serialize();
        $.ajax({
            url: '/' + DIR_CGI_CPAN + '/prontus_dd_public.cgi',
            data: data,
            type: 'POST',
            dataType: 'json',
            success: function (resp) {
                if (resp.status == 1) {
                    PortDD._actualizarPreview();
                    PortDD.cargarArticulosNoPub();
                    $('#port-modified').val(0);
                }
            },
            error: function () {
            }
        });
    },
    
    refrescar: function () {
        PortDD.mostrarBotones(false);
        if ($('#port-modified').val() == 1) {
            if (confirm(ProntusLangController.getString('_portdd_unsaved_changes_confirm_refresh'))) {
                window.location.href = window.location.href;
            } else {
                PortDD.mostrarBotones(true);
            }
        } else {
            window.location.href = window.location.href;
        }
        //~ PortDD._actualizarPreview();
        //~ PortDD.cargarArticulosNoPub();
    },

    mostrarBotones: function (st) {
        if (!st) {
            $('#prontusportdd-botones a').hide();
            $('#prontusportdd-botones .loading-action').show();
        } else {
            $('#prontusportdd-botones a').show();
            $('#prontusportdd-botones .loading-action').hide();
        }
    },

    pingRecurso: function () {
        Admin.urlPing = '/' + DIR_CGI_CPAN + '/prontus_ping_inuse.cgi';
        Admin.pingRecurso('port', PortDD.nom_recurso, PortDD.pingRecurso);
    },

    verModulo: function (port) {
        var divid = "#portmod_" + port;
        $.colorbox({inline: true, href: divid, open: true});
    },

    setGlobalMsg: function (msg, tipo) {
        var img = '<img src="/' + PortDD._prontus_id + '/cpan/core/imag/boto/msg-' + tipo + '.png" />';
        $('#global-msg').html(img + '<span>' + msg + '</span>').fadeIn('fast');
    },

    _findPortlLevels: function () {
        var portlevels = {};
        $('#prontusportddportada div[id^="area_"]').each(function () {
            if ($(this).hasClass('lv1')) {
                var port = $(this).attr("rel");
                if (!portlevels[port]) {
                    portlevels[port] = 1;
                }
            } else if ($(this).hasClass('lv2')) {
                var port = $(this).attr("rel");
                if (!portlevels[port]) {
                    portlevels[port] = 2;
                }
            } else {
                var port = $(this).attr("rel");
                if (!portlevels[port]) {
                    portlevels[port] = 0;
                }
            }
        });
        
        PortDD.portlevels = JSON.stringify(portlevels);
    },

    deshabilitaArticDup: function () {
        var tslist = [];
        var duplicados = {};
        var x = 0;
        $('input[name^="_area_"]').each(function () {
            var matchs = $(this).attr("name").match(/^_area_(\d{14})$/);
            if (matchs != null) {
                var ts = matchs[1];
                if (!tslist[ts]) {
                    tslist[ts] = 1;
                } else {
                    duplicados[x] = ts;
                    x++;
                }
            }
        });

        var arraylen = Object.keys(duplicados).length;

        if (arraylen > 0) {
            var strdups = '';
            for (x = 0; x < arraylen; x++) {
                var ts = duplicados[x];
                $('div[rel="' + ts + '"]').addClass('nohandler');
                $('div[rel="' + ts + '"]').prepend('<div class="dup"></div>');
            };

            $('.item-area > .tools').hide();
            $('.item-area > .tools-subitem').hide();
            $('#prontusportdd-listnopub').hide();
            $('#prontusportdd-botones').hide();
            PortDD.setGlobalMsg(ProntusLangController.getString('_portdd_duplicated_art_error') + strdups, 'error');
            return;
        }
    },

    toggleAreaDD: function (o) {
        var imgObj = $(o).children();
        var st = $('#prontusportddportada .area .item-area .tools').toggle().css('display');
        
        if (st == 'block') {
            var txt = ProntusLangController.getString('_portdd_hide_areas');
            var src = imgObj.attr("src");
            src = src.replace('grid_of.png', 'grid_on.png');
            imgObj.attr("src", src);
            imgObj.attr("alt", txt);
            imgObj.attr("title", txt);
            PortDD.grid_status = 'on';
        } else {
            var txt = ProntusLangController.getString('_portdd_visualize_areas');
            var src = imgObj.attr("src");
            src = src.replace('grid_on.png', 'grid_of.png');
            imgObj.attr("src", src);
            imgObj.attr("alt", txt);
            imgObj.attr("title", txt);
            PortDD.grid_status = 'off';
        }
    }

};
