#!/bin/bash

ARGS="$@"

TIME=""	# any time format `date` understands

# read parameters
while getopts lt: OPT
do
	case "$OPT" in
	t)	# set start time
		TIME="$OPTARG"
		echo "Will always execute at ${TIME} until you stop me."
		;;
	esac
done
shift $(($OPTIND -1))


function waitForStartTime(){
	if [ -z "${TIME}" ]; then return; fi
	
	# check start time
	TS_START=$(date -d $TIME +%s)
	until [ $(date -d 'now' +%s) -eq $TS_START ]; do
		echo -e "Next start time is set to ${TIME}, now it is $(date), waiting…\033[1A"	# that foobar at the end is moving the cursor one line up after printing text
		sleep 0.3
		TS_START=$(date -d $TIME +%s)
	done
	echo
	echo "Now it is $(date), starting…"
}

waitForStartTime

# exit when any command fails
set -e
# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
trap 'echo; echo "\"${last_command}\" command filed with exit code $?."' EXIT


LOGFILE="logs/$(date +%Y%m%d-%H%M)_downloadAndUpdate.log"

# make sure to work on the newest code
git co main
git pull | tee -a $LOGFILE

# merge with newer site data possibly generated on different machine 
# remaining problem: plots contain the time so they will always be rewritten.
# (Perhaps also differing matplotlib different PNG binaries?)
# --> Either do NOT often switch machines ... or remove the time from the plots?
cd ../cov19de
echo $(pwd) | tee -a ../covviz/$LOGFILE
git pull | tee -a ../covviz/$LOGFILE

# come back to code repo
cd ../covviz
echo $(pwd) | tee -a $LOGFILE

# python dependencies, enter and log source folder
source ~/.bashrc && conda activate covh
cd src
echo $(pwd) | tee -a ../$LOGFILE

# the whole shebang
# remove the unbuffer command OR install unbuffer for this to work:    sudo apt install expect
PYTHONUNBUFFERED=1 python downloadAndUpdate.py | tee -a ../$LOGFILE

echo done.
cd ..

# restart waiting for next run, if time has been given
if [ -n "${TIME}" ]; then 
	exec $0 ${ARGS} 
fi


