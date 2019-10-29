#!/usr/bin/env bash


echo Running cromwell server.
cat cromwell.conf
echo Local environment: $(ls -latrh)
java -Dconfig.file=cromwell.conf -jar cromwell.jar server
