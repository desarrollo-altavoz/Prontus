var Login = {

    dir_cgi_cpan: '',

    // -------------------------------------------------------------------------
    init: function(dir_cgi_cpan) {
        Login.dir_cgi_cpan = dir_cgi_cpan;
        $('#FrmLogin').submit(function() {
            Login.doLogin();
            return false;
        });
        if($.browser.msie) {
            $('input.fieldform').keypress(function(eventObject) {
                return Login.entsub(eventObject);
            });
        }
        var urlOlvide = '/' + Login.dir_cgi_cpan + '/prontus_olvidopass.cgi?_path_conf=' + window.document.FrmLogin._path_conf.value;
        $('#olvide_clave').attr('href', urlOlvide);
    },

    // -------------------------------------------------------------------------
    doLogin: function() {
        var configAjax = {
            formSelector: '#FrmLogin',
            actionURL: '/' + Login.dir_cgi_cpan + '/prontus_login.cgi',
            method: 'post'
        };

        var optsAjax = {
            success:   function(json, statusText) {
                if(json === null) {
                    return;
                };
                if (json.status=='2') {    // buffer html
                    $('.bodysite').html(json.msg);
                    $('.loading-action').hide();
                    $('.boton-ingresar').show();
                } else if (json.status=='1') {
                    Login.goToProntus();
                } else  {
                    alert(unescape(json.msg));
                    $('.loading-action').hide();
                    $('.boton-ingresar').show();

                }
            }, // success
            complete: function(XMLHttpRequest, textStatus) {
                if (textStatus != 'success') {
                    $('.loading-action').hide();
                    $('.boton-ingresar').show();
                };
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                SubmitForm.handleError(configAjax.actionURL, XMLHttpRequest, textStatus, errorThrown);
            }
        };

        $('.loading-action').css({display: 'inline'});
        $('.boton-ingresar').hide();
        SubmitForm.submitGenericAjax(configAjax, optsAjax);
    },

    // -------------------------------------------------------------------------
    chgImgSrc: function(obj, img) {
        $(obj).attr("src", img);
    },

    // -------------------------------------------------------------------------
    entsub: function(event, ourform) {
        if (event && event.which == 13) {
            Login.doLogin();
            return false;
        } else {
            return true;
        }
    },

    // -------------------------------------------------------------------------
    checkSession: function () {

        $.ajax({
            type: "GET",
            url: '/' + Login.dir_cgi_cpan + '/prontus_check_session.cgi',
            data: "_path_conf=" + window.document.FrmLogin._path_conf.value,
            success: function (data) {
                if (data == '1') {
                    Login.goToProntus();
                } else {
                    $('#checkSession').hide();
                    $('#loginbox').show();
                }
            }
        });
    },

    // -------------------------------------------------------------------------
    goToProntus: function() {

        $('#FrmLogin').unbind('submit');
        $('#FrmLogin').attr('action', '/' + Login.dir_cgi_cpan + '/prontus_art_newadmin.cgi');
        $('#FrmLogin').attr('method', 'get');
        //~ $('#_sbmit').trigger('click');
        $('#FrmLogin').submit();
    }

};
