#!/bin/sh
if [ X"$1" = X"" ]; then
	echo "usage: $0 <fb-contrib-dir>"
	exit 1
fi

_cdir=$(cd -- "$(dirname "$0")" && pwd)
"${_cdir}/fb2sq.py" -e CD_CIRCULAR_DEPENDENCY --html --tidy "${_cdir}/sq_rules.fbcontrib.dat" "$1/etc"
