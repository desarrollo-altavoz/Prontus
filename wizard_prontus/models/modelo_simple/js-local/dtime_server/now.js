/**
Funciones de fecha y hora en tiempo real.
09/03/2007 - ALD - 1.1 - Genera ajuste automatico de hora de acuerdo a Decretos Supremos del Ministerio
                         del Interior 1.489 del 6 de octubre de 1970 y 1.142 del 20 de octubre de 1980
25/06/2008 - ALD - 1.2 - Usa segundos epoch en vez de Date.
                       - Reduce cantidad de funciones a las estrictamente necesarias.
28/07/2008 - ALD - 1.3 - Usa Date, corrigiendo nomenclatura del mes.
26/09/2009 - CVI - 1.4 - Se encapsula para usar Orientación a Objetos. Se hace una Solución Prontus
04/01/2010 - PRB - 1.5 - Se soluciona bug en get_fecha_min, se mostraba mes -1
*/

var oNow = {
  meses: new Array('enero','febrero','marzo','abril','mayo','junio',
                      'julio','agosto','septiembre','octubre','noviembre','diciembre'),
  dias: new Array('Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'),

  HUSO: null,
  t_inicial: null,
  offsetDate: null,

  // -----------------------------------
  // Obtiene la fecha en formato:
  // showSem=0   ->  12 de Enero de 2009
  // showSem=1   ->  Lunes 12 de enero de 2009
  get_fecha: function(showSem) {
    if(typeof showSem == 'undefined') showSem = 0;
    var fecha = new Date;
    fecha.setTime(oNow.t_inicial.getTime() + oNow.offset_now());
    var ano = fecha.getYear();
    if (ano < 200) { // onda 103, NS70
      ano = ano + 1900;
    }
    var mes = fecha.getMonth();
    var dia = fecha.getDate();
    var diasem = oNow.dias[fecha.getDay()];
    var mes = oNow.meses[mes];
    if (showSem == 1) {
      return diasem + ' ' + dia + ' de ' + mes + ' de ' + ano;
    } else {
      return dia + ' de ' + mes + ' de ' + ano;
    };
  }, // get_fecha

  // -----------------------------------
  // Obtiene la fecha:  26/06/2009  (ojo que se puede cambiar el separador)
  get_fecha_min: function(sep) {
    if(typeof sep == 'undefined') sep = '/';
    var fecha = new Date;
    fecha.setTime(oNow.t_inicial.getTime() + oNow.offset_now());
    var ano = fecha.getYear();
    if (ano < 200) { // onda 103, NS70
      ano = ano + 1900;
    }
    var mes = fecha.getMonth();
    mes = mes + 1;
    var dia = fecha.getDate();
    return oNow.w2(dia,2) + sep + oNow.w2(mes,2) + sep + ano;
  }, // get_fecha

  // -----------------------------------
  // Obtiene el día de la Semana:  Lunes
  get_fecha_wday_name: function() {
    var fecha = new Date;
    fecha.setTime(oNow.t_inicial.getTime() + oNow.offset_now());
    var diasem = oNow.dias[fecha.getDay()];
    return diasem;
  }, // get_fecha

  // -----------------------------------
  // Obtiene la Hora en formato:  20090626
  get_fecha_iso: function() {
    // Retorna la fecha del servidor en formato iso
    var fecha = new Date;
    // fecha.setTime(1000 * s_inicial + offset_now());
    fecha.setTime(oNow.t_inicial.getTime() + oNow.offset_now());
    var ano = fecha.getYear();
    if (ano < 200) { // onda 103, NS70
      ano = ano + 1900;
    };
    var mes = fecha.getMonth();
    var dia = fecha.getDate();
    var diasem = oNow.dias[fecha.getDay()];
    mes = mes + 1;
    // return diasem + ', ' + dia + ' de ' + mes + ' de ' + ano;
    return ano + oNow.w2(mes,2) + oNow.w2(dia,2);
  }, // fecha_iso

  // -----------------------------------
  // Obtiene la Hora en Formato:  01:21
  get_hora_min: function() {
    var fecha = new Date;
    var fechaGMT = new Date;
    fecha.setTime(oNow.t_inicial.getTime() + oNow.offset_now());
    fechaGMT.setTime(oNow.t_inicial.getTime() + oNow.offset_now() + oNow.HUSO * 3600000);
    var hora = fecha.getHours();
    var min = fecha.getMinutes();
    var seg = fecha.getSeconds();
    var strHora = oNow.w2(hora,2) + ':' + oNow.w2(min,2);
    return strHora
  }, // get_hora

  // -----------------------------------
  // Obtiene la Hora en Formato:  01:21:32
  get_hora: function() {
    var fecha = new Date;
    var fechaGMT = new Date;
    fecha.setTime(oNow.t_inicial.getTime() + oNow.offset_now());
    fechaGMT.setTime(oNow.t_inicial.getTime() + oNow.offset_now() + oNow.HUSO * 3600000);
    var hora = fecha.getHours();
    var min = fecha.getMinutes();
    var seg = fecha.getSeconds();
    var strHora = oNow.w2(hora,2) + ':' + oNow.w2(min,2) + ':' + oNow.w2(seg,2);
    return strHora
  }, // get_hora

  // -----------------------------------
  // Obtiene la Hora en formato:  01:21:32 (GMT 15:28:15)
  get_hora_full: function() {
    var fecha = new Date;
    var fechaGMT = new Date;
    fecha.setTime(oNow.t_inicial.getTime() + oNow.offset_now());
    fechaGMT.setTime(oNow.t_inicial.getTime() + oNow.offset_now() + oNow.HUSO * 3600000);
    var hora = fecha.getHours();
    var min = fecha.getMinutes();
    var seg = fecha.getSeconds();
    var horaGMT = fechaGMT.getHours();
    var minGMT = fechaGMT.getMinutes();
    var segGMT = fechaGMT.getSeconds();
    var strHora = oNow.w2(hora,2) + ':' + oNow.w2(min,2) + ':' + oNow.w2(seg,2) + ' (GMT '
        + oNow.w2(horaGMT,2) + ':' + oNow.w2(minGMT,2) + ':' + oNow.w2(segGMT,2) + ')';
    return strHora
  }, // get_hora

  // -----------------------------------
  offset_now: function() {
    var ahora = new Date();
    return ahora.getTime() - oNow.offsetDate.getTime();
  },

  // -----------------------------------
  segundoSabadoDe: function(mes) { // 1.1
    var fecha = new Date();
    // Detectar segundo sabado de mes.
    var sabados = 0;
    var ano = fecha.getYear(); // Ano actual.
    if(ano < 2000) ano += 1900;
    var sabado;
    for(i=1;i<=31;i++) {
      sabado = new Date(ano,mes,i,23,59,59);
      if(sabado.getDay() == 6) {
        sabados++;
        if(sabados == 2) break;
      };
    };
    fecha = new Date(ano,mes,i,20,59,59); //
    return fecha;
  }, // segundoSabadoDe

  // -----------------------------------
  // 1.1 segundo sabado de octubre - segundo sabado de marzo
  getHuso: function(fms) { // 1.2
    var sab1 = new Date;
    var sab2 = new Date;
    sab1 = oNow.segundoSabadoDe(2);
    sab2 = oNow.segundoSabadoDe(9);
    if( (fms >= sab1.getTime()) && (fms <= sab2.getTime()) ) {
      return 4;
    } else {
      return 3;
    };
  }, // getHuso

  // -----------------------------------
  // Formatea un número a n dígitos rellenando con ceros
  w2: function(num,n) {
    var a = num + '';
    while (a.length < n) {
      a = '0' + a;
    };
    return a;
  } // w2
}

// <!--#config timefmt="%s"-->
  oNow.HUSO = oNow.getHuso(1000 * <!--#echo var="DATE_GMT" -->),
// <!--#config timefmt="%Y,1%m - 101,1%d * 1 - 100,1%H * 1 - 100,1%M * 1 - 100,1%S * 1 - 100"-->
  oNow.t_inicial = new Date(<!--#echo var="DATE_LOCAL" -->),
// <!--#config timefmt="%s"-->
  oNow.offsetDate = new Date();