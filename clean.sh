#!/bin/sh
_outdir='build'
_cdir=$(cd -- "$(dirname "$0")" && pwd)
cd -- "${_cdir}"
rm -rf "${_outdir}"

