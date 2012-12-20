<?php
//Includes
require_once dirname(__FILE__) . '/_str.php';


// ----------------------------------------------------
// Valida acceso al form para emitir opinion en foro
// Esto mismo se valida ademas enla cgi, por si acceden al form o la invocan directamente.
function _acceso_check_formforo($forocerrado, $apert_fecha, $apert_hora, $cierre_fecha, $cierre_hora) {
    // valida q el foro no este cerrado, esto afecta indistintamente de si el foro requiere o no autenticacion
    if ($forocerrado) {
        return "Los comentarios de esta noticia se encuentran cerrados desde el ". $cierre_fecha ." a las ". $cierre_hora ."hrs";
    }

    // fechas vienen como dd/mm/aaaa y horas como hh:mm
    $cierre = _str_date2iso($cierre_fecha) . substr($cierre_hora,0,2) .  substr($cierre_hora,3,2); // aaaammddhhmm
    $apert = _str_date2iso($apert_fecha) . substr($apert_hora,0,2) .  substr($apert_hora,3,2); // aaaammddhhmm
    $ts_now = date("YmdHi"); // aaaammddhhmm
    if (($cierre <= $ts_now) and ($cierre >= $apert)) {
        return "Los comentarios de esta noticia se encuentran cerrados desde el ". $cierre_fecha ." a las ". $cierre_hora ."hrs";
    }
    if ($apert > $ts_now) {
        return "Este foro se encuentra cerrado hasta el $cierre_fecha - $cierre_hora hrs.";
    }
    return '';
};
?>