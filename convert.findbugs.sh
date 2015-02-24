#!/bin/sh
if [ X"$1" = X"" ]; then
	echo "usage: $0 <findbugs-dir>"
	exit 1
fi

_cdir=$(cd -- "$(dirname "$0")" && pwd)
"${_cdir}/fb2sq.py" -e TESTING -e TESTING1 -e TESTING2 -e TESTING3 -e UNKNOWN --html --tidy "${_cdir}/sq_rules.findbugs.dat" "$1/findbugs/etc"
