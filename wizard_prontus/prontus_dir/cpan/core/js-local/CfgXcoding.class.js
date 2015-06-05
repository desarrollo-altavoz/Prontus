/**
CfgXcoding.class.js

Descripcion:
    Maneja la creacion de configuraciones de transcodificacion

Dependencias:
    Ninguna

Versión:
    1.0.0 - 27/04/2015 - EAG - Primera versión.
**/

var CfgXcoding = {
    formatos: {},
    marca_defecto: 'MULTIMEDIA_VIDEO1',
    prefijo_marca: 'MULTIMEDIA_VIDEO',

    dirCgi: '/cgi-cpn/xcoding/',
    cgiCargaFormatos: 'prontus_xcoding_getformatos.cgi',
    cgiGuardaFormatos: 'prontus_xcoding_guardarformatos.cgi',
    cgiVerificaFFmpeg: 'prontus_check_ffmpeg.cgi',


    init: function () {
        CfgXcoding.cargaCfg();
        $('.xcoding_param').keyup(CfgXcoding.actualizaFormatos);
        $('.xcoding_param').on("click", function () {
            CfgXcoding.actualizaFormatos();
        });
        CfgXcoding.soloNumeros('.xc_numero');
        CfgXcoding.soloLetras('.xc_letra');
    },

    /**
     * Carga las configuraciones de transcodificaciones
     * @param
     */
    cargaCfg: function () {
        $.ajax({
            async: false,
            url: CfgXcoding.dirCgi + CfgXcoding.cgiCargaFormatos,
            data: {
                prontus_id: Admin.prontus_id
            },
            type: 'POST',
            dataType: 'json',
            success: function (json) {
                if (typeof json.status !== 'undefined') {
                    if (json.status === 1) {
                        CfgXcoding.formatos = json.data;
                        var marca = '';
                        var marcas = [];
                        marcas[0] = CfgXcoding.marca_defecto;
                        var nombre;
                        var last_marca = '';
                        for (marca in CfgXcoding.formatos) {
                            nombre = marca.split('.');
                            if (marcas.indexOf(nombre[0]) < 0) {
                                marcas.push(nombre[0]);
                            }
                        }
                        marcas.sort();
                        var largo = marcas.length;
                        var combo_marca = document.getElementById('MARCA_PRONTUS');
                        combo_marca.options.length = 0;
                        for (var j = 0; j < largo; j++) {
                            combo_marca.options[j] = new Option(marcas[j], marcas[j]);
                        }
                        CfgXcoding.cargaFormatos();

                    } else {
                        alert(json.msg);
                    }
                }
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                alert('Ha ocurrido un error al cargar los formatos: ' + errorThrown);
            }
        });
    },

    /**
     * Carga la combo de formatos con los valores de formatos adicionales
     */

    cargaFormatos: function () {
        var marca_seleccionada = document.getElementById('MARCA_PRONTUS').value;
        var marca = '';
        var marcas = [];
        var nombre;
        var combo_formatos = document.getElementById('FORMAT');
        var i = 0;
        for (marca in CfgXcoding.formatos) {
            nombre = marca.split('.');
            if (marca_seleccionada == nombre[0] && nombre.length > 1) {
                marcas[i] = marca;
                i++;
            }
        }
        marcas.sort();

        combo_formatos.options.length = 0;
        combo_formatos.options[0] = new Option('Por defecto', '');
        combo_formatos.options[0].selected = true;
        for (var j = 0; j < i; j++) {
            nombre = marcas[j].split('.');
            combo_formatos.options[j+1] = new Option(nombre[1], nombre[1]);
        }
        CfgXcoding.cargaParametros();
    },

    /**
     * Carga los parametros del formato seleccionado
     */

    cargaParametros: function() {
        CfgXcoding.limpiaParametros();
        var marca_seleccionada = document.getElementById('MARCA_PRONTUS').value;
        var formato_seleccionado = document.getElementById('FORMAT').value;
        var formato = '';
        if (formato_seleccionado == '') {
            formato = marca_seleccionada;
        } else {
            formato = marca_seleccionada + '.' +formato_seleccionado;
        }
        if (typeof CfgXcoding.formatos[formato] !== 'undefined') {
            var campo;
            for (campo in CfgXcoding.formatos[formato]) {
                document.getElementById(campo).value = CfgXcoding.formatos[formato][campo];
            }
        }
        return true;
    },

    actualizaFormatos: function() {
        var marca_seleccionada = document.getElementById('MARCA_PRONTUS').value;
        var formato_seleccionado = document.getElementById('FORMAT').value;
        var formato = '';
        if (formato_seleccionado == '') {
            formato = marca_seleccionada;
        } else {
            formato = marca_seleccionada + '.' +formato_seleccionado;
        }
        if (typeof CfgXcoding.formatos[formato] === 'undefined' ) {
            CfgXcoding.formatos[formato] = {};
        }
        CfgXcoding.formatos[formato].VIDEOBITRATE  = document.getElementById('VIDEOBITRATE').value;
        CfgXcoding.formatos[formato].H264PROFILE   = document.getElementById('H264PROFILE').value;
        CfgXcoding.formatos[formato].VIDEOSIZE     = document.getElementById('VIDEOSIZE').value;
        CfgXcoding.formatos[formato].X264          = document.getElementById('X264').value;
        CfgXcoding.formatos[formato].AUDIOBITRATE  = document.getElementById('AUDIOBITRATE').value;
        CfgXcoding.formatos[formato].AUDIOCHANNELS = document.getElementById('AUDIOCHANNELS').value;
        CfgXcoding.formatos[formato].AUDIOSAMPLING = document.getElementById('AUDIOSAMPLING').value;
    },

    /**
     * limpia los campos antes de cargar datos nuevos
     */
    limpiaParametros: function() {
        document.getElementById('VIDEOBITRATE').value = '';
        document.getElementById('H264PROFILE').value = '';
        document.getElementById('VIDEOSIZE').value = '';
        document.getElementById('X264').value = '';
        document.getElementById('AUDIOBITRATE').value = '';
        document.getElementById('AUDIOCHANNELS').value = '';
        document.getElementById('AUDIOSAMPLING').value = '';
    },

    /**
     * agrega un nuevo formato a la lista
     */
    agregarFormato: function() {
        var nuevo_formato = document.getElementById('nuevo_formato_xcoding').value;
        if (/\S+/.test(nuevo_formato)) {
            nuevo_formato = nuevo_formato.toUpperCase();
            if (/^[a-zA-Z]+$/.test(nuevo_formato)) {
                var combo_formato = document.getElementById('FORMAT');
                var combo_marca = document.getElementById('MARCA_PRONTUS');
                if (typeof CfgXcoding.formatos[combo_marca.value + '.' + nuevo_formato] !== 'undefined') {
                    alert('Este formato ya existe ');
                    return false;
                }

                CfgXcoding.actualizaFormatos();
                combo_formato.options[combo_formato.options.length] = new Option(nuevo_formato, nuevo_formato);
                combo_formato.options[combo_formato.options.length-1].selected = true;
                document.getElementById('nuevo_formato_xcoding').value = '';
                CfgXcoding.limpiaParametros();
            } else {
                alert('Sólo se pueden ingresar letras. No se permite Ñ, espacios, números, letras con tilde o símbolos');
            }
        } else {
            alert('Debe ingresar un identificador para el formato');
        }
    },

    /**
     * agrega una nueva marca prontus a la lista
     */
    agregarMarca: function() {
        var nuevo_id = document.getElementById('nueva_marca_xcoding').value;
        if (/\d+/.test(nuevo_id)) {
            if (/^[0-9]+$/.test(nuevo_id)) {
                var combo_marca = document.getElementById('MARCA_PRONTUS');
                var nueva_marca = CfgXcoding.prefijo_marca +  nuevo_id;
                var nombre;
                for (var marca in CfgXcoding.formatos) {
                    nombre = marca.split('.');
                    if (nueva_marca == nombre[0] && nombre.length > 1) {
                        alert('Esta marca ya existe');
                        return false;
                    }
                }
                CfgXcoding.actualizaFormatos();
                combo_marca.options[combo_marca.options.length] = new Option(nueva_marca, nueva_marca);
                combo_marca.options[combo_marca.options.length-1].selected = true;
                CfgXcoding.cargaFormatos();
                document.getElementById('nueva_marca_xcoding').value = '';
                CfgXcoding.limpiaParametros();
            } else {
                alert('Sólo se pueden ingresar números.');
            }
        } else {
            alert('Debe ingresar un id');
        }
    },

    /**
     * Ejecuta una verificacion de la configuracion del directorio y de ffmpeg si lo encuentra
     */
    borrarMarca: function() {
        var msg = "¿Estás seguro de eliminar la marca de transcodificación?\nSe eliminarán todos los formatos asociados. Esta acción no se puede deshacer.";
        if (confirm(msg)) {
            var marca_seleccionada = document.getElementById('MARCA_PRONTUS').value;
            var nombre;
            for (marca in CfgXcoding.formatos) {
                nombre = marca.split('.');
                if (marca_seleccionada == nombre[0]) {
                    delete CfgXcoding.formatos[marca];
                }
            }
            CfgXcoding.guardarServidor();
        }
    },

    /**
     * Ejecuta una verificacion de la configuracion del directorio y de ffmpeg si lo encuentra
     */
    borrarFormato: function() {
        var formato_seleccionado = document.getElementById('FORMAT').value;
        var marca_seleccionada = document.getElementById('MARCA_PRONTUS').value;
        var msg = "¿Estás seguro de eliminar el formato de transcodificación?. Esta acción no se puede deshacer.";
        if (formato_seleccionado == '') {
            alert('Este formato no se puede eliminar');
            return false;
        }
        if (confirm(msg)) {
            if (typeof CfgXcoding.formatos[marca_seleccionada+ '.' +formato_seleccionado] !== 'undefined') {
                delete CfgXcoding.formatos[marca_seleccionada+ '.' +formato_seleccionado];
                CfgXcoding.guardarServidor();
            }
        }
        return false;
    },

    /**
     * confirma el guardado y llama el almacenamiento definitivo
     */
    guardar: function() {
        for (var marca in CfgXcoding.formatos) {
            if (typeof CfgXcoding.formatos[marca]['VIDEOSIZE'] !== undefined) {
                if (CfgXcoding.formatos[marca]['VIDEOSIZE'] % 2 == 1) {
                    var nombre = marca.split('.');
                    alert('El parametro VIDEOSIZE no puede ser impar, formato incorrecto:\n' + marca);
                    return false;
                }
            }
        }
        var msg = "¿Estás seguro de modificar los formatos de transcodificación?";
        if (confirm(msg)) {
            CfgXcoding.guardarServidor();
        }
    },

    /**
     * guarda la configuracion editada en el servidor
     */
    guardarServidor: function() {
        $.ajax({
            url: CfgXcoding.dirCgi + CfgXcoding.cgiGuardaFormatos,
            data: {
                prontus_id: Admin.prontus_id,
                formatos: JSON.stringify(CfgXcoding.formatos)
            },
            type: 'POST',
            dataType: 'json',
            async: false,
            success: function (json) {
                if (typeof json.status !== 'undefined') {
                    if (json.status === 1) {
                        alert('Se han guardado correctamente los formatos');
                    } else {
                        alert(json.msg);
                    }
                }
                CfgXcoding.cargaCfg();
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                alert('Ha ocurrido un error al guardar los formatos: ' + errorThrown);
            }
        });
    },

    soloNumeros: function(selector) {
     // Por teclado solo se puede ingresar números
        $(selector).keydown(function(event) {
            //~ if (event.shiftKey) event.preventDefault(); //desactivar shift
            if (event.keyCode == 46 || event.keyCode == 8 || event.keyCode == 9 || event.keyCode == 37 || event.keyCode == 39){
                //se permiten estas teclas
            }else{
                if (event.keyCode < 95) {
                    if (event.keyCode < 48 || event.keyCode > 57 ) event.preventDefault();
                }
                else {
                    if (event.keyCode < 96 || event.keyCode > 105) event.preventDefault();
                }
            }
        });
    },

    soloLetras: function(selector) {
     // Por teclado solo se puede ingresar números
        $(selector).keydown(function(event) {
            //~ if (event.shiftKey) event.preventDefault(); //desactivar shift
            if (event.keyCode == 46 || event.keyCode == 8 || event.keyCode == 9 || event.keyCode == 37 || event.keyCode == 39){
                //se permiten estas teclas
            }else{
                if (event.keyCode < 65 || event.keyCode > 90) event.preventDefault();

            }
        });
    },

    /**
     * Ejecuta una verificacion de la configuracion del directorio y de ffmpeg si lo encuentra
     */
    testFFmpeg: function() {
        var path = $('#DIR_FFMPEG').val();
        if (path != '') {
            var obj = Opciones.optsDefault;
            obj.width = '900px';
            obj.height = '500px';
            obj.href = CfgXcoding.dirCgi + CfgXcoding.cgiVerificaFFmpeg;
            obj.href += '?prontus_id=' + Admin.prontus_id;
            obj.href += '&path=' + path;
            $('#DIR_FFMPEG').val();
            obj.onLoad = function() {
                Admin.mostrarBarraColorbox();
            };
            $.fn.colorbox(obj);
        }
    },

    /**
     * Muestra/oculta las advertencias
     */
    showAlert: function(object) {
        if (object.value == 'SI') {
            $('#'+object.name+'_alert').show();
        } else {
            $('#'+object.name+'_alert').hide();
        }
    }
};
