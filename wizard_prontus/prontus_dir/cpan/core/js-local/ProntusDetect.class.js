var ProntusDetect = {

    getIdProntus: function() {
        var url = unescape(document.URL);
        url.match(/\/([^\/]+)\/cpan.+$/);
        var IdProntus = RegExp.$1;
        return IdProntus;
    },

    getPathConf: function() {
        var url = unescape(document.URL);
        url.match(/https?\:\/\/[^\/]+(\/.+\/cpan).+$/);
        var PathConf = RegExp.$1 + '/' + ProntusDetect.getIdProntus() + '.cfg';
        return PathConf;
    },

    // Transforma nombre del dir de Prontus en string capitalizado
    getNomProntus: function(nomDir) {
        var pos_underline = nomDir.indexOf('_');
        var nomProntus = nomDir.capitalize();
        if (pos_underline >= 0) {
            nomProntus = nomProntus.substr(0,pos_underline) + ' ' + nomProntus.substr(pos_underline + 1).capitalize();
        }
        return nomProntus;
    }
};

String.prototype.capitalize = function(){
    return this.replace(/\w+/g, function(a){
        return a.charAt(0).toUpperCase() + a.slice(1).toLowerCase();
    });
};
