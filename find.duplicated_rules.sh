#!/bin/sh
_outdir='build'
cd $(dirname $0) && cd ${_outdir}
grep '<rule key=' rules*.xml | cut -d '"' -f 2 | sort | uniq -c | sort -n | awk '{ print $1 " " $2 }' | grep -v "^1 "
