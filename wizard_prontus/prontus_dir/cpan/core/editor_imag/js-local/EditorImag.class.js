(function (window) {
    var self = null;
    var EditorImag = {
        containerID: "#imag_container",
        imagID: "#imag",
        imag: {
            path: null,
            realWidth: null,
            realHeight: null,
            origWidth: null,
            origHeight: null,
            currentWidth: null,
            currentHeight: null
        },
        lastPost: null,
        zoomScale: 1.0,
        init: function (path_foto, w, h) {
            self = this;
            self.imag.path = path_foto;
            self.imag.realWidth = w;
            self.imag.realHeight = h;

            // loading
            $(self.imagID).on('load', function () {
                self.imag.origWidth = self.imag.currentWidth = $(self.imagID).width();
                self.imag.origHeight = self.imag.currentHeight = $(self.imagID).height();

                console.log(self.imag);
            });

            $(self.imagID).attr("src", self.imag.path);

            self.divWidth = $(self.containerID).width();
            self.divHeight = $(self.containerID).height();

            $(self.imagID).draggable({
                start: function (event, ui) {
                    console.log('start');

                    if ($(self.containerID).width() > $(self.imagID).width()) {
                        return false;
                    }

                    if ($(self.containerID).height() > $(self.imagID).height()) {
                        return false;
                    }

                },
                drag: function (event, ui) {
                    var workAreaOffset = $(self.containerID).offset();
                    var nleft = parseInt(($(self.imagID).width() - $(self.containerID).width()) * -1);
                    var ntop = parseInt(($(self.imagID).height() - $(self.containerID).height()) * -1);

                    if (ui.offset.left >= workAreaOffset.left) {
                        ui.position.left = 0;
                    }

                    if (ui.position.left <= nleft) {
                        ui.position.left = nleft;
                    }

                    if (ui.position.top <= ntop) {
                        ui.position.top = ntop;
                    }

                    if (ui.offset.top >= workAreaOffset.top) {
                        ui.position.top = 0;
                    }
                },
                stop: function (event, ui) {
                    self.lastPost = ui.position;
                }
            });

            self.bindEvents();
        },
        bindEvents: function () {
                $("#zoom_in").on('click', function (e) {
                    e.preventDefault();

                    if ((self.imag.origWidth * self.zoomScale) >= self.imag.realWidth) {
                        return false;
                    } else {
                        self.zoomScale += 0.1;
                    }

                    self.imag.currentWidth = self.imag.origWidth * self.zoomScale;
                    self.imag.currentHeight = self.imag.origHeight * self.zoomScale;

                    $(self.imagID).width(self.imag.currentWidth);
                    $(self.imagID).height(self.imag.currentHeight);

                });

                $("#zoom_out").on('click', function (e) {
                    e.preventDefault();
                    if (self.zoomScale <= 1) {
                        return false;
                    } else {
                        self.zoomScale -= 0.1;
                    }

                    var oldW = self.imag.currentWidth;
                    var oldH = self.imag.currentHeight;

                    self.imag.currentWidth  = self.imag.origWidth * self.zoomScale;
                    self.imag.currentHeight = self.imag.origHeight * self.zoomScale;

                    $(self.imagID).width(self.imag.currentWidth);
                    $(self.imagID).height(self.imag.currentHeight);

                    var diffW   = oldW - self.imag.currentWidth;
                    var diffH   = oldH - self.imag.currentHeight;
                    var newLeft = $(self.imagID).position().left + diffW;
                    var newTop  = $(self.imagID).position().top + diffH;

                    // console.log($(self.imagID).position().top, diffH, 'newTop: ' + newTop, 'newLeft: ' + newLeft);

                    if (newLeft > 0) newLeft = 0;
                    if (newTop > 0) newTop = 0;

                    if ($(self.imagID).position().left <= 0) {
                        $(self.imagID).css("left", newLeft);
                    }

                    if ($(self.imagID).position().top <= 0) {
                        $(self.imagID).css("top", newTop);
                    }
                });

                $(self.imagID).on('mousewheel', function (e) {
                    console.log(e.deltaX, e.deltaY, e.deltaFactor);

                    if (e.deltaY > 0) {
                        // Arriba.
                        $("#zoom_in").trigger('click');
                        // Centrar imagen en puntero del mouse.
                    } else {
                        // Abajo
                        console.log("Abajo");
                        $("#zoom_out").trigger("click");
                    }
                });
        }
    };
    window.EditorImag = EditorImag;
})(this);