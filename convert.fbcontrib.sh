#!/bin/sh
if [ X"$1" == X"" ]; then
	echo "usage: $0 <fb-contrib-dir>"
	exit 1
fi	

$(dirname $0)/fbp2sq.py --html $1/etc 

