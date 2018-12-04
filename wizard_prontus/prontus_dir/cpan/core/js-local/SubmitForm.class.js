
var SubmitForm = {

    // -----------------------------------------------------------------------------
    // Resetea un formulario. Recibe como parametro el ID del formulario
    resetForm: function(theId) {
        var theForm = document.getElementById(theId);
        if(theForm) {
            theForm.reset();
        }
    },

    // -------------------------------------------------------------------
    submitGenericAjax: function(config, opts) {
        // Requiere jquery.form.js
        // http://malsup.com/jquery/form/#code-samples

        if((typeof config.formSelector === 'undefined')) {
            return;
        }

        if((typeof config.actionURL === 'undefined')) {
            config.actionURL = $(config.formSelector).attr('action');
        }

        // Url a la que se debe redireccionar de vuelta del post, opcional
        config.redirURL = (typeof config.redirURL === 'undefined') ? '' : config.redirURL;

        // Msg de confirmacion, opcional
        config.okMsg = (typeof config.okMsg == 'undefined') ? '' : config.okMsg;

        // Peticion ajax
        var options = {
            url:       config.actionURL,         // override for form's 'action' attribute
            dataType:  'json',        // 'xml', 'script', or 'json' (expected server response type)
            complete: function() {
                //alert('complete interno... ');
            },
            error:   function(XMLHttpRequest, textStatus, errorThrown) {
                SubmitForm.handleError(config.actionURL, XMLHttpRequest, textStatus, errorThrown);
            },
            success:   function(json, statusText) {   // post-submit callback
                // $("#reloj").hide();
                // $("#botones_ficha").show();
                if (json.status=='0') {
                    alert(unescape(json.msg));
                } else {
                    if (config.okMsg !== '') {
                        alert(config.okMsg);
                    }
                    // Si se seteo una url dsde la cgi (debe venir con urlencode()!!), direcciona a ella
                    // Sino, ve si se seteo una por js y direcciona a ella
                    var redirURLFromServer = (typeof json.redirURL === 'undefined') ? '' : json.redirURL;
                    redirURLFromServer = unescape(redirURLFromServer);
                    if (redirURLFromServer !== '') {
                        window.location.href = redirURLFromServer;
                    } else if (config.redirURL == '_self') {
                        window.location.reload();
                    } else if (config.redirURL !== '') {
                        window.location.href = config.redirURL;
                    }
                }
                return false;
            } // success
        }; // options


        if(typeof opts != 'undefined') {
            $.extend(options, opts);
        }

        // $("#botones_ficha").hide();
        // $("#reloj").show();

        $(config.formSelector).ajaxSubmit(options);
    },

    // -------------------------------------------------------------------
    escapeHTML: function(str) {
        return str.replace(/&/g,'&amp;').replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
    },

    // -------------------------------------------------------------------
    handleError:   function(url, XMLHttpRequest, textStatus, errorThrown) {
        alert(ProntusLangController.getString('_submitform_ajax_error') +
                url + '\ntextStatus=' +
                textStatus + '\nXMLHttpRequest.status=' +
                XMLHttpRequest.status + '-' + XMLHttpRequest.statusText +
                '\nXMLHttpRequest.responseText=[' + XMLHttpRequest.responseText +
                ']\nResponseHeaders=' + XMLHttpRequest.getAllResponseHeaders());
    }

}; //  Fin clase


