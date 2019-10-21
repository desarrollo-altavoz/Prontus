// -----------------------------------------------------------------------------
// Objeto que sirve par la mostrar los codigos para embeber video y audio
var Embed = {
    showAudio: true,
    showVideo: true,
    // -------------------------------------------------------------------------
    //muestra/oculta el codigo para embeber el video
    showCodeV: function() {
        if (Embed.showVideo && $('#linkVideo').children().length > 0) {
            Embed.embedVideo();
            Embed.showVideo = false;
        } else  {
            $('#embed-code').children().remove();
            Embed.showVideo = true;
        }

    },
    // -------------------------------------------------------------------------
    //genera el codigo para embeber el video
    embedVideo: function() {
        var videoUrl =$('#linkVideo').children().attr('href');
        var width = 440;
        var heigth = 350;
        var code = '';
        var pathPlayer = $('#_xcode_player_path').val();
        if(typeof pathPlayer === 'undefined' || pathPlayer === null || pathPlayer === '') {
            var patt = new RegExp('/(.+?)/site/.+');
            var result = patt.exec(videoUrl);
            pathPlayer = '/'+result[1]+'/flash/players/playerVideo.swf';
        }
        code += '<textarea rows="10" cols="80" style="font-size:12px;" class="embedable-code fieldform">';
        code += '<object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=10,0,0,0" width="'+width+'" height="'+heigth+'" id="videoembed">';
        code += '<param name="movie" value="'+pathPlayer+'">';
        code += '<param name="quality" value="high">';
        code += '<param name="wmode" value="opaque">';
        code += '<param name="AllowFullScreen" value="true">';
        code += '<param name="allowScriptAccess" value="sameDomain">';
        code += '<param name="flashvars" value="VURL=' + videoUrl + '">';
        code += '<embed src="'+pathPlayer+'" width="'+width+'" height="'+heigth+'" name="videoembed" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer" quality="high" wmode="opaque" allowfullscreen="true" allowscriptaccess="sameDomain" flashvars="VURL='+videoUrl+'">';
        code += '</object>';
        code += '</textarea>';
        $('#embed-code').append(code);
        $('.embedable-code').select();
    },
    // -------------------------------------------------------------------------
    //muestra/oculta el codigo para embeber el video
    showCodeA: function() {
        if (Embed.showAudio && $('.file-link').children().length > 0) {
            Embed.embedAudio();
            Embed.showAudio = false;
        } else  {
            $('#embed-code').children().remove();
            Embed.showAudio = true;
        }

    },
    // -------------------------------------------------------------------------
    //genera el codigo para embeber el audio
    embedAudio: function() {
        var audioUrl = $('.file-link').children().attr('href');
        var width = 350;
        var heigth = 20;
        var code = '';
        var patt = new RegExp('/(.+?)/site/.+');
        var result = patt.exec(audioUrl);
        code += '<textarea rows="13" cols="50" class="fieldform embedable-code">';
        code += '<object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=10,0,0,0" width="'+width+'" height="'+heigth+'" id="audioembed">';
        code += '<param name="movie" value="/'+result[1]+'/flash/players/playerAudio.swf">';
        code += '<param name="quality" value="high">';
        code += '<param name="wmode" value="opaque">';
        code += '<param name="AllowFullScreen" value="true">';
        code += '<param name="allowScriptAccess" value="sameDomain">';
        code += '<param name="flashvars" value="VURL=' + audioUrl + '">';
        code += '<embed src="/'+result[1]+'/flash/players/playerAudio.swf" width="'+width+'" height="'+heigth+'" name="audioembed" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer" quality="high" wmode="opaque" allowfullscreen="true" allowscriptaccess="sameDomain" flashvars="VURL='+audioUrl+'">';
        code += '</object>';
        code += '</textarea>';
        $('#embed-code').append(code);
        $('.embedable-code').select();
    }
};
