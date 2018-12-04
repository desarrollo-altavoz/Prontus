/**
 * ProntusLangController
 * @author INC
 */
var ProntusLangController = (function(window, undefined) {
    var UNDEFINED_LANG_FILE = 'Language file has not been defined.';
    var ID_NOT_FOUND = "ID not found in Lang File: ";
    var debug = false;

    function replaceTemplate(template, params) {
        for(var k in params) {
            if(params.hasOwnProperty(k)) {
                var rx = new RegExp('__'+k+'__');
                if(template.search(rx) >= 0) {
                    template = template.replace('__'+k+'__', params[k]);
                }
            }
        }

        return template;
    };

    function setDebug(debug) {
        this.debug = debug;
    }

    function getString(id, params) {
        if(typeof ProntusLang === "undefined") {
            return UNDEFINED_LANG_FILE;
        }

        if(id in ProntusLang.strings) {
            if(typeof params !== "undefined") {
                return replaceTemplate(ProntusLang.strings[id], params);
            }
            return ProntusLang.strings[id];
        } else {
            if(debug) {
                console.log(ID_NOT_FOUND + id);
            }
            return ProntusLang.RESOURCE_NOT_FOUND;
        }
    }

    function applyLang() {

    }

    return {
        getString: getString,
        setDebug: setDebug
    };

})(window);
