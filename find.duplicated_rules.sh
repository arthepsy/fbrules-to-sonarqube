#!/bin/sh
cd $(dirname $0)
grep '<rule key=' rules-*.xml | cut -d '"' -f 2 | sort | uniq -c | sort -n
