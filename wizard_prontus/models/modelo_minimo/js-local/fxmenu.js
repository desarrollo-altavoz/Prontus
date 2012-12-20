$(document).ready(function(){
    $("[id^=menu]").each(function(i,e){
        var theHref = window.location.href;
        enlace = $('#'+ this.id).attr('href');
        if ( (theHref == enlace) || (theHref.indexOf(enlace)> 0)) {
           $('#'+ this.id + ' span').css({'color':'#CC0000'});
        }
       
        /* para portadas taxonomicas taxport */
        if ((enlace.indexOf('cgi-bin')> 0) && (enlace.indexOf('seccion=9')> 0) && (theHref.indexOf('taxport')> 0)) {
            $('#'+ this.id + ' span').css({'color':'#CC0000'});
        }
     });    
 }); 