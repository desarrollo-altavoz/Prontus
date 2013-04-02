
// -----------------------------------------
var Fid = {

    objFormFid: '', // se setea en el doc. ready
    isGecko: navigator.userAgent.indexOf('Gecko') !== -1,
    animationSlideSpeed: 500,

    tooltipId: null,
    tooltipTime: 800,
    //iframeVoid: '/cpan/core/imag/bg-iframe.gif',

    init: function() {

        //Admin.prontus_id = mainFidJs.PRONTUS_ID;
        //Fid.iframeVoid = '/' + Admin.prontus_id + Fid.iframeVoid;

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

        // Para lazyLoad
        /*
        $("#ARTFOTOS img[id^='foto_']").lazyload({
            container: $("#ARTFOTOS")
        });
        */

        // Upload masivo de imagenes
        $('#uploadcomplete').hide();


        /* Verificar si d&d es compatible con el browser. */
        var showDragDrop = false;
        var userAgent = navigator.userAgent.toString().toLowerCase();
        jQuery.browser.version = parseInt(jQuery.browser.version);

        if (jQuery.browser.mozilla && jQuery.browser.version >= 4) { // Firefox 4+
            showDragDrop = true;
        } else if (jQuery.browser.webkit) {
            if (userAgent.indexOf('safari') != -1 && userAgent.indexOf('windows') == -1) { // Safari en MAC.
                if (jQuery.browser.version >= 5) {
                    showDragDrop = true;
                }
            } else if (userAgent.indexOf('chrome') != -1) { // Chrome 7+
                if (jQuery.browser.version >= 7) {
                    showDragDrop = true;
                }
            }
        }

        /* Mostrar drag & drop siempre y cuando este soportado. */
        if (showDragDrop) {
            // Iniciar upload Drag & Drop
            $('#uploadNormal').hide();
            $('#uploadDragDrop').show();
            $('#DragDropAndTradicional').show();

            var valoresAdicionales = {
                prontus_id: mainFidJs.PRONTUS_ID
            };

            $('#fileInput').fileupload({
                dataType: 'text',
                url: '/' + mainFidJs.DIR_CGI_PUBLIC + '/prontus_art_upfoto_dd.cgi',
                dropZone: $('#dropZone'),
                formData: valoresAdicionales,
                done: function (e, data) {
                    var arrResp = [];
                    var response = data.result
                    if (response == '0') {
                        $('#imagenescargadas').append('<div style="margin-left:10px;margin-top:16px;width:120px;height:135px;overflow:auto;display:inline;float:left">' +
                                '<div style="color:#FFA500;">Imagen con errores</div>' +
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

                        $('#imagenescargadas').append('<div style="margin-left:10px;margin-top:16px;width:120px;height:135px;overflow:auto;display:inline;float:left">' +
                                '<div>' + realNomFile + labelSize + '</div>' +
                                '<img src="' + relPath + '" id="' + idFoto  + '" width="' + wFoto + '">' +
                                '</div>' +
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
                    $('#fileInput').fileupload('disable');
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
                    $('#fileInput').hide();
                    $('#DragDropAndTradicional').hide();
                    $('#fileInputUploader').hide();
                }
            });
        }

        /* Uploadify */
        $('#fileInput').uploadify({
            'uploader'  : '/' + mainFidJs.PRONTUS_ID + '/cpan/core/js-local/uploadify/uploadify.swf',
            'queueSizeLimit' : 30,

            'buttonText': 'Examinar...',
            'script'    : '/' + mainFidJs.DIR_CGI_PUBLIC + '/prontus_art_upfoto.cgi',
            'fileDesc': 'Image Files',
            'fileExt': '*.jpg;*.jpeg;*.gif;*.png',
            'scriptData' : { "prontus_id": mainFidJs.PRONTUS_ID, "sdata": mainFidJs.SDATA},
            'cancelImg' : '/' + mainFidJs.PRONTUS_ID + '/cpan/core/js-local/uploadify/cancel.png',
            'auto'      : true,
            // 'folder'    : '%%_PRONTUS_ID%%/cpan/procs/uploadify',
            'multi'          : true,
            'onAllComplete'  : function(evt, data) {
                setTimeout(function() {
                    Fid.submitir('Guardar', '_self');
                }, 1500);
                $('#uploadcomplete').show();
            },
            'onComplete'     : function(evt, queueID, fileObj, response, data) {
                // alert(fileObj.filePath);
                // alert(response);
                if (response === false) {
                    alert( 'No fue posible subir correctamente la imagen ' + fileObj.name );
                    //$('#fileInput').uploadifyCancel(queueID);
                    //$('#fileInput').uploadifyUpload();
                    return true;
                } else {
                    var arrResp = [];
                    arrResp = response.split(","); // $idFoto,$wfoto,$hfoto,$rel_dst_path,$nomfile
                    var idFoto = arrResp[0];
                    var wFoto = arrResp[1];
                    var hFoto = arrResp[2];
                    var relPath = arrResp[3];
                    var nomFile = arrResp[4];
                    var labelSize = '<br/><span class="ST">(' + wFoto + ' x ' + hFoto + ')</span>';
                    if (wFoto > 100) {
                        wFoto = 100;
                    }

                    $('#imagenescargadas').append('<div style="margin-left:10px;margin-top:16px;width:120px;height:135px;overflow:auto;display:inline;float:left">' +
                            '<div>' + fileObj.name + labelSize + '</div>' +
                            '<img src="' + relPath + '" id="' + idFoto  + '" width="' + wFoto + '">' +
                            '</div>' +
                            '<input type="hidden" name="_fotobatch' + nomFile + '" value="' + relPath + '">');

                    return true;
                }
            },
            'onError'   :   function( evt, queueID, fileObj, errObj ) {
                alert( 'Error: [' + errObj.type + '] [' + errObj.info + '] No fue posible subir la imagen ' + fileObj.name );
                return true;
            },
            'onOpen'      : function(event,ID,fileObj) {
                /* Al subir imagenes por este metodo y si esta activado d&d, deshabilitarlo.*/
                if (showDragDrop) {
                    $('#fileInput').fileupload('disable');
                    $('#dropZone').css('cursor', 'not-allowed');
                }
            }
        });
        /* /Uploadify */

        Fid.setGUIProcesando(false);

        // Muestra por lo menos un body
        if($('.cabecera:visible').size() < 1) {
            $('.tabs a:first').trigger('click');
        }

        // Codigo para soporte de flash
        if(!jQuery.browser.flash) {
            $('.browser-comun').not('.browser-noflash').remove();
            $('#copy-artic-url, #copy-artic-ext').remove();

        } else {

            $('.browser-comun').not('.browser-normal').remove();

            // Para los input:file
            $(".upload input:file").filestyle({
                image: "/" + mainFidJs.PRONTUS_ID + "/cpan/core/imag/boto/examinar.gif",
                imageheight : 22,
                imagewidth : 82,
                width : 240
            });

            // Para el copiar al Clipboard
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
        }
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

        $('.cabecera').hide();
        $(thediv).show();
        $('.tabs a').removeClass('selected');
        $('.tabs a[href="'+thediv+'"]').addClass('selected');
        Fid.activarFotosFijas();

        // Se muestran / ocultan los botones de publicar foto
        if($(thediv).find('[id^="FOTOFIJA_"]').size() > 0) {
            $("#banco-img .botonera .publicar").show();
        } else {
            $("#banco-img .botonera .publicar").hide();
        }

        // Para la transcodificación
        if(typeof Transcoding !== 'undefined') {
            Transcoding.init(thediv);
        }
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

        var htmlFoto = $('#'+idFoto).parent().html();
        var currBody = '#'+$('#_curr_body').val();
        //alert(currBody + ' [id^="FOTOFIJA_"]');
        //alert($(currBody + ' [id^="FOTOFIJA_"]').length);
        $(currBody + ' [id^="FOTOFIJA_"]').each(function() {
            $(this).contents().find('body').html(htmlFoto);
        });
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
                    scalePhotos: false,
                    opacity: 0.8
                    // iframe: true,
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
            //alert(iframe);
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
            //alert(nom_img);
            Fid.objFormFid[this.id].value = nom_img;
        });
    },

    // -----------------------------------------
    procesarTags: function() {

        var tags4fid = $('#_tags4fid').val();
        if(typeof tags4fid === 'undefined') {
            return;
        }
        //alert(tags4fid);
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
        //alert($('#_tags').val());
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
        //iframe.contentWindow.document.body.background = '/'+Admin.prontus_id+Fid.iframeVoid;
        iframe.contentWindow.document.body.innerHTML = content;
        iframe.contentWindow.document.body.style.border = "none";
        iframe.contentWindow.document.body.style.margin = "2px";

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
    //Activa los controles del formulario
    activarFotosFijas: function() {
        $('iframe[id^=FOTOFIJA]').each(function(){
            try {
                if (Fid.isGecko) {
                    // A contar de Firefox 11
                    // this.contentDocument.designMode = 'on';
                    // this.contentWindow.document.contentEditable = true;
                    this.contentWindow.document.body.contentEditable = true;
                    this.contentWindow.document.addEventListener( "click", Fid.cancel_event, true );
                    this.contentWindow.document.addEventListener( "keydown", Fid.cancel_event, true );
                } else {
                    this.contentWindow.document.body.contentEditable = true;
                    this.contentWindow.document.body.attachEvent("onclick", Fid.cancel_event);
                    this.contentWindow.document.body.attachEvent("onkeydown", Fid.cancel_event);
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

        //var opciones = 'toolbar=0,status=0,menubar=0,scrollbars=1,resizable=1,location=0,directories=0,width=,height=,left=610,top=150';
        var url = 'prontus_imag_ficha.cgi?path_conf='+Admin.path_conf+'&ts='+mainFidJs.TS+'&foto='+nameimg;
        var nameWin = 'EditImg' + nameimg;
        Utiles.subWin(url, nameWin, 1000, 600);
        //var win = window.open(url, nameWin, opciones);
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
                    //window.open('prontus_art_ficha.cgi?_path_conf='+Admin.path_conf+'&_file='+resp.file+'&_fid='+resp.fid+'&fotosvtxt=/1/2/3/4');
                    //Fid.setGUIProcesando(false);
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
                //alert('pantalla ancha');
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
        Fid.guardaFotosFijas();
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

        // se submite el formulario
        $('#_mainFidForm').trigger('submit');

        if (bot_press == 'preview') {
            Fid.setGUIProcesando(false);
        }
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
                    // $("#reloj").hide();
                    // $("#botones_ficha").show();
                    if (json.status == 0) {
                        alert(unescape(json.msg));
                        Fid.listadoDatos();
                    } else {
                        if (json.msg !== '') {
                            alert(unescape(json.msg));
                            $.fn.colorbox.close();
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
    descargarArchivo: function() {
        
        var url = "prontus_form_download.cgi?" + $('#backupDatos').serialize();
        open(url, 'Descargar respaldo');
    },

    // -------------------------------------------------------------------------
    //Funcion usada en los formularios para abrir el administrador de archivos adjuntos
    listadoDatos: function() {
        var url = 'prontus_form_list.cgi?_prontus_id=' + mainFidJs.PRONTUS_ID +  '&_ts=' + mainFidJs.TS;
        $.fn.colorbox({
                open: true,
                href: url,
                width: 1000,
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
            var anio = now.getYear() + 1900;
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
                }
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
    }

};


