$(function() {
    $(".area-list").sortable({
            // items: 'li:not(".disabled")',
            cancel: '.disabled',
            connectWith: '.area-list',
            dropOnEmpty: true,
            placeholder: 'placeholder',
            handle: 'h2',

            containment: 'document',
            opacity: 0.6,
            zIndex:20000,
            helper: 'clone',

            update: function() {
                Listado.procesarListado('.area-list', 'li');
            }
     });
    $(".area-list li:not('.disabled') h2").css('cursor', 'move');
    $(".area-list li.disabled .item").css('background-color', '#eee');
    $(".area-list li.disabled .item .controls input").attr('readonly', 'readonly');

    // Las manejas los Fold de las áreas
    $('.titulo-area a').click(function() {
        var strId = $(this).parent().attr('id');
        strId = strId.substr(1, strId.length - 1);
        if($('#'+strId).is(':visible')) {
            $(this).find('span').removeClass('ui-icon-circle-triangle-s').addClass('ui-icon-circle-triangle-e');
            $('#'+strId).slideUp();
        } else {
            $(this).find('span').removeClass('ui-icon-circle-triangle-e').addClass('ui-icon-circle-triangle-s');
            $('#'+strId).slideDown();
        }
    });

    // Maneja los botones que Manejan todas las áreas
    $('#colapsar-todo').click(function() {
        $('#cont-pub .titulo-area span').removeClass('ui-icon-circle-triangle-s').addClass('ui-icon-circle-triangle-e');
        $('#cont-pub ul.area-list:visible').slideUp();
    });
    $('#descolapsar-todo').click(function() {
        $('#cont-pub .titulo-area span').removeClass('ui-icon-circle-triangle-e').addClass('ui-icon-circle-triangle-s');
        $('#cont-pub ul.area-list:hidden').slideDown();

    });
    // Finalmente se procesa el listado
    Listado.procesarListado('.area-list', 'li');
});

