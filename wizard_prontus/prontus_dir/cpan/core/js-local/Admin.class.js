var Admin = {

    prontus_id: '',
    path_conf: '',
    dir_cgi_cpn: '',
    dir_cgi_bin: '',

    counterError:0,
    maxErrorCounter:3,

    urlLogout: './prontus_logout.cgi',
    urlPing: './prontus_ping_inuse.cgi',
    urlUserInfo: 'prontus_head_info.cgi',

    timePing: 5000,
    timerPingId: null,

    isMSIE: false,
    isMozilla: false,
    isChrome: false,
    notFlash: false,

    randcode: 0,

    // -------------------------------------------------------------------------
    init: function(prontus_id) {
        Admin.prontus_id = prontus_id;
        Admin.path_conf = '/' + prontus_id + '/cpan/' + prontus_id + '.cfg';

        Admin.loadDirCgi();

        // Para chequeo y manejo multibrowser
        if($.browser.msie) {
            Admin.isMSIE = true;
        }
        if($.browser.mozilla) {
            Admin.isMozilla = true;
        }
        if($.browser.webkit) {
            Admin.isChrome = true;
        }

        // Si se han activado las Pop
        $('a.open_in_pop').live('click', function() {
            Admin.openArtic(this);
            return false;
        });

        Admin.randcode = Math.floor(Math.random() * (9999 - 1000 + 1)) + 1000;
        Admin.instalaDialogo();
    },


    // -------------------------------------------------------------------------
    openArtic: function(obj) {
        var lnk = $(obj).attr('href');
        var patt = /_file=(\d{14})/g;
        var results = patt.exec(lnk);
        var nom = 'newArtic';
        if(results !== null && results.length == 2) {
            nom = 'editFid'+results[1];
        }
        lnk = lnk + '&_popup=1';
        var winx = Math.floor(Math.random()*51);
        var winy = Math.floor(Math.random()*51);
        Utiles.subWin(lnk, nom, 1020, 640, winx, winy);
    },

    // -------------------------------------------------------------------------
    loadDirCgi: function() {
        var pathScript = '/' + Admin.prontus_id + '/cpan/dir_cgi.js';
        $.getScript(pathScript, function() {
            if(typeof DIR_CGI_CPAN === 'undefined') {
                setTimeout(function() {
                    Admin.loadDirCgi();
                }, 500);
            } else {
                Admin.dir_cgi_cpn = DIR_CGI_CPAN;
                // Para la carga de la informacion del usuario
                var datos = { _path_conf: Admin.path_conf };
                $('#userdata').load('/'+Admin.dir_cgi_cpn+'/'+Admin.urlUserInfo, datos);
            }
        });
    },

    // -------------------------------------------------------------------------
    cerrarSesion: function() {

        $.ajax({
            url: '/' + Admin.dir_cgi_cpn + '/' + Admin.urlLogout,
            data: {
                '_path_conf': Admin.path_conf,
                '_modo': 'ajax'
            },
            dataType: 'json',
            cache: false,
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                SubmitForm.handleError(LoadDiv.urlPub, XMLHttpRequest, textStatus, errorThrown);
            },
            success: function(resp, textStatus) {
                alert(ProntusLangController.getString('_admin_logout'));
                window.location.href = resp.url;
            }
        });
    },

    // -------------------------------------------------------------------------
    toLog: function(str) {
        str = str.replace(/</, '&lt;');
        str = str.replace(/>/, '&gt;');
        $('#log').html(str);

    },

    // -------------------------------------------------------------------------
    displayMessage: function(str, tipo) {
        $('#msg-global').hide();
        if(tipo == 'info' || tipo == 'alert' || tipo == 'error') {
            str = '<img src="/'+Admin.prontus_id+'/cpan/core/imag/boto/msg-'+tipo+'.png" width="24" height="24" alt="'+tipo+'" title="'+tipo+'" /> <span>' + str + '</span>' +
                    '<div class="cerrar"><a href="#" onclick="Admin.closeMessage(); return false;"><img src="/'+Admin.prontus_id+'/cpan/core/imag/boto/close-msg_of.png" ' +
                    'width="16" height="16" alt="'+ ProntusLangController.getString('_admin_alt_display_message_close')+'" title="'+ ProntusLangController.getString('_admin_alt_display_message_close')+'" class="cambia-boton"/></a></div>';
            $('#msg-global').html(str).fadeIn('slow');
        }
    },

    // -------------------------------------------------------------------------
    setPublicacionDirecta: function(str) {
        $('#pub-direct').hide();
        if(str !== '') {
            str = '<img src="/'+Admin.prontus_id+'/cpan/core/imag/boto/msg-alert.png" width="24" height="24" alt="'+ ProntusLangController.getString('_admin_alt_publicacion_directa')+'" title="'+ ProntusLangController.getString('_admin_alt_publicacion_directa')+'" /> <span>' + str + '</span>';
            $('#pub-direct').html(str).fadeIn();
        }
    },

    // -------------------------------------------------------------------------
    updateConcurrency: function(msg, tipo) {
        if(msg !== '') {
            if(tipo == 'port') {
                msg = ProntusLangController.getString('_admin_port_concurrency') + msg;
            } else if(tipo == 'art') {
                msg = ProntusLangController.getString('_admin_art_concurrency') + msg;
            } else {
                return;
            }
            var str = '<img src="/'+Admin.prontus_id+'/cpan/core/imag/boto/msg-alert.png" width="24" height="24" alt="'+ProntusLangController.getString('_admin_concurrency')+'" title="'+ProntusLangController.getString('_admin_concurrency')+'" /> <span>' + msg + '</span>';
            $('#concurrency').html(str).fadeIn();
        } else {
            $('#concurrency').hide();
        }
    },

    // -------------------------------------------------------------------------
    updateLockRecurso: function (value, tipo_rec) {
        if (typeof $('#lock_recurso').val() == 'undefined') {
            // Se define el input, para que la proxima vez que se haga el ping, no se vuelva a mostrar el mensaje.
            $('body').append('<input type="hidden" id="lock_recurso" value="' + value + '" />');
            if (value == 1) {
                // Solo advertencia.
                if (tipo_rec == 'art') var msg = ProntusLangController.getString('_admin_locked_art_warning');
                if (tipo_rec == 'port') var msg = ProntusLangController.getString('_admin_locked_port_warning');
                msg = ProntusLangController.getString('_admin_locked_warning')+":\n\n" + msg + "\n\n"+ProntusLangController.getString('_admin_locked_code')+": " +  Admin.randcode;
                Admin._lockRecursoPrompt(msg);
            } else if (value == 2) {
                // Bloqueo total.
                if (tipo_rec == 'art') var msg = ProntusLangController.getString('_admin_locked_art_error');
                if (tipo_rec == 'port') var msg = ProntusLangController.getString('_admin_locked_port_error');
                Admin._lockRecursoTotal(tipo_rec, msg);
            }
        }
    },

    _lockRecursoPrompt: function (msg) {
        var code = prompt(msg);
        if (code == null || code == '') {
            var msg = ProntusLangController.getString('_admin_unlock_get_code', {'code': Admin.randcode});
            Admin._lockRecursoPrompt(msg);
        } else {
            if (code != Admin.randcode) {
                var msg = ProntusLangController.getString('_admin_unlock_invalid_code', {'code': Admin.randcode});
                Admin._lockRecursoPrompt(msg);
            } else {
            }
        }
    },

    _lockRecursoTotal: function (tipo, msg) {
        var html = '<div class="lockscreen"><h3>' + msg + '</h3></div>';
        var height = $('#main').find('.content').height();
        $('#main').find('.main-left').append(html);
        $('.lockscreen').height(height);
        if (tipo == 'art') {
            $('.lockscreen').css('top', 143); // !!! no me rete cesar!
        }
    },

    // -------------------------------------------------------------------------
    closeMessage: function(str, tipo) {
        $('#msg-global').fadeOut();
    },

    // -------------------------------------------------------------------------
    ocultarBarraColorbox: function() {
        $('#cboxClose').hide();
        $('#cboxBottomLeft').css('height', '10px').css('background-position', 'left bottom');
        $('#cboxBottomCenter').css('height', '10px');
        $('#cboxBottomRight').css('height', '10px').css('background-position', '-36px bottom');
    },

    // -------------------------------------------------------------------------
    mostrarBarraColorbox: function() {
        $('#cboxClose').show();
        $('#cboxBottomLeft').css('height', '43px');
        $('#cboxBottomCenter').css('height', '43px');
        $('#cboxBottomRight').css('height', '43px');
    },

    // -------------------------------------------------------------------------
    cerrarColorbox: function() {
        $.fn.colorbox.close();
    },

    // -------------------------------------------------------------------------
    pingRecurso: function(tipo_rec, nom_rec, completeFunc) {

        if(Admin.timerPingId !== null) {
            clearTimeout(Admin.timerPingId);
        }
        var datos = {
            _tipo_recurso: tipo_rec,
            _nom_recurso: nom_rec,
            _path_conf: Admin.path_conf
        };
        $.ajax({
            url: Admin.urlPing,
            data: datos,
            dataType: 'json',
            cache: false,
            complete: function() {
                Admin.timerPingId = setTimeout(function() {
                    completeFunc();
                }, Admin.timePing);
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                Admin.counterError++;
                if(Admin.counterError >= Admin.maxErrorCounter) {
                    if($('#dialogping').dialog("isOpen") !== true) {
                        //alert(XMLHttpRequest+', '+textStatus+', '+errorThrown);
                        $('#dialogping .error').html(errorThrown);
                        $('#dialogping .detalle').html("Status:\n"+XMLHttpRequest.status+"\n\nResponseHeaders:\n"+XMLHttpRequest.getAllResponseHeaders());
                        $('#dialogping').dialog("open");
                    }
                }
            },
            success: function(resp, textStatus) {
                if(resp === null ) {
                    return;
                }
                Admin.counterError = 0;
                if(resp.status != 1) {
                    Admin.displayMessage(resp.msg, 'error');
                } else {
                    if($('#dialogping').dialog("isOpen") === true) {
                        $('#dialogping').dialog("close");
                    };
                    Admin.updateConcurrency(resp.msg, tipo_rec);
                    Admin.updateLockRecurso(resp.lock, tipo_rec);
                }
            }
        });
    },
    // -------------------------------------------------------------------------
    instalaDialogo: function () {

        if($("#dialogping-outter").size() < 1) {
            $("body").append('<div class="dialogping-outter"></div>');
            $(".dialogping-outter:last").append('<div></div>');
            $(".dialogping-outter div:last").attr('id', 'dialogping');
            var strerror = ProntusLangController.getString('_admin_install_conn_error')
                    + "<br/>"+ ProntusLangController.getString('_admin_install_status') + ":<br/><br/><span class=\"error\"></span><br/><br/>"
                    + ProntusLangController.getString('_admin_install_wait')
                    + ProntusLangController.getString('_admin_install_technical') + "<a href=\"#\">"+ProntusLangController.getString('_admin_install_button')+"</a>"
                    + "<textarea class=\"detalle\"></textarea>";
            $("#dialogping").html(strerror);
            $("#dialogping a").bind('click', function() {
                $("#dialogping .detalle").toggle();
            });
            $("#dialogping").dialog({
                title: ProntusLangController.getString('_admin_install_conn_error_dialog'),
                draggable: false,
                width: 600,
                height: 400,
                modal: true,
                autoOpen: false,
                position: {
                    my: "center",
                    at: "center top+300",
                    of: '#main'
                }
            });
        }
    },

    // -------------------------------------------------------------------------
    validaFecha: function(fecha) {
        if(typeof fecha === 'undefined' || fecha === '') {
            return true;
        }
        var patt1 = /^\d\d\/\d\d\/\d\d\d\d$/;
        if (patt1.test(fecha)) {
            var arr = fecha.split("/");
            var day = parseInt(arr[0], 10);
            var mo = parseInt(arr[1], 10);
            var yr = parseInt(arr[2], 10);
            var testDate = new Date(yr, mo-1, day);
            if(testDate.getDate() != day) {
                return false;

            } else if(testDate.getMonth() + 1 != mo) {
                return false;

            } else if(testDate.getFullYear() != yr) {
                return false;
            }
            return true;
        }
        return false;
    },

    // -------------------------------------------------------------------------
    validaHora: function(hora) {
        if(typeof hora === 'undefined' || hora === '') {
            return true;
        }
        var patt1 = /^(\d\d):(\d\d)$/;
        if(patt1.test(hora)) {
            var hh = hora.substr(0, 2);
            var mm = hora.substr(3, 2);
            if(hh >= 0 && hh <= 23 && mm >= 0 && mm <= 59) {
                return true;
            }
        }
        return false;
    },

    // -------------------------------------------------------------------------
    setUpdateContent: function(status_upd) {
        var content = '';
        var imag = '/'+Admin.prontus_id+'/cpan/core/imag/auxi';
        var dim = ' width="16" height="16"';
        var content, texto;
        var patt = /\d+\.\d+\.\d+/g;
        if(patt.test(status_upd)) {
            // Para el caso normal en que si hay un update
            texto = ProntusLangController.getString('_admin_update_to_release', {'release': status_upd});
            content = "<a href=\"#\" onclick=\"Admin.prontusUpdate('" + status_upd + "'); return false;\">";
            content = content + '<img src="'+imag+'/upd_update.png"'+dim+' alt="'+texto+'" title="'+texto+'" /></a>';
        } else if(status_upd == 'no_updates') {
            // Para cuando no hay updates
            texto = ProntusLangController.getString('_admin_update_none_available');
            content = '<img src="'+imag+'/upd_noupdates.png"'+dim+' alt="'+texto+'" title="'+texto+'" />';

        } else if(status_upd == 'no_user') {
            // En este caso, el usuario no es Admin, así que no se muestra nada
            texto = '';
            content = '';

        } else if(status_upd == 'disabled') {
            // Cuando estan deshabilitadas desde el CFG
            texto = ProntusLangController.getString('_admin_update_disabled');
            content = '<img src="'+imag+'/upd_disabled.png"'+dim+'  alt="'+texto+'" title="'+texto+'" />';

        } else {
            texto = ProntusLangController.getString('_admin_update_cant_get_info');
            content = '<img src="'+imag+'/upd_alert.png"'+dim+' alt="'+texto+'" title="'+texto+'" />';
        }
        $('#update-content').html(content);
    },

    // -------------------------------------------------------------------------
    prontusUpdate: function(last_version_disponible) {
        if (confirm(ProntusLangController.getString('_admin_update_confirm', {'version': last_version_disponible}))) {
            // window.location.href="prontus_update.cgi?_path_conf="
            $.fn.colorbox({
                open: true,
                href: '/' + Admin.dir_cgi_cpn + '/prontus_update.cgi?_path_conf=' + Admin.path_conf,
                width: '520',
                height: '400',
                iframe: true,
                overlayClose: false,
                escKey: false,
                onLoad: function() {
                    Admin.ocultarBarraColorbox();
                }

                // iframe: true,
            });
        }
    },

    // -------------------------------------------------------------------------
    // Si onlyTypes se evalua como verdadero, en vez de imprimir el contenido de
    // los atributos, se impreme solo el tipo.
    debugPrintObject: function(obj, onlyTypes) {
        if(typeof onlyTypes === 'undefined') {
            onlyTypes = false;
        }
        var str = '';
        for(x in obj) {
            if(onlyTypes) {
                str = str + x + ' -> ' + typeof(obj[x]) + "\n";
            } else {
                str = str + x + ' -> ' + obj[x] + "\n";
            }

        }
        return str;
    },

    // -------------------------------------------------------------------------
    // Abre un colorbox con el formulario para cambiar contraseña.
    mostrarCambiarPassword: function () {
        var url = '/' + Admin.dir_cgi_cpn + '/prontus_usr_chgpass.cgi?_path_conf=' + Admin.path_conf;
        $.fn.colorbox({
            open: true,
            href: url,
            width: 500,
            height: 350,
            maxWidth: '95%',
            maxHeight: '90%',
            opacity: 0.8
            // iframe: true,
        });
    }

};
