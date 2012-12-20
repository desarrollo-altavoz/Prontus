/**
 * Clase de validacion de formularios
 *
 * @author shoto
 * @version 5.00.00
 */


 /**
 * @class Validador
 * clase de validacion de formularios
 */
function Validador(formname, mode, color){
   this.fname = formname;
   if((mode != 'one') && (mode != 'acum')){
     alert('mode not valid in Validator constructor');
     return null;
   };
   this.mode = mode;
   this.debug = false;
   this.debugElemID = 'debugConsole';
   if(color == ''){ color = 'ffb900'; };
   this.bgcolor = color;
   this.validations = new Array;
};

/**
 * activa o desactiva la capacidad de debug de la clase Validador
 * @param boolean status
 */
Validador.prototype.setDebug = function(status){
  if(!this.fname){
    alert('Validator object not found');
    return;
  };
  this.debug = status;
  return true;
};

/**
 * agrega informacion a la capa de debug
 * @param string msg texto a agregar a la capa de debug
 */
Validador.prototype.addDebug = function(msg){
  if(!this.debug){
      return false;
  }
  if(!this.fname){
    alert('Validator object not found');
    return;
  };
  var objDebug =  document.getElementById(this.debugElemID);
  if (objDebug) {
      objDebug.innerHTML += msg + '<br/>';
  }
  return true;
};


/**
 * Agrega una validacion al objeto validador
 * @param {Object} control  nombre de control
 * @param {Object} fvalidation  nombre de validacion
 * @param {Object} fargs    argumentos de validacion
 * @param {Object} errmsg  mensaje de error asociado
 */
Validador.prototype.addconstraint = function(control,fvalidation,fargs,errmsg){
  if(!this.fname){
    alert('Validator object not found');
    return;
  };
  this.validations.push(new Constraint(control,fvalidation,fargs,errmsg));
  return true;
};

/**
 * Elimina una validaciÛn asociada al objeto validador
 * @param {Object} control   control asociado
 * @param {Object} fvalidation nombre de validacion
 */
Validador.prototype.delconstraint = function(control,fvalidation){
  if(!this.fname){
     alert('Validator object not found');
     return;
  };
  var erase = 0;
  for(validacion = 0; validacion < this.validations.length; validacion++){
    if ((this.validations[validacion].field == control) && (this.validations[validacion].tipo == fvalidation)){
       this.validations[validacion].field = '';
       this.validations[validacion].tipo = '';
       this.validations[validacion].args = '';
       this.validations[validacion].msg = '';
       erase++;
    };
  };
  if(erase != 0){
    return false;
  };
  return true;
};

/**
 * funcion que recibe estructura de datos de validaciones y las aplica
 * devuelve verdadero(si formulario completo valida) o falso(si al menos alguna
 * validacion falla)
 * @return true o false
 */
Validador.prototype.validar = function(){

  var validacion = 0;
  var strerr = '';
  var obj_elem = '';
  // loop de validaciones agregadas a la instancia
    for(validacion = 0; validacion < this.validations.length; validacion++){
      if(this.validations[validacion].field == ''){
         // validacion invalida se excluye
         this.addDebug('validation['+validacion+'] ignored , attribute field empty.');
         continue;
      };
      var objForm   = this._getFormObj(this.fname);

      if(! objForm){
         this.addDebug('Form ['+this.fname+'] not found');
         alert('Form ['+this.fname+'] not found');
         return false
      };
      var elem = this.validations[validacion].field;
      if(!objForm.elements[elem]){
          this.addDebug('Field Form ['+this.validations[validacion].field+'] not found, assumes string ');
          obj_elem = elem;
      }else{
          obj_elem = objForm.elements[elem];
      };
      // Evaluacion de validacion
      this.addDebug(this.validations[validacion].tipo+'('+obj_elem.name+','+this.validations[validacion].args+')');
      var instanceValidation = new Validation();
      try{
         var result = eval('instanceValidation.'+this.validations[validacion].tipo+'(obj_elem,this.validations[validacion].args)');
      }catch(e){
          this.addDebug('[lib_validator]Error: '+e);
          alert('[lib_validator]Error: '+e)
      }
      if(!result){
          if(this.mode == 'acum'){
              strerr = strerr + ' ' +this.validations[validacion].msg+"\n";
              this.addDebug(this.validations[validacion].msg.constructor.toString());
              this._change_color(obj_elem, this.bgcolor);
          }else{
              this._executeAction(this.validations[validacion].msg);
              this._change_color(obj_elem, this.bgcolor);
              if (!this._isString(obj_elem)) {
                  if (obj_elem.type) {
                      obj_elem.focus();
                  } else {
                      obj_elem[0].focus();
                  };
              }
              return false;
          };
       }else{
           this._executeRedoAction(this.validations[validacion].msg);
           this._change_color(obj_elem, '');
       };
  };
  if((this.mode == 'acum') && (strerr != '')){
    alert(strerr);
    return false;
  };
  return true;
};




