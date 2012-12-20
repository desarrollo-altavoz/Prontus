var Ayuda = {

    textos: new Array(
            'Inicio',
            'Acceso a Prontus',
            'Administrador de artículos',
            'Administrador de artículos',
            'Administrador de artículos',
            'Administrador de artículos',
            'Publicar un artículo (1)',
            'Publicar un artículo (2)',
            'Publicar un artículo (3)'
    ),

    cambiarTitulo: function (tit) {
        $('#ayuda_titulo').text(tit);
    },

    enviarComentario: function () {
        $('.boton-gris3').hide();
        $('#loadingcom').show();

        var options = {
            url:        'prontus_help_sbmitcom.cgi',
            type:       'POST',
            dataType:   'json',
            success: function (data) {
                if (data.status == '0') {
                    alert(data.msg);
                } else {
                    alert(data.msg);
                    $('#frmComentario').find('input[type="text"]').val('');
                    $('#frmComentario').find('input[type="file"]').val('');
                    $('#frmComentario').find('textarea').val('');
                    $('#frmComentario').find('select').val('');
                    $('#report_error_ayuda').hide();
                    $('#opt1').attr("checked", "checked");
                }
                $('.boton-gris3').show();
                $('#loadingcom').hide();
            },
            error: function () {
                alert('Ocurrio un error, intentelo nuevamente.');
                $('.boton-gris3').show();
                $('#loadingcom').hide();
            }
        };

        $('#frmComentario').ajaxSubmit(options);
    },

    actualizarTexto: function () {
        var selected = $('select[name="tipomsg"]').val();
        var str;
        if (selected === 'Reporte de Error') {
            $('#report_error_ayuda').show();
        } else {
            $('#report_error_ayuda').hide();
        }
    },

    guiaReporte: function () {
        var str;
        str  = "** Guía de reporte de errores **\n\n";
        str += "Para reportar un error, completar el mensaje con la siguiente información:\n\n";
        str += "* Asunto: Resumen del problema, por ejemplo, 'No se pueden subir fotos'.\n";
        str += "* Texto: Descripción del problema lo más detallado posible, incluir idealmente los pasos para reproducir el problema y los datos utilizados.\n";

        alert(str);
    }
};
