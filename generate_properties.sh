#!/bin/sh
_properties='findbugs.properties'
cat /dev/null > ${_properties} 
for i in `ls findbugs-*.properties`; do
       cat $i >> ${_properties}
done
