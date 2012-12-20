
var EdiAdmin = {
    dir_gi_cpan: "",
    path_conf: "",
    prontus_id: "",

    // -------------------------------------------------------------------------
    cargarFicha: function(id) {
        var url;

        if (typeof id === 'undefined') {
            url = '/' + EdiAdmin.dir_cgi_cpan + '/prontus_edi_ficha.cgi?_path_conf='+EdiAdmin.path_conf;
        } else {
            url = '/' + EdiAdmin.dir_cgi_cpan + '/prontus_edi_ficha.cgi?_path_conf='+EdiAdmin.path_conf+'&_edic='+id;
        }

        $.fn.colorbox({
            open: true,
            href: url,
            width: 460,
            height: 280,
            opacity: 0.8
        });
    },

    // -------------------------------------------------------------------------
    guardarFicha: function(id) {
        var configAjax = {
            formSelector: '#frmEdiFicha',
            actionURL: '/' + EdiAdmin.dir_cgi_cpan + '/prontus_edi_guardar.cgi?_path_conf='+EdiAdmin.path_conf
        };

        var optsAjax = {
            success:   function(json, statusText) {
                if (json.status == '1' && json.msg === '') {
                    window.location.href = '/' + EdiAdmin.dir_cgi_cpan + '/prontus_edi_admin.cgi?_path_conf='+EdiAdmin.path_conf;
                } else if (json.status == '1' && json.msg !== '') {
                    alert(json.msg);
                    $('.botones').show();
                    $('.fila_loading').hide();
                    window.location.href = '/' + EdiAdmin.dir_cgi_cpan + '/prontus_edi_admin.cgi?_path_conf'+EdiAdmin.path_conf;
                } else if (json.status === 0) {
                    alert(json.msg);
                    $('.botones').show();
                    $('.fila_loading').hide();
                }
            } // success
        };
        $('.botones').hide();
        $('.fila_loading').fadeIn('slow');
        SubmitForm.submitGenericAjax(configAjax, optsAjax);
    },

    // -------------------------------------------------------------------------
    actualizarVigencia: function(id) {

    },

    // -------------------------------------------------------------------------
    chgImgSrc: function(obj, img) {
        $(obj).attr("src", img);
    },

    // -------------------------------------------------------------------------
    borrar: function(id) {
        var msg = '¿Estás seguro de borrar esta edición?';
        if (confirm(msg)) {
            var form_data = '_edic='+id+'&_path_conf='+EdiAdmin.path_conf;
            $.ajax({
                url:        '/' + EdiAdmin.dir_cgi_cpan + '/prontus_edi_borrar.cgi',
                type:       'POST',
                dataType:   'json',
                data:       form_data,
                success: function(data) {
                    if (data.status == '0') {
                        alert(data.msg);
                    } else {
                        $('#item-edic-'+id).fadeOut('slow', function() {
                            $(this).remove();
                        });
                    }
                },
                error: function() {
                }
            });
        }
    }

};
