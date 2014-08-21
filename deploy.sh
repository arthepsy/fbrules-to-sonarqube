#!/bin/sh
_outdir='build'

if [ X"$1" == X"" ]; then
	echo "usage: $0 <sonar-findbugs-dir>"
	exit 1
fi	

check_dir() {
	if [ ! -d $1 ]; then
		echo "error: incorrect direcotry \"$1\""
		exit 1
	fi
}

check_dir $1
_ddir=$(cd $1 && pwd)
_odir=$(cd ${_outdir} && pwd)
_dir1="${_ddir}/src/main/resources/org/sonar/plugins/findbugs"
_dir2="${_ddir}/src/main/resources/org/sonar/l10n"
_dir3="${_dir2}/findbugs/rules/findbugs"

check_dir ${_dir1}
check_dir ${_dir2}
check_dir ${_dir3}

if [ -d "${_odir}" ]; then
	cp ${_odir}/rules*.xml ${_dir1}/
	cp ${_odir}/profile-*.xml ${_dir1}/
	cp ${_odir}/*.properties ${_dir2}/
	cp ${_odir}/html/*.html ${_dir3}/
fi

