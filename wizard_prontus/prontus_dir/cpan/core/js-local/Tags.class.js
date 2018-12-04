/*jslint vars: true, undef: true, sloppy: true, maxerr: 50, indent: 4 */
var Tags  = {
    dir_cgi_cpan: "",
    path_conf: "",
    prontus_id: "",
    val_orig: {},
    loading: true,

    cgiMostrar: 'prontus_tags_resumen.cgi',
    cgiEliminar: 'prontus_tags_borrar.cgi',
    cgiGuardar: 'prontus_tags_guardar.cgi',
    cgiCambiaSt: 'prontus_tags_cambia_st.cgi',

    defaultTagText: ProntusLangController.getString('_tags_default_tag_text'),
    idTagInput: '#_tags4fid',

    textoBuscador: ProntusLangController.getString('_tags_search_text'),
    textoBuscadorRapido: ProntusLangController.getString('_tags_quick_search'),
    textoNombreTag: ProntusLangController.getString('_tags_tag_name'),

    // -------------------------------------------------------------------------
    init: function () {
        Tags.loading = false;
        Tags.path_conf = Admin.path_conf;
        Tags.prontus_id = Admin.prontus_id;
        Tags.dir_cgi_cpan = Admin.dir_cgi_cpn;

        /* Quitar clase 'input-sinpulsar' a los inputs que se les hace click. */
        $('#nuevo-tags-0').find('input[type="text"]').focus(function () {
            if ($(this).hasClass('input-sinpulsar')) {
                $(this).removeClass('input-sinpulsar');
                $(this).val('');
            }
        });

        // Para el importar y exportar taxonomia
        $('.colorbox').colorbox({
            width: '520',
            height: '450',
            iframe: true,
            title: '  ',
            overlayClose: false,
            escKey: false,  // Deshabilita el ESC
            onLoad: function () {
                Admin.ocultarBarraColorbox();
            }
        });

        // Para el buscador
        Utiles.instalaHandlerBuscador('#search_texto', Tags.textoBuscador);

    },

    // -------------------------------------------------------------------------
    initFid: function (path_conf) {

        // Para instalar el plugin de tags
        $(Tags.idTagInput).tagsInput({
            'autocomplete_url': './prontus_tags_search.cgi',
            'width': '450px',
            'height': 'inherit',
            'unique': true,
            'defaultText': Tags.defaultTagText,
            'onRemoveTag': function () {
                Tags.marcaAgregados(Tags.getUsedTags(), '#lasttags');
            },
            'autocomplete': {
                width: '400',
                delay: '300',
                mustMatch: true,
                autoFill: false,
                multiple: true,
                multipleSeparator: '|',
                cacheLength: 1,
                minChars: 2,
                highlight: function (texto, query) {
                    if (query === '') {
                        return texto;
                    }
                    if (typeof texto !== 'undefined' && texto !== null && texto !== '') {
                        texto = texto.replace(query, '<span style="color:red; font:menu">' + query + '</span>');
                    }
                    return texto;
                },
                formatItem: function (row, pos, tot, term) {
                    return row[1];
                },
                formatMatch: function (row, pos, tot) {
                    if (row[0] === 0) {
                        return '';
                    }
                    return row[1];
                },
                formatResult: function (row, pos, tot) {
                    if (row[0] === 0) {
                        return '';
                    }
                    return row[1];
                },
                extraParams: {
                    '_path_conf': path_conf,
                    defaultstr: Tags.defaultTagText,
                    existing: function () {
                        return $('#_tags4fid').val();
                    }
                }
            }
        });

        // Para los últimos tags ingresados
        $('#lasttags a').bind('click', function () {
            var lnk = $(this).attr('href');
            if (lnk !== '' && lnk !== null) {
                var strId = lnk.replace('#tag', '');
                var nomtag = $(this).attr('alt');
                Tags.addTagFromLink(strId, nomtag);
                $(this).parent().addClass('unused').addClass('used');
            }
        });

        // Marca los tags que ya están agregados
        var usedtags = Tags.getUsedTags();
        Tags.marcaAgregados(usedtags, '#lasttags');

        // Para ver todos los tags en un colorbox
        $('#linkTags4Fids').colorbox({
            width: '745',
            height: '90%',
            iframe: true,
            onClosed: function() {
                var usedtags = Tags.getUsedTags();
                Tags.marcaAgregados(usedtags, '#lasttags');
            }
        });
    },


    // -------------------------------------------------------------------------
    initQuickSearch: function () {

        if (typeof parent.Tags === 'undefined') {
            alert(ProntusLangController.getString('_tags_no_parent_window'));
            return;
        }
        TagsParent = parent.Tags;

        // Para el buscador rapido
        Utiles.instalaHandlerBuscador('#search_texto', Tags.textoBuscadorRapido);

        // Marca los tags que ya están agregados en el fondo
        var usedtags = TagsParent.getUsedTags();
        Tags.marcaAgregados(usedtags, '#alltags');

        Tags.instalaOcultarUsados();

        Tags.instalaHandlerSearch();

        // Para los últimos tags ingresados
        $('#alltags a').bind('click', function () {
            if ($(this).parent().hasClass('used')) {
                return;
            }
            var lnk = $(this).attr('href');
            if (lnk !== '' && lnk !== null) {
                var strId = lnk.replace('#tag', '');
                var nomtag = $(this).attr('rev');
                TagsParent.addTagFromLink(strId, nomtag);
                $(this).parent().addClass('unused').addClass('used');
            }
        });
    },

    // -------------------------------------------------------------------------
    // Instala el handler de la busqueda rapida
    instalaHandlerSearch: function () {

        $('#search_texto').bind('change', function () {

            var filter = $(this).val(); // get the value of the input, which we filter on
            if (filter === Tags.textoBuscadorRapido) {
                //alert('Ingrese un texto para filtrar los tags');
                return;
            }
            if (filter) {
                $('#alltags').find("a:not(:contains(" + filter + "))").parent().addClass('hideFilter');
                $('#alltags').find("a:contains(" + filter + ")").parent().removeClass('hideFilter');
            } else {
                $('#alltags div').removeClass('hideFilter');
            }

        }).bind('keyup', function () {
            $(this).change();
        });
    },

    // -------------------------------------------------------------------------
    // Instala el handler para ocultar los usados
    instalaOcultarUsados: function () {

        $('#ocultarusados').bind('change', function () {
            if ($(this).is(':checked')) {
                $('#alltags').addClass('hideUsed');
            } else {
                $('#alltags').removeClass('hideUsed');
            }
        });
    },

    // -------------------------------------------------------------------------
    // Marca los que estan siendo usados en el tag principal
    marcaAgregados: function (usedtags, contenedor) {
        if (typeof contenedor === 'undefined') {
            return;
        }
        if (typeof usedtags === 'undefined' || usedtags === null || usedtags.length < 0) {
            return;
        }
        $(contenedor + ' div').removeClass('used').addClass('unused');
        var idtag;
        for (idtag in usedtags) {
            $(contenedor + ' a[rel="item' + idtag + '"]').parent().removeClass('unused').addClass('used');
        }
    },

    // -------------------------------------------------------------------------
    // Obtiene los tags que existen actualmente en el input,
    // en formato arr[id] = name
    getUsedTags: function () {
        var arrTags = [];
        var usedtags = $(Tags.idTagInput).val();
        if (typeof usedtags !== 'undefined' && usedtags !== '' && usedtags !== null) {
            var arr = usedtags.split(',');
            var idtag;
            for (idtag in arr) {
                if (arr[idtag].length > 0) {
                    var arr2 = arr[idtag].split('|');
                    if (arr2.length === 2) {
                        arrTags[arr2[0]] = arr2[1];
                    }
                }
            }
        }
        return arrTags;
    },

    // -------------------------------------------------------------------------
    // Agrega un nuevo tag, pero recibiedo un string en formato: #tag<id>
    // junto con el nombre del tag
    addTagFromLink: function (strId, nomtag) {
        if (strId !== '' && nomtag !== '') {
            var tagid = parseInt(strId, 10);
            if (!isNaN(tagid)) {
                var tagValue = tagid + '|' + nomtag;
                var valueInput = $(Tags.idTagInput).val();
                if (valueInput === '') {
                    $(Tags.idTagInput).addTag(tagValue); /* Cannot find value in array */
                    $(Tags.idTagInput + '_tag').val(Tags.defaultTagText).css('color', '#666666');
	            } else {
	                var taglist = valueInput.split(',');
                    if (jQuery.isArray(taglist) && (jQuery.inArray(tagValue, taglist) == -1)) {
	                    $(Tags.idTagInput).addTag(tagValue); /* Cannot find value in array */
	                    $(Tags.idTagInput + '_tag').val(Tags.defaultTagText).css('color', '#666666');
	                }
	            }
            }
        }
    },

    // -------------------------------------------------------------------------
    // Muestra el resumen de un determinado tag
    resumenItem: function (obj) {

        if (Tags.loading) {
            Tags.handleLoading();
            return;
        }
        var id_tag = Tags.findId(obj);
        var url = '/' + Tags.dir_cgi_cpan + '/' + Tags.cgiMostrar;
        url += '?_path_conf=' + Tags.path_conf;
        url += '&_id=' + id_tag;

        // Para el importar y exportar taxonomia
        $.colorbox({
            open: true,
            href: url,
            width: '720',
            height: '500',
            iframe: true
        });

    },

    // -------------------------------------------------------------------------
    // Guarda un item existente en el listado
    guardarItem: function (obj) {

        if (Tags.loading) {
            Tags.handleLoading();
            return;
        }

        //var id_tag = Tags.findId(obj);
        var theUrl = '/' + Tags.dir_cgi_cpan + '/' + Tags.cgiGuardar;
        var form_data = '_path_conf=' + Tags.path_conf;

        var id_tag = Tags.findId(obj);
        form_data += '&_id=' + id_tag;

        var nom_tag = $('#_nom' + id_tag).val();

        form_data += '&_nom=' + Url.encode(nom_tag);

        /* ver si existen vistas. */
        if ($('input[name^="_nom' + id_tag + '-vista-"]').length > 0) {
            $('input[name^="_nom' + id_tag + '-vista-"]').each(function () {
                var reg_exp = new RegExp("_nom" + id_tag + "-vista-(.*?)", "g");
                var nom_vista = ($(this).attr('name')).replace(reg_exp, '');
                form_data += "&_nom-" + nom_vista + "=" + Url.encode($(this).val());
            });
        }

        /* Mostrar imagen loading y esconder botones. */
        $(obj).parent().find('a').hide();
        $(obj).parent().find('.loading_save').show();

        $.ajax({
            url:        theUrl,
            type:       'POST',
            dataType:   'json',
            data:       form_data,
            cache:      false,
            complete: function () {
                $(obj).parent().find('.loading_save').hide();
                $(obj).parent().find('a').show();
            },
            success: function (data) {
                if (data.status == '0') {
                    if (data.msg) {
                        alert(data.msg);
                    } else {
                        alert(ProntusLangController.getString('_tags_deleting_error'));
                    }
                    return;

                } else {

                    var theId = data.theId;
                    var theName = data.theName;

                    $('#_nom' + theId).val(Tags.unescapeHTML(theName));

                    /* ver si existen vistas. */
                    if ($('input[name^="_nom' + theId + '-vista-"]').length > 0) {
                        var tmp_val;
                        $('input[name^="_nom' + theId + '-vista-"]').each(function () {
                            var reg_exp = new RegExp("_nom" + theId + "-vista-(.*?)", "g");
                            var nom_vista = ($(this).attr('name')).replace(reg_exp, '');
                            // eval("tmp_val=data.theName_" + nom_vista);
                            tmp_val = data["theName_" + nom_vista];
                            $('#_nom' + theId + '-vista-' + nom_vista).val(Tags.unescapeHTML(tmp_val));
                            //$('.txt_nom' + id_tag + '-vista-' + nom_vista).html(tmp_val);
                            $('#divtag' + theId).find('.txt_nom-' + nom_vista).html(tmp_val);
                        });
                    }

                    $('#divtag' + theId).find('.modo-vista').find('.col1-tags:eq(0)').html(theName);
                    $('#divtag' + theId).addClass('newitem');
                    Tags.mostrarEditar(obj);
                }
            },
            error:   function (XMLHttpRequest, textStatus, errorThrown) {
                SubmitForm.handleError(theUrl, XMLHttpRequest, textStatus, errorThrown);
            }
        });
    },

    // -------------------------------------------------------------------------
    // Guarda un nuevo item en el listado
    guardarItemNuevo: function (obj, newitem) {

        if (Tags.loading) {
            Tags.handleLoading();
            return;
        }
        //var id_tag = Tags.findId(obj);
        var theUrl = '/' + Tags.dir_cgi_cpan + '/' + Tags.cgiGuardar;
        var form_data = '_path_conf=' + Tags.path_conf;

        /* Mostrar imagen loading y esconder botones. */
        $(obj).parent().find('a').hide();
        $(obj).parent().find('.loading_save').show();

        /* Obtener y armar data para el .ajax */
        if ($('#field-text').hasClass('input-sinpulsar') && $('#field-text').val() === Tags.textoNombreTag) {
            form_data += '&_nom=';
        } else {
            form_data += '&_nom=' + Url.encode($('#field-text').val());
        }

        /* ver si existen vistas. */
        if ($('input[id^="field-text-vista-"]').length > 0) {
            $('input[id^="field-text-vista-"]').each(function () {
                var nom_vista = $(this).attr('name');
                if ($(this).hasClass('input-sinpulsar') && $(this).val() == Tags.textoNombreTag) {
                    form_data += "&" + nom_vista + "=";
                } else {
                    form_data += "&" + nom_vista + "=" + Url.encode($(this).val());
                }
            });
        }

        $.ajax({
            url:        theUrl,
            type:       'POST',
            dataType:   'json',
            data:       form_data,
            cache:      false,
            complete: function () {
                $(obj).parent().find('.loading_save').hide();
                $(obj).parent().find('a').show();
            },
            success: function (data) {
                if (data.status == '0') {
                    if (data.msg) {
                        alert(data.msg);
                    } else {
                        alert(ProntusLangController.getString('_tags_deleting_error'));
                    }
                    return;

                } else {
                    //var theId = data.theId;
                    //var theName = data.theName;
                    Tags.cloneNewItem(data);
                    $('#field-text').val('');
                    $('input[name^="_nom-"]').val(Tags.textoNombreTag).addClass('input-sinpulsar');
                    if (newitem === 0) {
                        Tags.mostrarNuevo();
                    } else {
                        $('#field-text').focus();
                    }
                }
            },
            error:   function (XMLHttpRequest, textStatus, errorThrown) {
                SubmitForm.handleError(theUrl, XMLHttpRequest, textStatus, errorThrown);
            }
        });

    },

    // -------------------------------------------------------------------------
    // Elimina un tag del listado
    eliminarTags: function (obj) {

        if (Tags.loading) {
            Tags.handleLoading();
            return;
        }
        var id_tag = Tags.findId(obj);
        var msg = ProntusLangController.getString('_tags_delete_confirm');

        if (confirm(msg)) {
            var theUrl = '/' + Tags.dir_cgi_cpan + '/' + Tags.cgiEliminar;
            var form_data = '_id_tag=' + id_tag + '&_path_conf=' + Tags.path_conf;
            $('#divtag' + id_tag + ' .link-borrar').hide();
            $('#divtag' + id_tag + ' .loading-borrar').show();
            $.ajax({
                url:        theUrl,
                type:       'POST',
                dataType:   'json',
                data:       form_data,
                complete: function () {
                    $('#divtag' + id_tag + ' .link-borrar').show();
                    $('#divtag' + id_tag + ' .loading-borrar').hide();
                },
                success: function (data) {
                    if (data.status == '0') {
                        if (data.msg) {
                            alert(data.msg);
                        } else {
                            alert(ProntusLangController.getString('_tags_deleting_error'));
                        }
                        return;
                    }
                    $('#divtag' + id_tag).parent().fadeOut();
                },
                error:   function (XMLHttpRequest, textStatus, errorThrown) {
                    SubmitForm.handleError(theUrl + '?' + form_data, XMLHttpRequest, textStatus, errorThrown);
                }
            });

        }
    },

    // -------------------------------------------------------------------------
    // Cambia el estado de un item en el listado de tags
    cambiaEstado: function (obj) {

        var img_src = $(obj).find('img').attr("src");
        //var orig_title = $(obj).find('img').attr("title");
        var theId = Tags.findId(obj);

        $(obj).parent().find('a').hide();
        $(obj).parent().find('.loading-borrar').show();

        // btn_ticket_red, btn_ticket_green
        var value = 1;
        if ($(obj).find('img').attr("alt") == 'btn_ticket_green') {
            value = 0;
        }

        var form_data = '_id_tag=' + theId + '&_path_conf=' + Tags.path_conf + '&_new_st=' + value;
        var theUrl = '/' + Tags.dir_cgi_cpan + '/' + Tags.cgiCambiaSt;
        $.ajax({
            url:        theUrl,
            type:       'POST',
            dataType:   'json',
            data:       form_data,
            complete: function () {
                $(obj).parent().find('a').show();
                $(obj).parent().find('.loading-borrar').hide();
            },
            success: function (data) {
                if (data.status == '0') {
                    alert(data.msg);
                } else {
                    if ($(obj).find('img').attr("alt") == 'btn_ticket_green') {
                        $(obj).find('img').attr("src", img_src.replace('green.png', 'red.png')).attr("alt", "btn_ticket_red");
                        $(obj).parents('li').removeClass('habilitado1').addClass('habilitado0');
                    } else {
                        $(obj).find('img').attr("src", img_src.replace('red.png', 'green.png')).attr("alt", "btn_ticket_green");
                        $(obj).parents('li').removeClass('habilitado0').addClass('habilitado1');
                    }
                }
            },
            error:   function (XMLHttpRequest, textStatus, errorThrown) {
                SubmitForm.handleError(theUrl + '?' + form_data, XMLHttpRequest, textStatus, errorThrown);
            }
        });
    },

    // -------------------------------------------------------------------------
    // Oculta los items que estan deshabilitados
    ocultarDeshabilitadas: function (obj) {
        if ($(obj).hasClass('link-ocultar')) {
            // Ocultar los deshabilitados
            $(obj).hide().parent().find('.link-mostrar').show();
            $('#lista-tags li.habilitado0').slideToggle('slow');
        } else {
            // Mostrar los deshabilitados
            $(obj).hide().parent().find('.link-ocultar').show();
            $('#lista-tags li.habilitado0').slideToggle('slow');
        }
    },

    // -------------------------------------------------------------------------
    // Muestra la caja de nuevo item del listado
    mostrarNuevo: function () {
        if ($('#nuevo-tags-0').is(':visible')) {
            $('#nuevo-tags-0').slideToggle('slow');
        } else {
            $('#nuevo-tags-0').find('input[name^="_nom"]').val(Tags.textoNombreTag).addClass('input-sinpulsar');
            $('#nuevo-tags-0').slideToggle('slow');
        }
    },

    // -------------------------------------------------------------------------
    // Muestra la caja de edicion de un item del listado
    mostrarEditar: function (obj) {
        var fila1 = $(obj).parents('.fila1');
        if ($(fila1).find('div:first').is(':visible')) {
            $(fila1).find('.modo-vista').hide();
            $(fila1).find('.modo-edicion').show();
            $(fila1).addClass('editing');
        } else {
            $(fila1).find('.modo-edicion').hide();
            $(fila1).find('.modo-vista').show();
            $(fila1).removeClass('editing');
        }
    },

    // -------------------------------------------------------------------------
    // Clona una fila para poder crear un nuevo item del listado
    cloneNewItem: function (data) {
        var theId = data.theId;
        var theName = data.theName;

        var newLi = $('#lista-tags li:last').clone();
        $(newLi).find('div:first').attr('id', 'divtag' + theId).addClass('newitem');
        $(newLi).find('.col0').html(theId);
        $(newLi).find('.col1-tags:first').html(theName);
        $(newLi).find('.col1-tags input:first').attr('id', '_nom' + theId).attr('name', '_nom' + theId).val(Tags.unescapeHTML(theName));

        /* Hay vistas? */
        if ($(newLi).find('input[name^="nom-new-item-vista-"]').length > 0) {
            var tmp_value;
            $(newLi).find('input[name^="nom-new-item-vista-"]').each(function () {
                var vista = ($(this).attr("name")).replace('nom-new-item-vista-', '');
                // eval("tmp_value = data.theName_" + vista);
                tmp_value = data["theName_" + vista];
                $(newLi).find('.txt_nom-' + vista).html(tmp_value);
                $(this).val(Tags.unescapeHTML(tmp_value));
                /* Cambiar nombre del input. */
                $(this).attr("name", "_nom" + theId + "-vista-" + vista);
            });
        }

        $(newLi).prependTo('#lista-tags').fadeIn();
    },

    // -------------------------------------------------------------------------
    // Encuentra el ID de la fila actual en el listado de tags
    findId: function (obj) {
        var theId = $(obj).parents('.fila1').attr('id');
        if (theId !== '') {
            theId = theId.replace('divtag', '');
        }
        return theId;
    },

    // -------------------------------------------------------------------------
    // ?????
    handleLoading: function () {
        // TODO Colocar un loading y ocultarlo en este punto
        alert(ProntusLangController.getString('_tags_wait_before_delete'));
    },

    // -------------------------------------------------------------------------
    abrirAdminTags: function() {
        var msg = ProntusLangController.getString('_tags_open_admin_tags_confirm');
        if(confirm(msg)) {
            return true;
        } else {
            return false;
        }
    },

    // -------------------------------------------------------------------------
    // Gatilla la busqueda de tags en el listado de tags
    realizarBusqueda: function () {
        var theUrl =  '/' + Tags.dir_cgi_cpan + '/prontus_tags_admin.cgi';
        $('#frmBuscadorTags').attr("action", theUrl);
        if ($('#search_texto').val() === '' || $('#search_texto').val() == Tags.textoBuscador) {
            alert(ProntusLangController.getString('_tags_keyword_required'));
        } else {
            $('#frmBuscadorTags').submit();
        }
    },

    // -------------------------------------------------------------------------
    // Gatilla el filtrado (en realidad no deberia usarse nunca)
    realizarBusquedaRapida: function () {
        var filter = $('#search_texto').val();
        if (filter === '' || filter === Tags.textoBuscadorRapido) {
            alert(ProntusLangController.getString('_tags_filter_required'));
            return;
        }
        $('#search_texto').change();
    },

    // -------------------------------------------------------------------------
    // Limpia los filtros de busqueda en el listado de tags
    limpiaFiltros: function () {
        var theUrl = '/' + Tags.dir_cgi_cpan + '/prontus_tags_admin.cgi?_path_conf=' + Tags.path_conf;
        window.location.href = theUrl;
    },

    // -------------------------------------------------------------------------
    // Sirve para cambiar de vista en el listado de tags
    navVista: function (nom_vista, direccion) {
        var regx, cls;
        if (direccion == 'right') {
            if ($('.vista-' + nom_vista).next().hasClass('col-anex')) {
                $('.vista-' + nom_vista).hide();
                $('.vista-' + nom_vista).next().show();

                $('.txt_nom-' + nom_vista).hide();
                $('.txt_nom-' + nom_vista).next().show();
            } else {

                $('.vista-' + nom_vista).hide();
                regx = /vista-(\w+)/;
                cls = ($('[class*="vista-"]:first').attr("class")).match(regx);
                $('[class*="vista-' + cls[1] + '"]').show();

                $('.txt_nom-' + nom_vista).hide();
                $('[class*="txt_nom-' + cls[1] + '"]').show();

            }
        } else if (direccion == 'left') {
            if ($('.vista-' + nom_vista).prev().hasClass('col-anex')) {
                $('.vista-' + nom_vista).hide();
                $('.vista-' + nom_vista).prev().show();

                $('.txt_nom-' + nom_vista).hide();
                $('.txt_nom-' + nom_vista).prev().show();
            } else {
                $('.vista-' + nom_vista).hide();
                regx = /vista-(\w+)/;
                cls = ($('[class*="vista-"]:last').attr("class")).match(regx);
                $('[class*="vista-' + cls[1] + '"]').show();

                $('.txt_nom-' + nom_vista).hide();
                $('[class*="txt_nom-' + cls[1] + '"]').show();
            }
        }
    },

    // -------------------------------------------------------------------------
    // Escapea y ademas despulga un string
    unescapeHTML: function (str) {
        if (typeof str !== 'undefined' && str !== null && str !== '') {
            return str.replace(/&amp;/g, '&').replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
        }
        return '';
    }

};

var TagsParent;


// Ejemplo de como hacer un :Contains que haga busqueda Case-insentivie
//jQuery.expr[':'].Contains = function (a,i,m) {
//    return (a.textContent || a.innerText || "").toUpperCase().indexOf(m[3].toUpperCase())>=0;
//};
