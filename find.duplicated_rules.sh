#!/bin/sh
grep '<rule key=' *.xml | cut -d '"' -f 2 | sort | uniq -c | sort -n
