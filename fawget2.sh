#!/bin/bash
# settings
onexists="quit"
#onexists="continue"
cookies="cookies.txt"
# these should not be changed
gallery="$1" # must not begin or end with slash
if [[ -z "${gallery}" ]]
then
cat <<EOF
Downloader for FurAffinity
Part of the https://github.com/prndev/naughty-scripts collection.

Usage:
  fawget2.sh gallery [destination directory]

If destination directory is omitted, it is automatically inferred from the gallery name.
You need to log into FurAffinity first and export your session cookie into a file named cookies.txt in the working directory.

Example:
  fawget2.sh gallery/roanoak/folder/205224/Safeword Downloads/Safeword
EOF
  exit 0
fi
if [[ ! -r "${cookies}" ]]
then
  echo "Error: Cannot read ${cookies}."
  exit 1
fi
wgetopts=(--load-cookies "${cookies}" --keep-session-cookies --save-cookies "${cookies}")
baseurl="https://www.furaffinity.net"
destdir="$2"
if [[ -z "${destdir}" ]]
then
    destdir="Downloads/${gallery##*/}"
    echo "Auto-generated destination directory ${destdir}."
    mkdir -p "${destdir}"
fi
prevpage="0"
page="1"
while [[ ${prevpage} -le ${page} ]]
do
    # get index
    echo ${baseurl}/${gallery}/${page}/
    index=$(wget --quiet "${wgetopts[@]}" "${baseurl}/${gallery}/${page}/" -O -)
    
    for viewid in $(echo "${index}" | grep -Po '(?<=/view/)[^/]+' | uniq)
    do
        # get view
        echo ${baseurl}/view/${viewid}/
        viewpage=$(wget --quiet "${wgetopts[@]}" "${baseurl}/view/${viewid}" -O -)
        
        # get file source url
        fileurl="https:"$(echo "${viewpage}" | grep -Po '[^"]+(?=">Download</a>)' | head -n 1)
        # infer target file name
        destfilename="${destdir}/${fileurl##*/}"
        # check for existence
        if [[ -f "${destfilename}" ]]
        then
            echo "File ${destfilename} already exists."
            if [[ "${onexists}" == "quit" ]]
            then
                echo "Quitting as requested…"
                exit 0
            fi
        else
            # do download
            wget --no-clobber --no-verbose --show-progress "${fileurl}" -O "${destfilename}"
        fi
        
        #perl -0e '<div class="submission-description.*?</div>'
    done
    
    prevpage=${page}
    page=$(echo "${index}" | grep -Po "(?<=/${gallery}/)[^/\"]+" | tail -n 1)
done
