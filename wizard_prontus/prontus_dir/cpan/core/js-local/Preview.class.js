
var Preview = {

    openType: 'left',
    screenLimit: 1480,
    anchoMin: 1024,

    isOpen: false,
    isBussy: false,
    timer: null,
    zoom: 70,
    maxZoom: 100,
    minZoom: 20,
    stepZoom: 10,

    widthTab: 19,
    widthTable: 500,

    animationSpeed: 200,
    timePreview: 5000,

    scrollObj: null,

    urlPreview: './prontus_art_public.cgi',

    // -------------------------------------------------------------------------
    init: function() {
        $('#preview .tab .abrir').click(function() {
            Preview.openPreview();
        });
        $('#preview .tab .cerrar').click(function() {
            Preview.closePreview();
        });
        Preview.widthTab = $('#preview .tab').width();
        Preview.widthTable = $('#preview .cont table').width();

        // Cargar automaticamente la fecha y la hora
        Preview.precargaFechaHora();

        // Cargar la combo de vistas
        Preview.cargaComboVistas();

        if(screen.width) {
            if(screen.width >= Preview.screenLimit) {
                //alert('pantalla ancha');
                Preview.openType = 'right';
                $('#main').css('overflow', 'visible');
            }
        }

        $('#theIframe').load(function() {
            Preview.setWidth();
            Preview.doZoom(Preview.zoom);
            Preview.setScroll();
            $('.loading-preview').fadeOut();
        });

        //alert('Admin.isMSIE:' + Admin.isMSIE + ', Admin.isWebkit:' + Admin.isWebkit);
    },

    // -------------------------------------------------------------------------
    openPreview: function() {
        if(Preview.isOpen) {
            return;
        }
        Preview.precargaFechaHora();
        Preview.isOpen = true;
        Preview.execPreview();
        if(Preview.openType == 'right') {
            $('#preview .cont').animate({width: Preview.widthTable}, Preview.animationSpeed);
            //$('html,body').animate({scrollLeft: Preview.widthTable}, Preview.animationSpeed);
            $('#preview .tab .abrir').hide();
            $('#preview .tab .cerrar').show();
        } else {
            $('#preview .cont').animate({marginLeft: '-=' + Preview.widthTable, width: Preview.widthTable}, Preview.animationSpeed);
            $('#preview .tab .abrir').hide();
            $('#preview .tab .cerrar').show();
        }
    },

    // -------------------------------------------------------------------------
    closePreview: function() {

        if(!Preview.isOpen) {
            return;
        }
        if(Preview.isBussy) {
            Admin.displayMessage('Por favor, espere a que termine de generar el Preview', 'alert');
            return;
        }
        Preview.isOpen = false;
        clearTimeout(Preview.timer);
        Preview.stopTimeleft();
        if(Preview.openType == 'right') {
            $('#preview .cont').animate({width: Preview.widthTab}, Preview.animationSpeed, function() {
            //$('html,body').animate({scrollLeft: 0}, Preview.animationSpeed);
                $('#preview .tab .abrir').show();
                $('#preview .tab .cerrar').hide();
                $('.loading-preview').hide();
            });
        } else {
            $('#preview .cont').animate({marginLeft: '+=' + Preview.widthTable, width: Preview.widthTab}, Preview.animationSpeed, function() {
                $('#preview .tab .abrir').show();
                $('#preview .tab .cerrar').hide();
                $('.loading-preview').hide();
            });
        }
        
        
    },

    // -------------------------------------------------------------------------
    cargaComboVistas: function() {

        var vistas = $('#_listado_vistas').val();
        if(vistas.length > 1) {
            var arrv = vistas.split(',');
            var x;
            for(x in arrv) {
                if(typeof arrv[x] !== 'undefined'){
                    $('#cmb_vista').append('<option value="'+ arrv[x] +'">'+ arrv[x] +'</option>');
                }
            }
        }
    },

    // -------------------------------------------------------------------------
    precargaFechaHora: function() {

        var today = new Date();
        var day = Preview.fix2Digits( today.getDate() );
        var mon = Preview.fix2Digits( today.getMonth() + 1);
        var yea = today.getFullYear();
        var hou = Preview.fix2Digits( today.getHours() );
        var min = Preview.fix2Digits( today.getMinutes() );

        $('#fecha_preview').val(day+'/'+mon+'/'+yea);
        $('#hora_preview').val(hou+':'+min);
    },

    // -------------------------------------------------------------------------
    fix2Digits: function(digit) {
        digit = '' + digit;
        if(digit.length == 2) {
            return digit;
        }
        digit = '0' + digit;
        return digit;
    },

    // -------------------------------------------------------------------------
    fastPreview: function() {

        // Si el preview no está abierto, no se hace nada
        if(!Preview.isOpen) {
            return;
        }

        // Se gatilla el preview
        if(Preview.timer !== null) {
            clearTimeout(Preview.timer);
        }

        Preview.execPreview();
    },

    // -------------------------------------------------------------------------
    startPreview: function() {
        // Si el preview no está abierto, no se hace nada
        if(!Preview.isOpen) {
            return;
        }

        // Se gatilla el preview
        if(Preview.timer !== null) {
            clearTimeout(Preview.timer);
        }
        Preview.startTimeleft();
        Preview.timer = setTimeout(function() {
            Preview.execPreview();

        }, Preview.timePreview);
    },

    // -------------------------------------------------------------------------
    execPreview: function() {
        // Si el preview no está abierto, no se hace nada
        if(!Preview.isOpen) {
            return;
        }

        // Se comprueba que el preview no esté gatillando un request anterior
        if(Preview.isBussy) {
            return;
        }
        Preview.isBussy = true;
        Preview.stopTimeleft();
        $('.loading-preview').show();

        //Valida Fecha Hora
        var fecha = $('#fecha_preview').val();
        var hora = $('#hora_preview').val();
        if(!Admin.validaFecha(fecha)) {
            Admin.displayMessage('La fecha no es válida, no se puede calcular el Preview', 'alert');
            //alert('La fecha no es válida, no se puede calcular el Preview');
            return;
        }
        if(!Admin.validaHora(hora)) {
            Admin.displayMessage('La hora no es válida, no se puede calcular el Preview', 'alert');
            //alert('La hora no es válida, no se puede calcular el Preview');
            return;
        }

        $('#_accion').val('preview');
        $('#_edic').val($('#cmb_edic').val());
        $('#_port').val($('#cmb_port').val());
        $('#_vista').val($('#cmb_vista').val());
        $('#_fecha_preview').val($('#fecha_preview').val());
        $('#_hora_preview').val($('#hora_preview').val());

        // Se captura el Scroll
        Preview.capturarScroll();

        var opts = {
            complete: function() {
                Preview.isBussy = false;
                if(Admin.isMSIE) {

                    setTimeout(function() {
                        if($('.loading-preview').is(':visible')) {
                            $('.loading-preview').fadeOut();
                        }
                    }, 2000);
                }
            },
            success: function(resp, textStatus) {
                if(!Preview.isOpen) {
                    return;
                }
                if(textStatus == 'success') {
//                    Admin.displayMessage('Se ejecuta el Preview', 'info');
//                    setTimeout(function() {Admin.closeMessage();}, 1000);
                    if(resp.status == 1) {
                        //alert(resp.msg);
                        $('#theIframe').attr('src', resp.msg);
                    } else {
                        Admin.displayMessage(resp.msg, 'error');
                    }
                } else {
                    Admin.displayMessage('Se produjo un error al intentar recargar el preview', 'error');
                }
            }
        };
        var config = {
            formSelector: '#listado',
            actionURL: Preview.urlPreview
        };

        //Acciones.muestraAcciones(false);
        SubmitForm.submitGenericAjax(config, opts);
    },

    // -------------------------------------------------------------------------
    previewNewWin: function() {
        // Se comprueba que el preview no esté gatillando un request anterior
        if(Preview.isBussy) {
            alert("open");
            return;
        }
        Preview.isBussy = true;

        //Valida Fecha Hora
        var fecha = $('#fecha_preview').val();
        var hora = $('#hora_preview').val();
        if(!Admin.validaFecha(fecha)) {
            Admin.displayMessage('La fecha no es válida, no se puede calcular el Preview', 'alert');
            //alert('La fecha no es válida, no se puede calcular el Preview');
            return;
        }
        if(!Admin.validaHora(hora)) {
            Admin.displayMessage('La hora no es válida, no se puede calcular el Preview', 'alert');
            //alert('La hora no es válida, no se puede calcular el Preview');
            return;
        }

        $('#_accion').val('preview');
        $('#_edic').val($('#cmb_edic').val());
        $('#_port').val($('#cmb_port').val());
        $('#_vista').val($('#cmb_vista').val());
        $('#_fecha_preview').val($('#fecha_preview').val());
        $('#_hora_preview').val($('#hora_preview').val());

        var opts = {
            complete: function() {
                Preview.isBussy = false;
            },
            success: function(resp, textStatus) {
                if(textStatus == 'success') {
                    if(resp.status == 1) {
                        //~ $('#theIframe').attr('src', resp.msg);
                        $('#openblank').val(resp.msg);
                        Preview.isBussy = false;
                    } else {
                        Admin.displayMessage(resp.msg, 'error');
                    }
                } else {
                    Admin.displayMessage('Se produjo un error al intentar recargar el preview', 'error');
                }
            }
        };
        var config = {
            formSelector: '#listado',
            actionURL: Preview.urlPreview
        };

        //Acciones.muestraAcciones(false);
        SubmitForm.submitGenericAjax(config, opts);

        var intervalo = setInterval(function () {
            if ($('#openblank').val() != '') {
                window.open($('#openblank').val());
                clearInterval(intervalo);
            }
        }, 500);
    },

    // -------------------------------------------------------------------------
    startTimeleft: function() {
        $('#inner-timeleft').stop();
        $('#inner-timeleft').width(0);
        $('#inner-timeleft').animate({width: '100%'}, Preview.timePreview);
    },

    // -------------------------------------------------------------------------
    stopTimeleft: function() {
        $('#inner-timeleft').stop();
        $('#inner-timeleft').width(0);
    },

    // -------------------------------------------------------------------------
    changeZoom: function(sign) {
        var actualZoom = Preview.zoom;
        var cambio;
        if(sign == '-') {
            cambio = (-1)*Preview.stepZoom;
        } else if(sign == '+') {
            cambio = Preview.stepZoom;
        } else {
            return;
        }
        var newZoom = actualZoom + cambio;
        if(newZoom >= Preview.maxZoom) {
            newZoom = Preview.maxZoom;
        } else if(newZoom <= Preview.minZoom) {
            newZoom = Preview.minZoom;
        }
        if(newZoom == actualZoom) {
            return;
        }
        Preview.doZoom(newZoom);
    },

    // -------------------------------------------------------------------------
    doZoom: function(zoom) {

        var zoomFactor = zoom / 100;
        var elIframe = document.getElementById('theIframe');
        if(Admin.isMSIE || Admin.isChrome) {
            // Si se usa elIframe, el zoom se aplica a toda la página... =/
            theIframe.document.body.style.zoom = zoomFactor;
        } else if(Admin.isMozilla) {
            $(elIframe.contentWindow.document.body).css('-moz-transform', 'scale('+zoomFactor+')');
            $(elIframe.contentWindow.document.body).css('-moz-transform-origin', '0 0');
        }
        Preview.zoom = zoom;
        $('#zoom-actual').html(zoom + '%');
    },

    // -------------------------------------------------------------------------
    getTransformProperty: function(element) {
        var properties = ['transform', 'WebkitTransform', 'MozTransform'];
        var p = properties.shift();
        while (p) {
            if (typeof element.style[p] != 'undefined') {
                return p;
            }
            p = properties.shift();
        }
        return false;
    },

    // -------------------------------------------------------------------------
    capturarScroll: function() {

        var scrollX;
        var scrollY;
        if(Admin.isMSIE) {
            // Si se usa elIframe, el zoom se aplica a toda la página
            scrollX = theIframe.document.body.scrollLeft;
            scrollY = theIframe.document.body.scrollTop;

        } else if(Admin.isMozilla) {
            var elIframe = document.getElementById('theIframe');
            scrollX = elIframe.contentWindow.pageXOffset;
            scrollY = elIframe.contentWindow.pageYOffset;
        } else {
            scrollX = 0;
            scrollY = 0;
        }
        Preview.scrollObj = {
            scrollX: scrollX,
            scrollY: scrollY
        };
    },

    // -------------------------------------------------------------------------
    setScroll: function() {
        if(Preview.scrollObj !== null) {
            var scrollX = Preview.scrollObj.scrollX;
            var scrollY = Preview.scrollObj.scrollY;
            if(typeof scrollX === 'undefined' || typeof scrollY === 'undefined') {
                return;
            }

            if(Admin.isMSIE) {
                // Si se usa elIframe, el zoom se aplica a toda la página
                theIframe.document.body.scrollLeft = scrollX;
                theIframe.document.body.scrollTop = scrollY;
                //alert(scrollX+', '+scrollY);
                //alert(Utiles.objectToString(theIframe.document.body));

            } else if(Admin.isMozilla) {
                var elIframe = document.getElementById('theIframe');
//                elIframe.contentWindow.pageXOffset = scrollX;
//                elIframe.contentWindow.pageYOffset = scrollY;
                elIframe.contentWindow.scrollBy(scrollX, scrollY);
            }

            Preview.scrollObj = null;
        }
    },

    // -------------------------------------------------------------------------
    setWidth: function() {
        if(Preview.isOpen === true) {
            var ancho = 0;
            var anchoMax;
            var body;
            var docum;
            if(Admin.isMSIE) {
                //anchoMax = theIframe['outerWidth'];
                body = theIframe.document.body;
                docum = theIframe.document;
            } else if(Admin.isMozilla) {
                var elIframe = document.getElementById('theIframe');
                //anchoMax = elIframe.contentWindow['outerWidth'];
                body = elIframe.contentWindow.document.body;
                docum = elIframe.contentWindow.document;
            } else {
                return;
            }

            // Se procesa el ancho
            var nodos = body.childNodes;
            var y;
            for(y in nodos) {
                if(typeof nodos[y].clientWidth !== 'undefined') {
                    var anchoTemp = nodos[y].clientWidth;
                    ancho = Math.max(ancho, anchoTemp);
                }
            }
            if(ancho < Preview.anchoMin) {
                 ancho = Preview.anchoMin;
            }

            var div = docum.createElement("div");
            div.id = "wrap";
            div.setAttribute('style', 'width:'+ancho+'px;');
            // Move the body's children into this wrapper
            while (body.firstChild) {
                div.appendChild(body.firstChild);
            }
            // Append the wrapper to the body
            body.appendChild(div);
        }
    }
};
