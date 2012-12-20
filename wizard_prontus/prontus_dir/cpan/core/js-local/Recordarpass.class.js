var Recordarpass = {
    // -------------------------------------------------------------------------
    recordar: function(prontus_id, dir_cgi_cpan) {
        var configAjax = {
            formSelector: '#FrmRecordar',
            actionURL:  '/' + dir_cgi_cpan + '/prontus_recordarpass.cgi',
            redirURL:   '/'+prontus_id+'/cpan/core/prontus_index.html',
            okMsg:      'La nueva contraseña ha sido enviada a tu email registrado en Prontus.'
        };

        
        var optAjax = {
            complete: function() {
                Captcha.generate();
                $('.loading-action').hide();
                $('.botonIngresar').show();
            }
        };

        $('.loading-action').css({display: 'inline'});
        $('.botonIngresar').hide();
        SubmitForm.submitGenericAjax(configAjax, optAjax);
    }
};
