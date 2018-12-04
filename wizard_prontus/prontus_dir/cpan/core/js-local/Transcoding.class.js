var Transcoding, Msg, Flash;
(function () {
    "use strict";

    // -----------------------------------------------------------------------------
    // Objeto que sirve par la transcodificación
    Transcoding = {

        // Configuración
        panelVideo: '.panel-xcode',
        idVideo: '#linkVideo',
        panelStatus: '#panelStatus',
        idMultimediaVideo: '#MULTIMEDIA_VIDEO1',

        dirCgi: './xcoding/',
        cgiCode: 'prontus_videoxcode.cgi',
        cgiStatus: 'prontus_videoxcodestatus.cgi',
        cgiSnap: 'prontus_videogetsnapshot.cgi',
        cgiCut: 'prontus_videocut.cgi',
        cgiQt: 'prontus_qtfaststart_check.cgi',

        videoExtension: '.mp4',
        imageExtension: '.jpg',

        timeStatus: 2000,

        // Uso interno
        linkVideo: '',
        linkExt: '',
        linkImagen: '',
        linkImagenB: '',
        initialized: false,
        transcoding: false,

        // -------------------------------------------------------------------------
        init: function (idTab) {
            if ($(idTab + ' #xcodeInput').val() != 1) {
                return;
            }
            $(Transcoding.idVideo + ' a:first').each(function () {
                if (Transcoding.initialized) {
                    if(! Transcoding.transcoding) {
                        return;
                    }
                    Transcoding.reloadVideo();
                    return;
                }
                Transcoding.initialized = true;

                Transcoding.linkVideo = $(this).attr('href');
                Transcoding.linkExt = Transcoding.linkVideo.substr(Transcoding.linkVideo.lastIndexOf('.'));
                Transcoding.linkImagen = Transcoding.linkVideo.substr(0, Transcoding.linkVideo.lastIndexOf('.')) + Transcoding.imageExtension;
                var nameImg = Transcoding.linkImagen.substr(Transcoding.linkImagen.lastIndexOf('/') + 1);
                Transcoding.linkImagenB = '/' + Admin.prontus_id + '/cpan/procs/imgedit/' + nameImg;

                if (Transcoding.linkExt !== Transcoding.videoExtension) {
                    //alert('Transcoding.checkStatus');
                    Msg.setStatusMessage(ProntusLangController.getString('_transcode_checking_state'));
                    Transcoding.checkStatus();
                } else {
                    //alert('Transcoding.loadFlash');
                    Transcoding.checkMp4();
                }
            });
        },
        // -------------------------------------------------------------------------
        checkMp4: function () {
            $.ajax({
                url: Transcoding.dirCgi + Transcoding.cgiQt,
                type: "post",
                dataType: 'json',
                data: {video: Transcoding.linkVideo, prontus_id: Admin.prontus_id},
                success: function (data) {
                    if (typeof data !== 'undefined' && typeof data.status !== 'undefined') {
                        if (data.status == '1') {
                            if (data.msg == 'FIX') {
                                Msg.setStatusMessage(ProntusLangController.getString('_transcode_needs_adjustment'));
                                setTimeout(function () {
                                    Transcoding.checkMp4();
                                }, Transcoding.timeStatus);
                            } else if (data.msg == 'Busy') {
                                Msg.setStatusMessage(ProntusLangController.getString('_transcode_needs_adjustment'));
                                setTimeout(function () {
                                    Transcoding.checkMp4();
                                }, Transcoding.timeStatus);
                            } else if (data.msg == 'OK') {
                                Msg.setInfoMessage(ProntusLangController.getString('_transcode_adjusted'));
                                setTimeout(function () {
                                    Transcoding.loadFlash();
                                }, 250);
                            } else if (data.msg == 'XCODE') {
                                Msg.setStatusMessage(ProntusLangController.getString('_transcode_generating_versions'));
                                Transcoding.procesarVideo(1);
                            } else if (data.msg == 'Xcoding') {
                                Transcoding.checkStatus();
                            } else if (data.msg == 'RECODE') {
                                Msg.setStatusMessage(ProntusLangController.getString('_transcode_bitrate_too_high_adjusting'));
                                Transcoding.procesarVideo();
                            } else {
                                Msg.setAlertMessage(ProntusLangController.getString('_transcode_invalid_response'));
                            }
                        } else {
                            Msg.setAlertMessage(ProntusLangController.getString('_transcode_error_adjusting_video') + data.msg);
                        }
                    } else {
                        Msg.setAlertMessage(ProntusLangController.getString('_transcode_critical_error_adjusting_video') + data);
                    }
                },
                error:  function (msg) {
                    Msg.setAlertMessage(ProntusLangController.getString('_transcode_error_retrieving_status') + msg);
                }
            });
        },

        // -------------------------------------------------------------------------
        checkStatus: function () {
            $.ajax({
                url: Transcoding.dirCgi + Transcoding.cgiStatus,
                type: "post",
                dataType: 'json',
                data: {video: Transcoding.linkVideo, prontus_id: Admin.prontus_id},
                success: function (data) {
                    if (typeof data !== 'undefined' && typeof data.status !== 'undefined') {
                        if (data.status == '1') {
                            if (data.msg == 'none') {
                                Msg.setStatusMessage(ProntusLangController.getString('_transcode_video_being_processed'));
                                Transcoding.procesarVideo();
                            } else if (data.msg == 'busy') {
                                Transcoding.transcoding = true;
                                Msg.setStatusMessage(ProntusLangController.getString('_transcode_video_being_processed'));
                                setTimeout(function () {
                                    Transcoding.checkStatus();
                                }, Transcoding.timeStatus);

                            } else if (data.msg == 'ready') {
                                Transcoding.transcoding = false;
                                Msg.setInfoMessage(ProntusLangController.getString('_transcode_video_converted'));
                                setTimeout(function () {
                                    Transcoding.loadFlash();
                                }, 250);
                            }
                        } else {
                            if (data.msg != '') {
                                Msg.setAlertMessage(ProntusLangController.getString('_transcode_error_retrieving_status') + data.msg);
                            } else {
                                Msg.setAlertMessage(ProntusLangController.getString('_transcode_error_retrieving_status'));
                            }
                        }
                    } else {
                        Msg.setAlertMessage(ProntusLangController.getString('_transcode_error_retrieving_status'));
                    }
                },
                error:  function (msg) {
                    Msg.setAlertMessage(ProntusLangController.getString('_transcode_error_retrieving_status') + msg);
                }
            });
        },
        // -------------------------------------------------------------------------
        procesarVideo: function (generar_versiones) {
            var opciones = {
                video: Transcoding.linkVideo,
                prontus_id: Admin.prontus_id,
                generar_versiones: 0,
            };

            if (typeof generar_versiones != 'undefined') {
                opciones.generar_versiones = 1;
            }

            $.ajax({
                url: Transcoding.dirCgi + Transcoding.cgiCode,
                type: "post",
                dataType: 'json',
                data: opciones,
                success: function (resp) {
                    if (typeof resp !== 'undefined' && typeof resp.status !== 'undefined') {
                        if (resp.status == '1') {
                            Msg.setStatusMessage(ProntusLangController.getString('_transcode_video_being_processed'));
                            Transcoding.transcoding = true;
                            setTimeout(function () {
                                Transcoding.checkStatus();
                            }, Transcoding.timeStatus);

                        } else {
                            Msg.setAlertMessage(ProntusLangController.getString('_transcode_error_converting_video') + resp.msg);
                        }

                    } else {
                        Msg.setAlertMessage(ProntusLangController.getString('_transcode_critical_error_converting_video') + resp);
                    }
                },
                error:  function (msg) {
                    Msg.setAlertMessage(ProntusLangController.getString('_transcode_ajax_response_error') + msg.responseText);
                }
            });
        },

        // -------------------------------------------------------------------------
        loadFlash: function () {
            if (Transcoding.linkExt !== Transcoding.videoExtension) {
                Transcoding.linkVideo = Transcoding.linkVideo.substr(0, Transcoding.linkVideo.lastIndexOf('.')) + Transcoding.videoExtension;
                Transcoding.linkExt = Transcoding.linkVideo.substr(Transcoding.linkVideo.lastIndexOf('.'));
                $(Transcoding.idVideo + ' a:first').attr('href', Transcoding.linkVideo);

                var nameVideo = Transcoding.linkVideo;
                nameVideo = nameVideo.substr(Transcoding.linkVideo.lastIndexOf('/') + 1);
                $(Transcoding.idVideo + " input[name^='_HIDD_']").val(nameVideo);
            }
            $(Transcoding.panelVideo).show();
            Flash.iniciaFlash('#player-content');
        },

        // -------------------------------------------------------------------------
        reloadVideo: function () {
            //alert('Flash.setMovie');
            Flash.setMovie(Transcoding.linkVideo);
        },

        // -------------------------------------------------------------------------
        generaScreenshot: function () {
            try {
                Msg.setStatusMessage(ProntusLangController.getString('_transcode_screenshot_creating'));
                var time = Flash.getPlayPoint();

                if (typeof time === 'undefined') {
                    if (Transcoding.transcoding === true) {
                        Msg.setAlertMessage(ProntusLangController.getString('_transcode_screenshot_wait_for_conversion'));

                    } else if (Transcoding.linkVideo === '') {
                        Msg.setAlertMessage(ProntusLangController.getString('_transcode_screenshot_no_video_loaded'));

                    } else {
                        Msg.setAlertMessage(ProntusLangController.getString('_transcode_screenshot_error_reading_time'));
                    }
                } else {
                    $.ajax({
                        url: Transcoding.dirCgi + Transcoding.cgiSnap,
                        type: "post",
                        data: {t: time, video: Transcoding.linkVideo, prontus_id: Admin.prontus_id}, // w: Transcoding.wvideo, h: Transcoding.hvideo},
                        success: function (msg) {
                            if (msg === 'OK') {
                                Msg.setInfoMessage(ProntusLangController.getString('_transcode_screenshot_done'));
                                setTimeout(function () {
                                    $('#_fotoeditada').val(Transcoding.linkImagenB);
                                    Fid.submitir('Guardar', '_self');
                                }, 500);
                            } else {
                                Msg.setAlertMessage(ProntusLangController.getString('_transcode_screenshot_error') + msg);
                            }
                        },
                        error:  function (msg) {
                            Msg.setAlertMessage(ProntusLangController.getString('_transcode_screenshot_error') + msg);
                        }
                    });
                }
            } catch (e) {
                Msg.setAlertMessage(ProntusLangController.getString('_transcode_screenshot_error') + e);
            }
        },

        // -------------------------------------------------------------------------
        cortarVideo: function () {
            try {
                Msg.setStatusMessage('Generando el Corte del Video');
                var marcas = Flash.getMarkers();

                if (typeof marcas === 'undefined') {

                    if (Transcoding.transcoding === true) {
                        Msg.setAlertMessage(ProntusLangController.getString('_transcode_cut_wait_for_conversion'));

                    } else if (Transcoding.linkVideo === '') {
                        Msg.setAlertMessage(ProntusLangController.getString('_transcode_cut_no_video_loaded'));

                    } else {
                        Msg.setAlertMessage(ProntusLangController.getString('_transcode_cut_couldnt_get_marks'));
                    }
                } else {

                    if (marcas.length !== 2) {
                        Msg.setAlertMessage(ProntusLangController.getString('_transcode_cut_wrong_mark_format'));
                        return;
                    }
                    if (marcas[0] === 0 && marcas[1] === 0) {
                        Msg.setAlertMessage(ProntusLangController.getString('_transcode_cut_correct_mark_usage'));
                        return;
                    }

                    $.ajax({
                        url: Transcoding.dirCgi + Transcoding.cgiCut,
                        type: "post",
                        data: {t1: marcas[0], t2: marcas[1], video: Transcoding.linkVideo, prontus_id: Admin.prontus_id},
                        success: function (msg) {
                            if (msg === 'OK') {
                                Msg.setInfoMessage(ProntusLangController.getString('_transcode_cut_success'));
                                setTimeout(function () {
                                    // Sólo para efectos de refresh
                                    Fid.submitir('Guardar', '_self');
                                }, 500);
                            } else {
                                Msg.setAlertMessage(ProntusLangController.getString('_transcode_cut_generic_error') + msg);
                            }
                        },
                        error:  function (msg) {
                            Msg.setAlertMessage(ProntusLangController.getString('_transcode_cut_generic_error') + msg);
                        }
                    });
                }
            } catch (e) {
                Msg.setAlertMessage(ProntusLangController.getString('_transcode_cut_generic_error') + e);
            }
        },

        // -------------------------------------------------------------------------
        validarVideo: function () {
            var file, idx, ext;

            file = $(Transcoding.idMultimediaVideo).val();
            if (file !== '') {
                idx = file.lastIndexOf('.');
                if (idx < 0) {
                    return ProntusLangController.getString('_transcode_file_without_extension');
                }
                ext = file.substr(idx);
                ext = ext.toLowerCase();

                if (ext !== '.avi' && ext !== '.flv' && ext !== '.mp4' && ext !== '.wmv' && ext !== '.mpg' && ext !== '.mpeg' && ext !== '.3gp' && ext !== '.mov') {
                    return ProntusLangController.getString('_transcode_unsupported_file_extension');
                }

            }
            return '';
        },

        // -------------------------------------------------------------------------
        setFlashReady: function () {
            Flash.setMovie(Transcoding.linkVideo);
            return true;
        }
    };

    // -----------------------------------------------------------------------------
    //  Objeto encargado de mostrar los mensajes
    Msg = {

        imgAlert: '/cpan/core/imag/xcode/ico_alert.gif',
        imgInfo: '/cpan/core/imag/xcode/ico_info.gif',
        imgStatus: '/cpan/core/imag/loading.gif',

        // Funciones para los Estados y Mensajes
        setInfoMessage: function (msg) {
            var img = '<img src="/' + Admin.prontus_id + Msg.imgInfo + '" alt="'+ProntusLangController.getString('_transcode_information')+'" width="32" height="32" />';
            $(Transcoding.panelStatus).html(img + ' <div>' + msg + '</div>');
        },
        setStatusMessage: function (msg) {
            var img = '<img src="/' + Admin.prontus_id + Msg.imgStatus + '" alt="'+ProntusLangController.getString('_transcode_loading')+'" width="32" height="32" />';
            $(Transcoding.panelStatus).html(img + ' <div>' + msg + '</div>');
        },
        setAlertMessage: function (msg) {
            var img = '<img src="/' + Admin.prontus_id + Msg.imgAlert + '" alt="'+ProntusLangController.getString('_transcode_alert')+'" width="32" height="32" />';
            $(Transcoding.panelStatus).html(img + ' <div>' + msg + '</div>');
        }
    };

    // -----------------------------------------------------------------------------
    //  Objeto que ejecuta las funciones de internas del flash
    Flash = {

        movieObj: null,

        pooling: 0,
        maxPooling: 5,

        anchoPlayer: 440,
        altoPlayer: 350,

        playerVideo: '/cpan/core/flash/player_video/playerVideo.swf',
        playerId: 'idPlayer',
        playerName: 'playerVideoName',

        //Inicia el Flash del video, para que funcione en IE
        iniciaFlash: function (idDiv) {
            if (Flash.movieObj === null) {

                // Se inserta el player
                Flash.insertaPlayer(idDiv);

                // Para darle tiempo al flash para que se cargue
                setTimeout(function () {
                    Flash.movieObj = Flash.getObject();
                    //alert('iniciaFlash Flash.movieObj: ' + Flash.movieObj);
                }, 500);

            }
        },

        // Inserta el player según corresponda
        insertaPlayer: function (idDiv) {

            if(!jQuery.browser.flash) {
                $(idDiv).html('<video width="'+Flash.anchoPlayer+'" height="'+Flash.altoPlayer+'" controls="controls"></video>')
                        .find('video').append('<source src="'+Transcoding.linkVideo+'" type="video/mp4" />');
            } else {
                $(idDiv).media({
                    width: Flash.anchoPlayer,
                    height: Flash.altoPlayer,
                    src: '/' + Admin.prontus_id + Flash.playerVideo,
                    params: {
                        allowScriptAccess: 'always',
                        allowFullScreen: 'true',
                        wmode: 'opaque'
                        //quality: 'high'
                    },
                    attrs: {
                        id: Flash.playerId,
                        name: Flash.playerName
                    },
                    flashvars: {
                        XCOD: 'true'
                    }
                });
            }

        },

        // Obtiene el objeto movie
        getObject: function () {
            // Se obtiene el objeto
            var movieObj = window[Flash.playerName];
            if (typeof movieObj === 'undefined') {

                movieObj = document[Flash.playerName];
                if (typeof movieObj === 'undefined') {

                    movieObj = document.getElementById(Flash.playerId);
                }
            }
            if (typeof movieObj === 'undefined') {
                Msg.setAlertMessage(ProntusLangController.getString('_transcode_error_loading_player'));
                movieObj = null;
            }
            return movieObj;
        },

        // Setea el archivo de video en el flash
        setMovie: function (linkVideo) {
            try {

                if(Admin.notFlash) {
                    return;
                }
                //alert('Flash.movieObj: ' + Flash.movieObj);
                if (Flash.movieObj === null) {
                    Flash.movieObj = Flash.getObject();
                }
                if (typeof Flash.movieObj.setMovie === 'function') {
                    Flash.movieObj.setMovie(linkVideo);
                    Flash.movieObj.setScreenshot();
                    Flash.pooling = 0;

                } else {
                    if (Flash.pooling > Flash.maxPooling) {
                        Msg.setAlertMessage(ProntusLangController.getString('_transcode_flash_setmovie_error'));
                        return;
                    }
                    setTimeout(function () {
                        Flash.setMovie(linkVideo);
                    }, 500);
                    Flash.pooling++;
                }
            } catch (e) {
                Msg.setAlertMessage(ProntusLangController.getString('_transcode_flash_setmovie_error') + e);
            }
        },
        // Obtiene el punto actual que se está reproduciendo
        getPlayPoint: function () {
            try {
                if (Flash.movieObj === null) {
                    return;
                }
                return Flash.movieObj.getPlayPoint();
            } catch (e) {
                Msg.setAlertMessage(ProntusLangController.getString('_transcode_flash_getplaypoint_error') + e);
            }
        },
        // Coloca la marca A en el player
        setMarkerA: function () {
            try {
                if (Flash.movieObj === null) {
                    return;
                }
                Flash.movieObj.setMarkerA();
            } catch (e) {
                Msg.setAlertMessage(ProntusLangController.getString('_transcode_flash_setmarkera_error') + e);
            }

        },
        // Coloca la marca B en el player
        setMarkerB: function () {
            try {
                if (Flash.movieObj === null) {
                    return;
                }
                Flash.movieObj.setMarkerB();
            } catch (e) {
                Msg.setAlertMessage(ProntusLangController.getString('_transcode_flash_setmarkerb_error') + e);
            }
        },
        // Obtiene las marcas inicio y fin del trozo seleccionado
        getMarkers: function () {

            try {
                if (Flash.movieObj === null) {
                    return;
                }
                var markers = Flash.movieObj.getMarkers();
                //alert(markers);
                return markers;

            } catch (e) {
                Msg.setAlertMessage(ProntusLangController.getString('_transcode_flash_getmarkers_error') + e);
            }
        }
    };
})();
