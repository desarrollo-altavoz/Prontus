<?php

class TagsRelac {

    public static $MAX_ARTICS = 5;
    public static $PRONTUS_ID = '';
    public static $TODAY = '';
    public static $REL_PATH_TXT = '';
    public static $TIME_ZONE = 'America/Santiago';

    public static $result;
    //date_default_timezone_set();

    /** --------------------------------------------------------------- **/
    /** Se encarga de cambiar el TimeZone por defecto **/
    public static function setTimeZone($str) {
        if($str != '') {
            TagsRelac::$TIME_ZONE = $str;
        }
    }

    /** --------------------------------------------------------------- **/
    /** Busca el arreglo con todos los artículos asociados **/
    public static function getArrayArtics($tags = '', $prontus, $ts = '', $max = 0) {

        if($max > 0) {
            TagsRelac::$MAX_ARTICS = $max;
        }

        TagsRelac::$result = array();
        date_default_timezone_set(TagsRelac::$TIME_ZONE);
        TagsRelac::$TODAY = date('YmdHi');

        // Para el Prontus
        TagsRelac::$PRONTUS_ID = $prontus;
        if(TagsRelac::$PRONTUS_ID == '') {
            return TagsRelac::$result;
        }
        TagsRelac::$REL_PATH_TXT = $_SERVER['DOCUMENT_ROOT'].'/'.TagsRelac::$PRONTUS_ID.'/site/cache/tagging/pags/';

        // Para los tags
        if($tags == '') {
            return TagsRelac::$result;
        }

        $arr_tags = explode(',', $tags);
        foreach($arr_tags as $tag) {
            $arr_artic = TagsRelac::getDataCSV($tag);
            TagsRelac::$result = ($arr_artic + TagsRelac::$result);
        }

        // Se elimina el artículo actual
        if(!empty(TagsRelac::$result[$ts])) {
            unset(TagsRelac::$result[$ts]);
        }

        // Realizar el orden y el filtrado
        uasort(TagsRelac::$result, "TagsRelac::cmpFechaHora");
        if(sizeof(TagsRelac::$result) > TagsRelac::$MAX_ARTICS) {
            $result = array_slice(TagsRelac::$result, 0, TagsRelac::$MAX_ARTICS, true);
        }

        return TagsRelac::$result;
    }

    /** --------------------------------------------------------------- **/
    /** Lee un archivo CSV y lo convierte en arreglo **/
    public static function getDataCSV($tag = '') {
        $arr = array();
        if($tag === '' || !is_numeric($tag)) {
            return $arr;
        }

        $counter = 1;
        $txt = TagsRelac::$REL_PATH_TXT . $tag . '.txt';
        if(is_file($txt)) {
            if (($handle = fopen($txt, "r")) !== FALSE) {
                while (($data = fgetcsv($handle, 1000, "\t")) !== FALSE) {
                    if(count($data) != 8 || array_key_exists($data[0], TagsRelac::$result)) {
                        continue;
                    }
                    $artic = array(
                            'fechahorap' => $data[1],
                            'fechahorae' => $data[2],
                            'titular' => $data[3],
                            'extension' => $data[4],
                            'fid' => $data[5],
                            'soloport' => $data[6],
                            'ctrlfecha' => $data[7]);

                    if(TagsRelac::chequeaStatus($artic)) {
                        $artic['file_url'] = TagsRelac::makeFriendlyURL($data[0], $artic);
                        $arr[$data[0]] = $artic;
                        // En el peor de los casos, se necesitan MAX_ARTICS artículos
                        // Se asume que vienen ordenados por fechap
                        if($counter > TagsRelac::$MAX_ARTICS) {
                            fclose($handle);
                            return $arr;
                        }
                        $counter++;
                    }
                }
                fclose($handle);
            }
        }
        return $arr;
    }

    /** --------------------------------------------------------------- **/
    /** Chequea el status del artículo **/
    public static function chequeaStatus($arr_artic, $today = '') {

        $tags_fechahorap = $arr_artic['fechahorap'];
        $tags_fechahorae = $arr_artic['fechahorae'];
        $tags_soloport = $arr_artic['soloport'];
        $tags_ctrlfecha = $arr_artic['ctrlfecha'];

        if($today === '') {
            $today = TagsRelac::$TODAY;
            if($today === '') {
                date_default_timezone_set(TagsRelac::$TIME_ZONE);
                $today = date('YmdHi');
            }
        };

        // se chequea la fecha de publicacion
        if($tags_fechahorap > $today) {
            error_log($tags_fechahorap .'>'. $today);
            return false;
        }

        // Se chequea la expiracion, siempre que haya control_fecha y no tenga el despublicar sólo de portadas
        if($tags_ctrlfecha) {
            if($tags_soloport != '1' && $tags_fechahorae < $today) {
                return false;
            }
        }
        return true;
    }

