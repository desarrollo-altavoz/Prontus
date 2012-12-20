/**
 * Clase encargada de colocar y actualizar la fecha y hora en una pagina web
 * Versión: 2.0.0 - 15/06/2011
 */

var FechaHora = {

    idFecha: "lafecha", // ID del div o span que contendrá la fecha
    idHora: "lahora", // ID del div o span que contendrá la hora
    tUpdate: 1000, // Tiempo en milisegundos en que se refrescará la fecha/hora

    domfecha: null,
    domhora: null,
    tInterval: -1,

    // -----------------------------------------------
    // Se inicia el intervalo de tiempo
    init: function () {
        if (typeof document.getElementById !== 'undefined') {
            FechaHora.write_fecha_hora();
            FechaHora.tInterval = setInterval(function () {
                FechaHora.write_fecha_hora();
            }, FechaHora.tUpdate);
        }
    },

    // -----------------------------------------------
    // Para detener el timer
    stop: function () {
        clearInterval(FechaHora.tInterval);
        FechaHora.domfecha = null;
        FechaHora.domhora = null;
    },

    // -----------------------------------------------
    // Funcion para escritura de fecha / hora
    write_fecha_hora: function () {
        var hr, fec;
        // Para la fecha
        fec = oNow.get_fecha(1);  // ---- Modificar Aca
        if (FechaHora.domfecha !== null) {
            FechaHora.domfecha.innerHTML = fec;
        } else {
            if (document.getElementById(FechaHora.idFecha)) {
                FechaHora.domfecha = document.getElementById(FechaHora.idFecha);
                FechaHora.domfecha.innerHTML = fec;
            }
        }

        // Para la hora
        hr = oNow.get_hora() + ' hrs'; // ---- Modificar Aca
        if (FechaHora.domhora !== null) {
            FechaHora.domhora.innerHTML = hr;
        } else {
            if (document.getElementById(FechaHora.idHora)) {
                FechaHora.domhora = document.getElementById(FechaHora.idHora);
                FechaHora.domhora.innerHTML = hr;
            }
        }
    }
};

// Se inicia el sistema
//FechaHora.init();