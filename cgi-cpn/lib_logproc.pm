#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

package lib_logproc;

$LOG_FILE = '';
$MODO_WEB = 0;

# ---------------------------------------------------------------
sub log_init {
  my ($title, $desc) = ($_[0], $_[1]);
  my ($buffer) = q{<html><head><title>%%title%%</title>
    <http-equiv="pragma" content="no-cache">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <style type="text/css">
    body {font-family:Arial,Helvetica,sans-serif;}
    a {color:#00F;}
    a:hover {color:#800;}
    </style>
    </head><body bgcolor="#ffffff">
    <a name="top"></a>
    <h2>%%title%%</h2>
    <p>%%desc%%</p>
    <p>&raquo <a href="#" onclick="window.close(); return false;">cerrar página</a> &nbsp;
    &raquo <a href="#bottom">bajar</a></p><pre>};

  $buffer =~ s/%%title%%/$title/g;
  $buffer =~ s/%%desc%%/$desc/g;

  utf8::encode($buffer);
  if(-f ("$prontus_varglb::DIR_SERVER$LOG_FILE")) {
    unlink "$prontus_varglb::DIR_SERVER$LOG_FILE";
  }
  &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$LOG_FILE", $buffer);

}; # logInit

# ------------------------------------------------------------------------------
sub flush_log {

  # Abrir archivo log.
  my $buffer = &glib_fildir_02::read_file($LOG_FILE);
  unlink $LOG_FILE;

  open(LOG, ">>$LOG_FILE") ||  die "\n No se pudo abrir $LOG_FILE \n";
  #binmode(LOG, ":utf8");

  print LOG $buffer;
  if ($MODO_WEB) {
    $buffer =~ s/<INPUT .*?presione.*?refrescar.*?>//is;
    print $buffer;
  };
  close LOG;
};

# ------------------------------------------------------------------------------
sub add_to_log {

  my ($msg) = $_[0];

  # Abrir archivo log
  return unless($LOG_FILE);
  open(LOG, ">>$LOG_FILE") ||  die "\n No se pudo abrir $LOG_FILE \n";
  binmode(LOG, ":utf8");

  # Se imprime el mensaje sin fecha
  print LOG "$msg\n";
  print "$msg\n" if ($MODO_WEB);
  close LOG;
};

# ------------------------------------------------------------------------------
sub add_to_log_count {

  my ($msg) = $_[0];
  return unless($msg);

  # Se calcula fecha / hora
  my $dtime = &glib_hrfec_02::get_dtime_pack4();
  $dtime = &format_dtime($dtime);

  # Se actualiza fecha / hora con el mensaje
  my $newmsg = "$dtime\t$msg";
  &add_to_log($newmsg);
};

# ------------------------------------------------------------------------------
sub add_to_log_finish {

  my ($msg) = $_[0];
  my ($do_exit) = $_[1]; # 0 | 1

  &add_to_log_count($msg);
  &writeRule();

  $newmsg = $newmsg . "</pre><a name=\"bottom\"></a>";
  $newmsg = $newmsg . "<p>&raquo <a href=\"#\" onclick=\"window.close(); return false;\">cerrar p&aacute;gina</a> &nbsp";
  $newmsg = $newmsg . "&raquo <a href=\"#top\">subir</a></p>\n</body></html>";
  &add_to_log($newmsg);
  exit if ($do_exit == 1);
};

# ------------------------------------------------------------------------------
sub handle_error {
  my ($msg, $ok_regs) = @_;

  $ok_regs = '0' if($ok_regs eq '');
  &writeRule();
  &add_to_log_count("Ejecucion abortada: $msg.\n\tSe alcanzaron a procesar $ok_regs registros.");

  $newmsg = $newmsg . "</pre><a name=\"bottom\"></a>";
  $newmsg = $newmsg . "<p>&raquo <a href=\"#\" onclick=\"window.close(); return false;\">cerrar p&aacute;gina</a> &nbsp";
  $newmsg = $newmsg . "&raquo <a href=\"#top\">subir</a></p>\n</body></html>";
  &add_to_log($newmsg);

  if (ref($BD)) {
    $BD->disconnect;
  };
  exit;
};

# ------------------------------------------------------------------------------
sub writeRule {
  my $msg = "----------------------------------------------------------------------";
  &add_to_log($msg);
};

# ------------------------------------------------------------------------------
sub format_dtime {
my ($dtime) = $_[0];
  $dtime =~ /(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)/;
  return "$3/$2/$1 - $4:$5:$6";
};

return 1;
