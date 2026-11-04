#!/bin/bash
#
# Run reprotest once on the Phoenix lab, varying one axis.
#
#   run.sh LAYER AXIS [LABEL]
#
# This is a readable copy of ../phoenix-rt/run.sh as of e9e84397
# (14 October 2026). It gives reprotest the same command.
#
# LAYER is what each build does:
#
#   1  dotnet build of the two programs.
#   2  What the release job does: a locked restore and both publishes.
#   R  The whole release: the frontend first, then layer 2, which copies
#      the frontend's out/ into wwwroot/. Before layer 2 the frontend's
#      node_modules and .next are removed, because CI's publish job only
#      gets out/.
#   Z  Layer R, then the release zips, made twice: as CI makes them
#      (zip -r) in release/zip-ci, and normalised in release/zip-norm
#      (modes 755 or 644 from the owner's x bit, every time set to ZEPOCH,
#      names sorted, no extra fields, TZ=UTC).
#   W  The Windows release as the Windows job builds it, but on Linux and
#      unsigned: the frontend, a locked restore, the three win-x64
#      publishes, the migrator copied as the job copies it, and both zips
#      packed with the commit's own scripts/pack-release-zip.sh. No Linux
#      publish.
#
# AXIS is a reprotest variation (build_path, time, locales, umask,
# exec_path, timezone, environment, home, kernel, aslr, num_cpus,
# domain_host, user_group), or "none" to vary nothing, or "all" for every
# variation that runs here without extra setup. LABEL names the output
# files; the default is L<LAYER>-<AXIS>.
#
# OUT must point to a folder for the results. You can also set:
#
#   MIN_CPUS    CPUs for the control build (default 2; reprotest's is 1).
#   LAB         the lab (default /private/tmp/rb1-phoenix). It must hold no
#               build output.
#   FIXENV      a VAR=VALUE that goes in front of every dotnet and npm
#               command, for example FIXENV=LC_ALL=C.UTF-8.
#   DOTNET_DIR  the SDK folder (default /home/leos/.dotnet, SDK 9.0.120).
#               For .NET 10: /private/tmp/rb1-dotnet10/sdk (SDK 10.0.401).
#   NODE_DIR    the Node folder for R, Z and W (default /opt/rb1-node,
#               Node 20.20.2). After the merge of main (13/10):
#               /private/tmp/rb1-node22 (Node 22.23.3).
#   VER         the version flags for the publishes (default the two /p:
#               flags for v0.0.0-thesis). From 5031c5af the release sets
#               APP_VERSION instead: use VER= and put APP_VERSION in FIXENV.
#   ZEPOCH      Z and W only: the time for the zips, for example the
#               commit's time (git log -1 --format=%ct).
#
# How each build is protected:
#
# - reprotest starts under env -i with five variables only. The builds
#   inherit reprotest's environment, so without this they would get
#   whatever the starting shell had (reprotest-probe R4).
# - Every build starts and ends with "dotnet build-server shutdown", and
#   MSBuild's node reuse is off, so no compiler server or MSBuild node lives
#   on from one build into the next (W27). Anything still running after the
#   run is listed in leftover-LABEL.txt.
# - sample-dotnet.py samples the dotnet processes during the run, so we can
#   check that the variation reached them.
# - Each build writes a list of file modes, because reprotest compares only
#   contents.
#
# AXIS=user_group runs the experiment build as rb1b (see
# setup-user-group.sh). rb1b can't read /home/leos, so both builds then use
# the SDK copy in /opt/rb1-dotnet, and a second sampler runs as rb1b.

set -u

usage() {
    echo "usage: run.sh LAYER AXIS [LABEL]" >&2
    exit 1
}

die() {
    echo "run.sh: $*" >&2
    exit 2
}

short_hash() {
    if [ -f "$1" ]; then
        sha256sum < "$1" | cut -c1-16
    else
        echo -
    fi
}

