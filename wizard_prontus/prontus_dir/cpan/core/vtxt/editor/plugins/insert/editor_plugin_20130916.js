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
                        width : 500 + parseInt(ed.getLang('insert.delta_width', 0)),
                        height : 350 + parseInt(ed.getLang('insert.delta_height', 0)),
                        inline : 1
                }, {
                        plugin_url : url, // Plugin absolute URL
                        some_custom_arg : 'custom arg' // Custom argument
                });
            });

            // Register example button
            ed.addButton('insert', {
                title : 'insert.desc',
                cmd : 'mceInsert',
                image : url + '/img/insert_code.png'
            });

            // Add a node change handler, selects the button in the UI when a image is selected
            ed.onNodeChange.add(function(ed, cm, n) {
                cm.setActive('insert', n.nodeName == 'IMG');
            });

            var head  = document.getElementsByTagName('head')[0];
            var link  = document.createElement('link');
            link.rel  = 'stylesheet';
            link.type = 'text/css';
            link.href = url + '/css/content.css';
            link.media = 'all';
            head.appendChild(link);

            ed.onPreInit.add(function () {
                ed.schema.addValidElements("prontus:insert");
                ed.parser.addNodeFilter("prontus:insert", function (nodes) {
                    var pointer = nodes.length;
                    while (pointer--) {
                        thisref.parseNode(nodes[pointer], ed.schema);
                    }
                });
                ed.serializer.addNodeFilter("div", function (nodes) {
                    var tot = nodes.length;
                    while (tot--) {
                        var myclass = nodes[tot].attr('class');
                        //TODO - Robustecer esta validacion (split para todas las clases)
                        if(myclass == "mceItemInsert") {
                            thisref.serializeNode(nodes[tot], ed.schema);
                        }
                    }
                })
            });
            ed.onInit.add(function () {
                if (ed.theme && ed.theme.onResolveName) {
                    ed.theme.onResolveName.add(function (s, t) {
                        if (t.name === "img" && ed.dom.hasClass(t.node, "vtxt_include")) {
                            t.name = "vtxt_include"
                        }
                    })
                }
            });


        },

        parseNode: function(node, schema) {
            //var text = node.innerHTML;
            //var node = node.unwrap();
            //var content = new tinymce.html.Serializer().serialize(node.firsChild);
            //var code = span.replace(/<span.*?>(.*?)<\/span>/, "$1");
            //var content = node;

            //alert(Admin.debugPrintObject(node, true));

            var content = node.firstChild;
            var serializer = new tinymce.html.Serializer();
            var text = serializer.serialize(node.firstChild);
            text = text.replace(/</g, '&lt;');
            text = text.replace(/>/g, '&gt;');

            //alert(text);
            var html = '<div class="mceItemInsert">'+text+'</div>';
            var parser = new tinymce.html.DomParser({validate: true}, schema);
            var rootNode = parser.parse(html);
            //rootNode.append();
            //rootNode.append(node);
            node.replace(rootNode);

            //alert(node.getContent());
            //~ var div = this.editor.dom.create("div", {
                //~ width: '100%',
                //~ height: '50',
                //~ "class": "mceItemInsert"
                //~ //"class": "mceItemMedia mceItem" + this.getType(data.type).name,
                //~ //"data-mce-json": tinymce.util.JSON.serialize(, "'")
            //~ });
            //~ node.replace(div);
        },

        serializeNode: function(node, schema) {

            var content = node.firstChild;
            var serializer = new tinymce.html.Serializer();
            var text = serializer.serialize(node.firstChild);

            //alert('serializando');
            text = text.replace(/&lt;/g, '<');
            text = text.replace(/&gt;/g, '>');

            var content = node.firstChild;
            var serializer = new tinymce.html.Serializer();
            var text = serializer.serialize(node.firstChild);
            text = text.replace(/</g, '&lt;');
            text = text.replace(/>/g, '&gt;');

            //alert(text);
            var html = '<prontus:insert>'+text+'</prontus:insert>';
            var parser = new tinymce.html.DomParser({validate: true}, schema);
            var rootNode = parser.parse(html);
            //rootNode.append();
            //rootNode.append(node);
            node.replace(rootNode);

            var json = node.attr('data-mce-json');
            if(json) {
                var code = tinymce.util.JSON.parse(json);
                code = '<span class="vtxt_include">'+code+'</span>';
                var parser = new tinymce.html.DomParser({validate: false}, schema);
                var rootNode = parser.parse(code);
                node.replace(rootNode);
            } else {
                node.remove();
            }
        },

        codeToImg: function (code) {
            //'<div class="vtxt_include">'
            var random = Math.random();
            var editor = this.editor;
            var data = {};
            data.code = code;
            var div = editor.dom.create("div", {
                id: 'insert'+random,
                width: '100%',
                height: '50',
                src: editor.theme.url + "/img/trans.gif",
                "class": "mceItemInsert",
                //"class": "mceItemMedia mceItem" + this.getType(data.type).name,
                "data-mce-json": tinymce.util.JSON.serialize(data, "'")
            });
            return imagen;
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
