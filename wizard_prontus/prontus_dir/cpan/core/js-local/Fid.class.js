
// -----------------------------------------
var Fid = {
    friendlyVer: 1,

    showDragDrop: false,
    ishttps: false,

    objFormFid: '', // se setea en el doc. ready
    isGecko: navigator.userAgent.indexOf('Gecko') !== -1,
    isMac: navigator.userAgent.indexOf('Macintosh') !== -1,
    animationSlideSpeed: 500,

    waitingProntusForm: 0,
    tooltipId: null,
    tooltipTime: 800,

    init: function() {
        // Muestra los elementos con class hide-new-artic, cuando el artículo no es nuevo
        if(mainFidJs.TS !== '') {
            $('.hide-new-artic').show();
        }

        // Para la información del Artículo
        $('#link_info_artic').click(function() {
            $.fn.colorbox({
                open: true,
                href: '#info_artic',
                inline: true,
                width: 720,
                height: 300,
                opacity: 0.8

            });
        });

        // Para las fechas de las opciones (publicacion y expiracion)
        $.datepicker.setDefaults($.datepicker.regional.es);
        $('.opciones .fecha').datepicker({
            dateFormat: 'dd/mm/yy',
            buttonImage: '/'+mainFidJs.PRONTUS_ID+'/cpan/core/imag/boto/calendar-s.gif',
            buttonImageOnly: true,
            buttonText: 'Mostrar calendario',
            showOn: 'both'
        });

        // Para manejar los Fold de las opciones
        $('.rotulo .flecha span').click(function() {
            var div;
            var alto;
            if($(this).hasClass('opened')) {
                $(this).removeClass('opened').addClass('closed');
                div = $(this).parent().parent().next();
                alto = $(div).height();
                $(div).slideUp(Fid.animationSlideSpeed);
                $('#scroll-banco').animate({height: '+=' + alto}, Fid.animationSlideSpeed);
            } else {
                $(this).removeClass('closed').addClass('opened');
                div = $(this).parent().parent().next();
                alto = $(div).height();
                $('#scroll-banco').animate({height: '-=' + alto}, Fid.animationSlideSpeed);
                $(this).parent().parent().next().slideDown(Fid.animationSlideSpeed);
            }
            return false;
        });

        // Propaga el nombre del form ppal del fid
        Fid.objFormFid = document._mainFidForm;
        Fechas.objFormFid = document._mainFidForm;
        CombosTax.objFormFid = document._mainFidForm;

        // LLena campos fecha
        Fechas.fillfechapshrt();
        Fechas.fillHora();
        $('#div-fechas').show();

        // Taxonomia
        CombosTax.generaTemas(1, mainFidJs.ID_TEMA_SELECTED[0]);
        CombosTax.generaTemas(2, mainFidJs.ID_TEMA_SELECTED[1]);
        CombosTax.generaTemas(3, mainFidJs.ID_TEMA_SELECTED[2]);

        CombosTax.generaSubtemas(1, mainFidJs.ID_SUBTEMA_SELECTED[0]);
        CombosTax.generaSubtemas(2, mainFidJs.ID_SUBTEMA_SELECTED[1]);
        CombosTax.generaSubtemas(3, mainFidJs.ID_SUBTEMA_SELECTED[2]);

        // Para Tabs
        $(".tabs").idTabs(mainFidJs.CURR_BODY, ":grouped", function(id,list,set){
            Fid.showBody(id);
            $('#_curr_body').val(id.substring(1));
        });
        // Para Tabs Alternativos
        $(".tabs-alt").idTabs(0);

        // Upload masivo de imagenes
        $('#uploadcomplete').hide();

        /* Verificar si d&d es compatible con el browser. */
        var userAgent = navigator.userAgent.toString().toLowerCase();
        jQuery.browser.version = parseInt(jQuery.browser.version);
        if (jQuery.browser.mozilla && jQuery.browser.version >= 4) { // Firefox 4+
            Fid.showDragDrop = true;
            $('.ishttps').hide();

        } else if (jQuery.browser.webkit) {
            if (userAgent.indexOf('safari') != -1 && userAgent.indexOf('windows') == -1) { // Safari en MAC.
                if (jQuery.browser.version >= 5) {
                    Fid.showDragDrop = true;
                }
            } else if (userAgent.indexOf('chrome') != -1) { // Chrome 7+
                if (jQuery.browser.version >= 7) {
                    Fid.showDragDrop = true;
                }
            }
        }

        /* Mostrar drag & drop siempre y cuando este soportado. */
        if (Fid.showDragDrop) {
            // Iniciar upload Drag & Drop
            $('#uploadNormal').hide();
            $('#uploadDragDrop').show();
            $('#uploadUploadify').show();
            $('#DragDropAndTradicional').show();

            $('#fileInputDD').fileupload({
                dataType: 'text',
                url: '/' + mainFidJs.DIR_CGI_PUBLIC + '/prontus_art_upfoto_dd.cgi',
                dropZone: $('#dropZone'),
                formData: { prontus_id: mainFidJs.PRONTUS_ID },
                done: function (e, data) {
                    var arrResp = [];
                    var response = data.result
                    if (response == '0') {
                        $('#imagenescargadas').append('<div class="prontus-imagenescargadas">' +
                                '<div class="img-error">Imagen con errores</div>' +
                                '</div>');

                    } else if (response != '') {
                        arrResp = response.split(",");
                        var idFoto = arrResp[0];
                        var wFoto = arrResp[1];
                        var hFoto = arrResp[2];
                        var relPath = arrResp[3];
                        var nomFile = arrResp[4];
                        var realNomFile = arrResp[5];
                        var labelSize = '<br/><span class="ST">(' + wFoto + ' x ' + hFoto + ')</span>';
                        if (wFoto > 100) {
                            wFoto = 100;
                        }

                        $('#imagenescargadas').append('<div class="prontus-imagenescargadas">' +
                                '<div>' + realNomFile + labelSize + '</div>' +
                                '<img src="' + relPath + '" id="' + idFoto  + '">' +
                                '</div>' +
                                '<input type="hidden" name="_fotoreal" value="' + realNomFile + '">' +
                                '<input type="hidden" name="_fotobatch' + nomFile + '" value="' + relPath + '">');
                    }
                },
                progressall: function (e, data) {
                    var progress = parseInt(data.loaded / data.total * 100, 10);
                    $('#uploadProgressBar').css('width', progress + '%');
                    $('#uploadProgressPercent').text(progress+'%');
                },
                stop: function (e) {
                    $('#uploadProgressBar').css('width', '100%');
                    $('#uploadProgressPercent').text('100%');
                    $('#fileInputDD').fileupload('disable');
                    $('#dropZone').css('cursor', 'not-allowed');
                    setTimeout(function () {
                        $('#uploadProgressContainer').hide();
                        $('#uploadcomplete').show();
                        Fid.submitir('Guardar', '_self');
                    }, 1000);
                },
                drop: function (e, data) {
                    /* Validar extensiones de archivo. */
                    var fail = false;
                    $.each(data.files, function (index, file) {
                        var ext = (file.name).split('.').pop().toLowerCase();
                        if ($.inArray(ext, ['gif','png','jpg','jpeg']) == -1) {
                            alert("El archivo [" + file.name + "] es inválido.\nLos archivos permitidos son imágenes gif, png, jpg o jpeg.");
                            fail = true;
                            return false; /* break. */
                        }
                    });

                    if (fail) {
                        return false; /* al retornar false, se detiene la ejecución del plugin. */
                    }

                    $('#uploadProgress').show();
                    $('#uploadUploadify').hide();
                }
            });
        }

        Fid.setGUIProcesando(false);

        // Muestra por lo menos un body
        if($('.cabecera:visible').size() < 1) {
            $('.tabs a:first').trigger('click');
        }

        // Para los input:file
        $('.upload input:file,.ipad-mult input:file').filestyle({
            image: "/" + mainFidJs.PRONTUS_ID + "/cpan/core/imag/boto/examinar.gif",
            imageheight : 22,
            imagewidth : 82,
            width : 240
        });

        // Para el copiar al Clipboard
        if (jQuery.browser.msie) { // para internet explorer
            if (jQuery.browser.flash) { // navegador tiene flash
                Fid.instalaClipboardFlash();
            } else if (Admin.clipboardHtml5) { // navegador soporta api html5
                Fid.instalaClipboardHtml5();
            } else { // no se puede habilitar funcionalidad de clipboard
            $('#copy-artic-url, #copy-artic-ext').remove();
        }
        } else if (Admin.clipboardHtml5) { // navegador soporta api html5
            Fid.instalaClipboardHtml5();
        } else if (jQuery.browser.flash) { // navegador tiene flash
            Fid.instalaClipboardFlash();
        } else { // no se puede habilitar funcionalidad de clipboard
            $('#copy-artic-url, #copy-artic-ext').remove();
        }

        // Codigo para soporte de flash general
        if(!jQuery.browser.flash) {
            $('.browser-comun').not('.browser-noflash').remove();
            $('#uploadUploadify').remove();
            if (Fid.showDragDrop) {
                $('.browser-noflash').remove();
            }
        } else {
            $('.browser-comun').not('.browser-normal').remove();

            /* Uploadify */
            var cgiuploadify = '/' + mainFidJs.DIR_CGI_PUBLIC + '/prontus_art_upfoto.cgi';

            $('#fileInput').uploadify({
                //debug:          true,
                removeCompleted: false,
                buttonText:     'Examinar...',
                swf:            '/' + mainFidJs.PRONTUS_ID + '/cpan/core/js-local/uploadify/uploadify.swf',
                auto:           true,
                multi:          true,
                queueSizeLimit: 30,
                uploader:       cgiuploadify,
                fileSizeLimit:  0,
                fileTypeDesc:   'Image Files',
                fileTypeExts:   '*.jpg;*.jpeg;*.gif;*.png',
                uploadLimit:    100,
                formData: {
                    "prontus_id":   mainFidJs.PRONTUS_ID,
                    "sdata":        mainFidJs.SDATA
                },
                'onQueueComplete':  function(queueData) {
                    $('#uploadcomplete').show();
                    setTimeout(function() {
                        Fid.submitir('Guardar', '_self');
                    }, 1500);
                },
                'onUploadSuccess': function(fileObj, data, response) {
                    if (response === false) {
                        alert( 'No fue posible subir correctamente la imagen [' + fileObj.name + ']');
                        return true;
                    } else {
                        var arrResp = [];
                        arrResp = data.split(","); // $idFoto,$wfoto,$hfoto,$rel_dst_path,$nomfile,$nomReal
                        var idFoto = arrResp[0];
                        var wFoto = arrResp[1];
                        var hFoto = arrResp[2];
                        var relPath = arrResp[3];
                        var nomFile = arrResp[4];
                        var nomReal = arrResp[5];
                        var labelSize = '<br/><span class="ST">(' + wFoto + ' x ' + hFoto + ')</span>';
                        if (wFoto > 100) {
                            wFoto = 100;
                        }

                        $('#imagenescargadas').append('<div class="item-uploaded">' +
                                '<div>' + fileObj.name + labelSize + '</div>' +
                                '<img src="' + relPath + '" id="' + idFoto  + '" width="' + wFoto + '">' +
                                '<input type="hidden" name="_fotobatch' + nomFile + '" value="' + relPath + '">' +
                                '<input type="hidden" name="_fotoreal" value="' + nomReal + '">' +
                                '</div>');
                        return true;
                    }
                },
                'onUploadError': function(fileObj, errorCode, errorMsg, errorString) {
                    alert( '[' + errorMsg + '] No fue posible subir la imagen [' + fileObj.name + ']');
                    return true;
                },
                'onDialogOpen': function() {
                    // Al subir imagenes por este metodo y si esta activado d&d, deshabilitarlo
                    if (Fid.showDragDrop) {
                        $('#fileInputDD').fileupload('disable');
                        $('#dropZone').css('cursor', 'not-allowed');
                    }
                }
            }, {preserve_relative_urls: true});
            /* /Uploadify */

            // El uploadify no funciona en Firefox con https
            if (jQuery.browser.mozilla && Fid.ishttps) {
                $('#uploadUploadify').hide();
            }
        }

        // Para el drag and drop de Fotofijas en Chrome de Mac
        Fid.addDragImagenes();

        // Para la edicion de friendly v4
        Fid.iniciaSlug();
    },

    instalaClipboardHtml5: function() {
        var clipboard = new Clipboard(document.getElementById('copy-artic-int'),{
                text: function(trigger) {
                    return  $('#copy-artic-url').attr('href');
                }
            });
        clipboard.on('success', function(e) {
            Fid.showTooltipCopiar(e.trigger.offsetLeft, e.trigger.offsetTop);
        });
    },

    instalaClipboardFlash: function() {
        ZeroClipboard.setMoviePath('/'+Admin.prontus_id+'/cpan/core/js-local/zeroclipboard/ZeroClipboard.swf');
        var clip = new ZeroClipboard.Client();
        clip.setHandCursor(true);
        clip.setCSSEffects(true);
        clip.addEventListener('mouseDown', function (client, text) {
            var theUrl = $('#copy-artic-url').attr('href');
            clip.setText(theUrl);
            Fid.showTooltipCopiar(client.domElement.offsetLeft, client.domElement.offsetTop);
            return true;
        });
        clip.glue('copy-artic-int', 'copy-artic-ext', {position:'relative', left:'0', top:'0'});
    },

    // -------------------------------------------------------------------------
    showTooltipCopiar: function(posx, posy) {
        $('#tooltip-copiar').stop().hide().css({left:posx-70, top:posy-30}).fadeIn(400, function() {
            $(this).css('opacity', '1');
            clearTimeout(Fid.tooltipId);
            Fid.tooltipId = setTimeout(function() {
                $('#tooltip-copiar').fadeOut(500);
            }, Fid.tooltipTime);
        });
    },

    // -----------------------------------------
    // Esconde div de upload mmultiple
    hideExternalBody: function(){
        $('.cabecera').hide();
    },

    // -----------------------------------------
    //Muestra el contenido de un div para el div con valor 'thediv'
    showBody: function(thediv) {
        $('#banco-img').fadeIn(300);
        $('.cabecera').hide();
        $(thediv).show();
        $('.tabs a').removeClass('selected');
        $('.tabs a[href="'+thediv+'"]').addClass('selected');
        Fid.activarFotosFijas();

        // se destruyen los drop asociados a los vtxt
        FotoFija.destroyDroppableVTXT();

        // Se muestran / ocultan los botones de publicar foto
        if($(thediv).find('[id^="FOTOFIJA_"]').size() > 0) {
            $("#banco-img .botonera .publicar").show();
            FotoFija.initDraggableBanco();
            // se inicia drop para vtxt, para que puedan existir vtxt
            // y fotos fijas en el mismo tab
            if($(thediv).find('iframe[id^="VTXT_"]').size() > 0) {
                FotoFija.initDroppableVTXT(thediv);
            }
        } else {
            $("#banco-img .botonera .publicar").hide();
            FotoFija.destroyDraggableBanco();
        }

        // Para la transcodificación
        if(typeof Transcoding !== 'undefined') {
            Transcoding.init(thediv);
        }
    },

    // -----------------------------------------
    // Deja seteado el flag de https
    setHttps: function() {
        Fid.ishttps = true;
    },

    // -----------------------------------------
    //Obtiene el editor html
    localGetHTML: function(visualEditor, idEditor) {
        var html = '';
        switch (visualEditor._editMode) {
            case "wysiwyg":
                html = frames[idEditor].contentWindow.document.body.innerHTML;
                break;
            case "textmode":

                html = visualEditor._textArea.value;
                break;
        }
        return html;
    },

    // -----------------------------------------
    asignarFotoFija: function(idFoto) {
        FotoFija.actions.assignFoto(idFoto);
    },

    // -----------------------------------------
    //Elimina una foto Fija
    borraFotoFija: function(lafoto) { // es un iframe
        var esta_foto = document.getElementById(lafoto);
        esta_foto.contentWindow.document.body.innerHTML = '&nbsp;';
        if (Fid.isGecko) {
            esta_foto.contentDocument.designMode = "on"; // restaura este att. q se pierde al borrar.
        }
        Fid.objFormFid[lafoto].value = "";

    },

    // -----------------------------------------
    //Muestra una foto Fija
    showFotoFija: function(urlFoto) { // es un iframe
        if(urlFoto !== '') {
            $.fn.colorbox({
                    transition: 'elastic',
                    scrolling: true,
                    open: true,
                    href: urlFoto,
                    maxWidth: '90%',
                    maxHeight: '90%',
                    scalePhotos: true,
                    opacity: 0.8
            });
        }
    },

    // -----------------------------------------
    // Recorre los divs, detecta los que contienen fotos y los asigna a hiddens del mismo nombre.
    guardaFotosFijas: function() {

        var wfoto = '';
        var hfoto = '';
        var i;
        $('iframe:[id^=FOTOFIJA]').each(function(){
            var iframe = this.contentWindow.document.body.innerHTML;
            var imag = $(this).contents().find("img");
            for (i = 0; i < imag.length; i++){
                wfoto = $(imag[i]).attr("width");
                if (!wfoto){
                    wfoto = $(imag[i]).attr("width");
                }
                Fid.objFormFid['_W' + this.id].value = wfoto;
                hfoto =  $(imag[i]).attr("width");
                if (!hfoto){
                    hfoto =  $(imag[i]).attr("width");
                }
                Fid.objFormFid['_W' + this.id].value = hfoto;
            }
            //rescata Ruta de la imagen
            var nom_img;
            var expr = /src="([^"]+?)"/;
            var ret = expr.exec(iframe);
            if (ret !== null) {
                nom_img = RegExp.$1;
            } else {
                nom_img = '';
            }
            Fid.objFormFid[this.id].value = nom_img;
        });
    },

    // -----------------------------------------
    procesarTags: function() {
        var tags4fid = $('#_tags4fid').val();
        if(typeof tags4fid === 'undefined') {
            return;
        }
        var _tags = '';
        if(tags4fid !== '') {
            var arr = tags4fid.split(',');
            var x;
            for(x in arr) {
                if(arr[x] !== '') {
                    var arr2 = arr[x].split('|');
                    if(arr2.length === 2) {
                        _tags = _tags + arr2[0] + ',';
                    }
                }
            }
        }
        if(_tags.length > 0) {
            _tags = _tags.substr(0, _tags.length-1);
        }
        $('#_tags').val(_tags);
    },

    // -----------------------------------------
    clearReplaceFoto: function() {
        var i;
        var tot = Fid.objFormFid._REPLACE_FOTO.length;
        for (i = 0; i < tot; i++) {
            if (Fid.objFormFid._REPLACE_FOTO[i].value === '') {
                Fid.objFormFid._REPLACE_FOTO[i].checked = true;
            }
        }
    },

    // -----------------------------------------
    // setea atributos y contenido de los contenedores de fotos fijas
    // excepto su capacidad de edicion, porque no resulta cuando esta hidden.
    // Lo anterior se hace al hacer click en los tabs
    initFotoFija: function(iframe, content) {
        if (content === '') {
            content = '&nbsp;';
        }
        iframe.contentWindow.document.body.innerHTML = content;
        iframe.contentWindow.document.body.style.border = "none";
        iframe.contentWindow.document.body.style.margin = "2px";
        iframe.contentWindow.document.body.style.height = "100%";

        if (Fid.isGecko) {
            iframe.contentWindow.document.body.style.overflow = "hidden";
        } else {
            iframe.contentWindow.document.body.scroll = "no";
        }
    },

    // -----------------------------------------
    cancel_event: function(e) {
        if (Fid.isGecko) {
            e.preventDefault();
        } else {
            e.returnValue = false;
            e.cancelBubble = true;
        }
    },


    // -----------------------------------------
    // Activa el handler de Drag&Drop de fotos para Chrome en Mac
    addDragImagenes: function() {
        if (Fid.isGecko && Fid.isMac) {
            var elems = document.getElementsByTagName("img");
            var matchClass = 'fotodrag';
            for (i in elems) {
                if((' ' + elems[i].className + ' ').indexOf(' ' + matchClass + ' ') > -1) {
                    elems[i].addEventListener("dragstart", function(_event) {
                        _event.dataTransfer.setData('imagen', this.outerHTML);
                    }, false);
                }
            }
        }
    },

    // -----------------------------------------
    //Activa los controles de Fotofija del Fid
    activarFotosFijas: function() {
        $('iframe[id^=FOTOFIJA]').each(function(){
            try {
                var bodyiframe = this.contentWindow.document.body;
                if (Fid.isGecko) {
                    // A contar de Firefox 11
                    // this.contentDocument.designMode = 'on';
                    // this.contentWindow.document.contentEditable = true;
                    if (Fid.isMac) {
                        bodyiframe.contentEditable = true;
                        bodyiframe.addEventListener("click", Fid.cancel_event, true );
                        bodyiframe.addEventListener("keydown", Fid.cancel_event, true );
                        bodyiframe.addEventListener("dragover", function(_event) {
                            bodyiframe.focus();
                            _event.stopPropagation();
                            _event.preventDefault();

                        }, false);
                        bodyiframe.addEventListener("drop", function(_event) {
                            var imagen = _event.dataTransfer.getData('imagen');
                            if(imagen) {
                                _event.stopPropagation();
                                _event.preventDefault();
                                _event.currentTarget.innerHTML = imagen;
                            }
                        }, false);
                    } else {
                        bodyiframe.contentEditable = true;
                        bodyiframe.addEventListener("onclick", Fid.cancel_event);
                        bodyiframe.addEventListener("onkeydown", Fid.cancel_event);
                        bodyiframe.addEventListener("dragover", function(_event) {
                            bodyiframe.focus();
                        }, false);
                    }
                } else {
                    bodyiframe.contentEditable = true;
                    bodyiframe.attachEvent("onclick", Fid.cancel_event);
                    bodyiframe.attachEvent("onkeydown", Fid.cancel_event);
                }
            } catch(e) {
                // Al primer error retorna de inmediato
                return;
                // No funciona cuando el contenedor esta oculto
            }
        });
    },

    // -----------------------------------------
    deleteFotoBanco: function(idThumb) { // true | false. De momento es invocado por el js generado por prontus_art_ficha.cgi

        var idButtonDel = 'borrar' + idThumb;
        /*
        alert('idButtonDel:' + idButtonDel);
        alert('idThumb:' + idThumb);
        alert('signal:' + signal);
        */
        var objInput = Fid.objFormFid['_BORR_'+idThumb];
        if (objInput.checked) {
            objInput.checked = false;
            $('#' + idButtonDel).attr({alt: 'Click para borrar', title: 'Click para borrar'});
            $('#' + idThumb).attr({src: $('#' + idThumb).attr('realsrc'), width: $('#' + idThumb).attr('realwidth')});
            $('#' + idThumb).removeAttr('realsrc');
            $('#' + idThumb).removeAttr('realwidth');

        } else {
            objInput.checked = true;
            $('#' + idButtonDel).attr({alt: 'Click para cancelar eliminación', title: 'Click para cancelar eliminación'});

            // guarda ruta y ancho original
            $('#' + idThumb).attr('realsrc', $('#' + idThumb).attr('src'));
            $('#' + idThumb).attr('realwidth', $('#' + idThumb).attr('width'));

            // detecta ruta de iconos
            var srcButtonDel = $('#' + idButtonDel).attr('src');
            var relpathNoImg = srcButtonDel.replace(/\w+\.\w+$/, 'noimg2.png');

            // cambia el src y ancho del thumb por una  de icono 'borrado'
            $('#' + idThumb).attr('src', relpathNoImg);
            $('#' + idThumb).attr('width', 80);
        }
    },

    // -------------------------------------------------------------------------
    editFotoBanco: function(nameimg) {
        var url = 'prontus_imag_ficha.cgi?path_conf='+Admin.path_conf+'&ts='+mainFidJs.TS+'&foto='+nameimg;
        var nameWin = 'EditImg' + nameimg;
        Utiles.subWin(url, nameWin, 1000, 600);
    },

    // -------------------------------------------------------------------------
    verArtActual: function(obj, ts) {
        var url = $(obj).attr('href');
        window.open(url);
    },

    // -------------------------------------------------------------------------
    copyArtic: function(ts) {

        if(! confirm("Este artículo será copiado.\nSe perderán los datos que no hayas guardado.\n¿Deseas continuar?")) {
            return;
        }

        if(FidConfig.cargando) {
            alert(FidConfig.msgCargando);
            return false;
        }

        Fid.setGUIProcesando(true);
        var actionURL = 'prontus_art_copy.cgi';
        $.ajax({
            type: "GET",
            dataType: 'json',
            url: actionURL,
            data: {
                _path_conf: Admin.path_conf,
                _ts: ts
            },
            success: function (resp, textStatus, jqXHR) {
                if (resp.status == '1') {
                    window.location.href = 'prontus_art_ficha.cgi?_path_conf='+Admin.path_conf+'&_file='+resp.file+'&_fid='+resp.fid+'&fotosvtxt=/1/2/3/4';
                } else {
                    Fid.setGUIProcesando(false);
                    alert(resp.msg);
                }
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                SubmitForm.handleError(actionURL, XMLHttpRequest, textStatus, errorThrown);
                Fid.setGUIProcesando(false);
            }
        });
    },

    // -------------------------------------------------------------------------
    abrirMultimedia: function() {

        var ancho = 1060;
        var alto = 560;
        var posx = 50;
        var posy = 50;
        if(screen.width) {
            if(screen.width <= ancho) {
                ancho = screen.width;
                alto = ancho * 0.56;
                if(alto >= screen.height) {
                    alto = screen.height;
                }
            }
            posx = (screen.width - ancho)/2;
            posy = (screen.height - alto)/2;
        }

        var url = 'dam/prontus_dam_search.cgi?path_conf='+Admin.path_conf+'&asset_search_type=foto&asset_search_popup=1';
        Utiles.subWin(url, 'multimedia', ancho, alto, posx, posy);
    },

    // --------------------------------------------------------
    //Funcion para inicializar el tab  que se mostrara  cuando cambiemos de FID
    // Se invoca desde JS from  prontus_art_ficha.cgi
    onSetTab: function(){
        $('#_curr_body').val('body1');
    },

    // -------------------------------------------------------------------------
    // Validacion y submit del formulario.
    submitir: function(bot_press, target) {
        if(FidConfig.cargando) {
            alert(FidConfig.msgCargando);
            return false;
        }

        Fid.setGUIProcesando(true);

        $('#_accion').val(bot_press); // save | preview | save_new
        $(Fid.objFormFid).attr('action', 'prontus_art_sbmit.cgi');
        $(Fid.objFormFid).attr('target', target);

        Fechas.fillfechap();
        CombosTax.fillSeccTemStem(); // Taxonomia
        Fid.procesarTags();

        // Para la transcodificacion
        if($('#xcodeInput').val() == 1) {
            var msg = Transcoding.validarVideo();
            if(msg !== '') {
                alert(msg);
                Fid.setGUIProcesando(false);
                return ;
            }
        }

        if (! GaleriaProntus.verificaArchivoCargado()) {
            return false;
        }

        if (GaleriaProntus.pproc_working) {
            if (!confirm(GaleriaProntus.msg_confirm)) {
                return false;
            }
        }

        GaleriaProntus.guardarGaleriaProntus();

        // si friendly 4 esta activada el guardado se hace acá y no se ejecuta el codigo siguiente
        if (Fid.friendlyVer == 4 && (bot_press == 'save' || bot_press == 'save_new')) {
                Fid.validaTitular(bot_press);
                return false;
        }

        // se submite el formulario
        $('#_mainFidForm').trigger('submit');

        if (bot_press == 'preview') {
            Fid.setGUIProcesando(false);
        }
    },
    // -------------------------------------------------------------------------
    // habilita la edicion manual del campo de url
    slugEditable: function(editar) {
        if (editar == true) {
            $('#_custom_slug').val('SI');
            $("#_slug").attr("readonly", false);
            $("#_slug").addClass('active');
        } else {
            $('#_custom_slug').val('NO');
            $("#_slug").attr("readonly", true);
            $("#_slug").removeClass('active');
            Fid.validaTitular('check');
        }
    },
    // -------------------------------------------------------------------------
    // Inicia el valor del slug y comportamiento del fid al cargar el articulo
    iniciaSlug: function() {
        if (Fid.friendlyVer == 4) {
            if ($('#_custom_slug').val() == '' || $('#_slug').val() == '') {
                $('#_custom_slug').val('NO');
                Fid.slugEditable(false);
            } else if ($('#_custom_slug').val() == 'SI') {
                Fid.slugEditable(true);
            }
        }
    },
    // -------------------------------------------------------------------------
    // Valida si la url friendly correspondiente a este articulo ya existe
    // gatilla guardado del articulo si corresponde
    // save y save_new, gatillan guardado, check solo verifica y genera alerta
    validaTitular: function(bot_press) {
        if (Fid.friendlyVer == 4) {
            if (bot_press == 'check-slug' && $('#_custom_slug').val() == 'NO') {
                return false;
            }
            if (bot_press == 'check-titular' && $('#_custom_slug').val() == 'SI') {
                return false;
            }
            $('#url_art_ts').html('');
            $('#url_art_id').html('');
            $('#url_art_titu').html('');
            $('#url_art_editar').attr("href", '#');
            $('#url_art_path').html('');
            $('#url_art_slug').html('');

            var element_id = '#_txt_titular';
            if ($('#_custom_slug').val() == 'SI') {
                element_id = '#_slug';
            }

            $.ajax({
                type: 'POST',
                url: 'prontus_art_check_url.cgi',
                data: { _prontus_id: mainFidJs.PRONTUS_ID,
                        _txt_titular: $(element_id).val(),
                        _ts: mainFidJs.TS,
                        _path_conf: $('[name=_path_conf]').val()
                    },
                dataType: 'json',
                success: function (data) {
                        if (data.status == 'OK') {
                            $('#_slug').val(data.uri_titular);
                            Fid.alertaTitular();
                            if (bot_press == 'save' || bot_press == 'save_new') {
                                // se submite el formulario
                                $('#_mainFidForm').trigger('submit');
                            }
                        } else {
                            if (typeof data.ts === 'undefined' || data.ts == '') {
                                Fid.alertaTitular(data.msg);
                                if ($('#_custom_slug').val() == 'SI') {
                                    $('#_slug').focus();
                                } else {
                                    $('#_txt_titular').focus();
                                }
                            } else {
                                $('#url_art_ts').html(data.ts);
                                $('#url_art_id').html(data.id);
                                $('#url_art_titu').html(data.titular);
                                var link = 'prontus_art_ficha.cgi?_path_conf='+Admin.path_conf+'&_file='+data.ts + '.' + data.ext+'&_fid='+data.fid+'&fotosvtxt=/1/2/3/4';
                                $('#url_art_editar').attr("href", link);
                                var path = '/' + mainFidJs.PRONTUS_ID + '/site/artic/' + data.ts.substr(0,8) + '/pags/' + data.ts + '.' + data.ext;
                                $('#url_art_path').html(path);
                                $('#url_art_slug').html(data.uri_titular);
                                $.fn.colorbox({
                                    open: true,
                                    href: '#info_url_conflict',
                                    inline: true,
                                    width: 720,
                                    height: 230,
                                    opacity: 0.8,
                                    onClosed:function(){
                                        if ($('#_custom_slug').val() == 'SI') {
                                            $('#_slug').focus();
                                        } else {
                                            $('#_txt_titular').focus();
                                        }
                                    }
                                });
                            }
                            Fid.setGUIProcesando(false);
                        }
                    }
            });
        }

        return false;
    },

    // -------------------------------------------------------------------------
    // Funcion usada para vaciar el titular en caso que sea "sin titulo \d+"
    limpiaTitular: function(elemento) {
        if (/^Sin título \d+$/.test($(elemento).val())) {
            $(elemento).val('');
        }
    },
    // -------------------------------------------------------------------------
    // alerta para indicar que el titular o slug estan incorrectos
    alertaTitular: function(msg) {
        if(typeof msg !== 'undefined' && msg !== '') {
            var str = '<img src="/'+Admin.prontus_id+'/cpan/core/imag/boto/msg-error.png" width="24" height="24" alt="Error en titular o slug" title="Error en titular o slug" /> <span>' + msg + '</span>';
            $('#slug-alert').html(str).fadeIn();
        } else {
            $('#slug-alert').hide();
        }
    },
    // -------------------------------------------------------------------------
    // Funcion usada para abrir el editor de un articulo en otra ventana
    abrirEditor: function(elemento) {
        window.open(elemento.attr('href'));
    },

    // -------------------------------------------------------------------------
    //Funcion usada en los formularios para eliminar archivos de respaldos
    eliminarArchivo: function() {
        if (confirm(FidConfig.msgConfirmRemoveBackup)) {
            var config = {
                formSelector: '#backupDatos'
            };
            var opts = {
                success:   function(json, statusText) {   // post-submit callback
                    if (json.status == 0) {
                        alert(unescape(json.msg));
                        parent.Fid.listadoDatos();
                    } else {
                        if (json.msg !== '') {
                            alert(unescape(json.msg));
                            parent.$('#cboxClose').trigger('click');
                        }
                    }
                    return false;
                } // success
            };

            SubmitForm.submitGenericAjax(config, opts);
        }
    },

    // -------------------------------------------------------------------------
    //Funcion usada en los formularios para descargar el archivo de respaldo
    generarArchivoForm: function() {
        $('#msg-link').hide();
        $('#msg-error').hide();
        if (Fid.waitingProntusForm == 0) {
            var actionURL = "prontus_form_download.cgi?" + $('#backupDatos').serialize();
            $.ajax({
                type: "GET",
                dataType: 'json',
                url: actionURL,
                cache: false,
                success: function (resp, textStatus, jqXHR) {
                    if (resp.status == '1') {
                        $('#msg-loading').show();
                        Fid.waitingProntusForm = setTimeout(function(){ Fid.chequeaDescargaForm(); }, 5000);
                    } else {
                        $('#msg-error').show();
                        $('#error-data').html("Ha ocurrido un error al procesar la solicitud: " + resp.msg);
                    }
                },
                error: function(XMLHttpRequest, textStatus, errorThrown) {
                    $('#msg-error').show();
                    $('#error-data').html("Ha ocurrido un error al procesar la solicitud");
                }
            });
        }
    },

    chequeaDescargaForm: function() {
        Fid.waitingProntusForm = 0;
        var actionURL = '/' + mainFidJs.PRONTUS_ID + '/cpan/procs/form/' + mainFidJs.TS + '/status.json';
        $.ajax({
            type: "GET",
            dataType: 'json',
            url: actionURL,
            cache: false,
            success: function (resp, textStatus, jqXHR) {
                if (resp.status == '1') {
                    Fid.waitingProntusForm = setTimeout(function(){ Fid.chequeaDescargaForm(); }, 5000);
                } else if (resp.status == '0') {
                    $('#msg-link').show();
                    $('#msg-loading').hide();
                    $('#link-csv')[0].href = resp.path;
                } else {
                    $('#msg-error').show();
                    $('#error-data').html("Ha ocurrido un error al procesar la solicitud: "  + resp.msg);
                    $('#msg-link').show();
                    $('#msg-loading').hide();
                }
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                $('#msg-error').show();
                $('#error-data').html("Ha ocurrido un error al procesar la solicitud.");
                $('#msg-link').hide();
                $('#msg-loading').hide();
            }
        });
    },

    // -------------------------------------------------------------------------
    //Funcion usada en los formularios para abrir el administrador de archivos adjuntos
    listadoDatos: function() {
        var url = 'prontus_form_list.cgi?_prontus_id=' + mainFidJs.PRONTUS_ID +  '&_ts=' + mainFidJs.TS;
        $.fn.colorbox({
                open: true,
                href: url,
                width: 1010,
                height: 600,
                maxWidth: '98%',
                maxHeight: '98%',
                opacity: 0.8,
                scroll: true,
                iframe: true
        });
    },

    // -------------------------------------------------------------------------
    // Bloquea controles mientras se procesa
    setGUIProcesando: function(signal) {
        if (signal) {
            $('.botones a').hide();
            $('.botones .loading-action').fadeIn();
        } else {
            $('.botones .loading-action').hide();
            $('.botones a').fadeIn();
        }
    },

    // -------------------------------------------------------------------------
    // Bloquea controles mientras se procesa
    actualizaFechaHora: function(tipo) {

        var fecha;
        var hora;

        if(tipo === 'pub') {
            fecha = $('input[name="_FECHAPSHRT"]');
            hora  = $('input[name="_HORAP"]');
        } else if(tipo === 'exp') {
            fecha = $('input[name="_FECHAESHRT"]');
            hora  = $('input[name="_HORAE"]');
        } else {
            alert('tipo desconocido: ' + tipo);
            return;
        }

        var now = new Date();
        var normaliza2Digitos = function(val) {
            if(val < 10 && val >= 0) {
                val = '0'+val;
            }
            return val;
        };
        if(hora) {
            var minu = now.getMinutes();
            var hors = now.getHours();
            hora.val(normaliza2Digitos(hors)+':'+normaliza2Digitos(minu));
        }
        if(fecha) {
            var dia = now.getDate();
            var mes = now.getMonth() + 1;
            var anio = now.getYear();
            if (anio < 1000) {
                anio = anio + 1900;
            }
            fecha.val(normaliza2Digitos(dia)+'/'+normaliza2Digitos(mes)+'/'+normaliza2Digitos(anio));
        }
    },

    // -------------------------------------------------------------------------
    // Autochequea los campos indicados por params, separados por coma
    autocheckNewArtic: function(params) {

        if(mainFidJs.TS !== '') {
            return;
        }
        if(typeof params !== 'undefined' && params !== null && params !== '') {
            params = params.replace('"', '');
            params = params.replace('\'', '');
            var arr = params.split(',');
            if(arr !== null) {
                var len = arr.length;
                for(var i = 0; i < len; i++) {
                    var str = arr[i];
                    $('input[name^="'+arr[i]+'"]:checkbox').attr('checked', 'checked');
                }
            }
        }
    },

    // -------------------------------------------------------------------------
    // Muestra las imagenes restantes del banco de imagenes
    verMasImagenes: function() {

        $('.banco-vermas a').hide();
        $('.banco-vermas img').show();
        var theurl = './prontus_art_banco.cgi?_ts='+mainFidJs.TS+'&_path_conf='+Admin.path_conf;
        $('#banco-content').load(theurl, function(responseText, textStatus, XMLHttpRequest) {
            $('.banco-vermas').remove();
            $('#banco-content').slideDown('fast', function() {
                $(this).css('border-top','1px #ccc solid');
                var curr_body = '#' + $('#_curr_body').val();
                if($(curr_body).find('[id^="FOTOFIJA_"]').size() > 0) {
                    $("#banco-content .botonera .publicar").show();
                    FotoFija.initDraggableBanco();
                }
                FotoFija.methods.bindEditorFotos();
                Fid.addDragImagenes();
            });
        });
    },

    // -------------------------------------------------------------------------
    // Hace un ping al servidor para indicar
    pingRecurso: function() {
        if(mainFidJs.TS === '') {
            return;
        }
        Admin.pingRecurso('art', mainFidJs.TS, Fid.pingRecurso);
    },

    // -------------------------------------------------------------------------
    // Abre el XML desde el CPAN
    verXML: function(p, ts) {

        var loc = 'prontus_art_view_xml.cgi?_prontus_id='+p+'&_ts='+ts;
        nom = "verXML"+ts;
        Utiles.subWin(loc, nom, 800, 500, 50, 50);

    }

};
