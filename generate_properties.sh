#!/bin/sh
_outdir='build'
_properties_src=${_outdir}'/findbugs-*.properties'
_properties=${_outdir}'/findbugs.properties'

cd $(dirname $0) && mkdir -p ${_outdir}
cat /dev/null > ${_properties} 
for i in `ls ${_properties_src}`; do
       cat $i >> ${_properties}
done