[ $# -ge 2 ] || usage
layer=$1
axis=$2
label=${3:-L$layer-$axis}

if [ -z "${OUT:-}" ]; then
    echo "run.sh: set OUT to a private data folder" >&2
    exit 1
fi
MIN_CPUS=${MIN_CPUS:-2}
FIXENV=${FIXENV:-}
LAB=${LAB:-/private/tmp/rb1-phoenix}

experiments=$(cd "$(dirname "$0")/.." && pwd)
reprotest=/home/leos/.local/bin/reprotest
store=$OUT/store-$label
shared=/private/tmp/rb1-shared

dotnet_root=${DOTNET_DIR:-/home/leos/.dotnet}
node_root=${NODE_DIR:-/opt/rb1-node}
modes_dir=$OUT/modes

case $axis in
none)
    vary=(--vary=-all)
    ;;
all)
    # Leave out the ones that can't run here without extra setup.
    vary=(--vary=+all,-user_group,-fileordering,-domain_host)
    ;;
user_group)
    vary=(--vary=-all,+user_group --vary=user_group.available+=rb1b:rb1b)
    dotnet_root=/opt/rb1-dotnet
    modes_dir=$shared/modes
    ;;
*)
    vary=("--vary=-all,+$axis")
    ;;
esac

# reprotest itself starts with only these variables.
launch=(env -i HOME="$HOME" USER="$USER" LOGNAME="$LOGNAME" SHELL=/bin/bash
        PATH=/home/leos/.local/bin:/usr/local/bin:/usr/bin)

# Goes in front of every dotnet command. \$PATH is expanded later, by the
# shell that runs the command, not here.
dotnet_env="env DOTNET_ROOT=$dotnet_root PATH=$dotnet_root:\$PATH DOTNET_CLI_HOME=/tmp/dch DOTNET_NOLOGO=1 MSBUILDDISABLENODEREUSE=1"
if [ -n "$FIXENV" ]; then
    dotnet_env="$dotnet_env $FIXENV"
fi
stop_servers="$dotnet_env dotnet build-server shutdown > /dev/null"
version=${VER-'/p:Version=0.0.0-thesis /p:InformationalVersion=v0.0.0-thesis'}

# Goes in front of every npm command.
node_env="env PATH=$node_root/bin:\$PATH CI=true npm_config_cache=/private/tmp/rb1-npm npm_config_update_notifier=false NEXT_TELEMETRY_DISABLED=1"
if [ -n "$FIXENV" ]; then
    node_env="$node_env $FIXENV"
fi

tag=v0.0.0-thesis
zip=/private/tmp/rb1-tools/zip
linux_dirs='ws-pems-linux-x64 ws-pems-job-worker-linux-x64'
windows_dirs='ws-pems-win-x64 ws-pems-job-worker-win-x64'

# Layer 2: the release job's restore and the two Linux publishes.
linux_publish="$dotnet_env dotnet restore ./WS.Phoenix.sln --locked-mode $version"
linux_publish="$linux_publish && $dotnet_env dotnet publish ./src/WebAPI/WebAPI.csproj -c Release -o ./release/ws-pems-linux-x64 -r linux-x64 --self-contained true --no-restore /p:SkipSpaBuild=true $version"
linux_publish="$linux_publish && $dotnet_env dotnet publish ./src/BackgroundJobExecutor/BackgroundJobExecutor.csproj -c Release -o ./release/ws-pems-job-worker-linux-x64 -r linux-x64 --self-contained true --no-restore $version"

# The frontend's static export into ClientApp/out. Then remove what CI's
# publish job does not get.
frontend="( cd src/WebAPI/ClientApp && $node_env npm ci --offline --no-audit --no-fund && $node_env npm run build && rm -rf node_modules .next )"

# Layer R: the whole Linux release.
release="$frontend && $linux_publish"

# Layer W: the Windows job's restore, its three publishes and the
# migrator's copy.
windows_publish="$dotnet_env dotnet restore ./WS.Phoenix.sln --locked-mode $version"
windows_publish="$windows_publish && $dotnet_env dotnet publish ./src/WebAPI/WebAPI.csproj -c Release -o ./release/win/ws-pems-win-x64 -r win-x64 --self-contained true --no-restore /p:SkipSpaBuild=true $version"
windows_publish="$windows_publish && $dotnet_env dotnet publish ./src/BackgroundJobExecutor/BackgroundJobExecutor.csproj -c Release -o ./release/win/ws-pems-job-worker-win-x64 -r win-x64 --self-contained true --no-restore $version"
windows_publish="$windows_publish && $dotnet_env dotnet publish ./src/DbMigrator/DbMigrator.csproj -c Release -o ./publish/migrator-win -r win-x64 --self-contained true --no-restore $version"
windows_publish="$windows_publish && cp publish/migrator-win/ws-pems-db-migrator.exe release/win/ws-pems-db-migrator-win-x64-$tag.exe"

