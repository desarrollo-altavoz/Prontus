// v1.0.0 - JOR
var Cfgedit = {
    newPortLastId: 0,
    guardaCfg: function (cfg) {
        var msg = "¿Estás seguro de modificar la configuración?";
        if (confirm(msg)) {
            var configAjax = {
                formSelector: '#frmCFG-' + (cfg.toUpperCase()),
                actionURL: 'prontus_cfg_save.cgi?_path_conf=' + Admin.prontus_id
            };

            var optsAjax = {
                success:   function(json, statusText) {
                    if (typeof json.msg !== 'undefined') {
                        alert(json.msg);
                    }

                    if (json.status === 1) {
                        var default_tab = $('form[name="frmCFG-' + cfg.toUpperCase() + '"]').find('input[name="_tab"]').val();
                        window.location.href = 'prontus_admin_main.cgi?_path_conf=/' + Admin.prontus_id + '/cpan/' +  Admin.prontus_id + '.cfg&tab=' + default_tab;
                    }

                    $('form[name="frmCFG-' + cfg.toUpperCase() + '"]').parent().find('.botones').show();
                    $('form[name="frmCFG-' + cfg.toUpperCase() + '"]').parent().find('#ajax-loading').hide();
                },
                error:   function(XMLHttpRequest, textStatus, errorThrown) {
                    SubmitForm.handleError(configAjax.actionURL, XMLHttpRequest, textStatus, errorThrown);
                    $('form[name="frmCFG-' + cfg.toUpperCase() + '"]').parent().find('.botones').show();
                    $('form[name="frmCFG-' + cfg.toUpperCase() + '"]').parent().find('#ajax-loading').hide();
                }
            };
            $('form[name="frmCFG-' + cfg.toUpperCase() + '"]').parent().find('.botones').hide();
            $('form[name="frmCFG-' + cfg.toUpperCase() + '"]').parent().find('#ajax-loading').show();

            if (cfg === 'art') {
                // Armar input.
                 var form_plts = '';

                $('input[name^="nombrefid_"]').each(function () {
                    if (!$(this).is(':disabled')) {
                        var id = ($(this).attr("name")).replace(/nombrefid_/, '');
                        var plantillas = '';
                        var plantillas_paralelas = '';

                        $('select[name="plantillasfid_' + id + '"] option:selected').each(function () {
                            plantillas += $(this).val() + ';';
                        });

                        $('select[name="plantillasfid_pla_' + id + '"] option:selected').each(function () {
                            plantillas_paralelas += $(this).val() + ';';
                        });


                        plantillas = plantillas.substring(0, plantillas.length - 1);
                        plantillas_paralelas = plantillas_paralelas.substring(0, plantillas_paralelas.length - 1);

                        if ($('[name="archivofid_' + id + '"]').val() !== '') {
                            form_plts += $('[name="archivofid_' + id + '"]').val() + ':' + $(this).val() + '(' + plantillas + ')(' + plantillas_paralelas + ')|';
                        }
                    }
                });

                form_plts = form_plts.substring(0, form_plts.length - 1);

                $('input[name="FORM_PLTS"]').val(form_plts);

            } else if (cfg === 'port') {
                // Actualizar input con lista de valores.
                var port_plts = '';

                $('[name^="portada_"]').each(function () {
                    if (!$(this).is(':disabled')) {
                        var id = ($(this).attr("name")).replace(/portada_/, '');
                        var plts = '';
                        $('select[name="plt_paralelas_' + id + '"] option:selected').each(function () {
                            plts += $(this).val() + ';';
                        });
                        plts = plts.substring(0, plts.length - 1);
                        var nom_port = $('input[name="nom_portada_' + id + '"]').val();
                        if (nom_port == '') {
                            nom_port = $(this).val();
                        }
                        nom_port = nom_port.replace(/</g, '&lt;');
                        nom_port = nom_port.replace(/>/g, '&gt;');
                        nom_port = nom_port.replace(/'/g, '&#39;');
                        nom_port = nom_port.replace(/"/g, '&quot;');
                        nom_port = nom_port.replace(/\(/g, '&#40;');
                        nom_port = nom_port.replace(/\)/g, '&#41;');
                        nom_port = nom_port.replace(/\[/g, '&#91;');
                        nom_port = nom_port.replace(/\]/g, '&#92;');
                        nom_port = nom_port.replace(/\{/g, '&#123;');
                        nom_port = nom_port.replace(/\}/g, '&#125;');
                        nom_port = nom_port.replace(/,/g, '&#44;');
                        nom_port = nom_port.replace(/\//g, '&#47;');

                        if ($(this).val() !== '') {
                            port_plts += $(this).val() + '(' + nom_port + ')(' + plts + ')(' + $('select[name="plt_preview_' + id + '"]').val() + ')|';
                        }
                    }
                });
                port_plts = port_plts.substring(0, port_plts.length - 1);

                $('input[name="PORT_PLTS"]').val(port_plts);

                var base_ports = '';
                $('[name="INPUT_BASE_PORTS[]"]').each(function () {
                    if (!$(this).is(':disabled')) {
                        base_ports += $(this).val() + "|";
                    }
                });
                $('input[name="BASE_PORTS"]').val(base_ports);

                var ports_dd = '';
                $('[name="INPUT_PORT_DRAGANDROP[]"]').each(function () {
                    if (!$(this).is(':disabled')) {
                        ports_dd += $(this).val() + "|";
                    }
                });
                $('input[name="PORT_DRAGANDROP"]').val(ports_dd);

            } else if (cfg === 'tax') {
                var taxport_orden = '';
                taxport_orden = $('select[name="TAXPORT_ORDEN_TIPO"]').val() + '(' + $('select[name="TAXPORT_ORDEN_ORD"]').val() + ')';
                $('input[name="TAXPORT_ORDEN"]').val(taxport_orden);
            } else if (cfg === 'tag') {
                var tagport_orden = '';
                tagport_orden = $('select[name="TAGPORT_ORDEN_TIPO"]').val() + '(' + $('select[name="TAGPORT_ORDEN_ORD"]').val() + ')';
                $('input[name="TAGPORT_ORDEN"]').val(tagport_orden);
            } else if (cfg === 'list') {
                var list_orden = '';
                list_orden = $('select[name="LIST_ORDEN_TIPO"]').val() + '(' + $('select[name="LIST_ORDEN_ORD"]').val() + ')';
                $('input[name="TAGPORT_ORDEN"]').val(list_orden);
            } else if (cfg === 'var') {
                var multivista = '';
                $('input[name="INPUT_MULTIVISTA[]"]').each(function () {
                    if (!$(this).is(':disabled')) {
                        if ($(this).val() !== '') {
                            multivista += $(this).val() + "|";
                        }
                    }
                });

                $('input[name="MULTIVISTA"]').val(multivista);

                var varnish = '';
                $('input[name="INPUT_VARNISH_SERVER_NAME[]"]').each(function () {
                    varnish += $(this).val() + "|";
                });
                $('input[name="VARNISH_SERVER_NAME"]').val(varnish);
            } else if (cfg === 'buscador') {
                //=============
                var prontus_dirs = '';
                $('input[name="INPUT_PRONTUS_DIR[]"]').each(function () {
                    if (!$(this).is(':disabled') && $(this).val() !== '') {
                        prontus_dirs += (($(this).val()).replace(/( +)|(\t)/, '')) + "|";
                    }
                });
                prontus_dirs = prontus_dirs.substring(0, prontus_dirs.length - 1);
                $('input[name="PRONTUS_DIR"]').val(prontus_dirs);
                //=============
                var raw_dirs = '';
                $('input[name="INPUT_RAW_DIR[]"]').each(function () {
                    if (!$(this).is(':disabled') && $(this).val() !== '') {
                        raw_dirs += (($(this).val()).replace(/( +)|(\t)/, '')) + "|";
                    }
                });
                raw_dirs = raw_dirs.substring(0, raw_dirs.length - 1);
                $('input[name="RAW_DIR"]').val(raw_dirs);
                //=============
                var raw_filetypes = '';
                $('input[name="INPUT_RAW_FILETYPES[]"]').each(function () {
                    if (!$(this).is(':disabled')) {
                        raw_filetypes += (($(this).val()).replace(/( +)|(\t)/, '')) + " ";
                    }
                });
                raw_filetypes = raw_filetypes.substring(0, raw_filetypes.length - 1);
                $('input[name="RAW_FILETYPES"]').val(raw_filetypes);

                var url_filetypes = '';
                $('input[name="INPUT_URL_FILETYPES[]"]').each(function () {
                    if (!$(this).is(':disabled')) {
                        url_filetypes += (($(this).val()).replace(/( +)|(\t)/, '')) + " ";
                    }
                });
                url_filetypes = url_filetypes.substring(0, url_filetypes.length - 1);
                $('input[name="URL_FILETYPES"]').val(url_filetypes);

                var fids = '';
                $('input[name="INPUT_FIDS[]"]').each(function () {
                    if ($(this).is(":checked")) {
                        fids += $(this).val() + ' ';
                    }
                });
                fids = fids.substring(0, fids.length - 1);
                $('input[name="FIDS"]').val(fids);

                var textvars = '';
                $('input[name="INPUT_TEXTVARS[]"]').each(function () {
                    if (!$(this).is(':disabled')) {
                        textvars += (($(this).val()).replace(/( +)|(\t)/, '')) + " ";
                    }
                });
                textvars = textvars.substring(0, textvars.length - 1);
                $('input[name="TEXTVARS"]').val(textvars);
            }

            SubmitForm.submitGenericAjax(configAjax, optsAjax);
        }
    },
    agregarFid: function () {
        var html = '<input name="INPUT_FORM_PLTS[]" value="" class="fieldform" style="margin-bottom: 1px; width: 89%;"/>';
        $('#form_plts_list').append(html);
    },
    agregarPort: function () {
        var html = '<input name="INPUT_PORTS_PLTS[]" value="" class="fieldform" style="margin-bottom: 1px; width: 89%;"/>';
        $('#port_plts_list').append(html);
    },
    agregarBasePort: function () {
        var html = '<input name="INPUT_BASE_PORTS[]" value="" class="fieldform" style="margin-bottom: 1px; width: 89%;"/>';
        $('#base_port_list').append(html);
    },
    agregarMv: function () {
        var html = '<tr><td><input name="INPUT_MULTIVISTA[]" value="" class="fieldform" style="margin-bottom: 1px; width: 125px;"/></td><td></td></tr>';
        $('#multivista_listado').append(html);
    },
    agregarRawDir: function () {
        var html = '<tr><td><input name="INPUT_RAW_DIR[]" value="" class="fieldform" style="margin-bottom: 1px; width: 125px;"/></td><td></td></tr>';
        $('#rawdir_listado').append(html);
    },
    agregarProntusDir: function () {
        var html = '<tr><td><input name="INPUT_PRONTUS_DIR[]" value="" class="fieldform" style="margin-bottom: 1px; width: 125px;"/></td><td></td></tr>';
        $('#prontusdir_listado').append(html);
    },
    agregarRawftype: function () {
        var html = '<tr><td><input name="INPUT_RAW_FILETYPES[]" value="" class="fieldform" style="margin-bottom: 1px; width: 125px;"/></td><td></td></tr>';
        $('#rawftype_listado').append(html);
    },
    agregarUrlftype: function () {
        var html = '<tr><td><input name="INPUT_URL_FILETYPES[]" value="" class="fieldform" style="margin-bottom: 1px; width: 125px;"/></td><td></td></tr>';
        $('#urlftype_listado').append(html);
    },
    agregarTextvar: function () {
        var html = '<tr><td><input name="INPUT_TEXTVARS[]" value="" class="fieldform" style="margin-bottom: 1px; width: 125px;"/></td><td></td></tr>';
        $('#textvars_listado').append(html);
    },
    agregarVarnish: function () {
        var html = '<input name="INPUT_VARNISH_SERVER_NAME[]" value="" class="fieldform" style="margin-bottom: 1px; width: 89%;"/>';
        $('#varnish_list').append(html);
    },
    agregarCluster: function () {
        var html = '<input name="INPUT_CLUSTERING_SERVER[]" value="" class="fieldform" style="margin-bottom: 1px; width: 89%;"/>';
        $('#clustering_list').append(html);
    },
    mostrarPermitidos: function () {
        $('input[name="UPLOADS_PERMITIDOS"]').toggle();
    },
    quitarFid: function (obj, id) {
        if ($(obj).is(':checked')) {
            // Deshabilitar inputs, para que no sean enviados en el formulario.
            $('input[name="nombrefid_' + id + '"]').attr("disabled", "disabled").addClass('disabled-field');
            $('input[name="archivofid_' + id + '"]').attr("disabled", "disabled").addClass('disabled-field');
            $('select[name="plantillasfid_' + id + '"]').attr("disabled", "disabled").addClass('disabled-field');
            $('select[name="plantillasfid_pla_' + id + '"]').attr("disabled", "disabled").addClass('disabled-field');

        } else {
            $('input[name="nombrefid_' + id + '"]').removeAttr("disabled").removeClass('disabled-field');
            $('input[name="archivofid_' + id + '"]').removeAttr("disabled").removeClass('disabled-field');
            $('select[name="plantillasfid_' + id + '"]').removeAttr("disabled").removeClass('disabled-field');
            $('select[name="plantillasfid_pla_' + id + '"]').removeAttr("disabled").removeClass('disabled-field');
        }
    },
    quitarPortada: function (obj, id) {
        if ($(obj).is(':checked')) {
            // Deshabilitar inputs, para que no sean enviados en el formulario.
            $('input[name="portada_' + id + '"]').attr("disabled", "disabled").addClass('disabled-field');
            $('select[name="plt_paralelas_' + id + '"]').attr("disabled", "disabled").addClass('disabled-field');
            $('select[name="plt_preview_' + id + '"]').attr("disabled", "disabled").addClass('disabled-field');
        } else {
            $('input[name="portada_' + id + '"]').removeAttr("disabled").removeClass('disabled-field');
            $('select[name="plt_paralelas_' + id + '"]').removeAttr("disabled").removeClass('disabled-field');
            $('select[name="plt_preview_' + id + '"]').removeAttr("disabled").removeClass('disabled-field');
        }
    },
    quitarBaseport: function (obj, id) {
        if ($(obj).is(':checked')) {
            // Deshabilitar inputs, para que no sean enviados en el formulario.
            $('#baseport_' + id).attr("disabled", "disabled").addClass('disabled-field');
        } else {
            $('#baseport_' + id).removeAttr("disabled").removeClass('disabled-field');
        }
    },
    quitarPortDD: function (obj, id) {
        if ($(obj).is(':checked')) {
            // Deshabilitar inputs, para que no sean enviados en el formulario.
            $('#portdd_' + id).attr("disabled", "disabled").addClass('disabled-field');
        } else {
            $('#portdd_' + id).removeAttr("disabled").removeClass('disabled-field');
        }
    },
    quitarMV: function (obj, id) {
        if ($(obj).is(':checked')) {
            // Deshabilitar inputs, para que no sean enviados en el formulario.
            $('#mv_' + id).attr("disabled", "disabled").addClass('disabled-field');
        } else {
            $('#mv_' + id).removeAttr("disabled").removeClass('disabled-field');
        }
    },
    quitarProntusDir: function (obj, id) {
        if ($(obj).is(':checked')) {
            // Deshabilitar inputs, para que no sean enviados en el formulario.
            $('#prontusdir_' + id).attr("disabled", "disabled").addClass('disabled-field');
        } else {
            $('#prontusdir_' + id).removeAttr("disabled").removeClass('disabled-field');
        }
    },
    quitarRawDir: function (obj, id) {
        if ($(obj).is(':checked')) {
            // Deshabilitar inputs, para que no sean enviados en el formulario.
            $('#rawdir_' + id).attr("disabled", "disabled").addClass('disabled-field');
        } else {
            $('#rawdir_' + id).removeAttr("disabled").removeClass('disabled-field');
        }
    },
    quitarRawftype: function (obj, id) {
        if ($(obj).is(':checked')) {
            // Deshabilitar inputs, para que no sean enviados en el formulario.
            $('#rawftype_' + id).attr("disabled", "disabled").addClass('disabled-field');
        } else {
            $('#rawftype_' + id).removeAttr("disabled").removeClass('disabled-field');
        }
    },
    quitarUrlftype: function (obj, id) {
        if ($(obj).is(':checked')) {
            // Deshabilitar inputs, para que no sean enviados en el formulario.
            $('#urlftype_' + id).attr("disabled", "disabled").addClass('disabled-field');
        } else {
            $('#urlftype_' + id).removeAttr("disabled").removeClass('disabled-field');
        }
    },
    quitarTextvar: function (obj, id) {
        if ($(obj).is(':checked')) {
            // Deshabilitar inputs, para que no sean enviados en el formulario.
            $('#textvar_' + id).attr("disabled", "disabled").addClass('disabled-field');
        } else {
            $('#textvar_' + id).removeAttr("disabled").removeClass('disabled-field');
        }
    },
    // Cambia de multiple a single y viceversa.
    toggleCombo: function (obj, id) {
        var obj_sel = $('select[name="' + id + '"]');
        if ($(obj_sel).attr("multiple")) {
            // Es multiple, convertirlo en "single"
            $(obj_sel).removeAttr("multiple");
            $(obj).attr("src", (($(obj).attr("src")).replace('men_of', 'mas_of')));
        } else {
            $(obj_sel).attr("multiple", "multiple");
            $(obj).attr("src", (($(obj).attr("src")).replace('mas_of', 'men_of')));
        }
    },
    toggleMultiedicion: function () {
        if ($('#tr_multiedicion').is(':visible')) {
            $('#tr_multiedicion').hide();
            // Desactivar inputs para sacarlos del cfg.
            $('input[name="INPUT_BASE_PORTS[]"]').attr("disabled", "disabled");
        } else {
            $('#tr_multiedicion').show();
            $('input[name="INPUT_BASE_PORTS[]"]').removeAttr("disabled");
        }
    },
    comentEnviarPub: function () {
        if ($('.enviar_publicacion').is(':visible')) {
            $('.enviar_publicacion').hide();
            $('input[name="MAIL_PUBLICACION_ASUNTO"]').attr("disabled", "disabled");
            $('input[name="MAIL_PUBLICACION_FROM"]').attr("disabled", "disabled");
            $('input[name="MAIL_PUBLICACION_SMTP"]').attr("disabled", "disabled");
        } else {
            $('.enviar_publicacion').show();
            $('input[name="MAIL_PUBLICACION_ASUNTO"]').removeAttr("disabled");
            $('input[name="MAIL_PUBLICACION_FROM"]').removeAttr("disabled");
            $('input[name="MAIL_PUBLICACION_SMTP"]').removeAttr("disabled");
        }
    },

    // Duplicar, utilizando el primero elemento como plantilla.
    agregarPortada: function () {
        var obj = $('#plt_new_port').clone();
        $(obj).attr("id", "");
        $(obj).find('.botones').remove();
        var id = '';
        var new_id = '';

        if (Cfgedit.newPortLastId == 0) {
            id = $(obj).find('select[name^="portada_"]').attr("name");
            var new_id = id.replace("portada_", "");
            new_id = parseInt(new_id);
            new_id = new_id + 1;
            Cfgedit.newPortLastId = new_id;
        } else {
            id = Cfgedit.newPortLastId;
            new_id = id + 1;
            Cfgedit.newPortLastId = new_id;
        }


        $(obj).find('select[name^="portada_"]').attr("name", "portada_" + new_id);
        $(obj).find('select[id^="portada_"]').attr("id", "portada_" + new_id);
        $(obj).find('input[name^="nom_portada_"]').attr("name", "nom_portada_" + new_id);
        $(obj).find('input[name^="nom_portada_"]').val('');
        $(obj).find('select[name^="plt_preview_"]').attr("name", "plt_preview_" + new_id);
        $(obj).find('select[id^="plt_preview_"]').attr("id", "plt_preview_" + new_id);
        $(obj).find('select[name^="plt_paralelas_"]').attr("name", "plt_paralelas_" + new_id);
        $(obj).find('select[id^="plt_paralelas_"]').attr("id", "plt_paralelas_" + new_id);
        $(obj).find('.selmultiple').attr("onclick", "Cfgedit.toggleCombo(this, 'plt_paralelas_" + new_id + "');");
        $(obj).find('select[name^="portada_"]').attr("onchange", "Cfgedit.setPortNom(this.value, '" + new_id + "');");
        $(obj).insertAfter("#plt_new_port");

    },

    setPortNom: function (value, id) {
        $('input[name="nom_portada_' + id + '"]').val(value);
    },

    showHelpCompatibilidad: function() {
        var obj = Opciones.optsDefault;
        //obj.href = Opciones.urlCheckPlat + '?prontus_id=' + Admin.prontus_id;
        obj.width = '600px';
        obj.height = '450px';
        obj.href = '/' + Admin.prontus_id + '/cpan/core/port_dd/compatibilidad.html'
        obj.onLoad = function() {
            Admin.mostrarBarraColorbox();
        };
        $.fn.colorbox(obj);
    },

};
