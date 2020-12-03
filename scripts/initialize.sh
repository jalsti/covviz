#!/bin/bash

#!/bin/bash

# exit when any command fails
set -e
# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
trap 'echo; echo "\"${last_command}\" command filed with exit code $?."' EXIT


LOGFILE="logs/$(date +%Y%m%d-%H%M)_initialize.log"

# make sure to work on the newest code
echo $(pwd) | tee -a $LOGFILE
git pull | tee -a $LOGFILE

# python dependencies, enter and log source folder
#~ source  ./py3science/bin/activate
source ~/.bashrc && conda activate covh
cd src
echo $(pwd) | tee -a ../$LOGFILE


# download databases, scrape pages, generate distances - and make all pages and pics once
echo ... | tee -a ../$LOGFILE
echo python initialize.py | tee -a ../$LOGFILE

#~ unbuffer python initialize.py | tee -a ../$LOGFILE
PYTHONUNBUFFERED=1 python initialize.py | tee -a ../$LOGFILE


