
var Tax  = {
    dir_cgi_cpan: "",
    path_conf: "",
    prontus_id: "",
    val_orig: {},

    // -------------------------------------------------------------------------
    init: function(_newitem) {

        Tax.path_conf = Admin.path_conf;
        Tax.prontus_id = Admin.prontus_id;

        /* Inicio drag&drop para lista-seccion */
        $('#lista-seccion').sortable({
                items: "li:not(.ui-state-disabled), ul",
                dropOnEmpty: true,
                handle: '.handler',
                opacity: 0.75,
                update: function (event, ui) {
                    $(ui.item).addClass('moved');
                    var img_src = $(ui.item).find('.fila1 .mover a img').attr('src');
                    $(ui.item).find('.fila1 .mover a img').attr('src', img_src.replace('mover2.png', 'mover2_on.png'));
                    Tax.guardarPos(ui.item, 'seccion');
                }
        });

        // Para el importar y exportar taxonomia
        $('.colorbox').colorbox({
            width: '520',
            height: '400',
            iframe: true,
            overlayClose: false,
            escKey: false,  // Deshabilita el ESC
            onLoad: function() {
                Admin.ocultarBarraColorbox();
            }
        });

        $('#lista-seccion').delegate('.showurls', 'click', function() {
            var rel = $(this).attr('rel');
            if(rel) {
                rel = rel.replace('show', '');
                Tax.showURLs(rel)
            }
            return false;
        });

        $('.mostrar').each(function () {
            if ($(this).attr('alt') == 'btn_ticket_green') {
                $(this).attr('title', 'Click para ocultar en el FID');
            } else {
                $(this).attr('title', 'Click para visibilizar en el FID');
            }
        });

        if (_newitem == 1) {
          Tax.mostrarOculto('nuevo-seccion-0');
        }
    },

    // -------------------------------------------------------------------------
    /* Escapea y ademas despulga. */
    escapeHTML: function(str) {
        return str.replace(/&/g,'&amp;').replace(/>/g,'').replace(/</g,'').replace(/"/g,'').replace(/'/g, '').replace('/\\/', '');
    },

    // -------------------------------------------------------------------------
    guardarPos: function(obj, entidad) {
        var form_data = "";
        var id;
        var pos;

        /* Armar data. */
        $('li[id^="item-'+entidad+'"]').each(function () {
            id = ($(this).attr("id")).replace('item-'+entidad+'-', '');
            if (entidad == 'seccion') {
                pos = $(this).index()+1;
            } else {
                pos = $(this).index();
            }
            form_data += "&_pos"+id+"="+pos;
        });

        form_data = "_entidad="+entidad+form_data+"&_path_conf="+Tax.path_conf;

        var img_obj = $(obj).find('.fila1 .mover a img');
        img_obj.removeClass('handler');
        img_obj.attr('src', (img_obj.attr('src')).replace('boto/mover2_on.png', 'loading_button.gif'));

        $.ajax({
            url:        '/' + Tax.dir_cgi_cpan + '/prontus_tax_guardarpos.cgi',
            type:       'POST',
            dataType:   'json',
            cache:          false,
            data:       form_data,
            success: function(data) {
                if (data.status == '0') {
                    alert(data.msg);
                } else {
                    img_obj.addClass('handler');
                    img_obj.attr('src', (img_obj.attr('src')).replace('loading_button.gif', 'boto/mover2_on.png'));
                }
            },
            error: function() {
                alert('Ocurrio un error, intentelo nuevamente.');
                img_obj.addClass('handler');
                img_obj.attr('src', (img_obj.attr('src')).replace('loading_button.gif', 'boto/mover2_on.png'));
            }
        });

    },

    // -------------------------------------------------------------------------
    editarItem: function(entidad, id) {
        if ($('#mostrar-'+entidad+'-'+id).is(':visible')) {
            $('#mostrar-'+entidad+'-'+id).hide();
            $('#edicion-'+entidad+'-'+id).show();
        }
    },

    // -------------------------------------------------------------------------
    guardarItem: function(obj, entidad, id) {
        /* esconder botones y mostrar cargando. */
        $(obj).parent().find('a').hide();
        $(obj).parent().find('.fila_loading').show();

        /* deshabilitar inputs */
        $('#edicion-'+entidad+'-'+id).find('input[type="text"]').attr('disabled', 'disabled');

        /* armar data */
        var form_data = "_entidad="+entidad+"&_path_conf="+Tax.path_conf;
        /* nombre del item */
        form_data += "&_nom="+Url.encode($('input[name="_nom-'+entidad+'-'+id+'"]').val());
        /* ver si existen vistas. */
        if ($('input[name^="_nom_vista-'+entidad+'-'+id+'-"]').length > 0) {
            $('input[name^="_nom_vista-'+entidad+'-'+id+'-"]').each(function () {
                var reg_exp = new RegExp("_nom_vista-"+entidad+"-(.*?)-","g");
                var nom_vista = ($(this).attr('name')).replace(reg_exp, '');
                form_data += "&_nom-"+nom_vista+"="+Url.encode($(this).val());
            });
        }
        /* portada */

        form_data += "&_port="+Url.encode($('input[name="_port-'+entidad+'-'+id+'"]').val());

        var adicional = "&_id="+id;

        if (entidad == 'tema') {
            adicional += "&_secc_id="+($('#item-'+entidad+'-'+id).parent().attr("id")).replace('lista-temas-', '');
        }

        if (entidad == 'subtema') {
            adicional += "&_tema_id="+($('#item-'+entidad+'-'+id).parent().attr("id")).replace('lista-subtemas-', '');
        }

        form_data = form_data+adicional;

        /* enviar info. */
        $.ajax({
            url:        '/' + Tax.dir_cgi_cpan + '/prontus_tax_guardar.cgi',
            type:       'POST',
            dataType:   'json',
            cache:          false,
            data:       form_data,
            success: function(data) {
                if (data.status == '0') {
                    alert(data.msg);
                    /* esconder cargando y mostrar botones. */
                    $(obj).parent().find('.fila_loading').hide();
                    $(obj).parent().find('a').show();
                    /* habilitar inputs. */
                    $('#edicion-'+entidad+'-'+id).find('input[type="text"]').removeAttr('disabled');

                } else {
                    /* todo ok, actualizar informacion en ram. */
                    /* nombre item */
                    $('#mostrar-'+entidad+'-'+id).find('.txt_nom').html(Tax.escapeHTML($('input[name="_nom-'+entidad+'-'+id+'"]').val()));
                    /* nombre item vistas */
                    if ($('input[name^="_nom_vista-'+entidad+'-'+id+'-"]').length > 0) {
                        $('input[name^="_nom_vista-'+entidad+'-'+id+'-"]').each(function () {
                            var reg_exp = new RegExp("_nom_vista-"+entidad+"-(.*?)-","g");
                            var nom_vista = ($(this).attr('name')).replace(reg_exp, '');
                            if ($(this).val() == '') {
                                $('#mostrar-'+entidad+'-'+id).find('.txt_nom-'+nom_vista).html(Tax.escapeHTML($('input[name="_nom-'+entidad+'-'+id+'"]').val()));
                                $(this).val($('input[name="_nom-'+entidad+'-'+id+'"]').val());
                            } else {
                                $('#mostrar-'+entidad+'-'+id).find('.txt_nom-'+nom_vista).html(Tax.escapeHTML($(this).val()));
                            }
                        });
                    }
                    /* portada */
                    $('#mostrar-'+entidad+'-'+id).find('.txt_port').html(Tax.escapeHTML($('input[name="_port-'+entidad+'-'+id+'"]').val())+'&nbsp;');

                    $('#edicion-'+entidad+'-'+id).hide();
                    $('#mostrar-'+entidad+'-'+id).show();

                    /* esconder cargando y mostrar botones. */
                    $(obj).parent().find('.fila_loading').hide();
                    $(obj).parent().find('a').show();
                    /* habilitar inputs. */
                    $('#edicion-'+entidad+'-'+id).find('input[type="text"]').removeAttr('disabled');

                }
            },
            error: function() {
                alert("Ocurrio un error, intentelo nuevamente.");
                /* esconder cargando y mostrar botones. */
                $(obj).parent().find('.fila_loading').hide();
                $(obj).parent().find('a').show();
                /* habilitar inputs. */
                $('#edicion-'+entidad+'-'+id).find('input[type="text"]').removeAttr('disabled');
            }
        });

    },

    // -------------------------------------------------------------------------
    cancelarEditar: function (obj, entidad, id) {
        if ($('#edicion-'+entidad+'-'+id).is(':visible')) {
            $('#edicion-'+entidad+'-'+id).hide();
            $('#mostrar-'+entidad+'-'+id).show();
        }
    },

    // -------------------------------------------------------------------------
    guardarItemNuevo: function(obj, entidad, identif, newitem) {
        var form_data = '_entidad='+entidad+'&_path_conf='+Tax.path_conf;
        var id_vista;

        /* Mostrar imagen loading y esconder botones. */
        $(obj).parent().find('a').hide();
        $(obj).parent().find('.fila_loading').show();

        /* Obtener y armar data para el .ajax */
        var obj_nom = $('#nuevo-item-'+entidad+'-'+identif).find('.nueva-'+entidad).find('input[name="_nom"]');

        if ($(obj_nom).hasClass('input-sinpulsar') && $(obj_nom).val() == '[nombre]') {
            form_data += '&_nom=';
        } else {
            form_data += '&_nom=' + Url.encode($(obj_nom).val());
        }

        $('#nuevo-item-'+entidad+'-'+identif).find('.nueva-'+entidad+'Vista').each(function () {
            id_vista = ($(this).attr("id")).replace('vista-'+identif+'-', '');
            obj_nom = $(this).find('input[name="_nom-'+id_vista+'"]');
            if ($(obj_nom).hasClass('input-sinpulsar') && $(obj_nom).val() == '[nombre]') {
                form_data += '&_nom-'+id_vista+"=";
            } else {
                form_data += '&_nom-'+id_vista+"=" + Url.encode($(obj_nom).val());
            }
        });

        var obj_url = $('#nuevo-item-'+entidad+'-'+identif).find('.nueva-'+entidad+'Url').find('input[name="_port"]');

        if ($(obj_url).hasClass('input-sinpulsar') && $(obj_url).val() == '[url]') {
            form_data += '&_port=';
        } else {
            form_data += '&_port=' + escape($(obj_url).val());
        }

        var adicional = "";

        var id_adicional;
        if (entidad == 'tema') {
            id_adicional = ($('#nuevo-item-'+entidad+'-'+identif).parent().attr('id')).replace('lista-temas-', '');
            adicional = '&_secc_id='+id_adicional;
        }

        if (entidad == 'subtema') {
            id_adicional = ($('#nuevo-item-'+entidad+'-'+identif).parent().attr('id')).replace('lista-subtemas-', '');
            adicional = '&_tema_id='+id_adicional;
        }

        form_data += adicional;

        $.ajax({
            url:        '/' + Tax.dir_cgi_cpan + '/prontus_tax_guardar.cgi',
            type:       'POST',
            dataType:   'json',
            data:       form_data,
            cache:          false,
            success: function(data) {
               if (data.status == '0')  {
                   alert(data.msg);
                   $(obj).parent().find('.fila_loading').hide();
                   $(obj).parent().find('a').show();
                } else {
                   if (entidad == 'tema') {
                       Tax.mostrarTemas(false, id_adicional, newitem);
                    } else if (entidad == 'subtema') {
                       Tax.mostrarSubtemas(false, id_adicional, newitem);
                    } else if (entidad == 'seccion') {
                        window.location.href = '/' + Tax.dir_cgi_cpan + '/prontus_tax_admin.cgi?_entidad=seccion&_path_conf='+Tax.path_conf+'&_newitem='+newitem;
                    }
                }
                $(obj).parent().find('.fila_loading').hide();
                $(obj).parent().find('a').show();
            },
            error: function() {
                alert("Ocurrio un error, intentelo nuevamente.");
                $(obj).parent().find('.fila_loading').hide();
                $(obj).parent().find('a').show();
            }
        });

    },

    // -------------------------------------------------------------------------
    /* Mostrar temas. */
    mostrarTemas: function(obj, id, newitem) {

        if((typeof newitem === 'undefined')) {
            newitem = 0;
        }

        if (obj !== false) {
            var img_src = $(obj).find('img').attr("src");
            var txt = $(obj).find('img').attr('alt');
        }

        $(obj).parent().find('a').hide();
        $(obj).parent().find('.fila_loading').show();

        /* Para solucionar problema de cache de IE, agregar un parametro X con un valor variable, en este caso
         * el time.
         * */
        var r = new Date().getTime();
        var url = '/' + Tax.dir_cgi_cpan + '/prontus_tax_admin.cgi?_entidad=tema&_path_conf='+Tax.path_conf+"&_secc_id="+id+'&r='+r;

        if ($('#lista-temas-'+id).length === 0 || obj === false) {
             if ($('#lista-temas-'+id).length === 0) {
                  $('#item-seccion-'+id).append('<ul id="lista-temas-'+id+'" class="oculto"></ul>');
             }
             $('#lista-temas-'+id).load(url, function(data) {
                 if (obj !== false) {
                     $('#lista-temas-'+id).slideToggle();
                 }
                 $(obj).parent().find('a').show();
                 $(obj).parent().find('.fila_loading').hide();
                 /* Inicio drag&drop para lista-temas */
                 $('ul[id="lista-temas-'+id+'"]').sortable({
                         items: "li:not(.ui-state-disabled), ul",
                         dropOnEmpty: true,
                         handle: '.mover .handler',
                         opacity: 0.75,
                         update: function (event, ui) {
                             $(ui.item).addClass('moved');
                             var img_src = $(ui.item).find('.fila1 .mover a img').attr('src');
                             $(ui.item).find('.fila1 .mover a img').attr('src', img_src.replace('mover2.png', 'mover2_on.png'));
                             Tax.guardarPos(ui.item, 'tema');
                         }
                 });

                 /* Soluciona problema en explorer al arrastar items anidados. */
                 $('ul[id="lista-temas-'+id+'"]').bind('mousedown', function(e) {
                        e.stopPropagation();
                 });

                 /* Cambia boton */
                 if (obj !== false) {
                      img_src = ($(obj).find('img').attr("src")).replace('mas_of.png', 'men_of.png');
                     txt = txt.replace('Mostrar', 'Ocultar');
                     $(obj).find('img').attr("src", img_src);
                     $(obj).find('img').attr('alt', txt).attr('title', txt);
                 }
                 /* Si es 'guardar nuevo', abre el espacio de los inputs. */
                 if (newitem == 1) {
                     Tax.mostrarOculto('nuevo-tema-'+id)
                 }

                $('#lista-temas-'+id).find('.mostrar').each(function () {
                    if ($(this).attr('alt') == 'btn_ticket_green') {
                        $(this).attr('title', 'Click para ocultar en el FID');
                    } else {
                        $(this).attr('title', 'Click para visibilizar en el FID');
                    };
                });
             });
        } else {
            if ($('#lista-temas-'+id).is(':visible')) {
                $('#lista-temas-'+id).slideToggle('slow', function() {
                     $(this).remove();
                     /* Cambia boton */
                     if (obj !== false) {
                          img_src = ($(obj).find('img').attr("src")).replace('men_of.png', 'mas_of.png');
                         txt = txt.replace('Ocultar', 'Mostrar');
                         $(obj).find('img').attr("src", img_src);
                         $(obj).find('img').attr('alt', txt).attr('title', txt);
                     }
                });
            }

            $(obj).parent().find('a').show();
            $(obj).parent().find('.fila_loading').hide();
        }
    },
    // -------------------------------------------------------------------------
    /* Mostrar subtemas. */
    mostrarSubtemas: function(obj, id, newitem) {

        if((typeof newitem === 'undefined')) {
            newitem = 0;
        }

        if (obj !== false) {
            var img_src = $(obj).find('img').attr("src");
            var txt = $(obj).find('img').attr('alt');
        }

        $(obj).parent().find('a').hide();
        $(obj).parent().find('.fila_loading').show();

        /* Para solucionar problema de cache de IE, agregar un parametro X con un valor variable, en este caso
         * el time al momento de ejecutar la función.
         * */
        var r = new Date().getTime();
        var url = '/' + Tax.dir_cgi_cpan + '/prontus_tax_admin.cgi?_entidad=subtema&_path_conf='+Tax.path_conf+"&_tema_id="+id+'&r='+r;

        /* Para que funcione en explorer: $('#lista-subtemas-'+id).html() == '' */
        if ($('#lista-subtemas-'+id).length === 0 || $('#lista-subtemas-'+id).html() === '' || obj === false) {
             if ($('#lista-subtemas-'+id).length === 0) {
                  $('#item-tema-'+id).append('<ul id="lista-subtemas-'+id+'" class="oculto"></ul>');
             }
            $('#lista-subtemas-'+id).load(url, function(data) {
                if (obj !== false) {
                    $('#lista-subtemas-'+id).slideToggle();
                }
                $(obj).parent().find('a').show();
                $(obj).parent().find('.fila_loading').hide();
                $('ul[id="lista-subtemas-'+id+'"]').sortable({
                        items: "li:not(.ui-state-disabled), ul",
                        dropOnEmpty: true,
                        handle: '.mover .handler',
                        opacity: 0.75,
                        update: function (event, ui) {
                            $(ui.item).addClass('moved');
                            var img_src = $(ui.item).find('.fila1 .mover a img').attr('src');
                            $(ui.item).find('.fila1 .mover a img').attr('src', img_src.replace('mover2.png', 'mover2_on.png'));
                            Tax.guardarPos(ui.item, 'subtema');
                        }
                });
                /* Soluciona problema en explorer al arrastar items anidados. */
                 $('ul[id="lista-subtemas-'+id+'"]').bind('mousedown', function(e) {
                        e.stopPropagation();
                 });

                 $(obj).parent().find('a').show();
                 $(obj).parent().find('.fila_loading').hide();

                 /* Cambia boton */
                 if (obj !== false) {
                      img_src = ($(obj).find('img').attr("src")).replace('mas_of.png', 'men_of.png');
                 txt = txt.replace('Mostrar', 'Ocultar');
                 $(obj).find('img').attr("src", img_src);
                 $(obj).find('img').attr('alt', txt).attr('title', txt);
                 }

                /* si es 'guardar nuevo' mostrar espacio de los inputs. */
                if (newitem == 1) {
                    Tax.mostrarOculto('nuevo-subtema-'+id);
                }

                $('#lista-subtemas-'+id).find('.mostrar').each(function () {
                    if ($(this).attr('alt') == 'btn_ticket_green') {
                        $(this).attr('title', 'Click para ocultar en el FID');
                    } else {
                        $(this).attr('title', 'Click para visibilizar en el FID');
                    };
                });

            });
        } else {
            if (obj !== false) {
                $('#lista-subtemas-'+id).slideToggle('slow', function () {
                     $(this).remove();
                     /* Cambia boton */
                     if (obj !== false) {
                          img_src = ($(obj).find('img').attr("src")).replace('men_of.png', 'mas_of.png');
                         txt = txt.replace('Ocultar', 'Mostrar');
                         $(obj).find('img').attr("src", img_src);
                         $(obj).find('img').attr('alt', txt).attr('title', txt);
                     }
                });
            }
            $(obj).parent().find('a').show();
            $(obj).parent().find('.fila_loading').hide();
        }
    },
    // -------------------------------------------------------------------------
    borrarItem: function(obj, entidad, id) {
        var msg = '¿Estás seguro que quieres borrar est';
        switch (entidad) {
            case 'seccion':
                 msg += 'a sección?';
                 break;
            case 'tema':
                msg += 'e tema?';
                break;
            case 'subtema':
                msg += 'e subtema?';
                break;
        };
        if (confirm(msg)) {
            var form_data = '&_entidad='+entidad+'&_path_conf='+Tax.path_conf+'&_id='+id;

            if (entidad == 'tema') {
                form_data += '&_secc_id='+($('#item-tema-'+id).parent().attr('id')).replace('lista-temas-', '');
            } else if (entidad == 'subtema') {
                form_data += '&_tema_id='+($('#item-subtema-'+id).parent().attr('id')).replace('lista-subtemas-', '');
            }

            $(obj).parent().find('a').hide();
            $(obj).parent().find('.fila_loading').show();
            $.ajax({
                url:        '/' + Tax.dir_cgi_cpan + '/prontus_tax_borrar.cgi',
                type:       'POST',
                dataType:   'json',
                data:       form_data,
                success: function(data) {
                   if (data.status == '0')  {
                       alert(data.msg);
                        $(obj).parent().find('a').show();
                        $(obj).parent().find('.fila_loading').hide();
                    } else {
                        $('#item-'+entidad+'-'+id).fadeOut('slow', function() {
                            $(this).remove();
                        });
                    }
                },
                error: function() {
                    $(obj).parent().find('a').show();
                    $(obj).parent().find('.fila_loading').hide();
                }
            });
        }
    },
    // -------------------------------------------------------------------------
    actualizarMostrar: function(obj, entidad, id) {
        var img_src = $(obj).find('img').attr("src");
        var orig_title = $(obj).find('img').attr("title");

        $(obj).parent().find('a').hide();
        $(obj).parent().find('.fila_loading').show();

        // btn_ticket_red, btn_ticket_green
        var value = 1;
        if ($(obj).find('img').attr("alt") == 'btn_ticket_green') {
            value = 0;
            $(obj).find('img').attr("src", img_src.replace('btn_ticket_green.png', 'btn_ticket_red.png'));
            $(obj).find('img').attr("title", "Click para visibilizar en el FID").attr("alt", "btn_ticket_red");
        } else {
            $(obj).find('img').attr("src", img_src.replace('btn_ticket_red.png', 'btn_ticket_green.png'));
            $(obj).find('img').attr("title", "Click para ocultar en el FID").attr("alt", "btn_ticket_green");
        }

        var form_data = '_id='+id+'&_entidad='+entidad+'&_path_conf='+Tax.path_conf+'&_mostrar='+value;

        if (entidad == 'tema') {
            form_data += '&_secc_id='+($('#item-tema-'+id).parent().attr('id')).replace('lista-temas-', '');
        } else if (entidad == 'subtema') {
            form_data += '&_tema_id='+($('#item-subtema-'+id).parent().attr('id')).replace('lista-subtemas-', '');
        }

        $.ajax({
            url:        '/' + Tax.dir_cgi_cpan + '/prontus_tax_mostrar.cgi',
            type:       'POST',
            dataType:   'json',
            data:       form_data,
            success: function(data) {
               if (data.status == '0')  {
                    alert(data.msg);
                    $(obj).find('img').attr("src", img_src);
                    $(obj).find('img').attr("title", orig_title);
                    $(obj).find('img').attr("alt", orig_title);
                }
                $(obj).parent().find('a').show();
                $(obj).parent().find('.fila_loading').hide();
            },
            error: function() {
                $(obj).find('img').attr("src", img_src);
                $(obj).find('img').attr("title", orig_title);
                $(obj).find('img').attr("alt", orig_title);
                $(obj).parent().find('a').show();
                $(obj).parent().find('.fila_loading').hide();
            }
        });

    },

    // -------------------------------------------------------------------------
    chgImgSrc: function(obj, img) {
        $(obj).attr("src", img);
    },

    // -------------------------------------------------------------------------
    mostrarOculto: function (id) {

         if ($('#'+id).is(':visible')) {
              $('#'+id).slideToggle('slow');
         } else {
             $('#'+id).find('input[name^="_nom"]').val('[nombre]').addClass('input-sinpulsar');
             $('#'+id).find('input[name="_port"]').val('[url]').addClass('input-sinpulsar');
             $('#'+id).slideToggle('slow');
         }

        /* Quitar clase 'input-sinpulsar' a los inputs que se les hace click. */
        $('#'+id).find('input[type="text"]').click(function () {
             if ($(this).hasClass('input-sinpulsar')) {
                  $(this).removeClass('input-sinpulsar');
                 $(this).val('');
             }
        });

    },
    // -------------------------------------------------------------------------
    ocultarTodo: function () {
        $('li .contenido .showtemas').each(function() {
            var imagen = $(this).find('img').attr('src');
            if(imagen.indexOf('men_of.png') > 0) {
                $(this).click();
            }
        });
    },
    // -------------------------------------------------------------------------
    /* Deprecated. */
    expandirTodo: function () {
        $('li .contenido .showtemas').each(function() {
            var imagen = $(this).find('img').attr('src');
            if(imagen.indexOf('mas_of.png') > 0) {
                $(this).click();
            }
        });
    },
    // -------------------------------------------------------------------------
    ocultarDeshabilitadas: function () {
        $('li').each(function () {
            if ($(this).find('.contenido a img').attr('alt') == 'btn_ticket_red') {
                $(this).slideUp('slow');
            }
        });
    },
    // -------------------------------------------------------------------------
    navVista: function(nom_vista, direccion) {
        if (direccion == 'right') {
            if ($('.vista-'+nom_vista).next().hasClass('col-anex')) {
                $('.vista-'+nom_vista).hide();
                $('.vista-'+nom_vista).next().show();

                $('.txt_nom-'+nom_vista).hide();
                $('.txt_nom-'+nom_vista).next().next().show();
            } else {
                $('.vista-'+nom_vista).hide();
                $('[class*="vista-"]:eq(0)').show();

                $('.txt_nom-'+nom_vista).hide();
                var regx = /txt_nom-(.*)/;
                var cls = ($('[class*="txt_nom-"]:eq(0)').attr("class")).match(regx);
                $('[class*="txt_nom-'+cls[1]+'"]').show();
            };
        } else if (direccion == 'left') {
            if ($('.vista-'+nom_vista).prev().hasClass('col-anex')) {
                $('.vista-'+nom_vista).hide();
                $('.vista-'+nom_vista).prev().show();

                $('.txt_nom-'+nom_vista).hide();
                $('.txt_nom-'+nom_vista).prev().prev().show();
            } else {
                $('.vista-'+nom_vista).hide();
                var regx = /vista-(.*)/;
                var cls = ($('[class*="vista-"]:last').attr("class")).match(regx);
                $('[class*="vista-'+cls[1]+'"]').show();

                $('.txt_nom-'+nom_vista).hide();
                $('[class*="txt_nom-'+cls[1]+'"]').show();
            };
        };
    },

    // -------------------------------------------------------------------------
    showURLs: function(entidad) {
        if (! $('#tp_div'+entidad).hasClass('visible'+entidad)) {
            $('#tp_div'+entidad).slideDown();
            $('#tp_div'+entidad).addClass('visible'+entidad);
        } else {
            $('#tp_div'+entidad).slideUp();
            $('#tp_div'+entidad).removeClass('visible'+entidad);
        }
    }



};