    /** --------------------------------------------------------------- **/
    /** Entrega la Friendly URL de un articulo **/
    public static function makeFriendlyURL($ts, $arr_artic, $prontus = '') {

        if($prontus === '') {
            $prontus = TagsRelac::$PRONTUS_ID;
        }

        $titular = $arr_artic['titular'];
        $ext = $arr_artic['extension'];
        $server = $_SERVER['SERVER_NAME'];
        if(preg_match("|^(\d{4})(\d{2})(\d{2})(\d{6})$|", $ts, $matches)) {
            $fechac = $matches[1] . '-' . $matches[2] . '-' . $matches[3];
            $hora = $matches[4];
            // Se limpia el titular
            $newtitular = TagsRelac::escapeEntities($titular);
            $newtitular = TagsRelac::clearTags($newtitular);
            $newtitular = strtolower($newtitular);
            $filef = "http://$server/$newtitular/$prontus/$fechac/$hora.$ext";
            return $filef;
        };
        return '';
    }

    /** --------------------------------------------------------------- **/
    /** Para escapear las entidades **/
    public static function escapeEntities($titular) {
        $titular = strtolower($titular);
        $titular = preg_replace('/á/',  'a', $titular);
        $titular = preg_replace('/é/',  'e', $titular);
        $titular = preg_replace('/í/',  'i', $titular);
        $titular = preg_replace('/ó/',  'o', $titular);
        $titular = preg_replace('/ú/',  'u', $titular);
        $titular = preg_replace('/Á/',  'a', $titular);
        $titular = preg_replace('/É/',  'e', $titular);
        $titular = preg_replace('/Í/',  'i', $titular);
        $titular = preg_replace('/Ó/',  'o', $titular);
        $titular = preg_replace('/Ú/',  'u', $titular);
        $titular = preg_replace('/ü/',  'u', $titular);
        $titular = preg_replace('/Ü/',  'u', $titular);
        $titular = preg_replace('/ñ/',  'n', $titular);
        $titular = preg_replace('/Ñ/',  'n', $titular);

        $titular = preg_replace('/&(.)acute;/', "$1", $titular);
        $titular = preg_replace('/&(.)acute;/', "$1", $titular);
        $titular = preg_replace('/&(.)uml;/',   "$1", $titular);
        $titular = preg_replace('/&(.)circ;/',  "$1", $titular);
        $titular = preg_replace('/&(.)grave;/', "$1", $titular);
        $titular = preg_replace('/&[^;]+;/',    '', $titular);

        return $titular;
    }

    /** --------------------------------------------------------------- **/
    /** Elimina los tags del Titular **/
    public static function clearTags($titular) {

        $titular = preg_replace('/\r\n/',   ' ',    $titular);
        $titular = preg_replace('/\n/',     ' ',    $titular);
        $titular = preg_replace('/\r/',     ' ',    $titular);
        $titular = preg_replace('/<.*?>/',  ' ',    $titular);
        $titular = preg_replace('/ {2,}/',  ' ',    $titular);
        $titular = preg_replace('/ $/',     '',     $titular);
        $titular = preg_replace('/^ /',     '',     $titular);
        $titular = preg_replace("/'/",          "\xB4", $titular);
        $titular = preg_replace('/&#39;/',      "\xB4", $titular);
        $titular = preg_replace('/[^a-z0-9]/',  '-',    $titular);
        $titular = preg_replace('/\-+/',        '-',    $titular);
        $titular = preg_replace('/^\-|-$/',     '',     $titular);

        return $titular;
    }

    /** --------------------------------------------------------------- **/
    /** Para ordenar los campos **/
    public static function cmpFechaHora($a, $b) {

        //echo '<pre>A:'; print_r($a); echo 'B:'; print_r($b); echo '</pre>';
        if($a['fechahorap'] == $b['fechahorap']) {
            return 0;
        }
        if($a['fechahorap'] > $b['fechahorap']) {
            return -1;
        } else {
            return 1;
        }
    }
}
?>