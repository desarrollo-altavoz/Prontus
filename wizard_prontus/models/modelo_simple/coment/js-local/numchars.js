function chars_restantes(theform) {
    var coment_obj = theform.COMENT_TEXTO;
    var div_numchars = document.getElementById('numchars');
    var chars_restantes = LIMIT_CHARS - coment_obj.value.length;

    if (chars_restantes >= 0) {
        div_numchars.innerHTML = chars_restantes + '';
    }
    else {
        div_numchars.innerHTML = '0';
        coment_obj.value = coment_obj.value.substring(0, LIMIT_CHARS);
        alert('El número máximo de caracteres permitidos es ' + LIMIT_CHARS);
    };
};
