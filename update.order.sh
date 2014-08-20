#!/bin/sh
_outdir='build'
_sqrules='sq_rules.dat'

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

# -- rules order
echo "[ ] updating rule order ... "
_tmp=`echo tmp.$$`
_order=`grep key= ${_dir1}/rules.xml | cut -d '"' -f 2 | cat -n | awk '{ print $1 ":" $2 }'`
for i in ${_order}; do
	_nr=$(echo $i | cut -d ':' -f 1)
	_rk=$(echo $i | cut -d ':' -f 2)
	sed -e "s/$_rk:\([0-9]*\):/${_rk}:${_nr}:/" ${_sqrules} > ${_tmp} && mv ${_tmp} ${_sqrules} 
done

# -- properties order
echo "[ ] updating properties order ... "
_tmp=`echo tmp.$$`
_order=`cut -d '.' -f 3 ${_dir2}/findbugs.properties | cat -n | awk '{ print $1 ":" $2 }'`
for i in ${_order}; do
	_nr=$(echo $i | cut -d ':' -f 1)
	_rk=$(echo $i | cut -d ':' -f 2)
	sed -e "s/$_rk:\([0-9]*\):\([0-9]*\):/${_rk}:\1:${_nr}:/" ${_sqrules} > ${_tmp} && mv ${_tmp} ${_sqrules} 
done

# -- profile order
echo "[ ] updating profile order ... "
_tmp=`echo tmp.$$`
_order=`grep pattern= ${_dir1}/profile-findbugs.xml | cut -d '"' -f 2 | cat -n | awk '{ print $1 ":" $2 }'`
for i in ${_order}; do
	_nr=$(echo $i | cut -d ':' -f 1)
	_rk=$(echo $i | cut -d ':' -f 2)
	sed -e "s/$_rk:\([0-9]*\):\([0-9]*\):\([0-9]*\):/${_rk}:\1:\2:${_nr}:/" ${_sqrules} > ${_tmp} && mv ${_tmp} ${_sqrules} 
done
