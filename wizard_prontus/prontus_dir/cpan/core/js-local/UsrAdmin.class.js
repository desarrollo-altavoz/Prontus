
var UsrAdmin = {
    dir_gi_cpan: "",
    path_conf: "",
    prontus_id: "",
    widthNormal: 740,
    heightNormal: 680,
    widthAdmin: 735,
    heightAdmin: 390,
    maxLength: 32,
    minLength: 8,
    idAdmin: 1,

    // -------------------------------------------------------------------------
    cargarFicha: function(id) {
        var url;
        var new_width = UsrAdmin.widthNormal;
        var new_height = UsrAdmin.heightNormal;

        if (typeof id === 'undefined') {
            url = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_ficha.cgi?_path_conf='+UsrAdmin.path_conf;
        } else {
            url = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_ficha.cgi?_path_conf='+UsrAdmin.path_conf+'&USERS_ID='+id;
        }

        if (id == UsrAdmin.idAdmin) {
            new_width = UsrAdmin.widthAdmin;
            new_height = UsrAdmin.heightAdmin;
        }

        $.fn.colorbox({
            open: true,
            href: url,
            width: new_width,
            height: new_height,
            maxWidth: '95%',
            maxHeight: '90%',
            opacity: 0.8
            // iframe: true,
        });
    },
    // -------------------------------------------------------------------------
    initFicha: function() {
        $('.list input[type="checkbox"]').bind('click', function() {
            UsrAdmin.toggleChecked($(this));
        });

        $(document).tooltip({
            position: {
                my: "center center",
                at: "center top-20",
                within: '#content-list',
                collision: 'flipfit'
            },

            show: {effect: "fadeIn", duration: 200 },
            hide: {effect: "hide"},
            items: ".itemlistado label",
            content: function() {
                var title = $(this).attr('title');
                title = "<span class=\"tooltip-ficha\">"+title+"</span>";
                return title;
            }
        });

        $("#range-slide").slider({
            range: "min",
            value: 0,
            min: 0,
            max: 365,
            slide: function (e, ui) {
                $('#EXP_DAYS').val(ui.value);
            }
        });

        $("#range-slide").slider("option", "value", $('#EXP_DAYS').val());

        $('#EXP_DAYS').on('keyup', function (e) {
            if (e.keyCode == 13) {
                if ($(this).val() < 0) {
                    $(this).val(0);
                    $("#range-slide").slider("option", "value", 0);
                } else if ($(this).val() > 365) {
                    $(this).val(365);
                    $("#range-slide").slider("option", "value", 365);
                } else {
                    $("#range-slide").slider("option", "value", $(this).val());
                }
            }
        });

        UsrAdmin.bindCheckPasswordStrength();

        $('#show_password').on('click', function (e) {
            e.preventDefault();
            var $element =  $('#PSW1');
            var value = $element.val();

            if ($element.attr('type') == 'text') {
                $('<input type="password" name="PSW1" id="PSW1" size="30" value="' + value + '" class="field-password" maxlength="' + UsrAdmin.minLength +'">').insertBefore($element);
                $element.remove();
                UsrAdmin.bindCheckPasswordStrength();
            } else {
                $('<input type="text" name="PSW1" id="PSW1" size="30" value="' + value + '" class="field-password" maxlength="'+ UsrAdmin.maxLength +'">').insertBefore($element);
                $element.remove();
                UsrAdmin.bindCheckPasswordStrength();
            }
        })
    },
    bindCheckPasswordStrength: function () {
        $('#PSW1').on('keyup', function (e) {
            $('#psw_strength').html(UsrAdmin.checkPasswordStrength($(this).val()));
        });
    },
    checkPasswordStrength: function (password) {
        if (password.length == 0) return '';
        if (password.length < UsrAdmin.minLength) {
            $('#psw_strength').removeClass().addClass('short');

            return 'Muy corta';
        }

        // if (password.match(/([a-z].*[A-Z])|([A-Z].*[a-z])/)) strength += 1;
        // if (password.match(/([a-zA-Z])/) && password.match(/([0-9])/)) strength += 1;
        // if (password.match(/([!,%,&,@,#,$,^,*,?,_])/)) strength += 1;

        if (!password.match(/([a-z])/)) {
            return 'Incluye letras minúsculas';
        } else if (!password.match(/([A-Z])/))  {
            $('#psw_strength').removeClass().addClass('weak');
            return 'Incluye al menos una mayúscula';
        } else if (!password.match(/([0-9])/)) {
            $('#psw_strength').removeClass().addClass('weak');
            return 'Incluye al menos un número';
        } else if (!password.match(/([!,%,&,@,#,$,^,*,?,_])/)) {
            $('#psw_strength').removeClass().addClass('good');
            return 'Te falta incluir un caracter especial: !%&@#$^*?_.';
        } else {
            $('#psw_strength').removeClass().addClass('strong');
            return 'Excelente!';
        }
    },
    // -------------------------------------------------------------------------
    borrar: function(id) {
        var msg = '¿Está seguro de borrar a este usuario?';
        if (confirm(msg)) {
            $.ajax({
                url:        '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_borrar.cgi',
                type:       'POST',
                dataType:   'json',
                data:       '_id='+id+'&_path_conf='+UsrAdmin.path_conf,
                success: function(data) {
                    if (data.status == '0') {
                        alert(data.msg);
                    } else {
                        $('#item-user-'+id).fadeOut('slow', function() {
                            $(this).remove();
                        });
                    }
                },
                error: function() {
                    alert('Ocurrio un error, inténtelo nuevamente.');
                }
            });
        }
    },

    // -------------------------------------------------------------------------
    guardarFicha: function(id) {

        var msg = '¿Está seguro que desea guardar sus datos?';
        if (id == UsrAdmin.idAdmin && ! confirm(msg)) {
            return false;
        };

        var configAjax = {
            formSelector: '#frmUsrFicha',
            actionURL: '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_sbmit.cgi'
        };

        var optsAjax = {
            success:   function(json, statusText) {
                if (json.status == '1' && json.msg === '') {
                    if (id == UsrAdmin.idAdmin) {
                        window.location.href = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_logout.cgi?_path_conf=' + UsrAdmin.path_conf;
                    } else {
                        window.location.href = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_admin.cgi?_path_conf='+UsrAdmin.path_conf;
                    }
                } else if (json.status == '1' && json.msg !== '') {
                    alert(json.msg);
                    if (id == UsrAdmin.idAdmin) {
                        window.location.href = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_logout.cgi?_path_conf=' + UsrAdmin.path_conf;
                    } else {
                        window.location.href = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_admin.cgi?_path_conf='+UsrAdmin.path_conf;
                    }
                } else if (json.status == '0') {
                    alert(json.msg);
                }
            }, // success
            complete: function() {
                /* Cargando... */
            }
        };
        SubmitForm.submitGenericAjax(configAjax, optsAjax);
    },

    // -------------------------------------------------------------------------
    guardarChgPass: function() {

        var configAjax = {
            formSelector: '#frmChgPass',
            actionURL: '/' + UsrAdmin.dir_cgi_cpan + '/prontus_usr_chgpass_sbmit.cgi'
        };

        var optsAjax = {
            success:   function(json, statusText) {
                if (json.status == '1' && json.msg === '') {
                    window.location.href = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_logout.cgi?_path_conf=' + UsrAdmin.path_conf;
                } else if (json.status == '1' && json.msg !== '') {
                    alert(json.msg);
                    window.location.href = '/' + UsrAdmin.dir_cgi_cpan + '/prontus_logout.cgi?_path_conf=' + UsrAdmin.path_conf;
                } else if (json.status == '0') {
                    alert(json.msg);
                }
            }, // success
            complete: function() {
                /* Cargando... */
            }
        };

        SubmitForm.submitGenericAjax(configAjax, optsAjax);
    },

    // -------------------------------------------------------------------------
    chgImgSrc: function(obj, img) {
        $(obj).attr("src", img);
    },

    // -------------------------------------------------------------------------
    toggleChecked: function (o) {
        if ($(o).is(':checked')) {
            $(o).parent().find('label').addClass('checked');
        } else {
            $(o).parent().find('label').removeClass('checked');
        }
    },

    // -------------------------------------------------------------------------
    checkboxToggleChecked: function(name, action) {
        if (action == true) {
            $('input[name="' + name + '"]').attr("checked", "checked");
            $('input[name="' + name + '"]').next('label').addClass("checked");
        } else {
            $('input[name="' + name + '"]').removeAttr("checked");
            $('input[name="' + name + '"]').next('label').removeClass("checked");
        }
    },

};
