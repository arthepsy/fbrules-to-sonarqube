#!/bin/sh
if [ X"$1" = X"" ]; then
	echo "usage: $0 <findbugs-dir> [sonar-findbugs-dir]"
	exit 1
fi
_cdir=$(cd -- "$(dirname "$0")" && pwd)
if [ X"$2" != X"" ]; then
	"${_cdir}/fb.rules.py" "$1/findbugs/etc" -r "$2/src/main/resources/org/sonar/plugins/findbugs/rules.xml"
else
	"${_cdir}/fb.rules.py" "$1/findbugs/etc"
fi