/**
 * hace submit de formulario asociado
 * @todo cambiar compatible con xhtml form con id
 */
Validador.prototype.send = function(){
    if(! document.forms[this.fname]){
         alert('Form ['+this.fname+'] not found');
         return false
    };
    document.forms[this.fname].submit();
}


/**
 * @class Constraint
 * base para estructura de datos, objeto tipo constraint
 * @param nom nombre de elemento de formulario
 * @param tipo tipo de validacion
 * @param fargs argumentos para funcion de validacion
 * @param  msg mensaje en caso de error
 * @return true o false
 */
function Constraint(nom,tipo,fargs,msg){
    this.field = nom;
    this.tipo = tipo;
    this.args = fargs;
    this.msg = msg;
};


 /*
  * Metodos de validacion
  *
  */

 /**
  * @class Validation
  * agrupa metodos de validacion
  */
function Validation(){ }


 /**
 * Funcion que valida la obligatoriedad de contenido
 * @param control objeto elemento de formulario
 * @param args null
 * @return true o false
 */
Validation.prototype.obligatorio = function(control,args){
  var dato = '';
  // alert(control+'::'+typeof(control)); // DEBUG
  if(typeof(control) != 'string'){
    if(control.type){
      // alert(control.type); // debug
      if ((control.type == 'text') || (control.type == 'textarea') || (control.type == 'file') || (control.type == 'password') || (control.type == 'hidden')){
        dato = control.value;
      }else if (control.type == 'select-one'){
        dato = control.options[control.selectedIndex].value;
      }else if (control.type == 'select-multiple'){ // ycc
        // concatena todos los values seleccionados en 'dato'
        var i;
        for (i = 0; i < control.length; i++) {
          if (control.options[i].selected) {
            dato = dato + control.options[i].value;
          };
        };

      }else if(control.type == 'checkbox'){
         if(control.checked){
           dato = 1;
         };
      }else if(control.type == 'radio'){
         if(control.checked){
           dato = 1;
         };
       };
    }else{
       if(control[0].type == 'radio'){
         var i = 0;
         for(i=0;i<control.length;i++){
           if(control[i].checked){
             dato = 1;
           };
         };
      }else{
        alert('Obligatorio: validation dont work with type of field form.');
        return;
      };
    };
  }else{
    dato = control;
  };
  if (dato == ''){
    return false;
  }else{
    return true;
  };
};

/**
 * Funcion que valida una direccion de e-mail
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args null
 * @return true o false
 */
Validation.prototype.email = function(control,args){
  var dato;
  if(typeof(control) != 'string'){
    if ((control.type == 'text') || (control.type == 'password') || (control.type == 'hidden')){
       dato = control.value;
    }else if (control.type == 'select-one'){
       dato = control.options[control.selectedIndex].value;
    }else{
      alert('Email: validation dont work with type of field form.');
      return;
    };
  }else{
    dato = control;
  };
  if(dato != ''){
    var expr = /^[a-zA-Z][a-zA-Z\_\-\.0-9]+@[a-zA-Z\-\.0-9]+\.[a-zA-Z]{2,4}$/;
    var found = expr.exec(dato);
    if (! found){
      return false;
    }else{
      return true;
    };
  }else{
    return true;
  };
};

