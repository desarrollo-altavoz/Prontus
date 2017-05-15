// ---------------------------------------------------------------
// SCRIPT
// ---------------------------------------------------------------
// FotoFija.class.js
//
// ---------------------------------------------------------------
// PROPOSITO
// ---------------------------------------------------------------
//
// ---------------------------------------------------------------
// HISTORIAL DE VERSIONES
// ---------------------------------------------------------------
// 1.0.0 - 04/11/2015 - JOR - Primera versión.
// ---------------------------------------------------------------

(function (window) {
    var self = null;
    var FotoFija = {
        prontus_id: '',
        draggableBanco: false,
        workArea: {
            realW: false,
            realH: false,
            areaW: false,
            areaH: false,
            areaFotoW: false,
            areaFotoH: false,
            zoomScale: 1.0,
            rotation: 0,
            x: 0,
            y: 0,
            dx: 0,
            dy: 0
        },
        // ---------------------------------------------------------------
        init: function (prontus_id) {
            self = this;
            self.prontus_id = prontus_id;

            self.initDraggableBanco();

            // Verificar nombres de fotos duplicados.
            var duplicados = '';
            $('div[id^="recuadro_FOTOFIJA_"]').each(function(){
              var id = $('div[id="'+this.id+'"]');
              if(id.length>1 && id[0]==this) {
                duplicados += this.id + "\n";
              }
            });

            if (duplicados) {
                alert("Advertencia: los siguientes campos de foto están duplicados y necesitan ser corregidos:\n\n" + duplicados);
            }

            // Al guardar verificar que todas las fotos fijas esten correctas.
            // Pueden existir iframes antiguos.
            $('#_mainFidForm').submit(function() {
                $('iframe[id^="FOTOFIJA_"]').each(function () {
                    var id = $(this).attr("id").replace("FOTOFIJA_", "");
                    var $foto = $(this).contents().find('body').find('img');

                    if ($foto.length) {
                        if (typeof self.foto.instances[id] == 'object' && self.foto.instances[id].src == '') {
                            self.foto.set(id, $foto.attr('src'), $foto.attr("data-w"), $foto.attr("data-h"));
                        }
                    }
                });
            });

            self.actions.bindOpenColorBox();
            self.actions.bindZoom();
            self.actions.bindRotate();
            self.actions.bindReset();
        },
        // ---------------------------------------------------------------
        // Inicia drag & drop desde banco de imagenes.
        // ---------------------------------------------------------------
        initDraggableBanco: function () {
            $('#banco-img .foto-icon').draggable({
                helper: "clone",
                containment: "document",
                zIndex: 9999,
                appendTo: "body"
            });
            self.draggableBanco = true;
        },
        // ---------------------------------------------------------------
        // Destruye drag & drop del banco de imagenes.
        // ---------------------------------------------------------------
        destroyDraggableBanco: function () {
            if (self.draggableBanco === true) {
                $('#banco-img .foto-icon').draggable("destroy");
                self.draggableBanco = false;
            }
        },
        // ---------------------------------------------------------------
        // Inicia drag & drop para VTXT
        // ---------------------------------------------------------------
        initDroppableVTXT: function (thediv) {
            $(thediv).find('iframe[id^="VTXT_"]').each(function () {
                var iframe = $(this);
                var id = iframe.attr('id').replace('_ifr', '');
                iframe.droppable({
                    drop: function (e, ui) {
                        // Sobrepasa los limites.
                        if (ui.helper.position().top < (iframe.position().top)) {
                            return false;
                        }
                        tinyMCE.getInstanceById(id).execCommand('mceInsertContent', false, $(ui.helper).html());
                    }
                });
            });
        },
        // ---------------------------------------------------------------
        // Destruye drag & drop para VTXT
        // ---------------------------------------------------------------
        destroyDroppableVTXT: function () {
            $('iframe[id^="VTXT_"].ui-droppable').droppable("destroy");
        },
        // ---------------------------------------------------------------
        // Crea una nueva instancia de un campo de foto.
        // ---------------------------------------------------------------
        newInstance: function (id, maxW, maxH, imgW, imgH) {
            self.foto.init(id, maxW, maxH, imgW, imgH);
        },
        // ---------------------------------------------------------------
        // Acciones
        // ---------------------------------------------------------------
        actions: {
            // ---------------------------------------------------------------
            // Eliminar/quitar una foto de un campo.
            // ---------------------------------------------------------------
            remove: function (id) {
                $('input[name="FOTOFIJA_' + id + '"]').val('');
                $('input[name="_WFOTOFIJA_' + id + '"]').val('');
                $('input[name="_HFOTOFIJA_' + id + '"]').val('');
                $('input[name="_ACTIONSFOTOFIJA_' + id + '"]').val('');
                $("div#recuadro_FOTOFIJA_" + id).html('');
                $('iframe[id="FOTOFIJA_' + id + '"]').contents().find('body').html('&nbsp;');


                self.foto.unBindEvents(id);
                self.foto.unset(id);
                self.methods.toggleButtons(id, {lupa:'off',editar:'off',borrar:'off',cuadrar:'off'});
                // self.actions.hideAlert(id);

                if (self.preview.getCurrent(id) == id) {
                    self.preview.hide(id);
                }
            },
            // ---------------------------------------------------------------
            // Ver una foto en su tamaño real en un colorbox.
            // ---------------------------------------------------------------
            show: function (id) {
                var imgSrc = $('input[name="FOTOFIJA_' + id + '"]').val();

                if (imgSrc) {
                    // self.actions.hideAlert(id);

                    $.fn.colorbox({
                            transition: 'elastic',
                            scrolling: true,
                            open: true,
                            href: imgSrc,
                            maxWidth: '90%',
                            maxHeight: '90%',
                            scalePhotos: false,
                            opacity: 0.8
                            // iframe: true,
                    });
                }
            },
            // ---------------------------------------------------------------
            // Asignar una foto del banco de imagenes a todos los campos de foto
            // Llamada desde Fid.class.js
            // ---------------------------------------------------------------
            assignFoto: function (idFoto) {
                var imgSrc = $('#' + idFoto).attr("src");
                var imgW = $('#' + idFoto).attr("data-w");
                var imgH = $('#' + idFoto).attr("data-h");
                var currBody = '#' + $('#_curr_body').val();

                $(currBody + ' div[id^="recuadro_FOTOFIJA_"]').each(function() {
                    var id = $(this).attr("id").replace("recuadro_FOTOFIJA_", "");
                    self.foto.set(id, imgSrc, imgW, imgH);

                    // if ($(this).parent().hasClass('active')) {
                    //     self.preview.update(id);
                    // }
                });
            },
            bindOpenColorBox: function () {
                $('body').find('.openFotoEditor').click(function () {
                    var nomfoto = $(this).data("nomfoto");
                    var relfoto = $(this).data("relfoto");
                    var wfoto = $(this).data("wfoto");
                    var hfoto = $(this).data("hfoto");

                    self.workArea.realW = wfoto;
                    self.workArea.realH = hfoto;

                    $.colorbox({
                        inline: true,
                        href:"#editor_container",
                        width: 1040,
                        height: 580,
                        onComplete: function () {
                            $("#editor_workarea_foto").css("background-image", "url(" + relfoto + ")");

                            // Cargar fotos en sidebar.
                            $("#editor_fotos").empty();

                            $('input[name^="FOTOFIJA_"]').each(function () {
                                console.log($(this).attr("value").indexOf('/'));
                                if ($(this).attr("value") && $(this).attr("value").indexOf('/') == 0) {
                                    var active = '';
                                    if ($(this).attr("value") == relfoto) active = 'active';

                                    console.log($(this).attr("name"), nomfoto);



                                    $("#editor_fotos").append('<div class="foto ' + active + '" data-fotofijaname="' + $(this).attr("name") + '"><a href="#"><img src="' +  $(this).attr("value") + '"></a></div>');
                                }
                            });


                            $('#editor_workarea_foto').draggable({
                                // containment: "parent", // Contaiment no funciona con propiedad css "transform scale". Se debe hacer a mano.
                                start: function (event, ui) {
                                },
                                drag: function (event, ui) {
                                    var workAreaOffset = $("#editor_workarea").offset();

                                    // console.log(ui.offset.left, workAreaOffset.left, ui.position);

                                    if (ui.offset.left >= workAreaOffset.left) {
                                        ui.position.left = 0;
                                    }


                                    if (ui.offset.left <= workAreaOffset.left) {
                                        // ui.position.left = 0;
                                    }

                                    var var1 = $("#editor_workarea").width() + workAreaOffset.left;
                                    var var2 = $('#editor_workarea_foto').width() + ui.offset.left;
                                    var var3 = ($('#editor_workarea_foto').width() - $("#editor_workarea").width()) / 2;

                                    if (var2 <= var1) {
                                        // console.log("el otro lado", ui.position, ui.offset);
                                        // ui.position.left = 
                                        // console.log(var3);
                                    }

                                    if (ui.offset.top >= workAreaOffset.top) {
                                        ui.position.top = 0
                                    }

                                    console.log(ui.offset, workAreaOffset);


                                }
                            });

                        },
                        onClosed: function () {
                            $('#editor_workarea_crop').resizable("destroy");
                            $('#editor_workarea_crop').draggable("destroy");
                        }
                    });
                })
            },
            bindZoom: function () {
                $("#editor_zoom_in").click(function (e) {
                    e.preventDefault();

                    if ((self.workArea.areaW * self.workArea.zoomScale) >= self.workArea.realW) {
                        return false;
                    } else {
                        self.workArea.zoomScale += 0.1;
                    }

                    $("#editor_workarea_foto").css("transform", "rotate(" + self.workArea.rotation + "deg) scale(" + self.workArea.zoomScale + ")");
                });

                $("#editor_zoom_out").click(function (e) {
                    e.preventDefault();
                    if (self.workArea.zoomScale <= 1) {
                        return false;
                    } else {
                        self.workArea.zoomScale -= 0.1;
                    }

                    $("#editor_workarea_foto").css("transform", "rotate(" + self.workArea.rotation + "deg) scale(" + self.workArea.zoomScale + ")");
                });
            },
            bindRotate: function () {
                $("#editor_rotate_left").click(function (e) {
                    e.preventDefault();
                    self.workArea.rotation -= 90;

                    if (self.workArea.rotation == -360) self.workArea.rotation = 0;

                    $("#editor_workarea_foto").css("transform", "rotate(" + self.workArea.rotation + "deg) scale(" + self.workArea.zoomScale + ")");


                });

                $("#editor_rotate_right").click(function (e) {
                    e.preventDefault();
                    self.workArea.rotation += 90;

                    if (self.workArea.rotation == 360) self.workArea.rotation = 0;

                    $("#editor_workarea_foto").css("transform", "rotate(" + self.workArea.rotation + "deg) scale(" + self.workArea.zoomScale + ")");

                });
            },
            bindReset: function () {
                $("#editor_reset").click(function (e) {
                    e.preventDefault();
                    $("#editor_workarea_foto").css("left", 0);
                    $("#editor_workarea_foto").css("top", 0);

                    self.workArea.rotation = 0;
                    self.workArea.zoomScale = 1;

                    $("#editor_workarea_fotoimg").css("transform", "scale(1) rotate(0deg)");
                });
            },
            apply: function () {

            }
        },
        // ---------------------------------------------------------------
        // Métodos varios.
        // ---------------------------------------------------------------
        methods: {
            // ---------------------------------------------------------------
            // Cambiar el estado de los botones.
            // ---------------------------------------------------------------
            toggleButtons: function (id, states) {
                $.each(states, function (i, v) {
                    if (i == 'cuadrar') {
                        if (v == "on") {
                            $('input[name="CHK_cuadrar_FOTOFIJA_' + id + '"]').parent().show();
                        } else {
                            $('input[name="CHK_cuadrar_FOTOFIJA_' + id + '"]').parent().hide();
                        }
                    } else {
                        if (v == "on") {
                            $('img[name="' + i + 'FOTOFIJA_' + id + '"]').parent().show();
                        } else {
                            $('img[name="' + i + 'FOTOFIJA_' + id + '"]').parent().hide();
                        }
                    }
                });
            }
        },
        // ---------------------------------------------------------------
        // Manejo de fotos.
        // ---------------------------------------------------------------
        foto: {
            // ---------------------------------------------------------------
            // Lista de instancias de fotos.
            // ---------------------------------------------------------------
            instances: {},
            // ---------------------------------------------------------------
            // Inicializa un campo de foto.
            // ---------------------------------------------------------------
            init: function (id, maxW, maxH, imgW, imgH) {
                var currImgSrc = $('input[name="FOTOFIJA_' + id + '"]').val();
                // var $preview = self.preview.getPreview(id);
                // var editar = 'on';

                self.foto.instances[id] = {
                    id: id,
                    maxW: parseInt(maxW),
                    maxH: parseInt(maxH),
                    imgW: parseInt(imgW),
                    imgH: parseInt(imgH),
                    src: currImgSrc,
                    left: 0,
                    top: 0,
                    preW: false,
                    preH: false
                };

                if (currImgSrc && currImgSrc != 'javascript:void(0)') {

                    $('div#recuadro_FOTOFIJA_' + id).html('<img src="' + currImgSrc + '" />');
                    self.methods.toggleButtons(id, {lupa:'on',borrar:'on', cuadrar:'on'});
                    self.foto.bindEvents(id);
                    // Para compatibilidad, se agrega al iframe.
                    $('iframe[id="FOTOFIJA_' + id + '"]').contents().find('body').html('<img src="' + currImgSrc + '" />');

                } else {
                    self.methods.toggleButtons(id, {lupa:'off',editar:'off',borrar:'off',cuadrar:'off'});
                    self.foto.instances[id].src = ''; // fix
                }

                // if ($("div#recuadro_FOTOFIJA_" + id).attr("data-ini") == 1) {
                    // self.preview.update(id);
                // }

                $("div#recuadro_FOTOFIJA_" + id).droppable({
                    accept: '.foto-icon',
                    hoverClass: 'ui-state-active',
                    drop: function (event, ui) {
                        var $item   = ui.helper.find('.fotodrag');
                        var imgSrc  = $item.attr('src');
                        var imgW    = $item.attr("data-w");
                        var imgH    = $item.attr("data-h");

                        self.foto.set(id, imgSrc, imgW, imgH);
                        // self.preview.update(id);
                        //self.preview.showFotoList(id);
                        // self.actions.cancelRep(id);
                    }
                });

                // $("div#recuadro_FOTOFIJA_" + id).on('click', function () {
                    // self.preview.update(id);
                // });

                // if (!$preview) {
                //     $('div[data-id="FOTOFIJA_' + id + '"]').parent().find('.name').hide();
                //     $('div[data-id="FOTOFIJA_' + id + '"]').parent().find('.size').hide();
                // }
            },
            // ---------------------------------------------------------------
            // Vacia una instancia de un campo de foto.
            // ---------------------------------------------------------------
            unset: function (id) {
                self.foto.instances[id] = {
                    id: id,
                    maxW: '',
                    maxH: '',
                    imgW: '',
                    imgH: '',
                    src: '',
                    left: 0,
                    top: 0,
                    preW: false,
                    preH: false
                };
            },
            // ---------------------------------------------------------------
            // Inicia los eventos asociados a una foto.
            // ---------------------------------------------------------------
            bindEvents: function (id) {
                $('div[data-id="FOTOFIJA_' + id + '"]').hover(
                    function () {
                        $(this).find('.botones').show();
                    },
                    function () {
                        $(this).find('.botones').hide();
                    }
                );

                $('div[data-id="FOTOFIJA_' + id + '"]').find('.botones').hover(
                    function () {
                        $(this).show();
                    }
                );
            },
            // ---------------------------------------------------------------
            // Detiene los eventos asociados a una foto.
            // ---------------------------------------------------------------
            unBindEvents: function (id) {
                $('div[data-id="FOTOFIJA_' + id + '"]').off('hover');
                $('div[data-id="FOTOFIJA_' + id + '"]').find('.botones').off('hover').hide();
            },
            // ---------------------------------------------------------------
            // Setea una foto (fuente y tamaño) a una instancia.
            // ---------------------------------------------------------------
            set: function (id, imgSrc, imgW, imgH) {
                // var $preview = self.preview.getPreview(id);
                // var editar = 'on';

                $('div#recuadro_FOTOFIJA_' + id).html('<img src="' + imgSrc + '" />');
                $('input[name="FOTOFIJA_' + id + '"]').val(imgSrc);
                $('input[name="_WFOTOFIJA_' + id + '"]').val(imgW);
                $('input[name="_HFOTOFIJA_' + id + '"]').val(imgH);

                self.foto.instances[id].src = imgSrc;
                self.foto.instances[id].imgW = parseInt(imgW);
                self.foto.instances[id].imgH = parseInt(imgH);

                // if (!$preview) editar = 'off';
                // if (self.noCrop === true) editar = 'off';

                // Para compatibilidad, se agrega al iframe.
                $('iframe[id="FOTOFIJA_' + id + '"]').contents().find('body').html('<img src="' + imgSrc + '" />');

                self.methods.toggleButtons(id, {lupa:'on',borrar:'on',cuadrar:'on'});
                self.foto.bindEvents(id);
            },
            // ---------------------------------------------------------------
            // Setea las acciones a realizar en una foto.
            // ---------------------------------------------------------------
            setActions: function (id, actions) {
                $('input[name="_ACTIONSFOTOFIJA_' + id + '"]').val(actions);
            }
        },
        // ---------------------------------------------------------------
        // Helpers.
        // ---------------------------------------------------------------
        helper: {
            // ---------------------------------------------------------------
            // Obtener nuevo ancho y alto para los tamaños dados.
            // ---------------------------------------------------------------
            resize: function(w, h, maxw, maxh) {
                var ratio = maxh/maxw;

                if (h/w > ratio){
                    if (h > maxh){
                        w = Math.round(w*(maxh/h));
                        h = maxh;
                    }
                } else {
                    if (w > maxh){
                        h = Math.round(h*(maxw/w));
                        w = maxw;
                    }
                }

                return [parseInt(w), parseInt(h)];
            },
            // ---------------------------------------------------------------
            // Obtener algo nuevo alto proporcional.
            // ---------------------------------------------------------------
            getHeight: function (newW, imgW, imgH) {
                var proportion = newW / imgW;
                var newH = imgH * proportion;

                return Math.round(newH);
            },
            // ---------------------------------------------------------------
            // Obtiene el tab actual.
            // ---------------------------------------------------------------
            getCurrentTab: function () {
                return $('#_curr_body').val();
            }
        }
    };

    window.FotoFija = FotoFija;
})(this);
