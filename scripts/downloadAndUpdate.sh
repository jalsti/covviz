#!/bin/bash

ARGS="$@"

TIME=""	# any time format `date` understands, used in waitForStartTime()
PROJECT_DIR=$(realpath $(dirname ${0})/..)
WWW_REPO_PATH=$(realpath ${PROJECT_DIR}/../cov19de)

# read parameters
while getopts vt: OPT
do
	case "$OPT" in
	t)	# set start time
		TIME="$OPTARG"
		echo "Will always execute at ${TIME} until you stop me."
		;;
	v)	# verbose
		set -x
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

cd ${PROJECT_DIR}

# exit when any command fails
set -e
# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
trap 'echo; echo "\"${last_command}\" command failed with exit code $?."' EXIT


LOGFILE="${PROJECT_DIR}/logs/$(date +%Y%m%d-%H%M)_downloadAndUpdate.log"

pwd |& tee -a ${LOGFILE}


# make sure to work on the newest code
git co main
git pull |& tee -a ${LOGFILE}

# merge with newer site data possibly generated on different machine 
# remaining problem: plots contain the time so they will always be rewritten.
# (Perhaps also differing matplotlib different PNG binaries?)
# --> Either do NOT often switch machines ... or remove the time from the plots?
cd ${WWW_REPO_PATH} 
pwd |& tee -a ${LOGFILE}
git co master
git pull |& tee -a ${LOGFILE}

# come back to code repo
cd - |& tee -a ${LOGFILE}

# python dependencies, enter and log source folder
source ~/.bashrc && conda activate covh
cd ${PROJECT_DIR}/src
pwd |& tee -a ${LOGFILE}

# the whole shebang
# remove the unbuffer command OR install unbuffer for this to work:    sudo apt install expect
python --version |& tee -a ${LOGFILE}
PYTHONUNBUFFERED=1 python downloadAndUpdate.py |& tee -a ${LOGFILE}

echo done work. |& tee -a ${LOGFILE}
cd - |& tee -a ${LOGFILE}
set +e |& tee -a ${LOGFILE}

if which hardlink; then
	echo trying to save storage space through hard-linking PNG and CSV files |& tee -a ${LOGFILE}
	hardlink -v ${WWW_REPO_PATH} ${PROJECT_DIR} -i ".*csv|png$" |& tee -a ${LOGFILE}
fi

# restart waiting for next run, if time has been given
if [ -n "${TIME}" ]; then 
	exec $0 ${ARGS} 
fi