case $layer in
1)
    build="$dotnet_env dotnet build src/WebAPI/WebAPI.csproj -c Release -p:SkipSpaBuild=true"
    build="$build && $dotnet_env dotnet build src/BackgroundJobExecutor/BackgroundJobExecutor.csproj -c Release"
    hash_dir='src/*/bin'
    hash_file=bin.sha256
    artifacts='bin.sha256'
    artifacts="$artifacts src/WebAPI/bin/Release/net9.0/*.dll"
    artifacts="$artifacts src/WebAPI/bin/Release/net9.0/*.pdb"
    artifacts="$artifacts src/WebAPI/bin/Release/net9.0/*.json"
    artifacts="$artifacts src/BackgroundJobExecutor/bin/Release/net9.0/BackgroundJobExecutor.*"
    ;;
2)
    build=$linux_publish
    hash_dir=release
    hash_file=release.sha256
    artifacts='release.sha256'
    artifacts="$artifacts release/*/ApplicationCore.* release/*/Infrastructure.*"
    artifacts="$artifacts release/*/WebAPI.* release/*/BackgroundJobExecutor.*"
    artifacts="$artifacts release/*/WebAPI release/*/BackgroundJobExecutor"
    ;;
R)
    build=$release
    hash_dir=release
    hash_file=release.sha256
    artifacts='release.sha256'
    artifacts="$artifacts release/*/ApplicationCore.* release/*/Infrastructure.*"
    artifacts="$artifacts release/*/WebAPI.* release/*/BackgroundJobExecutor.*"
    artifacts="$artifacts release/*/WebAPI release/*/BackgroundJobExecutor"
    artifacts="$artifacts release/ws-pems-linux-x64/wwwroot"
    ;;
Z)
    if [ -z "${ZEPOCH:-}" ]; then
        echo "run.sh: layer Z needs ZEPOCH" >&2
        exit 1
    fi
    # First a hash list of the unzipped release, then both kinds of zip.
    # The \$d parts are expanded inside the build, not here.
    release_hashes="find release -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > release.sha256"
    zip_as_ci="for d in $linux_dirs; do $zip -q -r zip-ci/\$d-$tag.zip \$d/; done"
    normalise="find \$d -type d -exec chmod 755 {} +"
    normalise="$normalise && find \$d -type f -perm -u+x -exec chmod 755 {} +"
    normalise="$normalise && find \$d -type f ! -perm -u+x -exec chmod 644 {} +"
    normalise="$normalise && find \$d -exec touch -h -d @$ZEPOCH {} +"
    zip_normalised="for d in $linux_dirs; do $normalise && find \$d | LC_ALL=C sort | TZ=UTC $zip -q -X -@ zip-norm/\$d-$tag.zip; done"
    build="$release && $release_hashes && cd release && mkdir zip-ci zip-norm && $zip_as_ci && $zip_normalised && cd .."
    hash_dir='release/zip-ci release/zip-norm'
    hash_file=zips.sha256
    artifacts='zips.sha256 release.sha256 release/zip-ci release/zip-norm'
    ;;
W)
    if [ -z "${ZEPOCH:-}" ]; then
        echo "run.sh: layer W needs ZEPOCH" >&2
        exit 1
    fi
    pack="for d in $windows_dirs; do env PATH=/private/tmp/rb1-tools:\$PATH SOURCE_DATE_EPOCH=$ZEPOCH ../../scripts/pack-release-zip.sh \$d ../\$d-$tag.zip; done"
    build="$frontend && $windows_publish && cd release/win && $pack && cd ../.."
    hash_dir=release
    hash_file=release.sha256
    artifacts="release.sha256 release/*.zip release/win/ws-pems-db-migrator-win-x64-$tag.exe"
    ;;
