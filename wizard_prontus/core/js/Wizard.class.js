
var Wizard = {
    
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
        }       
    },
    
    // -----------------------------------------------------------------    
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
    
    // -----------------------------------------------------------------
    initDescarga: function() {
        
        $('.screenshot').colorbox();
        $('.description').live('click', function() {
            var url = $(this).attr('href');
            var name = $(this).attr('rel');
            Utiles.subWin(url, name, 730, 700, 500, 75);
        });
        
    },
    
    // -----------------------------------------------------------------
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
    
    enviarPaso2: function() {
        
    },
    
    cancelarWizard: function() {
        
        window.location.href='/wizard_prontus/';
        
    },
    
    showDescargar: function() {
        
        window.location.href = 'wizard_show_descargar.cgi';
    },
    
    showPaso2: function() {
        
        window.location.href = 'wizard_show_paso2.cgi';
    },
    showPaso1: function() {
        
        window.location.href = '/wizard_prontus/core/paso1.html';
    }
    
    
    
    
}
