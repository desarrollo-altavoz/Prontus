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
        // ---------------------------------------------------------------
        init: function (prontus_id) {
            self = this;
            self.prontus_id = prontus_id;

            $('#banco-img .fotodrag').draggable({
                helper: "clone",
                containment: "document",
                zIndex: 9999,
                appendTo: "body"
            });

            $('div[id^="body"]').each(function () {
                $(this).find('div[id^="FOTOFIJA_"]:eq(0)').attr("data-ini", "1");
            });

            // Verificar nombres de fotos duplicados.
            var duplicados = '';
            $('[id^="FOTOFIJA_"]').each(function(){
              var id = $('[id="'+this.id+'"]');
              if(id.length>1 && id[0]==this) {
                duplicados += this.id + "\n";
              }
            });

            if (duplicados) {
                alert("Advertencia: los siguientes campos de foto están duplicados y necesitan ser corregidos:\n\n" + duplicados);
            }
        },
        // ---------------------------------------------------------------
        newInstance: function (id, maxW, maxH, imgW, imgH) {
            self.foto.init(id, maxW, maxH, imgW, imgH);
        },
        // ---------------------------------------------------------------
        preview: {
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
            getFotoListHtml: function (id, nombre) {
                var html = '<li><input type="checkbox" name="_asignar_%%id%%" id="_asignar_%%id%%" value="%%id%%"/> <label for="_asignar_%%id%%">%%nombre%%</label></li>';
                html = html.replace(/%%id%%/g, id).replace(/%%nombre%%/g, nombre);

                return html;
            },
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
            getPreview: function (id) {
                var $preview = $('#FOTOFIJA_' + id).parents('.cabecera').find('.preview-fotofija');

                if ($preview.length) {
                    return $preview;
                } else {
                    return false;
                }
            },
            // ---------------------------------------------------------------
            getPreviewParent: function (id) {
                var $previewParent = $('#FOTOFIJA_' + id).parents('.cabecera');
                if ($previewParent.length) {
                    return $previewParent;
                } else {
                    return false;
                }
            },
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
            hide: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                $preview.find('.work-area').removeClass('cropping');
                $preview.find('.work-area').html('');
                $preview.find('.botones .crop-aplicar').hide();
            },
            // ---------------------------------------------------------------
            getCurrent: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var currentId = $preview.attr("data-current");

                return currentId;
            },
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
            showFotoList: function (id) {
                var $preview = self.preview.getPreview(id);
                var html = '';
                if (!$preview) return; // si no exite preview, terminar.

                $preview.parent().find('[id^="FOTOFIJA_"]').each(function () {
                    var idFoto = $(this).attr("id").replace("FOTOFIJA_", "");
                    if (idFoto !== id) {
                        html += self.preview.getFotoListHtml(idFoto, idFoto);
                    }
                });

                $preview.find('.foto-list-container ul').html(html);
                $preview.find('.foto-list-container').fadeIn('fast').find('a').attr("data-idFoto", id);
            }
        },
        // ---------------------------------------------------------------
        crop: {
            containment: [0,0,0,0],
            active: false,
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
            init: function (id) {
                if (!self.crop.hasValidDimensions(id)) {
                    self.crop.disableCrop(id);
                    return;
                }

                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');
                var $img = $workArea.find('.img');
                var $zoom = $workArea.find('.zoom .range');

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
                Fid.submitir('Guardar', '_self');
            },
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
                        self.foto.instances[id].top = ui.position.top;
                        self.foto.instances[id].left = ui.position.left;

                        $img.css({
                            top: ui.position.top,
                            left: ui.position.left
                        });
                    },
                    stop: function (event, ui) {
                        self.crop.containment = self.crop.getContainment(id);
                    }
                });
            },
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
            alignCropImage: function (id) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');
                var $crop = $workArea.find('.crop-box img');
                var $img = $workArea.find('.img img');
                var props = {
                    top: 0.5 * ($workArea.height() - $img.height()),
                    left: 0.5 * ($workArea.width() - $img.width())
                };

                $img.css(props);
                $crop.css(props);
            },
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
            disableCrop: function (id) {
                var msg = "La foto no se puede editar ya que tiene menor o igual tamaño que el área de recorte.";
                self.crop.active = false;
                self.actions.showAlert(id, msg);
            }
        },
        // ---------------------------------------------------------------
        zoom: {
            zoomLimits: {left: 0, top: 0},
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
            sliderCallback: function (id, oldValue, newValue) {
                var $preview = self.preview.getPreview(id);
                if (!$preview) return; // si no exite preview, terminar.
                var $workArea = $preview.find('.work-area');
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
            },
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
        actions: {
            // ---------------------------------------------------------------
            remove: function (id) {
                $('input[name="FOTOFIJA_' + id + '"]').val('');
                $('input[name="_WFOTOFIJA_' + id + '"]').val('');
                $('input[name="_HFOTOFIJA_' + id + '"]').val('');
                $('input[name="_ACTIONSFOTOFIJA_' + id + '"]').val('');
                $("#FOTOFIJA_" + id).html('');

                self.foto.unBindEvents(id);
                self.foto.unset(id);
                self.methods.toggleButtons(id, {lupa:'off',editar:'off',borrar:'off',cuadrar:'off'});
                self.actions.hideAlert(id);

                if (self.preview.getCurrent(id) == id) {
                    self.preview.hide(id);
                }
            },
            // ---------------------------------------------------------------
            edit: function (id) {
                if (self.noCrop === true) return; // crop deshabilitado. (global)

                if (self.preview.getCurrent(id) != id) {
                    self.preview.update(id);
                }

                self.crop.init(id);
            },
            // ---------------------------------------------------------------
            preview: function (id) {
                self.preview.update(id);
            },
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
            center: function (id) {
                self.crop.alignCropImage(id);
            },
            // ---------------------------------------------------------------
            showAlert: function (id, msg) {
                var $preview = self.preview.getPreview(id);
                var $alert = $preview.find('.alert');
                $alert.html('<div>' + msg + '</div>').stop().fadeIn('fast');
                $alert.delay(3500).fadeOut('fast');
            },
            // ---------------------------------------------------------------
            hideAlert: function (id) {
                var $preview = self.preview.getPreview(id);
                var $alert = $preview.find('.alert');
                $alert.stop().hide();
            },
            // ---------------------------------------------------------------
            applyCrop: function (id) {
                self.crop.apply(id);
            },
            // ---------------------------------------------------------------
            assignFoto: function (idFoto) {
                var imgSrc = $('#' + idFoto).attr("src");
                var imgW = $('#' + idFoto).attr("data-w");
                var imgH = $('#' + idFoto).attr("data-h");
                var currBody = '#' + $('#_curr_body').val();

                $(currBody + ' [id^="FOTOFIJA_"]').each(function() {
                    var id = $(this).attr("id").replace("FOTOFIJA_", "");
                    self.foto.set(id, imgSrc, imgW, imgH);

                    if ($(this).parent().hasClass('active')) {
                        self.preview.update(id);
                    }
                });
            },

            showRep: function (id) {
                if (self.crop.active == true) {
                    self.preview.update(id);
                }
                self.preview.showFotoList(id);
            },

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
        methods: {
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
        foto: {
            instances: {},
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

                    $('#FOTOFIJA_' + id).html('<img src="' + currImgSrc + '" />');
                    self.methods.toggleButtons(id, {lupa:'on',editar:editar,borrar:'on', cuadrar:'on'});
                    self.foto.bindEvents(id);
                } else {
                    self.methods.toggleButtons(id, {lupa:'off',editar:'off',borrar:'off',cuadrar:'off'});
                    self.foto.instances[id].src = ''; // fix
                }

                if ($("#FOTOFIJA_" + id).attr("data-ini") == 1) {
                    self.preview.update(id);
                }

                $("#FOTOFIJA_" + id).droppable({
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

                $("#FOTOFIJA_" + id).on('click', function () {
                    self.preview.update(id);
                });

                if (!$preview) {
                    $('[data-id="FOTOFIJA_' + id + '"]').parent().find('.name').hide();
                    $('[data-id="FOTOFIJA_' + id + '"]').parent().find('.size').hide();
                }
            },
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
            bindEvents: function (id) {
                $('[data-id="FOTOFIJA_' + id + '"]').hover(
                    function () {
                        $(this).find('.botones').show();
                    },
                    function () {
                        $(this).find('.botones').hide();
                    }
                );

                $('[data-id="FOTOFIJA_' + id + '"]').find('.botones').hover(
                    function () {
                        $(this).show();
                    }
                );
            },
            // ---------------------------------------------------------------
            unBindEvents: function (id) {
                $('[data-id="FOTOFIJA_' + id + '"]').off('hover');
                $('[data-id="FOTOFIJA_' + id + '"]').find('.botones').off('hover').hide();
            },
            // ---------------------------------------------------------------
            set: function (id, imgSrc, imgW, imgH) {
                var $preview = self.preview.getPreview(id);
                var editar = 'on';

                $('#FOTOFIJA_' + id).html('<img src="' + imgSrc + '" />');
                $('input[name="FOTOFIJA_' + id + '"]').val(imgSrc);
                $('input[name="_WFOTOFIJA_' + id + '"]').val(imgW);
                $('input[name="_HFOTOFIJA_' + id + '"]').val(imgH);

                self.foto.instances[id].src = imgSrc;
                self.foto.instances[id].imgW = parseInt(imgW);
                self.foto.instances[id].imgH = parseInt(imgH);

                if (!$preview) editar = 'off';
                if (self.noCrop === true) editar = 'off';

                self.methods.toggleButtons(id, {lupa:'on',editar:editar,borrar:'on',cuadrar:'on'});
                self.foto.bindEvents(id);
            },
            // ---------------------------------------------------------------
            setSelected: function (id) {
                var $previewParent = self.preview.getPreviewParent(id);
                $previewParent.find('[data-id^="FOTOFIJA_"]').removeClass("active");
                $previewParent.find('[data-id="FOTOFIJA_' + id + '"]').addClass("active");
            },
            // ---------------------------------------------------------------
            setActions: function (id, actions) {
                $('input[name="_ACTIONSFOTOFIJA_' + id + '"]').val(actions);
            }
        },
        // ---------------------------------------------------------------
        helper: {
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
            getHeight: function (newW, imgW, imgH) {
                var proportion = newW / imgW;
                var newH = imgH * proportion;

                return Math.round(newH);
            },
            // ---------------------------------------------------------------
            getCurrentTab: function () {
                return $('#_curr_body').val();
            }
        }
    };

    window.FotoFija = FotoFija;
})(this);
