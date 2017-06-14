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
                    $('.freesize').show();
                    $('.freesize').text(cropData.width + 'x' + cropData.height);
                } else {
                    $("#" + active).trigger("click", true);
                    $('.fotos-fijas').animate({scrollTop: $("#" + active).offset().top}, 500);
                    self.activeFotoFija = active;
                }
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
                        if (data.status == '0') {
                            alert(data.msg);

                            // Si la cgi arroja error, se habilita todo de nuevo para recibir un nuevo intento.
                            $('.tools-container .tools').show();
                            $('.tools-container .loading').hide();
                            $('.image-container').css('opacity', 1);
                            $(self.imgElementId).cropper('enable');
                            self.actions.onFotosfijas();

                        } else {
                            var arr = data.msg.split(';');
                            var url = arr[0];
                            var numfoto = arr[1];
                            var wfoto = arr[2];
                            var hfoto = arr[3];

                            // Agregar wfoto y hfoto.  obtener esos datos del banco de imagenes.
                            var html = [
                                '<input type="hidden" name="_w%%numfoto%%" value="%%wfoto%%">',
                                '<input type="hidden" name="_h%%numfoto%%" value="%%hfoto%%">'
                            ].join("").replace(/%%numfoto%%/g, numfoto).replace(/%%wfoto%%/g, wfoto).replace(/%%hfoto%%/g, hfoto);


                            // La edicion de la foto viene desde una fotofija. Asignar la nueva foto a este campo.
                            if (self.activeFotoFija) {
                                parent.FotoFija.foto.set(self.activeFotoFija, url, wfoto, hfoto);
                                parent.FotoFija.imgEditor = true; // Le dice al padre que se hizo una edición y colorbox debe hacer submit.
                            }

                            parent.$("#_mainFidForm").prepend(html);

                            // Se actualiza el banco de imagenes.
                            parent.FotoFija.methods.reloadBancoImagenes(true); // Guardar despues de recargar el banco de imagenes.

                            // Cerrar colorbox.
                            parent.$.colorbox.close();
                        }
                    },
                    error: function() {
                        alert('Ocurrió un error al procesar la imagen, inténtelo nuevamente.');
                        $('.tools-container .tools').show();
                        $('.tools-container .loading').hide();
                        $('.image-container').css('opacity', 1);
                        $(self.imgElementId).cropper('enable');
                        self.methods.onFotosfijas();
                    }
                });
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
            saveZoomRatio: function (e) {
                self.zoomRatio = e.ratio;
                self.hasChanges = true;

                if (self.fotoFijaW && self.fotoFijaH) {
                    var data = $(self.imgElementId).cropper("getData");

                    console.log(data);

                    if (data.width <= self.fotoFijaW || data.height <= self.fotoFijaH) {
                        // console.log("pixeleando", data.width, data.height);
                        $('.tools-container .warning').text("Si aplica zoom la foto esta se verá pixelada.").show();
                    } else {
                        $('.tools-container .warning').hide();
                    }
                }
            },
            showCropSize: function (e) {
                if (self.free) {
                    $('.freesize').show();
                    $('.freesize').text(Math.round(e.width) + 'x' + Math.round(e.height));
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
            },
            initActions: function () {
                $("#zoom_in").on("click", self.actions.zoom_in);
                $("#zoom_out").on("click", self.actions.zoom_out);
                $("#rotate_left").on("click", self.actions.rotate_left);
                $("#rotate_right").on("click", self.actions.rotate_right);
                $("#reset").on("click", self.actions.reset);
                $("#move_left").on("click", self.actions.move_left);
                $("#move_right").on("click", self.actions.move_right);
                $("#move_up").on("click", self.actions.move_up);
                $("#move_down").on("click", self.actions.move_down);
                $("#apply").on("click", self.actions.apply);
                $("#cancel").on("click", self.actions.cancel);
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
                $(".fotos-fijas .box").on('click', function (e, trigger) {
                    var aspectRatio = $(this).data("aspectratio");
                    var fotow = $(this).data("fotow");
                    var fotoh = $(this).data("fotoh");

                    if (aspectRatio == 0) {
                        self.free = 1;
                        $('.tools-container .warning').hide();
                    } else {
                        self.free = 0;
                        $('.freesize').hide();
                    }

                    $(".fotos-fijas .box").removeClass('active');
                    $(this).addClass('active');
                    self.activeFotoFija = $(this).attr("id");

                    $('.image-container').css('opacity', 0).animate({opacity: 1}, 250);

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
                                    $(self.imgElementId).cropper('zoom', -10);
                                } else {
                                    $('.tools-container .warning').hide();
                                    $(self.imgElementId).cropper('zoom', -10);
                                }
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
                                $(self.imgElementId).cropper('zoom', -10);
                                self.hasChanges = false;
                            } else {
                                $(self.imgElementId).cropper('zoom', -10);
                                self.hasChanges = false;
                                $('.tools-container .warning').hide();
                            }
                        }
                    }

                });

                $(".fotos-fijas .box").css('opacity', 1);
            },

            offFotosFijas: function () {
                $(".fotos-fijas .box").off('click');
                $(".fotos-fijas .box").css('opacity', 0.5);
            }
        }
    };
    window.EditorImag = EditorImag;
})(this);