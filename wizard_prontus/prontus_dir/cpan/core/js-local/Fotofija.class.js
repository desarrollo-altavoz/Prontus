var Fotofija = {
    // -----------------------------------------
    cropCbWidth: 980,
    cropCbHeight: 600,
    // -----------------------------------------
    cropAreaWidthOrig: '',
    cropAreaHeightOrig: '',
    cropAreaWidth: '',
    cropAreaHeight: '',    
    cropImageUrl: '',
    cropImgWidth: '',
    cropImgHeight: '',
    cropUi: false,
    cropFotofija: '',
    croptInitZoom: 0.1, // %
    slideValue: 0.1,

    // -----------------------------------------
    init: function () {
        Fotofija.validateImageDimensions();

        $('iframe[id^=FOTOFIJA]').each(function() {
            var id = $(this).attr("id");
            var maxw = parseInt($('input[name="_MAXW' + id + '"]').val());
            var maxh = parseInt($('input[name="_MAXH' + id + '"]').val());
            //var bodyiframe = this.contentWindow.document.body;
            var bodyiframe = $(this).contents().find('body');

            $(bodyiframe).on('drop', function (e) {
                setTimeout(function () {
                    Fotofija.handleDropImage(bodyiframe, maxw, maxh, id);
                }, 100);
            });       
        });

    },

    // -----------------------------------------    
    handleDropImage: function (bodyiframe, maxw, maxh, id) {
        var fotow = parseInt(bodyiframe.find('img').attr("data-w"));
        var fotoh = parseInt(bodyiframe.find('img').attr("data-h"));

        console.log(fotow, maxw, '|', fotoh, maxh);

        if (fotow > maxw && fotoh > maxh) {
            var boton = $('img[name="editar' + id + '"]').parent();
            boton.attr("data-w", fotow);
            boton.attr("data-h", fotoh);
            boton.removeClass("disabled");
            boton.show();
        }
    },

    // -----------------------------------------
    disableEdit: function (id) {
        var boton = $('img[name="editar' + id + '"]').parent();
        boton.hide();
        boton.attr("data-w", "");
        boton.attr("data-h", "");
    },

    // -----------------------------------------
    showCrop: function(f, o) {
        if ($(o).hasClass('disabled')) { 
            alert("La foto es muy pequeña en relación al tamaño del campo de foto fija. No se puede editar.");
            return;
        }

        Fotofija.cropFotofija = f; // id de la foto fija.
        Fotofija.cropAreaWidth = Fotofija.cropAreaWidthOrig = parseInt($(o).attr("data-maxw"));
        Fotofija.cropAreaHeight = Fotofija.cropAreaHeightOrig = parseInt($(o).attr("data-maxh"));

        var $body = $(document.getElementById(f).contentWindow.document.body);

        Fotofija.cropImageUrl = $body.find('img').attr("src");

        if (!Fotofija.cropImageUrl) {
            alert("El campo de foto fija no tiene una foto asignada.")
            return;
        }

        // Abrir colorbox.
        Fotofija.cropOpenColorbox(Fotofija.cropAreaWidth, Fotofija.cropAreaHeight);
    },

    // -----------------------------------------
    validateImageDimensions: function () {
        $('a.cropFotofija').each(function () {
            if ($(this).attr("data-w") && $(this).attr("data-w")) {
                if (parseInt($(this).attr("data-w")) <= parseInt($(this).attr("data-maxw")) || parseInt($(this).attr("data-h")) <= parseInt($(this).attr("data-maxh"))) {
                    $(this).addClass('disabled');
                }
            } else {
                $(this).hide();
            }
        });
    },

    // -----------------------------------------
    cropCloseColorbox: function () {
        $.fn.colorbox.close();
    },

    // -----------------------------------------
    cropOpenColorbox: function(w, h) {
        $.fn.colorbox({
            open: true,
            href: '#edit-fotofija',
            width: Fotofija.cropCbWidth,
            height: Fotofija.cropCbHeight,
            maxWidth: '98%',
            maxHeight: '98%',
            opacity: 0.8,
            scroll: true,
            inline: true,
            onComplete: function () {
                // Setear tamaño del crop area.
                // Si es mas grande que el colorbox, se reduce visualmente.
                var newSize = Fotofija.helper.resize(Fotofija.cropAreaWidth, Fotofija.cropAreaHeight, (Fotofija.cropCbWidth-20), (Fotofija.cropCbHeight-20));

                Fotofija.cropAreaWidth = newSize[0]
                Fotofija.cropAreaHeight = newSize[1]

                $('#fotofija-crop-area').css("width", newSize[0]);
                $('#fotofija-crop-area').css("height", newSize[1]);

                // Quitar estilos y tamaño y setiar el src de la foto.
                $('#workImg').attr('style', '').attr("width", '').attr("height", "").attr("src", Fotofija.cropImageUrl);
                $('#workImg2').attr('style', '').attr("width", '').attr("height", "").attr("src", Fotofija.cropImageUrl);

                // Se guardan los tamaños originales de la foto.
                Fotofija.cropImgWidth = $('#workImg').width();
                Fotofija.cropImgHeight = $('#workImg').height();

                Fotofija.cropInstallSlider();
                Fotofija.cropSetZoom(Fotofija.croptInitZoom, true);
                Fotofija.centerWorkImg();
                Fotofija.cropPrepareArea();
                Fotofija.cropInstalllDraggable();
                Fotofija.colorboxAddButtons();
            }
        });
    },

    centerWorkImg: function () {
        var cHeight = $('#fotofija-preview-container').height();
        var cWidth = $('#fotofija-preview-container').width();

        $('#workImg').css({
            top: 0.5 * (cHeight - $('#workImg').height()),
            left: 0.5 * (cWidth - $('#workImg').width())
        });  

    },

    colorboxAddButtons: function () {
        var buttons = '';
        buttons += '<input type="button" value="Aplicar" onclick="Fotofija.cropApply();" />';
        buttons += '<input type="button" value="Cancelar" onclick="Fotofija.cropCloseColorbox();" />';
        $('#cboxBottomCenter').html(buttons);
    },

    cropApply: function() {
        var action = 'crop[' + Fotofija.cropAreaWidthOrig + 'x' + Fotofija.cropAreaHeightOrig;
        action += '+' + $('#workImg2').css('left').replace(/[^\d]/g, '');
        action += '+' + $('#workImg2').css('top').replace(/[^\d]/g, '');

        var imgw = $('#workImg2').css('width').replace(/[^\d]/g, '');
        var imgh = $('#workImg2').css('height').replace(/[^\d]/g, '');

        if (imgw && Fotofija.cropImgWidth != imgw) {
            action += '!' + imgw + 'x' + imgh;
        } else {
            action += '!0x0';
        }

        action += ']';

        $('input[name="_ACTIONS' + Fotofija.cropFotofija + '"]').val(action);

        // convert -resize "1214x910" -crop 80x80+691+601 foto_0000000820150825140343.jpg crop.jpg
        Fotofija.cropCloseColorbox();
    },

    cropPrepareArea: function () {
        var w_container = $('#fotofija-preview-container').width();
        var h_container = $('#fotofija-preview-container').height();

        var area_left = ((w_container / 2) - (Fotofija.cropAreaWidth / 2));
        var area_top = ((h_container / 2) - (Fotofija.cropAreaHeight / 2));

        // Ajusta posicion del crop area, para centrarlo.
        $('#fotofija-crop-area').css('left', area_left);
        $('#fotofija-crop-area').css('top', area_top);

        var cropAreaOffset = $('#fotofija-crop-area').offset();
        var cropAreaPosition = $('#fotofija-crop-area').position();
        var previewAreaOffset = $('#fotofija-preview-container img').offset();

        $('#workImg2').css('left', '-' + (cropAreaOffset.left-previewAreaOffset.left) + 'px');
        $('#workImg2').css('top', '-' + (cropAreaOffset.top-previewAreaOffset.top) + 'px');

        if ($('#workImg2').hasClass('ui-draggable')) {
            $('#workImg2').draggable('destroy');
        }

        $("#workImg2").disableSelection();        
    },

    cropUpdateUi: function () {
        if (!Fotofija.cropUi) return;

        var cropAreaOffset = $('#fotofija-crop-area').offset();

        if (Fotofija.cropUi.offset.left >= cropAreaOffset.left) {
           Fotofija.cropUi.offset.left = cropAreaOffset.left;
           Fotofija.cropUi.position.left = 0;
        }

        if (Fotofija.cropUi.offset.top >= cropAreaOffset.top) {
           Fotofija.cropUi.offset.top = cropAreaOffset.top;
           Fotofija.cropUi.position.top = 0;
        }    

        var r = $('#workImg').width() - Fotofija.cropAreaWidth;

        if ((r+Fotofija.cropUi.position.left) <= 0) {
            Fotofija.cropUi.offset.left = (r - cropAreaOffset.left - 2)*-1; // -2 es por el borde
            Fotofija.cropUi.position.left = r*-1;
        }

        var r = $('#workImg').height() - Fotofija.cropAreaHeight;

        if ((r+Fotofija.cropUi.position.top) <= 0) {
            Fotofija.cropUi.offset.top = (r - cropAreaOffset.top - 2) *-1;
            Fotofija.cropUi.position.top = r * -1;
        }

        $('#workImg').offset({top: (Fotofija.cropUi.offset.top), left: Fotofija.cropUi.offset.left});
    },

    cropInstalllDraggable: function () {
        $("#workImg2").draggable({
            drag: function (event, ui) {
                Fotofija.cropUi = ui;
                Fotofija.cropUpdateUi();
            }         
        });        
    },

    cropSetZoom: function (factor, isInit) {
        var newW = Math.round(Fotofija.cropImgWidth * factor);
        var newH = Fotofija.helper.getHeight(newW, Fotofija.cropImgWidth, Fotofija.cropImgHeight);

        if (isInit) {
            $("#rango-zoom").slider("option", {min:0.1,max:1,value:Fotofija.croptInitZoom});
        }

        if (newW < Fotofija.cropAreaWidth || newH < Fotofija.cropAreaHeight) {
            $("#rango-zoom").slider("option", {min:1,max:1.5,value:1});

            return;
        }
        
        Fotofija.slideValue = $("#rango-zoom").slider("value");        

        $('#workImg').width(newW);
        $('#workImg').height(newH);
        $('#workImg2').width(newW);
        $('#workImg2').height(newH);

        //Fotofija.centerWorkImg();
        Fotofija.cropUpdateUi();
        Fotofija.cropPrepareArea();
    },

    cropInstallSlider: function () {
        $( "#rango-zoom" ).slider({
            min: 0.1,
            max: 1,
            step: 0.01,
            value: 0.1,
            slide: function (e, ui) {
                Fotofija.cropSetZoom(ui.value, false);
            },
            stop: function (e, ui) {
                Fotofija.cropInstalllDraggable();
            }
        });
    },

    helper: {
        resize: function(w, h, maxh, maxw) {
            var ratio = maxh/maxw;

            if (h/w > ratio){
                // height is the problem
                if (h > maxh){
                    w = Math.round(w*(maxh/h));
                    h = maxh;
                }
            } else {
                // width is the problem
                if (w > maxh){
                    h = Math.round(h*(maxw/w));
                    w = maxw;
                }
            }

            return [w, h];
        },
        getHeight: function (newW, imgW, imgH) {
            var proportion = newW / imgW;
            var newH = imgH * proportion;

            return Math.round(newH);
        }      
    }
};