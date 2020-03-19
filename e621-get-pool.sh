#!/bin/bash
set -e
poolid="$1"
if [[ -z "${poolid}" ]]
then
cat <<EOF
Pool downloader for e621
Part of the https://github.com/prndev/naughty-scripts collection.

Downloaded files are prefixed with their index in the pool to maintain order.

Usage:
  e621-get-pool.sh poolid
  
Example:
  e621-get-pool.sh 1188
EOF
  exit 0
fi
curlopts=(--user-agent 'e621 Pool Downloader/0.0.0 (by prndev on github)')
postids=$(curl --silent "${curlopts[@]}" "https://e621.net/pools.json?limit=1&search[id]=${poolid}" | jq '.[0]|.post_ids|.[]')
number=1
for postid in ${postids}
do
    fileurl=$(curl --silent "${curlopts[@]}" "https://e621.net/posts/${postid}.json" | jq --raw-output '.post|.file|.url')
    destfilename="${number}_${fileurl##*/}"
    if [[ -f "${destfilename}" ]]
    then
        echo "File #${number} already exists."
    else
        echo "Getting file #${number}…"
        curl "${curlopts[@]}" "${fileurl}" > "${destfilename}"
    fi
    number=$((number+1))
done
