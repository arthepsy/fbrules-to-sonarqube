#!/bin/sh
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

_dir1="$1/src/main/resources/org/sonar/plugins/findbugs"
_dir2="$1/src/main/resources/org/sonar/l10n"
_dir3="${_dir2}/findbugs/rules/findbugs"

check_dir ${_dir1}
check_dir ${_dir2}
check_dir ${_dir3}

cd $(dirname $0)
for r in rules-*.xml; do
	if [ X"$r" == X"rules-findbugs.xml" ]; then
		cp $r ${_dir1}/rules.xml
	else
		cp $r ${_dir1}/$r
	fi	
done

./generate_profile.sh
cp profile-findbugs.xml ${_dir2}/

./generate_properties.sh
cp findbugs.properties ${_dir2}/

cp html/*.html ${_dir3}/


