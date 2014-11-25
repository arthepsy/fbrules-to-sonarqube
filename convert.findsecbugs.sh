#!/bin/sh
if [ X"$1" = X"" ]; then
	echo "usage: $0 <findsecbugs-dir>"
	exit 1
fi	

$(dirname $0)/fb2sq.py --html --tidy $1/plugin/src/main/resources/metadata 

