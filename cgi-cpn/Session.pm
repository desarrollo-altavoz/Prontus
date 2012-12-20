#!/usr/bin/perl

package Session;
use strict;
use Carp qw(cluck carp);
use warnings;
no warnings 'uninitialized';

use DBI;
use glib_str_02;
use glib_fildir_02;


# use diagnostics;


# ---------------------------------------------------------------
# Errores orientados a que los pueda leer el usuario, sin info del ambiente.
# el texto completo del error se tira al STDERR
our $ERR;

# Tiempo de expiracion de la session (tpo max de inactividad para borrar el archivo de la sesion)
our $EXPIRE_SESS_SEGS = 172800; # 48hrs

# ---------------------------------------------------------------
sub new {
# Crea el objeto y retorna una referencia a el.

    my $clase = shift;
    my $sess = {@_};
    bless $sess, $clase;

    # Atributos recibidos.
    $sess->{prontus_id}         ||= '';
    $sess->{document_root}      ||= '';
    $sess->{id_session_given}   ||= ''; # permite ver si un id de sesion es valido aun cuando no haya acceso a cookies, esta es comprobada viendo si existe el file


    # Valida document_root
    if ( ($sess->{document_root} eq '') || (!-d $sess->{document_root}) ) {
        $Session::ERR = "Session::new con params no validos:\n"
                      . "document_root[$sess->{document_root}] \n";
        return 0;
    };

    # Valida prontus_id
    if ( (!-d "$sess->{document_root}/$sess->{prontus_id}") || ($sess->{prontus_id} eq '') || ($sess->{prontus_id} !~ /^[\w\d]+$/) ) {
        $Session::ERR = "Session::new con params no validos:\n"
                      . "prontus_id[$sess->{prontus_id}] \n";
        return 0;
    };

    # despulga id de sesion dada
    $sess->{id_session_given} =~ s/\W//sg;

    # set dir de sesiones
    $sess->{dir_sessions} = "$sess->{document_root}/$sess->{prontus_id}/cpan/data/users/sessions";
    if (! &glib_fildir_02::check_dir($sess->{dir_sessions})) {
        $Session::ERR = "Session::new --> no se pudo crear dir de sesiones o este no es valido\n";
        return 0;
    };

    # Recupera sesion activa
    my $sesion_existente = $sess->_existe_session();
    if ($sesion_existente ne '') {
        $sess->{id_session} = $sesion_existente;
    };

    return $sess;
};

# ---------------------------------------------------------------
sub _existe_session {
# si existe una sesion valida, retorna el id, sino retorna ''
    my $this = shift;

    my $id_session;
    if ($this->{id_session_given} ne '') {
        $id_session = $this->{id_session_given};
    } else {
        my %cookies = &lib_cookies::get_cookies();
        $id_session = $cookies{'SESSION_' . $this->{prontus_id}};
    };

    if (($id_session ne '') && (-f "$this->{dir_sessions}/$id_session")) {
        return $id_session;
    } else {
        return '';
    };

};


# ---------------------------------------------------------------
sub set_new_session {
    my $this = shift;

    # Primero detecta si hay una activa y la mata--> basta con q este la cookie
    my %cookies = &lib_cookies::get_cookies();
    my $id_session = $cookies{'SESSION_' . $this->{prontus_id}};
    $this->end_session() if ($id_session ne '');


    # Crea la sesion
    $this->{id_session} = &glib_str_02::random_string(20);
    while (-f "$this->{dir_sessions}/$this->{id_session}") {
        $this->{id_session} = &glib_str_02::random_string(20);
    };
    &glib_fildir_02::write_file("$this->{dir_sessions}/$this->{id_session}");
    &lib_cookies::set_simple_cookie('SESSION_' . $this->{prontus_id}, $this->{id_session});

    # Grabage de sesiones antiguas
    $this->_garbage_sessionid();
};
# ---------------------------------------------------------------
sub rejuvenece_sesion {
# Renueva el arch de la sesion para que esta siga activa y no sea borrada por el garbage
    my $this = shift;
    &glib_fildir_02::write_file("$this->{dir_sessions}/$this->{id_session}");
};

