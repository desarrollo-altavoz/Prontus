(function (window) {
    var self = null;
    var MantenedorMultiTag = {
        prontus_id: '',
        _path_conf: '',
        // ------------------------------------------------------------------
        init: function (prontus_id) {
            $('#multitag-tabs').idTabs();
            self = this;
            self.prontus_id = prontus_id;
            self._path_conf = '/' + self.prontus_id + '/cpan/' + self.prontus_id + '.cfg';

            self.actions.loadData(function () {
                self.bindEvents();
                self.row.bindEvents();
            });

            self.initCompleteFriendly();

            $('#borrar-cache-mtag').on('click', function () {
                var msg = "Se borrará todo el caché. ¿Estás seguro?";
                if (confirm(msg)) {
                    $.ajax({
                        url: '/'+Admin.dir_cgi_cpn+'/multitag/prontus_multitag_mant_limpia_cache.cgi',
                        data: {_path_conf:self._path_conf},
                        dataType: 'json',
                        success: function (data) {
                            if (data.status === 1) {
                                alert("El caché fue eliminado.");
                            } else {
                                alert("Ocurrió un error al tratar de eliminar el caché. Inténtalo nuevamente más tarde.");
                            }
                        }
                    });
                }

                return false;
            });
        },
        // ------------------------------------------------------------------
        initCompleteFriendly: function () {

            $('li[id^="form-"]').each(function () {
                var $inputNombre = $(this).find('.campo-nombre input');
                var $inputFriendly = $(this).find('.campo-friendly input');

                $inputNombre.keyup(function (e) {
                    var nombre = $inputNombre.val().toLowerCase();
                    nombre = nombre.replace(/á/gi, "a");
                    nombre = nombre.replace(/é/gi, "e");
                    nombre = nombre.replace(/í/gi, "i");
                    nombre = nombre.replace(/ó/gi, "o");
                    nombre = nombre.replace(/ú/gi, "u");
                    nombre = nombre.replace(/ñ/gi, "n");

                    nombre = nombre.replace(/([^a-z0-9 ]+)/gi, "");
                    nombre = nombre.replace(/ +/g, ' ');
                    nombre = nombre.replace(/ /g, "-");

                    if (nombre.length > 32) {
                        nombre = nombre.substr(0, 32);
                    }

                    $inputFriendly.val(nombre);
                });

                $inputFriendly.keyup(function (e) {
                    var friendly = $inputFriendly.val().toLowerCase();
                    friendly = friendly.replace(/á/gi, "a");
                    friendly = friendly.replace(/é/gi, "e");
                    friendly = friendly.replace(/í/gi, "i");
                    friendly = friendly.replace(/ó/gi, "o");
                    friendly = friendly.replace(/ú/gi, "u");
                    friendly = friendly.replace(/ñ/gi, "n");

                    friendly = friendly.replace(/([^a-z0-9\- ]+)/gi, "");
                    friendly = friendly.replace(/ +/g, ' ');
                    friendly = friendly.replace(/ /g, "-");

                    if (friendly.length > 32) {
                        friendly = friendly.substr(0, 32);
                    }

                    $inputFriendly.val(friendly);
                });
            });
        },
        // ------------------------------------------------------------------
        bindEvents: function () {
            self.bindCambiaBoton();
            // Agregar nuevo.
            $('.agrega-item').on('click', function () {
                var $parent = $(this).parents('.form');
                var type = $(this).attr('data-type');
                var nombre = $('#form-' + type).find('.campo-nombre input').val();
                var friendly = $('#form-' + type).find('.campo-friendly input').val();

                $parent.find('.boton-guardar').hide();
                $parent.find('.loading').show();

                self.actions.saveData('', type, {
                    nombre: nombre,
                    friendly: friendly
                }, function (data) {
                    if (data.status == 0) {
                        alert(data.msg);
                    } else if (data.status == 1) {
                        self.row.addRow(data.id, data.type, data.nombre, data.friendly, (data.estado == 1 ? 'on' : 'off'), true);
                        $('#form-' + type).find('.campo-nombre input').val('');
                        $('#form-' + type).find('.campo-friendly input').val('');
                        self.row.bindEvents('#' + data.type + '_' + data.id);
                        self.bindCambiaBoton();
                    }
                    $parent.find('.boton-guardar').show();
                    $parent.find('.loading').hide();
                });

                return false;
            });

            var $copy = $('.copiar-link');

            $copy.on('click', function(e) {
                e.preventDefault();
            });

            $copy.clipboard({
                path: '/' + self.prontus_id + '/cpan/core/js-local/jquery/plugins/clipboard/jquery.clipboard.swf',

                copy: function() {
                    self.helper.toogle($(this).find('img').get(0), 'on');
                    return $(this).attr('href');
                },
                afterCopy: function () {
                    self.helper.toogle($(this).find('img').get(0), 'of');
                }
            });
        },
        // ------------------------------------------------------------------
        bindCambiaBoton: function () {
            $('img.cambia-boton').on('mouseover', function() {
                self.helper.toogle(this, 'on');
            }).on('mouseout click', function() {
                self.helper.toogle(this, 'of');
            });

            $('a.cambia-boton').on('mouseover', function() {
                self.helper.toogle($(this).find('img').get(0), 'on');
            }).on('mouseout click', function() {
                self.helper.toogle($(this).find('img').get(0), 'of');
            });
        },
        // ------------------------------------------------------------------
        initSortable: function () {
            $('#multitag_seccion').sortable({
                handle: '.campo-handler img',
                items: "li:not(.ignore-sortable)",
                stop: function (event, ui) {
                    // Guardar posicion via ajax.
                }
            });
        },
        // ------------------------------------------------------------------
        actions: {
            // ------------------------------------------------------------------
            loadData: function (callback) {
                $.ajax({
                    url: '/'+Admin.dir_cgi_cpn+'/multitag/prontus_multitag_load_data.cgi',
                    data: {
                        _path_conf: self._path_conf
                    },
                    dataType: 'json',
                    success: function (data) {
                        $.each(data.secciones, function (i, v) {
                            self.row.addRow(v.MULTITAG_s_id, 'seccion', v.MULTITAG_s_nombre, v.MULTITAG_s_friendly, (v.MULTITAG_s_estado == 1 ? 'on' : 'off'));
                        });

                        $.each(data.temas, function (i, v) {
                            self.row.addRow(v.MULTITAG_t_id, 'tema', v.MULTITAG_t_nombre, v.MULTITAG_t_friendly, (v.MULTITAG_t_estado == 1 ? 'on' : 'off'));
                        });

                        $.each(data.subtemas, function (i, v) {
                            self.row.addRow(v.MULTITAG_st_id, 'subtema', v.MULTITAG_st_nombre, v.MULTITAG_st_friendly, (v.MULTITAG_st_estado == 1 ? 'on' : 'off'));
                        });

                        if (typeof callback === "function") {
                            callback();
                        }
                    }
                });
            },
            // ------------------------------------------------------------------
            saveData: function (id, type, data, callback) {
                console.log(id + ' , '+ type + ' , '+  data + ' , '+ callback)
                if (self.actions.validateData(id, data)) {
                    $.extend(data, {
                        _path_conf: self._path_conf,
                        id: id,
                        type: type
                    }),
                    $.ajax({
                        url: '/'+Admin.dir_cgi_cpn+'/multitag/prontus_multitag_mant_guardar.cgi',
                        data: data,
                        type: 'POST',
                        dataType: 'json',
                        success: function (data) {
                            if (typeof callback === "function") {
                                callback(data);
                            }
                        }
                    });
                } else {
                    if (typeof callback === "function") {
                        callback(data);
                    }
                }
            },
            // ------------------------------------------------------------------
            deleteData: function (id, type, callback) {
                $.ajax({
                    url: '/'+Admin.dir_cgi_cpn+'/multitag/prontus_multitag_mant_borrar.cgi',
                    data: {_path_conf:self._path_conf,id:id,type:type},
                    type: 'POST',
                    dataType: 'json',
                    success: function (data) {
                        if (typeof callback === "function") {
                            callback(data);
                        }
                    }
                });
            },
            // ------------------------------------------------------------------
            validateData: function (id, data) {
                if (data.nombre == "") {
                    alert('El nombre es obligatorio.');
                    return false;
                }

                if (!id) { // es nuevo.
                    if (data.friendly == "") {
                        alert('La Friendly URL es obligatoria.');
                        return false;
                    }
                }

                return true;
            }
        },
        // ------------------------------------------------------------------
        row: {
            // ------------------------------------------------------------------
            getHtmlTemplate: function (id, type, nombre, friendly, estado) {
                var html = [
                //'<li>',
                '    <div class="fila data" id="%%type%%_%%id%%">',
                '        <div class="campo campo-handler"><img src="/%%_prontus_id%%/cpan/core/imag/boto/mover2.png" alt=""></div>',
                '        <div class="campo campo-id"><p>%%id%%</p></div>',
                '        <div class="campo campo-nombre"><p>%%nombre%%</p></div>',
                '        <div class="campo campo-friendly"><p><a href="/%%type%%/%%friendly%%/p/1" target="_blank">%%friendly%%</a></p></div>',
                '        <div class="campo botones acciones">',
                '            <a href="%%url%%" class="copiar-link" title="Copiar enlace"><img src="/%%_prontus_id%%/cpan/core/imag/boto/copylink2_of.png" width="18" height="18" alt="Copiar enlace" title="Copiar enlace" class="cambia-boton"></a>',
                '            <!--<a href="#" class="estado" data-estado="%%estado%%"><img class="mostrar" src="/%%_prontus_id%%/cpan/core/imag/boto/%%btn_ticket%%.png" width="18" height="18" title="Cambiar estado"></a>-->',
                '            <a href="#" class="editar"><img src="/%%_prontus_id%%/cpan/core/imag/boto/editar_of.png" width="18" height="18" alt="Editar" title="Editar" class="cambia-boton"></a>',
                '            <a href="#" class="borrar"><img src="/%%_prontus_id%%/cpan/core/imag/boto/borrar_of.png" width="18" height="18" alt="Borrar" title="Borrar" class="cambia-boton"></a>',
                '        </div>',
                '        <div class="campo botones edicion">',
                '            <a href="#" class="guardar"><img src="/%%_prontus_id%%/cpan/core/imag/boto/gu2_of.png" width="18" height="18" class="cambia-boton" alt="Guardar" title="Guardar"></a>',
                '            <a href="#" class="cancelar" onclick=""><img src="/%%_prontus_id%%/cpan/core/imag/boto/can_of.png" width="18" height="18" class="cambia-boton" alt="Cancelar" title="Cancelar"></a>',
                '        </div>',
                '        <div class="campo loading aright">',
                '           <img src="/%%_PRONTUS_ID%%/cpan/core/imag/loader/ajax-loader.gif"/>',
                '        </div>',
                '    </div>',
                //'</li>'
                ].join('');

                html = html.replace(/%%id%%/g, id);
                html = html.replace(/%%_prontus_id%%/g, self.prontus_id);
                html = html.replace(/%%type%%/g, type);
                html = html.replace(/%%nombre%%/g, nombre);
                html = html.replace(/%%friendly%%/g, friendly);
                html = html.replace(/%%estado%%/g, estado);

                var url = "/" + type + "/" + friendly + "/p/1";
                var btn_ticket;

                html = html.replace(/%%url%%/g, url);

                if (estado === 'on') btn_ticket = 'btn_ticket_green';
                if (estado === 'off') btn_ticket = 'btn_ticket_red';

                html = html.replace(/%%btn_ticket%%/g, btn_ticket);

                return html;
            },
            // ------------------------------------------------------------------
            addRow: function (id, type, nombre, friendly, estado, fadein) {
                var $html = $('<li/>').html(self.row.getHtmlTemplate(id, type, nombre, friendly, estado));
                if (typeof fadein !== "undefined" && fadein === true) {
                    $html.hide();
                    $('#multitag_' + type).append($html);
                    $('#' + type + '_' + id).parent().fadeIn('fast');
                } else {
                    $('#multitag_' + type).append($html);
                }

            },
            // ------------------------------------------------------------------
            bindEvents: function (selector) {
                if (typeof selector === "undefined") {
                    selector = 'div.fila.data';
                }
                $(selector).find('.editar').click(function () {
                    var elementId = $(this).parents('.fila.data').attr('id');
                    self.row.editRow(elementId);
                    return false;
                });
                $(selector).find('.cancelar').click(function () {
                    var elementId = $(this).parents('.fila.data').attr('id');
                    self.row.cancelEditRow(elementId);
                    return false;
                });
                $(selector).find('.borrar').click(function () {
                    var elementId = $(this).parents('.fila.data').attr('id');
                    self.row.removeRow(elementId);
                    return false;
                });
                $(selector).find('.guardar').click(function () {
                    var elementId = $(this).parents('.fila.data').attr('id');
                    self.row.saveRow(elementId);
                    return false;
                });
                $(selector).find('.estado').click(function () {
                    var elementId = $(this).parents('.fila.data').attr('id');
                    self.row.toggleStatus(elementId, true);
                    return false;
                });
            },
            // ------------------------------------------------------------------
            editRow: function (elementId) {
                var $row = $('#' + elementId);

                $row.find('.acciones').hide();
                $row.find('.edicion').show();

                var nombre = $row.find('.campo-nombre p').text();

                $row.find('.campo-nombre').html('<input type="text" value="' + nombre + '" name="edit-nombre" maxlength="64"/><input type="hidden" value="' + nombre + '" name="old-nombre" />');
            },
            // ------------------------------------------------------------------
            cancelEditRow: function (elementId) {
                var $row = $('#' + elementId);

                $row.find('.acciones').show();
                $row.find('.edicion').hide();

                // restaurar nombre anterior.
                var old_nombre = $row.find('.campo-nombre input[name="old-nombre"]').val();

                $row.find('.campo-nombre').html('<p>' + old_nombre + '</p>');
            },
            // ------------------------------------------------------------------
            removeRow: function (elementId) {
                if (confirm("Esta operación es irreversible. ¿Estás seguro?")) {
                    var $row = $('#' + elementId);
                    var item = self.helper.getIdType(elementId);

                    $row.find('.acciones').hide();
                    $row.find('.loading').show();

                    self.actions.deleteData(item.id, item.type, function (data) {
                        if (data.status === 1) {
                            $row.parent().fadeOut('fast');
                        } else {
                            alert(data.msg);
                            $row.find('.acciones').show();
                            $row.find('.loading').hide();
                        }
                    });

                }
            },
            // ------------------------------------------------------------------
            saveRow: function (elementId) {
                var $row = $('#' + elementId);
                var nombre = $row.find('.campo-nombre input[name="edit-nombre"]').val();
                var item = self.helper.getIdType(elementId);

                $row.find('.edicion').hide();
                $row.find('.loading').show();

                // Guardar.
                self.actions.saveData(item.id, item.type, {
                    nombre: nombre,
                }, function (data) {
                    if (data.status == 0) {
                        alert(data.msg);
                        self.row.cancelEditRow(elementId);
                    } else if (data.status == 1) {
                        $row.find('.campo-nombre').html('<p>' + data.nombre + '</p>');
                        $row.find('.acciones').show();
                        $row.find('.edicion').hide();
                        $row.find('.loading').hide();
                    }

                });
            },
            // ------------------------------------------------------------------
            toggleStatus: function (elementId, save) {
                var $row = $('#' + elementId);
                var estado = $row.find('.estado').attr('data-estado');
                var item = self.helper.getIdType(elementId);

                if (estado === 'on') {
                    $row.find('.estado').attr('data-estado', 'off');
                    var src = $row.find('.estado img').attr('src').replace('btn_ticket_green', 'btn_ticket_red');
                    $row.find('.estado img').attr('src', src);
                    estado = 'off';
                } else {
                    $row.find('.estado').attr('data-estado', 'on');
                    var src = $row.find('.estado img').attr('src').replace('btn_ticket_red', 'btn_ticket_green');
                    $row.find('.estado img').attr('src', src);
                    estado = 'on';
                }

                if (typeof save !== "undefined" && save === true) {
                    // guardar via ajax.
                    $row.find('.acciones').hide();
                    $row.find('.loading').show();

                    self.actions.saveData(item.id, item.type, {
                        estado: estado,
                        solo_estado:1
                    }, function () {
                        $row.find('.acciones').show();
                        $row.find('.loading').hide();
                    });
                }
            }
        },
        // ------------------------------------------------------------------
        helper: {
            // ------------------------------------------------------------------
            toogle: function (imag, estado) {
                if(typeof imag === 'undefined') {
                    return;
                }
                var thesrc = imag.src;
                var ind = thesrc.lastIndexOf('.');
                var before = thesrc.substr(0, ind-2);
                var state = thesrc.substr(ind-2, 2);
                var after = thesrc.substr(ind, thesrc.length - ind);
                var newstate = '';

                if(typeof estado !== 'undefined') {
                    newstate = estado;
                } else {
                    if(state == 'on') {
                        newstate = 'of';
                    } else if(state == 'of') {
                        newstate = 'on';
                    } else {
                        return;
                    }
                }

                imag.src = before + newstate + after;
                return;
            },
            // ------------------------------------------------------------------
            getIdType: function (idCompuesto) {
                var arr = idCompuesto.split('_');
                return {
                    id: arr[1],
                    type: arr[0]
                };
            }
        }
    };

    window.MantenedorMultiTag = MantenedorMultiTag;
})(this);
