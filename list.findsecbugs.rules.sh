#!/bin/sh
if [ X"$1" = X"" ]; then
	echo "usage: $0 <findsecbugs-dir> [sonar-findbugs-dir]"
	exit 1
fi
_cdir=$(cd -- "$(dirname "$0")" && pwd)
if [ X"$2" != X"" ]; then
	"${_cdir}/fb.rules.py" "$1/plugin/src/main/resources/metadata" -r "$2/src/main/resources/org/sonar/plugins/findbugs/rules-findsecbugs.xml"
else
	"${_cdir}/fb.rules.py" "$1/plugin/src/main/resources/metadata"
fi
