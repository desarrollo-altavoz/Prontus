
var Preview = {
    isOpen: false,
    isBussy: false,
    urlPreview: './prontus_art_public.cgi',

    // -------------------------------------------------------------------------
    previewNewWin: function() {
        // Se comprueba que el preview no esté gatillando un request anterior
        if(Preview.isBussy) {
            alert("open");
            return;
        }
        Preview.isBussy = true;

        //Valida Fecha Hora
        var fecha = $('#fecha_preview').val();
        var hora = $('#hora_preview').val();
        if(!Admin.validaFecha(fecha)) {
            Admin.displayMessage('La fecha no es válida, no se puede calcular el Preview', 'alert');
            //alert('La fecha no es válida, no se puede calcular el Preview');
            return;
        }
        if(!Admin.validaHora(hora)) {
            Admin.displayMessage('La hora no es válida, no se puede calcular el Preview', 'alert');
            //alert('La hora no es válida, no se puede calcular el Preview');
            return;
        }

        $('#_accion').val('preview');
        $('#_edic').val($('#cmb_edic').val());
        $('#_port').val($('#cmb_port').val());
        $('#_vista').val($('#cmb_vista').val());
        $('#_fecha_preview').val($('#fecha_preview').val());
        $('#_hora_preview').val($('#hora_preview').val());

        var opts = {
            complete: function() {
                Preview.isBussy = false;
            },
            success: function(resp, textStatus) {
                if(textStatus == 'success') {
                    if(resp.status == 1) {
                        //~ $('#theIframe').attr('src', resp.msg);
                        var respuesta = resp.msg;
                        if (respuesta !== '') {
                            Utiles.subWin(respuesta, 'Preview'+$('#_port').val());
                        }
                    } else {
                        Admin.displayMessage(resp.msg, 'error');
                    }
                } else {
                    Admin.displayMessage('Se produjo un error al intentar recargar el preview', 'error');
                }
            }
        };
        var config = {
            formSelector: '#listado',
            actionURL: Preview.urlPreview
        };

        //Acciones.muestraAcciones(false);
        SubmitForm.submitGenericAjax(config, opts);
    }
};
