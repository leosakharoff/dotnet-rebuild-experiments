#!/bin/bash
#
# Make the lab: an exact export of one Phoenix commit, outside git.
#
#   make-lab.sh COMMIT
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

if [ $# -ne 1 ]; then
    echo "usage: make-lab.sh COMMIT" >&2
    exit 1
fi
REPO=${REPO:-$HOME/Dev/Weel-Sandvig/WS.Phoenix-repro}
LAB=${LAB:-/private/tmp/rb1-phoenix}

# The commit's full id and time. Stops here if there is no such commit.
commit=$(git -C "$REPO" rev-parse --verify "$1^{commit}")
time=$(git -C "$REPO" log -1 --format=%ct "$commit")

# The commit file goes first, so a failed export leaves none behind.
rm -rf "$LAB.commit" "$LAB"
mkdir "$LAB"
git -C "$REPO" archive "$commit" -- . ':(exclude).claude' | tar -x -C "$LAB"
echo "$commit $time" > "$LAB.commit"

echo "$LAB: $(find "$LAB" -type f | wc -l) files from $commit"
