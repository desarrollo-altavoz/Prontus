// ****************************************************
// Función
scrollList=new Array();
function registraScroll(idAbajo, idArriba, div, velAbajo, velArriba) {
    if(scrollList[idAbajo]==null) scrollList[idAbajo]=new Array();
    if(scrollList[idArriba]==null) scrollList[idArriba]=new Array();
    scrollList[idAbajo].push(new Array(div, velAbajo));
    scrollList[idArriba].push(new Array(div, velArriba));
};

// window.onload=inicializar;

function getEl(elementId) {
    return document.getElementById(elementId);
};

function inicializar() {
    for(key in scrollList) {
        var elemento=getEl(key);
        // debug(key);
        // elemento.onmouseover=iniciaScroll;
        // elemento.onmouseout=detieneScroll;
        elemento.onmousedown=iniciaScroll;
        elemento.onmouseup=detieneScroll;
    };
};

function iniciaScroll() {
    scrollDivs=new Array();
    velDivs=new Array();
    for(key in scrollList[this.id]) {
        scrollDivs.push(getEl(scrollList[this.id][key][0]));
        velDivs.push(scrollList[this.id][key][1]);
    };
    identificador=setInterval('scrollNow()', 50);
};

function detieneScroll() {
    clearInterval(identificador);
};

function scrollNow() {
    // debug('scroll');
    for(key in scrollDivs) {
       var desplazamientoActual=scrollDivs[key].scrollLeft;
       var nuevoDesplazamiento=desplazamientoActual+velDivs[key];
       scrollDivs[key].scrollLeft=nuevoDesplazamiento;
    };
};

function debug(msg) {
    document.getElementById("debug").innerHTML = document.getElementById("debug").innerHTML + msg + '<br>';
};

registraScroll('flechaAbajo1','flechaArriba1','numpags1',10,-10);
// registraScroll('flechaAbajo2','flechaArriba2','numpags2',10,-10);

inicio=setTimeout('inicializar()', 50);

/* ejemplo:

<div id="flechas1">
    <span id="flechaArriba1" class="flecha">[&lt;] </span>
    <span id="flechaAbajo1" class="flecha">... [&gt;]</span>
</div>
<div class="scroll" id="numpags1">%%_HTML_NROS_PAG%%</div>

y

.coment .scroll {width:550px; height:25px; overflow:hidden; border:0px solid #000000; white-space:nowrap;}
.coment .flecha {cursor:pointer;display:inline;}
*/