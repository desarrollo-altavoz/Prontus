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
        imgEditor: false,
        // ---------------------------------------------------------------
        init: function (prontus_id) {
            self = this;
            self.prontus_id = prontus_id;

            self.initDraggableBanco();

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

            self.methods.bindEditorFotos();
        },
        // ---------------------------------------------------------------
        // Inicia drag & drop desde banco de imagenes.
        // ---------------------------------------------------------------
        initDraggableBanco: function () {
            $('#banco-img .foto-icon').draggable({
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
                $('#banco-img .foto-icon').draggable("destroy");
                self.draggableBanco = false;
            }
        },
        // ---------------------------------------------------------------
        // Inicia drag & drop para VTXT
        // ---------------------------------------------------------------
        initDroppableVTXT: function (thediv) {
            $(thediv).find('iframe[id^="VTXT_"]').each(function () {
                var iframe = $(this);
                var id = iframe.attr('id').replace('_ifr', '');
                iframe.droppable({
                    drop: function (e, ui) {
                        // Sobrepasa los limites.
                        if (ui.helper.position().top < (iframe.position().top)) {
                            return false;
                        }
                        tinyMCE.getInstanceById(id).execCommand('mceInsertContent', false, $(ui.helper).html());
                    }
                });
            });
        },
        // ---------------------------------------------------------------
        // Destruye drag & drop para VTXT
        // ---------------------------------------------------------------
        destroyDroppableVTXT: function () {
            $('iframe[id^="VTXT_"].ui-droppable').droppable("destroy");
        },
        // ---------------------------------------------------------------
        // Crea una nueva instancia de un campo de foto.
        // ---------------------------------------------------------------
        newInstance: function (id, maxW, maxH, imgW, imgH) {
            self.foto.init(id, maxW, maxH, imgW, imgH);
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
            },
            // ---------------------------------------------------------------
            // Ver una foto en su tamaño real en un colorbox.
            // ---------------------------------------------------------------
            show: function (id) {
                var imgSrc = $('input[name="FOTOFIJA_' + id + '"]').val();

                if (imgSrc) {
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
            edit: function (id, wfoto, hfoto) {
                var path = $('input[name="FOTOFIJA_' + id + '"]').val();

                if (path) {
                    $.colorbox({
                        iframe: true,
                        href:"/" + DIR_CGI_CPAN + "/prontus_editor_imag.cgi?&_path_conf=" + Admin.path_conf + "&ts=" + mainFidJs.TS + "&relfoto=" + path + "&w=" + wfoto + "&h=" + hfoto + "&active=" + id,
                        innerWidth: 1024,
                        innerHeight: 576
                    });
                }
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
                });
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
            },
            bindEditorFotos: function () {
                $('body').find('.openFotoEditor').off('click').on('click', function () {
                    var nomfoto     = $(this).data("nomfoto");
                    var relfoto     = $(this).data("relfoto");
                    var wfoto       = $(this).data("wfoto");
                    var hfoto       = $(this).data("hfoto");

                    $.colorbox({
                        iframe: true,
                        href:"/" + DIR_CGI_CPAN + "/prontus_editor_imag.cgi?&_path_conf=" + Admin.path_conf + "&ts=" + mainFidJs.TS + "&relfoto=" + relfoto,
                        innerWidth: 1024,
                        innerHeight: 576,
                        onClosed: function () {
                            // Se guarda el FID automaticamente si hay cambios en el editor de fotos.
                            if (self.imgEditor) {
                                Fid.submitir('save', '_self');
                            }
                        }
                    });
                })
            },
            reloadBancoImagenes: function () {
                $('#scroll-banco').empty();

                var theurl = './prontus_art_banco.cgi?_ts=' + mainFidJs.TS + '&_path_conf='+Admin.path_conf + '&_all=1';

                $('#scroll-banco').load(theurl, function(responseText, textStatus, XMLHttpRequest) {
                    FotoFija.initDraggableBanco();
                    FotoFija.methods.bindEditorFotos();
                    Fid.addDragImagenes();

                    var curr_body = '#' + $('#_curr_body').val();
                    if ($(curr_body).find('[id^="FOTOFIJA_"]').size() > 0) {
                        $("#scroll-banco .botonera .publicar").show();
                    }

                    $('#banco-img').find('img.fotodrag').each(function () {
                        var $objSinUsar = $(this).parent().next('.datos-foto').find('.sin-usar');
                        var sinusar = $objSinUsar.text();
                        var fotosrcbanco = $(this).attr('src');

                        $(curr_body).find('[id^="recuadro_FOTOFIJA_"]').each(function () {
                            var fotosrc = $(this).find('img').attr("src");

                            if (fotosrc && fotosrc == fotosrcbanco) {
                                if (sinusar == '(sin usar)') {
                                    $objSinUsar.text('');
                                }
                            }
                        });
                    });
                });
            }
        },
        // ---------------------------------------------------------------
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
                // var editar = 'on';

                self.foto.instances[id] = {
                    id: id,
                    maxW: parseInt(maxW),
                    maxH: parseInt(maxH),
                    imgW: parseInt(imgW),
                    imgH: parseInt(imgH),
                    src: currImgSrc
                };

                if (currImgSrc && currImgSrc != 'javascript:void(0)') {

                    $('div#recuadro_FOTOFIJA_' + id).html('<img src="' + currImgSrc + '" />');
                    self.methods.toggleButtons(id, {lupa:'on',borrar:'on', cuadrar:'on'});
                    self.foto.bindEvents(id);
                    // Para compatibilidad, se agrega al iframe.
                    $('iframe[id="FOTOFIJA_' + id + '"]').contents().find('body').html('<img src="' + currImgSrc + '" />');

                } else {
                    self.methods.toggleButtons(id, {lupa:'off',editar:'off',borrar:'off',cuadrar:'off'});
                    self.foto.instances[id].src = ''; // fix
                }

                $("div#recuadro_FOTOFIJA_" + id).droppable({
                    accept: '.foto-icon',
                    hoverClass: 'ui-state-active',
                    drop: function (event, ui) {
                        var $item   = ui.helper.find('.fotodrag');
                        var imgSrc  = $item.attr('src');
                        var imgW    = $item.attr("data-w");
                        var imgH    = $item.attr("data-h");

                        self.foto.set(id, imgSrc, imgW, imgH);
                    }
                });

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
                    src: ''
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
                // var editar = 'on';

                $('div#recuadro_FOTOFIJA_' + id).html('<img src="' + imgSrc + '" />');
                $('input[name="FOTOFIJA_' + id + '"]').val(imgSrc);
                $('input[name="_WFOTOFIJA_' + id + '"]').val(imgW);
                $('input[name="_HFOTOFIJA_' + id + '"]').val(imgH);

                self.foto.instances[id].src = imgSrc;
                self.foto.instances[id].imgW = parseInt(imgW);
                self.foto.instances[id].imgH = parseInt(imgH);

                // Para compatibilidad, se agrega al iframe.
                $('iframe[id="FOTOFIJA_' + id + '"]').contents().find('body').html('<img src="' + imgSrc + '" />');

                self.methods.toggleButtons(id, {lupa:'on',borrar:'on',cuadrar:'on'});
                self.foto.bindEvents(id);
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
                return '#' + $('#_curr_body').val();
            },
            submitForm: function () {
                Fid.submitir('save', '_self');
            }
        }
    };

    window.FotoFija = FotoFija;
})(this);
