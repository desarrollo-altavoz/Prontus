tinyMCEPopup.requireLangPack();

var InsertDialog = {

    init : function() {

        // TODO: Traducir el plugin Insert al inglés

        var f = document.forms[0];
        var editor = tinyMCEPopup.editor;
        var node = editor.selection.getNode();


        // Primero se carga el cuadro, si es que es una edición
        if(node.nodeName === 'BODY') {
            editor.setContent('<p></p>');
            //console.log(Admin.debugPrintObject(node.firstChild, true));
            if(typeof node.firstElementChild !== 'undefined') {
                node = node.firstElementChild;
            }
        }
        if(node.className == 'mceItemInsert') {
            //console.log(node.nodeName);
            this.codeToForm(node);

        } else {
            // Si no es una edición, se carga el html type, por defecto
            var tipohtml = (tinyMCE.customDataIncludeType) ? tinyMCE.customDataIncludeType : '';
            this.setCombo('insert_html_type', tipohtml);
        }
    },

    insert : function() {
        this.updateInsertType();

        var editor = tinyMCEPopup.editor;
        var rootNode = this.formToNode();
        if(rootNode) {
            editor.execCommand('mceRepaint');
            tinyMCEPopup.restoreSelection();

            // TODO: Pulir esta parte para no dejar la escoba con nodos mezclados
            var rootPar = editor.dom.getParent(tinyMCE.activeEditor.selection.getNode());
            if(rootPar.nodeName === 'P') {
                rootPar.parentNode.replaceChild(rootNode, rootPar);
                tinyMCEPopup.close();
            } else if(rootPar.nodeName === 'BODY') {

                if(typeof rootPar.firstElementChild !== 'undefined') {
                    rootPar = rootPar.firstElementChild;
                    rootPar.replaceChild(rootNode, rootPar);
                    tinyMCEPopup.close();

                } else {
                    if(rootPar.childNodes.length > 0) {
                        rootPar.replaceChild(rootNode, rootPar.firstChild);
                        tinyMCEPopup.close();
                    } else {
                        console.log(rootNode.nodeName);
                        var serializer = new tinymce.html.Serializer();
                        var text = serializer.serialize(rootNode);
                        console.log(text);
                        tinyMCE.activeEditor.setContent(text);
                        tinyMCEPopup.close();
                        //console.log(.getNode().nodeName);
                        //console.log(Admin.debugPrintObject(rootPar, false));
                        //tinyMCEPopup.close();
                    }


                }

            }
        }
    },

    displayTab: function(tab, panel) {
        var tipo = panel.replace(/_panel$/, '');
        mcTabs.displayTab(tab, panel);
        this.updateInsertType();
    },

    updateInsertType: function() {
        var ul = document.getElementById('tabs');
        var lis = ul.childNodes;
        for(x in lis) {
            if(lis[x].className == 'current') {
                var theid = lis[x].getAttribute('id');
                var tipo = theid.replace(/_tab$/, '');
                this.setVal('tipo_insert', tipo);
                return;
            }
        }
    },

    updateJsType: function() {
        var tipojs = this.getVal('insert_js_type');
        document.getElementById('tr_tab_code').style.display = 'none';
        document.getElementById('tr_tab_file').style.display = 'none';
        document.getElementById('tr_tab_'+tipojs).style.display = 'block';
    },

    formToNode: function() {

        var formu = document.forms[0];
        var editor = tinyMCEPopup.editor;
        var tipo = this.getVal('tipo_insert');
        var html;

        var node_type;
        var node_src;
        var node_code;
        var node_text;

        if(tipo == 'html') {
            var tipohtml = this.getVal('insert_html_type');
            if(tipohtml == '') {
                // Manejar este error
                alert('Debe indicar el "Tipo de include a realizar"');
                return;
            }
            var htmlfile = this.getVal('insert_file');
            if(htmlfile === '') {
                // Validar el archivo de alguna forma
                alert('Debe indicar la "Ruta al archivo"');
                return;
            }
            if(tipohtml == 'ssi') {
                node_type = 'ssi';
                node_text = 'Include SSI';
                node_src = htmlfile;
            } else if(tipohtml == 'ssi2') {
                node_type = 'ssi2';
                node_text = 'Include SSI Virtual';
                node_src = htmlfile;
            } else {
                node_type = 'php';
                node_text = 'Include PHP';
                node_src = htmlfile;
            }

        } else {
            var tipojs = this.getVal('insert_js_type');
            node_type = 'js';
            if(tipojs == 'code') {
                var jscode = this.getVal('insert_js_code');
                if(jscode === '') {
                    // Validar el archivo de alguna forma
                    alert('Debe indicar el campo "Código Javascript"');
                    return;
                }
                jscode = encodeURIComponent(jscode);
                node_text = 'Código Javascript';
                node_code = jscode;

            } else {
                var jsfile = this.getVal('insert_js_file');
                if(jsfile === '') {
                    // Validar el archivo de alguna forma
                    alert('Debe indicar el campo "Ruta del archivo"');
                    return;
                }
                node_text = 'Include Javascript';
                node_src = jsfile;
            }
        }

        rootNode = editor.dom.create("p", {
            "class": "mceItemInsert",
            "type": node_type
        });

        //console.log(rootNode.className);
        if(node_src) {
            rootNode.setAttribute('src', node_src);
        } else if(node_code) {
            rootNode.setAttribute('code', node_code);
        } else {
            alert('Error al crear el nodo de destino.');
            return;
        }

        rootNode.innerHTML = node_text;
        return rootNode;

    },

    codeToForm: function(node) {

        var editor = tinyMCEPopup.editor;
        var tipo = node.getAttribute('type');
        if(tipo == 'php') {
            this.displayTab('html_tab','html_panel');
            this.setCombo('insert_html_type', 'php');
            var src = node.getAttribute('src');
            var input = document.getElementById('insert_file');
            input.value = src;

        } else if(tipo == 'ssi') {
            this.displayTab('html_tab','html_panel');
            this.setCombo('insert_html_type', 'ssi');
            var src = node.getAttribute('src');
            var input = document.getElementById('insert_file');
            input.value = src;

        } else if(tipo == 'ssi2') {
            this.displayTab('html_tab','html_panel');
            this.setCombo('insert_html_type', 'ssi2');
            var src = node.getAttribute('src');
            var input = document.getElementById('insert_file');
            input.value = src;

        } else if(tipo == 'js') {
            this.displayTab('js_tab','js_panel');
            var src = node.getAttribute('src');
            if(src !== null) {
                this.setCombo('insert_js_type', 'file');
                this.updateJsType();
                var input = document.getElementById('insert_js_file');
                input.value = src;

            } else {
                var code = node.getAttribute('code');
                if(code !== null) {
                    var text = decodeURIComponent(code);
                    this.setCombo('insert_js_type', 'code');
                    this.updateJsType();
                    var textarea = document.getElementById('insert_js_code');
                    textarea.innerHTML = text;
                }
            }
        }
    },

    setCombo: function(combo, valor) {
        var sel = document.getElementById(combo);
        sel.selectedIndex = 0;
        for(var i, j = 0; i = sel.options[j]; j++) {
            if(i.value == valor) {
               sel.selectedIndex = j;
               return;
            }
        }
    },

    getVal: function(id) {
        var elm = document.getElementById(id);

        if (elm.nodeName == "SELECT")
            return elm.options[elm.selectedIndex].value;

        if (elm.type == "checkbox")
            return elm.checked;

        return elm.value;
    },

    setVal: function(id, val) {
        var elm = document.getElementById(id);

        if (elm.nodeName == "SELECT")
            return;

        if (elm.type == "checkbox")
            return;

        elm.value = val;
    }

};

tinyMCEPopup.onInit.add(InsertDialog.init, InsertDialog);
