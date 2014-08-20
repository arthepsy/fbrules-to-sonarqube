#!/bin/sh
cd $(dirname $0)
./convert.findbugs.sh ../findbugs/
./convert.fbcontrib.sh ../fb-contrib/
./convert.findsecbugs.sh ../find-sec-bugs/