/**
 * Funcion que valida que el archivo asociado a un control file este
 * en un conjunto de extensiones permitidas
 * @param control objeto elemento de formulario
 * @param args arreglo de extensiones
 * @return true o false
 */
Validation.prototype.checkTipoArchivo =  function(control,args){
  var dato = '';
  if(typeof(control) != 'string'){
    if(control.type){
      if (control.type == 'file'){
        dato = control.value;
      }else{
        alert('checkTipoArchivo: validation dont work with type of field form.');
        return;
      };
    };
  }else{
    dato = control;
  };
  if (dato != ''){
    var ext = getExtension(dato);
    for (extPer in args) {
        if (ext == args[extPer]) {
            return true;
        }
    }
    return false;
  }else{
    return true;
  };
};


/**
 * Funcion para validar un numero entre un rango determinado
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args rango n,m
 * @return true o false
 */
Validation.prototype.rango = function(control, param){
  var args = new Array;
  args = param.split(",");
  var number;
  if(typeof(control) != 'string'){
    if ((control.type == 'text') || (control.type == 'password') || (control.type == 'hidden')){
       number = control.value;
    }else if (control.type == 'select-one'){
       number = control.options[control.selectedIndex].value;
    }else{
      alert('Rango: validation dont work with type of field form.');
      return;
    };
  }else{
    number = control;
  };
  if(number != ''){
    var num = parseFloat(number);
    if(isNaN(num)){
      return false;
    };
    if ((args[0] != '') && (args[1] != '')){
      if ((num >= parseFloat(args[0])) && (num <= parseFloat(args[1]))){
        return true;
      }else{
        return false;
      };
    }else if((args[0] == '') && (args[1] != '')){
      if (num <= parseFloat(args[1])){
        return true;
      }else{
        return false;
      };
    }else if((args[0] != '') && (args[1] == '')){
       if (num >= parseFloat(args[0])){
         return true;
       }else{
         return false;
       };
    };
  }else{
    return true;
  };
};


/**
 * Funcion que valida solo alfabeto, no verifica obligatoriedad
 *
 * @param control objeto elemento de formulario
 * @param args null
 * @return true o false
 */
Validation.prototype.alpha = function(control,args){
  var dato;
  if(typeof(control) != 'string'){
    if ((control.type == 'text') ||  (control.type == 'password') || (control.type == 'hidden')){
       dato = control.value;
    }else if (control.type == 'select-one'){
       dato = control.options[control.selectedIndex].value;
    }else{
      alert('alpha: validation dont work with type of field form.');
      return;
    };
  }else{
    dato = control;
  };
  if (dato != ''){
    var expr = /[^a-zA-ZÒ—·ÈÌÛ˙‰ÎÔˆ¸¡…Õ”⁄ƒÀœ÷‹]/;
    if (dato.match(expr)){
      return false;
    }else{
      return true;
    };
  }else{
    return true;
  };
};

/**
 * Funcion que valida alphabeto y numeros
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args null
 * @return true o false
 */
Validation.prototype.alphanum = function(control,args){
  var dato;
  if(typeof(control) != 'string'){
    if ((control.type == 'text') || (control.type == 'password') || (control.type == 'hidden')){
       dato = control.value;
    }else if (control.type == 'select-one'){
       dato = control.options[control.selectedIndex].value;
    }else{
      alert('alphanum: validation dont work with this type of field form.');
      return;
    };
  }else{
    dato = control;
  };
  if (dato != ''){
    var expr = /[^0-9a-zA-ZÒ—·ÈÌÛ˙‰ÎÔˆ¸¡…Õ”⁄ƒÀœ÷‹]/;
    if (dato.match(expr)){
      return false;
    }else{
      return true;
    };
  }else{
    return true;
  };
};

