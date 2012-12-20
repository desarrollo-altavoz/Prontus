function subwin(url, posx, posy) {
  // Llama a ventana popup

  var options = "toolbar=0,status=0,menubar=0,scrollbars=1,resizable=1,location=0,directories=0,width=450,height=480";
  win = window.open(url, 'tit', options);
  win.focus();
  win.moveTo(posx, posy);
};


var i = 0;
function enviar() {
  // if ( i == 0) {
    if (valida_campos()) {
      // i = 1;
		  // return true;
		  window.document.form1.submit();
	  };
	// }
	// else {
	//	 alert('Acción en proceso... por favor espere.');

	// };
};

