#!/bin/sh
_usage() {
	echo "usage: $0 <findbugs-dir> <fbcontrib-dir> [sonar-findbugs-dir]"
	exit 1
}
if [ X"$1" = X"" ]; then
	_usage
fi
if [ X"$2" = X"" ]; then
	_usage
fi
_cdir=$(cd -- "$(dirname "$0")" && pwd)
if [ X"$3" != X"" ]; then
	"${_cdir}/fb.rules.py" list "$1" "$2" -s "$3"
else
	"${_cdir}/fb.rules.py" list "$1" "$2"
fi
