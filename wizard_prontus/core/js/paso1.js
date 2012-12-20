function check_install() {

    var expr = /^[a-z][a-z0-9\_\-]+$/;
    var found = expr.exec(window.document.form1.PRONTUS_ID.value);
    if (! found) {
        alert('Nombre de publicador no válido. Debe comenzar con letra minúscula sin tilde y seguirle letras del mismo tipo o números, guión o underscore.');
        window.document.form1.PRONTUS_ID.focus();
        window.document.form1.PRONTUS_ID.select();
        return false;
    };
    // se llama con accion=1 para q solo haga el chequeo de escritura
    var urlcheck = '/' + DIR_CGI_CPAN + '/prontus_check_install.cgi?wizard=1&accion=1&_prontus_id=' + window.document.form1.PRONTUS_ID.value;
    $.fn.colorbox({open:true, href: urlcheck, width:'750px', height:'550px'});
};

// -----------------------------------------------------------------
function valida_campos() {
    var expr;
    var found;
    var vprontus;

    expr = /^[a-z][a-z0-9\_\-]+$/;
    found = expr.exec(window.document.form1.PRONTUS_ID.value);
    if (! found) {
        alert('Nombre de publicador no válido. Debe comenzar con letra minúscula sin tilde y seguirle letras del mismo tipo o números, guión o underscore.');
        window.document.form1.PRONTUS_ID.focus();
        window.document.form1.PRONTUS_ID.select();
        return false;
    };

    // smtp
    if (window.document.forms[0].PRONTUS_SMTP.value != "") {
        var expr = /^[A-Z\.a-z\_\-0-9]+$/;
        var found = expr.exec(window.document.forms[0].PRONTUS_SMTP.value);
        if (! found) {
            alert('Servidor SMTP no válido.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, punto, guión y underscore.');
            window.document.forms[0].PRONTUS_SMTP.focus();
            window.document.forms[0].PRONTUS_SMTP.select();
            return false;
        };
    };

    /*
    NOM_BD
    USER_BD
    PWD_BD
    SERVER_BD
    */
    expr = /^[\w\-\.]{1,128}$/;
    var found = expr.exec(window.document.forms[0].SERVER_BD.value);
    if (! found) {
        alert('Servidor de BD no es válido.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, punto, guión y underscore, máximo 128.');
        window.document.forms[0].SERVER_BD.focus();
        window.document.forms[0].SERVER_BD.select();
        return false;
    };

    var expr_mysql;
    expr_mysql = /^[\w\-]{1,64}$/;
    found = expr_mysql.exec(window.document.form1.NOM_BD.value);
    if (! found) {
        alert('Nombre de BD no es válido.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, guión y underscore, máximo 64.');
        window.document.form1.NOM_BD.focus();
        window.document.form1.NOM_BD.select();
        return false;
    };

    expr_mysql = /^[\w\-]{1,16}$/;
    found = expr_mysql.exec(window.document.form1.USER_BD.value);
    if (! found) {
        alert('Usuario de BD no es válido.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, guión y underscore, máximo 16.');
        window.document.form1.USER_BD.focus();
        window.document.form1.USER_BD.select();
        return false;
    };

    expr_mysql = /^[\w\-\.\@\:\$%!]{1,16}$/;
    found = expr_mysql.exec(window.document.form1.PWD_BD.value);
    if (! found) {
        alert('Contraseña para usuario de BD no es válida.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, y los caracteres ., _, -, @, $, % y !, máximo 16.');
        window.document.form1.PWD_BD.focus();
        window.document.form1.PWD_BD.select();
        return false;
    };

    /* para creacion BD */
    if (window.document.forms[0].SUPERUSER_BD.value != "") {
        expr_mysql = /^[\w\-]{1,16}$/;
        found = expr_mysql.exec(window.document.form1.SUPERUSER_BD.value);
        if (! found) {
            alert('Usuario para creación de BD no es válido.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, guión y underscore, máximo 16.');
            window.document.form1.SUPERUSER_BD.focus();
            window.document.form1.SUPERUSER_BD.select();
            return false;
        };
    };

    if (window.document.forms[0].SUPERPWD_BD.value != "") {
        expr_mysql = /^[\w\-\.\@\:\$%!]{1,16}$/;
        found = expr_mysql.exec(window.document.form1.SUPERPWD_BD.value);
        if (! found) {
            alert('Contraseña para creación de BD no es válida.\nCaracteres permitidos:letras minúsculas o mayúsculas, dígitos, guión y underscore, máximo 16.');
            window.document.form1.SUPERPWD_BD.focus();
            window.document.form1.SUPERPWD_BD.select();
            return false;
        };
    };


    return true;
};

// -----------------------------------------------------------------
function get_oct_dig(caracter) {
    caracter = caracter.toUpperCase();
    if (caracter == 'Y') {
        return 1;
    }
    if (caracter == 'X') {
        return 2;
    }
    if (caracter == 'W') {
        return 3;
    }
    if (caracter == 'A') {
        return 4;
    }

    return '0';

};

// -----------------------------------------------------------------
