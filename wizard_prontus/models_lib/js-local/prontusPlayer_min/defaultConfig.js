(function (window) {
    var defaultConfig = {
        contentId: 'prontusPlayer',  // Id del Div que contiene el player.
        player: {
            swf: "player/prontusPlayer.swf", // URl del player flash.
            imageFolder: 'img/', //ruta de la carpeta con las imagenes de prontusPlayer
            waitUntilContentLoaded:false,   //permite forzar que el player se instale una vez cargada la página
            forcePlayer: false, //permite forzar el player por defecto en caso contrario se implementara el player html5 solo en dispositivos moviles.
            defaultPlayer: "flash", //player por defecto puede ser flash o html5
            autoPlay: false,    //habilita la reproducción automática
            pseudoStreaming:false,  //habilita el pseudistreaming en flash
            adEnable: false,    //habilita la publicidad
            forceSize: true,    //fuerza el tamaño del player
            volume: 100,    //volumen inicial del player
            width: 640,     //ancho del player
            height: 480,    //alto del player
            seek: 20,   //tiempo en segundo para los saltos relativos
            showPanelOnComplete: "share", // permite identificar que panel se muestra al finalizar el video puede ser "related" o "share"
        },
        ads: {
            adInfoMsg: "La publicidad finaliza en __TIME__ segundos.", //mensaje que se muestra mientras se reproduce el pre-roll (__TIME__ es marca reservada que se reemplaza con el tiempo restante en segundos)
            adVideoTag: "", //url vast pre-roll
            adBannerTag: "", //url vast overlay 
            adBannerInterval: 120000,   // [ms] intervalo de tiempo para la aparición del overlay
            overlayDelay: 10000,    // [ms] delay entre el fin del preroll y el inicio del overlay (si no hay preroll, corresponde al delay en relación al inicio del video)
            overlayAutoHideDelay: 20000     //[ms] tiempo para que se auto oculte el overlay
        },
        share: {
            enableShare: false,     //habilita el panel de compartir
            shareUrl: "shareUrl",   //link a compartir
            embedCode: "embedCode"  //codigo embed a compartir 
        },
        
    };
    window.prontusPlayerDefaultConfig = defaultConfig;
})(window);