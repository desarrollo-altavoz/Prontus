/* =========================================================

// jquery.innerfade.js

// Datum: 2007-01-29
// Firma: Medienfreunde Hofmann & Baldes GbR
// Autor: Torsten Baldes
// Mail: t.baldes@medienfreunde.com
// Web: http://medienfreunde.com

// based on the work of Matt Oakes http://portfolio.gizone.co.uk/applications/slideshow/

// ========================================================= */
// jquery.animated.innerfade.js

// Datum: 2007-10-30
// Firma: OpenStudio
// Autor: Arnault PACHOT
// Mail: apachot@openstudio.fr
// Web: http://www.openstudio.fr




(function($) {

  $.fn.animatedinnerfade = function(options) {
    var mytimer;
    var pauseActivated=false;
    this.each(function(){
      var settings = {
        animationtype: 'fade',
        speed: 'normal',
        timeout: 15000,
        type: 'sequence',
        containerheight: '300px',
        containerwidth: '600px',
        runningclass: 'innerfade',
        animationSpeed: 15000,
        bgFrame: 'none',
        controlButtonsPath: 'img',
        controlBox: 'none',
        controlBoxClass: 'none',
        displayTitle: 'none',
        titleClass: 'innerfade-title'
      };
      $(this).css('margin', '0 0 0 0').css('padding', '0 0 0 0').find('img').css('border', 'none');
      if(options)
      $.extend(settings, options);

      var elements = $(this).children();

      if (settings.displayTitle != 'none')
      $(this).append("<div class='"+settings.titleClass+"'><h2>"+$(elements[0]).find("img:first").attr("title")+"</h2></div>");

      if (settings.bgFrame != 'none')
      {
        $(this).append("<div class='bg-frame'><a href='"+$(elements[0]).find("a:first").attr("href")+"'><img src='"+settings.bgFrame+"' width='"+settings.containerwidth+"' height='"+settings.containerheight+"' style='border: none;' /></a></div>");
        $(this).find(".bg-frame").css('position', 'absolute').css('top', 0).css('left', 0).css('z-index', 300).css('height', settings.containerheight).css('width', settings.containerwidth);
      }
      if (settings.controlBox != 'none')
      {
        if (settings.controlBoxClass != 'none') $(this).append("<div class='"+settings.controlBoxClass+" control-panel'><a class='back-button' href='#'><img src='"+settings.controlButtonsPath+"/previous.gif' alt='previous' style='border: none;' /></a> <a class='pause-button' href='#'><img src='"+settings.controlButtonsPath+"/pause.gif' alt='pause' style='border: none;' /></a> <a class='next-button' href='#'><img src='"+settings.controlButtonsPath+"/next.gif' alt='next' style='border: none;' /></a></div>");
        else $(this).append("<div class='control-panel'><a class='back-button' href='#'><img src='"+settings.controlButtonsPath+"/previous.gif' alt='previous' style='border: none;' /></a> <a class='pause-button' href='#'><img src='"+settings.controlButtonsPath+"/pause.gif' alt='pause' style='border: none;' /></a> <a class='next-button' href='#'><img src='"+settings.controlButtonsPath+"/next.gif' alt='next' style='border: none;' /></a></div>");

          if (settings.controlBox != "show")
          {
            $(this).find(".control-panel").hide();
            $(this).bind('mouseover', function(){$(this).find(".control-panel").show();});
            $(this).bind('mouseout', function(){$(this).find(".control-panel").hide();});
          }

          $(this).find(".control-panel").css('z-index', 350).css('position', 'absolute');
          if (settings.controlBoxClass == 'none')
          $(".control-panel").css('right', '10px').css('top', '5px').css('textAlign', 'right').css('margin', 0).css('paddingTop', '0').css('marginRight', '0').css('fontSize', '20px').css('color', '#88d300');

          $(this).find(".control-panel a.next-button").bind('click', function(){pauseActivated = false; clearTimeout(mytimer); $(".control-panel a.pause-button").html("<img src='"+settings.controlButtonsPath+"/pause.gif' alt='pause' style='border: none;' />"); $.animatedinnerfade.next(elements, settings, 1, 0, mytimer, pauseActivated);return false;});
          $(this).find(".control-panel a.back-button").bind('click', function(){pauseActivated = false; clearTimeout(mytimer); $(".control-panel a.pause-button").html("<img src='"+settings.controlButtonsPath+"/pause.gif' alt='pause' style='border: none;' />"); $.animatedinnerfade.next(elements, settings, elements.length - 1, 0, mytimer, pauseActivated);return false;});
          $(this).find(".control-panel a.pause-button").bind('click', function(){
            clearTimeout(mytimer);
            if (!pauseActivated){
              pauseActivated = true;
              $(this).html("<img src='"+settings.controlButtonsPath+"/play.gif' alt='play' style='border: none;' />");
              $(elements[0]).stop().stop();
            }else {
              pauseActivated = false;
              $(this).html("<img src='"+settings.controlButtonsPath+"/pause.gif' alt='pause' style='border: none;' />");
              var vwidth =  - (parseInt($(elements[0]).find("img").attr("width"))-parseInt(settings.containerwidth));
              if (vwidth > 0) vwidth = 0;
              var duree = parseInt(settings.timeout) - parseInt((parseInt($(elements[0]).css('left')) / parseInt(vwidth)) * parseInt(settings.timeout));
              $(elements[0]).animate({top: 0, left: vwidth}, duree);
              mytimer = setTimeout(function(){
                $.animatedinnerfade.next(elements, settings, 1, 0, mytimer, pauseActivated);
              }, duree);
            }
            return false;
          });
        }


        if (elements.length > 1) {

          $(this).css('position', 'relative').css('overflow', 'hidden').css('height', settings.containerheight).css('width', settings.containerwidth);

          $(this).addClass(settings.runningclass);

          for ( var i = 0; i < elements.length; i++ ) {
            $(elements[i]).css('position', 'absolute').css('top', 0).css('left', 0).css('z-index', String(elements.length-i));
            $(elements[i]).hide();
          };
          $(elements[0]).css('top', 0);
          $(elements[0]).css('left', 0);

          $.animatedinnerfade.move_photo(elements[0], settings);

          if ( settings.type == 'sequence' ) {
            mytimer = setTimeout(function(){
              $.animatedinnerfade.next(elements, settings, 1, 0, mytimer, pauseActivated);
            }, settings.timeout);

          }
          else {
            var nextrandom;
            do { nextrandom = Math.floor ( Math.random ( ) * ( elements.length ) ); } while ( nextrandom == 0 )
            mytimer = setTimeout((function(){$.animatedinnerfade.next(elements, settings, nextrandom, 0, mytimer, pauseActivated);}), settings.timeout);

          }
          $(elements[0]).show();
        }

      });
    };


    $.animatedinnerfade = function() {}
    $.animatedinnerfade.next = function (elements, settings, current, last, mytimer, pauseActivated) {
      var vwidth =  - (parseInt($(elements[current]).find("img").attr("width"))-parseInt(settings.containerwidth));
      if ((parseInt($(elements[current]).css('left')) == 0) || (parseInt($(elements[current]).css('left')) == vwidth))
      {
        clearTimeout(mytimer);


        var vwidth =  - (parseInt($(elements[current]).find("img").attr("width"))-parseInt(settings.containerwidth));

        var next, prev;
        if (current == (elements.length - 1))
        next = 0;
        else
          next = current+1;

          if (current == 0)
          prev = elements.length - 1;
          else
            prev = current - 1;

            for ( var i = 0; i < elements.length; i++ ) {
              if ((i != last) && (i != current))
              {
                $(elements[i]).css('z-index', '1');
                $(elements[i]).css('top', 0).css('left', 0);
                $(elements[i]).hide();
              }
            }

            $(elements[last]).css('z-index', '190');
            $(elements[current]).css('z-index', '195');

            if (settings.displayTitle != 'none')
            $("."+settings.titleClass+" h2").html($(elements[current]).find("img:first").attr("title"));

            if (settings.controlBox != 'none')
            {
              $(this).find(".control-panel a.next-button").unbind('click'); $(".control-panel a.next-button").bind('click', function(){pauseActivated = false;clearTimeout(mytimer);$(".control-panel a.pause-button").html("<img src='"+settings.controlButtonsPath+"/pause.gif' alt='pause' style='border: none;' />"); $.animatedinnerfade.next(elements, settings, next, current, mytimer, pauseActivated);return false;});
              $(this).find(".control-panel a.back-button").unbind('click'); $(".control-panel a.back-button").bind('click', function(){pauseActivated = false; clearTimeout(mytimer);$(".control-panel a.pause-button").html("<img src='"+settings.controlButtonsPath+"/pause.gif' alt='pause' style='border: none;' />"); $.animatedinnerfade.next(elements, settings, prev, current, mytimer, pauseActivated);return false;});
              $(this).find(".control-panel a.pause-button").unbind('click');$(".control-panel a.pause-button").bind('click', function(){
                clearTimeout(mytimer);
                if (!pauseActivated){
                  pauseActivated = true;
                  $(this).html("<img src='"+settings.controlButtonsPath+"/play.gif' alt='play' style='border: none;' />"); $(elements[current]).stop().stop();
                }else{
                  pauseActivated = false;
                  $(this).html("<img src='"+settings.controlButtonsPath+"/pause.gif' alt='pause' style='border: none;' />");
                  var vwidth =  - (parseInt($(elements[current]).find("img").attr("width"))-parseInt(settings.containerwidth));
                  if (vwidth > 0) vwidth = 0;
                  var duree = parseInt(settings.timeout) - parseInt((parseInt($(elements[current]).css('left')) / parseInt(vwidth)) * parseInt(settings.timeout));
                  $(elements[current]).animate({top: 0, left: vwidth}, duree);
                  mytimer = setTimeout((function(){$.animatedinnerfade.next(elements, settings, next, current, mytimer, pauseActivated);}), duree);
                }
                return false;
              });
            }
            if (settings.bgFrame != 'none')
            $(this).find(".bg-frame a").attr("href", $(elements[current]).find("a:first").attr("href"));

            $(elements[current]).css('top', 0).css('left', 0);
            if ( settings.animationtype == 'slide' ) {
              $(elements[last]).slideUp(settings.speed, $(elements[current]).slideDown(settings.speed));
            } else if ( settings.animationtype == 'fade' ) {
              $(elements[last]).fadeOut(settings.speed);
              $(elements[current]).fadeIn(settings.speed);
            } else {
              alert('animationtype must either be \'slide\' or \'fade\'');
            };

            $.animatedinnerfade.move_photo(elements[current], settings);

            if ( settings.type == 'sequence' ) {
              mytimer = setTimeout((function(){$.animatedinnerfade.next(elements, settings, next, current, mytimer, pauseActivated);}), settings.timeout);
            }
            else
              {
                var nextrandom;
                do { nextrandom = Math.floor ( Math.random ( ) * ( elements.length ) ); } while ( nextrandom == current )
                mytimer = setTimeout((function(){$.animatedinnerfade.next(elements, settings, nextrandom, current, mytimer, pauseActivated);}), settings.timeout);
              }
            }
          };

          $.animatedinnerfade.move_photo = function (element, settings) {

            if (settings.animationSpeed > 0)
            {
              var vheight =  - (parseInt($(element).find("img").attr("height"))-parseInt(settings.containerheight));
              var vwidth =  - (parseInt($(element).find("img").attr("width"))-parseInt(settings.containerwidth));
              if (vheight > 0) vheight = 0;
              if (vwidth > 0) vwidth = 0;
              $(element).show().css('left', 0).css('top', 0).animate({top: vheight, left: parseInt(vwidth/2)}, parseInt(settings.animationSpeed/2)).animate({top: 0, left: vwidth}, parseInt(settings.animationSpeed/2));
            }
          };

        })(jQuery);

