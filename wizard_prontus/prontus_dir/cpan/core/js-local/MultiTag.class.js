(function (window) {
    var self = null;
    var MultiTag = {
        prontus_id: '',
        _path_conf: '',
        init: function (prontus_id) {
            self = this;
            self.prontus_id = prontus_id;
            self._path_conf = '/' + self.prontus_id + '/cpan/' + self.prontus_id + '.cfg';

            self.actions.loadData(function () {
                $('input[id^="multitag_"]').click(function () {
                    // Actualizar hidden con secciones/temas/substemas
                    self.actions.updateHidden($(this).attr('data-type'));
                });
                $('#btnCombMtag').colorbox({
                    width: '850',
                    height: '60%',
                    inline: true,
                    href: "#divCombinaciones",
                    onOpen: function () {
                        self.actions.makeCombinations();
                    },
                    onClosed: function() {
                    },
                    onComplete: function () {
                        self.actions.bindCopyLink();
                    }
                });
            });
        },

        instalaClipboardHtml5: function(element) {
            var $elem = $(element);
            var $td = $elem.parent().next();
            var clipboard = new Clipboard($elem.get(0),{
                    text: function(trigger) {
                        return $td.find('a').attr('href');
                    }
                });
            clipboard.on('success', function(e) {
                $td.animate({
                    backgroundColor: "#dff0d8"
                }, 500).animate({
                    backgroundColor: "#fafafa"
                }, 500);
                return true;
            });
        },

        instalaClipboardFlash: function(element) {
            var $elem = $(element);
            ZeroClipboard.setMoviePath('/'+Admin.prontus_id+'/cpan/core/js-local/zeroclipboard/ZeroClipboard.swf');
            var clip = new ZeroClipboard.Client();
            clip.setHandCursor(true);
            clip.setCSSEffects(true);
            clip.addEventListener('mouseDown', function (client, text) {
                var $td = $elem.parent().next();
                clip.setText($td.find('a').attr('href'));
                $td.animate({
                    backgroundColor: "#dff0d8"
                }, 500).animate({
                    backgroundColor: "#fafafa"
                }, 500);
                return true;
            });
            clip.glue($elem.get(0), 'divCombinaciones');
        },
        actions: {
            bindCopyLink: function () {
                var $copy = $('.copiar-link-mtag');

                $copy.on('click', function(e) {
                    e.preventDefault();
                });

                $copy.each( function() {
                    // Para el copiar al Clipboard
                    if (jQuery.browser.msie) { // para internet explorer
                        if (jQuery.browser.flash) { // navegador tiene flash
                            self.instalaClipboardFlash(this);
                        } else if (Admin.clipboardHtml5) { // navegador soporta api html5
                            self.instalaClipboardHtml5(this);
                        } else { // no se puede habilitar funcionalidad de clipboard
                            $('.copiar-link-mtag').remove();
                        }
                    } else if (Admin.clipboardHtml5) { // navegador soporta api html5
                        self.instalaClipboardHtml5(this);
                    } else if (jQuery.browser.flash) { // navegador tiene flash
                        self.instalaClipboardFlash(this);
                    } else { // no se puede habilitar funcionalidad de clipboard
                        $('.copiar-link-mtag').remove();
                    }
                });
            },
            makeCombinations: function () {
                var secciones = $('#multitag_lista_seccion').find('input[type="checkbox"]:checked');
                var temas = $('#multitag_lista_tema').find('input[type="checkbox"]:checked');
                var subtemas = $('#multitag_lista_subtema').find('input[type="checkbox"]:checked');
                var btnCopy = '<a href="#" class="copiar-link-mtag" title="Copiar enlace"><img src="/' + self.prontus_id + '/cpan/core/imag/boto/copylink2_of.png" width="15" height="15" alt="Copiar enlace" title="Copiar enlace" class="cambia-boton"></a>';

                $('#divCombinaciones').html('<h3>Listado de enlaces</h3><table width="100%" cellpadding="5" cellspacing="5"><tr><th>Nombre</th><th>&nbsp;</th><th>Enlace</th></tr></table>');

                $.each(secciones, function () {
                    var sf = $(this).attr('data-friendly');
                    var sn = $(this).attr('data-title');

                    $('#divCombinaciones table').append('<tr><td>' + sn + '</td><td>' + btnCopy + '</td><td><a target="_blank" href="/seccion/' + sf + '/p/1" class="lv1">/seccion/' + sf + '/p/1</a></td></tr>');

                    $.each(temas, function () {
                        var tf = $(this).attr('data-friendly');
                        var tn = $(this).attr('data-title');
                        $('#divCombinaciones table').append('<tr><td>' + sn + ' &raquo; ' + tn + '</td><td>' + btnCopy + '</td><td><a target="_blank" href="/seccion/' + sf + '/tema/' + tf + '/p/1" class="lv2">/seccion/' + sf + '/tema/' + tf + '/p/1</a></td></tr>');
                        $.each(subtemas, function () {
                            var stf = $(this).attr('data-friendly');
                            var stn = $(this).attr('data-title');
                            $('#divCombinaciones table').append('<tr><td>' + sn + ' &raquo; ' + tn + ' &raquo; ' + stn + '</td><td>' + btnCopy + '</td><td><a target="_blank" href="/seccion/' + sf + '/tema/' + tf + '/subtema/' + stf + '/p/1" class="lv3">/seccion/' + sf + '/tema/' + tf + '/subtema/' + stf + '/p/1</a></td></tr>');
                        });
                    });
                });

                $.each(secciones, function () {
                    var sf = $(this).attr('data-friendly');
                    var sn = $(this).attr('data-title');

                    $.each(subtemas, function () {
                        var stf = $(this).attr('data-friendly');
                        var stn = $(this).attr('data-title');
                        $('#divCombinaciones table').append('<tr><td>' + sn + ' &raquo; ' + stn + '</td><td>' + btnCopy + '</td><td><a target="_blank" href="/seccion/' + sf + '/subtema/' + stf + '/p/1" class="lv1">/seccion/' + sf + '/subtema/' + stf + '/p/1</a></td></tr>');
                    });
                });

                $.each(temas, function () {
                    var tf = $(this).attr('data-friendly');
                    var tn = $(this).attr('data-title');
                    $('#divCombinaciones table').append('<tr><td>' + tn + '</td><td>' + btnCopy + '</td><td><a target="_blank" href="/tema/' + tf + '/p/1" class="lv1">/tema/' + tf + '/p/1</a></td></tr>');

                    $.each(subtemas, function () {
                        var stf = $(this).attr('data-friendly');
                        var stn = $(this).attr('data-title');
                        $('#divCombinaciones table').append('<tr><td>' + tn + ' &raquo; ' + stn + '</td><td>' + btnCopy + '</td><td><a target="_blank" href="/tema/' + tf + '/subtema/' + stf + '/p/1" class="lv2">/tema/' + tf + '/subtema/' + stf + '/p/1</a></td></tr>');
                    });
                });

                $.each(subtemas, function () {
                    var stf = $(this).attr('data-friendly');
                    var stn = $(this).attr('data-title');
                    $('#divCombinaciones table').append('<tr><td>' + stn + '</td><td>' + btnCopy + '</td><td><a target="_blank" href="/subtema/' + stf + '/p/1" class="lv1">/subtema/' + stf + '/p/1</a></td></tr>');
                });
            },
            loadData: function (callback) {
                $.ajax({
                    url: '/cgi-cpn/multitag/prontus_multitag_load_data.cgi',
                    data: {
                        _path_conf: self._path_conf
                    },
                    dataType: 'json',
                    success: function (data) {
                        var mtagSList = self.actions.getMtagList('seccion');
                        $.each(data.secciones, function (i, v) {
                            self.row.addRow(v.MULTITAG_s_id, 'seccion', v.MULTITAG_s_nombre, v.MULTITAG_s_friendly, mtagSList);
                        });

                        var mtagTList = self.actions.getMtagList('tema');
                        $.each(data.temas, function (i, v) {
                            self.row.addRow(v.MULTITAG_t_id, 'tema', v.MULTITAG_t_nombre, v.MULTITAG_t_friendly, mtagTList);
                        });

                        var mtagSTList = self.actions.getMtagList('subtema');
                        $.each(data.subtemas, function (i, v) {
                            self.row.addRow(v.MULTITAG_st_id, 'subtema', v.MULTITAG_st_nombre, v.MULTITAG_st_friendly, mtagSTList);
                        });

                        if (typeof callback === "function") {
                            callback();
                        }
                    }
                });
            },
            updateHidden: function (type) {
                var data = [];

                $('input[id^="multitag_' + type + '"]:checked').each(function () {
                    data.push($(this).val());
                });

                $('#multitag_' + type).val(data.join(','));
            },
            getMtagList: function (type) {
                var str = $('#multitag_' + type).val();
                var arr = str.split(',');

                return arr;
            }
        },
        row: {
            // ------------------------------------------------------------------
            getHtmlTemplate: function (id, type, nombre, friendly, checked) {
                var html = [
                    '<input type="checkbox" id="multitag_%%type%%_%%id%%" data-type="%%type%%" data-title="%%nombre%%" data-friendly="%%friendly%%" value="%%id%%" %%checked%%/> <label for="multitag_%%type%%_%%id%%">%%nombre%%</label>'
                ].join('');

                html = html.replace(/%%id%%/g, id);
                html = html.replace(/%%_prontus_id%%/g, self.prontus_id);
                html = html.replace(/%%type%%/g, type);
                html = html.replace(/%%nombre%%/g, nombre);
                html = html.replace(/%%friendly%%/g, friendly);

                if (checked) {
                    html = html.replace(/%%checked%%/, 'checked="checked"');
                } else {
                    html = html.replace(/%%checked%%/, '');
                }

                return html;
            },
            // ------------------------------------------------------------------
            addRow: function (id, type, nombre, friendly, mtagList) {
                var checked = false;
                if ($.inArray(String(id), mtagList) >= 0) checked = true;

                var $html = $('<div/>').html(self.row.getHtmlTemplate(id, type, nombre, friendly, checked));
                $html.addClass('item');
                $('#multitag_lista_' + type).append($html);
            }
        }
    };

    window.MultiTag = MultiTag;
})(this);
