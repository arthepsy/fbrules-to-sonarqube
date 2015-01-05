#!/bin/sh
_appname='fb2sq.deploy'
_outdir='build'

if [ X"$1" = X"" ]; then
	echo "usage: $0 <sonar-findbugs-dir>"
	exit 1
fi

_cdir=$(cd -- "$(dirname "$0")" && pwd)
. "${_cdir}/ar.utils.sh"

_chkdir "$1"
_sqfbdir=$(_getdir "$1/decoy")
_odir=$(_getdir "${_outdir}/decoy")
_dir1="${_sqfbdir}/src/main/resources/org/sonar/plugins/findbugs"
_dir2="${_sqfbdir}/src/main/resources/org/sonar/l10n"
_dir3="${_dir2}/findbugs/rules/findbugs"

_chkdir "${_dir1}" "${_dir2}" "${_dir3}"
if [ -d "${_odir}" ]; then
	find "${_odir}" -name "rules*.xml" -exec cp "{}" "${_dir1}/" \;
	find "${_odir}" -name "profile-*.xml" -exec cp "{}" "${_dir1}/" \;
	find "${_odir}" -name "*.properties" -exec cp "{}" "${_dir2}/" \;
	find "${_odir}/html/findbugs/" -name "*.html" -exec cp "{}" "${_dir3}/" \;
fi

