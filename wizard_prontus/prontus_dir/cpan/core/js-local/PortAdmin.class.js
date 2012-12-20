
var PortAdmin = {
        
    duplicar: function () {
    
        if ($('select[name="Lst_PORT3"] option:selected').length) {
            var newport = prompt('Plantilla Origen: ' + $('select[name="Lst_PORT3"] option:selected').val() + '\nIngrese el nombre de la nueva plantilla, ejemplo: politica.html', '');
            if (newport) {
                var expr = /^[a-z\_0-9][a-z\_\-0-9]*\.[a-z\_0-9\-]+$/;
                var found = expr.exec(newport);
                if (!found) {
                    alert('Nombre de plantilla no válido.\nDebe comenzar con letra, número o underscore.\nCaracteres permitidos:letras minúsculas, dígitos, guión y underscore más el punto para la extensión, la cual es obligatoria.');
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
            alert("Por favor, seleccione una portada para duplicar.");
        }
    },
    borrar: function () {
    
        if ($('select[name="Lst_PORT4"] option:selected').length) {
            if (confirm("¿Está seguro de eliminar esta Portada?")) {
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
            alert("Por favor, seleccione una portada para borrar.");
        }
    }
};
