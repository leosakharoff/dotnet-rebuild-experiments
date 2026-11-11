#!/bin/bash
#
# Make the lab: an exact export of one Phoenix commit, outside git.
#
#   make-lab.sh STAGE [before|after]
#   make-lab.sh COMMIT
#
# With a stage, for example 3-frontend, the commit comes from
# ../commits.txt: the stage's "after" commit, or its "before" commit.
#
# Deletes the lab, makes it again as an empty folder, and unpacks the
# commit into it with git archive, without .claude/. Writes the commit's
# full id and its time (seconds since 1970) to LAB.commit, beside the lab
# and not in it, so it never reaches a build. rt.sh reads that file: it
# records the commit with every run, and passes the time to the builds,
# which pack the zips with it as the release jobs do (stages 4 and 6).
#
# The folder is new and empty, so the lab holds exactly the commit's files
# and nothing else. labcheck.py is not needed after this.
#
# You can set:
#
#   REPO  the Phoenix repository (default ~/Dev/Weel-Sandvig/WS.Phoenix-repro)
#   LAB   the lab (default /private/tmp/rb1-phoenix)

# Stop at the first command that fails, also inside a pipe (pipefail), and
# at any variable that is not set.
set -euo pipefail

usage() {
    echo "usage: make-lab.sh STAGE [before|after]   or   make-lab.sh COMMIT" >&2
    exit 1
}

[ $# -ge 1 ] && [ $# -le 2 ] || usage
REPO=${REPO:-$HOME/Dev/Weel-Sandvig/WS.Phoenix-repro}
LAB=${LAB:-/private/tmp/rb1-phoenix}

# A stage's name is looked up in commits.txt. Anything else is a commit.
table=$(realpath "$(dirname "$0")/..")/commits.txt
if awk -v s="$1" '$1 == s { found = 1 } END { exit !found }' "$table"; then
    which=${2:-after}
    wanted=$(awk -v s="$1" -v w="$which" '$1 == s && $2 == w { print $3 }' "$table")
    if [ -z "$wanted" ]; then
        echo "make-lab.sh: commits.txt has no \"$which\" commit for $1" >&2
        exit 1
    fi
else
    [ $# -eq 1 ] || usage
    wanted=$1
fi

# The commit's full id and time. Stops here if there is no such commit.
commit=$(git -C "$REPO" rev-parse --verify "$wanted^{commit}")
time=$(git -C "$REPO" log -1 --format=%ct "$commit")

# The commit file goes first, so a failed export leaves none behind.
rm -rf "$LAB.commit" "$LAB"
mkdir "$LAB"
git -C "$REPO" archive "$commit" -- . ':(exclude).claude' | tar -x -C "$LAB"
echo "$commit $time" > "$LAB.commit"

echo "$LAB: $(find "$LAB" -type f | wc -l) files from $commit"
