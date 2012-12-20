<?php
// ---------------------------------------------------------
// Recibe la fecha y la convierte a formato aaaammdd
// $fecha = Fechas del tipo dd/mm/aaaa || dd-mm-aaaa
// Retorna: aaaammdd
function _str_date2iso($fecha) {
    $dia  = substr($fecha,0,2);
    $mes  = substr($fecha,3,2);
    $anno = substr($fecha,6,4);
    return "$anno$mes$dia";
};
?>