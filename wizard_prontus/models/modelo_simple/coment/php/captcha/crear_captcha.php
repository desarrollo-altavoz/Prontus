<?php
if(session_id() == '') {
    session_start();
};
// Despliega un captcha y deja en una cookie el valor crypteado
$MAX_SESSION = 500; // Numero maximo de sessiones permitidas para almacenar captcha de artículos
$CAPTCHA_TEXT = set_captcha_texto($MAX_SESSION);
$width = 110;
$height = 25;

//error_log($CAPTCHA_TEXT);
if (empty($CAPTCHA_TEXT)){ /* generar captcha no disponible */

    // Si no se esta disponible el texto para el captcha, se genera captcha  no disponible
    $image = imagecreatefromgif(dirname(__FILE__)."/../../imag/nodisponible.gif");

    //Covierte la imagen a *.PNG y la envia al browser
    if($image) {
        header("Content-Type: image/png");
        ImagePNG($image);
        ImageDestroy($image);
    }
} else {  /*genera captcha */

    $captcha_imagen = imagecreate($width,$height);
    $color_negro = imagecolorallocate ($captcha_imagen, 0, 0, 0);
    $color_blanco = imagecolorallocate ($captcha_imagen, 255, 255, 255);
    $noise_color = imagecolorallocate($captcha_imagen, 203, 9, 9);
    imagefill($captcha_imagen, 0, 0, $color_blanco);

    /* generate random dots in background */
    for( $i=0; $i<($width*$height)/30; $i++ ) {
       imagefilledellipse($captcha_imagen, mt_rand(0,$width), mt_rand(0,$height), 1, 1, $noise_color);
    }

    /* generate random lines in background */
    for( $i=0; $i<($width*$height)/600; $i++ ) {
       // imageline($captcha_imagen, mt_rand(0,$width), mt_rand(0,$height), mt_rand(0,$width), mt_rand(0,$height), $noise_color);
    }
    $font_size = $height * 0.70;
    $suple_y = 15;
    imagettftext($captcha_imagen, $font_size, mt_rand(-5, 5), 10, mt_rand(2, 5)+$suple_y, $color_negro, "./fontcaptcha.ttf", $CAPTCHA_TEXT[0]);
    imagettftext($captcha_imagen, $font_size, mt_rand(-5, 5), 35, mt_rand(2, 5)+$suple_y, $color_negro, "./fontcaptcha.ttf", $CAPTCHA_TEXT[1]);
    imagettftext($captcha_imagen, $font_size, mt_rand(-5, 5), 60, mt_rand(2, 5)+$suple_y, $color_negro, "./fontcaptcha.ttf", $CAPTCHA_TEXT[2]);
    imagettftext($captcha_imagen, $font_size, mt_rand(-5, 5), 85, mt_rand(2, 5)+$suple_y, $color_negro, "./fontcaptcha.ttf", $CAPTCHA_TEXT[3]);
    header("Content-type: image/jpeg");
    imagejpeg($captcha_imagen);
}



//-------------------------------------------------------------------------------------------------
function set_captcha_texto($MAX_SESSION) {

    // Si no se envia el ts en la peticion php para generar imagen no retorna el texto del captcha
    if (!isset($_GET["_ts"])) return "";
    $ts = $_GET["_ts"];

    $captcha_texto = "";
    for ($i = 1; $i <= 4; $i++) {
        $captcha_texto .= caracter_aleatorio();
    };
    $captcha_text_crypted = crypt(strtolower($captcha_texto),'av');

    /* CPN - 13/08/2010 - Implementa potencialidad de comentar en mas de un articulo abierto al mismo tiempo*/
    $sessions = 0;
    if (isset($_SESSION)){
        $var = count($_SESSION);
        $sessions = 0;

        // Contar las sessiones usadas para comentar artículos, solo cuenta variables de session usada en el sistema de comentarios
        foreach ($_SESSION as $key => $value){
            $flag = preg_match('/_COMENT_CAPTCHA_/', $key, $arr);
            if ($flag) $sessions++;
        }
    };

    if (isset($_SESSION["_COMENT_CAPTCHA_".$ts])){

        // Si existe la session para el artículo resetear el captcha del artículo
        $_SESSION["_COMENT_CAPTCHA_".$ts] = $captcha_text_crypted;
    } else {

         // No esta seteada la session del comentario del articulo y existe disponible de limite de sessiones
         if ($sessions < $MAX_SESSION){
            $_SESSION["_COMENT_CAPTCHA_".$ts] = $captcha_text_crypted;
         } else {

            // No esta seteada la variable de session y tampoco existen  sessiones disponibles
            return "";
         }
    }
    return $captcha_texto;
    /* CPN - 13/08/2010*/

};


//-------------------------------------------------------------------------------------------------
// Retorna un string aleatorio de n letras.
function caracter_aleatorio() {
    $charset = 'ABCDEFGHJKLMNPRTUVWXY23456789abcdeghijkmnprsuvwxyz';
    $salida = substr($charset, mt_rand(0, strlen($charset)-1), 1);
    return $salida;
};

?>