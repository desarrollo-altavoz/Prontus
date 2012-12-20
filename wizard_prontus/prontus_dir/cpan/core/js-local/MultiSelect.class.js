function MultiSelect(iddest, idsrc) {

    this.iddest = iddest;
    this.destList = $('#'+iddest);
    this.idsrc = idsrc;
    this.srcList = $('#'+idsrc);

    // Agrega
    this.srcToDest = function() {
        if(this.idsrc === '') {
            return;
        }
        this.destList.children('option').attr('selected', '');
        this.destList.append(this.srcList.children('option:selected'));
        this.destList.children('option[value=""]').remove();
        this.sortCombos(this.destList);
    };

    // Agrega Todos
    this.srcToDestAll = function() {
        if(this.idsrc === '') {
            return;
        }
        this.destList.children('option').attr('selected', '');
        this.destList.append(this.srcList.children('option'));
        this.destList.children('option[value=""]').remove();
        this.sortCombos(this.destList);
    };

    // Elimina
    this.destToSrc = function() {
        if(this.idsrc === '') {
            return;
        }
        this.srcList.children('option').attr('selected', '');
        this.srcList.append(this.destList.children('option:selected'));
        this.srcList.children('option[value=""]').remove();
        this.sortCombos(this.srcList);
    };

    // Elimina Todos
    this.destToSrcAll = function() {
        if(this.idsrc === '') {
            return;
        }
        this.srcList.children('option').attr('selected', '');
        this.srcList.append(this.destList.children('option'));
        this.srcList.children('option[value=""]').remove();
        this.sortCombos(this.srcList);
    };

    // Ordena uno de los Select
    this.sortCombos = function(obj) {
        if(this.idsrc ==='') {
            return;
        }
        obj.find('option').sort("title", "asc").appendTo(obj);
    };

    // Selecciona todos los Elementos
    this.selectDestAll = function() {
        this.destList.children('option').attr('selected', 'selected');
    };

    // Realiza tareas de limipieza y seleccion al momento de submitir
    this.procesarGuardado = function() {
        this.destList.children('option[value=""]').remove();
        this.selectDestAll();
    };

    // Setea la fuente actual
    this.setFuente = function (tipo) {

        if(tipo === '') {
            this.idsrc = '';
            this.srcList = '';
        } else {
            this.idsrc = 'lstChanDisp_'+tipo;
            this.srcList = $('#'+this.idsrc);
        }
    };
}
