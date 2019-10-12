#!/usr/bin/env bash

SERVER_NAME='s76'

# rsync python files to server
echo RSyncing python files to ${SERVER_NAME}
rsync --verbose --recursive --stats ./templates ${SERVER_NAME}:/home/ph/WikiNeighbors
rsync --verbose --recursive --stats ./static ${SERVER_NAME}:/home/ph/WikiNeighbors
rsync --verbose --recursive --stats ./wikineighbors ${SERVER_NAME}:/home/ph/WikiNeighbors
rsync --verbose --recursive --stats ./app.py ${SERVER_NAME}:/home/ph/WikiNeighbors

ssh -X ${SERVER_NAME} <<- EOF
    APP_PID=\$(lsof -i:5000 -t)
    if [ \${APP_PID:-0} -gt 0 ]
    then
        echo Killing Wikineighbors on port 5000.
        kill -9  \${APP_PID}
    fi
    cd /home/ph/WikiNeighbors
    python3.6 app.py  --no-debug --s76
EOF
