#!/bin/sh
_outdir='build'
_sqrules='sq_rules.dat'

if [ X"$1" == X"" ]; then
	echo "usage: $0 <findbugs-dir>"
	exit 1
fi	

check_dir() {
	if [ ! -d $1 ]; then
		echo "error: incorrect directory: \"$1\""
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
_cdir=$(cd $(dirname $0) && pwd)
_sdir="$(cd $1 && pwd)/findbugs/etc"
_odir="$(cd ${_outdir} && pwd)"
_fbmsg=${_sdir}/messages.xml
_sqdat=${_cdir}/sq_rules.dat

check_dir ${_sdir}
check_dir ${_odir}
check_file ${_fbmsg}
check_file ${_sqdat}

_tmpdir=$(mktemp -d)
if [ $? -ne 0 ]; then
	echo "error: could not create temporary directory"
	exit 1
fi
_sqnew=${_tmpdir}/sq_rules.dat

cp ${_sqdat} "${_sqnew}"
grep "<BugPattern type=" ${_fbmsg} | cut -d '"' -f 2 | sort > ${_tmpdir}/fb.rules
grep -v "^#" ${_sqdat} | cut -d ':' -f 1 | sort > ${_tmpdir}/sq.rules
for diff in $(diff -ruN ${_tmpdir}/sq.rules ${_tmpdir}/fb.rules | tail -n +3 | grep "^[\+-]"); do
	_r_act=$(echo $diff | cut -c -1)
	_r_key=$(echo $diff | cut -c 2-)
	if [ X"$_r_act" == X"-" ]; then
		echo "[ ] removing rule ${_r_key}"
		grep -v "^${_r_key}:" ${_sqnew} > tmp.$$ && mv tmp.$$ ${_sqnew}
	elif [ X"$_r_act" == X"+" ]; then
		echo "[ ] adding rule ${_r_key}"
		echo "${_r_key}:0:0:0:?::" >> ${_sqnew}
	fi
done
sort ${_sqnew} > ${_sqdat}

rm -rf ${_tmpdir}
