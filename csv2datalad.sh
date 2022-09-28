#!/usr/bin/env bash

###
# CDI = "cryo data ingest"

###
# Expected CSV format
#
# URL,filename
# https://path/to/file1.ext,file1.ext
# https://path/to/file2.ext,file2.ext

set -o nounset
set -o pipefail
set -o errexit
# set -o errtrace

PROGNAME=$(basename $0)
red='\033[0;31m'; orange='\033[0;33m'; green='\033[0;32m'; yellow='\033[0;93m'; nc='\033[0m' # No Color
log_info() { echo -e "${green}[$(date --iso-8601=seconds)] [INFO] [${PROGNAME}] ${@}${nc}"; }
log_warn() { echo -e "${orange}[$(date --iso-8601=seconds)] [WARN] [${PROGNAME}] ${@}${nc}"; }
log_err() { echo -e "${red}[$(date --iso-8601=seconds)] [ERR] [${PROGNAME}] ${@}${nc}" >&2; }
log_debug() { if [[ ${debug:-} == 1 ]]; then echo -e "${yellow}[$(date --iso-8601=seconds)] [DEBUG] [${PROGNAME}] ${@}${nc}"; fi }
err_exit() { echo -e "${red}[$(date --iso-8601=seconds)] [ERR] [${PROGNAME}] ${@:-"Unknown Error"}${nc}" >&2; exit 1; }

trap ctrl_c INT # trap ctrl-c and call ctrl_c()
function ctrl_c() {
  MSG_WARN "Caught CTRL-C"
  MSG_WARN "Killing process"
  MSG_WARN "No cleanup done..."
  kill -term $$ # send this program a terminate signal
}

function print_usage() { cat <<EOF
csv2datalad.sh -c csvfile -d datalad_dir [-h|--help] [--debug] [-v]
  -c|--csvfile:      Input CSV file [FORMAT: URL,filename]
  -d|--datalad_dir:  Directory where to build dataset
  -v|--verbose:      Print verbose messages during processing
  -h|--help:         Print this help
  --debug:           Print debugging messages
EOF
}

# check dependencies
function check_shell() {
  if [[ $(which datalad) == "" ]]; then
    err_exit "datalad command not found"
  fi
}


# parse CLI args
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -h|--help)
      print_usage; exit 1;;
    -c|--csvfile)
      csvfile="$2"
      shift # past argument
      shift # past value
      ;;
    -d|--datalad_dir)
      datalad_dir="$2"; shift; shift;;
    --debug)
      debug=1; shift;;
    -v|--verbose)
      verbose=1; set -o xtrace; shift;;
    *)    # unknown option
      positional+=("$1") # save it in an array for later.
      shift;;
  esac
done


### Check inputs, set up environment
if [[ -z ${csvfile:-} ]]; then print_usage; err_exit "-c not set"; else log_debug "CSV file:: ${csvfile}"; fi
if [[ -z ${datalad_dir:-} ]]; then print_usage; err_exit "-d not set"; else log_debug "DATALAD dir: ${datalad_dir}"; fi

# download a dataset into a local datalad repository
function cdi_download() {
  log_info "Running datalad (DRYRUN)..."
  datalad addurls -d ${datalad_dir} -n --fast --nosave  ${csvfile} '{URL}' '{filename}'
  log_info "Running datalad..."
  datalad addurls -d ${datalad_dir} --fast --nosave  ${csvfile} '{URL}' '{filename}'
  log_info "Running datalad..."
  datalad save ${datalad_dir} -m "Created ${datalad_dir}"
}

# Create a GitHub remote and push a local datalad repository to it
function cdi_set_remote() {
  log_info "Creating GitHub repository"
  gh repo create \
     cryo-data/${datalad_dir} \
     -d "${datalad_dir}" \
     --public \
     -s ${datalad_dir}
  # undo: gh repo delete cryo-data/${datalad_dir}
  log_info "Pushing to GitHub"
  (cd ${datalad_dir}; git push -u origin main)
  (cd ${datalad_dir}; datalad push)
}

cdi_download
cdi_set_remote
