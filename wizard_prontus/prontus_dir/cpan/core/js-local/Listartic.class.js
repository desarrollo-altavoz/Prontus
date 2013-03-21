
var Listartic = {

    TOTAL_PORTS_values: [],
    TOTAL_PORTS_labels: [],

    itemsPerPage: 10,
    ordenLista: 'C', // 'F' (fecha public, default)  / 'T' (titular) / 'C' creacion
    searchFlag: 0,

    cargandoPub: false,
    cargandoNoPub: false,

    saving: false,
    draging: false,

    idDivPub: '#cont-pub',
    idDivNoPub: '#cont-nopub',
    idUlPub: '#cont-pub .area-list',
    idUlNoPub: '#cont-nopub .area-list',
    controlClass: '.controles',

    prontus_id: '',
    path_conf: '',

    urlBorrar: './prontus_art_borrar.cgi',
    urlGuardar: './prontus_art_public.cgi',
    urlPing: './prontus_ping_inuse.cgi',
    urlRayo: './prontus_cluster_preport.cgi',
    urlAdministrarPortadas: './prontus_pltport_admin.cgi',

    animationSlideSpeed: 250,
    timePing: 10000,
    timerPingId: null,

    altoFila: 26, //Alto de la fila colapsada
    timerMouseEnterID: null, //Timer para el setTimeout
    timerMouseEnter: 300,

    areaActiva: '', //

    msgChangePort: 'La portada ha sido modificada, debe guardar para conservar los cambios',
    msgChangePortBeforeUnload: 'La portada ha sido modificada. ¿Está seguro que desea abandonar esta página?',
    msgChangePortConfirm: 'La portada ha sido modificada. ¿Está seguro que desea refrescar el listado de artículos publicados?',
    modPort: false,

    init: function() {

        Listartic.prontus_id = Admin.prontus_id;
        Listartic.path_conf = Admin.path_conf;
        //Admin.prontus_id = prontus;

        // Maneja los botones que Manejan los Folds de todas las áreas
        $('#colapsar-todo .right').click(function() {
            $('.rotulo .flecha span').removeClass('opened').addClass('closed');
            $(Listartic.idUlPub + ':visible').slideUp(Listartic.animationSlideSpeed);
        });
        $('#colapsar-todo .down').click(function() {
            $('.rotulo .flecha span').removeClass('closed').addClass('opened');
            $(Listartic.idUlPub + ':hidden').slideDown(Listartic.animationSlideSpeed);
        });

        // Instala los Handlers
        Buscador.instalaHandlers();         // Para los handlers del buscador
        Listartic.instalaAgrandaFila();     // Instala los onclick para agrandar las filas
        Listartic.instalaReceiveAreas();    // Para que las Areas se activen y desactiven
        Listartic.instalaPublicar();        // Para el boton de publicación directa
        Listartic.instalaDespublicar();     // Para el boton de despublicación directa
        Listartic.instalaHandlerAreas();    // Para los colapsar y descolapsar de las áreas
        Listartic.instalaTooltipPublic();   // Para el tooltip de donde esta publicado el articulo
        Listartic.instalaMouseover();

        // Guarda las portadas totales y carga inicialmente
        Listartic.mostrarEdiciones();
        Listartic.backupTotalPorts();
        Listartic.cargaComboPortadas();

        // Carga el estado actual
        Listartic.cargaEstado();
        Listartic.cambiaLinkPort();

        // Instala los Listados
        Acciones.refrescarListados();

        // Para reportarse en el server
        Listartic.pingRecurso();

        // Para el Preview
        Preview.init();
        
        // Para el modificado a las
        Listartic.updateLastMod();
    },

    // -------------------------------------------------------------------------
    instalaReceiveAreas: function() {
        $('#cont-pub .rotulo .rotulo-interno').live('click', function() {
            var area = $(this).parent().next().attr('id');
            if(area.length <= 5) {
                return;
            }
            area = area.substr(5);
            if(area == Listartic.areaActiva) {
                Listartic.areaActiva = '';
                $('.rotulo').removeClass('selected');
                $('#artics').addClass('disable-flecha');
            } else {
                Listartic.areaActiva = area;
                $('.rotulo').removeClass('selected');
                $('#artics').removeClass('disable-flecha');
                $(this).parent().addClass('selected');
                Admin.displayMessage('El área ' + area + ' ha sido activada. Ahora puede usar el botón "Publicar en Área Activa".', 'info');
            }
        });
    },
    // -------------------------------------------------------------------------
    instalaAgrandaFila: function() {

        $('ul.area-list li .agranda_fila .down').live('click', function() {
            Listartic.closeFila($(this).parents('li'));
        });

        $('ul.area-list li .agranda_fila .right').live('click', function() {
            Listartic.openFila($(this).parents('li'));
        });

        $('.links-utiles .agranda-fila-all .right').live('click', function() {
            $(this).parents('.col470').find('.area-list li').each(function() {
                Listartic.closeFila(this, true);
            });
        });

        $('.links-utiles .agranda-fila-all .down').live('click', function() {
            $(this).parents('.col470').find('.area-list li').each(function() {
                Listartic.openFila(this, true);
            });
        });
    },
    // -------------------------------------------------------------------------
    openFila: function(objList, anulaEfecto) {
        if(! $(objList).is(':visible')) {
            return;
        }
        $(objList).find('.agranda_fila img').hide();
        $(objList).find('.down').show();
        var alto = $(objList).find('.fila1').height() + 2;
        if(typeof anulaEfecto === 'undefined' || anulaEfecto === false) {
            $(objList).animate({height: alto + 'px'}, Listartic.animationSlideSpeed);
        } else {
            $(objList).height(alto);
        }

        $(objList).find('.titulo').addClass('nohover');
        $(objList).find('.titulo').find('.status').show();
        $(objList).find('.titulo').find('.vobo').show();
        $(objList).find('.titulo').find('.autoinc').show();
        $(objList).find('.titulo').find('.botones').hide();
    },
    // -------------------------------------------------------------------------
    closeFila: function(objList, anulaEfecto) {
        if(! $(objList).is(':visible')) {
            return;
        }
        $(objList).find('.agranda_fila img').hide();
        $(objList).find('.right').show();
        if(typeof anulaEfecto === 'undefined' || anulaEfecto === false) {
            $(objList).animate({height: Listartic.altoFila + 'px'}, Listartic.animationSlideSpeed);
        } else {
            $(objList).height(Listartic.altoFila);
        }

        $(objList).find('.titulo').removeClass('nohover');
    },

    // -------------------------------------------------------------------------
    instalaPublicar: function() {

        // Para el handler del boton despublicar
        $('.area-list .flecha_publicar').live('click', function() {
            var theLi = $(this).parents('.fila1').parent();
            var titlepub = theLi.attr('title');
            if($(Listartic.idUlPub + ' li[title="'+titlepub+'"]').size() >= 1) {
                return;
            }
            //theLi.clone().prependTo('#area-'+Listartic.areaActiva).fadeIn().addClass('moved').height(Listartic.altoFila);
            var cloned = theLi.clone().prependTo('#area-'+Listartic.areaActiva).fadeIn().addClass('moved');
            Listartic.procesarListado(Listartic.idUlPub, 'li');
            //LoadDiv.refrescaListadoNoPub();
            Preview.startPreview();
            Admin.displayMessage(Listartic.msgChangePort, 'alert');
            Listartic.instalaPortModProtector();
            Listartic.instalaMouseover();

            Listartic.habilitarVoBo(cloned);
            return false;
        });
    },

    // -------------------------------------------------------------------------
    instalaDespublicar: function() {

        // Para el handler del boton despublicar
        $('.area-list .flecha_mover').live('click', function() {
            $(this).parents('.fila1').parent().fadeOut('slow', function() {
                var titlenopub = $(this).attr('title');
                $(Listartic.idUlNoPub + ' li[title="'+titlenopub+'"]').fadeOut().remove();
                //$(this).prependTo(Listartic.idUlNoPub).fadeIn().addClass('moved').height(Listartic.altoFila);
                $(this).prependTo(Listartic.idUlNoPub).fadeIn().addClass('moved');
                //Listartic.intercalaGris(Listartic.idUlPub);
                //Listartic.intercalaGris(Listartic.idUlNoPub);
                Preview.startPreview();
                Admin.displayMessage(Listartic.msgChangePort, 'alert');
                Listartic.instalaPortModProtector();
                //Listartic.procesarCorruptos(Listartic.idUlNoPub, 'li');
                //LoadDiv.refrescaListadoNoPub();
                var item = $(this).after();
                Listartic.quitarVoBo(item);
            });
            return false;
        });
    },

    // -------------------------------------------------------------------------
    instalaHandlerAreas: function() {

        // Para manejar los Fold de las áreas
        $('.rotulo .flecha span').live('click', function() {
            if($(this).hasClass('opened')) {
                $(this).removeClass('opened').addClass('closed').attr('title', 'Expandir');
                $(this).parent().parent().next().slideUp(Listartic.animationSlideSpeed);
            } else {
                $(this).removeClass('closed').addClass('opened').attr('title', 'Contraer');
                $(this).parent().parent().next().slideDown(Listartic.animationSlideSpeed);
            }
            return false;
        });
    },

    // -------------------------------------------------------------------------
    instalaTooltipPublic: function() {
		
		$(document).tooltip({
			position: {
				my: "right middle", 
				at: "left-15 middle"
			},
			show: {effect: "fadeIn", duration: 200 },
			hide: {effect: "hide" },
			items: ".iconos img.artic_pub",
			content: function() {
				//alert($(this).parent().find('.tooltip-ini-pub').html());
				return $(this).parent().find('.tooltip-ini').html();
			}
		});
		/**
        $('.iconos img.artic_pub').live('mouseover', function() {
            var thishref = $(this).attr('src');
            if(thishref.indexOf('port_artic_si') > 0) {
                $('#tooltip-public .middle').empty();
                $(this).parent().find('.tooltip-ini-pub').clone().appendTo('#tooltip-public .middle');
                var newoffset = $(this).parent().offset();
                //alert('top:'+newoffset.top+', left:'+newoffset.left);
                newoffset.left = newoffset.left - 300;
                newoffset.top = newoffset.top - 10;
                $('#tooltip-public').show().offset({top:newoffset.top, left:newoffset.left});
            };
        }).live('mouseout', function() {
            //$('#tooltip-public').hide().empty().offset({top:0, left:0});
            $('#tooltip-public').offset({top:0, left:0}).hide();
        });
        * **/
    },

    // -------------------------------------------------------------------------
    instalaDragAndDrop: function(selector) {
        $(selector).sortable({
            // items: 'li:not(".disabled")',
            cancel: '.disabled, ._artic_sin_file, .editable_list0',
            connectWith: '.area-list',
            dropOnEmpty: true,
            handle: '.mover .handler',
            opacity: 0.75,
            update: function(event, ui) {
                $(ui.item).addClass('moved');
                Listartic.procesarListado(selector, 'li');
                if(selector == Listartic.idUlPub) {
                    Preview.startPreview();
                    Admin.displayMessage(Listartic.msgChangePort, 'alert');
                    Listartic.instalaPortModProtector();
                }
            },
            receive: function(event, ui) {
                if($(ui.item).parents('#cont-pub').size() >= 1) {
                    LoadDiv.refrescaListadoNoPub();
                    Listartic.habilitarVoBo(ui.item);
                } else {
                    var titlenopub = $(ui.item).attr('title');
                    if ($(Listartic.idUlNoPub + ' li[title="'+titlenopub+'"]').size() >= 1) {
                        $(ui.item).addClass('no-remove');
                        $(Listartic.idUlNoPub + ' li[title="'+titlenopub+'"]').not('.no-remove').fadeOut().remove();
                        $(ui.item).removeClass('no-remove');
                        Listartic.deshabilitarVoBo(ui.item);
                    }
                }

            },
            stop: function(event, ui) {
                Listartic.draging = false;
            },
            start: function(event, ui) {
                Listartic.draging = true;
            }
        });
    },

    // -------------------------------------------------------------------------
    instalaPortModProtector: function(flag) {
        if(typeof flag === 'undefined' || flag === true) {
            Listartic.modPort = true;
            window.onbeforeunload = function() {
                return Listartic.msgChangePortBeforeUnload;
            };
        } else {
            Listartic.modPort = false;
            window.onbeforeunload = null;
        }
    },

    // -------------------------------------------------------------------------
    procesarListado: function(listado, elementos) {
        $(listado).each(function() {
            var theId = $(this).attr('id');
            var patt = /^(area-)(\d+)$/gi;
            var res = theId.match(patt);
            if(res === null) {
                $(Listartic.idUlPub).find('li').each(function(orden) {
                    if(!$(this).parent().hasClass('area-list')) {
                        return;
                    }
                    var theId = $(this).attr('title');
                    var theTS = theId.substr(theId.length - 14);
                    //alert(theTS);
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
        //Listartic.intercalaGris(listado);
        //$(".area-list li.disabled .fila1, .area-list li._artic_sin_file .fila1").css('background-color', '#ffffea');
    },

    // -------------------------------------------------------------------------
    procesarCorruptos: function(listado, elementos) {
		$(listado).each(function() {
            $(this).find(elementos + '._artic_sin_file').each(function() {
                // Se ocultan los datos que no se necesitan
                $(this).find('.status').remove();
                $(this).find('.datos').html('');
                // Se muestran los datos del artículo eliminado
                var ts = $(this).find('.titulo-left .ocultar').html();
                var tit_artic_sin_file = 'Artículo Eliminado o Corrupto';
                $(this).find('.titulo-left span:first').css('color', '#800000').html('('+ts+')');
                $(this).find('.titulo-left a').replaceWith(tit_artic_sin_file);
                $(this).find('.datos').html('');
                $(this).find('.datos').append('<span class="msg-pub">Para eliminar de la portada, debe guardar ésta</span>');
                $(this).find('.datos').append('<span class="msg-nopub">Para eliminar del listado, se debe "Regenerar tabla de Artículos"</span>');
                // $(this).find('.titulo-left').css('padding-top', '5px');
                // Se agrega campo oculto para que el Prontus lo borre
                $(this).find('.controles').html('<input type="hidden" name="_corrupt_'+ts+'" value="1" class="area" />');
            });
        });
    },

    // -------------------------------------------------------------------------
    limpiarControles: function() {
        $(Listartic.idUlNoPub + ' .item-content ' + Listartic.controlClass).remove();
    },

    // -------------------------------------------------------------------------
    intercalaGris: function(idListado) {
        $(idListado + ' .fila1').removeClass('gris');
        $(idListado + ' li .fila1:odd').addClass('gris');
    },

    // -------------------------------------------------------------------------
    generaControles: function(theTS, area, orden) {
        var str = '<input type="hidden" name="_area_'+theTS+'" value="'+area+'" class="area" />' +
                '<input type="hidden" name="_vb_'+theTS+'" value="1" class="vobo" />' +
                '<input type="hidden" name="_orden_'+theTS+'" value="'+orden+'" class="orden" />' + "\n";
        return str;
    },

    // -------------------------------------------------------------------------
    mostrarEdiciones: function() {
        if($('#_multi_edicion').val() == 'SI') {
            $('#div_cmb_edic').show();
        } else {
            $('#cmb_edic').html('<option value="base">base</option>');
        }
    },

    // -------------------------------------------------------------------------
    backupTotalPorts: function() {

        if($('#_multi_edicion').val() == 'SI') {
            var values = [];
            var labels = [];
            $('#cmb_port option').each(function(idx) {
                values[idx] = $(this).val();
                labels[idx] = $(this).text();
            });
            Listartic.TOTAL_PORTS_values = values;
            Listartic.TOTAL_PORTS_labels = labels;
            //alert(values.length + ', ' + values[1]);
        }
    },

    // -------------------------------------------------------------------------
    cargaComboPortadas: function() {

        if($('#_multi_edicion').val() != 'SI') {
            $('#total_ports').html('Nº de Portadas: ' + $('#cmb_port option').size());
            return;
        }

        var curr_edic = $('#cmb_edic').val();
        if(curr_edic === '') {
            return;
        }

        var value_ini_selected = Listartic.restauraPorts();

        $('#cmb_port option').each(function() {

            var len = (arr_base_ports.length-1);
            var found;
            var j;
            var valopt = $(this).val();
            // Si estoy parado en la edicion base
            if (curr_edic == 'base') {
                found = 0;
                for(j = len; j >= 0; j--) {
                    if (valopt == arr_base_ports[j]) {
                        found = 1;
                    }
                }
                if (!found) {
                    $(this).remove();
                }

            // Si no estoy parado en la edicion base:
            } else {
                found = 0;
                for(j = len; j >= 0; j--) {
                    if (valopt == arr_base_ports[j]) {
                        found = 1;
                    }
                }
                if (found) {
                    $(this).remove();
                }
            }
        });
        $('#cmb_port option[value="'+value_ini_selected+'"]').attr('selected', 'selected');
        $('#total_ports').html('Nº de Portadas: ' + $('#cmb_port option').size());
    },

    // -------------------------------------------------------------------------
    restauraPorts: function() {
        // Borra la combo y la carga con el total de portadas
        var value_selected = $('#cmb_port option:selected').val();
        var len = Listartic.TOTAL_PORTS_values.length;
        $('#cmb_port').html('');

        var values = Listartic.TOTAL_PORTS_values;
        var labels = Listartic.TOTAL_PORTS_labels;

        for(var i = 0; i < len; i++) {
            $('#cmb_port').append('<option value="' + values[i] + '">' + labels[i] + '</option>');
        }
        return value_selected;
    },


    // -------------------------------------------------------------------------
    cargaEstado: function() {

        var edicion = Cookies.readCookie('edic');
        if(edicion !== null && edicion !== '' && $('#div_cmb_edic').is(':visible')) {
            $('#cmb_port option[value="'+portada+'"]').attr('selected', 'selected');
        }

        var portada = Cookies.readCookie('port');
        if(portada !== null && portada !== '') {
            $('#cmb_port option[value="'+portada+'"]').attr('selected', 'selected');
        }

        var items = Cookies.readCookie('itemsPerPage');
        if(items !== null && items != Listartic.itemsPerPage) {
            var obj = $('.mostrar a[rel="'+items+'"]');
            $(obj).parent().find('a').removeClass('selected');
            $(obj).addClass('selected');
            Listartic.itemsPerPage = items;
        }

        var orden = Cookies.readCookie('ordenLista');
        if(orden !== null && orden != Listartic.ordenLista) {
            var obj = $('.mostrar a[rel="'+orden+'"]');
            $(obj).parent().find('a').removeClass('selected');
            $(obj).addClass('selected');
            Listartic.ordenLista = orden;
        }
    },

    // -------------------------------------------------------------------------
    guardaEstado: function() {

        var portada = $('#cmb_port').val();
        Cookies.createCookie('port', portada, 365);

        var edicion = $('#cmb_edic').val();
        Cookies.createCookie('edic', edicion, 365);

        Cookies.createCookie('itemsPerPage', Listartic.itemsPerPage, 365);

        Cookies.createCookie('ordenLista', Listartic.ordenLista, 365);
    },

    // -------------------------------------------------------------------------
    cambiaPortada: function() {
        if(Listartic.cargandoPub === false) {
            $('#main').find('.lockscreen').remove();
            $('#lock_recurso').remove();
            Admin.closeMessage();
            // Se procesa el listado de la portada
            LoadDiv.refrescaListadoPub();
            if(Listartic.cargandoNoPub === false) {
                // Se procesa el listado de los no publicados
                LoadDiv.refrescaListadoNoPub();
            }
            Listartic.areaActiva = '';
            Listartic.pingRecurso();
            Listartic.guardaEstado();
            Listartic.cambiaLinkPort();
        }
    },

    // -------------------------------------------------------------------------
    cambiaEdicion: function() {

        // Se carga la combo de portadas
        Listartic.cargaComboPortadas();

        if(Listartic.cargandoPub === false) {
            Admin.closeMessage();
            // Se procesa el listado de la portada
            LoadDiv.refrescaListadoPub();
            Listartic.pingRecurso();
            Listartic.guardaEstado();
            Listartic.cambiaLinkPort();
            // Se refresca el listado de no publicados
            LoadDiv.refrescaListadoNoPub();
        }
    },

    // -------------------------------------------------------------------------
    cambiaLinkPort: function() {
        var edic = $('#cmb_edic').val();
        var port = $('#cmb_port').val();
        if(edic === '') {
            edic = 'base';
        }
        var theLink = '/' + Admin.prontus_id + '/site/edic/' + edic + '/port/' + port;
        $('#link-port').attr('href', theLink);
    },

    // -------------------------------------------------------------------------
    cambiarArticPerPage: function(obj) {

        // Se verifica el candado
        if(Listartic.cargandoNoPub === true) {
            return;
        }

        // Se procesa el numero
        var numb = $(obj).text();
        if(numb == Listartic.itemsPerPage) {
            return;
        }

        // Se aplica el candado
        Listartic.cargandoNoPub = true;

        // Se aplica el nuevo estilo
        Listartic.itemsPerPage = numb;
        $(obj).parent().find('a').removeClass('selected');
        $(obj).addClass('selected');

        // Se guarda el estado
        Listartic.guardaEstado();

        // Se procesa el listado de la portada
        LoadDiv.refrescaListadoNoPub();
    },

    // -------------------------------------------------------------------------
    cambiarOrdenTipo: function(obj, tipo) {

        // Se verifica el candado
        if(Listartic.cargandoNoPub === true) {
            return;
        }

        // Se procesa el numero
        if(tipo == Listartic.ordenLista) {
            return;
        }

        // Se aplica el candado
        Listartic.cargandoNoPub = true;

        // Se aplica el nuevo estilo
        Listartic.ordenLista = tipo;
        $(obj).parent().find('a').removeClass('selected');
        $(obj).addClass('selected');

        // Se guarda el estado
        Listartic.guardaEstado();

        // Se procesa el listado de la portada
        LoadDiv.refrescaListadoNoPub();
    },

    // -------------------------------------------------------------------------
    showPort: function() {
        var edic = $('#cmb_edic').val();
        var port = $('#cmb_port').val();
        if(edic === '') {
            edic = 'base';
        }
        window.open('/' + Admin.prontus_id + '/site/edic/' + edic + '/port/' + port, port, 'width=1000,height=680');
    },

    // -------------------------------------------------------------------------
    // Hace un ping al servidor para indicar
    pingRecurso: function() {
        var edic = $('#cmb_edic').val();
        var port = $('#cmb_port').val();
        if(edic === '') {
            edic = 'base';
        }
        var nom_recurso =  edic + '-' + port;
        Admin.pingRecurso('port', nom_recurso, Listartic.pingRecurso);
    },

    // -------------------------------------------------------------------------
    firstpag: function(_rec_ini) {
        if(Listartic.cargandoNoPub === false) {
            Listartic.cargandoNoPub = true;
            BuscadorFields._rec_ini = _rec_ini;
            LoadDiv.refrescaListadoNoPub();
        }
    },

    // -------------------------------------------------------------------------
    prevpag: function(_rec_ini) {
        if(Listartic.cargandoNoPub === false) {
            Listartic.cargandoNoPub = true;
            BuscadorFields._rec_ini = _rec_ini;
            LoadDiv.refrescaListadoNoPub();
        }
    },

    // -------------------------------------------------------------------------
    nextpag: function(_rec_ini) {
        if(Listartic.cargandoNoPub === false) {
            Listartic.cargandoNoPub = true;
            BuscadorFields._rec_ini = _rec_ini;
            LoadDiv.refrescaListadoNoPub();
        }
    },

    // -------------------------------------------------------------------------
    ultpag: function(_rec_ini) {
        if(Listartic.cargandoNoPub === false) {
            Listartic.cargandoNoPub = true;
            BuscadorFields._rec_ini = _rec_ini;
            LoadDiv.refrescaListadoNoPub();
        }
    },

    // -------------------------------------------------------------------------
    instalaMouseover: function () {

        $('.col470.aleft').off('hover');
        $('.col470.aleft').find('.contenido .titulo').hover(
            function () { // in
                if (!$(this).hasClass('nohover')) {
                    //~ $(this).find('.status').hide();
                    $(this).find('.autoinc').hide();
                    //~ $(this).find('.vobo').hide();
                    $(this).find('.botones').show();
                    $(this).find('.vobo').attr('style', 'float: right; margin: 2px 0px 0 8px;');
                }
            },
            function () { // out
                if (!$(this).hasClass('nohover')) {
                    //~ $(this).find('.status').show();
                    $(this).find('.autoinc').show();
                    //~ $(this).find('.vobo').show();
                    $(this).find('.botones').hide();
                    $(this).find('.vobo').attr('style', '');
                }
            }
        );

        $('.col470.aright').off('hover');
        $('.col470.aright').find('.contenido .titulo').hover(
            function () { // in
                if (!$(this).hasClass('nohover')) {
                    $(this).find('.status').hide();
                    $(this).find('.autoinc').hide();
                    $(this).find('.vobo').hide();
                    $(this).find('.botones').show();
                }
            },
            function () { // out
                if (!$(this).hasClass('nohover')) {
                    $(this).find('.status').show();
                    $(this).find('.autoinc').show();
                    $(this).find('.vobo').show();
                    $(this).find('.botones').hide();
                }
            }
        );
    },

    deshabilitarVoBo: function (item) {
        $(item).find('.contenido .titulo').off('hover');
        $(item).find('.vobo').removeClass('vobo').addClass('vobo_disabled').hide();
        Listartic.instalaMouseover();
    },

    habilitarVoBo: function (item) {
        $(item).find('.contenido .titulo').off('hover');
        $(item).find('.status').show();
        $(item).find('.vobo_disabled').removeClass('vobo_disabled').addClass('vobo').show();
    },
    
    updateLastMod: function() {
        
        setInterval(function() {
            
            var mod = $('#_localmodtime').val();
            if(mod) {
                var thestring;
                var dmod = new Date(mod*1000);
                mod = dmod.getTime();
                var dnow = new Date();
                var now = dnow.getTime();
                
                if(mod > now) {
                    // La fecha de ahora es mas antigua
                    $('#lastmodPortada').html('');
                    return;
                }
                var diff = now - mod; // En milisegundos
                diff = diff / 1000; // En segundos
                if(diff < 60) {
                    thestring = "Modificada hace unos segundos";
                } else if(diff < 3600) {
                    diff = Math.round(diff/60);
                    if(diff == 1) {
                        thestring = "Modificada hace un minuto";
                    } else {
                        thestring = "Modificada hace "+diff+" minutos";
                    }
                } else {
                    var dnow2 = dnow;
                    dnow2.setTime(dnow2.getTime() - 86400);
                    var fechamod = dmod.getYear()+'-'+dmod.getMonth()+'-'+dmod.getDate();
                    var fechahoy = dnow.getYear()+'-'+dnow.getMonth()+'-'+dnow.getDate();
                    var fechaayer = dnow2.getYear()+'-'+dnow2.getMonth()+'-'+dnow2.getDate();
                    
                    if(fechamod == fechahoy) {
                        var hora = Utiles.getHora(mod, true);
                        thestring = "Modificada hoy a las "+hora+" hrs";
                        
                    } else if(fechamod == fechaayer) {
                        var hora = Utiles.getHora(mod, true);
                        thestring = "Modificada ayer a las "+hora+" hrs";
                    } else {
                        var hora = Utiles.getHora(mod, true);                            
                        var fecha = Utiles.getFecha(mod, true);
                        thestring = "Modificada el "+fecha;
                    }
                }
                $('#lastmodPortada').html(thestring);

            } else {
                //No se pudo leer la fecha de modififcacion
                $('#lastmodPortada').html('');
            }
            
        }, 1000);
    }
}; // fin clase


