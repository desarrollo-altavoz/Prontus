#!/bin/bash

apt-get update
apt-get install libmail-sender-perl
apt-get install -y --force-yes ffmpeg
apt-get install libuniversal-require-perl

#instalacion PHP Session
PHP="/var/www/instal/PHP-Session-0.27.tar.gz";

cd "/var/www/instal/";
tar zxvf "$PHP";
cd "${PHP%\.tar.gz}" 2> /dev/null || {
	echo -e "\aError instalar php session";
	exit 1;
	}
perl Makefile.PL;
make;
make test;
make install;
