var Recordarpass = {
    // -------------------------------------------------------------------------
    recordar: function(prontus_id, dir_cgi_cpan) {
        var configAjax = {
            formSelector: '#FrmRecordar',
            actionURL:  '/' + dir_cgi_cpan + '/prontus_recordarpass.cgi',
            redirURL:   '/'+prontus_id+'/cpan/core/prontus_index.html',
            okMsg:      ProntusLangController.getString('_remember_pass_new_pass_sent')
        };

        
        var optAjax = {
            success: function (data) {
                if (typeof data.status != 'undefined') {
                    if (data.status == '0') {
                        alert(data.msg);
                        Captcha.generate();
                        $('.loading-action').hide();
                        $('.botonIngresar').show();
                    } else if (data.status == '1') {
                        alert(data.msg);
                        window.location.href = configAjax.redirURL;
                    }
                }
            }
        };

        $('.loading-action').css({display: 'inline'});
        $('.botonIngresar').hide();
        SubmitForm.submitGenericAjax(configAjax, optAjax);
    }
};
