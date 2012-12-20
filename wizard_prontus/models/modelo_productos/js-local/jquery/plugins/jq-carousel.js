/* 
* hardcode.nl jQuery carousel Plugin
* version: 1.01 (12-DEC-2009)
* @requires jQuery 
*
* Examples and documentation at: http://www.hardcode.nl/demos/overlay.html
* Dual licensed under the MIT and GPL licenses:
*   http://www.opensource.org/licenses/mit-license.php
*   http://www.gnu.org/licenses/gpl.html
*
*/

(function($){
  $.fn.imageCarousel = function(options) {
 		var busy = false, i=0,endReached = false; 
 		var opts = $.extend({}, $.fn.imageCarousel.defaults, options);
 
 		this.each(function() {
   		$this = $(this);
   		$children = $(this).children();
			$firstchild = $children.eq(0);
			var itemHeight = opts.itemHeight ? opts.itemHeight : $firstchild.outerHeight(true);
			var itemWidth = $firstchild.outerWidth(true);
			var totWidth = parseInt($children.length) * itemWidth;
   		//store itemWidth
   		/* @todo - allow for variable width elements: */
 
   		$this.data("imageCarouselData", {'itemWidth': itemWidth,'itemHeight':itemHeight});
   		// update element styles
   		$children.css({'float':'left'});
 			$this.wrap('<div style="position:relative; height:'+itemHeight+'px; width:'+opts.visibleItems*itemWidth+'px; overflow:hidden" class="featureWindow" ></div>')
			 	.css({position:'absolute',top:'0px',left:'0px', width:totWidth+'px',margin:'0px',paddingRight:'0px',paddingLeft:'0px',height:itemHeight+'px'})
			 	.parent().after('<div class="carouselButtons"><a href="#" class="leftArrow carouselWhiteArrows ">'+opts.leftArrowText+'</a><a href="#" class="rightArrow carouselWhiteArrows">'+opts.rightArrowText+'</a></div>'); 
		});
		$('.carouselWhiteArrows').click(function(){	
			if (busy) return false; 
			busy = true;
			var featureWindow = $(this).parent().prev();
			var featureContainer = featureWindow.children().eq(0);
			var features = featureContainer.children();
			var curPos = featureContainer.offset().left - featureWindow.offset().left //- featureWindow.offsetParent().offset().left;
			var direction = this.className.indexOf('eftArrow'); 
			var dat = featureContainer.data('imageCarouselData');
			var xMove = dat.itemWidth * opts.moveElements;
			var newX = parseInt(curPos) + (xMove * direction)
 
			if (direction===1 && curPos >=0){
				newX = -parseInt((featureContainer.outerWidth(true))- featureWindow.outerWidth(true));
				endReached = true; 
			}else{
				//check for end of the list/*
				if (direction == -1){ 
						if((parseInt(featureContainer.outerWidth(true)+newX )- featureWindow.outerWidth(true))< 0){
						if (!endReached){
							endReached = true; 
							newX = -parseInt((featureContainer.outerWidth(true))- featureWindow.outerWidth(true));
						}else{
							endReached = false; 
							newX=0;
						}
					}
				}else if (newX >=0){newX = 0}
			}
			featureContainer.animate({left: newX+'px'}, opts.speed,function(){busy=false;});
			return false;
		});
		if (opts.autoScroll){
			var lastArrow = $('.rightArrow').eq($('.rightArrow').length-1);
		 	setInterval(function(){lastArrow.click()},0);
		}
	return this;
  };
 
  $.fn.imageCarousel.defaults = {
 	leftArrowText: 'left',
 	rightArrowText: 'right',
 	visibleItems:4,
 	moveElements:3,
 	speed:2000,
 	itemHeight:0,
	autoScroll:false
  };
})(jQuery);
