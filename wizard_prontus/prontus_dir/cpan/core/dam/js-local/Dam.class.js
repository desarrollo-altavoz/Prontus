
var Dam = {

    idTimer: null,
    tooltipTime: 800,

    tipoAsset: null,
    textoBuscador: '',

    anchoPlayer: 440,
    altoPlayer: 350,

    idDivVideo: '#video_asset',
    playerVideo: '/cpan/core/flash/player_video/playerVideo.swf',

    // -------------------------------------------------------------------------
    init: function() {
        // Instala el colorbox
        $('.colorbox').colorbox({
          maxWidth: '95%',
          maxHeight: '90%'
        });

        Dam.instalaColorboxFotos();
        Dam.instalaHoverFotoList();

        // Instala el plugin de Media
        //~ $.fn.media.defaults.flvPlayer = '/'+Admin.prontus_id+'/cpan/core/js-local/jquery/plugins/media/mediaplayer.swf';
        //$.fn.media.defaults.mp3Player = '/'+Admin.prontus_id+'/cpan/core/js-local/jquery/plugins/media/mediaplayer.swf';
        //~ $('.media').media({
          //~ width:220,
          //~ height:150
        //~ });
        $('.media-audio').each(function() {
            $(this).media({
                src: '/'+Admin.prontus_id+'/cpan/core/js-local/jquery/plugins/media/mediaplayer.swf',
                width: 280,
                height: 24,
                params: {
                    allowScriptAccess: 'always',
                    allowFullScreen: 'true',
                    wmode: 'opaque'
                    //quality: 'high'
                },
                flashvars: {
                    //audio: $(this).attr('href')
                    file: $(this).attr('href')
                }
            });
        });

        // Precarga la combo en imagenes, si no viene nada
        if($('#asset_search_type').val() === '') {
            $('#asset_search_type').val('foto');
        }

        // Para el link que copia la URL del medio en caso que sea iPad
        if(!jQuery.browser.flash) {
            $('.copiar').each(function() {
                $(this).next().show().addClass('copiar-url').html('&nbsp;').mouseover(function() {
                    $(this).addClass('hover');
                }).mouseout(function() {
                    $(this).removeClass('hover');
                })
                $(this).remove();
            });
        } else {
            Dam.instalaZeroClipboard();
        }
        // Para centrar verticalmente:
        $('.dam .item-multimedia .foto-preview').each(function() {
            var altodiv = $(this).height();
            var altoimg = $(this).find('img').height();
            if(altoimg < altodiv) {
                var padding = Math.floor((altodiv - altoimg) / 2);
                $(this).find('a').css({'margin-top':padding, 'display':'block'});
            }
        });

        // Para el buscador de assets
        Dam.tipoAsset = $('#asset_search_type').val();
        Dam.textoBuscador = 'Buscar ' + Dam.tipoAsset;
        Utiles.instalaHandlerBuscador('#asset_search_wordkey', Dam.textoBuscador);

        // Para el cambiar Orden
        var orden = $('#asset_search_orden').val();
        var arr = orden.split('_');
        $('.orderby a[href="#'+arr[0]+'"]').addClass(arr[1]).addClass('selected');
        $('.orderby .cambia-orden').click(function() {
            var lnk = $(this).attr('href').replace('#', '');
            Dam.cambiaOrden(lnk,$(this).hasClass('asc'),$(this).hasClass('desc'));
        });
    },

    // -------------------------------------------------------------------------
    showTooltipCopiar: function(posx, posy) {
//        Admin.displayMessage('La URL ha sido copiada', 'info');
//        setTimeout(function() {
//            Admin.closeMessage();
//        }, 2000);
        $('#tooltip-copiar').stop().hide().css({left:posx-20, top:posy-50}).fadeIn(400, function() {
            $(this).css('opacity', '1');
            clearTimeout(Dam.idTimer);
            Dam.idTimer = setTimeout(function() {
                $('#tooltip-copiar').fadeOut(500);
            }, Dam.tooltipTime);
        });
    },
    // -------------------------------------------------------------------------
    buscarAsset: function() {
        var search_texto = $('#asset_search_wordkey').val();
        if(search_texto !== '' && search_texto != Dam.textoBuscador) {
            $('#formDAM').submit();
        } else {
            alert("Debes ingresar la palabra clave.");
            return;
        }
    },
    // -------------------------------------------------------------------------
    cambiaOrden: function(lnk, asc, desc) {
        if(asc) {
            lnk = lnk + '_desc';
        } else if(desc) {
            lnk = lnk + '_asc';
        } else {
            if(lnk == 'text') {
                lnk = lnk + '_asc';
            } else {
                lnk = lnk + '_desc';
            }
        }
        $('#asset_search_orden').val(lnk);
        var search_texto = $('#asset_search_wordkey').val();
        if(search_texto == Dam.textoBuscador) {
            $('#asset_search_wordkey').val('');
        }
        $('#formDAM').submit();
    },
    // -------------------------------------------------------------------------
    limpiaFiltros: function() {
        $('#asset_search_wordkey').val('');
        $('#formDAM').submit();
    },
    // -------------------------------------------------------------------------
    showPlayer: function(linkVideo, prontus) {

        if(!jQuery.browser.flash) {
            $(Dam.idDivVideo).html('<video width="'+Dam.anchoPlayer+'" height="'+Dam.altoPlayer+'" controls="controls"></video>')
                .find('video').append('<source src="'+linkVideo+'" type="video/mp4" />');

        } else {
            $(Dam.idDivVideo).media({
                width: Dam.anchoPlayer,
                height: Dam.altoPlayer,
                src: '/' + prontus + Dam.playerVideo,
                params: {
                    allowScriptAccess: 'always',
                    allowFullScreen: 'true',
                    wmode: 'opaque'
                    //quality: 'high'
                },
                attrs: {
                    id: Dam.idDivVideo,
                    name: Dam.idDivVideo
                },
                flashvars: {
                    VURL: linkVideo
                }
            });
        }
    },

    instalaZeroClipboard: function() {
        ZeroClipboard.setMoviePath('/'+Admin.prontus_id+'/cpan/core/js-local/zeroclipboard/ZeroClipboard.swf');
        $('.copiar').each(function() {
            var clip = new ZeroClipboard.Client();
            clip.setHandCursor(true);

            var theId = $(this).attr('id');
            var theId2 = $(this).children().attr('id');
            var theUrl = $(this).next().attr('href');
            clip.addEventListener('mouseDown', function (client, text) {
                clip.setText(theUrl);
                Dam.showTooltipCopiar(client.domElement.offsetLeft, client.domElement.offsetTop);
                return true;
            });
            clip.glue(theId2, theId, {position:'relative', left:'0', top:'0'});
            this.clip = clip;
        });
    },

    instalaColorboxFotos: function() {
        $('.colorbox_asset').colorbox({
            maxWidth: '95%',
            maxHeight: '90%',
            onComplete: function () {
                Dam.instalaThumbNav();
            }
        });
    },

    instalaHoverFotoList: function() {
        $('.foto-list').hover( 
            function () {
                $(this).addClass('bg');
            },
            function () {
                $(this).removeClass('bg');
            }
        );
    },

    instalaThumbNav: function() {
        $('#asset_thumb_nav .scroll').slimScroll({
            height: '485px'
        });

        $('#asset_thumb_nav .thumb').click(function () {
            $('#asset_thumb_nav .thumb').find('div.active').remove();
            var src = $(this).css("background-image");
            src = src.replace('url(','').replace(')','');
            src = src.replace(/"/g, '');
            src = src.replace(/'/g, '');
            var w = $(this).attr("data-w");
            var h = $(this).attr("data-h");
            var w_orig = $(this).attr("data-w-orig");
            var h_orig = $(this).attr("data-h-orig");
            var num = $(this).index() + 1;

            $(this).append('<div class="active">#' + num + '</div>');

            $('#asset_viewer .item').html('<img src="' + src + '" width="' + w + '" height="' + h + '" />');
            $('#asset_viewer .toolbar #num').html("&raquo; Foto #" + num + ' (' + w_orig + 'x' + h_orig + ')');
            src = src.replace(/^(https?:\/\/.*?\/)/, '/'); // Dejar ruta relativa.

            ZeroClipboard.setMoviePath('/'+Admin.prontus_id+'/cpan/core/js-local/zeroclipboard/ZeroClipboard.swf');
            var clip = new ZeroClipboard.Client();
            clip.setHandCursor(true);

            clip.addEventListener('mouseDown', function (client, text) {
                clip.setText(src);
                $('.toolbar .dam-tooltip').fadeIn('fast', function () {
                    var obj = $(this);
                    setTimeout(function () {
                        $(obj).fadeOut('fast');
                    }, 500);
                });
                return true;
            });

            clip.glue("asset_list_int_cb", "asset_list_ext_cb", {position:'absolute', left:'0', top:'0', width: '18px', height: '18px'});
        });

        $('#asset_thumb_nav .thumb:eq(0)').click();
    }
};
