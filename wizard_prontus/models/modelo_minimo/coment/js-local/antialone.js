// Funciones para redireccionar páginas sueltas de comentarios a su contexto dentro del articulo.

function _antialone_redirToArtic(dir_prontus, _antialone_token) {
    var url = document.URL;
    var ts_artic = url.substr(url.indexOf(_antialone_token) + _antialone_token.length, 14);
    var currpage = url.substring(url.indexOf(ts_artic) + 14 + 1, url.length - 5); // 14 + 1 -> artic mas el slash, -5 -> la extension mas el punto
    var fecha = ts_artic.substr(0, 8);
    var ext_artic = url.substring(url.indexOf(ts_artic + '.'), url.length);
    var pag_artic = window.location.protocol + '//' + document.domain + dir_prontus + '/site/artic/' + fecha + '/pags/' + ts_artic + ext_artic;
    document.write('<p style="font-family:Tahoma; font-size:11px; font-weight:bold">Redireccionando en 3 segs a versión completa...<br>Si lo anterior no funciona, haga click <a href="' + pag_artic + '?comentpage=' + currpage + '&ts_artic=' + ts_artic + '">aqu&iacute;</a></p>');
    var aux = setTimeout("redir('" + pag_artic + "', " + currpage + ", " + ts_artic + ")", 3000);
};

function redir(pag_artic, currpage, ts_artic) {
    window.location.href = pag_artic + '?comentpage=' + currpage + '&ts_artic=' + ts_artic;
};

function _antialone_posicionaPagComent(_antialone_token) {
    var url = document.URL;
    var coment_page;
    if (url.indexOf('comentpage=') > 0) {
        var numpag = url.substring(url.indexOf('comentpage=') + 11, url.indexOf('&ts_artic='));
        var ts_artic = url.substr(url.indexOf('&ts_artic=') + 10, 14);
        if (url.indexOf(ts_artic) <= 0) return;
        var ext_artic = url.substring(url.indexOf(ts_artic + '.'), url.length);
        coment_page = _antialone_token + ts_artic + '/' + numpag + ext_artic;
        recarga_coment(coment_page); // from ajax_send
    }
};
