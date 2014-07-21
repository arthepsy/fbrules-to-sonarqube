#!/bin/sh
if [ X"$1" == X"" ]; then
	echo "usage: $0 <findsecbugs-dir>"
	exit 1
fi	

$(dirname $0)/fbp2sq.py $1/plugin/src/main/resources/metadata > rules-findsecbugs.xml

