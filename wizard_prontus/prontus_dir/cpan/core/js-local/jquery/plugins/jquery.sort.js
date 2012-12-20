/*
 * jQuery Sort plugin
 * Version 1.0.1 (2/1/09)
 * @requires jQuery v1.2.3 or later
 *
 * Copyright (c) 2009 C. Pettit / ZeroPoint Development
 * Dual licensed under the MIT and GPL licenses:
 * http://www.opensource.org/licenses/mit-license.php
 * http://www.gnu.org/licenses/gpl.html
 *
 * 06/03/2009 - CVI - Se mejora/corrige comparación numérica
 */
(function(a){a.fn.sort=function(b,k){if(typeof(b)==="undefined"){return a(this)}if(b==""){return a(this)}if(typeof(b)==="string"){var e=a(this).get().sort(function(c,f){if(a(c).attr(b)==parseInt(a(c).attr(b))){return parseInt(a(c).attr(b))>parseInt(a(f).attr(b))?1:-1}else{return a(c).attr(b).toLowerCase()>a(f).attr(b).toLowerCase()?1:-1}});if(j(k)){return a(e.reverse())}else{return a(e)}}if(typeof(b)==="object"){if((b).length){var e=a(this).get().sort(function(c,f){var g=0;var d=1;while(g<b.length){var h=a(c).attr(b[g]).toLowerCase();var i=a(f).attr(b[g]).toLowerCase();if(h>i){d=1;break}if(i>h){d=-1;break}g++}return d});if(j(k)){return a(e.reverse())}else{return a(e)}}else{var e=a(this).get().sort(function(c,f){var g=0;for(var d in b){var h=a(c).attr(d).toLowerCase();var i=a(f).attr(d).toLowerCase();if(h>i){return(j(b[d]))?-1:1}if(i>h){return(j(b[d]))?1:-1}}});return a(e)}}};function j(c){if(typeof c=="boolean"){return c}else if(c.toLowerCase()=="desc"){return true}else return false}})(jQuery);