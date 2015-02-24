#!/bin/sh
if [ X"$1" = X"" ]; then
	echo "usage: $0 <findsecbugs-dir>"
	exit 1
fi

_cdir=$(cd -- "$(dirname "$0")" && pwd)
"${_cdir}/fb2sq.py" --html --tidy "${_cdir}/sq_rules.findsecbugs.dat" "$1/plugin/src/main/resources/metadata"
