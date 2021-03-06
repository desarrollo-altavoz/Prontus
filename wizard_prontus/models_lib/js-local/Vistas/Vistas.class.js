/**
Vistas.class.js
2.0.2 - 13/04/2011 - CPN - Se agrega opcion para redireccionar a una pagina luego del seteo de la cookie
**/

var Vistas={dirCgiBin:'/cgi-bin',coockiename:'vista',urlRedirect:'',change:function(lang,gotoURL){if(gotoURL!==undefined){Vistas.urlRedirect=gotoURL;}
if(lang=='es'){Vistas.goSpanish();}else if(lang=='en'){Vistas.goEnglish();}else if(lang=='acc'){Vistas.goAccesibilidad();}else{Vistas.goSpanish();}},setMultivista:function(value){var name=Vistas.coockiename;var path='/';var expires=new Date();expires.setDate(expires.getDate()+365);document.cookie=name+"="+window.escape(value)+";expires="+expires.toGMTString()+";path="+path;},readMultivista:function(){var name=Vistas.coockiename;var nameEQ=name+"=";var ca=document.cookie.split(';');for(var i=0;i<ca.length;i++){var c=ca[i];while(c.charAt(0)===' '){c=c.substring(1,c.length);}
if(c.indexOf(nameEQ)===0){return c.substring(nameEQ.length,c.length);}}
return null;},goSpanish:function(){Vistas.setMultivista('es');var url=document.URL;if(url.indexOf('/site/cache/nroedic/taxport')>0){var urltotax=Vistas.getUrlTaxport(url,'');if(urltotax==''){window.location.href='/';}
window.location.href=urltotax;}else if(url.indexOf(Vistas.dirCgiBin)>0){window.location.href='/';}else{if(Vistas.urlRedirect){window.location.href=Vistas.urlRedirect;}else{window.location.reload();}}},goAccesibilidad:function(){Vistas.setMultivista('acc');var url=document.URL;if(url.indexOf('/site/cache/nroedic/taxport')>0){var urltotax=Vistas.getUrlTaxport(url,'acc');if(urltotax==''){window.location.href='/';}
window.location.href=urltotax;}else if(url.indexOf(Vistas.dirCgiBin)>0){window.location.href='/';}else{if(Vistas.urlRedirect){window.location.href=Vistas.urlRedirect;}else{window.location.reload();}}},goEnglish:function(){Vistas.setMultivista('en');var url=document.URL;if(url.indexOf('/site/cache/nroedic/taxport')>0){var urltotax=Vistas.getUrlTaxport(url,'en');if(urltotax==''){window.location.href='/';}
window.location.href=urltotax;}else if(url.indexOf(Vistas.dirCgiBin)>0){window.location.href='/';}else{if(Vistas.urlRedirect){window.location.href=Vistas.urlRedirect;}else{window.location.reload();}}},getUrlTaxport:function(url,vista){var prontus=url.match(/(\/[a-zA-Z_0-9]+)\/site\//);if(typeof prontus[1]==='undefined'||prontus[1]===''){return'';}
var indices=url.match(/\/(\d+)_(\d+)_(\d+)_(\d+)\./);var urltotax=Vistas.dirCgiBin+'/prontus_taxport_lista.cgi?_MV='+vista+'&_REL_PATH_PRONTUS='+prontus[1];if(indices[1]>0){urltotax=urltotax+'&seccion='+indices[1];}
if(indices[2]>0){urltotax=urltotax+'&tema='+indices[2];}
if(indices[3]>0){urltotax=urltotax+'&subtema='+indices[3];}
if(indices[4]>0){urltotax=urltotax+'&nropag='+indices[4];}
return urltotax;},convertFecha:function(lang,fecha){if(lang=='en'){var trozos=fecha.split("/");return trozos[1]+'/'+trozos[0]+'/'+trozos[2];}else{return fecha;}}};

/**  Configuraciones **/
//Vistas.dirCgiBin = '/cgi-bin';
//Vistas.coockiename = 'vista';