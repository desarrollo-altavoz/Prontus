----------------------------------------------------------------------------------------------------
Datos
----------------------------------------------------------------------------------------------------
Ingeniero: CVI/EAG
Versi�n: 2.0.1
Fecha: 16/02/2012

----------------------------------------------------------------------------------------------------
Descripci�n
----------------------------------------------------------------------------------------------------
Esta soluci�n se encarga de escribir la fecha y hora en alg�n lugar de la pagina y hacer
que esta se vaya actualizando.

El formato de salida por defecto es:
Fecha: Mi�rcoles 15 de junio de 2011
Hora: 16:48:50 hrs

Con actualizaci�n cada 1 segundo.

----------------------------------------------------------------------------------------------------
Instalaci�n General
----------------------------------------------------------------------------------------------------
Se explica de manera r�pida, que hacer para instalar la fecha hora en un header,
como se hace, por ejemplo, en cooperativa y lanacion:

- header.html:
Este archivo debe poseer 2 divs o span, con los IDs:
<span id='lafecha'></span>
<span id='lahora'></span>

- copiar la carpeta de:
/js-local/fechahora/
Al servidor de destino

Nota: La instalacion puede ser en la raiz o dentro de prontus. No afecta el funcionamiento.
S�lo se debe tener en cuenta la ubicaci�n final, al incluir los scripts.

- Incluir ambos scripts:
<script type="text/javascript" language="JavaScript" src="/js-local/fechahora/oNow.class.js"></script>
<script type="text/javascript" language="JavaScript" src="/js-local/fechahora/FechaHora.class.js"></script>
En las p�ginas del sitio

- En el header, debajo de los scrits, iniciar el objeto oNow de la siguiente forma:
  <script type="text/javascript">
    <?php date_default_timezone_set('America/Santiago'); ?>
    oNow.init('<?php echo date("U"); ?>', '<?php echo date("Z"); ?>', true);
  </script>

- Finalmente, se puede setear la fecha/hora de la siguiente forma:
Si se desea que la fecha hora se actualice cada 1 segundo:
FechaHora.init();

O bien, si se quiere poner la fecha hora 1 sola vez sin refrescar, se usa:
FechaHora.write_fecha_hora();

Ambos llamados deben hacerse en el onload de la p�gina. Esto se puede hacer con jquery o directamente
en el onload del body.

----------------------------------------------------------------------------------------------------
Instalaci�n en Modelos
----------------------------------------------------------------------------------------------------
Para su uso en Prontus se provee una macro: macro_fechahora.html que contiene el codigo necesario
para la inicializacion y los elementos span "lafecha", "lahora" donde aparecer la fecha y hora.
Adem�s se deben incluir los js previamente mencionados en las portadas y/o articulos donde se vaya
utilizar la macro.
Actualmente se encuentra instalada en el modelo "Productos".

----------------------------------------------------------------------------------------------------
Modificaci�n
----------------------------------------------------------------------------------------------------
Si se desea cambiar el formato de la fecha y hora, modificar SOLO el archivo FechaHora.class.js
Se deja comentado con:  // ---- Modifcar Aca
Para que sea m�s f�cil ubicarse en el script



