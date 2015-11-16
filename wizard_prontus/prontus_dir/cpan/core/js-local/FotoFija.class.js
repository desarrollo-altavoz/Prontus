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

            $('div[id^="body"]').each(function () {
                $(this).find('div[id^="recuadro_FOTOFIJA_"]:eq(0)').attr("data-ini", "1");
            });

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
        },
        // ---------------------------------------------------------------
        // Inicia drag & drop desde banco de imagenes.
        // ---------------------------------------------------------------
        initDraggableBanco: function () {
            $('#banco-img .fotodrag').draggable({
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
                $('#banco-img .fotodrag').draggable("destroy");
                self.draggableBanco = false;
            }
        },
        // ---------------------------------------------------------------
        // Crea una nueva instancia de un campo de foto.
        // ---------------------------------------------------------------
        newInstance: function (id, maxW, maxH, imgW, imgH) {
            self.foto.init(id, maxW, maxH, imgW, imgH);
        },
        // ---------------------------------------------------------------
        // Preview de fotos
        // ---------------------------------------------------------------
        preview: {
            // ---------------------------------------------------------------
            // Plantilla del area de trabajo del preview.
            // ---------------------------------------------------------------
            getWorkAreaHtml: function() {
                var html = [
                '<div class="img"></div>',
                '<div class="zoom">',
                '<div class="plus">+</div>',
                '<div class="range"><div class="ui-slider-handle"></div></div>',
                '<div class="minus">-</div>',
                '</div>'].join('').replace(/%%_prontus_id%%/g, self.prontus_id);

                return html;
            },
            // ---------------------------------------------------------------
            // Plantilla de listado de fotos (replica)
            // ---------------------------------------------------------------
            getFotoListHtml: function (id, nombre) {
                var html = '<li><input type="checkbox" name="_asignar_%%id%%" id="_asignar_%%id%%" value="%%id%%"/> <label for="_asignar_%%id%%">%%nombre%%</label></li>';
                html = html.replace(/%%id%%/g, id).replace(/%%nombre%%/g, nombre);

                return html;
            },
            // ---------------------------------------------------------------
            // Plantilla de botones
            // ---------------------------------------------------------------
            getButtonsHtml: function (id) {
                var html = [
                    '<div class="boton-gris3 aleft crop-aplicar">',
                    '<a class="button" href="#" onclick="FotoFija.actions.applyCrop(\'%%id%%\'); return false;" title="Aplicar recorte de foto">',
                    '<span>Aplicar recorte</span>',
                    '</a></div>',
                    '<div class="boton-gris3 aleft crop-aplicar">',
                    '<a class="button" href="#" onclick="FotoFija.actions.preview(\'%%id%%\'); return false;" title="Cancelar recorte de foto">',
                    '<span>Cancelar</span>',
                    '</a></div>',
                    '<a href="#" onclick="FotoFija.actions.center(\'%%id%%\'); return false;" class="crop-aplicar">',
                    '<img src="/%%_prontus_id%%/cpan/core/imag/edi/cen_of.png" class="cambia-boton" alt="Centrar foto en área de recorte" title="Centrar foto en área de recorte" width="18" height="17">',
                    '</a>',
                    '<a href="#" onclick="FotoFija.actions.showRep(\'%%id%%\'); return false;" class="">',
                    '<img src="/%%_prontus_id%%/cpan/core/imag/edi/rep_of.png" class="cambia-boton" alt="Replicar foto" title="Replicar foto" width="18" height="17">',
                    '</a>'
                ].join('').replace(/%%_prontus_id%%/g, self.prontus_id).replace(/%%id%%/g, id);

                return html;
            },
            // ---------------------------------------------------------------
            // Obtiene el DOM del preview de la foto dada.
            // ---------------------------------------------------------------
            getPreview: function (id) {
                var $preview = $('div#recuadro_FOTOFIJA_' + id).parents('.cabecera').find('.preview-fotofija');

                if ($preview.length) {
                    return $preview;
                } else {
                    return false;
                }
            },
            // ---------------------------------------------------------------
            // Obtiene el DOM del padre del preview de la foto dada.
            // ---------------------------------------------------------------
            getPreviewParent: function (id) {
                var $previewParent = $('div#recuadro_FOTOFIJA_' + id).parents('.cabecera');
                if ($previewParent.length) {
                    return $previewParent;
                } else {
                    return false;
                }
            },
            // ---------------------------------------------------------------
            // Actualiza el preview con una nueva foto.
            // ---------------------------------------------------------------
            update: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');

                $preview.disableSelection();
                self.actions.hideAlert(id);

                $preview.find('.barra h3').text(id + ' - ' + self.foto.instances[id].maxW + 'x' + self.foto.instances[id].maxH + ' px');
                $preview.attr("data-current", id);
                $workArea.removeClass('cropping');
                $workArea.html(self.preview.getWorkAreaHtml());

                var imgSrc = self.foto.instances[id].src;

                if (imgSrc) {
                    $workArea.find('.img').html('<img src="' + imgSrc + '"/>');
                    $preview.find('.botones').html($('.botones_' + id).html() + self.preview.getButtonsHtml(id));
                    $preview.find('.botones').find('.cuadrar').remove();
                    $preview.find('.botones').show().find('a').css('opacity', 1);

                    self.foto.instances[id].preW = $workArea.find('.img img').width();
                    self.foto.instances[id].preH = $workArea.find('.img img').height();
                    self.foto.instances[id].top = 0.5 * ($workArea.height() - self.foto.instances[id].preH);
                    self.foto.instances[id].left = 0.5 * ($workArea.width() - self.foto.instances[id].preW);

                    $workArea.find('.img img').css({
                        top: self.foto.instances[id].top,
                        left: self.foto.instances[id].left
                    });

                } else {
                    $workArea.find('.img').html('');
                    $preview.find('.botones').hide();
                }

                self.preview.initDroppable(id);
                self.foto.setSelected(id);
                self.crop.active = false;
            },
            // ---------------------------------------------------------------
            // Esconde el preview
            // ---------------------------------------------------------------
            hide: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                $preview.find('.work-area').removeClass('cropping');
                $preview.find('.work-area').html('');
                $preview.find('.botones .crop-aplicar').hide();
            },
            // ---------------------------------------------------------------
            // Obtiene el id de la foto que se está visualizando en el preview.
            // ---------------------------------------------------------------
            getCurrent: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var currentId = $preview.attr("data-current");

                return currentId;
            },
            // ---------------------------------------------------------------
            // Inicializa el droppable.
            // ---------------------------------------------------------------
            initDroppable: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.

                $preview.droppable({
                    accept: '.fotodrag',
                    drop: function (event, ui) {
                        var imgSrc  = ui.helper.attr('src');
                        var imgW    = ui.helper.attr("data-w");
                        var imgH    = ui.helper.attr("data-h");

                        self.foto.set(id, imgSrc, imgW, imgH);
                        self.preview.update(id);
                        //self.preview.showFotoList(id);
                        self.actions.cancelRep(id);
                    }
                });
            },
            // ---------------------------------------------------------------
            // Mostrar el listado de campos de foto para replicación.
            // ---------------------------------------------------------------
            showFotoList: function (id) {
                var $preview = self.preview.getPreview(id);
                var html = '';
                if (!$preview) return; // si no exite preview, terminar.

                $preview.parent().find('div[id^="recuadro_FOTOFIJA_"]').each(function () {
                    var idFoto = $(this).attr("id").replace("recuadro_FOTOFIJA_", "");
                    if (idFoto !== id) {
                        html += self.preview.getFotoListHtml(idFoto, idFoto);
                    }
                });

                $preview.find('.foto-list-container ul').html(html);
                $preview.find('.foto-list-container').fadeIn('fast').find('a').attr("data-idFoto", id);
            }
        },
        // ---------------------------------------------------------------
        // Manejo de crop de fotos.
        // ---------------------------------------------------------------
        crop: {
            containment: [0,0,0,0],
            active: false,
            drag: false,
            // ---------------------------------------------------------------
            // Plantilla para crop.
            // ---------------------------------------------------------------
            getCropHtml: function (img) {
                var html = [
                '<img class="img-drag" src="%%img%%" />',
                '<div class="crop-box">',
                '<div class="crop-sizer"><img class="img-drag" src="%%img%%" /></div>',
                '</div>',
                ''
                ].join('').replace(/%%_prontus_id%%/g, self.prontus_id).replace(/%%img%%/g, img);

                return html;
            },
            // ---------------------------------------------------------------
            // Inicializa el crop para una foto.
            // ---------------------------------------------------------------
            init: function (id) {
                if (!self.crop.hasValidDimensions(id)) {
                    self.crop.disableCrop(id);
                    return;
                }

                self.crop.drag = false;

                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');
                var $img = $workArea.find('.img');

                $preview.find('.botones .crop-aplicar').show();
                $preview.find('.botones .crop-editar').hide();
                $workArea.addClass('cropping');

                var newSize = self.helper.resize(self.foto.instances[id].maxW, self.foto.instances[id].maxH, $workArea.width()-5, $workArea.height()-5);

                $img.html(self.crop.getCropHtml(self.foto.instances[id].src));

                var $crop = $img.find('.crop-box');
                var $sizer = $crop.find('.crop-sizer');
                var areaLeft = (($workArea.width() / 2) - (newSize[0] / 2));
                var areaTop = (($workArea.height() / 2) - (newSize[1] / 2));

                // Ajusta posicion del crop area, para centrarlo.
                $crop.css('left', Math.round(areaLeft));
                $crop.css('top', Math.round(areaTop));

                $crop.attr("title", "Tamaño: " + self.foto.instances[id].maxW + "x" + self.foto.instances[id].maxH + "px");
                $crop.width(newSize[0]);
                $crop.height(newSize[1]);
                $crop.show();

                // Doble click sobre el area de recorte, aplica los cambios.
                $crop.dblclick(function () {
                    if (confirm("Se recortará la foto. ¿Estás seguro?")) {
                        self.crop.apply(id);
                    }
                });

                // Alinea crop-sizer.
                $sizer.css("top", $crop.position().top * -1);
                $sizer.css("left", $crop.position().left * -1);

                self.zoom.setZoomLimits(id);
                self.crop.alignCropImage(id);
                self.crop.initDraggable(id);
                self.zoom.init(id);
                self.crop.active = true;
            },
            // ---------------------------------------------------------------
            // Aplica el crop de la foto.
            // ---------------------------------------------------------------
            apply: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');
                var $img = $workArea.find('.img img');
                var $cropbox = $workArea.find('.crop-box');
                var $crop = $cropbox.find('img');
                var $zoom = $workArea.find('.zoom .range');

                if ($img.width() < $cropbox.width() || $img.height() < $cropbox.height()) {
                    alert("La foto no se ajusta al área de recorte.");
                    return;
                }

                var x = $cropbox.offset().left - $crop.offset().left;
                var y = $cropbox.offset().top - $crop.offset().top;
                var w = self.foto.instances[id].imgW;
                var h = self.foto.instances[id].imgH
                var resize;
                var zoomValue = $zoom.slider("value") - 100;

                if (zoomValue > 0) {
                    w = Math.round(self.foto.instances[id].imgW + self.foto.instances[id].imgW * (zoomValue/100));
                    h = Math.round(self.foto.instances[id].imgH + self.foto.instances[id].imgH * (zoomValue/100));
                    resize = 'resize[' + w + 'x' + h + '],';
                }

                //Extrapolar.
                var exLeft = Math.round((w * x) / $crop.width());
                var exTop = Math.round((h * y) / $crop.height());
                var exMaxW = Math.round((w * $cropbox.width()) / $crop.width());
                var exMaxH = Math.round((h * $cropbox.height()) / $crop.height());

                var action = [
                    'crop[', exMaxW, 'x', exMaxH,
                    '+', exLeft, '+', exTop,
                    '!', self.foto.instances[id].maxW, 'x', self.foto.instances[id].maxH,
                    ']'
                ].join('');

                self.foto.setActions(id, resize + action); // primero debe ir el resize.
                Fid.submitir('Guardar', '_self'); // Se guarda el artículo.
            },
            // ---------------------------------------------------------------
            // Inicializa el drag de la foto que se está editando.
            // ---------------------------------------------------------------
            initDraggable: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');
                var $crop = $workArea.find('.crop-box');
                var $img = $workArea.find('.img img');

                self.crop.containment = self.crop.getContainment(id);


                $workArea.find('img.img-drag').draggable({
                    scroll: false,
                    containment: self.crop.containment,
                    drag: function (event, ui) {
                        var props = self.crop.getAlignProps(id);

                        if ($crop.width() > $img.width()) {
                            ui.position.left = props.left;
                        }

                        if ($crop.height() > $img.height()) {
                            ui.position.top = props.top;
                        }

                        self.foto.instances[id].top = ui.position.top;
                        self.foto.instances[id].left = ui.position.left;

                        $img.css({
                            top: ui.position.top,
                            left: ui.position.left
                        });
                    },
                    stop: function (event, ui) {
                        self.crop.containment = self.crop.getContainment(id);
                    },
                    start: function (event, ui) {
                        self.crop.drag = true; // para saber la primera vez que empezo el drag.
                    }
                });
            },
            // ---------------------------------------------------------------
            // Obtiene las cordenadas de contención para el área de crop.
            // ---------------------------------------------------------------
            getContainment: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');
                var $crop = $workArea.find('.img .crop-box');
                var $img = $crop.find('.crop-sizer img');

                var right = $crop.offset().left;
                var bottom = $crop.offset().top;
                var left = ($img.outerWidth() > $crop.outerWidth()) ? ($crop.outerWidth() + $crop.offset().left) - $img.outerWidth() : 0;
                var top = ($img.outerHeight() > $crop.outerHeight()) ? ($crop.outerHeight() + $crop.offset().top) - $img.outerHeight() : 0;

                return [left, top, right, bottom];
            },
            // ---------------------------------------------------------------
            // Centrar la foto en el área de crop.
            // ---------------------------------------------------------------
            alignCropImage: function (id) {
                var props = self.crop.getAlignProps(id);
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');
                var $crop = $workArea.find('.crop-box img');
                var $img = $workArea.find('.img img');

                $img.css(props);
                $crop.css(props);
            },
            getAlignProps: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');
                var $crop = $workArea.find('.crop-box img');
                var $img = $workArea.find('.img img');
                var props = {
                    top: 0.5 * ($workArea.height() - $img.height()),
                    left: 0.5 * ($workArea.width() - $img.width())
                };

                return props;
            },
            // ---------------------------------------------------------------
            // Validar si la foto tiene dimensiones válidas.
            // ---------------------------------------------------------------
            hasValidDimensions: function (id) {
                //console.log(self.foto.instances[id]);
                //hidde-crop
                if (self.foto.instances[id].imgW <= self.foto.instances[id].maxW || self.foto.instances[id].imgH <= self.foto.instances[id].maxH) {
                    return false;
                }

                return true;
            },
            // ---------------------------------------------------------------
            // Deshabilita el crop.
            // ---------------------------------------------------------------
            disableCrop: function (id) {
                var msg = "La foto no se puede editar ya que tiene menor o igual tamaño que el área de recorte.";
                self.crop.active = false;
                self.actions.showAlert(id, msg);
            }
        },
        // ---------------------------------------------------------------
        // Manejo del zoom de una imagen.
        // ---------------------------------------------------------------
        zoom: {
            zoomLimits: {left: 0, top: 0},
            // ---------------------------------------------------------------
            // Inicializa el zoom.
            // ---------------------------------------------------------------
            init: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');

                $workArea.find('.zoom .range').slider({
                    min: 100,
                    max: 200,
                    step: 1,
                    value: 100,
                    orientation: "vertical",
                    animate: "fast",
                    slide: function (e, ui) {
                        var oldValue = $(this).slider("value");
                        self.zoom.sliderCallback(id, oldValue, ui.value);
                    },
                    stop: function (e, ui) {
                        // Volver a iniciar el drag, el containment cambia con los nuevos tamaños.
                        self.crop.initDraggable(id);
                    }
                });

                $workArea.find('.zoom .minus').click(function () {
                    var val = $workArea.find('.zoom .range').slider("option", "value");
                    var newVal = val - 1;
                    $workArea.find('.zoom .range').slider("value", newVal);
                    self.zoom.sliderCallback(id, val, newVal);
                });

                $workArea.find('.zoom .plus').click(function () {
                    var val = $workArea.find('.zoom .range').slider("option", "value");
                    var newVal = val + 1;
                    $workArea.find('.zoom .range').slider("value", newVal);
                    self.zoom.sliderCallback(id, val, newVal);
                });

                $workArea.find('.zoom').show();
            },
            // ---------------------------------------------------------------
            // Callback para el slider del zoom.
            // ---------------------------------------------------------------
            sliderCallback: function (id, oldValue, newValue) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');
                var $cropbox = $workArea.find('.img .crop-box');
                var $crop = $workArea.find('.img .crop-box img');
                var $img = $workArea.find('.img img');

                var properties = {
                    "max-width": newValue + "%",
                    "max-height": newValue + "%",
                    "width": Math.round(self.foto.instances[id].preW * (newValue/100)),
                    "height": Math.round(self.foto.instances[id].preH * (newValue/100))
                };

                var antesW = $crop.outerWidth();
                var antesH = $crop.outerHeight();

                // Cambio de tamaño de las fotos.
                $crop.css(properties);
                $img.css(properties);

                var despuesW = $crop.outerWidth();
                var despuesH = $crop.outerHeight();
                var difW, difH;

                if (oldValue > newValue) {
                    // disminuye.
                    difW = antesW - despuesW;
                    difH = antesH - despuesH;
                } else {
                    // aumenta.
                    difW = despuesW - antesW;
                    difH = despuesH - antesH;
                }

                properties = {};
                var varH = $crop.outerHeight() + $crop.offset().top;
                var varW = $crop.outerWidth() + $crop.offset().left;

                if (varW <= self.zoom.zoomLimits.left) {
                    properties["left"] = $crop.position().left+difW;
                }

                if (varH <= self.zoom.zoomLimits.top) {
                    properties["top"] = $crop.position().top+difH;
                }

                // Se aplican las modificaciones a la posicion de las imagenes luego de la redimensión.
                $crop.css(properties);
                $img.css(properties);

                if (self.crop.drag === false) self.crop.alignCropImage(id);

                if ($cropbox.width() > despuesW) {
                    self.crop.alignCropImage(id);
                }

                if ($cropbox.height() > despuesH) {
                    self.crop.alignCropImage(id);
                }
            },
            // ---------------------------------------------------------------
            // Setea los limites de contención para el zoom.
            // ---------------------------------------------------------------
            setZoomLimits: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');
                var limitTop = $workArea.find('.crop-box').offset().top +  $workArea.find('.crop-box').outerHeight();
                var limitLeft = $workArea.find('.crop-box').offset().left +  $workArea.find('.crop-box').outerWidth();

                self.zoom.zoomLimits = {left: limitLeft, top: limitTop};
            }
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
                self.actions.hideAlert(id);

                if (self.preview.getCurrent(id) == id) {
                    self.preview.hide(id);
                }
            },
            // ---------------------------------------------------------------
            // Editar una foto. Inicia el crop.
            // ---------------------------------------------------------------
            edit: function (id) {
                if (self.noCrop === true) return; // crop deshabilitado. (global)

                if (self.preview.getCurrent(id) != id) {
                    self.preview.update(id);
                }

                self.crop.init(id);
            },
            // ---------------------------------------------------------------
            // Carga el preview de la foto.
            // ---------------------------------------------------------------
            preview: function (id) {
                self.preview.update(id);
            },
            // ---------------------------------------------------------------
            // Ver una foto en su tamaño real en un colorbox.
            // ---------------------------------------------------------------
            show: function (id) {
                var imgSrc = $('input[name="FOTOFIJA_' + id + '"]').val();

                if (imgSrc) {
                    self.actions.hideAlert(id);

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
            // Centrar una foto.
            // ---------------------------------------------------------------
            center: function (id) {
                self.crop.alignCropImage(id);
            },
            // ---------------------------------------------------------------
            // Mostrar una alerta.
            // ---------------------------------------------------------------
            showAlert: function (id, msg) {
                var $preview = self.preview.getPreview(id);
                var $alert = $preview.find('.alert');
                $alert.html('<div>' + msg + '</div>').stop().fadeIn('fast');
                $alert.delay(3500).fadeOut('fast');
            },
            // ---------------------------------------------------------------
            // Ocultar una alerta
            // ---------------------------------------------------------------
            hideAlert: function (id) {
                var $preview = self.preview.getPreview(id);
                var $alert = $preview.find('.alert');
                $alert.stop().hide();
            },
            // ---------------------------------------------------------------
            // Aplicar los cambios hechos a una foto cropeada.
            // ---------------------------------------------------------------
            applyCrop: function (id) {
                self.crop.apply(id);
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

                    if ($(this).parent().hasClass('active')) {
                        self.preview.update(id);
                    }
                });
            },
            // ---------------------------------------------------------------
            // Mostrar las opciones de replicación de la foto.
            // ---------------------------------------------------------------
            showRep: function (id) {
                if (self.crop.active == true) {
                    self.preview.update(id);
                }
                self.preview.showFotoList(id);
            },
            // ---------------------------------------------------------------
            // Cerrar las opciones de replicación.
            // ---------------------------------------------------------------
            cancelRep: function (obj) {
                var id;

                if (typeof obj === "object") {
                    id = $(obj).attr("data-idFoto");
                } else {
                    id = obj;
                }

                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.

                $preview.find('.foto-list-container').hide();
                $preview.find('.foto-list-container ul').html('');
            },
            // ---------------------------------------------------------------
            // Replicar una foto en los campos seleccionados.
            // ---------------------------------------------------------------
            doRep: function (obj) {
                var id = $(obj).attr("data-idFoto");
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.

                var fotoList = $preview.find('.foto-list-container .foto-list ul li input:checked');

                if (fotoList.length > 0) {
                    $.each(fotoList, function (i, v) {
                        self.foto.set(v.value, self.foto.instances[id].src, self.foto.instances[id].imgW, self.foto.instances[id].imgH);
                    });
                }

                $preview.find('.foto-list-container').hide();
                $preview.find('.foto-list-container ul').html('');
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
                var $preview = self.preview.getPreview(id);
                var editar = 'on';

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
                    if (!$preview) editar = 'off';
                    if (self.noCrop === true) editar = 'off';

                    $('div#recuadro_FOTOFIJA_' + id).html('<img src="' + currImgSrc + '" />');
                    self.methods.toggleButtons(id, {lupa:'on',editar:editar,borrar:'on', cuadrar:'on'});
                    self.foto.bindEvents(id);
                    // Para compatibilidad, se agrega al iframe.
                    $('iframe[id="FOTOFIJA_' + id + '"]').contents().find('body').html('<img src="' + currImgSrc + '" />');

                } else {
                    self.methods.toggleButtons(id, {lupa:'off',editar:'off',borrar:'off',cuadrar:'off'});
                    self.foto.instances[id].src = ''; // fix
                }

                if ($("div#recuadro_FOTOFIJA_" + id).attr("data-ini") == 1) {
                    self.preview.update(id);
                }

                $("div#recuadro_FOTOFIJA_" + id).droppable({
                    accept: '.fotodrag',
                    drop: function (event, ui) {
                        var imgSrc = ui.helper.attr('src');
                        var imgW = ui.helper.attr('data-w');
                        var imgH = ui.helper.attr('data-h');

                        self.foto.set(id, imgSrc, imgW, imgH);
                        self.preview.update(id);
                        //self.preview.showFotoList(id);
                        self.actions.cancelRep(id);
                    }
                });

                $("div#recuadro_FOTOFIJA_" + id).on('click', function () {
                    self.preview.update(id);
                });

                if (!$preview) {
                    $('div[data-id="FOTOFIJA_' + id + '"]').parent().find('.name').hide();
                    $('div[data-id="FOTOFIJA_' + id + '"]').parent().find('.size').hide();
                }
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
                var $preview = self.preview.getPreview(id);
                var editar = 'on';

                $('div#recuadro_FOTOFIJA_' + id).html('<img src="' + imgSrc + '" />');
                $('input[name="FOTOFIJA_' + id + '"]').val(imgSrc);
                $('input[name="_WFOTOFIJA_' + id + '"]').val(imgW);
                $('input[name="_HFOTOFIJA_' + id + '"]').val(imgH);

                self.foto.instances[id].src = imgSrc;
                self.foto.instances[id].imgW = parseInt(imgW);
                self.foto.instances[id].imgH = parseInt(imgH);

                if (!$preview) editar = 'off';
                if (self.noCrop === true) editar = 'off';

                // Para compatibilidad, se agrega al iframe.
                $('iframe[id="FOTOFIJA_' + id + '"]').contents().find('body').html('<img src="' + imgSrc + '" />');

                self.methods.toggleButtons(id, {lupa:'on',editar:editar,borrar:'on',cuadrar:'on'});
                self.foto.bindEvents(id);
            },
            // ---------------------------------------------------------------
            // Marca como activa la foto dada.
            // ---------------------------------------------------------------
            setSelected: function (id) {
                var $previewParent = self.preview.getPreviewParent(id);
                $previewParent.find('div[data-id^="FOTOFIJA_"]').removeClass("active");
                $previewParent.find('div[data-id="FOTOFIJA_' + id + '"]').addClass("active");
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
