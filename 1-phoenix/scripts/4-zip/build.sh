#!/bin/bash
#
# Layer 4: the Linux release zips. The frontend (layer 3's build.sh), then
# the release job's locked restore and two self-contained linux-x64
# publishes with the export in wwwroot/, then both folders packed with
# the commit's own scripts/pack-release-zip.sh. Then a hash of every file
# under release/: the zips and the folders they hold.
#
# The commands are the publish-linux job in .github/workflows/03-release.yml
# as of 2cd85fd01 (21 October 2026), as ci/ci-local.sh runs it. They fit
# the commits from 5ec085acb on, where every zip is packed by that script.
#
# To run it by hand, without reprotest, from inside a lab:
#
#   cd /private/tmp/rb1-phoenix
#   env DOTNET_DIR=$HOME/.dotnet NODE_DIR=/private/tmp/rb1-node22 \
#       COMMIT_TIME=$(cut -d' ' -f2 /private/tmp/rb1-phoenix.commit) bash ~/Dev/dotnet-rebuild-experiments/1-phoenix/scripts/4-zip/build.sh
#
# COMMIT_TIME is the commit's time, which make-lab.sh writes beside the
# lab. That leaves the build output in the lab, so make it again before
# rt.sh.
#
# shared/rt.sh passes all three in. The job packs with the commit's time,
# so two builds of one commit give the same zip times.

# Stop at the first command that fails (-e) and at any variable that is
# not set (-u).
set -eu

: "${COMMIT_TIME:?no commit time; make the lab again with make-lab.sh}"
lab=$PWD

# Layer 3 first. The publish job gets only out/ from the frontend job, so
# node_modules/ and .next/ go.
bash "$(dirname "$0")/../3-frontend/build.sh"
rm -rf src/WebAPI/ClientApp/node_modules src/WebAPI/ClientApp/.next

export DOTNET_ROOT=$DOTNET_DIR
export PATH=$DOTNET_DIR:$PATH
export DOTNET_CLI_HOME=/tmp/dch
export DOTNET_NOLOGO=1
export MSBUILDDISABLENODEREUSE=1

# The job's environment. GITHUB_ACTIONS turns on the locked restore in
# Directory.Build.props (84d73a2f6). The version comes from the tag
# (5031c5af). The locale is pinned (4e5237a33).
export GITHUB_ACTIONS=true
export APP_VERSION=v0.0.0-thesis
export LC_ALL=C.UTF-8

# No compiler server may live on from one build into the next. The trap
# also runs when a build fails.
dotnet build-server shutdown > /dev/null
trap 'dotnet build-server shutdown > /dev/null' EXIT

dotnet restore ./WS.Phoenix.sln
python3 scripts/verify-nuget-downloads.py
dotnet publish ./src/WebAPI/WebAPI.csproj -c Release -o ./release/ws-pems-linux-x64 \
    -r linux-x64 --self-contained true --no-restore /p:SkipSpaBuild=true
dotnet publish ./src/BackgroundJobExecutor/BackgroundJobExecutor.csproj -c Release -o ./release/ws-pems-job-worker-linux-x64 \
    -r linux-x64 --self-contained true --no-restore

# The job's packing step. Our zip is the one in /private/tmp/rb1-tools, the
# same that ci/ci-local.sh uses.
cd release
for d in ws-pems-linux-x64 ws-pems-job-worker-linux-x64; do
    PATH=/private/tmp/rb1-tools:$PATH SOURCE_DATE_EPOCH=$COMMIT_TIME \
        "$lab/scripts/pack-release-zip.sh" "$d" "$d-$APP_VERSION.zip"
done
cd ..

# One line per file: its SHA-256 and its path. -print0, sort -z and
# xargs -0 keep file names with spaces whole; LC_ALL=C sorts the same way
# on every machine.
find release -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > hashes.sha256
