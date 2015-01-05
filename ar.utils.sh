#!/bin/sh

if [ X"${_ar_utils}" = X"1" ]; then return; else _ar_utils=1; fi

_getdir() { echo $(cd -- "$(dirname "$1")" 2>/dev/null && pwd || echo "/nonexistent"); }
_getfile() { echo "$(_getdir "$1")/$(basename "$1")"; }

_chkdir() {
	for d in "$@"; do
		if [ ! -d "$d" ]; then
			_err "error: directory not found: \"$d\""
		fi
	done
}
_chkfile() {
	for d in "$@"; do
		if [ ! -f "$d" ]; then
			_err "error: file not found: \"$d\""
		fi
	done
}

_gettmpdir() {
	_tmp=$(mktemp -d) || _err "error: could not create temporary directory"
	echo ${_tmp}
	return 0
}


_err() { _out $1 && exit 1; }
_out() {
		if [ X"$1" = X"" ]; then
			return
		fi
		if [ X"${_appname}" != X"" ]; then
			echo -n "[${_appname}] "
		fi
		echo $@
}

_trap() {
	if [ X"$1" = X"" ]; then
		return
	fi
	local _fn=$1
	shift
	local _sig=""
	while [ X"$1" != X"" ]; do
		local _sig="${_sig} $1" && shift;
	done
	local _trap="trap '$_fn ; trap 2 ; kill -2 $$' 1 2 3 13 15"
	if [ X"${_sig}" != X" " ]; then
		local _trap="${_trap}; trap '$_fn' ${_sig}"
	fi
	eval "${_trap}"
}

_args=$@
