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

            self.workArea.bindFotoEditor();
            self.workArea.bindZoom();
            // self.actions.bindZoom();
            // self.actions.bindRotate();
            // self.actions.bindReset();
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
            bindZoom: function () {
                $("#editor_zoom_in").click(function (e) {
                    e.preventDefault();

                    if ((self.workArea.fotoOrigW * self.workArea.zoomScale) >= self.workArea.fotoRealW) {
                        return false;
                    } else {
                        self.workArea.zoomScale += 0.1;
                    }

                    self.workArea.fotoW = self.workArea.fotoOrigW * self.workArea.zoomScale;
                    self.workArea.fotoH = self.workArea.fotoOrigH * self.workArea.zoomScale;

                    $("#editor_workarea_foto").width(self.workArea.fotoW);
                    $("#editor_workarea_foto").height(self.workArea.fotoH);

                    var var1 = ($("#editor_workarea").width() - self.workArea.fotoW) / 2;
                    var var2 = ($("#editor_workarea").height() - self.workArea.fotoH) / 2;

                    // if (!self.workArea.dragged) {
                        $("#editor_workarea_foto").css("left", var1);
                        $("#editor_workarea_foto").css("top", var2);
                    // }

                    // $("#editor_workarea_foto").css("transform", "rotate(" + self.workArea.rotation + "deg) scale(" + self.workArea.zoomScale + ")");
                });

                $("#editor_zoom_out").click(function (e) {
                    e.preventDefault();
                    if (self.workArea.zoomScale <= 1) {
                        return false;
                    } else {
                        self.workArea.zoomScale -= 0.1;
                    }

                    self.workArea.fotoW = self.workArea.fotoOrigW * self.workArea.zoomScale;
                    self.workArea.fotoH = self.workArea.fotoOrigH * self.workArea.zoomScale;

                    $("#editor_workarea_foto").width(self.workArea.fotoW);
                    $("#editor_workarea_foto").height(self.workArea.fotoH);

                    var var1 = ($("#editor_workarea").width() - self.workArea.fotoW) / 2;
                    var var2 = ($("#editor_workarea").height() - self.workArea.fotoH) / 2;

                    // if (!self.workArea.dragged) {
                        $("#editor_workarea_foto").css("left", var1);
                        $("#editor_workarea_foto").css("top", var2);
                    // }

                    // $("#editor_workarea_foto").css("transform", "rotate(" + self.workArea.rotation + "deg) scale(" + self.workArea.zoomScale + ")");
                });
            },
            bindRotate: function () {
                $("#editor_rotate_left").click(function (e) {
                    e.preventDefault();
                    self.workArea.rotation -= 90;

                    if (self.workArea.rotation == -360) self.workArea.rotation = 0;

                    $("#editor_workarea_foto").css("transform", "rotate(" + self.workArea.rotation + "deg)");


                });

                $("#editor_rotate_right").click(function (e) {
                    e.preventDefault();
                    self.workArea.rotation += 90;

                    if (self.workArea.rotation == 360) self.workArea.rotation = 0;

                    $("#editor_workarea_foto").css("transform", "rotate(" + self.workArea.rotation + "deg)");

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
        // Manejo del area de trabajo.
        // ---------------------------------------------------------------
        workArea: {
            canvas: {
                editor: null,
                context: null,
                width: false,
                height: false,
                image: {
                    object: null,
                    realWidth: 0,
                    realHeight: 0,
                    scale: 0,
                    relativePath: null,
                },
                lastX: false,
                lastY: false,
            },
            restart: function () {

            },
            bindFotoEditor: function () {
                $('body').find('.openFotoEditor').click(function () {
                    var nomfoto     = $(this).data("nomfoto");
                    var relfoto     = $(this).data("relfoto");
                    var wfoto       = $(this).data("wfoto");
                    var hfoto       = $(this).data("hfoto");

                    // Se guarda el tamaño real de la foto.
                    self.workArea.canvas.image.realWidth = wfoto;
                    self.workArea.canvas.image.realHeight = hfoto;
                    self.workArea.canvas.image.relativePath = relfoto;

                    $.colorbox({
                        inline: true,
                        href:"#editor_container",
                        width: 1030,
                        height: 700,
                        onComplete: function () {
                            self.workArea.canvas.width = $("#editor_workarea_foto").width();
                            self.workArea.canvas.height = $("#editor_workarea_foto").height();

                            self.workArea.cargarFotosSidebar();
                            self.workArea.handleColorBox();
                        },
                        onClosed: function () {
                        }
                    });
                })
            },
            handleColorBox: function () {
                self.workArea.canvas.editor = $("#editor_workarea_foto");
                self.workArea.canvas.context = self.workArea.canvas.editor[0].getContext("2d");
                self.workArea.canvas.image.object = new Image;
                self.workArea.canvas.image.object.onload = function () {
                    // self.workArea.dibujarImagen(true);
                    self.workArea.handleZoom(0);
                    self.workArea.eventsListeners();
                };

                self.workArea.canvas.image.object.src = self.workArea.canvas.image.relativePath;
                self.workArea.handleTransforms(self.workArea.canvas.context);

            },
            eventsListeners: function () {
                self.workArea.canvas.lastX = self.workArea.canvas.width / 2;
                self.workArea.canvas.lastY = self.workArea.canvas.height / 2;
                var dragStart;
                var dragged;

                self.workArea.canvas.editor.on('mousedown', function (evt) {
                    document.body.style.mozUserSelect = document.body.style.webkitUserSelect = document.body.style.userSelect = 'none';
                    self.workArea.canvas.lastX = evt.offsetX || (evt.pageX - self.workArea.canvas.editor.offsetLeft);
                    self.workArea.canvas.lastY = evt.offsetY || (evt.pageY - self.workArea.canvas.editor.offsetTop);
                    dragStart = self.workArea.canvas.context.transformedPoint(self.workArea.canvas.lastX, self.workArea.canvas.lastY);
                    dragged = false;
                });

                self.workArea.canvas.editor.on('mousemove', function (evt) {
                    self.workArea.canvas.lastX = evt.offsetX || (evt.pageX - self.workArea.canvas.editor.offset().left);
                    self.workArea.canvas.lastY = evt.offsetY || (evt.pageY - self.workArea.canvas.editor.offset().top);
                    dragged = true;

                    if (dragStart) {
                        var pt = self.workArea.canvas.context.transformedPoint(self.workArea.canvas.lastX, self.workArea.canvas.lastY);
                        self.workArea.canvas.context.translate(pt.x - dragStart.x, pt.y - dragStart.y);
                        self.workArea.handleZoom(0);

                        var var1 = evt.pageX - evt.offsetX;
                        console.log(evt.pageX, evt.offsetX, var1, self.workArea.canvas.editor.offset().left);
                    }
                });

                self.workArea.canvas.editor.on('mouseup', function (evt) {
                    dragStart = null;
                    if (!dragged) self.workArea.handleZoom(evt.shiftKey ? -1 : 1);
                });

                // Estos no funcionan en esta version de jQuery.
                document.getElementById('editor_workarea_foto').addEventListener('DOMMouseScroll', function(evt) {
                    var delta = evt.wheelDelta ? evt.wheelDelta/40 : evt.detail ? -evt.detail : 0;
                    if (delta) self.workArea.handleZoom(delta);

                    return evt.preventDefault() && false;
                }, false);

                document.getElementById('editor_workarea_foto').addEventListener('mousewheel', function(evt) {
                    var delta = evt.wheelDelta ? evt.wheelDelta/40 : evt.detail ? -evt.detail : 0;
                    if (delta) self.workArea.handleZoom(delta);

                    return evt.preventDefault() && false;
                }, false);

            },
            handleZoom: function (clicks) {
                var scaleFactor = 1.1;
                var pt = self.workArea.canvas.context.transformedPoint(self.workArea.canvas.lastX, self.workArea.canvas.lastY);
                self.workArea.canvas.context.translate(pt.x, pt.y);
                var factor = Math.pow(scaleFactor, clicks);
                self.workArea.canvas.context.scale(factor, factor);
                self.workArea.canvas.context.translate(-pt.x, -pt.y);
                self.workArea.dibujarImagen(true);
            },
            dibujarImagen: function (centrar) {
                var p1 = self.workArea.canvas.context.transformedPoint(0, 0);
                var p2 = self.workArea.canvas.context.transformedPoint(self.workArea.canvas.width, self.workArea.canvas.height);
                self.workArea.canvas.context.clearRect(p1.x, p1.y, (p2.x - p1.x), (p2.y - p1.y));

                self.workArea.canvas.context.save();
                self.workArea.canvas.context.setTransform(1, 0, 0, 1, 0, 0);
                self.workArea.canvas.context.clearRect(0, 0, self.workArea.canvas.width, self.workArea.canvas.height);
                self.workArea.canvas.context.restore();
                // self.workArea.canvas.context.resetTransform();

                if (typeof centrar !== 'undefined' && centrar) {
                    var hRatio = self.workArea.canvas.width / self.workArea.canvas.image.realWidth;
                    var vRatio = self.workArea.canvas.height / self.workArea.canvas.image.realHeight;
                    var ratio = Math.min(hRatio, vRatio);
                    var centerShift_x = (self.workArea.canvas.width - self.workArea.canvas.image.realWidth * ratio) / 2;
                    var centerShift_y = (self.workArea.canvas.height - self.workArea.canvas.image.realHeight * ratio) / 2;

                    self.workArea.canvas.context.drawImage(self.workArea.canvas.image.object, 0, 0, self.workArea.canvas.image.realWidth, self.workArea.canvas.image.realHeight, centerShift_x, centerShift_y, self.workArea.canvas.image.realWidth*ratio, self.workArea.canvas.image.realHeight*ratio);
                } else {
                    self.workArea.canvas.context.drawImage(self.workArea.canvas.image.object, 0, 0);
                }
            },
            handleTransforms: function () {
                var svg = document.createElementNS("http://www.w3.org/2000/svg",'svg');
                var xform = svg.createSVGMatrix();
                var savedTransforms = [];
                var save = self.workArea.canvas.context.save;
                var restore = self.workArea.canvas.context.restore;
                var scale = self.workArea.canvas.context.scale;
                var rotate = self.workArea.canvas.context.rotate;
                var translate = self.workArea.canvas.context.translate;
                var transform = self.workArea.canvas.context.transform;
                var setTransform = self.workArea.canvas.context.setTransform;
                var pt  = svg.createSVGPoint();

                self.workArea.canvas.context.getTransform = function() {
                    return xform;
                };

                self.workArea.canvas.context.save = function() {
                    savedTransforms.push(xform.translate(0, 0));

                    return save.call(self.workArea.canvas.context);
                };

                self.workArea.canvas.context.restore = function() {
                    xform = savedTransforms.pop();

                    return restore.call(self.workArea.canvas.context);
                };

                self.workArea.canvas.context.scale = function(sx, sy){
                    xform = xform.scaleNonUniform(sx, sy);

                    return scale.call(self.workArea.canvas.context, sx, sy);
                };

                self.workArea.canvas.context.rotate = function(radians) {
                    xform = xform.rotate(radians * 180 / Math.PI);

                    return rotate.call(self.workArea.canvas.context, radians);
                };

                self.workArea.canvas.context.translate = function(dx, dy) {
                    xform = xform.translate(dx, dy);

                    return translate.call(self.workArea.canvas.context, dx, dy);
                };

                self.workArea.canvas.context.transform = function(a, b, c, d, e, f) {
                    var m2 = svg.createSVGMatrix();
                    m2.a = a;
                    m2.b = b;
                    m2.c = c;
                    m2.d = d;
                    m2.e = e;
                    m2.f = f;
                    xform = xform.multiply(m2);

                    return transform.call(self.workArea.canvas.context, a, b, c, d, e, f);
                };

                self.workArea.canvas.context.setTransform = function(a, b, c, d, e, f) {
                    xform.a = a;
                    xform.b = b;
                    xform.c = c;
                    xform.d = d;
                    xform.e = e;
                    xform.f = f;

                    return setTransform.call(self.workArea.canvas.context, a, b, c, d, e, f);
                };

                self.workArea.canvas.context.transformedPoint = function(x,y) {
                    pt.x = x;
                    pt.y = y;

                    return pt.matrixTransform(xform.inverse());
                };
            },
            cargarFotosSidebar: function () {
                // Cargar fotos en sidebar.
                $("#editor_fotos").empty();

                $('input[name^="FOTOFIJA_"]').each(function () {
                    $("#editor_fotos").append('<div class="foto"><span>' + $(this).attr("name") + '</span></div>');
                });
            },

            bindZoom: function () {
                $("#editor_zoom_in").click(function (e) {
                    e.preventDefault();

                    self.workArea.context.scale(2, 2);

                });
            }
        },
        // ---------------------------------------------------------------
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
