
var Acciones = {

    // -------------------------------------------------------------------------
    borrarArtic: function(obj, ts, btnover) {

        if(!confirm(ProntusLangController.getString('_action_art_delete_confirm'))) {
            return false;
        }

        var parent;
        if (typeof btnover != 'undefined') {
            parent = $(obj).parent().parent().parent().parent();
            $(parent).addClass('nohover');
            $(parent).find('.status').hide();
            $(parent).find('.autoinc').hide();
            $(parent).find('.botones').show();
        }

        $(obj).hide().next().show();
        var opts = {
            _path_conf: Listartic.path_conf,
            _ts: ts
        };

        setTimeout(function() {

            $.ajax({
                url: Listartic.urlBorrar,
                data: opts,
                dataType: 'json',
                cache: false,
                complete: function() {
                    $(obj).next().hide().prev().show();
                },
                error: function(XMLHttpRequest, textStatus, errorThrown) {
                    SubmitForm.handleError(Listartic.urlBorrar, XMLHttpRequest, textStatus, errorThrown);
                },
                success: function(resp, textStatus) {
                    if(typeof resp === 'undefined' || resp === null) {
                        Admin.displayMessage(ProntusLangController.getString('_action_art_delete_error'), 'error');
                    }
                    if(resp.status == 1) {
                        //Admin.displayMessage('Artículo eliminado');
                        $(obj).parents('.fila1').parent().fadeOut('slow');
                    } else {
                        //Admin.displayMessage(resp.msg, 'error');
                        alert(resp.msg+' '); // Para corregir caracter extraño en chrome
                        if (typeof btnover != 'undefined') {
                            $(parent).removeClass('nohover');
                            $(parent).find('.status').show();
                            $(parent).find('.autoinc').show();
                            $(parent).find('.botones').hide();
                        }
                    }
                }
            });

        }, 1000);
    },

    // -------------------------------------------------------------------------
    refrescarListados: function() {

        if(Listartic.modPort === false || confirm(Listartic.msgChangePortConfirm)) {

            Listartic.instalaPortModProtector(false);
            Admin.closeMessage();

            if(Listartic.saving === false) {
                // Se procesa el listado de la portada
                LoadDiv.refrescaListadoPub();
            }

            // Se procesa el listado de los no publicados
            LoadDiv.refrescaListadoNoPub();
        }
    },

    // -------------------------------------------------------------------------
    guardarPort: function() {

        // Si se está guardando no se hace nada
        if(Listartic.saving === true) {
            return;
        }
        // Si se está en modo carga, no se guarda
        if(Listartic.cargandoPub === true) {
            alert(ProntusLangController.getString('_action_port_save_wait_for_load'));
            return;
        }
        // La carga de la portada no se realizó como la gente
        if($('#_load_ok').size() < 1) {
            alert(ProntusLangController.getString('_action_port_save_wrong_load'));
            return;
        }


        Listartic.saving = true;

        $('#_accion').val('update');
        $('#_edic').val($('#cmb_edic').val());
        $('#_port').val($('#cmb_port').val());
        $('#_vista').val('');
        $('#_fecha_preview').val('');
        $('#_hora_preview').val('');

        var opts = {
            complete: function() {
                Listartic.saving = false;
                Acciones.muestraAcciones(true);
                //alert('complete externo...');
            },
            success: function(json) {
                if (json.status=='0') {
                    Admin.displayMessage(json.msg, 'error');
                    return;
                }
                Admin.displayMessage(ProntusLangController.getString('_action_port_save_success'), 'info');
                Listartic.instalaPortModProtector(false);

                if(Listartic.cargandoPub === false) {
                    // Se procesa el listado de la portada
                    LoadDiv.refrescaListadoPub();
                }
            }
        };
        var config = {
            formSelector: '#listado',
            actionURL: Listartic.urlGuardar
        };

        Acciones.muestraAcciones(false);
        SubmitForm.submitGenericAjax(config, opts);
        //Admin.displayMessage($('#listado').serialize(), 'info');

    },


    // -------------------------------------------------------------------------
    clusteringPort: function() {

        var opts = '?_edic='+$('#cmb_edic').val()+
            '&_port='+$('#cmb_port').val()+
            '&_prontus_id='+Admin.prontus_id;

        $.fn.colorbox({
                open: true,
                href: Listartic.urlRayo + opts,
                width: 500,
                height: 250,
                opacity: 0.8,
                iframe: true
        });
        return false;
    },

    // -------------------------------------------------------------------------
    showPort: function() {

        var edic = $('#cmb_edic').val();
        var port = $('#cmb_port').val();
        if(edic === '') {
            edic = 'base';
        }
        var url = '/' + Admin.prontus_id + '/site/edic/' + edic + '/port/' + port;
        window.open(url);
    },

    // -------------------------------------------------------------------------
    muestraAcciones: function(flag) {
        if(!flag) {
            $('.top-titulo.botones a').hide();
            $('.top-titulo.botones .loading-action').fadeIn();
        } else {
            $('.top-titulo.botones .loading-action').hide();
            $('.top-titulo.botones a').filter(':not("#port_dd_btn")').fadeIn();
        }
    },

    // -------------------------------------------------------------------------
    openDragAndDrop: function() {

        var port = $('#cmb_port').val();
        var edic = $('#cmb_edic').val();
        if(typeof edic === 'undefined' || edic === null) {
            edic = 'base';
        }
        var url = Listartic.urlDragAndDrop + '?_edic=' + edic + '&_port=' + port + '&_path_conf=' + Admin.path_conf;
        Utiles.subWin(url, 'portpreview', 1300, 640, 50, 50, 'scrollbars=1,resizable=1');
    },

    // -------------------------------------------------------------------------
    toggleVoBo: function (obj, ts) {
        var vb_input_obj = $('input[name="_vb_' + ts + '"]');
        var st_vb = $(vb_input_obj).val();

        var parent_obj = $(obj).parent()
        var parent_class = parent_obj.attr("class");

        if (parent_class == 'vobo') {
             var finder_obj = parent_obj.parent().parent();
        } else if (parent_class == 'voboboto') {
            var finder_obj = parent_obj.parent().parent().parent();
        }

        var img1_obj = $(finder_obj).find('.vobo').find('img');
        var img2_obj = $(finder_obj).find('.voboboto img');

        Admin.displayMessage(Listartic.msgChangePort, 'alert');

        Listartic.instalaPortModProtector(true);
        if (st_vb == 1) {
            // nopub
            var img_src = $(img1_obj).attr("src");
            var title = ProntusLangController.getString('_action_port_vobo_do_publish');
            img_src = img_src.replace("vobo_pub", "vobo_nopub");
            img1_obj.attr("src", img_src).attr("title", title).attr("alt", title);
            img2_obj.attr("src", img_src).attr("title", title).attr("alt", title);
            $(vb_input_obj).val(0);
        } else {
            // pub
            var img_src = $(img1_obj).attr("src");
            var title = ProntusLangController.getString('_action_port_vobo_dont_publish');
            img_src = img_src.replace("vobo_nopub", "vobo_pub");
            img1_obj.attr("src", img_src).attr("title", title).attr("alt", title);
            img2_obj.attr("src", img_src).attr("title", title).attr("alt", title);
            $(vb_input_obj).val(1);
        }
        Preview.startPreview();
    }

};
