
var Wizard = {
    
    downloadingModel: false,
    
    /**
     * Funcion que inicia los pasos comunes.
     * Recibe como parámetro el paso que se va a ejecutar
     **/
    init: function(paso) {
        
        $('#link-check').click(function() {
            $.fn.colorbox({open:true, href: '/cgi-cpn/prontus_check_platform.cgi', width:'780px', height:'580px', maxWidth: '95%', maxHeight: '90%'});
        });
        $('#link-license').click(function() {
            $.fn.colorbox({open:true, href: '/wizard_prontus/prontus_dir/cpan/core/license/license.html', width:'750px', height:'580px', maxWidth: '95%', maxHeight: '90%'});
        });
        $('.help a').click(function() {
            Utiles.subWin('/wizard_prontus/core/ayuda.html#'+paso, paso, 480, 500, 500, 75);
        });
        
        // Chequea que se haya cargado realmente la variable del js anterior.
        if(paso) {
            if(typeof DIR_CGI_CPAN === 'undefined') {
                alert('Error al cargar elementos de la página, esto puede deberse a problemas de configuración, o bien, de velocidad en su conexión a internet.');
                window.location.href = '/wizard_prontus/';
            };
        };
        
        if(paso == 'paso1') {
            $('#form1').attr('action', '/' + DIR_CGI_CPAN + '/wizard_paso1.cgi');
            
        } else if(paso == 'paso2') {
            $('.modelo a').live('click', function() {
                var url = $(this).attr('href');
                $(this).colorbox({
                    open: true,
                    href: url,
                    width:'900px',
                    height:'650px',
                    iframe: true
                });
                return false;
            });
            
            $('.modelo:first').addClass('chequeado').find('input').attr('checked', 'checked');
            $('.modelo input').change(function() {
                $('.modelo').removeClass('chequeado');
                $(this).parents('.modelo').addClass('chequeado');
            });
            
        }
            
            
    },
    
    /**
     * Inicializa el link para desplegar la ayuda en algunos de los pasos del Wizard
     * El link a la ayuda se define en el botón correspondiente. Lo que hace este función
     * es setear el handler para abrirla en colorbox
     **/
    initHelp: function() {
        $('h3').bind('click', function() {
            $('.info p').hide();
            $(this).next().find('p').show();
        });
        
        $('.info p').hide();
        var paso = window.location.hash;
        if(paso) {
            paso = paso.replace('#', '');
            $('#titu-'+paso).trigger('click');
        } else {
            $('h3:first').trigger('click');
        }
    },
    
    /**
     * Inicializa el administrador de modelos.
     **/
    initAdminModels: function() {
        
        $('.screenshot a').each(function() {
            if($(this).attr('href') == $(this).find('img').attr('src')) {
                $(this).replaceWith($(this).find('img'));
                
            } else {
                $(this).colorbox();
            }
        });
        
        $('.description a').live('click', function() {
            var url = $(this).attr('href');
            //~ alert(url);
            $(this).colorbox({
                open: true,
                href: url,
                width:'900px',
                height:'650px',
                //scrolling: false,
                iframe: true
            });
            return false;
        });
        
    },
    
    /**
     * Gatilla la CGI para el chequeo de plataforma
     **/
    check_install: function() {
    
        var validator = new Validador('form1','one','#FDF8C1');
        validator.addconstraint('PRONTUS_ID','obligatorio','','Debe indicar el nombre del publicador.');
        validator.addconstraint('PRONTUS_ID','regex',new RegExp(/^[a-z][a-z0-9\_\-]+$/),'Nombre de publicador no válido. Debe tener letras minúsculas, números, guión o underscore.');
        
        if (!validator.validar()) {
            return false;
        };
        var urlcheck = '/' + DIR_CGI_CPAN + '/prontus_check_install.cgi?wizard=1&accion=1&_prontus_id=' + $('#prontus_id').val();
        $.fn.colorbox({open:true, href: urlcheck, width:'750px', height:'580px'});
    },

    /**
     * Validaciones para el áso numero 1
     * Luego de validar, envía el formulario para pasar al paso 2
     **/
    enviarPaso1: function() {
        
        var validator = new Validador('form1','one','#FDF8C1');
        validator.addconstraint('PRONTUS_ID','obligatorio','','Debe indicar el nombre del publicador.');
        validator.addconstraint('PRONTUS_ID','regex',new RegExp(/^[a-z][a-z0-9\_\-]+$/),'Nombre de publicador no válido. Debe comenzar con letra minúscula sin tilde y seguirle letras del mismo tipo o números, guión o underscore.');
        validator.addconstraint('NEW_TITLE_SITE_NAME','obligatorio','','Debe indicar el Nombre del Sitio Prontus.');
        validator.addconstraint('SERVER_BD','obligatorio','','Debe indicar el Servidor de BD');
        validator.addconstraint('SERVER_BD','regex',new RegExp(/^[\w\-\.]{1,128}$/),"Servidor de BD no es válido.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, punto, guión y underscore, máximo 128.");
        validator.addconstraint('NOM_BD','obligatorio','','Debe indicar el Nombre de BD');
        validator.addconstraint('NOM_BD','regex',new RegExp(/^[\w\-]{1,64}$/),"Nombre de BD no es válido.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, guión y underscore, máximo 64.");
        validator.addconstraint('USER_BD','obligatorio','','Debe indicar el Usuario de BD');
        validator.addconstraint('USER_BD','regex',new RegExp(/^[\w\-]{1,16}$/),"Usuario de BD no es válido.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, guión y underscore, máximo 16.");
        validator.addconstraint('PWD_BD','obligatorio','','Debe indicar la Contraseña para usuario de BD');
        validator.addconstraint('PWD_BD','regex',new RegExp(/^[\w\-]{1,16}$/),"Contraseña para usuario de BD no es válida.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, y los caracteres ., _, -, @, $, % y !, máximo 16.");
        
        /* para creacion BD */
        var superuser = $('input[name="SUPERUSER_BD"]').val();
        if (superuser !== "") {
            validator.addconstraint('SUPERUSER_BD','regex',new RegExp(/^[\w\-]{1,16}$/),"Usuario para creación de BD no es válido.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, guión y underscore, máximo 16.");
            validator.addconstraint('SUPERPWD_BD','obligatorio','','Debe indicar la Contraseña para creación de BD');
            validator.addconstraint('SUPERPWD_BD','regex',new RegExp(/^[\w\-\.\@\:\$%!]{1,16}$/),"Contraseña para creación de BD no es válida.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, guión y underscore, máximo 16.");
        };
        
        validator.addconstraint('PRONTUS_SMTP','obligatorio','','Debe indicar el servidor SMTP');
        validator.addconstraint('PRONTUS_SMTP','regex',new RegExp(/^[A-Z\.a-z\_\-0-9]+$/),"Servidor SMTP no válido.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, punto, guión y underscore.");
        
        if (!validator.validar()) {
            return false;
        };
        validator.send();
    },    
    
    /**
     * Validaciones y envío del paso 2
     * Luego de validar, envía el formulario para pasar al resumen
     **/
    enviarPaso2: function() {
        
        var validator = new Validador('form1','one','#FDF8C1');
        validator.addconstraint('PRONTUS_MODEL','obligatorio','','Debe indicar el Modelo Prontus que va a utilizar.');
                
        if (!validator.validar()) {
            return false;
        };
        validator.send();
    },
    
    /**
     * Gatilla la CGI que genera el Prontus, al final del Wizard
     * Por ahor asólo se hace un submit, pero a futuro se podrían agregar
     * validaciones o confirmaciones, etc
     **/
    enviarConfirmacion: function() {
        
        $('[name="form1"]').trigger('submit');
        
    },
    
    /**
     * Funcion encargada de volver al comienzo del Wizard.
     * Como ese se abre generalmente en una ventana normal, no se pude hacer window.close()
     * Se usa esta función, para centralizar el comportamiento del botón.
     **/
    cancelarWizard: function() {
        
        window.location.href='/wizard_prontus/';
        
    },
    
    /**
     * Centraliza la función de imprimir del Paso de Confirmación
     * Actualmente sólo realiza un window.print(), pero a futuro, se podría implementar
     * algo un poco más elaborado.
     **/
    imprimirResumen: function() {
        
        window.print();
    },
    
    /**
     * Muestra la ventana de administración de los modelos
     **/
    showDescargar: function() {
        
        window.location.href = 'wizard_show_models.cgi';
    },
    
    /**
     * Muestra el paso numero 2.
     * Se usa para volver, desde el resumen o el admin de modelos
     **/
    showPaso2: function() {
        
        window.location.href = 'wizard_show_paso2.cgi';
    },
    
    /**
     * Muestra el paso numero 2.
     * Se usa para volver, desde el paso 2
     **/
    showPaso1: function() {
        
        window.location.href = '/wizard_prontus/core/paso1.html';
    },
    
    /**
     * Handler utilizado en el Administrador de Modelos.
     * Recibe como parámetro el modelo que se desea eliminar
     * Invoca la CGI de borrado y luego borra el modelo del listado
     **/
    eliminarModelo: function(id) {
        
        if(confirm('¿Está seguro que desea eliminar este modelo?')) {
            
            if(Wizard.downloadingModel) {
                alert('Por favor, espere a que termine la descarga anterior');
                return;
            };
            Wizard.showLoading(id, true);
            var urlCGI = './wizard_models_delete.cgi';
            $.ajax({
                url: urlCGI,
                data: {
                    modelid: id
                },
                complete: function() {
                    Wizard.showLoading(id, false);
                },
                error: function(jqXHR, textStatus, errorThrown) {

                    Wizard.handleError(urlCGI, jqXHR, textStatus, errorThrown);

                },
                success: function(resp) {
                    if(typeof resp !== 'Object' && typeof resp !== 'object') {
                        alert('Respuesta no valida desde el servidor');
                        return;
                    }
                    if(resp.error) {
                        alert(resp.msg);
                        
                    } else {
                        if(resp.nodisponible) {
                            $('#idmodel-'+id).fadeOut(function() {
                                $(this).remove();
                            });
                        } else {
                            $('#idmodel-'+id).fadeOut('slow', function() {
                                $('#idmodel-'+id).insertAfter('#models .instalado:last').show();
                                $('#idmodel-'+id+' .version .actual').html('No instalado');
                                $('#idmodel-'+id).removeClass('actualizar').removeClass('actualizado').removeClass('nodisponible');
                                $('#idmodel-'+id).removeClass('instalado').addClass('noinstalado');
                            });
                        }
                    }
                }
            });
        }
    },
    
    /**
     * Metodo encargado de invocar la CGI que hace la descarga del modelo
     **/
    descargarModelo: function(id) {
        
        if(Wizard.downloadingModel) {
            alert('Por favor, espere a que termine la descarga anterior');
            return;
        }
        
        Wizard.showLoading(id, true);
        var urlCGI = './wizard_models_download.cgi';
        $.ajax({
            url: urlCGI,
            data: {
                modelid: id
                
            },
            complete: function() {
                Wizard.showLoading(id, false);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                
                Wizard.handleError(urlCGI, jqXHR, textStatus, errorThrown);
                
            },
            success: function(resp) {
                
                if(typeof resp !== 'Object' && typeof resp !== 'object') {
                    alert('Respuesta no valida desde el servidor');
                    return;
                }
                if(resp.error) {
                    alert(resp.msg);
                    
                } else {
                    var offset = $('#models').offset();
                    $('html, body').animate({scrollTop: offset.top}, 'fast');
                    $('#idmodel-'+id).fadeOut('slow', function() {
                        $('#idmodel-'+id).insertAfter('#models tr:first').show();
                        
                        $('#idmodel-'+id+' .version .actual').html($('#idmodel-'+id+' .version .last').html());
                        $('#idmodel-'+id).removeClass('noinstalado').addClass('instalado')
                        $('#idmodel-'+id).addClass('actualizado');
                        
                        var color = $('#idmodel-'+id+' td').css('background-color');
                        $('#idmodel-'+id+' td').css('background-color', '#F0E0D0');
                        setTimeout(function() {
                            $('#idmodel-'+id+' td').css('background-color', '');
                        }, 1500);
                    });

                }
               
            }
            
        });
        
    },
    
    /**
     * Este metodo se usa para Actualizar un modelo
     * Pese a que usa la misma CGI de descarga, el comportamiento post descarga es distinto
     **/
    actualizarModelo: function(id) {
        
        if(Wizard.downloadingModel) {
            alert('Por favor, espere a que termine la descarga anterior');
            return;
        }
        
        Wizard.showLoading(id, true);
        var urlCGI = './wizard_models_download.cgi';
        $.ajax({
            url: urlCGI,
            data: {
                modelid: id
                
            },
            complete: function() {
                Wizard.showLoading(id, false);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                Wizard.handleError(urlCGI, jqXHR, textStatus, errorThrown);
            },
            success: function(resp) {
                
                if(typeof resp !== 'Object' && typeof resp !== 'object') {
                    alert('Respuesta no valida desde el servidor');
                    return;
                }
                if(resp.error) {
                    alert(resp.msg);
                    
                } else {
                    $('#idmodel-'+id+' .version .actual').html($('#idmodel-'+id+' .version .last').html());
                    $('#idmodel-'+id+'').removeClass('actualizar').addClass('actualizado');
                    //~ $('#idmodel-'+id+' .version .status').html('Actualizado');
                    //$('#idmodel-'+id).removeClass('noinstalado').addClass('instalado');
                    //~ $('#idmodel-'+id+' .actualizar').removeClass('actualizable');
                    
                }
            }
        });
    },
    
    /**
     * Para manejar el evento de descarga. Se centraliza en este método
     * la lógica de "bloquear" la interface mientras está descargando
     **/
    showLoading: function(id, flag) {
        
        if(flag) {
            Wizard.downloadingModel = true;
            $("#idmodel-"+id+' .acciones .content-buttons').hide();
            $("#idmodel-"+id+' .acciones .content-loading').show();
            
        } else {
            Wizard.downloadingModel = false;
            $("#idmodel-"+id+' .acciones .content-buttons').show();
            $("#idmodel-"+id+' .acciones .content-loading').hide();
        }
    },
    
    /**
     * Funcion encargada de manejar el error que viene de las respuestas Ajax
     * Se deja centralizado para cambiar el tipo de manejo en caso necesario
     **/
    handleError: function(url, XMLHttpRequest, textStatus, errorThrown) {
        
        alert("Server error procesando request ajax:\nURL invocada:"
                + url + "\ntextStatus="
                + textStatus + "\nXMLHttpRequest.status="
                + XMLHttpRequest.status + '-' + XMLHttpRequest.statusText
                + "\nXMLHttpRequest.responseText=[" + XMLHttpRequest.responseText
                + "]\nResponseHeaders=" + XMLHttpRequest.getAllResponseHeaders());
    }
}
