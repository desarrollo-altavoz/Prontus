var Player,Flash;
(function () {
    "use strict";
    var _self;
    Player = {
        //configuración
        config:{
            volume: 100
        },
        //variables del player
        vars:{
            currentVolume:0,
            videoTemplate: '',
            videoSrc:'',
            controlsHeight:0,
            currentPlayer:'html5',
            markA:0,
            markB:0
        },
        init: function (video) {
            _self = this;
            _self.selectPlayer();
            if(_self.vars.currentPlayer == 'html5'){
                _self.vars.videoSrc = video + '?t='+ (new Date().getTime());
                _self.vars.videoTemplate = $('#video_template').html();
                $(".panel-player").append(_self.vars.videoTemplate);
                _self.ui.initUI();
                _self.setEvents();
                _self.setSource();
            }else{
                Flash.iniciaFlash('#player-content');
            }

        },
        selectPlayer: function(){
            if(_self.helper.isIE()){
                if(_self.helper.iTShouldBeFlash()){
                    _self.vars.currentPlayer = 'flash';
                }else{
                    if(_self.helper.iTShouldBeHtml5()){
                        _self.vars.currentPlayer = 'html5';
                    }else{
                        _self.vars.currentPlayer = 'flash';
                    }
                }
            }else{
                if(_self.helper.iTShouldBeHtml5()){
                    _self.vars.currentPlayer = 'html5';
                }else{
                    _self.vars.currentPlayer = 'flash';
                }
            }
        },
        ui:{
            elements:{},
            setElements:function(){
                _self.ui.elements.video = $("#videoId")[0];
                _self.ui.elements.contentId = $("#contentId");
                _self.ui.elements.playerContent = $("#playerContent");
                _self.ui.elements.videoContent =  $(".panel-player");
                _self.ui.elements.playButton  = $("#playButton");
                _self.ui.elements.mainPlayButton  = $("#mainPlayButton");
                _self.ui.elements.pauseButton  = $("#pauseButton");
                _self.ui.elements.rewindButton  = $("#rewindButton");
                _self.ui.elements.loader  = $("#loader");
                _self.ui.elements.seekBar  = $("#seekBar");
                _self.ui.elements.playingBar = $("#playingBar");
                _self.ui.elements.timeContent = $("#timeContent");
                _self.ui.elements.volumeButton = $("#volumeButton");
                _self.ui.elements.volumeButtonMute = $("#volumeButtonMute");
                _self.ui.elements.volumeBar = $("#volumeBar");
                _self.ui.elements.volumeBarCont = $("#volumeBarCont");
                _self.ui.elements.fullScreen = $("#fullScreen");
                _self.ui.elements.progressBar = $(".progressbar");
                _self.ui.elements.buttonsAuxi = $(".buttons-auxi");
                _self.ui.elements.controls = $("#controlsContentId");
                _self.ui.elements.markIndicatorA = $("#markIndicatorA");
                _self.ui.elements.markLabelA = $("#markA");
                _self.ui.elements.markIndicatorB = $("#markIndicatorB");
                _self.ui.elements.markLabelB = $("#markB");
                _self.ui.elements.cutBar = $("#cutBar");
                _self.ui.elements.totalbar = $("#totalbar");
                _self.ui.elements.bar1 = $("#bar1");
                _self.ui.elements.bar2 = $("#bar2");
                _self.ui.elements.bar3 = $("#bar3");
            },
            initUI:function(){
                _self.ui.setElements();
                _self.actions.setVolume(_self.config.volume / 100);
                _self.vars.currentVolume = _self.ui.elements.video.volume;

                _self.vars.controlsHeight = _self.ui.elements.buttonsAuxi.height() + _self.ui.elements.progressBar.height() +10;

                _self.ui.elements.videoContent.height((_self.ui.elements.videoContent.width()*9/16)+_self.vars.controlsHeight);
                _self.ui.elements.playerContent.height(_self.ui.elements.contentId.height() -_self.vars.controlsHeight);
                _self.ui.elements.totalbar.width(_self.ui.elements.seekBar.width());
                _self.ui.elements.bar3.width(_self.ui.elements.seekBar.width());


            },
            setInitMarks:function(){
                var markIndicatorA = _self.ui.elements.markIndicatorA;
                var markLabelA = _self.ui.elements.markLabelA;
                var markIndicatorB = _self.ui.elements.markIndicatorB;
                var markLabelB = _self.ui.elements.markLabelB;
                var seekBar = _self.ui.elements.seekBar;
                var controls = _self.ui.elements.controls;
                markIndicatorA.css('left',(seekBar.offset().left - controls.offset().left) - 3 + 'px');
                markLabelA.css('left',(seekBar.offset().left - controls.offset().left) - (markLabelA.width()/2) + 'px');
                markIndicatorB.css('left',(seekBar.offset().left - controls.offset().left + seekBar.width()) - 3 + 'px');
                markLabelB.css('left',(seekBar.offset().left - controls.offset().left + seekBar.width()) - (markLabelB.width()/2) + 'px');
                _self.ui.elements.cutBar.width(seekBar.width());
                _self.ui.elements.bar1.width(0);
                _self.ui.elements.bar2.width(seekBar.width());
                _self.vars.markA = 0;
                _self.vars.markB = _self.ui.elements.video.duration;
            }
        },
        setEvents:function(){
            _self.ui.elements.video.addEventListener("ended", _self.callbacks.onEnded);
            _self.ui.elements.video.addEventListener("loadedmetadata", function(){
                _self.ui.setInitMarks();
            });
            _self.ui.elements.video.addEventListener("timeupdate", _self.callbacks.onTimeUpdate);
            _self.ui.elements.video.addEventListener("playing", _self.callbacks.onPlaying);
            _self.ui.elements.playButton.on("click",_self.callbacks.onPlay);
            _self.ui.elements.mainPlayButton.on("click",_self.callbacks.onPlay);
            _self.ui.elements.pauseButton.on("click",_self.callbacks.onPause);
            $(window).on('resize',_self.callbacks.resize);

            _self.ui.elements.video.addEventListener("click", _self.callbacks.togglePlayPause);
            _self.ui.elements.volumeButton.on("click", function () {
                _self.actions.mute();
            });
            _self.ui.elements.volumeButtonMute.on("click", function () {
                _self.actions.mute();
                _self.actions.unmute();
            });

            _self.ui.elements.volumeBarCont.on("mouseup mousedown mouseleave touchmove", function (event) {

                var volumeBar = _self.ui.elements.volumeBarCont;
                switch (event.type) {
                    case "mousedown":
                        var percent = (parseInt(event.pageX) - volumeBar.offset().left) / (volumeBar.width());
                        _self.actions.setVolume(percent);
                        volumeBar.on('mousemove', function (event) {
                            var percent = (parseInt(event.pageX) - volumeBar.offset().left) / (volumeBar.width());
                            _self.actions.setVolume(percent);
                            return false;
                        });
                        break;
                    case "mouseup":
                        volumeBar.off("mousemove");
                        break;
                    case "mouseleave":
                        volumeBar.off("mousemove");
                        break;
                    default:
                        break;
                }
                return false;
            });

            _self.ui.elements.bar1.on("click",_self.callbacks.selectSegment);
            _self.ui.elements.bar2.on("click",_self.callbacks.selectSegment);
            _self.ui.elements.bar3.on("click",_self.callbacks.selectSegment);

            _self.ui.elements.seekBar.on("mousedown", function (event) {
                var video = _self.ui.elements.video;
                var progressBar = _self.ui.elements.progressBar;
                var percent = (parseInt(event.pageX) - progressBar.offset().left) / (progressBar.width());
                var nextTime = Math.floor(video.duration * percent);
                video.currentTime = nextTime;
                video.play();
            });

            _self.ui.elements.rewindButton.on("click", function () {
                _self.ui.elements.currentTime = 0;
                _self.ui.elements.rewindButton.hide();
                _self.actions.play();
            });

            _self.ui.elements.fullScreen.on("click", _self.callbacks.onFullScreen);

        },
        setSource:function(){
            _self.ui.elements.video.src = _self.vars.videoSrc;

        },
        actions:{
            play:function(){
                _self.ui.elements.video.play();
            },
            pause:function(){
                _self.ui.elements.video.pause();
                _self.ui.elements.playButton.show();
                _self.ui.elements.mainPlayButton.show();
                _self.ui.elements.pauseButton.hide();
            },
            mute: function () {
                var auxVolume = _self.vars.currentVolume;
                _self.actions.setVolume(0);
                _self.vars.currentVolume = auxVolume;
            },
            unmute: function () {
                if (_self.vars.currentVolume === 0) {
                    _self.actions.setVolume(_self.config.player.volume / 100);
                } else {
                    _self.actions.setVolume(_self.vars.currentVolume);
                }
            },
            setVolume: function (percent) {
                if (percent > 0.95)
                    percent = 1;
                if (percent < 0.1) {
                    percent = 0;
                    _self.ui.elements.volumeButtonMute.show();
                    _self.ui.elements.volumeButton.hide();
                } else {
                    _self.ui.elements.volumeButtonMute.hide();
                    _self.ui.elements.volumeButton.show();
                }
                _self.ui.elements.video.volume = percent;
                _self.vars.currentVolume = percent;
                var w = Math.floor(percent * 100) + "%";
                _self.ui.elements.volumeBar.width(w);
            },
            fullScreen: function () {
                var element = _self.ui.elements.contentId[0];
                if (document.webkitIsFullScreen || document.mozFullScreen || document.msFullscreenElement){
                    if (document.exitFullscreen){
                        document.exitFullscreen();
                    } else if (document.mozCancelFullScreen){
                        document.mozCancelFullScreen();
                    } else if (document.webkitExitFullscreen){
                        document.webkitExitFullscreen();
                    }
                } else {
                    if (element.requestFullscreen){
                        element.requestFullscreen();
                    } else if (element.mozRequestFullScreen){
                        element.mozRequestFullScreen();
                    } else if (element.webkitRequestFullscreen){
                        element.webkitRequestFullscreen();
                    } else if (element.msRequestFullscreen){
                        element.msRequestFullscreen();
                    }
                }
            },
            showCutTools:function(){
                _self.ui.elements.markIndicatorA.show();
                _self.ui.elements.markLabelA.show();
                _self.ui.elements.markIndicatorB.show();
                _self.ui.elements.markLabelB.show();
                _self.ui.elements.cutBar.show();
                _self.ui.elements.bar1.show();
                _self.ui.elements.bar2.show();
                _self.ui.elements.bar3.show();
            }
        },
        callbacks:{
            togglePlayPause: function () {
                var video = _self.ui.elements.video;
                if (video.paused) {
                    video.play();
                } else {
                    video.pause();
                }
            },
            onEnded:function(event){
                _self.ui.elements.playButton.show();
                _self.ui.elements.mainPlayButton.hide();
                _self.ui.elements.pauseButton.hide();
                _self.ui.elements.rewindButton.show();
            },
            onPause:function(event){
                _self.actions.pause();
            },
            onPlay:function(event){
                _self.actions.play();
            },
            onPlaying:function(event){
                _self.ui.elements.playButton.hide();
                _self.ui.elements.mainPlayButton.hide();
                _self.ui.elements.loader.hide();
                _self.ui.elements.pauseButton.show();
            },
            onTimeUpdate: function (event) {
                var currenttime = event.target.currentTime;
                var duration = event.target.duration;
                var percent = Math.floor(currenttime * 100 / duration);
                _self.ui.elements.seekBar.show();
                _self.ui.elements.rewindButton.hide();
                _self.ui.elements.playingBar.width(Math.floor(_self.ui.elements.seekBar.width()*percent/100)+ "px");
                _self.ui.elements.timeContent.text(_self.helper.formatTime(currenttime) + " / " + _self.helper.formatTime(duration));
            },
            onFullScreen: function () {
                _self.actions.fullScreen();
            },
            resize:function(){
                _self.ui.elements.playerContent.height(_self.ui.elements.contentId.height() - _self.vars.controlsHeight);

                _self.ui.elements.cutBar.width(_self.ui.elements.seekBar.width());
                // _self.callbacks.setMarkerA(_self.vars.markA);
                // _self.callbacks.setMarkerB(_self.vars.markB);

                var markIndicatorA = _self.ui.elements.markIndicatorA;
                var markLabelA = _self.ui.elements.markLabelA;
                var seekBar = _self.ui.elements.seekBar;
                var controls = _self.ui.elements.controls;
                var percent = _self.vars.markA / _self.ui.elements.video.duration;
                _self.ui.elements.bar1.width(seekBar.width()*percent);
                markIndicatorA.css('left',(seekBar.offset().left - controls.offset().left + seekBar.width()*percent) - 3 + 'px');
                markLabelA.css('left',(seekBar.offset().left - controls.offset().left + seekBar.width()*percent) - (markLabelA.width()/2) + 'px');
                var markIndicatorB = _self.ui.elements.markIndicatorB;
                var markLabelB = _self.ui.elements.markLabelB;
                percent = _self.vars.markB / _self.ui.elements.video.duration;
                _self.ui.elements.bar2.width(seekBar.width()*percent);
                markIndicatorB.css('left',(seekBar.offset().left - controls.offset().left + seekBar.width()*percent) - 3 + 'px');
                markLabelB.css('left',(seekBar.offset().left - controls.offset().left + seekBar.width()*percent) - (markLabelB.width()/2) + 'px');
            },
            setMarkerA:function(time){
                switch(_self.vars.currentPlayer){
                    case 'flash':
                        Flash.setMarkerA();
                        break;
                    case 'html5':
                        _self.actions.showCutTools();
                        var markIndicatorA = _self.ui.elements.markIndicatorA;
                        var markLabelA = _self.ui.elements.markLabelA;
                        var seekBar = _self.ui.elements.seekBar;
                        var controls = _self.ui.elements.controls;
                        _self.vars.markA = (time == undefined)?_self.ui.elements.video.currentTime:time;
                        if(_self.vars.markA >= _self.vars.markB){
                            _self.callbacks.setMarkerB(_self.ui.elements.video.duration);
                        }
                        var percent = _self.vars.markA / _self.ui.elements.video.duration;
                        _self.ui.elements.bar1.width(seekBar.width()*percent);
                        markIndicatorA.css('left',(seekBar.offset().left - controls.offset().left + seekBar.width()*percent) - 3 + 'px');
                        markLabelA.css('left',(seekBar.offset().left - controls.offset().left + seekBar.width()*percent) - (markLabelA.width()/2) + 'px');
                        break;
                }
            },
            setMarkerB:function(time){
                switch(_self.vars.currentPlayer){
                    case 'flash':
                        Flash.setMarkerB();
                        break;
                    case 'html5':
                        _self.actions.showCutTools();
                        var markIndicatorB = _self.ui.elements.markIndicatorB;
                        var markLabelB = _self.ui.elements.markLabelB;
                        var seekBar = _self.ui.elements.seekBar;
                        var controls = _self.ui.elements.controls;
                        _self.vars.markB = (time == undefined)?_self.ui.elements.video.currentTime:time;
                        if(_self.vars.markA >= _self.vars.markB){
                            _self.callbacks.setMarkerA(0);
                        }
                        var percent = _self.vars.markB / _self.ui.elements.video.duration;
                        _self.ui.elements.bar2.width(seekBar.width()*percent);
                        markIndicatorB.css('left',(seekBar.offset().left - controls.offset().left + seekBar.width()*percent) - 3 + 'px');
                        markLabelB.css('left',(seekBar.offset().left - controls.offset().left + seekBar.width()*percent) - (markLabelB.width()/2) + 'px');
                        break;
                }
            },
            selectSegment:function(event){
                $("#cutBar div").each(function(){
                    $(this).removeClass('barActive');
                })
                $(this).addClass('barActive');
            },
            getMarkers:function(){
                switch(_self.vars.currentPlayer){
                    case 'flash':
                        return Flash.getMarkers();
                        break;
                    case 'html5':
                        var marcas = [0,0];
                        $("#cutBar div").each(function(){
                            if($(this).hasClass('barActive')){
                                switch($(this)[0].id){
                                    case 'bar1':
                                        marcas = [0,_self.vars.markA];
                                        break
                                    case 'bar2':
                                        marcas = [_self.vars.markA,_self.vars.markB];
                                        break
                                    case 'bar3':
                                        marcas = [_self.vars.markB, _self.ui.elements.video.duration];
                                        break
                                }
                            }
                        })
                        return marcas;
                        break;
                }
            },
            getPlayPoint:function(){
                switch(_self.vars.currentPlayer){
                    case 'flash':
                        return Flash.getPlayPoint();
                        break;
                    case 'html5':
                        return _self.ui.elements.video.currentTime;
                        break;
                }
            },
            reloadVideo: function (link) {
                switch(_self.vars.currentPlayer){
                    case 'flash':
                        Flash.setMovie(link);
                        break;
                    case 'html5':
                        break;
                }
            }
        },
        helper:{
            formatTime: function (seconds) {
                var m = Math.floor(seconds / 60) < 10 ? "0" + Math.floor(seconds / 60) : Math.floor(seconds / 60);
                var s = Math.floor(seconds - (m * 60)) < 10 ? "0" + Math.floor(seconds - (m * 60)) : Math.floor(seconds - (m * 60));
                return m + ":" + s;
            },
            iTShouldBeHtml5:function(){
                return _self.helper.html5Mp4Support();
            },
            html5Mp4Support: function () {
                return (document.createElement('video').canPlayType('video/mp4') != "")?true:false;
            },
            iTShouldBeFlash:function(){
                return _self.helper.hasFLash();
            },
            hasFLash: function () {
                var hasFlash = false;
                try {
                    hasFlash = Boolean(new ActiveXObject('ShockwaveFlash.ShockwaveFlash'));
                } catch(exception) {
                    hasFlash = ('undefined' != typeof navigator.mimeTypes['application/x-shockwave-flash']);
                }
                return hasFlash;
            },
            isIE:function(){
                var ua = window.navigator.userAgent;
                var msie = ua.indexOf("MSIE ");

                if (msie > 0){ // If Internet Explorer, return version number
                    return true
                    //alert(parseInt(ua.substring(msie + 5, ua.indexOf(".", msie))));
                }

                return false;
            }
        }
    };
})();
