#!/bin/bash
#
# run-stage.sh: run reprotest once on the WS.PEMS lab, one stage and one
# axis. Named rt.sh until 16 November 2026.
#
#   run-stage.sh STAGE AXIS [LABEL]
#
# STAGE is a stage's folder next to shared/: 1-build, 2-publish,
# 3-frontend, 4-zip or 5-release. It holds
#
#   build.sh       what each build does. It must write hashes.sha256, a
#                  hash of every file the stage produces.
#   artifacts.txt  what reprotest keeps from each build and compares, one
#                  pattern per line.
#
# AXIS is a reprotest variation (build_path, time, locales, umask,
# exec_path, timezone, environment, home, kernel, aslr, num_cpus), "none"
# to vary nothing, or "all" for every variation that runs here without
# extra setup. LABEL names the run; the default is STAGE-AXIS-COMMIT, for
# example 1-build-none-6b7a3254d.
#
# Make the lab with make-lab.sh first; it records the commit and its time
# beside the lab. OUT must point to a folder for the results. You can also
# set:
#
#   LAB         the lab (default /private/tmp/rb1-phoenix). It must hold no
#               build output.
#   DOTNET_DIR  the SDK folder (default ~/.dotnet). It holds both SDKs the
#               commits ask for, 9.0.120 and 10.0.401; the lab's
#               global.json chooses.
#   NODE_DIR    the Node folder. By default the first of /opt/rb1-node
#               (Node 20.20.2) and /private/tmp/rb1-node22 (Node 22.23.3)
#               that has the version in the frontend's .nvmrc. Commits
#               before 631294806 have no .nvmrc and get /opt/rb1-node.
#   MIN_CPUS    CPUs for the control build (default 2; reprotest's is 1).
#
# The builds get DOTNET_DIR, NODE_DIR and COMMIT_TIME, the commit's time.
#
# Each run gets its own folder, OUT/LABEL, and one row in OUT/summary.tsv:
#
#   command.txt       the exact reprotest command, to repeat the run by hand
#   environment.txt   the commit, the SDK, the compiler's SHA-256, Node and
#                     the tools' versions, written before the run
#   reprotest.log     reprotest's output, and diffoscope's when they differ
#   samples.txt       the dotnet processes, once a second
#   samples-node.txt  the node processes, once a second
#   leftover.txt      .NET servers or node processes alive after the run
#   store/            what reprotest kept: control/, experiment-1/, and
#                     diffoscope's report when they differ
#
# What this script adds around reprotest:
#
# - reprotest starts under env -i with five variables, so the builds do
#   not inherit whatever the starting shell had (reprotest-probe R4).
# - The .NET build servers are stopped before the run. Any compiler server,
#   MSBuild node or node process from our folders still running after it is
#   listed in leftover.txt (W27).
# - sample-dotnet.py records the dotnet and node processes once a second,
#   so we can check afterwards that the variation reached them.
#
# The user_group axis needs a second user (rb1b) and is not run here. The
# runs up to 21 October did it with experiments/phoenix-rt/run.sh in
# Speciale2026.
#
# Written 9 November 2026 to replace run.sh, run-readable.sh and
# 3-frontend/run.sh with one driver and one build.sh per stage.

# No set -e: when a build fails or reprotest finds a difference, the run
# must still be written down in summary.tsv.
set -u

usage() {
    echo "usage: run-stage.sh STAGE AXIS [LABEL]" >&2
    exit 1
}

die() {
    echo "run-stage.sh: $*" >&2
    exit 2
}

# The first 16 characters of a file's SHA-256, or - if there is no file.
short_hash() {
    if [ -f "$1" ]; then
        sha256sum < "$1" | cut -c1-16
    else
        echo -
    fi
}

[ $# -ge 2 ] || usage
stage=$(basename "$1")
axis=$2

if [ -z "${OUT:-}" ]; then
    echo "run-stage.sh: set OUT to a private data folder" >&2
    exit 1
fi
# fish keeps the ~ in "env OUT=~/..." as it is, and the results would
# land in a folder named ~ under the current one.
case $OUT in
"~"*) die "OUT starts with ~, which fish does not expand after =; use \$HOME" ;;
esac
# Absolute, because the run itself starts from inside the lab.
OUT=$(realpath -m "$OUT")
LAB=${LAB:-/private/tmp/rb1-phoenix}
MIN_CPUS=${MIN_CPUS:-2}

