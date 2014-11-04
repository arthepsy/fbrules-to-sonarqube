#!/bin/sh
_outdir='build'
_sqrules='sq_rules.dat'

if [ X"$1" == X"" ]; then
	echo "usage: $0 <sonar-findbugs-dir>"
	exit 1
fi	

check_dir() {
	if [ ! -d $1 ]; then
		echo "error: incorrect directory \"$1\""
		exit 1
	fi
}
check_file() {
	if [ ! -f $1 ]; then
		echo "error: file not found: \"$1\""
		exit 1
	fi
}

check_dir $1
_ddir=$(cd $1 && pwd)
_odir=$(cd ${_outdir} && pwd)

_dir1="${_ddir}/src/main/resources/org/sonar/plugins/findbugs"
_dir2="${_ddir}/src/main/resources/org/sonar/l10n"

_fb_rules="${_dir1}/rules.xml"
_fb_props="${_dir2}/findbugs.properties"
_fb_profile="${_dir1}/profile-findbugs.xml"

check_dir ${_dir1}
check_dir ${_dir2}
check_file ${_fb_rules}
check_file ${_fb_props}
check_file ${_fb_profile}

_tmpdir=$(mktemp -d)
if [ $? -ne 0 ]; then
	echo "error: could not create temporary directory"
	exit 1
fi

# -- rules order
echo "[ ] updating rule order ... "
_tmp="${_tmpdir}/tmp.$$"
_order=$(grep "key=" ${_fb_rules} | cut -d '"' -f 2 | cat -n | awk '{ print $1 ":" $2 }')
for i in ${_order}; do
	_nr=$(echo $i | cut -d ':' -f 1)
	_rk=$(echo $i | cut -d ':' -f 2)
	sed -e "s/$_rk:\([0-9]*\):/${_rk}:${_nr}:/" ${_sqrules} > ${_tmp} && mv ${_tmp} ${_sqrules} 
done

# -- properties order
echo "[ ] updating properties order ... "
_order=$(cut -d '.' -f 3 ${_fb_props} | cat -n | awk '{ print $1 ":" $2 }')
for i in ${_order}; do
	_nr=$(echo $i | cut -d ':' -f 1)
	_rk=$(echo $i | cut -d ':' -f 2)
	sed -e "s/$_rk:\([0-9]*\):\([0-9]*\):/${_rk}:\1:${_nr}:/" ${_sqrules} > ${_tmp} && mv ${_tmp} ${_sqrules} 
done

# -- profile order
echo "[ ] updating profile order ... "
_order=$(grep "pattern=" ${_fb_profile} | cut -d '"' -f 2 | cat -n | awk '{ print $1 ":" $2 }')
for i in ${_order}; do
	_nr=$(echo $i | cut -d ':' -f 1)
	_rk=$(echo $i | cut -d ':' -f 2)
	sed -e "s/$_rk:\([0-9]*\):\([0-9]*\):\([0-9]*\):/${_rk}:\1:\2:${_nr}:/" ${_sqrules} > ${_tmp} && mv ${_tmp} ${_sqrules} 
done

rm -rf ${_tmpdir}
