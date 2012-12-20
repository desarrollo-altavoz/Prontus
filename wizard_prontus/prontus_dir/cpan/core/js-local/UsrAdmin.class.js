
var UsrAdmin = {
    dir_gi_cpan: "",
    path_conf: "",
    prontus_id: "",
    widthNormal: 740,
    heightNormal: 680,
    widthAdmin: 735,
    heightAdmin: 390,
    idAdmin: 1,

    // -------------------------------------------------------------------------
    cargarFicha: function(id) {
        var url;
        var new_width = UsrAdmin.widthNormal;
        var new_height = UsrAdmin.heightNormal;

        if (typeof id === 'undefined') {
            url = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_ficha.cgi?_path_conf='+UsrAdmin.path_conf;
        } else {
            url = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_ficha.cgi?_path_conf='+UsrAdmin.path_conf+'&USERS_ID='+id;
        }

        if (id == UsrAdmin.idAdmin) {
            new_width = UsrAdmin.widthAdmin;
            new_height = UsrAdmin.heightAdmin;
        }

        $.fn.colorbox({
            open: true,
            href: url,
            width: new_width,
            height: new_height,
            maxWidth: '95%',
            maxHeight: '90%',
            opacity: 0.8
            // iframe: true,
        });
    },
    // -------------------------------------------------------------------------
    borrar: function(id) {
        var msg = '¿Está seguro de borrar a este usuario?';
        if (confirm(msg)) {
            $.ajax({
                url:        '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_borrar.cgi',
                type:       'POST',
                dataType:   'json',
                data:       '_id='+id+'&_path_conf='+UsrAdmin.path_conf,
                success: function(data) {
                    if (data.status == '0') {
                        alert(data.msg);
                    } else {
                        $('#item-user-'+id).fadeOut('slow', function() {
                            $(this).remove();
                        });
                    }
                },
                error: function() {
                    alert('Ocurrio un error, inténtelo nuevamente.');
                }
            });
        }
    },
    
    // -------------------------------------------------------------------------
    guardarFicha: function(id) {

        var msg = '¿Está seguro que desea guardar sus datos?';
        if (id == UsrAdmin.idAdmin && ! confirm(msg)) {
            return false;
        };

        var configAjax = {
            formSelector: '#frmUsrFicha',
            actionURL: '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_sbmit.cgi'
        };

        var optsAjax = {
            success:   function(json, statusText) {
                if (json.status == '1' && json.msg === '') {
                    if (id == UsrAdmin.idAdmin) {
                        window.location.href = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_logout.cgi?_path_conf=' + UsrAdmin.path_conf;
                    } else {
                        window.location.href = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_admin.cgi?_path_conf='+UsrAdmin.path_conf;
                    }
                } else if (json.status == '1' && json.msg !== '') {
                    alert(json.msg);
                    if (id == UsrAdmin.idAdmin) {
                        window.location.href = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_logout.cgi?_path_conf=' + UsrAdmin.path_conf;
                    } else {
                        window.location.href = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_admin.cgi?_path_conf='+UsrAdmin.path_conf;
                    }
                } else if (json.status == '0') {
                    alert(json.msg);
                }
            }, // success
            complete: function() {
                /* Cargando... */
            }
        };
        SubmitForm.submitGenericAjax(configAjax, optsAjax);
    },
    
    // -------------------------------------------------------------------------
    guardarChgPass: function() {

        var configAjax = {
            formSelector: '#frmChgPass',
            actionURL: '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_chgpass_sbmit.cgi'
        };

        var optsAjax = {
            success:   function(json, statusText) {
                if (json.status == '1' && json.msg === '') {
                    window.location.href = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_logout.cgi?_path_conf=' + UsrAdmin.path_conf;
                } else if (json.status == '1' && json.msg !== '') {
                    alert(json.msg);
                    window.location.href = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_logout.cgi?_path_conf=' + UsrAdmin.path_conf;
                } else if (json.status == '0') {
                    alert(json.msg);
                }
            }, // success
            complete: function() {
                /* Cargando... */
            }
        };
        
        SubmitForm.submitGenericAjax(configAjax, optsAjax);
    },
    
    // -------------------------------------------------------------------------
    chgImgSrc: function(obj, img) {
        $(obj).attr("src", img);
    },
    
    // -------------------------------------------------------------------------
    toggleChecked: function (o) {
        if ($(o).is(':checked')) {
            $(o).parent().find('label').addClass('checked');
        } else {
            $(o).parent().find('label').removeClass('checked');
        }
    }
    
};
