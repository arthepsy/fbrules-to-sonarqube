#!/bin/sh
_appname='fb2sq'
_sqrules='sq_rules.dat'

_cdir=$(cd -- "$(dirname "$0")" && pwd)
. ${_cdir}/ar.utils.sh

if [ X"$1" = X"" ]; then
	_err "usage: $0 <sonar-findbugs-dir>"
fi

_chkdir "$1"
_sqfbdir=$(_getdir "$1/decoy")

_dir1="${_sqfbdir}/src/main/resources/org/sonar/plugins/findbugs"
_dir2="${_sqfbdir}/src/main/resources/org/sonar/l10n"

_fb_rules="${_dir1}/rules.xml"
_fb_props="${_dir2}/findbugs.properties"
_fb_profile="${_dir1}/profile-findbugs.xml"

_chkdir "${_dir1}" "${_dir2}"
_chkfile "${_fb_rules}" "${_fb_props}" "${_fb_profile}"

_tmpdir=$(_gettmpdir)
_clean() {
	rm -rf "${_tmpdir}"
}
_trap '_clean' 0

export LC_ALL=C
_out "updating rule order"
_tmp="${_tmpdir}/tmp.$$"
_order=$(grep "key=" "${_fb_rules}" | cut -d '"' -f 2 | cat -n | awk '{ print $1 ":" $2 }')
for i in ${_order}; do
	_nr=$(echo $i | cut -d ':' -f 1)
	_rk=$(echo $i | cut -d ':' -f 2)
	sed -e "s/$_rk:\([0-9]*\):/${_rk}:${_nr}:/" "${_sqrules}" > "${_tmp}" && mv "${_tmp}" "${_sqrules}" 
done

# -- properties order
_out "updating properties order"
_order=$(cut -d '.' -f 3 "${_fb_props}" | cat -n | awk '{ print $1 ":" $2 }')
for i in ${_order}; do
	_nr=$(echo $i | cut -d ':' -f 1)
	_rk=$(echo $i | cut -d ':' -f 2)
	sed -e "s/$_rk:\([0-9]*\):\([0-9]*\):/${_rk}:\1:${_nr}:/" "${_sqrules}" > "${_tmp}" && mv "${_tmp}" "${_sqrules}" 
done

# -- profile order
_out "updating profile order"
_order=$(grep "pattern=" "${_fb_profile}" | cut -d '"' -f 2 | cat -n | awk '{ print $1 ":" $2 }')
for i in ${_order}; do
	_nr=$(echo $i | cut -d ':' -f 1)
	_rk=$(echo $i | cut -d ':' -f 2)
	sed -e "s/$_rk:\([0-9]*\):\([0-9]*\):\([0-9]*\):/${_rk}:\1:\2:${_nr}:/" "${_sqrules}" > "${_tmp}" && mv "${_tmp}" "${_sqrules}" 
done
