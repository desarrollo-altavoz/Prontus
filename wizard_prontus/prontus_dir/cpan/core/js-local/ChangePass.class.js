var ChangePass = {

    // -------------------------------------------------------------------------
    enviar: function(dir_cgi_cpan) {
        var configAjax = {
            formSelector: '#FrmChangePass',
            okMsg: 'Su contraseña ha sido cambiada correctamente',
            redirURL: 'prontus_index.html',
            actionURL: '/' + dir_cgi_cpan + '/prontus_changepass.cgi'
        };
        SubmitForm.submitGenericAjax(configAjax);
    }
};
