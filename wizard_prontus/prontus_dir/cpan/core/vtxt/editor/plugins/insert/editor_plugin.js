/**
 * editor_plugin_src.js
 *
 * Copyright 2013, CVI - Altavoz S.A.
 * Released under LGPL License.
 */

(function() {

    // Load plugin specific language pack
    tinymce.PluginManager.requireLangPack('insert');

    tinymce.create('tinymce.plugins.InsertPlugin', {

        /**
         * Initializes the plugin, this will be executed after the plugin has been created.
         * This call is done before the editor instance has finished it's initialization so use the onInit event
         * of the editor instance to intercept that event.
         */
        init : function(ed, url) {

            var thisref = this;

            var random = Math.random();
            // Register the command so that it can be invoked by using tinyMCE.activeEditor.execCommand('mceExample');
            this.editor = ed;
            ed.addCommand('mceInsert', function() {
                ed.windowManager.open({
                        file : url + '/dialog.htm?'+random,
                        width : 520 + parseInt(ed.getLang('insert.delta_width', 0)),
                        height : 380 + parseInt(ed.getLang('insert.delta_height', 0)),
                        inline : 1
                }, {
                        plugin_url : url, // Plugin absolute URL
                        some_custom_arg : 'custom arg' // Custom argument
                });
            });

            // Register the insert button
            ed.addButton('insert', {
                title : 'insert.desc',
                cmd : 'mceInsert',
                image : url + '/img/insert_code.png'
            });

            // Para que al presionar ENTER sobre un nodo "prontus", no genere otro nodo prontus
            ed.onChange.add(function(ed, l) {
                var node = tinyMCE.activeEditor.selection.getNode();
                if(node.nodeName === 'P' && node.className == 'mceItemInsert') {
                    var content = node.innerHTML;
                    if(content == '<br data-mce-bogus="1">' || content == '') {
                        node.className = '';
                        node.removeAttribute('class');
                        node.removeAttribute('type');
                        node.removeAttribute('src');
                        node.removeAttribute('code');
                    }
                }
            });

            // Add a node change handler, selects the button in the UI when a image is selected
            ed.onNodeChange.add(function (ed, cmd, n) {
                if(n && n.nodeName === "P" && ed.dom.hasClass(n, "mceItemInsert")) {
                    cmd.setActive("insert", true);
                } else {
                    cmd.setActive("insert", false);
                };
            });

            // Agregar un css con estilos
            var head  = document.getElementsByTagName('head')[0];
            var link  = document.createElement('link');
            link.rel  = 'stylesheet';
            link.type = 'text/css';
            link.href = url + '/css/content.css';
            link.media = 'all';
            head.appendChild(link);

            // Se ejecuta antes de cargar el VTXT
            ed.onPreInit.add(function () {
                ed.schema.addValidElements("prontus:insert[src|type|code|title],p[src|type|code|title|class|dir<ltr?rtl|id|lang|onclick"
                        +"|ondblclick|onkeydown|onkeypress|onkeyup|onmousedown|onmousemove"
                        +"|onmouseout|onmouseover|onmouseup|style|title],");
                ed.parser.addNodeFilter("p", function (nodes) {
                    var pointer = nodes.length;
                    while (pointer--) {
                        thisref.parseNode(nodes[pointer], ed.schema);
                    }
                });
                ed.serializer.addNodeFilter("p", function (nodes) {
                    var tot = nodes.length;
                    while (tot--) {
                        var myclass = nodes[tot].attr('class');
                        //TODO - Robustecer esta validacion (split para todas las clases)
                        if(myclass == "mceItemInsert") {
                            thisref.serializeNode(nodes[tot], ed.schema);
                        }
                    }
                });
            });
            // Se ejecuta al cargar el VTXT
            ed.onInit.add(function () {
                if (ed.theme && ed.theme.onResolveName) {
                    ed.theme.onResolveName.add(function (s, t) {
                        if (t.name === "p" && ed.dom.hasClass(t.node, "mceItemInsert")) {
                            t.name = "vtxt_include"
                        }
                    })
                }
            });
        },

        /**
         * Método encargado de convertir un nodo del tipo: <prontus:insert></prontus:insert>
         * en un nodo P para que sea desplegado dentro del TinyMce
         **/
        parseNode: function(node, schema) {

            if(node.firstChild && node.firstChild.name == 'prontus:insert') {

                var html;
                var newnode = node.firstChild;

                if(newnode.attr('type') == 'js') {
                    if(newnode.attr('src')) {
                        html = '<p class="mceItemInsert" type="js" src="'+newnode.attr('src')+'">Include Javascript</p>';

                    } else if(newnode.attr('code')) {
                        html = '<p class="mceItemInsert" type="js" code="'+newnode.attr('code')+'">Código Javascript</p>';

                    } else {
                        node.empty();
                        return;
                    }
                } else if(newnode.attr('type') == 'php') {
                    html = '<p class="mceItemInsert" type="php" src="'+newnode.attr('src')+'">Include PHP</p>';

                } else if(newnode.attr('type') == 'ssi') {
                    html = '<p class="mceItemInsert" type="ssi" src="'+newnode.attr('src')+'">Include SSI</p>';
                } else if(newnode.attr('type') == 'ssi2') {
                    html = '<p class="mceItemInsert" type="ssi2" src="'+newnode.attr('src')+'">Include SSI Virtual</p>';

                } else {
                    node.empty();
                    return;
                }

                var parser = new tinymce.html.DomParser({validate: false}, schema);

                var rootNode = parser.parse(html);
                node.replace(rootNode);
            }
        },

        /**
         * Este método hace lo contrario del metodo anterior: transforma un nodo P en un nodo del
         * tipo: <prontus:insert></prontus:insert> para ser desplegado dentro del editor de HTML
         **/
        serializeNode: function(node, schema) {


            var serializer = new tinymce.html.Serializer();
            var text = serializer.serialize(node);
            text = this.decodeText(text);

            var type = node.attr('type');
            var src = node.attr('src');
            var code = node.attr('code');
            var extra;
            if(typeof code !== 'undefined') {
                extra = 'code="'+code+'"';
            } else {
                extra = 'src="'+src+'"';
            }

            var html = '<prontus:insert type="'+type+'" '+extra+'>'+text+'</prontus:insert>';
            var parser = new tinymce.html.DomParser({validate: true}, schema);
            var rootNode = parser.parse(html);

            node.replace(rootNode);
        },

        /**
         * Codifica un texto desde nodo <prontus:insert> a nodo <p>
         * Actualmente no se utiliza. En una próxima iteración se debería eliminar
         **/
        encodeText: function(text) {
            //TODO: Ver si esto se puede eliminar
            text = text.replace(/<\/?prontus:insert>/g, '');
            text = text.replace(/</g, '&lt;');
            text = text.replace(/>/g, '&gt;');
            text = text.replace(/\?/g, '&#63;');
            text = text.replace(/p/g, '&#112;');
            return text;
        },

        /**
         * Codifica el texto desde nodo <p> para ser usado como nodo <prontus:insert>
         * Básicamente, elimina el P y toma el contenido. Esto se debería eliminar a
         * futuro cuando haya mas tiempo, debe haber una forma mucho más facil de extraer
         * el contenido del nodo.
         */
        decodeText: function(text) {
            //TODO: Ver si esto se puede eliminar
            text = text.replace(/&lt;/g, '<');
            text = text.replace(/&gt;/g, '>');
            text = text.replace(/&#63;/g, '?');
            text = text.replace(/&#112;/g, 'p');
            text = text.replace(/^<p .*?>(.*?)<\/p>$/g, "$1");
            return text;
        },

        /**
         * Returns information about the plugin as a name/value array.
         * The current keys are longname, author, authorurl, infourl and version.
         */
        getInfo : function() {
            return {
                longname : 'Insert plugin',
                author : 'Cesar Vasquez',
                authorurl : 'http://www.prontus.cl',
                version : "1.0"
            };
        }
    });


    // Register plugin
    tinymce.PluginManager.add('insert', tinymce.plugins.InsertPlugin);
})();