# make-lab.sh writes the commit and its time beside the lab.
[ -f "$LAB.commit" ] || die "no $LAB.commit; make the lab with make-lab.sh"
read -r commit commit_time < "$LAB.commit"
[ -n "${commit_time:-}" ] || die "$LAB.commit has no commit time; make the lab again with make-lab.sh"
label=${3:-$stage-$axis-${commit:0:9}}
run=$OUT/$label
store=$run/store

# The scripts/ folder, one level up from this file.
scripts=$(realpath "$(dirname "$0")/..")
build=$scripts/$stage/build.sh
[ -f "$build" ] || die "no $build"
[ -f "$scripts/$stage/artifacts.txt" ] || die "no $scripts/$stage/artifacts.txt"
# The patterns from artifacts.txt on one line, without the comments.
artifacts=$(grep -v '^#' "$scripts/$stage/artifacts.txt" | tr '\n' ' ')
reprotest=$(command -v reprotest) || die "reprotest is not on PATH"

case $axis in
none)
    vary=--vary=-all
    ;;
all)
    # Leave out the ones that can't run here without extra setup.
    vary=--vary=+all,-user_group,-fileordering,-domain_host
    ;;
user_group)
    die "user_group needs a second user and is not run here; see the top of run-stage.sh"
    ;;
*)
    vary=--vary=-all,+$axis
    ;;
esac

app=$LAB/src/WebAPI/ClientApp
for dir in "$LAB"/bin "$LAB"/obj "$LAB"/release "$LAB"/publish "$LAB"/hashes.sha256 \
           "$LAB"/bundles "$LAB"/assets "$LAB"/dotnet-cli-home \
           "$LAB"/src/*/bin "$LAB"/src/*/obj "$LAB"/tests/bin "$LAB"/tests/obj \
           "$app"/node_modules "$app"/.next "$app"/out; do
    if [ -e "$dir" ]; then
        die "the lab holds build output ($dir); make it again with make-lab.sh"
    fi
done
if [ -e "$run" ]; then
    die "$run exists"
fi

# The SDK that the lab's global.json asks for. Stops here if DOTNET_DIR
# does not have it.
DOTNET_DIR=$(realpath -s "${DOTNET_DIR:-$HOME/.dotnet}")
sdk=$(cd "$LAB" && env DOTNET_ROOT="$DOTNET_DIR" DOTNET_CLI_HOME=/tmp/dch DOTNET_NOLOGO=1 \
      "$DOTNET_DIR/dotnet" --version 2> /dev/null) ||
    die "$DOTNET_DIR has no SDK for the lab's global.json"

# The Node that the frontend's .nvmrc asks for, and the folder that has it.
if [ -f "$app/.nvmrc" ]; then
    node=
    for dir in ${NODE_DIR:-/opt/rb1-node /private/tmp/rb1-node22}; do
        if [ "$("$dir/bin/node" --version 2> /dev/null)" = "v$(cat "$app/.nvmrc")" ]; then
            NODE_DIR=$dir
            node=$(cat "$app/.nvmrc")
            break
        fi
    done
    [ -n "$node" ] || die "no Node $(cat "$app/.nvmrc") in ${NODE_DIR:-/opt/rb1-node or /private/tmp/rb1-node22}"
else
    NODE_DIR=${NODE_DIR:-/opt/rb1-node}
    node="$("$NODE_DIR/bin/node" --version 2> /dev/null) (no .nvmrc)"
fi
NODE_DIR=$(realpath -s "$NODE_DIR")

