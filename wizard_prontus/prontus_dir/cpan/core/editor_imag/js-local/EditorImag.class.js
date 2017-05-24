(function (window) {
    var self = null;
    var EditorImag = {
        foto: null,
        path_conf: null,
        zoomRatio: 1,
        imgElementId: "#image",
        init: function (path_foto, w, h, path_conf) {
            self = this;
            self.foto = path_foto;
            self.path_conf = path_conf;

            self.methods.initCropper();
            self.methods.initActions();
            self.methods.initFotosFijas();
        },
        actions: {
            apply: function (e) {
                e.preventDefault();
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
                    _path_conf: self.path_conf
                };

                $.ajax({
                    url: "/" + DIR_CGI_CPAN + "/prontus_editor_imag_guardar.cgi",
                    type: "POST",
                    dataType: "json",
                    data: data,
                    success: function(data) {
                        if (data.status == '0') {
                            alert(data.msg);
                        } else {
                            alert('ok.');

                            parent.$('#_fotoeditada').val(data.msg);
                            parent.Fid.submitir('Guardar', '_self');
                        }
                    },
                    error: function() {
                        alert('Ocurrió un error al procesar la imagen, inténtalo nuevamente.');
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
                $(self.imgElementId).cropper('reset');
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
                parent.$.colorbox.close();
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
                        var w = 50;
                        var h = 50;

                        if (aspectRatio) {
                            if (h * aspectRatio > w) {
                                h = Math.round(w / aspectRatio);
                            } else {
                                w = Math.round(h * aspectRatio);
                            }
                        }

                        $(".fotos-fijas").append('<div class="box" id="'+ v.id + '" data-aspectratio="' + aspectRatio + '"><div class="modelo" style="width:' + w + 'px;height:' + h + 'px;"></div></div>');
                    }
                });

                $(".fotos-fijas .box").on('click', function (e) {
                    var aspectRatio = $(this).data("aspectratio");

                    $(".fotos-fijas .box").removeClass('active');
                    $(self.imgElementId).cropper("setAspectRatio", aspectRatio);
                    $(this).addClass('active');
                });
            }
        }
    };
    window.EditorImag = EditorImag;
})(this);