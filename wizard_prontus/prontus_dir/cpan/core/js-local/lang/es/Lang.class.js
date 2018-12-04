/**
 * Specific Language
 */
var ProntusLang = (function(window, undefined) {
    var RESOURCE_NOT_FOUND = 'Specified resource can\'t be found in Lang file.';
    var strings = {
        /* Acciones.class.js */
        '_action_art_delete_confirm'    : '¿Está seguro que desea eliminar este artículo?',
        '_action_art_delete_error'      : 'Se produjo un error al borrar el artículo',
        '_action_port_save_wait_for_load': 'Por favor, antes de guardar, espere hasta que la carga termine',
        '_action_port_save_wrong_load'  : 'La portada no cargó correctamente. Por favor, refresque el listado antes de guardar',
        '_action_port_save_success'     : 'La portada ha sido guardada',
        '_action_port_vobo_do_publish'  : 'Publicar en esta portada',
        '_action_port_vobo_dont_publish': 'No publicar en esta portada',

        /* Admin.class.js */
        '_admin_logout'                 : 'Vuelve prontus...',
        '_admin_alt_display_message_close'  : 'Cerrar Mensaje',
        '_admin_alt_publicacion_directa': 'Publicación Directa',
        '_admin_port_concurrency'       : 'Otros usuarios editando esta Portada: ',
        '_admin_art_concurrency'        : 'Otros usuarios editando este Artículo: ',
        '_admin_concurrency'            : 'Concurrencia',
        '_admin_locked_art_warning'     : 'Este Artículo está siendo utilizado por otro usuario.\nIngrese el siguiente código para poder utilizarlo.',
        '_admin_locked_port_warning'    : 'Esta Portada está siendo utilizada por otro usuario.\nIngrese el siguiente código para poder utilizarla.',
        '_admin_locked_warning'         : 'Advertencia',
        '_admin_locked_code'            : 'Código',
        '_admin_locked_art_error'       : 'El artículo está siendo utilizado por otro usuario y ha sido bloqueado para su edición.',
        '_admin_locked_port_error'      : 'La portada está siendo utilizada por otro usuario y ha sido bloqueada para su edición.',
        '_admin_unlock_get_code'        : 'Debe ingresar el código __code__ para desbloquear el recurso.',
        '_admin_unlock_invalid_code'    : 'El código ingresado es inválido.\nPorfavor ingrese el siguiente código para desbloquear el recurso: __code__',
        '_admin_install_conn_error'     : 'Se ha producido un error de conexión.',
        '_admin_install_status'         : 'El status entregado por el servidor',
        '_admin_install_wait'           : 'Espere unos minutos, si el problema persiste, consulte con el administrador de su servidor web. ',
        '_admin_install_technical'      : 'Para ver el detalle técnico del error presione ',
        '_admin_install_button'         : 'aquí',
        '_admin_install_conn_error_dialog'   : 'Error de Conexión',
        '_admin_update_to_release'      : 'Actualizar a la release \'__release__\'',
        '_admin_update_none_available'  : 'No hay actualizaciones disponibles',
        '_admin_update_disabled'        : 'Las actualizaciones están deshabilitadas',
        '_admin_update_cant_get_info'   : 'No se pudo obtener información sobre las actualizaciones',
        '_admin_update_confirm'         : '¿Está seguro de actualizar a Prontus __version__?\nEsta operación actualizará las CGIs y los \'core\' de todas las instancias Prontus instaladas en su sitio web.',

        /* Ayuda.class.js */
        '_help_generic_error'           : 'Ocurrió un error, intentelo nuevamente.',
        '_help_reporting_guidelines'    : '** Guía de reporte de errores **\n\nPara reportar un error, completar el mensaje con la siguiente información:\n\n* Asunto: Resumen del problema, por ejemplo, \'No se pueden subir fotos\'.\n',

        /* Buscador.class.js */
        '_search_by_title'              : 'Buscar por Titular',

        /* Captcha.class.js */
        '_captcha_imp_error'            : 'Error en la implementación',
        '_captcha_load_error'           : 'Error al leer el captcha, intente de nuevo',
        '_captcha_missing_type'         : 'Debe indicar el tipo de Captcha',

        /* CfgXcoding.class.js */
        '_xcoding_format_load_error'    : 'Ha ocurrido un error al cargar los formatos: ',
        '_xcoding_default_format_label' : 'Por defecto',
        '_xcoding_existing_format_error': 'Este formato ya existe',
        '_xcoding_character_restriction_error'  : 'Sólo se pueden ingresar letras. No se permite Ñ, espacios, números, letras con tilde o símbolos',
        '_xcoding_format_identifier_required'   : 'Debe ingresar un identificador para el formato',
        '_xcoding_existing_mark'        : 'Esta marca ya existe',
        '_xcoding_only_numbers_allowed' : 'Sólo se pueden ingresar números.',
        '_xcoding_id_required'          : 'Debe ingresar un id',
        '_xcoding_mark_deletion_confirm': '¿Estás seguro de eliminar la marca de transcodificación?\nSe eliminarán todos los formatos asociados. Esta acción no se puede deshacer.',
        '_xcoding_format_deletion_confirm'      : '¿Estás seguro de eliminar el formato de transcodificación?. Esta acción no se puede deshacer.',
        '_xcoding_format_cant_be_deleted'       : 'Este formato no se puede eliminar',
        '_xcoding_odd_videosize_error'  : 'El parametro VIDEOSIZE no puede ser impar, formato incorrecto:\n',
        '_xcoding_format_modification_confirm'  : '¿Estás seguro de modificar los formatos de transcodificación?',
        '_xcoding_format_save_success'  : 'Se han guardado correctamente los formatos',
        '_xcoding_format_save_error'    : 'Ha ocurrido un error al guardar los formatos: ',

        /* Cfgedit.class.js */
        '_cfg_modify_confirm'           : '¿Estás seguro de modificar la configuración?',
        '_cfg_cloudflare_purge_all_confirm' : '¿Estás seguro? Esta operación no se puede revertir ni detener.',
        '_cfg_cloudflare_purge_all_started' : 'Se inició el proceso de limpieza. Esto puede tardar varios minutos en completarse.',
        '_cfg_cloudflare_purge_file_confirm': '¿Estás seguro? Esta operación no se puede revertir ni detener.',
        '_cfg_cloudflare_purge_empty_list'  : 'La lista de archivos está vacia.',
        '_cfg_cloudflare_purge_file_started': 'Se inició el proceso de limpieza. Esto puede tardar unos minutos en completarse.',

        /* Coment.class.js */
        '_comment_delete_confirm'       : 'Está seguro de borrar este comentario?',
        '_comment_approve'              : 'Aprobar comentario',
        '_comment_disapprove'           : 'Desaprobar comentario',
        '_comment_generic_error'        : 'Ocurrio un error, intentelo nuevamente.',

        /* EdiAdmin.class.js */
        '_edition_admin_delete_confirm' : '¿Estás seguro de borrar esta edición?',

        /* Fechas.class.js */
        '_dates_months'                 : ['enero','febrero','marzo','abril','mayo','junio', 'julio','agosto','septiembre','octubre','noviembre','diciembre'],
        '_dates_days'                   : ['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'],

        /* Fid.class.js */
        '_fid_show_calendar'            : 'Mostrar calendario',
        '_fid_image_with_errors'        : 'Imagen con errores',
        '_fid_invalid_file_extension'   : 'El archivo [__filename__] es inválido.\nLos archivos permitidos son imágenes gif, png, jpg o jpeg.',
        '_fid_upload_examine'           : 'Examinar...',
        '_fid_upload_response_error'    : 'No fue posible subir correctamente la imagen [__filename__]',
        '_fid_upload_error'             : 'No fue posible subir la imagen',
        '_fid_click_to_delete'          : 'Click para borrar',
        '_fid_click_to_cancel_delete'   : 'Click para cancelar eliminación',
        '_fid_duplicate_article_confirm': 'Este artículo será copiado.\nSe perderán los datos que no hayas guardado.\n¿Deseas continuar?',
        '_fid_download_backup'          : 'Descargar respaldo',
        '_fid_unknown_type'             : 'tipo desconocido: ',

        /* FidConfig.class.js */
        '_fid_alert_loading'            : 'El FID aún no termina de cargar o ha fallado la carga. Por favor, refresque el FID antes de guardar',
        '_fid_alert_no_ts'              : 'Antes debe guardar el Artículo',
        '_fid_remove_backup_confirm'    : 'Está seguro que quiere eliminar el archivo de respaldo de datos?\nEsta operación no puede deshacerse.',

        /* ImgEdit.class.js */
        '_img_width_exceeded'           : 'No puedes superar el ancho de la imagen (__max_width__px).',
        '_img_height_exceeded'          : 'No puedes superar el alto de la imagen (__max_height__px).',
        '_img_dimensions_exceeded'      : 'La imagen no puede soprepasar las dimesiones __max_width__x__max_height__px.',
        '_img_no_changes'               : 'No has aplicado ninguna modificación.',
        '_img_cant_save_img_not_editing': 'No es posible guardar la imagen, el artículo ya no se encuentra en edición.',
        '_img_processing_error'         : 'Ocurrió un error al procesar la imagen, inténtalo nuevamente.',

        /* Intercambio.class.js */
        '_exchange_cant_exchange_self'  : 'No es posible intercambiar una portada consigo misma.',
        '_exchange_success'             : 'Las portadas seleccionadas fueron intercambiadas correctamente.',
        '_exchange_incomplete_selection': 'Por favor, seleccione portadas a intercambiar.',

        /* Listartic.class.js */
        '_listartic_change_port'        : 'La portada ha sido modificada, debe guardar para conservar los cambios',
        '_listartic_unsaved_changes_confirm_exit'   : 'La portada ha sido modificada. ¿Está seguro que desea abandonar esta página?',
        '_listartic_unsaved_changes_confirm_refresh': 'La portada ha sido modificada. ¿Está seguro que desea refrescar el listado de artículos publicados?',
        '_listartic_activate_area'      : 'El área __area__ ha sido activada. Ahora puede usar el botón "Publicar en Área Activa".',
        '_listartic_corrupted_deleted_file'         : 'Artículo Eliminado o Corrupto',
        '_listartic_save_before_delete' : 'Para eliminar de la portada, debe guardar ésta',
        '_listartic_article_regen_required'         : 'Para eliminar del listado, se debe "Regenerar tabla de Artículos"',
        '_listartic_port_number'        : 'Nº de Portadas: ',
        '_listartic_modified_seconds'   : 'Modificada hace unos segundos',
        '_listartic_modified_one_minute': 'Modificada hace un minuto',
        '_listartic_modified_minutes'   : 'Modificada hace __diff__ minutos',
        '_listartic_modified_today_time': 'Modificada hoy a las __hora__ hrs',
        '_listartic_modified_yesterday_time'        : 'Modificada ayer a las __hora__ hrs',
        '_listartic_modified_date'      : 'Modificada el __fecha__',

        /* Megalupa.class.js */
        '_megalupa_date_creation'       : 'de creación',
        '_megalupa_date_publication'    : 'de publicación',
        '_megalupa_date_expiration'     : 'de expiración',
        '_megalupa_art_invalid_code'    : 'Código de artículo no es válido.',
        '_megalupa_invalid_date_format' : 'La fecha __type__ no tiene un formato válido. (dd/mm/aaaa)',
        '_megalupa_wrong_month'         : 'El Mes (fecha __type__) debe estar entre 1 y 12.',
        '_megalupa_wrong_day'           : 'El dia (fecha __type__) debe estar entre 1 y 31.',
        '_megalupa_month_wrong_days'    : 'El Mes __month__ (fecha __type__) no tiene 31 días!',
        '_megalupa_feb_wrong_days'      : 'Febrero __year__ (fecha __type__) no tiene __day__ días!',

        /* Opciones.class.js */
        '_options_confirm_art_regen'    : '¿Está seguro de regenerar la tabla de artículos?',
        '_options_confirm_mult_regen'   : '¿Está seguro de regenerar la tabla de multimedia?',
        '_options_fid_required'         : 'Debe seleccionar al menos 1 FID.',
        '_options_invalid_date_format'  : 'El formato de la fecha no es válido, intente dd-mm-yyyy  ',
        '_options_confirm_art_massive_regen'    : '¿Está seguro de ejecutar la actualización masiva de artículos?',
        '_options_confirm_port_massive_regen'   : '¿Está seguro de ejecutar la actualización masiva de portadas?',
        '_options_selection_required'   : 'Debe elegir una de las opciones anteriores',
        '_options_error_processing_script'      : 'Error al procesar el script, recargue la página para continuar',
        '_options_unavailable'          : 'No disponible',

        /* PortAdmin.class.js */
        '_portadmin_prompt_new_template'    : 'Plantilla Origen: __template__\nIngrese el nombre de la nueva plantilla, ejemplo: politica.html',
        '_portadmin_invalid_template_name'  : 'Nombre de plantilla no válido.\nDebe comenzar con letra, número o underscore.\nCaracteres permitidos:letras minúsculas, dígitos, guión y underscore más el punto para la extensión, la cual es obligatoria.',
        '_portadmin_duplicate_port_required': 'Por favor, seleccione una portada para duplicar.',
        '_portadmin_delete_port_confirm'    : '¿Está seguro de eliminar esta Portada?',
        '_portadmin_delete_port_required'   : 'Por favor, seleccione una portada para borrar.',

        /* PortDD.class.js */
        '_portdd_wait_for_process'      : 'Espere a que el proceso termine.',
        '_portdd_unsaved_changes_confirm_refresh': 'La portada ha sido modificada. ¿Está seguro que desea refrescar?. Se perderán los cambios.',
        '_portdd_duplicated_art_error'  : 'Error: Existen articulos duplicados. Para continuar debe corregir esto.',
        '_portdd_hide_areas'            : 'Ocultar áreas drag & drop',
        '_portdd_visualize_areas'       : 'Visualizar áreas drag & drop',

        /* Preview.class.js */
        '_preview_wait_for_load'        : 'Por favor, espere a que termine de generar el Preview',
        '_preview_error_reloading'      : 'Se produjo un error al intentar recargar el preview',
        '_preview_invalid_date'         : 'La fecha no es válida, no se puede calcular el Preview',
        '_preview_invalid_hour'         : 'La hora no es válida, no se puede calcular el Preview',
        '_preview_error_reloading'      : 'Se produjo un error al intentar recargar el preview',

        /* Recordarpass.class.js */
        '_remember_pass_new_pass_sent'  : 'La nueva contraseña ha sido enviada a tu email registrado en Prontus.',

        /* Seo.class.js */
        '_seo_missing_description': '¡Falta descripción SEO!',

        /* SubmitForm.class.js */
        '_submitform_ajax_error': 'Server error procesando request ajax:\nURL invocada:',

        /* Tags.class.js */
        '_tags_default_tag_text'    : 'Escoja un tag',
        '_tags_search_text'         : 'Buscar Tags',
        '_tags_quick_search'        : 'Búsqueda rápida',
        '_tags_tag_name'            : '[Nombre del Tag]',
        '_tags_no_parent_window'    : 'No se pudo detectar la ventana Padre.',
        '_tags_deleting_error'      : 'Error, no se pudo eliminar',
        '_tags_delete_confirm'      : '¿Está seguro que quiere borrar este Tag?',
        '_tags_wait_before_delete'  : 'Espere unos segundos antes de realizar esta acción',
        '_tags_open_admin_tags_confirm': 'Se perderán los cambios que haya realizado en el artículo.\n¿Desea continuar?\n\nAyuda: Puede usar botón derecho y \nabrir en otra pestaña o en ventana nueva.',
        '_tags_keyword_required'    : 'Debes ingresar la palabra clave.',
        '_tags_filter_required'     : 'Ingrese un texto para filtrar los tags',

        /* Tax.class.js */
        '_tax_hide_from_fid'    : 'Click para ocultar en el FID',
        '_tax_show_in_fid'      : 'Click para visibilizar en el FID',
        '_tax_generic_error'    : 'Ocurrio un error, intentelo nuevamente.',
        '_tax_section_confirm_delete'   : '¿Estás seguro que quieres borrar esta sección?',
        '_tax_topic_confirm_delete'     : '¿Estás seguro que quieres borrar este tema?',
        '_tax_subtopic_confirm_delete'  : '¿Estás seguro que quieres borrar este subtema?',

        /* Transcoding.class.js */
        '_transcode_checking_state'     : 'Chequeando estado del video',
        '_transcode_needs_adjustment'   : 'El video mp4 necesita ser ajustado para su correcta reproducción, por favor espere mientras es procesado.',
        '_transcode_adjusted'           : 'El video mp4 se encuentra ajustado para su correcta reproducción.',
        '_transcode_generating_versions': 'Generando versiones del video.',
        '_transcode_bitrate_too_high_adjusting'     : 'El video mp4 tiene un bitrate muy alto y necesita ser ajustado para su correcta reproducción, por favor espere mientras es procesado.',
        '_transcode_invalid_response'   : 'Se ha producido un error:<br/> Respuesta no válida',
        '_transcode_error_adjusting_video'          : 'Se ha producido un error al realizar el ajuste del Video:<br/> ',
        '_transcode_critical_error_adjusting_video' : 'Se ha producido un error crítico al realizar el ajuste del Video:<br/> ',
        '_transcode_error_retrieving_status'        : 'Se ha producido un error al recuperar el Status:<br/> Respuesta no válida',
        '_transcode_video_being_processed'          : 'El video está siendo procesado',
        '_transcode_error_converting_video'         : 'Se ha producido un error al realizar la Conversión del Video:<br/> ',
        '_transcode_critical_error_converting_video': 'Se ha producido un error crítico al realizar la Conversión del Video:<br/> ',
        '_transcode_ajax_response_error': 'Se ha producido un error en la respuesta Ajax:',
        '_transcode_screenshot_creating': 'Generando la captura',
        '_transcode_screenshot_wait_for_conversion' : 'Debe esperar a que termine la conversión antes de extraer la captura',
        '_transcode_screenshot_no_video_loaded'     : 'Debe cargar un video antes de extraer la captura',
        '_transcode_screenshot_error_reading_time'  : 'No se pudo leer el tiempo asociado a la Captura',
        '_transcode_screenshot_done'    : 'La extracción de la captura ha finalizado',
        '_transcode_screenshot_error'   : 'Se ha producido un error al extraer la Captura del Video:<br/> ',
        '_transcode_cut_creating'       : 'Generando el Corte del Video',
        '_transcode_cut_wait_for_conversion'        : 'Debe esperar a que termine la conversión antes de poder editar',
        '_transcode_cut_no_video_loaded': 'Debe cargar un video antes de poder editar',
        '_transcode_cut_couldnt_get_marks'          : 'No se pudo obtener las marcas para cortar',
        '_transcode_cut_wrong_mark_format'          : 'El formato de las marcas entregado por el Flash no es válido',
        '_transcode_cut_correct_mark_usage'         : 'Debe ingresar 1 o 2 marcas y presionar sobre el trozo<br/> de película que desee cortar',
        '_transcode_cut_success'        : 'El video ha sido cortado exitosamente',
        '_transcode_cut_generic_error'  : 'Se ha producido un error al cortar el Video:<br/> ',
        '_transcode_file_without_extension'         : 'El archivo no posee extensión',
        '_transcode_unsupported_file_extension'     : 'El sistema sólo soporta archivos del tipo: avi, flv, mp4, wmv, mpg, mpeg, 3gp, mov',
        '_transcode_information'        : 'Información',
        '_transcode_loading'            : 'Cargando',
        '_transcode_alert'              : 'Alerta',
        '_transcode_error_loading_player'           : 'Se ha producido un error cargando el player de video.',
        '_transcode_flash_setmovie_error'           : 'Error al invocar función del Flash setMovie()',
        '_transcode_flash_getplaypoint_error'       : 'Error al invocar función del Flash getPlayPoint():<br/> ',
        '_transcode_flash_setmarkera_error'         : 'Error al invocar función del Flash setMarkerA():<br/> ',
        '_transcode_flash_setmarkerb_error'         : 'Error al invocar función del Flash setMarkerB():<br/> ',
        '_transcode_flash_getmarkers_error'         : 'Error al invocar función del Flash getMarkers():<br/> ',

        /* UsrAdmin.class.js */
        '_usradmin_confirm_usr_delete'  : '¿Está seguro de borrar a este usuario?',
        '_usradmin_generic_error'       : 'Ocurrio un error, inténtelo nuevamente.',
        '_usradmin_confirm_save'        : '¿Está seguro que desea guardar sus datos?',

        /* Utiles.class.js */
        '_util_enable_popups'           : 'Debes habilitar las ventanas emergentes en tu navegador para acceder a esta funcionalidad.'
    };

    return {
        RESOURCE_NOT_FOUND: RESOURCE_NOT_FOUND,
        strings: strings
    };

})(window);
