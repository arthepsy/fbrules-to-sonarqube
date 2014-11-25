#!/bin/sh
if [ X"$1" = X"" ]; then
	echo "usage: $0 <findbugs-dir>"
	exit 1
fi	

$(dirname $0)/fb2sq.py -e TESTING -e TESTING1 -e TESTING2 -e TESTING3 -e UNKNOWN --html --tidy $1/findbugs/etc

