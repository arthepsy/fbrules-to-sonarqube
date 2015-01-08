#!/bin/sh
_appname='fb2sq.data'
_sqrules='sq_rules.dat'

if [ X"$1" = X"" ]; then
	echo "usage: $0 <findbugs-dir>"
	exit 1
fi

_cdir=$(cd -- "$(dirname "$0")" && pwd)
. "${_cdir}/ar.utils.sh"

_chkdir "$1"
_sdir=$(_getfile "$1/findbugs/etc")
_fbmsg="${_sdir}/messages.xml"
_fbrls="${_sdir}/findbugs.xml"
_sqdat="${_cdir}/sq_rules.dat"

_chkdir "${_sdir}"
_chkfile "${_fbmsg}" "${_sqdat}"

_tmpdir=$(_gettmpdir)
_clean() {
	rm -rf "${_tmpdir}"
}
_trap '_clean' 0

_sqnew="${_tmpdir}/sq_rules.dat"
_tmpfbr="${_tmpdir}/fb.rules"
_tmpfbm="${_tmpdir}/fb.messages"
_tmpsqr="${_tmpdir}/sq.rules"
_tmptmp="${_tmpdir}/tmp.$$"

export LC_ALL=C
cp "${_sqdat}" "${_sqnew}"
grep "<BugPattern type=" "${_fbmsg}" | cut -d '"' -f 2 | sort > "${_tmpfbm}"
grep "<BugPattern abbrev=" "${_fbrls}" | cut -d '"' -f 4 | sort > "${_tmpfbr}"
grep -v "^#" "${_sqdat}" | cut -d ':' -f 1 | sort > "${_tmpsqr}"
for diff in $(diff -ruN "${_tmpsqr}" "${_tmpfbm}" | tail -n +3 | grep "^[\+-]"); do
	_r_act=$(echo $diff | cut -c -1)
	_r_key=$(echo $diff | cut -c 2-)
	_r_old=$(grep -q "^${_r_key}$" "${_tmpfbr}" || echo '1')
	if [ X"${_r_act}" = X"-" ]; then
		_out "removing rule ${_r_key}"
		grep -v "^${_r_key}:" "${_sqnew}" > "${_tmptmp}" && mv "${_tmptmp}" "${_sqnew}"
	elif [ X"$_r_act" = X"+" ]; then
		if [ X"${_r_old}" = X"1" ]; then
			_out "warning: rule ${_r_key} only in messages (not adding)"
		else
			_out "adding rule ${_r_key}"
			echo "${_r_key}:0:0:0:?::" >> "${_sqnew}"
		fi
	fi
done
sort "${_sqnew}" > "${_sqdat}"