/**
 * Funcion que valida TEXTO
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args null
 * @return true o false
 */
Validation.prototype.texto  = function(control,args){
  var dato;
  if(typeof(control) != 'string'){
    if ((control.type == 'text') ||  (control.type == 'password') || (control.type == 'hidden')){
       dato = control.value;
    }else if (control.type == 'select-one'){
       dato = control.options[control.selectedIndex].value;
    }else{
      alert('texto: validation dont work with this type of field form.');
      return;
    };
  }else{
    dato = control;
  };
  if (dato != ''){
  var expr = /[^0-9a-zA-ZÒ—·ÈÌÛ˙‰ÎÔˆ¸¡…Õ”⁄ƒÀœ÷‹\-\'\.\ ]/;
    if (dato.match(expr)){
      return false;
    }else{
      return true;
    };
  }else{
    return true;
  };
};

/**
 * Funcion que valida numero
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args null
 * @return true o false
 */
Validation.prototype.numero =  function(control,args){
  var dato;
  if(typeof(control) != 'string'){
    if ((control.type == 'text') || (control.type == 'password') || (control.type == 'hidden')){
       dato = control.value;
    }else if (control.type == 'select-one'){
       dato = control.options[control.selectedIndex].value;
    }else{
      alert('numero: validation dont work with type of field form.');
      return;
    };
  }else{
    dato = control;
  };
  if (dato != ''){
    if(args == ''){
      var expr = /^[0-9]+$/;
      dato = dato.replace(/\./g,'');
      var found = expr.exec(dato);
      if (! found){
        return false;
      }else{
        return true;
      };
    }else{
      var params = args.split(',');
      // params 0=parte entera , 1=decimal  ,2=separador(punto o coma)
      if(params[2] == ''){params[2] = ',';};
      var numero = dato.split(params[2]);
      numero[0] = numero[0].replace(/\./g,'');
      if(params.length != 3){
        alert('numero: number of parameters not valid.');
        return false;
      };
      if ((isNaN(parseInt(params[0]))) || (isNaN(parseInt(params[1])))){
        alert('numero: not valid parameters.');
        return false;
      };
     if(numero.length == '1'){
         var expr = /^[0-9]+$/;
         var found = expr.exec(numero[0]);
        if (! found){
          return false;
        };
        if(numero[0].length <= parseInt(params[0])){
          return true;
        }else{
          return false;
        };
     }else{
         var expr = /^[0-9]+$/;
         var found0 = expr.exec(numero[0]);
         var found1 = expr.exec(numero[1]);
        if ((!found0) || (!found1)){
          return false;
        };
        if((numero[0].length <= parseInt(params[0])) && (numero[1].length <= parseInt(params[1]))){
          return true;
        }else{
          return false;
        };
     };
    };
  }else{
    return true;
  };
};


/**
 * Funcion que restringe la cantidad maxima de caracteres permitidos.
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args numero maximo de caracteres
 * @return true o false
 */
Validation.prototype.cmaximo = function(control,args){
  var dato;
  if(typeof(control) != 'string'){
    if ((control.type == 'text') || (control.type == 'password') || (control.type == 'hidden') || (control.type == 'textarea')){
       dato = control.value;
    }else if (control.type == 'select-one'){
       dato = control.options[control.selectedIndex].value;
    }else{
      alert('cmaximo: validation dont work with type of field form.');
      return;
    };
  }else{
    dato = control;
  };
  if (dato != ''){
    var cant = parseInt(args);
    if(isNaN(cant)){
      alert('cmaximo: parameter is not valid.');
      return false;
    };
    if (dato.length > cant){
      return false;
    }else{
      return true;
    };
  }else{
    return true;
  };
};

/**
 * Funcion que restringe la cantidad minima de caracteres permitidos.
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args numero minimo de caracteres
 * @return true o false
 */
Validation.prototype.cminimo = function(control,args){
  var dato;
  if(typeof(control) != 'string'){
    if ((control.type == 'text') ||  (control.type == 'password') || (control.type == 'hidden') || (control.type == 'textarea')){
       dato = control.value;
    }else if (control.type == 'select-one'){
       dato = control.options[control.selectedIndex].value;
    }else{
      alert('cminimo: validation dont work with type of field form.');
      return;
    };
  }else{
    dato = control;
  };
  if (dato != ''){
    var cant = parseInt(args);
    if(isNaN(cant)){
      alert('cminimo: parameter is not valid.');
      return false;
    };
    if (dato.length < cant){
      return false;
    }else{
      return true;
    };
  }else{
    return true;
  };
};

/**
 * Funcion que valida el cumplimiento del valor sobre una exprecion regular definida
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args objeto RegExp
 * @return true o false
 * @version 2.00
 */
Validation.prototype.regex = function(control,args){
  var dato;
  if(typeof(control) != 'string'){
    if ((control.type == 'text') || (control.type == 'textarea') || (control.type == 'file') || (control.type == 'password') || (control.type == 'hidden')){
       dato = control.value;
    }else if (control.type == 'select-one'){
       dato = control.options[control.selectedIndex].value;
    }else{
      alert('regex: validation dont work with this type of field form.');
      return;
    };
  }else{
    dato = control;
  };
  if (dato != ''){
   try{
      var expr = args; // 4.02
    }catch(e){
       alert('[lib_validator]Error: '+e)
    }
    if (dato.match(expr)){
      return true;
    }else{
      return false;
    };
  }else{
    return true;
  };
};

/**
 * Funcion que valida que fecha sea valida
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args null
 * @return true o false
 * @version 2.03
 */
Validation.prototype.fecha = function(control,args){
  var dato;
  if(typeof(control) != 'string'){
    if ((control.type == 'text') || (control.type == 'textarea') || (control.type == 'file') || (control.type == 'password') || (control.type == 'hidden')){
       dato = control.value;
    }else if (control.type == 'select-one'){
       dato = control.options[control.selectedIndex].value;
    }else{
      alert('fecha: validation dont work with this type of field form.');
      return;
    };
  }else{
    dato = control;
  };
  if (dato != ''){
  var reg = '';
  var mifecha2 = '';
     if(args == ''){
       reg = /(\d\d)\/(\d\d)\/(\d\d\d\d)$/i;
       mifecha2 = dato.replace(reg,"$3/$2/$1");
    }else{
      // Este trozo esta a prueba ya que la idea es que maneje multiples formatos.
      // Lo hare cuando tenga mÔøΩs tiempo.
      try{
         reg = eval(args);
      }catch(e){
        alert('[lib_validator]Error: '+e)
      }
       mifecha2 = dato.replace(reg,"$3/$2/$1");
    };
    var mifecha = new Date(mifecha2);
    var dia = new String(mifecha.getDate());
    if(dia.length == 1) dia = '0'+dia;
    var mes = new String(mifecha.getMonth() + 1);
    if(mes.length == 1) mes = '0'+mes;
    var anio = new String(mifecha.getFullYear());
    var newfecha = dia+'/'+mes+'/'+anio;
    if (dato != newfecha) {
      return false;
    }else{
      return true;
    };
  }else{
    return true;
  };
};



/**
 * Funcion que valida que un valor no sea selecionado
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args valor no permitido
 * @return true o false
 */
Validation.prototype.dontselect = function(control,args){
  var dato;
  if(typeof(control) != 'string'){
    if (control.type == 'select-one'){
       dato = control.options[control.selectedIndex].value;
    }else{
      alert('dontselect: validation dont work with type of field form.');
      return;
    };
  }else{
    dato = control;
  };
  if(dato != ''){
	if (dato == args){
      return false;
    }else{
      return true;
    };
  }else{
    return true;
  };
};

/**
 * Funcion que valida un RUT segun el algoritmo
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args null
 * @return true o false
 */
Validation.prototype.rut = function(control,args){
  var dato;
  if(typeof(control) != 'string'){
    if ((control.type == 'text') ||  (control.type == 'password') || (control.type == 'hidden')){
       dato = control.value;
    }else if (control.type == 'select-one'){
       dato = control.options[control.selectedIndex].value;
    }else{
      alert('cmaximo: validation dont work with type of field form.');
      return;
    };
  }else{
    dato = control;
  };
  if (dato != ''){
      if (!validate_rut(dato)){
        return false;
      }else{
        return true;
      };
  }else{
    return true;
  };
};


/**
 * Funcion que valida si contenido es valor
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args valor
 * @return true o false
 */
Validation.prototype.is = function(control,args){
  var dato = '';
  if(typeof(control) != 'string'){
    if(control.type){
      if ((control.type == 'text') || (control.type == 'textarea') || (control.type == 'file') || (control.type == 'password') || (control.type == 'hidden')){
        dato = control.value;
      }else if (control.type == 'select-one'){
        dato = control.options[control.selectedIndex].value;
      }else if(control.type == 'checkbox'){
         if(control.checked){
           dato = 1;
         };
      };
    }else{
       if(control[0].type == 'radio'){
         var i = 0;
         for(i=0;i<control.length;i++){
           if(control[i].checked){
             dato = 1;
           };
         };
      }else{
        alert('is: validation dont work with type of field form.');
        return;
      };
    };
  }else{
    dato = control;
  };
  if (dato != args){
      return false;
    }else{
      return true;
    };
};

/**
 * Funcion que valida que el contenido no es valor
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args valor
 * @return true o false
 */
Validation.prototype.notIs = function(control,args){
  var dato = '';
  if(typeof(control) != 'string'){
    if(control.type){
      if ((control.type == 'text') || (control.type == 'textarea') || (control.type == 'file') || (control.type == 'password') || (control.type == 'hidden')){
        dato = control.value;
      }else if (control.type == 'select-one'){
        dato = control.options[control.selectedIndex].value;
      }else if(control.type == 'checkbox'){
         if(control.checked){
           dato = 1;
         };
      };
    }else{
       if(control[0].type == 'radio'){
         var i = 0;
         for(i=0;i<control.length;i++){
           if(control[i].checked){
             dato = 1;
           };
         };
      }else{
        alert('notIs: validation dont work with type of field form.');
        return;
      };
    };
  }else{
    dato = control;
  };
  if (dato == args){
      return false;
    }else{
      return true;
    };
};

/**
 * Funcion que valida si es url, el valor asociado al control tiene formato de URL
 * no verifica obligatoriedad
 * @param control objeto elemento de formulario
 * @param args null
 * @return true o false
 */
Validation.prototype.url = function(control,args){
  var dato;
  if ((control.type == 'text') || (control.type == 'password') || (control.type == 'hidden')){
     dato = control.value;
  }else if (control.type == 'select-one'){
     dato = control.options[control.selectedIndex].value;
  }else{
    alert('URL: validation dont work with type of field form.');
    return;
  };
  if(dato != ''){
    var expr = /^https?:\/\/[a-zA-Z\-\_\.0-9\/]+$/;
    var found = expr.exec(dato);
    if (! found){
      return false;
    }else{
      return true;
    };
  }else{
    return true;
  };
};

 /*
  * Metodos privados utilitarios de validacion
  *
  */

 /**
 * Funcion que valida un rut
 * @param crut rut en cualquier formato
 * @return true o false
 */
Validador.prototype._validate_rut = function(crut) {
  var tmpstr = "";
  var i, largo, dv, rut, dv, suma, mul, res, dvi;

  for ( i=0; i < crut.length ; i++ ) {
    if ( crut.charAt(i) != ' ' && crut.charAt(i) != '.' && crut.charAt(i) != ',' && crut.charAt(i) != '-' ) {
      tmpstr = tmpstr + crut.charAt(i);
    };
  };
  crut = tmpstr;
  largo = crut.length;
  if ( largo < 2 ) {
    return false;
  };
  if ( largo > 2 ) {
    rut = crut.substring(0, largo - 1);
  }
  else {
    rut = crut.charAt(0);
  };
  dv = crut.charAt(largo-1);
  checkCDV( dv );
  if ( rut == null || dv == null ) {
    return false;
  };
  var dvr = '0';
  suma = 0;
  mul  = 2;
  for (i= rut.length -1 ; i >= 0; i--) {
    suma = suma + rut.charAt(i) * mul;
    if (mul == 7) {
      mul = 2;
    }
    else {
      mul++;
    };
  };
  res = suma % 11;
  if (res==1) {
    dvr = 'k';
  }
  else if (res==0) {
    dvr = '0';
  }
  else {
    dvi = 11-res;
    dvr = dvi + "";
  };

  if (dvr != dv.toLowerCase()) {
    return false;
  };
  return true;
};

/**
 * Verifica el DV del un rut asociado
 * @param dvr digito verficador
 */
Validador.prototype._checkCDV = function(dvr) {
  var dv = dvr + "";
  if ( dv != '0' && dv != '1' && dv != '2' && dv != '3' && dv != '4' && dv != '5' && dv != '6' && dv != '7' && dv != '8' && dv != '9' && dv != 'k'  && dv != 'K') {
    return false;
  };
  return true;
};

/**
 * Path de archivo
 * @param {Object} filePath
 */
Validador.prototype._getExtension = function(filePath){
    var ext = '';
    try{
        var patron = new RegExp("\.([^.]+)$");
        var res = patron.exec(filePath)
        ext = res[1];
    }catch(e){};
    return ext;
}

/**
 * Obtiene obj formulario asociado al nombre
 * @param {Object} filePath
 */
Validador.prototype._getFormObj = function(formId){
    var objForm = null;
    try{
        objForm = document.getElementById(formId);
        if(!objForm){
            objForm =  document.forms[formId];
        }
    }catch(e){};
    return objForm;
}

/**
 * Cambia el color de fondo de un objeto
 * @param obj objeto a modificar
 * @param color codigo de color a modificar
 */
Validador.prototype._change_color = function(obj, color){
    if(obj.style){
      obj.style.backgroundColor = color;
    };
};


/**
 * Verifica si el parametro es un arreglo
 * @param {Object} obj
 */
Validador.prototype._isArray = function(obj) {
   if (obj.constructor.toString().indexOf("Array") == -1)
      return false;
   else
      return true;
}

/**
 * Verifica si el parametro es un objeto String
 * @param {Object} obj
 */
Validador.prototype._isString = function(obj) {
   if (obj.constructor.toString().indexOf("String") == -1)
      return false;
   else
      return true;
}

/**
 * Executa la accion asociada a la validacion seg˙n el tipo de objteo asociado a al accion
 * @param {Object} actionObj
 */
Validador.prototype._executeAction = function(actionObj) {
   this.addDebug(actionObj.constructor.toString());
   try{
       if(this._isArray(actionObj)){
           for(var mObj in actionObj){
               actionObj[mObj].performAction();
           }
       }else{
           actionObj.performAction();
       }
   }catch(e){
      this.addDebug('_executeAction: performAction error'+e);
      alert(actionObj);
   }
}

/**
 * Executa la accion REdo asociada a la validacion seg˙n el tipo de objteo asociado a al accion
 * osea aquella que indica que la validacion es exitosa es v·lido
 * @param {Object} actionObj
 */
Validador.prototype._executeRedoAction = function(actionObj) {
   this.addDebug(actionObj.constructor.toString());
   try{
       if(this._isArray(actionObj)){
           for(var mObj in actionObj){
               actionObj[mObj].performRedoAction();
           }
       }else{
           actionObj.performRedoAction();
       }
   }catch(e){
      this.addDebug('_executeRedoAction: performRedoAction error'+e);
   }
}


String.prototype.performAction = function(){
    alert(this);
}
