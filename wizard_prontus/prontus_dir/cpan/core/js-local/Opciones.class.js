var Opciones = {
    urlBD: 'prontus_set_bd.cgi',
    urlRegenBD: 'prontus_regenerabd.cgi',
    urlRegenART: 'prontus_art_regen.cgi',
    urlRegenPORT: 'prontus_port_regen.cgi',
    urlRegenDamBD: 'dam/prontus_dam_regen.cgi',
    urlCheckInst: 'prontus_check_install.cgi',
    urlCheckPlat: 'prontus_check_platform.cgi',
    optsDefault: {
        open: true,
        width: '520px',
        height: '500px',
        overlayClose: false,
        iframe: true,
        escKey: false  // Deshabilita el ESC
    },
    statusCounter: 0,
    maxarticsLimit: 1000,

    // -------------------------------------------------------------------------
    init: function(prontus_id) {

        var default_tab = $('#default_tab').val();
        if (default_tab === '') {
            $('#tabs-admin').idTabs();
            $('#tabs-config').idTabs();
            $('#tabs-regen').idTabs();
        } else {
            $('#tabs-admin').idTabs('tab7');
            $('#tabs-config').idTabs(default_tab);
            $('#tabs-regen').idTabs();
        }

        // Deshabilita el ESC
        $().bind('cbox_open', function(){ alert('open'); $().unbind("keydown.cbox_close"); });

        // Para los Logs
        $('.colorbox').colorbox({
          width: '80%',
          height: '70%',
          maxWidth: '95%',
          maxHeight: '90%',
          iframe: true
        });

        // Para el Datepicker de las opciones avanzadas
        $.datepicker.setDefaults($.datepicker.regional.es);
        $('#fecharegen').datepicker({
            dateFormat: 'dd-mm-yy',
            buttonImage: '/'+prontus_id+'/cpan/core/imag/boto/calendar.gif',
            buttonImageOnly: true,
            showOn: 'both'
        });

        $( "#datefrom" ).datepicker({
            dateFormat: 'dd-mm-yy',
        });

        $( "#dateto" ).datepicker({
            dateFormat: 'dd-mm-yy',
        });

        $('#operador-art').change(function (e) {
            e.preventDefault();
            //Reset de Variables
            $('#fecharegen').val('');
            $('#datefrom').val('');
            $('#dateto').val('');
            $('#fecharegen').prop('type','text');

            //Verificación tipo de fecha.
            var value = $(this).val();
            if (value == "rango"){
                $('#fecharegen').hide();
                $('.fechac .ui-datepicker-trigger').hide();
                $('.daterange').show();
            } else{
                $('.fechac .ui-datepicker-trigger').show();
                $('#fecharegen').show();
                $('.daterange').hide();
            }
        });
    },

    // -------------------------------------------------------------------------
    accionIndexarBuscador: function() {

        var obj = Opciones.optsDefault;
        obj.href = 'prontus_indexer.cgi?dir=%2F' + Admin.prontus_id;
        obj.onLoad = function() {
            Admin.mostrarBarraColorbox();
        };
        $.fn.colorbox(obj);
    },

    // -------------------------------------------------------------------------
    accionListarTablas: function() {
        var obj = Opciones.optsDefault;
        obj.href = Opciones.urlBD + '?_path_conf=%2F' + Admin.prontus_id + '%2Fcpan%2F' + Admin.prontus_id + '.cfg' +
                '&sbm_accion=Listar'+ '&_'+ new Date().getTime();
        obj.onLoad = function() {
            Admin.mostrarBarraColorbox();
        };
        $.fn.colorbox(obj);
    },

    // -------------------------------------------------------------------------
    accionCrearTablas: function() {
        var obj = Opciones.optsDefault;
        obj.href = Opciones.urlBD + '?_path_conf=%2F' + Admin.prontus_id + '%2Fcpan%2F' + Admin.prontus_id + '.cfg' +
                '&sbm_accion=Crear'+ '&_'+ new Date().getTime();
        obj.onLoad = function() {
            Admin.mostrarBarraColorbox();
        };
        $.fn.colorbox(obj);
    },

    // -------------------------------------------------------------------------
    accionRegenerarTablas: function() {

        if (confirm('¿Está seguro de regenerar la tabla de artículos?')) {
            var obj = Opciones.optsDefault;
            obj.href = Opciones.urlRegenBD + '?_path_conf=%2F' + Admin.prontus_id + '%2Fcpan%2F' + Admin.prontus_id + '.cfg'+ '&epoch='+ new Date().getTime();
            obj.height = '360';
            obj.onLoad = function() {
                Admin.ocultarBarraColorbox();
            };
            $.fn.colorbox(obj);
        };
    },

    // -------------------------------------------------------------------------
    accionRegenerarTablasDam: function() {

        if (confirm('¿Está seguro de regenerar la tabla de multimedia?')) {
            var obj = Opciones.optsDefault;
            obj.href = Opciones.urlRegenDamBD + '?_path_conf=%2F' + Admin.prontus_id + '%2Fcpan%2F' + Admin.prontus_id + '.cfg'+ '&_'+ new Date().getTime();
            obj.height = '360';
            obj.onLoad = function() {
                Admin.ocultarBarraColorbox();
            };
            $.fn.colorbox(obj);
        };
    },

    // -------------------------------------------------------------------------
    ejecutarActualizacionMasiva: function () {
        // Validaciones.
        var fids_checked = $('input[name="INPUT_FIDS_REGEN[]"]:checked').size();
        if (fids_checked == 0) {
            alert("Debe seleccionar al menos 1 FID.");
        } else {
             var href = '/' + Admin.dir_cgi_cpn + '/' +Opciones.urlRegenART + '?_path_conf=%2F' + Admin.prontus_id + '%2Fcpan%2F' + Admin.prontus_id + '.cfg';
            // Fids.
            var fids = new Array();
            $('input[name="INPUT_FIDS_REGEN[]"]:checked').each(function () {
                fids.push($(this).val());
            });
            var fids_str = fids.join(',');
            href += '&fids=' + fids_str;

            // Vistas.
            var mvs = new Array();
            $('input[name="INPUT_MVS_REGEN[]"]:checked').each(function () {
                mvs.push($(this).val());
            });
            var mvs_str = mvs.join(',');
            if (mvs_str == '') {
                mvs_str = '@normal';
            }
            href += '&mvs=' + mvs_str;

            // Fecha.
            var fecha = $('#fecharegen').val();
            var operador = $('#operador-art').val();
            if (fecha != '' || operador == 'rango') {

                //Validacion Rango de fecha.
                if(operador == 'rango'){
                    var datefrom = $('#datefrom').val();
                    var dateto = $('#dateto').val();
                    if (datefrom == '' || dateto == ''){
                        alert('El rango de fechas no es válido. Debe ingresar un fecha de inicio y un fecha fin.');
                        return false;
                    }
                    var fechaFrom = datefrom.split('-');
                    var fechaTo = dateto.split('-');
                    if (!Opciones.validateDateFormat(datefrom) || !Opciones.validateDateFormat(dateto)) {
                        alert('El formato de la fecha inicio o fecha fin no es válido, intenta dd-mm-yyyy.');
                        return false;
                    }
                    fecha = '' + fechaFrom[2] + fechaFrom[1] + fechaFrom[0]+'/'+fechaTo[2] + fechaTo[1] + fechaTo[0];
                }

                //Validacion General (<,>,fecha especifica)
                if(operador == 'mayor' || operador == 'menor' || operador == 'fecha'){
                    var arr = fecha.split('-');
                    if (!Opciones.validateDateFormat(fecha)) {
                        alert('El formato de la fecha no es válido, intente dd-mm-yyyy.');
                        return false;
                    }
                    fecha = '' + arr[2] + arr[1] + arr[0];
                }

                href += '&fecha=' + fecha;
                href += '&op=' + operador;
            } else {
                href += '&fecha=@all&op=';
            }

            var secc1 = $('#_SECCION1').val();
            var tem1 = $('#_TEMA1').val();
            var subtem1 = $('#_SUBTEMA1').val();

            if (secc1) {
                href += '&_seccion1=' +  secc1;
            } else {
                href += '&_seccion1=0';
            }

            if (tem1) {
                href += '&_tema1=' +  tem1;
            } else {
                href += '&_tema1=0';
            }

            if (subtem1) {
                href += '&_subtema1=' +  subtem1;
            } else {
                href += '&_subtema1=0';
            }

            if (confirm('¿Está seguro de ejecutar la actualización masiva de artículos?')) {
                var obj = Opciones.optsDefault;
                obj.href = href + '&_' + new Date().getTime();
                obj.height = '360';
                $.fn.colorbox(obj);
            }
        }
    },
    validateDateFormat: function(date) {
        var re = new RegExp("^[0-9]{2}[-|\/]{1}[0-9]{2}[-|\/]{1}[0-9]{4}$");
        if (re.test(date)) {
            return true;
        } else {
            return false;
        }
    },
    // -------------------------------------------------------------------------
    ejecutarActualizacionMasivaPortadas: function() {

         var href = '/' + Admin.dir_cgi_cpn + '/' +Opciones.urlRegenPORT + '?_path_conf=%2F' + Admin.prontus_id + '%2Fcpan%2F' + Admin.prontus_id + '.cfg';

        // Ejecutar Post Procesos
        var check_pp = $('#CHK_regenerar_post_procesos').is(':checked') ? 'si' : '';
        href = href + '&check_pp='+check_pp;

        // Ejecutar Operador para las ediciones
        var operador = $('#operador').val();
        operador = (typeof operador === 'undefined') ? '' : operador;
        href = href + '&operador='+operador;

        var cmb_edic = $('#cmb_edic').val();
        cmb_edic = (typeof cmb_edic === 'undefined') ? '' : cmb_edic;
        href = href + '&cmb_edic='+cmb_edic;

        if (confirm('¿Está seguro de ejecutar la actualización masiva de portadas?')) {
            var obj = Opciones.optsDefault;
            obj.href = href + '&_' + new Date().getTime();
            obj.height = '360';
            $.fn.colorbox(obj);
        }
    },
    // -------------------------------------------------------------------------
    checkboxToggleChecked: function(name, action) {
        if (action == true) {
            $('input[name="' + name + '"]').attr("checked", "checked");
        } else {
            $('input[name="' + name + '"]').removeAttr("checked");
        }
    },

    // -------------------------------------------------------------------------
    accionCheckInstall: function() {
        var obj = Opciones.optsDefault;
        var accion = $('.check-install input:checked:first').val();
        if(typeof accion === 'undefined' || accion === null || accion <= 0) {
            alert('Debe elegir una de las opciones anteriores');
            return;
        }
        obj.width = '900px';
        obj.height = '500px';
        obj.href = Opciones.urlCheckInst + '?_prontus_id=' + Admin.prontus_id +
                '&accion=' + accion;
        obj.onLoad = function() {
            Admin.mostrarBarraColorbox();
        };
        $.fn.colorbox(obj);
    },

    // -------------------------------------------------------------------------
    accionCheckPlatform: function() {
        var obj = Opciones.optsDefault;
        //obj.href = Opciones.urlCheckPlat + '?prontus_id=' + Admin.prontus_id;
        obj.width = '900px';
        obj.height = '580px';
        obj.href = Opciones.urlCheckPlat;
        obj.onLoad = function() {
            Admin.mostrarBarraColorbox();
        };
        $.fn.colorbox(obj);

    },

    // -------------------------------------------------------------------------
    cerrarColorbox: function() {
        $.fn.colorbox.close();
    },

    // -------------------------------------------------------------------------
    checkStatus: function(theURL) {

        $.ajax({
            url: theURL,
            dataType: 'json',
            cache: false,
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                SubmitForm.handleError(theURL, XMLHttpRequest, textStatus, errorThrown);
            },
            success: function(resp, textStatus) {
                if(resp === null) {
                    if(Opciones.statusCounter > 10) {
                        $('#msg-loading').hide();
                        $('#msg-error').html("Error al procesar el script, recargue la página para continuar");
                        $('#msg-log').fadeIn();
                        return;
                    } else {
                        Opciones.statusCounter++;
                    }
                    setTimeout(function() {
                        Opciones.checkStatus(theURL);
                    }, 1500);
                    return;
                }
                if(resp.status === 0) {
                    if(typeof resp.inprogress !== 'undefined') {
                        $('#inprogress').html(resp.inprogress).fadeIn();
                    }
                    setTimeout(function() {
                        Opciones.checkStatus(theURL);
                    }, 1500);
                } else {
                    $('#inprogress').hide();
                    $('.boton-generico').fadeIn();
                    if(resp.error) {
                        $('#msg-loading').hide();
                        $('#msg-error').html(resp.msg);
                        $('#msg-log').fadeIn();

                    } else if(resp.msg !== '') {
                        $('#msg-loading').html(resp.msg);
                        $('#msg-log').fadeIn();

                    } else {
                        $('#msg-loading').hide();
                        $('#msg-result').fadeIn();
                        $('#msg-log').fadeIn();
                    }
                    if(resp.total) {
                        $('#total').html(resp.total);
                        $('#total').parent().fadeIn();
                    }
                }
            }
        });

    },

    // -------------------------------------------------------------------------
    checkStatusAdvanced: function(theURL, postFunction) {
        Opciones.postFunction = postFunction;
        $.ajax({
            url: theURL,
            dataType: 'json',
            cache: false,
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                //alert('handle error???');
                SubmitForm.handleError(theURL, XMLHttpRequest, textStatus, errorThrown);
            },
            success: function(resp, textStatus) {
                if(resp === null) {
                    if(Opciones.statusCounter > 10) {
                        $('#status-progress .status-loading').hide();
                        $('#status-progress .status-msg').html(resp.msg);
                        $('#status-progress .boton-generico').fadeIn();
                        $('#status-progress .status-result').hide();
                        $('#status-progress .status-error').fadeIn();
                        return;
                    } else {
                        Opciones.statusCounter++;
                    }
                    setTimeout(function() {
                        Opciones.checkStatus(theURL);
                    }, 1500);
                    return;
                }
                if(resp.loading == 1) {
                    if(typeof resp.total === 'undefined') {
                        resp.total = '';
                    }
                    if(typeof resp.actual === 'undefined') {
                        resp.actual = '';
                    }
                    var percentage = 'No disponible';
                    if(resp.total !== '' && resp.actual !== '' && resp.total > 0) {
                        percentage = Math.floor((100 * resp.actual) / resp.total) + '%';
                    }
                    $('#status-progress .status-loading').show();
                    $('#status-progress .status-actual').html(resp.actual).show();
                    $('#status-progress .status-total').html(resp.total).show();
                    $('#status-progress .status-percentage').html(percentage).show();
                    setTimeout(function() {
                        Opciones.checkStatusAdvanced(theURL);
                    }, 1500);
                } else {
                    if(typeof resp.msg === 'undefined' || resp.msg === 'null') {
                        resp.msg = '';
                    }
                    $('#status-progress .status-loading').hide();
                    $('#status-progress .status-msg').html(resp.msg);
                    $('#status-progress .boton-generico').fadeIn();
                    if(resp.status == 1) {
                        $('#status-progress .status-result').fadeIn();
                        $('#status-progress .status-error').hide();
                        if(typeof Opciones.postFunction === 'function') {
                            Opciones.postFunction();
                        }
                    } else {
                        $('#status-progress .status-result').hide();
                        $('#status-progress .status-error').fadeIn();
                    }
                }
            }
        });

    },
    // -------------------------------------------------------------------------
    openPopupLog: function(obj) {

        if(typeof obj === 'undefined') {
            return;
        }

        if($(obj).attr('href') === '') {
            return;
        }

        var loc = $(obj).attr('href');
        var wpop = 800;
        var hpop = 600;
        var posx = 0;
        var posy = 0;
        var nom = $(obj).attr('rel');
        if(nom === '') {
            nom = 'new_win_log';
        }
        if(screen.width && screen.height) {
            if(wpop < screen.width) {
                posx = (screen.width - wpop) / 2;
            }
            if(hpop < screen.height) {
                posy = (screen.height - hpop) / 2;
            }
        } else {
            alert();
        }

        Utiles.subWin(loc, nom, wpop, hpop, posx, posy);
    },

    // -------------------------------------------------------------------------
    toggleRegenAvanzado: function (o) {
        if ($(o).hasClass('selected')) {
            $(o).removeClass('selected');
        } else {
            $(o).addClass('selected');
        }

        $(o).parents('.mensajes').siblings('.regen_avanzado').slideToggle('fast');
    },

    // -------------------------------------------------------------------------
    validarMaxartics: function(maxartics) {
        if(maxartics > Opciones.maxarticsLimit) {
            $('#msg-maxartics span').html(Opciones.maxarticsLimit);
            $('#msg-maxartics').show();
        }
    },

    // -------------------------------------------------------------------------
    validarTaxNivCero: function(taxniv) {
        if(taxniv == '0') {
            $('#msg-taxniv-cero').show();
        }
    }

};
