
var PortAdmin = {
        
    duplicar: function () {
    
        if ($('select[name="Lst_PORT3"] option:selected').length) {
            var plantillaSel = $('select[name="Lst_PORT3"] option:selected').val();
            var newport = prompt(ProntusLangController.getString('_portadmin_prompt_new_template', {'template': plantillaSel}), '');
            if (newport) {
                var expr = /^[a-z\_0-9][a-z\_\-0-9]*\.[a-z\_0-9\-]+$/;
                var found = expr.exec(newport);
                if (!found) {
                    alert(ProntusLangController.getString('_portadmin_invalid_template_name'));
                } else {
                    $('input[name="NEW_PORT"]').val(newport);
                    var configAjax = {
                        formSelector: '#frmDuplicar',
                        actionURL: '/' + Intercambio.dir_cgi_cpan + '/prontus_pltport_duplicar.cgi',
                    };
                    var opts = {
                        complete: function () {
                            parent.Opciones.cerrarColorbox();
                            window.location.reload();
                        },
                        success: function (json) {
                            alert(json.msg);
                        }
                    };
                    SubmitForm.submitGenericAjax(configAjax, opts);
                }
            };
        } else {
            alert(ProntusLangController.getString('_portadmin_duplicate_port_required'));
        }
    },
    borrar: function () {
    
        if ($('select[name="Lst_PORT4"] option:selected').length) {
            if (confirm(ProntusLangController.getString('_portadmin_delete_port_confirm'))) {
                var configAjax = {
                    formSelector: '#frmBorrar',
                    actionURL: '/' + Intercambio.dir_cgi_cpan + '/prontus_pltport_borrar.cgi',
                };
                
                var opts = {
                    complete: function () {
                        parent.Opciones.cerrarColorbox();
                        window.location.reload();
                    },
                    success: function (json) {
                        alert(json.msg);
                    },
                };
                SubmitForm.submitGenericAjax(configAjax, opts);
            };
        } else {
            alert(ProntusLangController.getString('_portadmin_delete_port_required'));
        }
    }
};
