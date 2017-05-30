var GaleriaProntus = {
    separadorTexto: '||==',
    separadorImagen: '|',
    total: 0,
    cantidadTamanos: 0,
    flag: '',
    pproc_working: false,
    errorCounter: 0,
    procesarDD: 0,
    firstInit: 0,

    cgi_borrar: 'galeria/prontus_galeria_garbage.cgi',
    // mensajes del proceso de archivo
    msg_confirm: "¿Está seguro que desea guardar el FID?\nEl proceso de upload masivo de imágenes aún no termina.",
    msg_process: 'Se están procesando los archivos subidos. No guarde este FID hasta que termine.',
    msg_error_zip: 'El archivo cargado no tiene extensión Zip. Suba un archivo zip y vuelva a guardar el artículo',
    msg_error_resp: 'Se ha producido un error en el procesamiento del Zip. Guarde de nuevo el artículo o suba otro archivo zip.',
    msg_error_com: 'Se ha producido un error de comunicación, se recargará el fid.',

    // --------------------------------------------------------------------
    init: function(flag) {
        if (!document.getElementById('_prontus_galeria_subtab1')) {
            return;
        }
        GaleriaProntus.flag = flag;
        GaleriaProntus.img_process = '<br/><img src="/'+Admin.prontus_id+'/cpan/core/imag/loading.gif" style="vertical-align:bottom;">';

        if (GaleriaProntus.procesarDD == 0) {
            GaleriaProntus.verificarZip();
        }

        if (GaleriaProntus.firstInit == 0) {
            $('#_gal_archive').blur(GaleriaProntus.verificaArchivoCargado);
        }

        // Primero que todo obtenemos un arreglo con las fotos temporales:
        var conf = $('#_galeria_prontus_conf').val();
        var arrconf = conf.split('|');
        GaleriaProntus.ArregloFotos = {};
        GaleriaProntus.cantidadTamanos = arrconf.length;
        for(x in arrconf) {
            var item = arrconf[x];
            var arritem = item.split(':');
            if(arritem.length == 2) {
                var num = arritem[0];
                var foto = arritem[1];
                var iframe = "FOTOFIJA_prontus_galeria_temporal"+num;
                var tam_foto_w = $('input[name="_MAXWFOTOFIJA_prontus_galeria_temporal'+num+'"]').val();
                var tam_foto_h = $('input[name="_MAXHFOTOFIJA_prontus_galeria_temporal'+num+'"]').val();
                GaleriaProntus.ArregloFotos['fotofija_prontus_galeria_temporal'+num] = {
                    num: num,
                    nombre: foto,
                    iframe: iframe,
                    ancho: tam_foto_w,
                    alto: tam_foto_h
                };
            }
        }

        // para evitar confusiones se esconde el banco de imagenes al subir fotos
        $('#_show_galeria_subtab2').click(function() {
            $('#banco-img').fadeOut(300);
        })
        // aseguramos que se muestre al editar la galeria
        $('#_show_galeria_subtab1').click(function() {
            $('#banco-img').fadeIn(300);
        })

        // Vemos si pudimos extraer algo de la conf
        if (GaleriaProntus.cantidadTamanos < 2) {
            GaleriaProntus.showMsg('Error en la configuración de la galería');
            return;
        }

        // Creamos los campos variables para el PostProceso
        for (x in GaleriaProntus.ArregloFotos) {
            var obj = GaleriaProntus.ArregloFotos[x];
            $('#_imagen_temporal').append('<input type="hidden" name="tam_galeria_prontus_'+obj.num+'" value="'+obj.ancho+':'+obj.alto+'" />');
        }

        // Cargamos los datos de la galeria para usarlos en el fid
        var galerias_str = $('#_galeria_prontus_str').val();
        var gal_str = galerias_str.split('@@');
        for (var i = 0; i < gal_str.length; i++) {
            $('#_galeria_prontus_str'+(i+1)).val(gal_str[i]);
        }

        // Si viene de una foto nueva, se debe agregar al saco y guardar de nuevo
        if (flag == 'si') {
            GaleriaProntus.addFoto();
        }

        // El drag and drop se deja instalado
        GaleriaProntus.iniciarArrastrarSoltar();

        // Valida que los largos sean correctos
        GaleriaProntus.cargaDatosFotos();

        if(GaleriaProntus.total == 0) {
            // console.log('No hay fotos que desplegar');
            return;
        }

        // Se indica el total de fotos
        $('#_galeria-prontus-total').html(GaleriaProntus.total);

        // Se cargan los datos en los input para que puedan guardar el FID
        GaleriaProntus.cargarDatosTexto();

        // Se agregan los thumb items al contenedor
        $('#_content-galeria-prontus').append('<ul id="_prontus-galeria-sortable"></ul>');
        for(var i = 0; i < GaleriaProntus.total; i++) {
            var idx = i + 1;
            i2 = (idx < 10) ? '0'+idx: ''+idx;
            var iditem = '#_prontus-foto'+idx;

            // Se recorren los distintos tamaños
            for(x in GaleriaProntus.ArregloFotos) {
                var obj = GaleriaProntus.ArregloFotos[x];
                // Considerando que podrian ser fotos externas ## revisar
                var foto = obj.arreglo[i];
                var ts = foto.substr(13, 14);
                var fechac = ts.substr(0, 8);
                var fullfoto = '/'+Admin.prontus_id+'/site/artic/'+fechac+'/imag/'+foto;

                if (obj.num == 1) {
                    $('#_prontus-galeria-sortable').append('<li class="item" id="_prontus-foto'+idx+'"></li>');
                    $(iditem).append('<div class="_prontus-img-container" ><img class="thumb"></div>');
                    $(iditem + ' .thumb').attr('src', fullfoto);
                    $(iditem).append($('#_matrix .botonera').clone());
                }
                if (obj.num == GaleriaProntus.cantidadTamanos) {
                    $(iditem + ' .botonera .show').attr('href', fullfoto);
                }
                var nombrefoto = obj.nombre;
                nombrefoto = nombrefoto.replace('@@', idx);
                $(iditem).append('<input type="hidden" name="'+nombrefoto+'" class="field-foto'+x+'" value="'+fullfoto+'">');
                $(iditem).append('<input type="hidden" name="_MAXW'+nombrefoto+'" class="field-foto'+x+'-maxw" value="' + obj.ancho + '">');
                $(iditem).append('<input type="hidden" name="_MAXH'+nombrefoto+'" class="field-foto'+x+'-maxh" value="' + obj.alto + '">');
            }

            $(iditem).append('<input type="hidden" name="txt_galeria_descripcion_foto'+idx+'" class="field-descripcion" value="'+GaleriaProntus.arrdesc[i]+'">');
            $(iditem).append('<input type="hidden" name="txt_galeria_credito_foto'+idx+'" class="field-credito" value="'+GaleriaProntus.arrcred[i]+'">');
        }

        // Si viene de una foto nueva, se debe agregar al saco y guardar de nuevo
        if(flag == 'si') {
            Fid.submitir('save', '_self');
            return;
        }

        // Se instancia el handler para ordenar
        $('#_prontus-galeria-sortable').sortable({
            placeholder: "placeholder"
        }).disableSelection();

        // Los eventos para los botones
        $('#_content-galeria-prontus #_prontus-galeria-sortable li .show, #_content-galeria-prontus ._prontus-img-container').live('click', function() {
            var iditem = $(this).parents('.item').attr('id');
            GaleriaProntus.accionShow('#'+iditem);
            return false;
        });
        $('#_content-galeria-prontus #_prontus-galeria-sortable li .edit').live('click', function(event) {
            var iditem = $(this).parents('.item').attr('id');
            GaleriaProntus.accionEdit('#'+iditem, event);
            return false;
        });
        $('#_content-galeria-prontus #_prontus-galeria-sortable li .delete').live('click', function() {
            var iditem = $(this).parents('.item').attr('id');
            GaleriaProntus.accionDelete('#'+iditem);
        });

        // Se inicia el dialogo
        GaleriaProntus.iniciarDialogo();
        GaleriaProntus.firstInit = 1;
    },

    // --------------------------------------------------------------------
    addFoto: function() {
        // Se recorren los distinos tamaños
        for(name in GaleriaProntus.ArregloFotos) {
            var obj = GaleriaProntus.ArregloFotos[name];
            var iframe = obj.iframe;
            var foto = document.getElementsByName(iframe)[1].value;
            if(obj.num == 1 && foto == '') {
                return;
            }
            foto = foto.substr(foto.lastIndexOf('/') + 1);
            var strfotos = $('#_galeria_prontus_str'+obj.num).val();
            strfotos = (strfotos) ? GaleriaProntus.separadorImagen+strfotos : '';
            $('#_galeria_prontus_str'+obj.num).val(foto+strfotos);

            Fid.borraFotoFija(iframe);
        }

        var strdesc = $('#_txt_galeria_description_total').val();
        strdesc = (strdesc) ? GaleriaProntus.separadorTexto+strdesc : '';
        $('#_txt_galeria_description_total').val(strdesc);

        var strcred = $('#_txt_galeria_credito_total').val();
        strcred = (strcred) ? GaleriaProntus.separadorTexto+strcred : '';
        $('#_txt_galeria_credito_total').val(strcred);
    },
    // --------------------------------------------------------------------
    cargaDatosFotos: function() {
        var thumbs = new Array();

        // Se obtienen los arreglos
        for(x in GaleriaProntus.ArregloFotos) {
            var obj = GaleriaProntus.ArregloFotos[x];
            var strfotos = $('#_galeria_prontus_str'+obj.num).val();
            if (obj.num == '5' && strfotos == '') {
                strfotos = $('#_galeria_prontus_str2').val();
                $('#_galeria_prontus_str5').val(strfotos);
            }

            if (strfotos == '') {
                GaleriaProntus.total = 0;
                return;
            }
            GaleriaProntus.ArregloFotos[x].arreglo = strfotos.split(GaleriaProntus.separadorImagen);
            if (obj.num == '1') {
                GaleriaProntus.total = GaleriaProntus.ArregloFotos[x].arreglo.length;
            }
        }

        // Se validan los arreglos
        for(x in GaleriaProntus.ArregloFotos) {
            var arr = GaleriaProntus.ArregloFotos[x].arreglo;
            if(typeof arr === 'undefined' || arr.length !== GaleriaProntus.total) {
                GaleriaProntus.showMsg('Los largos de los arreglos no coinciden');
                GaleriaProntus.total = 0;
                return;
            }
        };
    },
    // --------------------------------------------------------------------
    cargarDatosTexto: function() {
        // Se cargan las descripciones
        var desctotal = GaleriaProntus.limpiadorCaracteres($('#_txt_galeria_description_total').val());
        var arrdesc = new Array ();
        if(desctotal === '') {
            // Se carga con vacios
            for(var y=0 ; y < GaleriaProntus.total ; y++) {
                arrdesc[y] = '';
            }
            desctotal = arrdesc.join(GaleriaProntus.separadorTexto);
            $('#_txt_galeria_description_total').val(desctotal);
        } else {
            arrdesc =  desctotal.split(GaleriaProntus.separadorTexto);
            if(arrdesc.length != GaleriaProntus.total) {
                GaleriaProntus.showMsg('El número de descripciones no coinciden');
            }
        }
        GaleriaProntus.arrdesc = arrdesc;

        // Se cargan los creditos
        var credtotal = GaleriaProntus.limpiadorCaracteres($('#_txt_galeria_credito_total').val());
        var arrcred = [GaleriaProntus.total];
        if(credtotal === '') {
            // Se carga con vacios
            for(var y=0 ; y < GaleriaProntus.total ; y++) {
                arrcred[y] = '';
            }
            credtotal = arrcred.join(GaleriaProntus.separadorTexto);
            $('#_txt_galeria_credito_total').val(credtotal);
        } else {
            arrcred =  credtotal.split(GaleriaProntus.separadorTexto);
            if(arrcred.length != GaleriaProntus.total) {
                GaleriaProntus.showMsg('El número de creditos no coinciden');
            }
        }
        GaleriaProntus.arrcred = arrcred;
    },
    // --------------------------------------------------------------------
    iniciarArrastrarSoltar:function() {
        $('#scroll-banco .foto-icon img').live('mouseover',function() {
            if ($(this).attr('dragflag') != 'true') {
                $(this).draggable({
                    appendTo: "body",
                    helper: "clone"
                });
                $(this).attr('dragflag', 'true');
            };
            if ($('#_content-galeria-prontus').parents('.cabecera').is(':visible')) {
                $(this).draggable("enable");
            } else {
                $(this).draggable("disable");
            };
        });

        $("#_addimage-galeria-prontus").droppable({
            activeClass: "ui-state-default",
            hoverClass: "ui-state-hover",
            accept: ":not(.ui-sortable-helper)",
            drop: function(event, ui) {

                // Se cargan todas las fotofijas definidas
                var fullfoto = $(ui.draggable).parent().html();
                for(name in GaleriaProntus.ArregloFotos) {
                    var checked = (GaleriaProntus.ArregloFotos[name].num == '1') ? 'checked' : '';
                    $('#'+GaleriaProntus.ArregloFotos[name].iframe).contents().find('body').append(fullfoto).find('img').css('max-width', '80px');
                    $('input[name="CHK_cuadrar_'+GaleriaProntus.ArregloFotos[name].iframe+'"]').attr('checked', checked);
                }
                $('#_imagen_temporal').append('<input type="hidden" id="_galeria_flag_imagen_temporal" name="_galeria_flag_imagen_temporal">');
                $('#_galeria_flag_imagen_temporal').val('si');

                Fid.submitir('save', '_self');
            }
        })

        /* Mostrar drag & drop siempre y cuando este soportado. */
        if (Fid.showDragDrop) {
            var id_art = mainFidJs.TS;
            if (id_art == '') {
                id_art = (new Date()).getTime();
            }
            // Iniciar upload Drag & Drop
            $('#_galeria_fileInputDD').fileupload({
                dataType: 'text',
                url: 'galeria/prontus_galeria_upfoto_dd.cgi',
                dropZone: $('#_galeria_dropZone'),
                formData: { prontus_id: mainFidJs.PRONTUS_ID,
                            ts: id_art
                        },
                done: function (e, data) {
                    var response = JSON.parse(data.result);
                    if (response.status == '0') {
                        $('#_galeria_imagenescargadas').append('<div class="prontus-imagenescargadas">' +
                                '<div class="img-error">Imagen con errores</div>' +
                                '</div>');
                    } else if (response.status == '1') {
                        var idFoto       = response.data.idFoto;
                        var wFoto        = response.data.wFoto;
                        var hFoto        = response.data.hFoto;
                        var relPath      = response.data.relPath;
                        var nomFile      = response.data.nomFile;
                        var realNomFile  = response.data.realNomFile ;
                        var labelSize = '<br/><span class="ST">(' + wFoto + ' x ' + hFoto + ')</span>';
                        $('#_galeria_imagenescargadas').append('<div class="prontus-imagenescargadas">' +
                                '<div>' + realNomFile + labelSize + '</div>' +
                                '<img src="' + relPath + '" id="' + idFoto  + '" >' +
                                '</div>');
                        if (typeof $('input[name="_HIDD__gal_archive"]').val() === 'undefined' || $('input[name="_HIDD__gal_archive"]').val() == '') {
                            $('#_gal_archive').after('<input name="_HIDD__gal_archive" value="_prontus_galeria_'+id_art+'.zip" id="_HIDD__gal_archive" type="hidden" />');
                        }
                        GaleriaProntus.procesarDD = 1;
                    }
                },
                progressall: function (e, data) {
                    var progress = parseInt(data.loaded / data.total * 100, 10);
                    $('#_galeria_uploadProgressBar').css('width', progress + '%');
                    $('#_galeria_uploadProgressPercent').text(progress+'%');
                },
                stop: function (e) {
                    $('#_galeria_uploadProgressBar').css('width', '100%');
                    $('#_galeria_uploadProgressPercent').text('100%');
                    $('#_galeria_fileInputDD').fileupload('disable');
                    $('#_galeria_dropZone').css('cursor', 'not-allowed');
                    setTimeout(function () {
                        $('#_galeria_uploadProgressContainer').hide();
                        $('#_galeria_uploadcomplete').show();
                        Fid.submitir('Guardar', '_self');
                    }, 1000);
                },
                drop: function (e, data) {
                    /* Validar extensiones de archivo. */
                    var fail = false;
                    $.each(data.files, function (index, file) {
                        var ext = (file.name).split('.').pop().toLowerCase();
                        if ($.inArray(ext, ['gif','png','jpg','jpeg', 'zip']) == -1) {
                            alert("El archivo [" + file.name + "] es inválido.\nLos archivos permitidos son imágenes gif, png, jpg o jpeg; o un comprimido .zip con imágenes.");
                            fail = true;
                            return false;
                        }
                    });

                    if (fail) {
                        return false; /* al retornar false, se detiene la ejecución del plugin. */
                    }

                    $('#_galeria_uploadProgress').show();
                }
            });
        }
    },
    // --------------------------------------------------------------------
    guardarGaleriaProntus: function() {
        var strdesc = '';
        var strcred = '';

        // Se borran las actuales
        for(name in GaleriaProntus.ArregloFotos) {
            var obj = GaleriaProntus.ArregloFotos[name];
            var num = obj.num;
            $('#_galeria_prontus_str'+num).val('');
        }

        var galeria_str = new Array();
        // Se agregan las nuevas fotos
        $('#_prontus-galeria-sortable .item').each(function(indice) {
            var iditem = '#'+$(this).attr('id');
            var idx = indice + 1;

            // Se procesan las fotos por separado
            for (name in GaleriaProntus.ArregloFotos) {
                var obj = GaleriaProntus.ArregloFotos[name];
                var num = obj.num;
                var realname = obj.nombre;
                realname = realname.replace('@@', idx);
                $(iditem).find('.field-foto'+num).attr('name', realname);
                $(iditem).find('.field-foto'+num+'-maxw').attr('name', '_maxw'+realname);
                $(iditem).find('.field-foto'+num+'-maxh').attr('name', '_maxh'+realname);

                var foto = $(iditem).find('.field-foto'+name).val();
                foto = foto.substr(foto.lastIndexOf('/') + 1);

                var strtot = $('#_galeria_prontus_str'+num).val();
                strtot = (indice == 0) ? foto : strtot + GaleriaProntus.separadorImagen + foto;
                $('#_galeria_prontus_str'+num).val(strtot);
                galeria_str[num] = strtot;
            }

            $(iditem).find('.field-descripcion').attr('name', 'txt_galeria_descripcion_foto'+idx);
            $(iditem).find('.field-credito').attr('name', 'txt_galeria_credito_foto'+idx);

            if (indice == 0) {
                strdesc = $(iditem).find('.field-descripcion').val();
                strcred = $(iditem).find('.field-credito').val();
            } else {
                strdesc = strdesc + GaleriaProntus.separadorTexto + $(iditem).find('.field-descripcion').val();
                strcred = strcred + GaleriaProntus.separadorTexto + $(iditem).find('.field-credito').val();
            };
        });
        var str_gal = galeria_str.join('@@');
        str_gal = str_gal.replace(/^@@/,'');
        $('#_galeria_prontus_str').val(str_gal);

        // Finalmente se guardan las descripciones y credito
        $('#_txt_galeria_description_total').val(strdesc);
        $('#_txt_galeria_credito_total').val(strcred);

        if (GaleriaProntus.flag != 'si') {
            $('#_content-galeria-prontus').empty();
            GaleriaProntus.init(GaleriaProntus.flag);
        }
    },

    // --------------------------------------------------------------------
    aplicarCambiosDialogo: function() {

        var iditem = $('#_galeria_id_item_editing').val();
        var desc = GaleriaProntus.limpiadorCaracteres($('#_galeria_desc_temporal').val());
        var credito = GaleriaProntus.limpiadorCaracteres($('#_galeria_credito_temporal').val());

        //Validar que no exista el separador de texto
        if(desc.indexOf(GaleriaProntus.separadorTexto) >= 0) {
            GaleriaProntus.showMsg('La secuencia: '+GaleriaProntus.separadorTexto+' no se puede utilizar en la descripción.');
            return;
        }
        if(credito.indexOf(GaleriaProntus.separadorTexto) >= 0) {
            GaleriaProntus.showMsg('La secuencia: '+GaleriaProntus.separadorTexto+' no se puede utilizar en el crédito.');
            return;
        }

        $(iditem+' .field-descripcion').val(desc);
        $(iditem+' .field-credito').val(credito);

        GaleriaProntus.borrarDatosDialogo();
    },

    // --------------------------------------------------------------------
    borrarDatosDialogo: function() {
        $("#_dialog-form" ).dialog( "close" );
        $('#_galeria_id_item_editing').val('');
        $('#_galeria_desc_temporal').val('');
        $('#_galeria_credito_temporal').val('');
    },
    // --------------------------------------------------------------------
    limpiadorCaracteres: function(text) {
        var texto = text;
        texto = texto.replace(/(['"])/g, "\\$1");
        texto =  texto.replace(/\\\'/g,"&#39;");
        texto =  texto.replace(/\\\"/g,"&quot;");
        return texto;
    },

    // --------------------------------------------------------------------
    iniciarDialogo: function() {
        $("#_dialog-form").dialog({
            autoOpen: false,
            position:[148, 'center'],
            height: 280,
            width: 400,
            modal: true,
            buttons: {
                "Aplicar Cambios": function() {
                    GaleriaProntus.aplicarCambiosDialogo();
                },
                "Cancelar": function() {
                    GaleriaProntus.borrarDatosDialogo();
                }
            },
            close: function() {
                GaleriaProntus.borrarDatosDialogo();
            }
        });
    },

    // --------------------------------------------------------------------
    accionEdit: function(iditem, event) {
        var desc = GaleriaProntus.htmlDecode($(iditem+' .field-descripcion').val());
        var credito = GaleriaProntus.htmlDecode($(iditem+' .field-credito').val());

        $('#_galeria_desc_temporal').val(desc);
        $('#_galeria_credito_temporal').val(credito);
        $('#_galeria_id_item_editing').val(iditem);

        $("#_dialog-form").dialog('open');
    },

    // --------------------------------------------------------------------
    htmlDecode: function(input){
      var e = document.createElement('div');
      e.innerHTML = input;
      return e.childNodes.length === 0 ? "" : e.childNodes[0].nodeValue;
    },

    // --------------------------------------------------------------------
    accionShow: function(iditem) {
        var urlFoto = $(iditem).find('.show').attr('href');
        $.fn.colorbox({
                transition: 'elastic',
                scrolling: true,
                open: true,
                href: urlFoto,
                maxWidth: '100%',
                maxHeight: '100%',
                scalePhotos: true,
                opacity: 0.8
        });
    },

    // --------------------------------------------------------------------
    accionDelete: function(iditem) {
        if(confirm('¿Está seguro que desea eliminar esta imagen de la galería?')) {
            $(iditem).fadeOut(function() {
                $(this).remove();
            });
        }
    },

    // --------------------------------------------------------------------
    showMsg: function(msg) {
        alert(msg);
    },
    // funciones para el procesamiento del zip
    // ---------------------------------------------------------------------------------------------
    verificarZip: function() {
        // Para ver status del Zip con fotos
        var zipfile = $('[name="_HIDD__gal_archive"]').val();
        if (typeof zipfile !== 'undefined' && zipfile !== '' && /\.zip$/.test(zipfile)) {
            GaleriaProntus.pproc_working = true;
            $("#_prontus-galeria-dialog").html(GaleriaProntus.msg_process + GaleriaProntus.img_process);
            $("#_prontus-galeria-dialog").dialog({
                    closeOnEscape: false,
                    draggable: false,
                    modal: true,
                    position: [300,250],
                    resizable: false
            });
            GaleriaProntus.actualizaEstado(mainFidJs.TS, Admin.prontus_id);
            return;
        }
        if (typeof zipfile !== 'undefined' && zipfile !== '' && !/\.zip$/.test(zipfile)) {
            $("#_prontus-galeria-dialog").html(GaleriaProntus.msg_error_zip);
            $("#_prontus-galeria-dialog").dialog({
                    closeOnEscape: false,
                    draggable: false,
                    modal: true,
                    position: [300,250],
                    buttons: [{
                            text: 'Cerrar',
                            click: function() {
                                    $(this).dialog("close");
                                }
                            }],
                    resizable: false
            });
            return;
        }
    },
    // ---------------------------------------------------------------------------------------------
    actualizaEstado: function (ts, prontus_id) {
        // Se deja el dialogo modal
        // Ahora se revisa el json
        var url = '/'+Admin.prontus_id+'/cpan/procs/galeria_prontus/'+ts+'.json';
        $.ajax({
            url: url,
            dataType: 'json',
            cache: false,
            success: function(data) {
                if (typeof data.procesando !== 'undefined' && data.procesando == '0') {
                    GaleriaProntus.borrarEstado(ts, prontus_id, data.msg);
                } else {
                    setTimeout(function() {
                        GaleriaProntus.actualizaEstado(ts, prontus_id);
                    }, 5000);
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                // No se pudo leer el json
                if (GaleriaProntus.errorCounter >= 4) {
                    GaleriaProntus.terminarProcesamiento(GaleriaProntus.msg_error_resp, true);
                    return;
                } else {
                    GaleriaProntus.errorCounter++;
                    setTimeout(function() {
                        GaleriaProntus.actualizaEstado(ts, prontus_id);
                    }, 5000);
                }
            },
        });
    },

    // ---------------------------------------------------------------------------------------------
    borrarEstado: function(ts, prontus_id, msg) {
        $.ajax({
            data: {
                ts: ts,
                prontus_id:prontus_id
            },
            url: GaleriaProntus.cgi_borrar,
            dataType: 'json',
            cache: false,
            success: function(data, textStatus, jqXHR) {
                if (msg == "El archivo debe ser un ZIP") {
                    GaleriaProntus.terminarProcesamiento(GaleriaProntus.msg_error_zip, true);
                } else {
                    GaleriaProntus.terminarProcesamiento(msg);
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                // No se pudo obtener respuesta
                GaleriaProntus.terminarProcesamiento(GaleriaProntus.msg_error_com);
            }
        });
    },

    // ---------------------------------------------------------------------------------------------
    terminarProcesamiento: function(msg, noreload) {
        if (typeof noreload === 'undefined') {
            noreload = false;
        }
        GaleriaProntus.pproc_working = false;
        var labelBoton = 'Cerrar';
        if (!noreload) {
            labelBoton = 'Recargar';
            setTimeout(function() {
                window.location.reload();
            }, 500);
        }
        $('#_prontus-galeria-dialog').html(msg);
        $('#_prontus-galeria-dialog').dialog("option", "buttons", [{
            text: labelBoton,
            click: function() {
                if (!noreload) {
                    window.location.reload();
                } else {
                    $(this).dialog("close");
                }
            }
        }]);
    },
    // ---------------------------------------------------------------------------------------------
    verificaArchivoCargado: function() {
        var archivo = $('#_gal_archive').val();
        if (typeof archivo !== 'undefined' && archivo !== '' && !/\.zip$/.test(archivo)) {
            $('#_gal_archive').val('');
            $('#_gal_archive').parent().siblings(':input').val('')
            $("#_prontus-galeria-dialog").html(GaleriaProntus.msg_error_zip);
            $("#_prontus-galeria-dialog").dialog({
                    closeOnEscape: false,
                    draggable: false,
                    modal: true,
                    position: [300,250],
                    buttons: [{
                            text: 'Cerrar',
                            click: function() {
                                    $(this).dialog("close");
                                }
                            }],
                    resizable: false
            });
            return false;
        }
        return true;
    }

}
