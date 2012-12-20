<?php
 /**
 * [encargada de la administración de sessiones del sistema de comentarios]
 *
 * inicialmente, solo contendra la logica para ejecutar unset de la variables de session para el sistema de comentarios
 *
 * INVOCACIONES ACEPTADAS:
 * - solo via web, enviandole el parametro de la acción a realizar
 *
 * @package coment
 * @author  CPN cpizarro@altavoz.net
 * @version 
 * 1.0.0 - 18/08/2010 - CPN - Primera version
 * @todo 
 */  


// Recibir parametros de entrada
$_sid = (isset($_GET['_sid']))? $_GET['_sid']: "";
if (!$_sid) return "";


// Destruir session del articulo
if (isset($_SESSION[$_sid ])) unset($_SESSION[$_sid ]);
return 1;

?>