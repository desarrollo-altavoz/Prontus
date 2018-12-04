// Funciones relativas al manejo de fechas en formularios.
// 1.1 - 16/10/2007 - ych - Agrega un par de hh extras al hacer el new date a raiz de problemas
// con el cambio de hora detectados en lanacion2007

Fechas = {

    objFormFid: '', // se setea en el doc. ready

//    meses: ['enero','febrero','marzo','abril','mayo','junio', 'julio','agosto','septiembre','octubre','noviembre','diciembre'],
//    dias: ['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'],

    w2: function(num,n) {
        var a = num + '';
        while (a.length < n) {
            a = '0' + a;
        }
        return a;
    },

    validaFechaText: function(texto) {
        var datearray = texto.split('/');
        if ( isNaN(datearray[0]) || isNaN(datearray[1]) || isNaN(datearray[2]) ||
                (datearray[0] < 1) || (datearray[0] > 31) ||
                (datearray[1] < 1) || (datearray[1] > 12) ||
                (datearray[2] < 1) || (datearray[2] > 3000)) {
            return 0;
        } else {
            return 1;
        }
    },

    text2date: function(texto) {
        var datearray = texto.split('/');
        if (datearray[2] < 100) {
            datearray[2] = datearray[2] * 1 + 2000;
        }
        var date = new Date(datearray[2],(datearray[1] - 1),datearray[0],2,0,0); // 1.1
        return date;
    },

    date2iso: function(fechadate) {
        var ano = fechadate.getYear();
        if (ano < 200) { // onda 103, NS70
            ano = ano + 1900;
        }

        ano = Fechas.w2(ano,4);

        var mes = Fechas.w2(1 + fechadate.getMonth(),2);
        var dia = Fechas.w2(fechadate.getDate(),2);
        return ano + mes + dia + '';
    },

    date2text: function(fechadate) {
        var ano = fechadate.getYear();
        if (ano < 200) { // onda 103, NS70
            ano = ano + 1900;
        }

        ano = Fechas.w2(ano,4);

        var mes = Fechas.w2(1 + fechadate.getMonth(),2);
        var dia = Fechas.w2(fechadate.getDate(),2);
        return dia + '/' + mes + '/' + ano;
    },



    iso2date: function(iso) {
        if (iso.length == 8) {
            var ano = 0 + iso.substring(0,4);
            var mes = 0 + iso.substring(4,6);
            var dia = 0 + iso.substring(6);
            var date=new Date();
            date.setFullYear(ano,(mes - 1),dia);
            return date;
        }else{
            return Date();
        }
    },

    iso2longdate: function(iso) {
        var date = new Date();
        var ano;
        var mes;
        var dia;
        if (iso.length == 8) {
            ano = 1 * iso.substring(0,4);
            mes = 1 * iso.substring(4,6);
            dia = 1 * iso.substring(6);
            // var date = new Date(ano,(mes - 1),dia);
            date.setFullYear(ano,(mes - 1),dia);
        } else {
            ano = date.getDate();
            mes = date.getMonth();
            dia = date.getYear();
        }
        var diasem = ProntusLang.strings.dates_days[date.getDay()];
        var mes2 = ProntusLang.strings.dates_months[mes - 1];
        return diasem + ', ' + dia + ' de ' + mes2 + ' de ' + ano;
    },

    escribeFecha: function(isoin) {
        if (isoin == '99999999') { return; } // Fecha no válida.
        var iso;
        if (isoin === '') {
            var date = new Date();
            iso = Fechas.date2iso(date);
        }else{
            iso = isoin;
        }
        var texto = Fechas.iso2longdate(iso);
        document.write(texto);
    },

    fillfechapshrt: function() {
        var theForm = Fechas.objFormFid;
        // LLena fechapshrt en base a fechap
        if (typeof(theForm._FECHAP) !== 'undefined') {
            var fechap = theForm._FECHAP.value;
            if (fechap == '99999999') {
                theForm._FECHAPSHRT.value = '';
            } else {
                var date;
                if (fechap === '') {
                    date = new Date();
                } else {
                    date = Fechas.iso2date(fechap);
                }
                theForm._FECHAPSHRT.value = Fechas.date2text(date);
            }
        }

        // LLena fechaeshrt en base a fechae
        if (typeof(theForm._FECHAE) !== 'undefined') {
            var fechae = theForm._FECHAE.value;
            if (fechae == '99999999') {
                theForm._FECHAESHRT.value = '';
            } else {
                if (fechae === '') {
                    theForm._FECHAESHRT.value = '';
                }else{
                    var date2 = Fechas.iso2date(fechae);
                    theForm._FECHAESHRT.value = Fechas.date2text(date2);
                }

            }
        }

    },

    parseaFecha: function(fechapshrt) {
        if (fechapshrt === '') { return ''; }
        var iso = '';
        if (Fechas.validaFechaText(fechapshrt)) {
            var date = Fechas.text2date(fechapshrt);
            iso = Fechas.date2iso(date);
        }
        return iso;
    },

    fillfechap: function() {
        var theForm = Fechas.objFormFid;
        if (typeof(theForm._FECHAP) != 'undefined') {
            var fechapshrt = theForm._FECHAPSHRT.value;
            var fechap = Fechas.parseaFecha(fechapshrt);
            theForm._FECHAP.value = fechap;
        }

        if (typeof(theForm._FECHAE) != 'undefined') {
            var fechaeshrt = theForm._FECHAESHRT.value;
            var fechae = Fechas.parseaFecha(fechaeshrt);
            theForm._FECHAE.value = fechae;
        }

    },

    // Llena el campo hora con la hora actual
    fillHora: function(noreemp) {
        var theForm = Fechas.objFormFid;
        if (typeof(theForm._HORAP) !== 'undefined') {
            if (theForm._HORAP.value === '') {
                var date = new Date();
                var hora = '' + date.getHours();
                var min = '' + date.getMinutes();
                if (hora.length < 2) { hora = '0' + hora; }
                if (min.length < 2) { min = '0' + min; }
                theForm._HORAP.value = hora + ':' + min;
            }
        }

        if (typeof(theForm._HORAE) !== 'undefined') {
            if (theForm._FECHAE.value === '' || theForm._FECHAE.value == '99999999') {
                theForm._HORAE.value = '';
            }
        }
    }
};

