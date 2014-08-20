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

_cdir=$(cd $(dirname $0) && pwd)
cd ${_cdir} && mkdir -p ${_odir} && cd ${_odir}
for r in rules-*.xml; do
	if [ X"$r" == X"rules-findbugs.xml" ]; then
		cp $r ${_dir1}/rules.xml
	else
		cp $r ${_dir1}/$r
	fi
done

${_cdir}/generate_profile.sh
cp ${_odir}/profile-findbugs.xml ${_dir2}/

${_cdir}/generate_properties.sh
cp ${_odir}/findbugs.properties ${_dir2}/

cp ${_odir}/html/*.html ${_dir3}/


