var Intercambio = {
    init: function () {
        $('select[name="Lst_PORT2"]').change(function () {
            if ($(this).val() == $('select[name="Lst_PORT1"]').val()) {
                $('select[name="Lst_PORT2"]').val('');
            };
        });
        $('select[name="Lst_PORT1"]').change(function () {
            if ($(this).val() == $('select[name="Lst_PORT2"]').val()) {
                $('select[name="Lst_PORT1"]').val('');
            };
        });
    },
    cambiar: function () {
        if ($('select[name="Lst_PORT1"] option:selected').length && $('select[name="Lst_PORT2"] option:selected').length) {
            if ($('select[name="Lst_PORT1"]').val() == $('select[name="Lst_PORT2"]').val()) {
                alert(ProntusLangController.getString('_exchange_cant_exchange_self'));
            } else {
                var configAjax = {
                    formSelector: '#frmIntercambio',
                    actionURL: '/' + Intercambio.dir_cgi_cpan + '/prontus_pltport_saveintercambio.cgi',
                    redirURL: '_self',
                    okMsg: ProntusLangController.getString('_exchange_success')
                };
                SubmitForm.submitGenericAjax(configAjax);
            };
        } else {
            alert(ProntusLangController.getString('_exchange_incomplete_selection'));
        }
    }
};
