#!/bin/sh
if [ X"$1" = X"" ]; then
	echo "usage: $0 <findsecbugs-dir> [sonar-findbugs-dir]"
	exit 1
fi
_cdir=$(cd -- "$(dirname "$0")" && pwd)
if [ X"$2" != X"" ]; then
	"${_cdir}/fb.rules.py" list "$1" -s "$2"
else
	"${_cdir}/fb.rules.py" list "$1"
fi
