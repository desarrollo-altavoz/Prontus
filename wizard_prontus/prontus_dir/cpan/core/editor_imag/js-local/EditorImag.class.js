(function (window) {
    var self = null;
    var EditorImag = {
        currentZoom: 0,
        init: function (path_foto, w, h) {
            $("#image").on('load', function () {
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
                    minCropBoxHeight: 80
                });
            });

            $("#image").attr("src", path_foto);

            $("#zoom_in").on("click", function (e) {
                e.preventDefault();
                $("#image").cropper('zoom', 0.1)
            });

            $("#zoom_out").on("click", function (e) {
                e.preventDefault();
                $("#image").cropper('zoom', -0.1)
            });

            $("#rotate_left").on("click", function (e) {
                e.preventDefault();
                $("#image").cropper('rotate', -90)
            });

            $("#rotate_right").on("click", function (e) {
                e.preventDefault();
                $("#image").cropper('rotate', 90);
            });

            $("#reset").on("click", function (e) {
                e.preventDefault();
                $("#image").cropper('reset');
            });

            $("#move_left").on("click", function (e) {
                e.preventDefault();
                $("#image").cropper('move', -10, 0);
            });

            $("#move_right").on("click", function (e) {
                e.preventDefault();
                $("#image").cropper('move', 10, 0);
            });

            $("#move_up").on("click", function (e) {
                e.preventDefault();
                $("#image").cropper('move', 0, -10);
            });

            $("#move_down").on("click", function (e) {
                e.preventDefault();
                $("#image").cropper('move', 0, 10);
            });


            var fotoFijas = {};

            if (typeof parent.FotoFija.foto !== 'undefined') {
                fotoFijas = parent.FotoFija.foto.instances;
            }

            console.log(fotoFijas);

            $.each(fotoFijas, function (i, v) {
                if (v.id != "temporal1" && v.id != "temporal2") {
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

                    $(".fotos-fijas").append('<div class="box" id="'+ v.id + '" data-aspectratio="' + aspectRatio + '"><div class="size">' + v.maxW + 'x' + v.maxH +
                                             '</div><div class="modelo" style="width:' + w + 'px;height:' + h + 'px;"></div></div>');

                    console.log(w, h);

                }
            });

            $(".fotos-fijas .box").on('click', function (e) {
                var aspectRatio = $(this).data("aspectratio");
                $("#image").cropper("setAspectRatio", aspectRatio);
            });

        }
    };
    window.EditorImag = EditorImag;
})(this);