    
var Captcha = {
    
    nameCGI: 'prontus_captcha.cgi',
    defaultImageWidth: '85',
    defaultImageHeight: '45',
    refreshingCaptcha: false,
    
    properties: {
        type: '',
        pathCGI: 'cgi-cpn',
        idContent: '#prontus_captcha_content',
        msgSystem: 'Error en la implementación',
        msgCGI: 'Error al leer el captcha, intente de nuevo',
        msgType: 'Debe indicar el tipo de Captcha'
    },
    
    generate: function(prop) {
        
        if (typeof jQuery === 'undefined') {  
            alert(Captcha.properties.msgSystem);
            return;
        }
        if (typeof prop === 'undefined') {  
            prop = {};
        }
        $.extend(Captcha.properties, prop);
        
        if(Captcha.properties.type) {
            
            $.ajax({
                url: '/'+Captcha.properties.pathCGI+'/'+Captcha.nameCGI,
                data: {_type: Captcha.properties.type},
                dataType: 'json',
                error: function(jqXHR, textStatus, errorThrown) {
                    alert(Captcha.properties.msgCGI);
                },
                success: function(data, textStatus, jqXHR) {
                    if(typeof data !== 'undefined') {
                        if(data.msg == '') {
                            var relpathimg = data.path + data.img;
                            var imagen = '<img src="'+relpathimg+'" alt="captcha" width="'+Captcha.defaultImageWidth+'" height="'+Captcha.defaultImageHeight+'" />';
                            var input1 = '<input type="hidden" name="_captcha_img" value="'+data.img+'"/>';
                            var input2 = '<input type="hidden" name="_captcha_code" value="'+data.code+'"/>';
                            $(Captcha.properties.idContent).html(imagen+"\n"+input1+"\n"+input2);
                        } else if(typeof data.msg === 'undefined') {
                            alert(Captcha.properties.msgCGI);
                            
                        } else {
                            alert(data.msg);
                        }
                    };
                }
            });
        } else {
            alert(Captcha.properties.msgType);
            return;
        }
    },
    
	// -------------------------------------------------------------------------
    // Si onlyTypes se evalua como verdadero, en vez de imprimir el contenido de
    // los atributos, se impreme solo el tipo.  
    setRefreshCaptcha: function() {
		
		var timer = setTimeout(function() {
			var imagen = $(Captcha.properties.idContent).find('img').attr('src');
			$.ajax({
				url: imagen,
				type: 'HEAD',
				cache: false,
				error: function() {
					Captcha.generate();
				},
				success: function() {
					Captcha.setRefreshCaptcha();
				}
			});
		}, 250);
	}
};
