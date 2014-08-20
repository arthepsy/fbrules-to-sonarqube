#!/bin/sh
_properties='findbugs.properties'

cd $(dirname $0)
cat /dev/null > ${_properties} 
for i in `ls findbugs-*.properties`; do
       cat $i >> ${_properties}
done
