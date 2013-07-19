$(document).ready(function() {

	$('cite[title]').each(function() {
		var el = $(this);
		var title = el.attr('title');
		var tooltip = $('<span class="infoTooltip"><span class="flecha"></span>'+title+'</span>').css({
			position: 'absolute',
			top: el.offset().top +20,
			left: el.offset().left +20
		});
		
		el.mouseover(function() {
			$('body').append(tooltip);
			el.attr('title','');
		}).mouseout(function() {
			tooltip.remove();
			el.attr('title',title);
		});
	});

});