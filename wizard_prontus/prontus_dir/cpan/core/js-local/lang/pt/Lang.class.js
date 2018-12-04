/**
 * Specific Language
 */
var ProntusLang = (function(window, undefined) {
    var RESOURCE_NOT_FOUND = 'Specified resource can\'t be found in Lang file.';
    var strings = {
        /* Acciones.class.js */
        'action_art_delete_confirm'     : '¿Está seguro que desea eliminar este artículo?',
        'action_art_delete_error'       : 'Se produjo un error al borrar el artículo',
        'action_port_save_wait_for_load': 'Por favor, antes de guardar, espere hasta que la carga termine',
        'action_port_save_wrong_load'   : 'La portada no cargó correctamente. Por favor, refresque el listado antes de guardar',
        'action_port_save_success'      : 'La portada ha sido guardada',
        'action_port_vobo_do_publish'   : 'Publicar en esta portada',
        'action_port_vobo_dont_publish' : 'No publicar en esta portada',

        /* Admin.class.js*/
        'admin_logout'                  : 'Vuelve prontus...',
        'admin_alt_display_message_close': 'Cerrar Mensaje',
        'admin_alt_publicacion_directa' : 'Publicación Directa',
        'admin_port_concurrency'        : 'Otros usuarios editando esta Portada: ',
        'admin_art_concurrency'         : 'Otros usuarios editando este Artículo: ',
        'admin_concurrency'             : 'Concurrencia',
        'admin_locked_art_warning'      : 'Este Artículo está siendo utilizado por otro usuario.\nIngrese el siguiente código para poder utilizarlo.',
        'admin_locked_port_warning'     : 'Esta Portada está siendo utilizada por otro usuario.\nIngrese el siguiente código para poder utilizarla.',
        'admin_locked_warning'          : 'Advertencia',
        'admin_locked_code'             : 'Código',
        'admin_locked_art_error'        : 'El artículo está siendo utilizado por otro usuario y ha sido bloqueado para su edición.',
        'admin_locked_port_error'       : 'La portada está siendo utilizada por otro usuario y ha sido bloqueada para su edición.',
        'admin_unlock_get_code'         : 'Debe ingresar el código __code__ para desbloquear el recurso.',
        'admin_unlock_invalid_code'     : 'El código ingresado es inválido.\nPorfavor ingrese el siguiente código para desbloquear el recurso: __code__',
        'admin_install_conn_error'      : 'Se ha producido un error de conexión.',
        'admin_install_status'          : 'El status entregado por el servidor',
        'admin_install_wait'            : 'Espere unos minutos, si el problema persiste, consulte con el administrador de su servidor web. ',
        'admin_install_technical'       : 'Para ver el detalle técnico del error presione ',
        'admin_install_button'          : 'aquí',
        'admin_install_conn_error_dialog': 'Error de Conexión',
        'admin_update_to_release'       : 'Actualizar a la release \'__release__\'',
        'admin_update_none_available'   : 'Não há atualizações disponíveis',
        'admin_update_disabled'         : 'Las actualizaciones están deshabilitadas',
        '': ''
    };

    return {
        RESOURCE_NOT_FOUND: RESOURCE_NOT_FOUND,
        strings: strings
    };

})(window);
