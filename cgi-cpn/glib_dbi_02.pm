#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

#-------------------------------COMENTARIO GLOBAL---------------
#---------------------------------------------------------------
# PROPOSITO.
#-----------
# Rutinas para acceso generico a bases de datos via DBI.
# Para utilizar DBI, aparte de Perl se requieren los sgtes. paquetes :
# 1) DBI.
# 2) DBD-Mysql u otro específico para la BD que se desa accesar.

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 01 : Primera version at 04/feb/2000.
# 01.1 : MCO: 02/03/2001 - Funcion  insert_dev_id() que inserta registro y devuelve nuevo id.
# 01.2 : MCO: 02/04/2001 - Funcion ejecutar_sql_bind() que ejecuta una consulta y devuelve por medio de un fetch los valores de la fila.

# 02 : Cambio a segunda version - 18/04/2001.
# 02.1 : Se cambian unos 'local' por 'my' - 29/05/2001 -- YCC.
#
#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package glib_dbi_02;
use DBI;

#---------------------------------------------------------------
# SUB-RUTINAS.
#-------------
#-------------------------------------------------------------------------#
sub ejecutar_sql {
# Ejecuta una sentencia sql.

# Parametros :
# 0)base de datos abierta
# 1)sentencia sql

# Retorna : handle de salida de la sentencia

my ($base) = $_[0];
my ($sql) = $_[1];

my $tab_output = $base->prepare($sql)  or  print STDERR "<b>Error</><br>$sql<br>" . $base->errstr;

$tab_output->execute or  print STDERR "<b>Error</><br>$sql<br>" . $base->errstr;

return $tab_output;
};

#---------------------------------------------------------------
sub gen_popup_from_sql {
# Genera un objeto de lista de seleccion con la info suministrada

# Parametros :
# 0)sentencia sql. El orden de los campos requeridos es primero el del value y luego el de display
# 1)base de datos abierta
# 2)nombre que se le dara al objeto generado
# 3)nro. de items visibles
# 4)indicador de seleccion multiple ('' o 'MULTIPLE')
# 5)valor del VALUE en el cual se deberá posicionar el cursor

# Retorna : Lista de seleccion con datos, lista para imprimirla.

  my($base) = $_[0];        # 02.1
  my($sentencia) = $_[1];
  my($name_obj) = $_[2];
  my($items_visibles) = $_[3];
  my($ind_multiple) = $_[4];
  my($valor_clave) = $_[5];

  my($tab_output);
  my($campo_value);
  my($campo_display);


  $tab_output = &ejecutar_sql($base, $sentencia);
  $tab_output->bind_columns(undef, \(
                                     $campo_value,
                                     $campo_display
                                       ));

  # Generar la lista de seleccion en html
  $lista = q{<select name="} . $name_obj . q{" size="} . $items_visibles . q{" } . $ind_multiple . q{>};

  while($tab_output->fetch){
    $seleccionado = '';
    if ( $campo_value eq $valor_clave ) {
       $seleccionado = 'selected';
    }
    $lista .= "\n" . '<option value="' . $campo_value . '" ' . $seleccionado . '>';
    $lista .= "$campo_display</option>";
  };
  $lista = $lista . q{</select>};
  return $lista;
};

#-------------------------------------------------------------------------#
sub insert_dev_id { # 01.1
# Inserta registro y devuelve nuevo ID.

# Parametros :
# 0) base de datos abierta
# 1) sentencia insert

# Retorna : Nuevo ID.

  my ($base) = $_[0];
  my ($sql) = $_[1];
  my ($res, @nuevo_id);

  $res = $base->do($sql);

  $sql = 'select last_insert_id()';
  $res = &ejecutar_sql($base, $sql);
  @nuevo_id = $res->fetchrow_array;
  $res->finish;

  return $nuevo_id[0];
};

#-------------------------------------------------------------------------#
sub check_table_column {
    # Averigua si una col existe.
    # Si existe, retorna el nombre de la col.
    # Si no existe, retorna ''
    my ($base, $tabla, $colname, $coldef) = @_;
    my $sql = "SHOW COLUMNS FROM $tabla LIKE '$colname'";
    my $nom;
    my ($type, $null, $key, $default, $extra);
    my $res = &ejecutar_sql_bind($base, $sql, \($nom, $type, $null, $key, $default, $extra));
    $res->fetch;
    $res->finish;

    # crear columna si no existe y si es q viene la def del campo
    if ($coldef) {
        if (!$nom) {
            $base->do("ALTER TABLE $tabla ADD $colname $coldef") || return 0;
        };
        return 1;
    } else {
        return $nom;
    };

};
#-------------------------------------------------------------------------#
sub existe_tabla {
# Ve si la tabla existe;
  my ($base) = $_[0];
  my ($tabla) = $_[1];
  my ($sql, $salida, $nom);

  $nom = 0;

  $sql = "show tables";
  $salida = &ejecutar_sql_bind($base, $sql, \($nom));
  while ($salida->fetch) {
    if ($nom eq $tabla) {
      $salida->finish;
      return $nom;
    };
  };
  $salida->finish;
  return '';

};

#-------------------------------------------------------------------------#
sub ejecutar_sql_bind { # 01.2
  # ejecuta una sentencia sql y devuelve su handler.
  # Param entrada:
  #  0) descriptor de la base de datos abierta.
  #  1) sentencia SQL propiamente tal.
  #  2) nombres de las variables asociadas a los campos.
  # retorno:
  #  0) descriptor de la respuesta. (Usar solamente fetch para cargar las variables con las filas siguientes.

  my ($dbh) = shift;
  my ($sql) = shift;
  my (@var) = (@_);
  my ($sth);

  $sth = $dbh->prepare($sql) or  print STDERR "<b>Error</><br>$sql<br>" . $dbh->errstr;

  $sth->execute or print STDERR "<b>Error</><br>$sql<br>" . $dbh->errstr;
  $sth->bind_columns(undef, (@var));

  return($sth);
};


#-------------------------------END LIBRERIA------------------

return 1;
