// ---------------------------------------------------------------
// SCRIPT
// ---------------------------------------------------------------
// EditorImag.class.js
//
// ---------------------------------------------------------------
// PROPOSITO
// ---------------------------------------------------------------
// Manejo de eventos y funciones del editor de imagenes.
// ---------------------------------------------------------------
// HISTORIAL DE VERSIONES
// ---------------------------------------------------------------
// 1.0.0 - 24/05/2017 - JOR - Primera versión.
// 1.1.0 - 01/08/2017 - JOR - Se agrega soporte para resize de imagenes.
// 1.1.1 - 11/08/2017 - JOR - Se solucionan problemas con resize de imagenes.
// 2.0.0 - 07/09/2017 - JOR - Se cambia la gráfica y aplican mejoras y bugfixes.
// 2.0.1 - 11/09/2017 - JOR - Se soluciona problema con cálculo de ciertos tamaños de fotos.
// ---------------------------------------------------------------

(function (window) {
    var self = null;
    var EditorImag = {
        foto: null,
        path_conf: null,
        zoomRatio: 1,
        tsArtic: null,
        imgElementId: "#image",
        msgBoxId: "#msg-box",
        activeFotoFija: false,
        fotoFijaW: null,
        fotoFijaH: null,
        free: false,
        hasChanges: false,
        resizing: false,
        resizeWidth: null,
        resizeHeight: null,
        resizeOrigWidth: null,
        resizeOrigHeight: null,
        resizeChain: true,
        zooming: 0,
        fotoFijaClicked: 0,
        imgData: {},
        init: function (path_foto, path_conf, active, ts) {
            self = this;
            self.foto = path_foto;
            self.path_conf = path_conf;
            self.tsArtic = ts;

            self.methods.initCropper({}, function () {
                var cropData = $(self.imgElementId).cropper('getData', true);
                self.imgData = $(self.imgElementId).cropper('getImageData');

                if (!active) {
                    self.free = 1;
                    $('.fotos-fijas .box').eq(0).addClass('active');
                } else {
                    $("#" + active).trigger("click", true);
                    $('.fotos-fijas').animate({scrollTop: $("#" + active).offset().top}, 500);
                    self.activeFotoFija = active;
                }

                $('#freesize_width').val(cropData.width);
                $('#freesize_height').val(cropData.height);
            });

            self.methods.initActions();
            self.methods.initFotosFijas();
        },
        actions: {
            apply: function (e) {
                e.preventDefault();

                if (!self.hasChanges) {
                    if (confirm("No hay cambios que aplicar. ¿Desea continuar editando la imagen?")) {
                        return false;
                    } else {
                        parent.$.colorbox.close();
                        return false;
                    }
                }

                if (!confirm("¿Está seguro de aplicar sus cambios?")) {
                    return false;
                }

                var cropData = $(self.imgElementId).cropper('getData', true);
                var imageData = $(self.imgElementId).cropper('getImageData');
                var data = {
                    srcX: cropData.x,
                    srcY: cropData.y,
                    width: cropData.width,
                    height: cropData.height,
                    aspectRatio:imageData.aspectRatio,
                    rotate: cropData.rotate,
                    foto: self.foto,
                    zoomRatio: self.zoomRatio,
                    _path_conf: self.path_conf,
                    ts: self.tsArtic,
                    fotow: self.fotoFijaW,
                    fotoh: self.fotoFijaH
                };

                $('.tools-container .tools').hide();
                $('.tools-container .size-adj').hide();
                $('.tools-container .loading').show();
                $('.image-container').css('opacity', 0.5);
                $(self.imgElementId).cropper('disable');

                self.methods.offFotosFijas();

                $.ajax({
                    url: "/" + DIR_CGI_CPAN + "/prontus_editor_imag_guardar.cgi",
                    type: "POST",
                    dataType: "json",
                    data: data,
                    success: function(data) {
                        if (data.status === 0) {
                            alert(data.msg);

                            // Si la cgi arroja error, se habilita todo de nuevo para recibir un nuevo intento.
                            $('.tools-container .tools').show();
                            $('.tools-container .size-adj').show();
                            $('.tools-container .loading').hide();
                            $('.image-container').css('opacity', 1);
                            $(self.imgElementId).cropper('enable');
                            self.actions.onFotosfijas();

                        } else {
                            self.actions.imagGuardarCallback(data);
                        }
                    },
                    error: function() {
                        alert('Ocurrió un error al procesar la imagen, inténtelo nuevamente.');
                        $('.tools-container .tools').show();
                        $('.tools-container .size-adj').show();
                        $('.tools-container .loading').hide();
                        $('.image-container').css('opacity', 1);
                        $(self.imgElementId).cropper('enable');
                        self.methods.onFotosfijas();
                    }
                });
            },
            applyResize: function (e) {
                e.preventDefault();

                if (!self.resizing) {
                    if (confirm("No hay cambios que aplicar. ¿Desea continuar editando la imagen?")) {
                        return false;
                    } else {
                        parent.$.colorbox.close();
                        return false;
                    }
                }

                if (!confirm("¿Está seguro de aplicar sus cambios?")) {
                    return false;
                }

                $('.tools-container .freesize').hide();
                $('.tools-container .tools').hide();
                $('.tools-container .size-adj').hide();
                $('.tools-container .loading').show();
                $('.image-container').css("opacity", 0.5);
                $('.image-container img').css("margin", "auto");

                $(self.imgElementId).resizable("destroy");

                var data = {
                    foto: self.foto,
                    _path_conf: self.path_conf,
                    ts: self.tsArtic,
                    fotow: self.resizeWidth,
                    fotoh: self.resizeHeight,
                    only_resize: 1
                };

                $.ajax({
                    url: "/" + DIR_CGI_CPAN + "/prontus_editor_imag_guardar.cgi",
                    type: "POST",
                    dataType: "json",
                    data: data,
                    success: function (response) {
                        if (response.status == 1) {
                            self.actions.imagGuardarCallback(response);
                        } else {
                            alert(response.msg);

                            $('.tools-container .loading').hide();
                            $('.tools-container .tools').show();
                            $('.tools-container .size-adj').show();
                            $('.image-container').css("opacity", 1);

                            $(self.imgElementId).css({
                                width: "auto",
                                height: "auto",
                                margin: "auto"
                            });

                            self.actions.resize(); // lo inicializa de nuevo.
                        }
                    },
                    error: function () {
                        alert('Ocurrió un error al procesar la imagen, inténtelo nuevamente.');

                        $('.tools-container .loading').hide();
                        $('.tools-container .tools').show();
                        $('.tools-container .size-adj').show();
                        $('.image-container').css("opacity", 1);

                        $(self.imgElementId).css({
                            width: "auto",
                            height: "auto",
                            margin: "auto"
                        });

                        self.actions.resize(); // lo inicializa de nuevo.
                    }
                });

            },
            imagGuardarCallback: function (response) {
                var arr = response.msg.split(';');
                var url = arr[0];
                var numfoto = arr[1];
                var wfoto = arr[2];
                var hfoto = arr[3];

                // Agregar wfoto y hfoto.  obtener esos datos del banco de imagenes.
                var html = [
                    '<input type="hidden" name="_w%%numfoto%%" value="%%wfoto%%">',
                    '<input type="hidden" name="_h%%numfoto%%" value="%%hfoto%%">'
                ].join("").replace(/%%numfoto%%/g, numfoto).replace(/%%wfoto%%/g, wfoto).replace(/%%hfoto%%/g, hfoto);

                parent.$("#_mainFidForm").prepend(html);

                // Se actualiza el banco de imagenes.
                parent.FotoFija.methods.reloadBancoImagenes(true); // Guardar despues de recargar el banco de imagenes.

                // Cerrar colorbox.
                parent.$.colorbox.close();
            },
            move_down: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('move', 0, 10);
                self.hasChanges = true;
            },
            move_up: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('move', 0, -10);
                self.hasChanges = true;
            },
            move_right: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('move', 10, 0);
                self.hasChanges = true;
            },
            move_left: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('move', -10, 0);
                self.hasChanges = true;
            },
            reset: function (e) {
                if (typeof e !== 'undefined') {
                    e.preventDefault();
                }

                // Solo resize de imagen.
                if (self.resizing) {
                    if (self.resizeWidth && self.resizeHeight) {
                        if (!confirm("Hay cambios pendientes de aplicar. Si reinicia la edición estos se perderán.")) {
                            return false;
                        }
                    }

                    self.resizing = false;
                    self.hasChanges = false;

                    $('#freesize_width').attr("disabled", "disabled");
                    $('#freesize_height').attr("disabled", "disabled");

                    $(".tools.zoom a").css("opacity", 1);
                    $(".tools.rotate a").css("opacity", 1);
                    $(".tools.move a").css("opacity", 1);
                    $(".tools.resize").removeClass("active");
                    $(".tools.resize .resize-chain").removeClass("active");
                    $(".tools.resize .resize-chain").hide();

                    $("#link").off("click");

                    $(self.imgElementId).resizable("destroy");

                    self.init(self.foto, self.path_conf, self.activeFotoFija, self.tsArtic);
                } else {
                    if (self.hasChanges) {
                        if (confirm("Hay cambios pendientes de aplicar. Si reinicia la edición estos se perderán.")) {
                            $(self.imgElementId).cropper('clear');
                            $(self.imgElementId).cropper('reset');
                            $(self.imgElementId).cropper('crop');
                            self.hasChanges = false;
                        }
                    } else {
                        $(self.imgElementId).cropper('clear');
                        $(self.imgElementId).cropper('reset');
                        $(self.imgElementId).cropper('crop');
                    }
                }
            },
            rotate_right: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('rotate', 90);
                self.hasChanges = true;
            },
            rotate_left: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('rotate', -90);
                self.hasChanges = true;
            },
            zoom_out: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('zoom', -0.1);
                self.hasChanges = true;
            },
            zoom_in: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('zoom', 0.1);
                self.hasChanges = true;
            },
            cancel: function (e) {
                e.preventDefault();

                if (!self.hasChanges) {
                    parent.$.colorbox.close();
                } else {
                    if (confirm("Al cancelar, sus cambios se perderán. ¿Está seguro de cancelar sus cambios?")) {
                        parent.$.colorbox.close();
                    }
                }
            },
            resize: function (e) {
                if (typeof e !== 'undefined') {
                    e.preventDefault();
                }

                self.methods.offFotosFijas();
                self.resizing = true;

                if ($(".tools.resize").hasClass("active")) {
                    $(".tools.resize").removeClass("active");

                    self.actions.reset();

                    $('#freesize_width').val('');
                    $('#freesize_height').val('');

                    return false;
                }

                $(".tools.zoom a").css("opacity", 0.5);
                $(".tools.rotate a").css("opacity", 0.5);
                $(".tools.move a").css("opacity", 0.5);
                $(".tools.resize .resize-chain").show();
                $(".tools.resize").addClass("active");
                $('.tools-container .warning').hide();

                // Bindear botones a funcion dummy.
                $("#zoom_in").off("click").on("click", function (e) {e.preventDefault; return false;});
                $("#zoom_out").off("click").on("click", function (e) {e.preventDefault; return false;});
                $("#rotate_left").off("click").on("click", function (e) {e.preventDefault; return false;});
                $("#rotate_right").off("click").on("click", function (e) {e.preventDefault; return false;});
                $("#move_left").off("click").on("click", function (e) {e.preventDefault; return false;});
                $("#move_right").off("click").on("click", function (e) {e.preventDefault; return false;});
                $("#move_up").off("click").on("click", function (e) {e.preventDefault; return false;});
                $("#move_down").off("click").on("click", function (e) {e.preventDefault; return false;});

                // El metodo para redimensionar se cambia y se deja separado.
                $("#apply").off("click").on("click", self.actions.applyResize);

                // Redimensión libre o proporcional.
                $("#link").off("click").on("click", self.actions.resizeChain);

                $(self.imgElementId).cropper('destroy'); // Quita el cropper.
                $(self.imgElementId).addClass("resizing");

                $(self.imgElementId).css({
                    width: "auto",
                    height: "auto",
                    margin: "auto"
                });

                self.resizeOrigWidth = $(self.imgElementId).width();
                self.resizeOrigHeight = $(self.imgElementId).height();

                if ($(self.imgElementId).hasClass("ui-resizable")) {
                    return false;
                }

                $('#freesize_width').removeAttr("disabled");
                $('#freesize_height').removeAttr("disabled");

                self.actions.initResizable(true);
            },
            initResizable: function (aspectRatio) {
                var maxWidth = self.resizeOrigWidth;
                var maxHeight = self.resizeOrigHeight;

                $(self.imgElementId).resizable({
                    aspectRatio: aspectRatio,
                    minHeight: 80,
                    minWidth: 80,
                    maxWidth: maxWidth, // ajustar al ancho del container.
                    maxHeight: maxHeight,
                    handles: "all",
                    resize: function(event, ui) {
                        $(this).css({
                            "top": 0,
                            "left": 0,
                            "right": 0,
                            "bottom": 0,
                            "margin": "auto"
                        });

                        var p1 = (ui.size.width * 100) / maxWidth;
                        var p2 = (ui.size.height * 100) / maxHeight;
                        var w = Math.round($(self.imgElementId)[0].naturalWidth * p1/100);
                        var h = Math.round($(self.imgElementId)[0].naturalHeight * p2/100);

                        $('#freesize_width').val(w);
                        $('#freesize_height').val(h);

                        self.resizeWidth = w;
                        self.resizeHeight = h;
                        self.hasChanges = true;
                    },
                    create: function (event, ui) {
                        $(this).css({
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            margin: "auto"
                        });

                        $('#freesize_width').val($(self.imgElementId)[0].naturalWidth);
                        $('#freesize_height').val($(self.imgElementId)[0].naturalHeight);

                        $("#freesize_width").off('keyup').on("keyup", function (e) {
                            if (e.keyCode == 13) { // enter
                                if (self.resizeChain) {
                                    self.actions.updateResizeWidth();
                                } else {
                                    self.actions.updateResizeWidth();
                                    self.actions.updateResizeHeight();
                                }
                            }
                        });

                        $("#freesize_height").off('keyup').on("keyup", function (e) {
                            if (e.keyCode == 13) { // enter
                                if (self.resizeChain) {
                                    self.actions.updateResizeHeight();
                                } else {
                                    self.actions.updateResizeWidth();
                                    self.actions.updateResizeHeight();
                                }
                            }
                        });
                    }
                });
            },
            resizeChain: function (e) {
                if (typeof e !== 'undefined') {
                    e.preventDefault();
                }

                if ($(".tools.resize .resize-chain").hasClass("active")) {
                    // Deshabilita.
                    $(".tools.resize .resize-chain").removeClass("active");
                    $(".tools.resize .resize-chain img").attr("src", $(".tools.resize .resize-chain img").attr("data-off"));

                    $(self.imgElementId).resizable("destroy");
                    $(self.imgElementId).css({
                        width: "auto",
                        height: "auto",
                        margin: "auto"
                    });

                    self.resizeChain = true;
                    self.actions.initResizable(true);

                } else {
                    // Habilita.
                    $(".tools.resize .resize-chain").addClass("active");
                    $(".tools.resize .resize-chain img").attr("src", $(".tools.resize .resize-chain img").attr("data-on"));

                    $(self.imgElementId).resizable("destroy");
                    $(self.imgElementId).css({
                        width: "auto",
                        height: "auto",
                        margin: "auto"
                    });

                    self.resizeChain = false;
                    self.actions.initResizable(false); // Sin respetar proporciones.
                }
            },
            updateResizeWidth: function () {
                var val = $("#freesize_width").val();
                if ($.isNumeric(val) === false) {
                    alert('El ancho de la foto debe ser numérico.');
                    return false;
                }

                var w = Math.round((val * self.resizeOrigWidth) / $(self.imgElementId)[0].naturalWidth);

                if (val > $(self.imgElementId)[0].naturalWidth) {
                    alert("El ancho de la foto redimensionada no puede ser mayor a " + $(self.imgElementId)[0].naturalWidth + " pixeles.");

                    return false;
                }

                if (self.resizeChain) {
                    var newSize = self.actions.calculateSize($(self.imgElementId)[0].naturalWidth, $(self.imgElementId)[0].naturalHeight, $("#freesize_width").val(), false);
                    var w = (newSize[0] * self.resizeOrigWidth) / $(self.imgElementId)[0].naturalWidth;
                    var h = (newSize[1] * self.resizeOrigHeight) / $(self.imgElementId)[0].naturalHeight;

                    self.resizeWidth = newSize[0];
                    self.resizeHeight = newSize[1];

                    $('#freesize_height').val(self.resizeHeight);
                    $(".image-container .ui-wrapper").width(w);
                    $(".image-container .ui-wrapper img").width(w);
                    $(".image-container .ui-wrapper").height(h);
                    $(".image-container .ui-wrapper img").height(h);

                } else {
                    $(".image-container .ui-wrapper").width(w);
                    $(".image-container .ui-wrapper img").width(w);

                    self.resizeWidth = parseInt($('#freesize_width').val());
                    self.resizeHeight = parseInt($('#freesize_height').val());
                }
            },
            updateResizeHeight: function () {
                var val = $('#freesize_height').val();

                if ($.isNumeric(val) === false) {
                    alert('El alto de la foto debe ser numérico.');
                    return false;
                }

                var h = Math.round((val * self.resizeOrigHeight) / $(self.imgElementId)[0].naturalHeight);

                if (val > $(self.imgElementId)[0].naturalHeight) {
                    alert("El alto de la foto redimensionada no puede ser mayor a " + $(self.imgElementId)[0].naturalHeight + " pixeles.");

                    return false;
                }

                if (self.resizeChain) {
                    var newW = ($(self.imgElementId)[0].naturalWidth / $(self.imgElementId)[0].naturalHeight) * val;
                    var newSize = self.actions.calculateSize($(self.imgElementId)[0].naturalWidth, $(self.imgElementId)[0].naturalHeight, false, $("#freesize_height").val());
                    var w = (newSize[0] * self.resizeOrigWidth) / $(self.imgElementId)[0].naturalWidth;
                    var h = (newSize[1] * self.resizeOrigHeight) / $(self.imgElementId)[0].naturalHeight;

                    self.resizeWidth = newSize[0];
                    self.resizeHeight = newSize[1];

                    $('#freesize_width').val(self.resizeWidth);
                    $(".image-container .ui-wrapper").width(w);
                    $(".image-container .ui-wrapper img").width(w);
                    $(".image-container .ui-wrapper").height(h);
                    $(".image-container .ui-wrapper img").height(h);

                } else {
                    $(".image-container .ui-wrapper").height(h);
                    $(".image-container .ui-wrapper img").height(h);

                    self.resizeWidth = parseInt($('#freesize_width').val());
                    self.resizeHeight = parseInt($('#freesize_height').val());
                }
            },
            // scaleSize: function(maxW, maxH, currW, currH) {
            //     var ratio = currH / currW;

            //     if (currW >= maxW && ratio <= 1) {
            //         currW = maxW;
            //         currH = currW * ratio;
            //     } else if (currH >= maxH) {
            //         currH = maxH;
            //         currW = currH / ratio;
            //     }

            //     return [Math.ceil(currW), Math.ceil(currH)];
            // },
            calculateSize: function (origwidth, origheight, width, height) {
                var ratio = origwidth / origheight;

                if (width !== false) {
                    width = parseFloat(width);
                    var newheight = width / ratio;
                    newheight = Math.round(newheight);

                    return [width, newheight];
                } else if (height !== false) {
                    height = parseFloat(height);
                    var newwidth = ratio * height;
                    newwidth = Math.round(newwidth);

                    return [newwidth, height];
                }
            },
            saveZoomRatio: function (e) {
                self.zoomRatio = e.ratio;
                self.hasChanges = true;

                if (self.fotoFijaW && self.fotoFijaH) {
                    var data = $(self.imgElementId).cropper("getData");

                    if (data.width <= self.fotoFijaW || data.height <= self.fotoFijaH) {
                        $('.tools-container .warning').text("Si aplica zoom la foto se verá pixelada.").show();
                    } else {
                        $('.tools-container .warning').hide();
                    }
                }
            },
            showCropSize: function (e) {
                if (self.fotoFijaClicked == 1) {
                    self.fotoFijaClicked = 0;
                    $('#freesize_width').val(Math.round(e.width));
                    $('#freesize_height').val(Math.round(e.height));
                }

                if (Date.now() - self.zooming > 5) {
                    $('#freesize_width').val(Math.round(e.width));
                    $('#freesize_height').val(Math.round(e.height));
                }
            }
        },
        methods: {
            initCropper: function (extraOptions, fnBuilt) {
                var options = {
                    viewMode: 1,
                    dragMode: 'move',
                    autoCropArea: 0.65,
                    restore: false,
                    guides: false,
                    highlight: false,
                    cropBoxMovable: false,
                    cropBoxResizable: true,
                    minCropBoxWidth: 80,
                    minCropBoxHeight: 80,
                    zoom: self.actions.saveZoomRatio,
                    crop: self.actions.showCropSize,
                    built: fnBuilt,
                    cropstart: function (e) {
                        self.hasChanges = true;
                    }
                };

                $(self.imgElementId).cropper('destroy');
                $.extend(options, extraOptions);
                $(self.imgElementId).cropper(options);

                $(self.imgElementId).off('zoom.cropper').on('zoom.cropper', function (e) {
                    self.zooming = e.timeStamp;
                });
            },
            initActions: function () {
                $("#zoom_in").off("click").on("click", self.actions.zoom_in);
                $("#zoom_out").off("click").on("click", self.actions.zoom_out);
                $("#rotate_left").off("click").on("click", self.actions.rotate_left);
                $("#rotate_right").off("click").on("click", self.actions.rotate_right);
                $("#reset").off("click").on("click", self.actions.reset);
                $("#move_left").off("click").on("click", self.actions.move_left);
                $("#move_right").off("click").on("click", self.actions.move_right);
                $("#move_up").off("click").on("click", self.actions.move_up);
                $("#move_down").off("click").on("click", self.actions.move_down);
                $("#apply").off("click").on("click", self.actions.apply);
                $("#cancel").off("click").on("click", self.actions.cancel);
                $("#resize").off("click").on("click", self.actions.resize);
            },
            initFotosFijas: function () {
                self.methods.getCurrentTabFotoFija();
                self.methods.onFotosFijas();
            },
            getCurrentTabFotoFija: function () {
                var cTab = parent.FotoFija.helper.getCurrentTab();

                parent.$(cTab + ' div[id^="recuadro_FOTOFIJA_"]').each(function() {
                    var id = $(this).attr("id").replace("recuadro_FOTOFIJA_", "");
                    var maxW = parent.$('input[name="_MAXWFOTOFIJA_' + id + '"]').val();
                    var maxH = parent.$('input[name="_MAXHFOTOFIJA_' + id + '"]').val();

                    if (id.indexOf('temporal') == -1) { // Se usan en la galeria. Se ignoran.
                        var aspectRatio = parseFloat(maxW / maxH).toFixed(2);
                        var w = 45;
                        var h = 45;

                        if (aspectRatio) {
                            if (h * aspectRatio > w) {
                                h = Math.round(w / aspectRatio);
                            } else {
                                w = Math.round(h * aspectRatio);
                            }
                        }

                        $(".fotos-fijas").append('<div class="box" id="'+ id + '" data-aspectratio="' + aspectRatio + '" data-fotow="' + maxW + '" data-fotoh="' + maxH + '"><div class="modelo" style="width:' + w + 'px;height:' + h + 'px;"></div><div class="size">' + maxW + 'x' + maxH + '</div></div>');
                    }

                });
            },
            checkCropperInstance: function () {
                return $('.cropper-container').length;
            },
            onFotosFijas: function () {
                $(".fotos-fijas .box").off('click').on('click', function (e, trigger) {
                    var aspectRatio = $(this).data("aspectratio");
                    var fotow = $(this).data("fotow");
                    var fotoh = $(this).data("fotoh");

                    if (aspectRatio === 0) {
                        self.free = 1;
                        self.fotoFijaW = 0;
                        self.fotoFijaH = 0;
                        $('.tools-container .warning').hide();
                    } else {
                        self.free = 0;
                    }

                    self.fotoFijaClicked = 1;

                    $(".fotos-fijas .box").removeClass('active');
                    $(this).addClass('active');
                    self.activeFotoFija = $(this).attr("id");

                    $('.image-container').css('opacity', 0).animate({opacity: 1}, 250);

                    $('#freesize_width').val('');
                    $('#freesize_height').val('');

                    if (!trigger) {
                        self.methods.initCropper({}, function () {
                            $(self.imgElementId).cropper("setAspectRatio", aspectRatio);


                            if (fotow && fotoh) {
                                self.fotoFijaW = fotow;
                                self.fotoFijaH = fotoh;

                                if (fotow >= self.imgData.naturalWidth || fotoh >= self.imgData.naturalHeight) {
                                    if (!self.activeFotoFija) {
                                        alert('Advertencia: Las dimensiones de la foto (' + self.imgData.naturalWidth + 'x' + self.imgData.naturalHeight + ') son menores al area a recortar (' + fotow + 'x' + fotoh + ').');
                                    }
                                    // Forzar a quitar el zoom.
                                    $('.tools-container .warning').text("Si aplica zoom a la foto esta se verá pixelada.").show();
                                } else {
                                    $('.tools-container .warning').hide();
                                }

                                $(self.imgElementId).cropper('zoom', 0.05);
                            }
                        });
                    } else {
                        $(self.imgElementId).cropper("setAspectRatio", aspectRatio);

                        if (fotow && fotoh) {
                            self.fotoFijaW = fotow;
                            self.fotoFijaH = fotoh;

                            if (fotow >= self.imgData.naturalWidth || fotoh >= self.imgData.naturalHeight) {
                                if (!self.activeFotoFija) {
                                    alert('Advertencia: Las dimensiones de la foto (' + self.imgData.naturalWidth + 'x' + self.imgData.naturalHeight + ') son menores al area a recortar (' + fotow + 'x' + fotoh + ').');
                                }
                                // Forzar a quitar el zoom.
                                $('.tools-container .warning').text("Si aplica zoom a la foto esta se verá pixelada.").show();
                                self.hasChanges = false;
                            } else {
                                self.hasChanges = false;
                                $('.tools-container .warning').hide();
                            }

                            $(self.imgElementId).cropper('zoom', 0.05);
                        }
                    }
                });

                $(".fotos-fijas .box").css('opacity', 1);
                $(".fotos-fijas").css('overflow-y', 'scroll');
            },

            offFotosFijas: function () {
                $(".fotos-fijas .box").off('click');
                $(".fotos-fijas .box").css('opacity', 0.5);
                $(".fotos-fijas").css('overflow-y', 'hidden');
            }
        }
    };
    window.EditorImag = EditorImag;
})(this);