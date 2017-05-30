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
        activeFotoFija: null,
        init: function (path_foto, path_conf, active, ts) {
            self = this;
            self.foto = path_foto;
            self.path_conf = path_conf;
            self.tsArtic = ts;

            self.methods.initCropper();
            self.methods.initActions();
            self.methods.initFotosFijas();

            // Set active. La edicion viene desde un campo de fotofija.
            if (active) {
                $("#" + active).trigger("click");
                $('.fotos-fijas').animate({scrollTop: $("#" + active).offset().top}, 500);
                self.activeFotoFija = active;
            }
        },
        actions: {
            apply: function (e) {
                e.preventDefault();

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
                    ts: self.tsArtic
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

                            // Se actualiza el banco de imagenes.
                            parent.FotoFija.methods.reloadBancoImagenes();

                            // Agregar wfoto y hfoto.  obtener esos datos del banco de imagenes.
                            var html = [
                                '<input type="hidden" name="_w%%numfoto%%" value="%%wfoto%%">',
                                '<input type="hidden" name="_h%%numfoto%%" value="%%hfoto%%">'
                            ].join("").replace(/%%numfoto%%/g, numfoto).replace(/%%wfoto%%/g, wfoto).replace(/%%hfoto%%/g, hfoto);

                            parent.$("#_mainFidForm").prepend(html);

                            // La edicion de la foto viene desde una fotofija. Asignar la nueva foto a este campo.
                            if (self.activeFotoFija) {
                                parent.FotoFija.foto.set(self.activeFotoFija, url, wfoto, hfoto);
                            }

                            // Cerrar colorbox.
                            parent.$.colorbox.close();
                        }
                    },
                    error: function() {
                        alert('Ocurrió un error al procesar la imagen, inténtalo nuevamente.');
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
            },
            move_up: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('move', 0, -10);
            },
            move_right: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('move', 10, 0);
            },
            move_left: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('move', -10, 0);
            },
            reset: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('clear');
                $(self.imgElementId).cropper('reset');
                $(self.imgElementId).cropper('crop');
            },
            rotate_right: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('rotate', 90);
            },
            rotate_left: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('rotate', -90);
            },
            zoom_out: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('zoom', -0.1);
            },
            zoom_in: function (e) {
                e.preventDefault();
                $(self.imgElementId).cropper('zoom', 0.1);
            },
            cancel: function (e) {
                e.preventDefault();

                if (confirm("Al cancelar, sus cambios se perderán. ¿Está seguro de cancelar sus cambios?")) {
                    parent.$.colorbox.close();
                }
            },
            saveZoomRatio: function (e) {
                self.zoomRatio = e.ratio;
            }
        },
        methods: {
            initCropper: function () {
                $('#image').cropper({
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
                    zoom: self.actions.saveZoomRatio
                });
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
                var fotoFijas = {};

                if (typeof parent.FotoFija.foto !== 'undefined') {
                    fotoFijas = parent.FotoFija.foto.instances;
                }

                $.each(fotoFijas, function (i, v) {
                    if (v.id != "temporal1" && v.id != "temporal2") { // Se usan en la galeria. Se ignoran.
                        var aspectRatio = parseFloat(v.maxW / v.maxH).toFixed(2);
                        var w = 45;
                        var h = 45;

                        if (aspectRatio) {
                            if (h * aspectRatio > w) {
                                h = Math.round(w / aspectRatio);
                            } else {
                                w = Math.round(h * aspectRatio);
                            }
                        }

                        $(".fotos-fijas").append('<div class="box" id="'+ v.id + '" data-aspectratio="' + aspectRatio + '"><div class="modelo" style="width:' + w + 'px;height:' + h + 'px;"></div><div class="size">' + v.maxW + 'x' + v.maxH + '</div></div>');
                    }
                });

                self.methods.onFotosFijas();

            },
            onFotosFijas: function () {
                $(".fotos-fijas .box").on('click', function (e) {
                    var aspectRatio = $(this).data("aspectratio");

                    $(".fotos-fijas .box").removeClass('active');
                    $(self.imgElementId).cropper("setAspectRatio", aspectRatio);
                    $(this).addClass('active');
                    self.activeFotoFija = $(this).attr("id");
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