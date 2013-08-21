package lib_xcoding;

use glib_fildir_02;

# ---------------------------------------------------------------
sub get_formatos {
	my $marca = $_[0];
	my %formatos;
    my $file_formatos = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/data/xcoding/formatos.cfg";

    if (-f $file_formatos) {
        my $buffer_formatos = &glib_fildir_02::read_file($file_formatos);
        if ($marca ne '') {
            while ($buffer_formatos =~ /\s*($marca\.\w)\s*=\s*["|'](.*?)["|']/ig) {
                $formatos{$1} = $2;
            };
        };
    };

    return %formatos;
};

# ---------------------------------------------------------------
sub get_info_video {
	my $origen = $_[0];
	my @info =`$prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen 2>&1`;
	my ($width, $height, $h264, $baseline, $vcodec, $acodec, $ext);

    if ($origen =~ /.+\/\d{8}\/mmedia\/multimedia_video.+?\d{6}\.(\w+)$/) {
        $ext = $1;
    };

    foreach (@info) {
        # Video: h264 (Baseline), yuv420p, 1920x1080, 20745 kb/s, 29.97 fps, 29.97 tbr, 600 tbn, 1200 tbc
        if ($_ =~ m/(Video): ([^,]+), (\S+), ([0-9]+)x([0-9]+).+/) {
            if ($1 eq 'Video') {
                print STDERR "Video: [$1] [$2] [$3] [$4] [$5]\n";
                $vcodec = $2;
                $width = $4;
                $height = $5;
            };
        };
        # Audio: aac, 44100 Hz, mono, s16, 62 kb/s
        if ($_ =~ m/(Audio): ([^,]+), ([^,]+), ([^,]+), ([^,]+),.+/) {
            if ($1 eq 'Audio') {
                print STDERR "Audio: [$1] [$2] [$3] [$4] [$5]\n";
                $acodec = $2;
            };
        };
    };

    # si el tamaño se sobrepasa, ajustarlo.
    my ($new_width, $new_height);
    if ($width > 640 || ($width %2 != 0) || ($height %2 != 0) ) {
        $new_width = $width;
        $new_height = $height;
        if ($new_width > 640) {
            $new_width = 640;
            $new_height = int (640*$height/$width);
            if ($new_height %2 != 0){
                $new_height +=1;
            };
        } else {
            if ($new_width %2 != 0) {
                $new_width += 1;
            };
            if ($new_height%2 != 0) {
                $new_height += 1;
            };
        };
    };

    return ($new_width, $new_height, $h264, $baseline, $vcodec, $acodec);
};

# ---------------------------------------------------------------
sub get_cmd_ffmpeg {
    my $origen = $_[0];
    my $destino = $_[1];
    my $videoFlags = $_[2];
    my $pathnice = &lib_prontus::get_path_nice();

    if ($videoFlags ne '') {
    	return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen $videoFlags $destino";
    };

    my $videoFlags = $prontus_varglb::FFMPEG_PARAMS;
    if ($videoFlags eq '' ) {
        $videoFlags = "-flags +loop -cmp +chroma -partitions +parti8x8+parti4x4+partp8x8+partb8x8 -me_method umh -subq 8 -me_range 16 -keyint_min 25 -sc_threshold 40 -i_qfactor 0.71 -b_strategy 2 -qcomp 0.6 -qmin 10 -qmax 51 -qdiff 4 -directpred 3 -trellis 1 -coder 0 -bf 0 -refs 1 -flags2 -wpred-dct8x8+mbtree -level 30 -maxrate 10000000 -bufsize 10000000 -wpredp 0 -g 25 -b 600000"; #configuracion de compresion, para no utilizar presets ffmpeg
    };

    my ($ancho, $alto, $h264, $baseline, $vcodec, $acodec) = &get_info_video($origen);
    my $pathnice = &lib_prontus::get_path_nice();

    if ($ancho ne '' && $alto ne '') {
        print STDERR "Redimencion: ancho[$ancho], alto[$alto]\n";
        if ($acodec =~ /aac/i) {
            return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -s $ancho" . 'x' . "$alto -vcodec libx264 $videoFlags -acodec copy -f mp4 $destino";
        } else {
            return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -s $ancho" . 'x' . "$alto -vcodec libx264 $videoFlags -acodec libfaac -ar 44100 -ab 48k -f mp4 $destino";
        };

    } elsif ($acodec =~ /aac/i && $vcodec =~ /h264/i && $vcodec =~ /baseline/i) {
        return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -vcodec copy -acodec copy -f mp4 $destino";
    } elsif ($acodec =~ /aac/i) {
        return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -vcodec libx264 $videoFlags -acodec copy -f mp4 $destino";
    } else {
        return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -vcodec libx264 $videoFlags -acodec libfaac -ar 44100 -ab 48k -f mp4 $destino";
    };
};

return 1;