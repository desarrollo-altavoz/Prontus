
var Editor = {

    idEditor: 'myeditor',

    urlArbol: 'prontus_edit_arbol.cgi',
    urlFile: 'prontus_edit_file.cgi',
    urlGuardar: 'prontus_edit_guardar.cgi',
    urlBorrar: 'prontus_edit_borrar.cgi',
    urlUpload: 'prontus_edit_upload.cgi',
    urlCopiar: 'prontus_edit_copy.cgi',
    editorLoaded: false,

    textUploadName: '[nombre sin extensión]',

    // -------------------------------------------------------------------------
    init: function() {

        Extras.init();

        // Setea el Path
        var thePath = Editor.getParam(window.location.href, '_dir');
        var theFile = Editor.getParam(window.location.href, '_file');
        if(theFile !== '') {
            theFile = thePath + '/' + theFile;
        }
        Editor.cambiaPathActual(thePath, theFile);
        Utiles.instalaHandlerBuscador('#name_upload', Editor.textUploadName);
        // Para los input:file
        $(".upload input:file").filestyle({
            image: "/" + Admin.prontus_id + "/cpan/core/imag/boto/examinar.gif",
            imageheight : 22,
            imagewidth : 82,
            width : 100
        });

        // Para el colorbox de la imagen
        $('.editor a.colorbox').live('click', function() {
            $.fn.colorbox({open:true, href:$(this).attr('href'), maxWidth:'90%', maxHeight:'90%', initialWidth:'200px', initialHeight:'200px',
                onComplete: function() {
                    if($('#cboxTopCenter').width() < 100) {
                        $('#colorbox, #cboxTopCenter, #cboxContent, #cboxBottomCenter').css('width','100px');
                        $('#cboxWrapper').css('width','128px');
                        var newLeft = parseInt($('#colorbox').css('left'), 10);
                        newLeft = (newLeft - 50);
                        $('#colorbox').css('left', newLeft+'px');
                    }
                }
            });
            return false;
        });

        // Para mostrar las extensiones
        $('a.show-extension').live('click', function() {
            $.fn.colorbox({open:true, inline:true, href:'#ext-upload div', width:'400px', height:'250px',
                onComplete: function() {
                    //alert($('#cboxLoadedContent div.msg-extension').html());
                    $('#cboxLoadedContent div.msg-extension').clone().appendTo('#ext-upload');
                    return true;
                }
            });
            return false;
        });

        // Para el scroll del arbol de directorios
        var tipo = Cookies.readCookie('prontus-editor-scroll');
        if(tipo != 'normal') {
            tipo = 'scroll';
        }
        Editor.setScrollArbol(tipo);

        $('a.link-scroll').click(function() {
            var tipo = $(this).attr('href');
            if(tipo == '#arbol-scroll') {
                Editor.setScrollArbol('scroll');
            } else {
                Editor.setScrollArbol('normal');
            }
        });

    },
    // -------------------------------------------------------------------------
    setScrollArbol: function(ahora) {
        var antes = '';
        if(ahora == 'scroll') {
            antes = 'normal';
        } else {
            ahora = 'normal';
            antes = 'scroll';
        }
        $(".arbol-"+antes).removeClass('arbol-'+antes).addClass('arbol-'+ahora);
        Cookies.createCookie('prontus-editor-scroll', ahora);
        $('.link-scroll').hide();
        $('.tipo-'+antes).show();

    },
    // -------------------------------------------------------------------------
    initEditor: function() {
        // Aca se deja el loading
        $('#content-editor').prepend('<div class="list-loading" style="height:100px">&nbsp;</div>');
        //$('#content-editor .inner-editor').offset({left: -8000 });

        // Se inicia el editArea
        editAreaLoader.init({
            id : Editor.idEditor,        // textarea id
            language: "es",
            syntax: "html",            // syntax to be uses for highgliting
            start_highlight: true,        // to display with highlight mode on start-up
            replace_tab_by_spaces: 4,
            font_size:9,
            min_height: 400,
            min_width: 724,
            allow_resize:'both',
            allow_toggle:false,
            EA_load_callback: '',
            toolbar: "search, go_to_line, fullscreen, |, undo, redo, |, select_font,|, highlight, word_wrap, |, help",
            //EA_init_callback: 'Editor.initEditorHandler' //
            EA_load_callback: 'Editor.initEditorHandler'
        });
    },

    // -------------------------------------------------------------------------
    initEditorHandler: function(id_editor) {

        // Se oculta el loading
        $('#content-editor .list-loading').remove();
        //$('#content-editor .inner-editor').offset({left: 0});

        // se ajusta el alto, para cuando no se pude setear el alto nativamente
        $('#'+Editor.idEditor).css('height', '400px');
        $('#content-editor').css('height', '400px');

        // Se usa para saber cuando cargo exactamente el editor
        Editor.editorLoaded = true;
    },

    // -------------------------------------------------------------------------
    setTab: function() {
        var dir = $('#_curr_dir').val();
        $('#tabs2 a.selected').removeClass('selected');
        $('#tabs2 a').each(function() {
            var dirlink = Editor.getParam($(this).attr('href'), '_dir');
            if(dir == dirlink) {
                $(this).addClass('selected');
            }
        });
        if($('#tabs2 a.selected').size() < 1) {
            $('#tabs2 a:first').addClass('selected');
        }
    },

    // -------------------------------------------------------------------------
    procesaArbol: function(obj, tipo) {
        var dirlink;
        if(tipo == 'dir') {
            dirlink = Editor.getParam($(obj).attr('href'), '_dir');
            Editor.cambiaPathActual(dirlink);

        } else if(tipo == 'file') {
            dirlink = Editor.getParam($(obj).attr('href'), '_dir');
            var filelink = Editor.getParam($(obj).attr('href'), '_file');
            Editor.cambiaArchivoActual(dirlink, dirlink + '/' + filelink);

        } else {
            Admin.displayMessage(ProntusLangController.getString('_element_type_not_valid'), ProntusLangController.getString('_msg_generic_error'));
        }
    },

    // -------------------------------------------------------------------------
    cambiaTabShortcut: function(obj) {
        var dirlink = Editor.getParam($(obj).attr('href'), '_dir');
        Editor.cambiaPathActual(dirlink);

    },

    // -------------------------------------------------------------------------
    setLinksPathActual: function(thePath) {
        if(thePath === '' || thePath == '/') {
            $('#dir_actual').html(thePath);
            return;
        }
        var arr = thePath.split('/');
        var total = arr.length;
        if(total < 2) {
            $('#dir_actual').html(thePath);
            return;
        }
        var theNewPath = '';
        var thePathReal = '';
        for(var k = 0; k < total ; k++) {
            if(k > 0 && arr[k] != '') {
                thePathReal = thePathReal + '/' + arr[k];
                var lnk = 'prontus_edit_main.cgi?_path_conf='+Admin.path_conf+'&amp;_dir='+thePathReal;
                var onclk = 'Editor.procesaArbol(this, \'dir\');';
                theNewPath = theNewPath + ' <a href="'+lnk+'" onclick="'+onclk+' return false;" title="'+ ProntusLangController.getString('_go_to_the_directory') +' '+thePathReal+'">/'+arr[k]+'</a>';
            }
        }

        $('#dir_actual').html(theNewPath);
    },

    // -------------------------------------------------------------------------
    cambiaPathActual: function(thePath, file) {

        if(typeof thePath === 'undefined' || typeof thePath === '') {
            return;
        }

        // Set Loadings y Candados
        if(Editor.loading) {
            return;
        }
        Editor.loading = true;
        $('#col-arbol').hide().html('<div class="list-loading" style="height:100px">&nbsp;</div>').show();

        // Se debería cargar el Arbol con Ajax
        var datos = {
            _path_conf: Admin.path_conf,
            _dir: thePath
        };
        $('#col-arbol').load(Editor.urlArbol, datos, function(responseText, textStatus, XMLHttpRequest) {
            //Editor.setLinksPathActual(thePath);
            Editor.loading = false;
            if(textStatus == 'success') {
                // Una vez que el arbol está cargado, se setea el path y se pinta el tab
                $('#_curr_dir').val(thePath);
                Editor.setTab();

                // Si hay un archivo cargado, se pinta en el listado
                Editor.addStyleActual($('#_path_file').val());

                // Si se estaba cambiando para cargar un archivo, se carga dicho archivo
                if(typeof file !== 'undefined') {
                    Editor.cambiaArchivoActual(thePath, file);
                }
            } else {
                alert(ProntusLangController.getString('_server_error_processing_request_ajax') + "\n"+ ProntusLangController.getString('_url_invoked') +
                        thePath + "\ntextStatus=" +
                        textStatus + "\nresponseText=" +
                        responseText + "\nXMLHttpRequest.status=" +
                        XMLHttpRequest.status + '-' + XMLHttpRequest.statusText +
                        "\nXMLHttpRequest.responseText=" + XMLHttpRequest.responseText +
                        "\nResponseHeaders=" + XMLHttpRequest.getAllResponseHeaders());
            }
        });
    },

    // -------------------------------------------------------------------------
    cambiaArchivoActual: function(thePath, file) {

        // Se debe enviar si o si el archivo
        if(typeof file === 'undefined' || typeof file === '' || file.indexOf('..') >= 0) {
            $('#col-edit').hide().html('<div style="height:100px">&nbsp;</div>').show();
            return;
        }

        var dir = $('#_curr_dir').val();
        if(thePath != dir) {
            Editor.cambiaPathActual(thePath, file);
        }

        // Set Loadings y Candados
        if(Editor.loading) {
            return;
        }
        Editor.loading = true;
        if(Editor.editorLoaded) {
            editAreaLoader.delete_instance(Editor.idEditor);
        }
        $('#col-edit').hide().html('<div class="list-loading" style="height:100px">&nbsp;</div>').show();

        // Se debería cargar el Arbol con Ajax
        var datos = {
            _path_conf: Admin.path_conf,
            _path_file: file,
            _dir: thePath
        };
        $('#col-edit').load(Editor.urlFile, datos, function(responseText, textStatus, XMLHttpRequest){
            Editor.loading = false;
            if(textStatus == 'success') {
                Editor.addStyleActual(file);
                if($('#'+Editor.idEditor).size() == 1) {
                    Editor.initEditor();
                } else {
                    Editor.editorLoaded = false;
                }
            } else {
                alert(ProntusLangController.getString('_server_error_processing_request_ajax') + "\n" ProntusLangController.getString('_url_invoked') +
                        thePath + "\ntextStatus=" +
                        textStatus + "\nresponseText=" +
                        responseText + "\nXMLHttpRequest.status=" +
                        XMLHttpRequest.status + '-' + XMLHttpRequest.statusText +
                        "\nXMLHttpRequest.responseText=" + XMLHttpRequest.responseText +
                        "\nResponseHeaders=" + XMLHttpRequest.getAllResponseHeaders());
            }
        });
    },

    // -------------------------------------------------------------------------
    addStyleActual: function(file) {
        if(typeof file === 'undefined' || typeof file === '') {
            return;
        }
        // Se valida que estemos en el mismo directorio
        var currdir = $('#_curr_dir').val();
        var path =  Editor.extractPath(file);
        if(currdir != path) {
            return;
        }
        // Se valida que el nombre de archivo coincida y se marca como selected
        var filename = Editor.extractFilename(file);
        $('#col-arbol .item').removeClass('selected').each(function() {
            if($(this).text() == filename) {
                $(this).addClass('selected');
            }
        });

    },

    // -------------------------------------------------------------------------
    extractFilename: function(file) {
        if(typeof file === 'undefined' || typeof file === '') {
            return;
        }
        var filename = '';
        var lastIdx = file.lastIndexOf('/');
        if(lastIdx >= 0) {
            filename = file.substr(lastIdx+1);
        }
        return filename;
    },

    // -------------------------------------------------------------------------
    extractPath: function(file) {

        var path = '';
        if(typeof file === 'undefined' || typeof file === '') {
            return path;
        }
        var lastIdx = file.lastIndexOf('/');
        if(lastIdx >= 0) {
            path = file.substr(0, lastIdx);
        }
        return path;
    },
    // -------------------------------------------------------------------------
    getParam: function (theurl, nom) {
        if(typeof theurl === 'undefined' || typeof theurl === '' || typeof nom === 'undefined' || typeof nom === '') {
            return '';
        }
        // Bus en IE, que toma el hash
        if(theurl.indexOf('#') > 0) {
            theurl = theurl.substr(0, theurl.indexOf('#'));
        }

        var request = theurl;
        if ((nom !== null) && (nom !== 'undefined') && (nom !== '')) {
            var re = new RegExp(nom + '=([^&]*)');
            var found = request.match(re);
            if(found !== null && found.length >= 2) {
                return found[1];
            } else {
                return '';
            }
        }
        return '';
    },

    // -------------------------------------------------------------------------
    showHelp: function(nomItem, relPathProntus) {
        var msg;
        if (nomItem == 'snippet') {
            msg = ProntusLangController.getString('_editor_showhelp_msg1') +
                    '\n\n' + ProntusLangController.getString('_editor_showhelp_msg2') + relPathProntus + '/plantillas/snippets/';
        }
        alert(msg);
    },

    // -------------------------------------------------------------------------
    accionGuardar: function() {
        if(!confirm(ProntusLangController.getString('_editor_save_confirmation'))) {
            return;
        }
        if(Editor.loading) {
            return;
        }
        Editor.loading = true;
        Editor.muestraAcciones(false);

        $('#text_file').val(editAreaLoader.getValue(Editor.idEditor));
        $('#sbm_accion').val('Guardar');

        var config = {
            formSelector: '#form-editor',
            actionURL: Editor.urlGuardar
        };
        var opts = {
            complete: function() {
                Editor.loading = false;
                Editor.muestraAcciones(true);
            },
            success: function(resp) {
                if(resp.status == 1) {
                    Admin.displayMessage(ProntusLangController.getString('_file_saved_successfully'), 'info');
                } else {
                    Admin.displayMessage(resp.msg, 'error');
                }
            }
        };
        SubmitForm.submitGenericAjax(config, opts);

    },

    // -------------------------------------------------------------------------
    accionNuevo: function() {
        //document.forms[0].curr_dir.value = parent.frames[0].document.forms[0].curr_dir.value;
        var param = prompt(ProntusLangController.getString('_editor_enter_name_file_to_create') + "\n" + ProntusLangController.getString('_file_is_saved_in_current_directory'), "");
        if ((param === null) || !Editor.validFileName(param)) {
            return false;
        }
        if(param.indexOf('.') < 0) {
            if(!confirm(ProntusLangController.getString('_editor_file_no_extensión_msg') + "\n" + ProntusLangController.getString('_editor_file_no_extensión_msg2'))) {
                return false;
            }
        }

        if(Editor.loading) {
            return;
        }
        Editor.loading = true;
        Editor.muestraAcciones(false);

        $('#nom_new_file').val(param);
        $('#sbm_accion').val('Nuevo');

        var dir = $('#_curr_dir').val();
        var file = dir + '/' + param;
        file = file.replace('//', '/');

        var config = {
            formSelector: '#form-editor',
            actionURL: Editor.urlGuardar
        };
        var opts = {
            complete: function() {
                Editor.loading = false;
                Editor.muestraAcciones(true);
            },
            success: function(resp) {
                if(resp.status == 1) {
                    Editor.loading = false;
                    Editor.cambiaPathActual(dir, file);
                    Admin.displayMessage(ProntusLangController.getString('_file_created_successfully'), 'info');
                } else {
                    Admin.displayMessage(resp.msg, 'error');
                }
            }
        };
        SubmitForm.submitGenericAjax(config, opts);

    },

    // -------------------------------------------------------------------------
    accionCopiar: function() {
        //document.forms[0].curr_dir.value = parent.frames[0].document.forms[0].curr_dir.value;
        var actual = $('#_path_file').val();
        if(actual === '') {
            return
        }
        var actual_file = actual.substr(actual.lastIndexOf('/')+1, actual.length - actual.lastIndexOf('/')+1);
        var actual_dir = actual.substr(0, actual.lastIndexOf('/')+1);

        var param = prompt(ProntusLangController.getString('_editor_accioncopiar_param_msg') + "\n" + ProntusLangController.getString('_editor_accioncopiar_param_msg2'), "");
        if ((param === null) || !Editor.validFileName(param)) {
            return false;
        }
        if(param == actual_file) {
            alert(ProntusLangController.getString('_enter_name_different_from_the current'));
            return false;
        }
        if(param.indexOf('.') < 0) {
            if(!confirm(ProntusLangController.getString('_editor_accioncopiar_confirm') + "\n" + ProntusLangController.getString('_editor_accioncopiar_confirm2'))) {
                return false;
            }
        }

        if(Editor.loading) {
            return;
        }
        Editor.loading = true;
        Editor.muestraAcciones(false);

        $('#nom_new_file').val(param);
        var dir = $('#_curr_dir').val();
        var config = {
            formSelector: '#form-editor',
            actionURL: Editor.urlCopiar
        };
        var opts = {
            complete: function() {
                Editor.loading = false;
                Editor.muestraAcciones(true);
            },
            success: function(resp) {
                if(resp.status == 1) {
                    Editor.loading = false;
                    Editor.cambiaPathActual(dir, actual_dir+param);
                    Admin.displayMessage(ProntusLangController.getString('_the_file_has_been_copied'), 'info');
                } else {
                    Admin.displayMessage(resp.msg, 'error');
                }
            }
        };
        SubmitForm.submitGenericAjax(config, opts);
    },

    // -------------------------------------------------------------------------
    accionUploadLayer: function(show) {
        if(show) {
            $('#upload').show('fast');
        } else {
            $('#upload').hide();
        }
    },

    // -------------------------------------------------------------------------
    accionUpload: function() {

        if ($('#file_upload').val() === '') {
            alert(ProntusLangController.getString('_specify_file_to_upload'));
            return false;
        }
        var nombre = $('#name_upload').val();
        if(nombre.indexOf('.') >= 0) {
            alert(ProntusLangController.getString('_restriction_for_name'));
            return false;
        }

        if(Editor.loading) {
            return;
        }
        Editor.loading = true;
        Editor.muestraAcciones(false);
        Editor.accionUploadLayer(false);

        if($('#name_upload').val() == Editor.textUploadName) {
            $('#name_upload').val('');
        }

        var dir = $('#_curr_dir').val();
        var config = {
            formSelector: '#form-editor',
            actionURL: Editor.urlUpload
        };
        var opts = {
            complete: function() {
                Editor.loading = false;
                Editor.muestraAcciones(true);
                $('#name_upload').val(Editor.textUploadName);
                $('#file_upload, .upload-content .upload .file').val('');
            },
            success: function(resp) {
                if(resp.status == 1) {
                    Editor.loading = false;
                    Editor.cambiaPathActual(dir, '');
                    Admin.displayMessage(resp.msg, 'info');
                } else {
                    Admin.displayMessage(resp.msg, 'info');
                    $('#msg-global span a').each(function() {
                        $(this).attr('href', '#').attr('class', 'show-extension').css('cursor', 'pointer');
                    });
                }

            }
        };
        SubmitForm.submitGenericAjax(config, opts);

    },


    // -------------------------------------------------------------------------
    accionCerrar: function(tipo) {
        if(tipo === 'text') {
            if(!confirm(ProntusLangController.getString('_accioncerrar_confirm') + "\n" + ProntusLangController.getString('_accioncerrar_confirm2'))) {
                return false;
            }
        }
        var thePath = $('#_curr_dir').val();
        Editor.cambiaArchivoActual(thePath, '');
        $('#col-arbol .item').removeClass('selected');
    },
    // -------------------------------------------------------------------------
    accionMkdir: function() {
        //document.forms[0].curr_dir.value = parent.frames[0].document.forms[0].curr_dir.value;
        var param = prompt(ProntusLangController.getString('_accionmkdir_param') + "\n" + ProntusLangController.getString('_accionmkdir_param2'), "");
        if ((param === null) || !Editor.validFileName(param)) {
            return false;
        }

        if(Editor.loading) {
            return;
        }
        Editor.loading = true;
        Editor.muestraAcciones(false);

        var dir = $('#_curr_dir').val();
        var newdir = dir + '/' + param;
        newdir = newdir.replace('//', '/');

        $('#nom_new_file').val(param);
        $('#sbm_accion').val('CrearDir');

        var config = {
            formSelector: '#form-editor',
            actionURL: Editor.urlGuardar
        };
        var opts = {
            complete: function() {
                Editor.loading = false;
                Editor.muestraAcciones(true);
            },
            success: function(resp) {
                if(resp.status == 1) {
                    Editor.loading = false;
                    Editor.cambiaPathActual(dir, '');
                    Admin.displayMessage(ProntusLangController.getString('_directory_created_successfully'), 'info');
                } else {
                    Admin.displayMessage(resp.msg, 'error');
                }
            }
        };
        SubmitForm.submitGenericAjax(config, opts);
    },


    // -------------------------------------------------------------------------
    accionRmdir: function() {

        if(!confirm(ProntusLangController.getString('_editor_accionrmdir_delete_confirmation') + "\n" + ProntusLangController.getString('_editor_accionrmdir_delete_confirmation2'))) {
            return false;
        }

        if(Editor.loading) {
            return;
        }
        Editor.loading = true;
        Editor.muestraAcciones(false);

        $('#type_item').val('dir');
        var dir = $('#_curr_dir').val();
        var config = {
            formSelector: '#form-editor',
            actionURL: Editor.urlBorrar,
        };
        var opts = {
            complete: function() {
                Editor.loading = false;
                Editor.muestraAcciones(true);
            },
            success: function(resp) {
                if(resp.status == 1) {
                    Editor.loading = false;
                    var nextdir = dir.substr(0, dir.lastIndexOf('/'));
                    Editor.cambiaPathActual(nextdir, '');
                    Admin.displayMessage(resp.msg, 'info');
                } else {
                    Admin.displayMessage(resp.msg, 'error');
                }
            }
        };
        //alert($('#type_item').val());
        SubmitForm.submitGenericAjax(config, opts);
    },

    // -------------------------------------------------------------------------
    accionBorrar: function() {

        if(!confirm(ProntusLangController.getString('_editor_accionborrar_confirm'))) {
            return;
        }

        if(Editor.loading) {
            return;
        }
        Editor.loading = true;
        Editor.muestraAcciones(false);


        $('#type_item').val('file');
        var dir = $('#_curr_dir').val();
        var config = {
            formSelector: '#form-editor',
            actionURL: Editor.urlBorrar
        };
        var opts = {
            complete: function() {
                Editor.loading = false;
                Editor.muestraAcciones(true);
            },
            success: function(resp) {
                if(resp.status == 1) {
                    Editor.loading = false;
                    Editor.cambiaPathActual(dir, '');
                    Admin.displayMessage(ProntusLangController.getString('_the_file_has_been_deleted'), 'info');
                } else {
                    Admin.displayMessage(resp.msg, 'error');
                }
            }
        };
        SubmitForm.submitGenericAjax(config, opts);
    },

    // -------------------------------------------------------------------------
    muestraAcciones: function(flag) {
        if(!flag) {
            $('.botones-accion .acciones').hide();
            $('.botones-accion .loading-action').fadeIn();
        } else {
            $('.botones-accion .loading-action').hide();
            $('.botones-accion .acciones').fadeIn();
        }
    },


    // -----------------------------------------------------------------------------
    insertMarca: function(selectObject) { // isTag = true | false
        var args = selectObject.options[selectObject.selectedIndex].value;
        var args_arr = args.split(",");

        var nomMarca = args_arr[0];
        var isTag = args_arr[1];
        var param;

        if (nomMarca === '') {
            Editor.selItemCero(selectObject);
            return;
        }

        if (isTag)  {
            var marca_open = '';
            var marca_close = '';

            if (nomMarca == 'IF') {
                param = prompt(ProntusLangController.getString('_editor_insertmarca_param') + "\n- " + ProntusLangController.getString('_editor_insertmarca_param2'), "");
                if ((param === null) || !Editor.validMarcaParam(nomMarca, param)) {
                    Editor.selItemCero(selectObject);
                    return;
                }
                marca_open = '\n%%IF(' + param + ')%%\n';
                marca_close = '\n%%/IF%%\n';

            } else if (nomMarca == 'NIF') {
                param = prompt(ProntusLangController.getString('_editor_insertmarca_nommarca_nif'), "");
                if ((param === null) || !Editor.validMarcaParam(nomMarca, param)) {
                    Editor.selItemCero(selectObject);
                    return;
                }
                marca_open = '\n%%NIF(' + param + ')%%\n';
                marca_close = '\n%%/NIF%%\n';

            } else if ((nomMarca.substr(0,3) == 'IFV') || (nomMarca == 'NIFV')) { // IFV, IFVC y NIFV
                param = prompt(ProntusLangController.getString('_editor_insertmarca_nommarca_ifv') + " " + nomMarca + ProntusLangController.getString('_editor_insertmarca_nommarca_ifv2'), "");
                if ((param === null) || !Editor.validMarcaParam(nomMarca, param)) {
                    Editor.selItemCero(selectObject);
                    return;
                }
                marca_open = '\n%%' + nomMarca + '(' + param + ')%%\n';
                marca_close = '\n%%/' + nomMarca + '%%\n';

            } else if (nomMarca == 'LOOP') {
                param = prompt(ProntusLangController.getString('_editor_insertmarca_nommarca_loop'), "");
                if ((param === null) || !Editor.validMarcaParam(nomMarca, param)) {
                    Editor.selItemCero(selectObject);
                    return;
                }
                marca_open = '\n%%LOOP' + param + '%%\n';
                marca_close = '\n%%/LOOP%%\n';
            }

            editAreaLoader.insertTags(Editor.idEditor, marca_open, marca_close);

        } else {
            var marca = '';

            if (nomMarca == 'MACRO') {
                param = prompt(ProntusLangController.getString('_editor_insertmarca_nommarca_macro'), "");
                if ((param === null) || !Editor.validMarcaParam(nomMarca, param)) {
                    Editor.selItemCero(selectObject);
                    return;
                }
                marca = '\n%%MACRO(' + param + ')%%\n';
            } else {
                marca = '%%' + nomMarca + '%%';
            }
            editAreaLoader.setSelectedText(Editor.idEditor, marca);
        }

        Editor.selItemCero(selectObject);
    },

    // -------------------------------------------------------------------------
    selItemCero: function(selectObject) {
        selectObject.options[0].selected = true;
    },

    // -------------------------------------------------------------------------
    validMarcaParam: function(nomMarca, param) {
        var expr = '';

        if (nomMarca == 'IF') {
            expr = /^(\w*|\w+ *= *[^=]+)$/;

        } else if (nomMarca == 'NIF') {
            expr = /^\w*$/;

        // IFV, IFVC y NIFV
        } else if ((nomMarca.substr(0,3) == 'IFV') || (nomMarca == 'NIFV')) {
            expr = /^([0-9]+,[0-9]+)?$/;

        } else if (nomMarca == 'LOOP') {
            expr = /^[0-9]+$/;

        } else if (nomMarca == 'MACRO') {
            expr = /^([^\\\/:\*\?"><\|\s]+)?$/;
        }

        var found = expr.exec(param);
        if (! found) {
          alert(ProntusLangController.getString('_invalid_parameter_for') + nomMarca);
          return false;
        }
        return true;
    },

    // -------------------------------------------------------------------------
    validFileName: function(param) {
        var expr = /^([^\\\/:\*\?"><\|\s]+)$/;
        var found = expr.exec(param);
        if (! found) {
            alert(ProntusLangController.getString('_invalid_file_name'));
            return false;
        }
        return true;
    }

};