# ---------------------------------------------------------------
sub end_session {
    # Borra archivo y cookie de sesion
    my $this = shift;
    unlink "$this->{dir_sessions}/$this->{id_session}";
    &lib_cookies::set_simple_cookie('SESSION_' . $this->{prontus_id}, '');
};

# --------------------------------------------------------------------#
sub _garbage_sessionid {
    my $this = shift;
    my $dir = $this->{dir_sessions};

    # Lee el contenido del directorio.
    my @lisdir = &glib_fildir_02::lee_dir($dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

    # Borra archivos con mas de 48hrs de antiguedad, por fecha de ult modif.
    foreach my $entry (@lisdir) {
        if (-f "$dir/$entry") {
            my @stats = stat "$dir/$entry";
            # print $stats[10] . ' ';
            if ($stats[9] < (time - $Session::EXPIRE_SESS_SEGS)) { # 48hrs

                # si el q se va a borrar por casualidad llegara a ser la sesion activa, no la mata
                if ($entry ne $this->{id_session}) {
                    unlink "$dir/$entry";
                };
            };
        };
    };
};


# ---------------------------------------------------------------
return 1;

# Para desplegar la doc. desde linea de comandos:
# perldoc Session.pm
# Para generar la doc en html:
# perldoc -T -o html IO::Handle > IO::Handle.html

__END__

=head1 NOMBRE

B<Session.pm> - Clase para emular sesiones en Perl.

=for comment
# ---------------------------------------------------------------

=head1 SINOPSIS

Instanciar y acceder a un metodo publico:

    use Session;

    # Creacion del objeto.
    my $sess_obj = Session->new(
                    'prontus_id'        => 'prontus_noticias',
                    'document_root'     => '/sites/misitio/web')
                    || die("Error inicializando objeto Session: $Session::ERR\n");

    # Obtener id de sesion
    $sess_obj->get_sessionid() || die("Error: $Session::ERR");


=for comment
# ---------------------------------------------------------------

=head1 DESCRIPCION

Contiene operaciones para manipulacion de sesion en Perl

=for comment
# ---------------------------------------------------------------

=head2 VARIABLES DE CLASE, ESTATICAS

=over 8

=item C<$Session::ERR>

Variable que se carga con el texto descriptivo del error en caso de que un metodo retorne 0.
Este texto esta adecuado para ser presentado directamente al usuario, ya que el texto completo
del error, incluyendo paths y backtrace es enviado al STDERR.

=back

=for comment
# ---------------------------------------------------------------

=head2 ATRIBUTOS

Los atributos se acceden de la forma:

    my $attr = $sess_obj->{nombre_atributo};

Los atributos son:

B<id_session>:

    id alfanumerico de la sesion, de 20 caracteres.

B<prontus_id>:

    nombre del publicador Prontus,
    por ejemplo 'prontus_noticias'

B<document_root>:

    document root asociado al server,
    por ejemplo '/sites/misitio/web'

=for comment
# ---------------------------------------------------------------

=head2 METODOS PUBLICOS

=over 8

=for comment
# ---------------------------------------------------------------

=item B<new()>

Devuelve un nuevo objeto Session. Los parametros son los indicados en la sinopsis.

=for comment
# ---------------------------------------------------------------

=item B<renew()>

renueva el archivo de sesion, de manera que no sea tomado por el garbage

=for comment
# ---------------------------------------------------------------

=item B<get_sessionid()>

  Obtiene el id de sesion, por ejemplo
  '8Y9DrMMvguhokmbPV4yx'

=for comment
# ---------------------------------------------------------------

=head1 AUTOR

Yerko Chapanoff, E<lt>yerko@altavoz.netE<gt>

=cut
