/**
Flash.class.js

Descripcion:
Contiene funciones para insertar objetos flash y players de audio y video flash.
Si el user agent del navegador corresponde a uno movil, insertará tags html5.
En este caso los videos deben ser de formato mp4, ya que es compatible con
flash y dispositivos portatiles.
Los archivos de audio deben ser mp3 por lo mismo.

Dependencias:
Ninguna

Versión:
2.0.0 - 21/12/2011
Más información en Flash.txt

**/
var Flash = {

    // Zona de Configuraciones prontus_id
    prontus_dir: '/modelo_productos',
    swfVideo: '/flash/players/playerVideo.swf',    // Ruta del player de video
    swfAudio: '/flash/players/playerAudio.swf',    // Ruta del player de audio
    swfImgFade: '/flash/image_fade/prontus_imgfade_8.2.swf', // Ruta del swf de imageFade
    objDefault: {
        quality: 'high',
        wmode: 'transparent',
        AllowFullScreen: 'true',
        allowScriptAccess: 'sameDomain'
    },

    // -----------------------------------------------------
    isMobile: function() {
        var agent = (navigator.userAgent||navigator.vendor||window.opera);
        if(/android.+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od|ad)|iris|kindle|lge |maemo|midp|mmp|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|symbian|treo|up\.(browser|link)|vodafone|wap|windows (ce|phone)|xda|xiino/i.test(agent)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|e\-|e\/|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(di|rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|xda(\-|2|g)|yas\-|your|zeto|zte\-/i.test(agent.substr(0,4))) {
            if((/ip(hone|ad|od)/i.test(agent) && /Mac OS X/i.test(agent)) || (/android/i.test(agent) && /opera/i.test(agent))) {
                return true;
            } else {
                return false;
            };
        } else{
            return false;
        };
    },

    // -----------------------------------------------------
    insertaImageFade: function(file, objid, wflash, hflash, target, img1, img2, img3, img4) {
        if(typeof img1 == 'undefined') {
            img1 = '';
        }
        if(typeof img2 == 'undefined') {
            img2 = '';
        }
        if(typeof img3 == 'undefined') {
            img3 = '';
        }
        if(typeof img4 == 'undefined') {
            img4 = '';
        }
        if(typeof target == 'undefined') {
            target = '';
        }
        var flashvars = {
            linkurl: file,
            urlartic: file,
            target: target,
            foto1: img1,
            foto2: img2,
            foto3: img3,
            foto4: img4 };
        var obj = {flashvars: flashvars};
        Flash.insertaFlash(Flash.prontus_dir +Flash.swfImgFade, objid, wflash, hflash, obj);
    },

    // -----------------------------------------------------
    insertaPlayerVideo: function(vurl, objid, wflash, hflash, img, ts, secc, tema, stem, titu, aid) {
        if(typeof img == 'undefined') {
            img = '';
        }
        var flashvars = {
            VURL: vurl,
            VIMG: img,
            TS: ts,
            SECC: secc,
            TEMA: tema,
            STEM: stem,
            TITU: titu,
            AID: aid };
        var obj = {flashvars: flashvars, id: objid +'playervideo'};
        if(Flash.isMobile()) {
            var strHTML5 = '<video src="'+vurl+'" ' +
                'poster="'+img+'" ' +
                'width="'+wflash+'" ' +
                'height="'+hflash+'" ' +
                'controls="controls">' +
                'Tu navegador no soporta HTML5</video>';
            Flash.insertaHtml(strHTML5, objid, wflash);
        } else {
            Flash.insertaFlash(Flash.prontus_dir + Flash.swfVideo, objid, wflash, hflash, obj);
        }
    },
    // -----------------------------------------------------
    insertaPlayerAudio: function(vurl, objid, wflash, hflash, ts, secc, tema, stem, titu, aid) {
        var flashvars = {
            VURL: vurl,
            TS: ts,
            SECC: secc,
            TEMA: tema,
            STEM: stem,
            TITU: titu,
            AID: aid };
        var obj = {flashvars: flashvars, id: objid +'playeraudio'};
        if(Flash.isMobile()) {
            var strHTML5 = '<audio src="'+vurl+'" ' +
                'controls="controls">' +
                'Tu navegador no soporta HTML5</audio>';
            Flash.insertaHtml(strHTML5, objid, wflash);
        } else {
            Flash.insertaFlash(Flash.prontus_dir + Flash.swfAudio, objid, wflash, hflash, obj);
        }
    },
    // -----------------------------------------------------
    setWidth: function(wflash, objid) {
        var miDiv = document.getElementById(objid);
        if(typeof miDiv !== 'undefined') {
            miDiv.style.width = wflash+"px";
        }
    },
    // -----------------------------------------------------
    insertaHtml: function(str, objid, wflash) {
        // Se intenta con jquery
        if(Flash.hasJQuery()) {
            $('#'+objid).html(str);
        // Si no funciona jquery se hace a la antigua
        } else {
            var midiv = document.getElementById(objid);
            if(typeof midiv !== 'undefined') {
                midiv.innerHTML = str;
            }
        }
        Flash.setWidth(wflash, objid);
    },
    // -----------------------------------------------------
    insertaFlash: function(movieUrl, objid, wflash, hflash, obj) {
        obj = Flash.merge(Flash.objDefault, obj);
        // Validacion de los parametros de entrada
        if (typeof movieUrl === 'undefined' || movieUrl == '' ||
            typeof objid === 'undefined' || objid == '' ||
            typeof wflash === 'undefined' || wflash == '' ||
            typeof hflash === 'undefined' || hflash == '') {
            return;
        }

        // Si tiene el plugin de media, utiliza ese mismo para insertar
        if(Flash.hasMedia()) {

            // Se revisa si tiene flashvars
            var flashvars;
            if ((typeof obj !== 'undefined') && (typeof obj.flashvars !== 'undefined')) {
                flashvars = obj.flashvars;
                delete obj.flashvars;
            }

            // Y finalmente se inserta en el
            $('#'+objid).media({
                width:      wflash,
                height:     hflash,
                src:        movieUrl,
                params:     obj,
                attrs:      obj,
                flashvars:  flashvars
            });

        // Se utiliza el método carretero
        } else {

            var strFlash = Flash.getStrFlash(movieUrl, objid, wflash, hflash, obj);

            Flash.insertaHtml(strFlash, objid, wflash);
        }
    },

    // -----------------------------------------------------
    getStrFlash: function(movieUrl, objid, wflash, hflash, obj) {
        var str = '';

        // Se revisa si tiene flashvars
        if(typeof obj !== 'undefined' && typeof obj.flashvars !== 'undefined') {
            obj.flashvars = Flash.generaFlashVars(obj.flashvars);
            //delete obj.flashvars;
        }

        // Se comienza con la creacion del string
        str = str + '<object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000"';
        str = str + '  codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=10,0,0,0"';
        str = str + '  width="' + wflash + '"';
        str = str + '  height="' + hflash + '"';
        str = str + '  id="flash' + objid + '">';
        str = str + '  <param name="movie" value="' + movieUrl + '" />';
        for(var nomb1 in obj) {
            if(typeof obj[nomb1] !== 'undefined') {
                str = str +  '<param name="' + nomb1 + '" value="' + obj[nomb1] + '" />';
            }
        }
        str = str + '  <embed';
        str = str + '    src="' + movieUrl + '"';
        str = str + '    width="' + wflash + '"';
        str = str + '    height="' + hflash + '"';
        str = str + '    name="flash' + objid + '"';
        str = str + '    type="application/x-shockwave-flash"';
        str = str + '    pluginspage="http://www.macromedia.com/go/getflashplayer"';
        for(var nomb2 in obj) {
            if(typeof obj[nomb2] !== 'undefined') {
                str = str + '  ' + nomb2 + '="' + obj[nomb2] + '"';
            }
        }
        str = str + '    />';
        str = str + '</object>';
        return str;
    },

    // -----------------------------------------------------
    generaFlashVars: function(obj) {
        var str = '';
        for(var variable in obj) {
            if(typeof obj[variable] !== 'undefined') {
                str = str + variable + '=' + obj[variable] + '&';
            }
        }
        if(str != '') {
          str = str.substr(0, str.length - 1);
        }
        return str;
    },

    // -----------------------------------------------------
    merge: function(obj1, obj2) {
        if(typeof obj1 == 'undefined') {
            return obj2;
        } else if(typeof obj2 == 'undefined') {
            return obj1;
        }
        for(var attrname in obj2) {
            if(typeof obj2[attrname] !== 'undefined') {
                obj1[attrname] = obj2[attrname];
            }
        }
        return obj1;
    },

    // -----------------------------------------------------
    hasMedia: function() {
        if(!Flash.hasJQuery()) {
            return false;
        }
        if(jQuery().media) {
            return true;
        } else {
            return false;
        }
    },

    // -----------------------------------------------------
    hasJQuery: function() {
        if (typeof jQuery == 'undefined') {
            return false;
        } else {
            return true;
        }
    }
};
