var Coment = {

    dir_cgi_cpan: "",
    prontus_id: "",

    // -------------------------------------------------------------------------
    init: function() {

        // Si se han activado las Pop
        $('a.open_in_pop').live('click', function() {
            Admin.openArtic(this);
            return false;
        });
    },

    // -------------------------------------------------------------------------
    borrar: function(obj, id) {
        var msg = 'Está seguro de borrar este comentario?';
        if (confirm(msg)) {
            $(obj).parent().find('.fila_loading').show();
            $(obj).parent().find('a').hide();
            $.ajax({
                url:        '/' + Coment.dir_cgi_cpan + '/coment/coment_borrar.cgi',
                type:       'POST',
                dataType:   'json',
                cache:      false,
                data:       '_prontus_id='+Coment.prontus_id+'&COMENT_ID='+id,
                success:    function (data) {
                    if (data.status == '0') {
                        alert(data.msg);
                    } else {
                        /* Borrar fila */
                        $('#coment-'+id).fadeOut('slow', function () {
                            $(this).remove();
                        });
                    }
                    $(obj).parent().find('.fila_loading').hide();
                    $(obj).parent().find('a').show();
                },
                complete: function () {
                    $(obj).parent().find('.fila_loading').hide();
                    $(obj).parent().find('a').show();
                }
            });
        }
    },

    // -------------------------------------------------------------------------
    toggleSt: function (obj, id) {

        $(obj).parent().find('.fila_loading').show();
        $(obj).parent().find('a').hide();

        /* Nuevo st. */
        var new_st = 1;
        if ($(obj).find('img').attr('alt') == 'btn_ticket_green') {
            new_st = 0;
        }
        $.ajax({
            url:        '/' + Coment.dir_cgi_cpan + '/coment/coment_cambia_st.cgi',
            type:       'POST',
            dataType:   'json',
            cache:      false,
            data:       'COMENT_ID='+id+'&NEW_ST='+new_st+'&_prontus_id='+Coment.prontus_id,
            success:    function (data) {
                if (data.status == '0') {
                    alert(data.msg);
                } else {
                    /* Cambiar imagen, alt y title.*/
                    if (new_st == 1) {
                        $(obj).find('img').attr('src', ($(obj).find('img').attr('src')).replace('btn_ticket_red', 'btn_ticket_green'));
                        $(obj).find('img').attr('alt', 'btn_ticket_green');
                        $(obj).find('img').attr('title', 'Aprobar comentario');
                    } else {
                        $(obj).find('img').attr('src', ($(obj).find('img').attr('src')).replace('btn_ticket_green', 'btn_ticket_red'));
                        $(obj).find('img').attr('alt', 'btn_ticket_red');
                        $(obj).find('img').attr('title', 'Desaprobar comentario');
                    }
                }
          },
          complete: function () {
                $(obj).parent().find('.fila_loading').hide();
                $(obj).parent().find('a').show();
          },
          error: function (data) {
                alert("Ocurrio un error, intentelo nuevamente.");
                $(obj).parent().find('.fila_loading').hide();
                $(obj).parent().find('a').show();
            }
        });
    },

    // -------------------------------------------------------------------------
    chgImgSrc: function(obj, img) {
        $(obj).attr("src", img);
    }
};