# reprotest itself starts with only these variables.
launch=(env -i HOME="$HOME" USER="$USER" LOGNAME="$LOGNAME" SHELL=/bin/bash
        PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin")

# What reprotest runs as each build, inside its copy of the lab.
cmd="env DOTNET_DIR=$DOTNET_DIR NODE_DIR=$NODE_DIR COMMIT_TIME=$commit_time bash $build"

stop_servers() {
    env DOTNET_ROOT="$DOTNET_DIR" DOTNET_CLI_HOME=/tmp/dch DOTNET_NOLOGO=1 \
        "$DOTNET_DIR/dotnet" build-server shutdown > /dev/null
}

mkdir -p "$run"
printf '%s\n' "${launch[*]}" "$vary --min-cpus $MIN_CPUS" "$cmd" "$artifacts" > "$run/command.txt"

# What measured, written before the measurement. diffoscope is looked up
# with reprotest's own PATH, so it is the one reprotest will call.
{
    echo "commit      $commit, $(date -u -d "@$commit_time" +%Y-%m-%dT%H:%M:%SZ)"
    echo "lab         $LAB"
    echo "sdk         $sdk in $DOTNET_DIR"
    echo "csc.dll     $(sha256sum < "$DOTNET_DIR/sdk/$sdk/Roslyn/bincore/csc.dll" | cut -d' ' -f1)"
    echo "node        $node in $NODE_DIR"
    echo "reprotest   $(pipx list --short 2> /dev/null | sed -n 's/^reprotest //p') at $reprotest"
    echo "diffoscope  $("${launch[@]}" diffoscope --version)"
    echo "kernel      $(uname -srm)"
    echo "machine     $(hostname)"
} > "$run/environment.txt"

# From inside the lab, so its global.json chooses the SDK.
cd "$LAB" || exit 1
stop_servers

# Record the dotnet and node processes once a second while reprotest runs.
DOTNET_EXE=$DOTNET_DIR/dotnet python3 "$scripts/shared/sample-dotnet.py" "$run/samples.txt" &
sampler=$!
DOTNET_EXE=$NODE_DIR/bin/node python3 "$scripts/shared/sample-dotnet.py" "$run/samples-node.txt" &
node_sampler=$!

start=$(date +%Y-%m-%dT%H:%M)
start_s=$(date +%s)
timeout 7200 "${launch[@]}" "$reprotest" -v --min-cpus "$MIN_CPUS" --store-dir "$store" \
    "$vary" -c "$cmd" "$LAB" "$artifacts" > "$run/reprotest.log" 2>&1
status=$?
minutes=$(awk -v s="$start_s" -v e="$(date +%s)" 'BEGIN { printf "%.1f", (e - s) / 60 }')
kill $sampler $node_sampler
stop_servers

# A compiler server, MSBuild node or node process from our folders still
# running now has survived the builds, and could have carried state from
# one build into the next. Processes from other folders, such as an
# editor's, never reach the builds and are left out. node is found by its
# executable, because npm's own process is just "node".
{
    pgrep -af -- 'nodemode:|VBCSCompiler' | grep -v JetBrains | grep -F "$DOTNET_DIR/"
    for p in /proc/[0-9]*; do
        if [ "$(readlink "$p/exe" 2> /dev/null)" = "$NODE_DIR/bin/node" ]; then
            echo "${p#/proc/} $(tr '\0' ' ' < "$p/cmdline" | cut -c1-200)"
        fi
    done
} > "$run/leftover.txt"
leftover=$(wc -l < "$run/leftover.txt")

# reprotest exits 0 when the builds are identical, 1 when they differ, and
# 125 when something else went wrong, such as a failed build. timeout
# exits 124 when the two hours are up.
case $status in
0)   result=identical ;;
1)   result=different ;;
124) result=timeout ;;
*)   result="error (exit $status)" ;;
esac

# When reprotest finds no differences, it replaces the experiment's store
# with a link to the control's (R6). Say "link" then, not the control's
# hash again.
control=$(short_hash "$store/control/source-root/hashes.sha256")
if [ -L "$store/experiment-1" ]; then
    experiment=link
else
    experiment=$(short_hash "$store/experiment-1/source-root/hashes.sha256")
fi

# One row per run, under a header the first time.
if [ ! -f "$OUT/summary.tsv" ]; then
    printf 'run\tcommit\taxis\tresult\tstart\tminutes\tcontrol\texperiment\tleftover\n' > "$OUT/summary.tsv"
fi
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$label" "${commit:0:9}" "$axis" "$result" "$start" \
    "$minutes" "$control" "$experiment" "$leftover" >> "$OUT/summary.tsv"
echo "$label: $result (control $control, experiment $experiment, leftover $leftover, $minutes min)"