*)
    die "LAYER must be 1, 2, R, Z or W"
    ;;
esac

mkdir -p "$OUT/modes" "$modes_dir"

for dir in "$LAB"/bin "$LAB"/obj "$LAB"/release "$LAB"/src/*/bin "$LAB"/src/*/obj "$LAB"/tests/bin "$LAB"/tests/obj; do
    if [ -e "$dir" ]; then
        die "the lab holds build output ($dir); clean it first"
    fi
done
if [ "$layer" = R ] || [ "$layer" = Z ] || [ "$layer" = W ]; then
    for dir in node_modules .next out; do
        if [ -e "$LAB/src/WebAPI/ClientApp/$dir" ]; then
            die "the lab holds ClientApp/$dir; export it again"
        fi
    done
fi
if [ -e "$store" ]; then
    die "$store exists"
fi

# This is what reprotest runs as each build, control and experiment. It
# writes a hash list (an artifact, so reprotest compares it) and a list of
# file modes (reprotest only compares contents). It runs under sh -e, so we
# keep the build's exit code ourselves and still shut the servers down when
# the build fails. The \$ parts are expanded inside the build, not here.
hashes="find $hash_dir -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > $hash_file"
modes="find $hash_dir -type f -printf '%m %p\n' | LC_ALL=C sort > $modes_dir/$label-\$(umask)-\$\$.txt"
cmd="$stop_servers; rc=0; ( $build && $hashes && $modes ) || rc=\$?; $stop_servers; exit \$rc"

printf '%s\n' "${launch[*]}" "${vary[*]} --min-cpus $MIN_CPUS" "$cmd" "$artifacts" > "$OUT/rt-$label.cmd"

eval "$stop_servers"

# Sample the dotnet processes while reprotest runs, so we can check
# afterwards that the variation really reached them.
DOTNET_EXE=$dotnet_root/dotnet python3 "$experiments/sample-dotnet.py" "$OUT/samples-$label.txt" &
sampler=$!

if [ "$axis" = user_group ]; then
    # NuGet creates its config with mode 0600, so rb1b couldn't read it.
    # It only lists nuget.org.
    chmod 644 /tmp/dch/.nuget/NuGet/NuGet.Config || exit 2
    cp "$experiments/sample-dotnet.py" "$shared/sample-dotnet.py"
    sudo -n -u rb1b env DOTNET_EXE=$dotnet_root/dotnet python3 "$shared/sample-dotnet.py" "$shared/samples-$label-rb1b.txt" &
fi

start=$(date -Is)
cd "$LAB" || exit 1
timeout 3600 "${launch[@]}" "$reprotest" -v --min-cpus "$MIN_CPUS" --store-dir "$store" \
    "${vary[@]}" -c "$cmd" "$LAB" "$artifacts" > "$OUT/rt-$label.log" 2>&1
status=$?
sleep 2
kill $sampler
eval "$stop_servers"

if [ "$axis" = user_group ]; then
    sudo -n -u rb1b pkill -u rb1b -f "[s]amples-$label-rb1b"
    cp "$shared/samples-$label-rb1b.txt" "$OUT/"
    cp "$modes_dir/$label-"* "$OUT/modes/"
fi

# A compiler server or MSBuild node still running now survived the builds.
pgrep -af -- 'nodemode:|VBCSCompiler' | grep -v JetBrains > "$OUT/leftover-$label.txt"
leftover=$(wc -l < "$OUT/leftover-$label.txt")

# When reprotest finds no differences, it replaces the experiment's store
# with a link to the control's (R6). Say "link" then, not the control's
# hash again.
control=$(short_hash "$store/control/source-root/$hash_file")
if [ -L "$store/experiment-1" ]; then
    experiment=link
else
    experiment=$(short_hash "$store/experiment-1/source-root/$hash_file")
fi

printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$label" "$layer" "$axis" "$start" "$(date -Is)" \
    "$status" "$control" "$experiment" "$leftover" >> "$OUT/summary.tsv"
echo "$label exit $status control $control experiment $experiment leftover $leftover"
