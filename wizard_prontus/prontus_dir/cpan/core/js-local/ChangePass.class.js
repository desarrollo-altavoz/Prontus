var ChangePass = {

    // -------------------------------------------------------------------------
    enviar: function(dir_cgi_cpan) {
        $('.loading-action').show();
        $('.boton-gris3').hide();
        var configAjax = {
            formSelector: '#FrmChangePass',
            actionURL: '/' + dir_cgi_cpan + '/prontus_changepass.cgi'
        };
        var optsAjax = {
            success:   function(json, statusText) {
                if(json === null) {
                    return;
                };
                if (json.status == '1') {
                    if (typeof json.msg != 'undefined' && json.msg != '') {
                        alert(unescape(json.msg));
                    }
                    window.location.href = '/' + ProntusDetect.getIdProntus() + '/cpan/core/prontus_index.html';
                } else  {
                    alert(unescape(json.msg));
                    $('.loading-action').hide();
                    $('.boton-gris3').show();
                }
            }, // success
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                SubmitForm.handleError(configAjax.actionURL, XMLHttpRequest, textStatus, errorThrown);
            }
        };
        
        SubmitForm.submitGenericAjax(configAjax, optsAjax);
    }
};
