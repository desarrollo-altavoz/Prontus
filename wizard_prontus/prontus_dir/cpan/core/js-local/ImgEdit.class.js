/* Editor de imagenes - JOR */
var ImgEdit = {
    img_w: 0,
    img_h: 0,
    ejeX: 0, // Horizontal
    ejeY: 0, // Vertical
    crop: false,
    cropStatus: false,
    resizeStatus: false,
    crop_aspect: true,
    resize_aspect_val: true,
    guardar: false,
    rotacion: 0,
    msgboxInterval: false,
    max_width: 3888, // Equivale a una foto de 10 MPX
    max_height: 2592, // Equivale a una foto de 10 MPX
    // ---------------------------------------------------------------
    init_selector: function() {
        var pos_contenedor = $('#imagenContenedor').position();
        $('#imagenSelector').width(ImgEdit.img_w);
        $('#imagenSelector').height(ImgEdit.img_h);

        $('#Contenedor').width(ImgEdit.img_w);
        $('#Contenedor').height(ImgEdit.img_h);
        
        $('#imagenSelector').css('top', pos_contenedor.top+'px');
        $('#imagenSelector').css('left', Math.round(pos_contenedor.left)+'px');
    },
    // ---------------------------------------------------------------
    init: function (img_width, img_height) {
        ImgEdit.img_w = parseInt(img_width);
        ImgEdit.img_h = parseInt(img_height);
        $('#imagenContenedor').width(ImgEdit.img_w);
        $('#imagenContenedor').height(ImgEdit.img_h);
        ImgEdit.init_selector();

        $('#imagenContenedor').mousemove(function (e) {
            var pos = $(this).position();
            ImgEdit.ejeX = e.pageX;
            ImgEdit.ejeY = e.pageY;
        });

        $('#w').val(img_width);
        $('#h').val(img_height);
        
        // Setea valores por defecto.
        $('#srcX').val('');
        $('#srcY').val('');
        $('#width').val('');
        $('#height').val('');
        $('#new_width').val('');
        $('#new_height').val('');
        $('#flipv').val(0);
        $('#fliph').val(0);
        $('#rotar').val(0);
        $('#crop').val(0);
        $('#resize').val(0);

    },
    // ---------------------------------------------------------------
    crop_init: function() {
        ImgEdit.toggleImg('btn_crop');

        if (ImgEdit.cropStatus === true) {
            ImgEdit.crop_destroy();
        } else {
            ImgEdit.cropStatus = true;
            ImgEdit.resize_destroy();
            
            $('#imagenContenedor').mousemove(function (e) {
                var pos = $(this).position();
                ImgEdit.ejeX = e.pageX;
                ImgEdit.ejeY = e.pageY;
            });
            
            $('#imagenContenedor').css('cursor','crosshair');
            
            $('#imagenContenedor').mousedown(function (e) {
                if (e.preventDefault) e.preventDefault();
                ImgEdit.crop_start();
            });
            
            if ($.browser.msie) {
                document.ondragstart = function(e) {
                    return false;
                };
            };
            
            $('#imagenContenedor').mousemove(function (e) {
                ImgEdit.crop_resize(e);
            });
            
            $('#imagenSelector').mouseup(function () {
                ImgEdit.crop_end();
            });
            
            $('#imagenContenedor').mouseup(function () {
                ImgEdit.crop_end();
            });
            
            $('#imagenSelector').draggable({
                containment: "parent"
            });
            
            $('#imagenSelector').bind('drag', function () {
                ImgEdit.crop_move();
            });
            
            $('#imagenSelector').unbind('dblclick');
          
            $('#imagenSelector').dblclick(function () {
              ImgEdit.crop_aplicar();
            });

            $('#w').change(function () {
                ImgEdit.crop_input_w($(this).val());
            });
            $('#h').change(function () {
                ImgEdit.crop_input_h($(this).val());
            });
        };
    },
    // ---------------------------------------------------------------
    crop_start: function () {
        
        if($('#imagenSelector').data('resizable')) {
            $('#imagenSelector').resizable('destroy');
        }

        var imagen_pos = $('#imagenContenedor').position();

        var left = (ImgEdit.ejeX - 92);
        var top  = (ImgEdit.ejeY - 143);

        if (left < 0) { left = 0; };
        if (top < 0) { top = 0; };
        
        $('#imagenSelector').css('left', left + 'px');
        $('#imagenSelector').css('top',  top + 'px');
        $('#imagenSelector').width(30);
        $('#imagenSelector').height(30);
        $('#imagenSelector').addClass('crop-selector');
        $('#imagenSelector').show();
        $('#w').val(30);
        $('#h').val(30);

        $('#width').val(30);
        $('#height').val(30);
        
        ImgEdit.crop = true;
    },
    // ---------------------------------------------------------------
    crop_resize: function (e) {
        if (ImgEdit.crop) {
            var selector_pos = $('#imagenSelector').position();
            var imagen_pos = $('#imagenContenedor').position();

            var nuevo_width = ImgEdit.ejeX - (62 + selector_pos.left);
            var nuevo_height = ImgEdit.ejeY - (113 + selector_pos.top);

            if (selector_pos.left < 0 ) {
                selector_pos.left = 0;
                $('#imagenSelector').css('left', '0px');
            }

            if (selector_pos.top < 0 ) {
                selector_pos.top = 0;
                $('#imagenSelector').css('top', '0px');
            }
            
            $('#srcX').val(Math.round(selector_pos.left));
            $('#srcY').val(Math.round(selector_pos.top));
            
            $('#width').val(nuevo_width);
            $('#w').val(nuevo_width);
            $('#height').val(nuevo_height);
            $('#h').val(nuevo_height);
            
            $('#imagenSelector').width(nuevo_width);
            $('#imagenSelector').height(nuevo_height);
        };
    },
    crop_input_w: function (w) {
        var imagen_w = $('#imagenContenedor').width();
        var imagen_h = $('#imagenContenedor').height();
        if (w > imagen_w) {
            alert("No puedes superar el ancho de la imagen ("+ imagen_w +"px).");
            $('#w').val($('input[name="crop_w"]').val());
        } else {
            var selector_pos = $('#imagenSelector').position();
            var image_pos = $('#imagenContenedor').position();
            var limite = (imagen_w - w) - 2; // se le resta 2 porque son los pixel de los bordes.
            if (limite < 0) { limite = 0; };
            if (selector_pos.left > limite) {
                $('#imagenSelector').css('left', limite+'px');
            };
            var ch = $('#imagenSelector').height();
            var cw = $('#imagenSelector').width();
            if (ImgEdit.crop_aspect === true) {
                var calculo = Math.round((100*w)/ cw);
                var nuevo_height = Math.round((ch*calculo)/100);
                if (nuevo_height > imagen_h) { nuevo_height = imagen_h; };
                $('#height').val(nuevo_height);
                $('#imagenSelector').height(parseInt(nuevo_height));
                $('#h').val(nuevo_height);
                limite = (imagen_h - nuevo_height) - 2; // se le resta 2 porque son los pixel de los bordes.
                if (selector_pos.top > limite) {
                    $('#imagenSelector').css('top', limite+'px');
                };
            };
                
            $('#width').val(w);
            $('#imagenSelector').width(parseInt(w));
            ImgEdit.crop_move();
        };
    },
    crop_input_h: function (h) {
        var imagen_h = $('#imagenContenedor').height();
        var imagen_w = $('#imagenContenedor').width();
        if (h > imagen_h) {
            alert("No puedes superar el alto de la imagen ("+ imagen_h + "px).");
            $('#h').val($('input[name="crop_h"]').val());
        } else {
            var selector_pos = $('#imagenSelector').position();
            var image_pos = $('#imagenContenedor').position();
            var limite = (imagen_h - h) - 2; // se le resta 2 porque son los pixel de los bordes.
            if (limite < 0) { limite = 0; };
            if (selector_pos.top > limite) {
                $('#imagenSelector').css('top', limite+'px');
            };
            var ch = $('#imagenSelector').height();
            var cw = $('#imagenSelector').width();
            if (ImgEdit.crop_aspect === true) {
                var calculo = Math.round((100*h)/ ch);
                var nuevo_width = Math.round((cw*calculo)/100);
                if (nuevo_width > imagen_w) { nuevo_width = imagen_w; };
                $('#width').val(nuevo_width);
                $('#imagenSelector').width(parseInt(nuevo_width));
                $('#w').val(nuevo_width);
                limite = (imagen_w - nuevo_width) - 2; // se le resta 2 porque son los pixel de los bordes.
                if (selector_pos.left > limite) {
                    $('#imagenSelector').css('left', limite+'px');
                };
            };
            $('#height').val(h);
            $('#imagenSelector').height(parseInt(h));
            ImgEdit.crop_move();
        }
    },
    // ---------------------------------------------------------------
    crop_end: function () {
        $('#btn_crop_aplicar').show();
        $('#btn_crop_aspect').show();
        ImgEdit.crop = false;
        $('#imagenSelector').resizable({
            resize: function() {
                var nuevo_width = $('#imagenSelector').width();
                var nuevo_height = $('#imagenSelector').height();
                $('#w').val(nuevo_width);
                $('#h').val(nuevo_height);
                $('#width').val(nuevo_width);
                $('#height').val(nuevo_height);
            },
            handles: 'n,e,s,w,ne,se,sw,nw',
            containment: 'parent',
            aspectRatio: true
        });
    },
    // ---------------------------------------------------------------
    crop_aspect_free: function () {
        ImgEdit.toggleImg('btn_crop_aspect');
        if (ImgEdit.crop_aspect) {
            if($('#imagenSelector').data('resizable')) {
                $('#imagenSelector').resizable('destroy');
            }
            $('#imagenSelector').resizable({
                resize: function() {
                    var nuevo_width = $('#imagenSelector').width();
                    var nuevo_height = $('#imagenSelector').height();
                    $('#w').val(nuevo_width);
                    $('#h').val(nuevo_height);
                    $('#width').val(nuevo_width);
                    $('#height').val(nuevo_height);
                },
                handles: 'n,e,s,w,ne,se,sw,nw',
                containment: 'parent',
                aspectRatio: false
            });
            ImgEdit.crop_aspect = false;
        } else {
            if($('#imagenSelector').data('resizable')) {
                $('#imagenSelector').resizable('destroy');
            }
            $('#imagenSelector').resizable({
                resize: function() {
                    var nuevo_width = $('#imagenSelector').width();
                    var nuevo_height = $('#imagenSelector').height();
                    $('#w').val(nuevo_width);
                    $('#h').val(nuevo_height);
                    $('#width').val(nuevo_width);
                    $('#height').val(nuevo_height);
                },
                handles: 'n,e,s,w,ne,se,sw,nw',
                containment: 'parent',
                aspectRatio: true
            });
            ImgEdit.crop_aspect = true;
        };
    },
    // ---------------------------------------------------------------
    crop_destroy: function () {
        if(ImgEdit.cropStatus) {
            ImgEdit.toggleImg('btn_crop', true);
            $('#btn_crop_aplicar').hide();
            $('#btn_crop_aspect').hide();
            $('#imagenSelector').hide();
            $('#imagenSelector').removeClass();
            if($('#imagenSelector').data('draggable')) {
                $('#imagenSelector').draggable('destroy');
            }
            if($('#imagenSelector').data('resizable')) {
                $('#imagenSelector').resizable('destroy');
            }
            $('#imagenContenedor').unbind('mousemove');
            $('#imagenContenedor').unbind('mousedown');
            $('#imagenSelector').unbind('mouseup');
            $('#imagenContenedor').unbind('mouseup');
            $('#imagenContenedor').css('cursor','default');
            $('#imagenSelector').unbind('dblclick');
            $('#width').val('');
            $('#height').val('');
            $('#crop').val(0);
            ImgEdit.crop = false;
            ImgEdit.cropStatus = false;
            $('#h').unbind('change');
            $('#w').unbind('change');
        }
    },
    // ---------------------------------------------------------------
    crop_move: function () {
        var selector_pos = $('#imagenSelector').position();
        var imagen_pos = $('#imagenContenedor').position();

        var left = Math.round(selector_pos.left);
        var top = Math.round(selector_pos.top);

        if (left < 0) { left = 0; };
        if (top < 0) { top = 0; };
        $('#srcX').val(left);
        $('#srcY').val(top);
    },
    // ---------------------------------------------------------------
    crop_aplicar: function () {
        $('#imagenSelector').hide();
        $('#btn_crop_aplicar').hide();
        
        $('#crop').val(1);
        
        ImgEdit._toggleCargando();
        ImgEdit._enviarAjax();
        
        ImgEdit.crop = false;
        ImgEdit.crop_destroy();

        // Mostrar mensaje.
        
    },
    // ------------------------------------------------------------------
    resize_init: function (a) {
        var avoid = (typeof a !== 'undefined' ? true : false);
        if (ImgEdit.resizeStatus === true && avoid === false) {
            ImgEdit.resize_destroy();
        } else {
            ImgEdit.resizeStatus = true;
            ImgEdit.crop_destroy();
            ImgEdit.toggleImg('btn_resize');
            $('#btn_resize_aspect').show();
            var img_w = $('#Contenedor').width();
            var img_h = $('#Contenedor').height();
            $('#imagenSelector').css('top', '0px');
            $('#imagenSelector').css('left', '0px');
            $('#imagenSelector').width(img_w-2);
            $('#imagenSelector').height(img_h-2);
            $('#imagenSelector').show();
            $('#imagenSelector').addClass('resizing');
            if($('#imagenSelector').data('draggable')) {
                $('#imagenSelector').draggable('destroy');
            }
            if($('#imagenSelector').data('resizable')) {
                $('#imagenSelector').resizable('destroy');
            }
            $('#imagenSelector').resizable({
                aspectRatio: true,
                resize: function () {
                    ImgEdit.resize_do();
                },
                stop: function () {
                    ImgEdit.resize_end();
                },
            });
          $('#imagenSelector').dblclick(function () {
              ImgEdit.resize_aplicar();
          });
            $('#w').change(function () {
                ImgEdit.resize_input_w($(this).val());
            });
            $('#h').change(function () {
                ImgEdit.resize_input_h($(this).val());
            });
        };
    },
    // ---------------------------------------------------------------
    resize_init_free: function () {
        ImgEdit.crop_destroy();
        var img_w = $('#Contenedor').width();
        var img_h = $('#Contenedor').height();
        $('#imagenSelector').css('top', '0px');
        $('#imagenSelector').css('left', '0px');
        $('#imagenSelector').width(img_w-2);
        $('#imagenSelector').height(img_h-2);
        $('#imagenSelector').show();
        $('#imagenSelector').addClass('resizing');
        if($('#imagenSelector').data('draggable')) {
            $('#imagenSelector').draggable('destroy');
        }
        if($('#imagenSelector').data('resizable')) {
            $('#imagenSelector').resizable('destroy');
        }
        $('#imagenSelector').resizable({
            resize: function () {
                ImgEdit.resize_do();
            },
            stop: function () {
                ImgEdit.resize_end();
            },
        });

        $('#w').change(function () {
            ImgEdit.resize_input_w($(this).val());
        });
        $('#h').change(function () {
            ImgEdit.resize_input_h($(this).val());
        });
            
    },
    // ---------------------------------------------------------------
    resize_aspect: function () {
        if ($('#btn_resize_aspect').attr("title") === 'Liberar proporciones') {
            $('#btn_resize_aspect').attr("title", "Fijar proporciones");
        } else {
            $('#btn_resize_aspect').attr("title", "Liberar proporciones");
        }
        ImgEdit.toggleImg('btn_resize_aspect');
        if (ImgEdit.resize_aspect_val) {
            ImgEdit.resize_init_free();
            ImgEdit.resize_aspect_val = false;
        } else {
            ImgEdit.resize_init(true);
            ImgEdit.resize_aspect_val = true;
        };
    },
    // ---------------------------------------------------------------
    resize_do: function () {
        var nuevo_width = $('#imagenSelector').width();
        var nuevo_height = $('#imagenSelector').height();

        var img_w = $('#imagenContenedor').width();
        var img_h = $('#imagenContenedor').height();

        var position_img = $('#imagenContenedor').position();
        var div_w = $('#Contenedor').width();
        var div_h = $('#Contenedor').height();
        
        $('#w').val(nuevo_width);
        $('#h').val(nuevo_height);

        $('#imagenContenedor').width((img_w * nuevo_width/div_w));
        $('#imagenContenedor').height(img_h * nuevo_height/div_h);
        
        var currOffW = position_img.left * nuevo_width/div_w;
        var currOffH = position_img.top * nuevo_height/div_h;
        $('#imagenContenedor').css('top',currOffH+'px');
        $('#imagenContenedor').css('left',currOffW+'px');

        $('#srcX').val(currOffW);
        $('#srcY').val(currOffH);

        $('#imagenSelector').width($('#imagenSelector').width()-2);
        $('#imagenSelector').height($('#imagenSelector').height()-2);
        
        $('#Contenedor').width(nuevo_width);
        $('#Contenedor').height(nuevo_height);
  
    },
    // ---------------------------------------------------------------
    resize_end: function () {
        $('#btn_resize_aplicar').show();
    },
    // ---------------------------------------------------------------
    resize_destroy: function () {
        if(ImgEdit.resizeStatus) {
            ImgEdit.resizeStatus = false;
            ImgEdit.toggleImg('btn_resize', true);
            $('#imagenSelector').removeClass('resizing');
            if($('#imagenSelector').data('draggable')) {
                $('#imagenSelector').draggable('destroy');
            }
            if($('#imagenSelector').data('resizable')) {
                $('#imagenSelector').resizable('destroy');
            }
            $('#imagenSelector').width(30);
            $('#imagenSelector').height(30);
            $('#imagenSelector').hide();
            $('#btn_resize_aplicar').hide();
            $('#btn_resize_aspect').hide();

            $('#new_width').val('');
            $('#new_height').val('');
            $('#resize').val(0);

            $('#h').unbind('change');
            $('#w').unbind('change');
        };
    },
    // ---------------------------------------------------------------
    resize_aplicar: function () {
        $('#imagenSelector').removeClass('resizing');
        $('#imagenSelector').hide();
        $('#btn_resize_aplicar').hide();
        $('#btn_resize_aspect').hide();

        var nuevo_width = $('#Contenedor').width();
        var nuevo_height = $('#Contenedor').height();

        $('#new_width').val(nuevo_width);
        $('#new_height').val(nuevo_height);
        //$('#Contenedor').resizable('destroy');
        $('#resize').val(1);
        
        ImgEdit._toggleCargando();
        ImgEdit._enviarAjax();
        
        ImgEdit.resize_destroy();
    },
    resize_input_w: function (w) {
        var ch = $('#imagenContenedor').height();
        var cw = $('#imagenContenedor').width();

        if (w > ImgEdit.max_width) {
            alert("La imagen no puede soprepasar las dimesiones " + ImgEdit.max_width + "x" + ImgEdit.max_height + "px.");
            w = ImgEdit.max_width;
            $('#w').val(ImgEdit.max_width);
        };
        
        if (ImgEdit.resize_aspect_val === true) {
            var calculo = Math.round((100*w)/ cw);
            var nuevo_height = Math.round((ch*calculo)/100);
            
            if (nuevo_height > ImgEdit.max_height) {
                nuevo_height = ImgEdit.max_height;
            };
            
            $('#new_height').val(nuevo_height);
            $('#imagenContenedor').height(parseInt(nuevo_height));
            $('#Contenedor').height(parseInt(nuevo_height));
            $('#imagenSelector').height(parseInt(nuevo_height));
            $('#h').val(nuevo_height);
        }
        $('#new_width').val(w);
        $('#imagenContenedor').width(parseInt(w));
        $('#Contenedor').width(parseInt(w));
        $('#imagenSelector').width(parseInt(w));
        
        if (!$('#btn_resize_aplicar').is(':visible')) {
            $('#btn_resize_aplicar').show();
        };
    },
    resize_input_h: function (h) {
        var ch = $('#imagenContenedor').height();
        var cw = $('#imagenContenedor').width();

        if (h > ImgEdit.max_height) {
            alert("La imagen no puede soprepasar las dimesiones " + ImgEdit.max_width + "x" + ImgEdit.max_height + "px.");
            h = ImgEdit.max_height;
            $('#h').val(ImgEdit.max_height);
        };
        
        if (ImgEdit.resize_aspect_val === true) {
            var calculo = Math.round((100*h)/ ch);
            var nuevo_width = Math.round((cw*calculo)/100);
            if (nuevo_width > ImgEdit.max_width) {
                nuevo_width = ImgEdit.max_width;
            };
            $('#new_width').val(nuevo_width);
            $('#imagenContenedor').width(parseInt(nuevo_width));
            $('#Contenedor').width(parseInt(nuevo_width));
            $('#imagenSelector').width(parseInt(nuevo_width));
            $('#w').val(nuevo_width);
        }
        $('#new_height').val(h);
        $('#imagenContenedor').height(parseInt(h));
        $('#Contenedor').height(parseInt(h));
        $('#imagenSelector').height(parseInt(h));

        if (!$('#btn_resize_aplicar').is(':visible')) {
            $('#btn_resize_aplicar').show();
        };
    },
    // ---------------------------------------------------------------
    flip_h: function () {
        ImgEdit.crop_destroy();
        ImgEdit.resize_destroy();
        ImgEdit.toggleImg('btn_fliph');

        $('#fliph').val('1');

        ImgEdit._toggleCargando();
        ImgEdit._enviarAjax();
    },
    // ---------------------------------------------------------------
    flip_v: function () {
        ImgEdit.crop_destroy();
        ImgEdit.resize_destroy();
        ImgEdit.toggleImg('btn_flipv');

        $('#flipv').val('1');

        ImgEdit._toggleCargando();
        ImgEdit._enviarAjax();
    },
    // ---------------------------------------------------------------
    rotard: function () {
        ImgEdit.rotacion = 90;

        var w = $('#Contenedor').width();
        var h = $('#Contenedor').height();
        var mw = $('#imagenContenedor').width();
        var mh = $('#imagenContenedor').height();

        if (ImgEdit.rotacion == '90' || ImgEdit.rotacion == '270') {
            $('#Contenedor').width(h);
            $('#Contenedor').height(w);
        } else {
            $('#Contenedor').width(mw);
            $('#Contenedor').height(mh);
        };
        
        $('#rotar').val(ImgEdit.rotacion);
        if (ImgEdit.rotacion > 0) {
            ImgEdit._toggleCargando();
            ImgEdit._enviarAjax();
        } else {
            ImgEdit.rotari();
        };
    },
    // ---------------------------------------------------------------
    rotari: function () {
        ImgEdit.rotacion = 270;

        var w = $('#Contenedor').width();
        var h = $('#Contenedor').height();
        var mw = $('#imagenContenedor').width();
        var mh = $('#imagenContenedor').height();

        if (ImgEdit.rotacion == '90' || ImgEdit.rotacion == '270') {
            $('#Contenedor').width(h);
            $('#Contenedor').height(w);
        } else {
            $('#Contenedor').width(mw);
            $('#Contenedor').height(mh);
        };
        
        $('#rotar').val(ImgEdit.rotacion);

        if (ImgEdit.rotacion > 0) {
            ImgEdit._toggleCargando();
            ImgEdit._enviarAjax();
        } else {
            ImgEdit.rotard();
        }
    },
    // ---------------------------------------------------------------
    undo: function() {
        var url = window.location.href;
        window.location.href = url.replace('#', '');
    },
    // ---------------------------------------------------------------
    guardar: function() {
        if ($('#image_path_orig').val() == $('#image_path').val()) {
            alert('No has aplicado ninguna modificación.');
        } else {
            ImgEdit._toggleCargando();
            if (window.opener != null) {
                if (window.opener) {
                    window.opener.$('#_fotoeditada').val($('#image_path').val());
                    window.opener.focus();
                    window.opener.Fid.submitir('Guardar', '_self');
                    window.close();
                } else {
                    alert('No es posible guardar la imagen, el artículo ya no se encuentra en edición.');
                };
            } else {
                alert('No es posible guardar la imagen, el artículo ya no se encuentra en edición.');
            };
            ImgEdit._toggleCargando();
        };
    },
    // ---------------------------------------------------------------
    _toggleCargando: function () {
        if ($('#cargando_tools').is(':hidden')) {
            $('#cargando_imagen').width($('#Contenedor').width());
            $('#cargando_imagen').height($('#Contenedor').height());
            $('#cargando_imagen img').css('margin-top', (parseInt($('#Contenedor').height())/2)+'px');
            $('div[id^="cargando_"]').show();
        } else {
            $('div[id^="cargando_"]').hide();
        };
    },
    // ---------------------------------------------------------------
    toggleImg: function (id, forceoff) {
        var src = $('#'+id).find('img').attr('src');
        var force = ((typeof forceoff !== 'undefined') ? true : false);
        if (src.match(/.*_of/gi) && force === false) {
           $('#'+id).find('img').attr('src', src.replace('_of', '_on'));
        } else {
            $('#'+id).find('img').attr('src', src.replace('_on', '_of'));
        };
    },
    // ---------------------------------------------------------------
    _procesarParametros: function(data) {
        var arr = data.split(',');
        var params = new Array();
        for (dato in arr) {
            var arr_tmp = (arr[dato]).split(':');
            params[arr_tmp[0]] = arr_tmp[1];
        };
        return params;
    },
    // ---------------------------------------------------------------
    _enviarAjax: function(chg) {
        var change_image_path = (typeof chg !== 'undefined' ? chg : true);
        $.ajax({
            url:        '/' + DIR_CGI_CPAN + '/prontus_imag_guardar.cgi',
            type:       'POST',
            dataType:   'json',
            cache:       false,
            data:       $('#f').serialize(),
            success: function(data) {
                if (data.status == '0') {
                    alert(data.msg);
                    ImgEdit._toggleCargando();
                } else {
                    var params = ImgEdit._procesarParametros(data.msg);
                    if (change_image_path === true) {
                        $('#image_path').val(params['url']);
                    }
                    ImgEdit.init(params['w'], params['h']);
                    $('#imagenContenedor').attr('src', params['url'] + '?rd=' + (Math.random()*1000));
                    setTimeout("ImgEdit._toggleCargando()", 100);
                    if (!$('#msgbox').is(':visible')) {
                        $('#msgbox').fadeIn('fast');
                        //~ clearInterval(ImgEdit.msgboxInterval); // Para evitar que el mensaje se vuelva loco si el usuario hace muchas acciones rapidamente.
                        //~ ImgEdit.msgboxInterval = setTimeout("ImgEdit._hidemsgbox()", 3500);
                    };
                };
            },
            error: function() {
                alert('Ocurrió un error al procesar la imagen, inténtalo nuevamente.');
                ImgEdit.init(ImgEdit.img_w, ImgEdit.img_h);
                ImgEdit._toggleCargando();
            }
        });
    },
    _hidemsgbox: function () {
        $('#msgbox').fadeOut('slow');
    }
};
