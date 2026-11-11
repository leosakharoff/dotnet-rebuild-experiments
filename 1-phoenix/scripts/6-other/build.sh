#!/bin/bash
#
# Stage 6: the Windows release, built on Linux as the release's Windows
# job builds it, without signing. The frontend (stage 3's build.sh), then
# the locked restore, three self-contained win-x64 publishes, the
# migrator's copy, and both folders packed with the commit's own
# scripts/pack-release-zip.sh. Then a hash of every file under release/.
#
# The commands are .github/workflows/00-reusable-windows-publish.yml as of
# 2cd85fd01 (21 October 2026), as ci/ci-local.sh runs them. The signing is
# 6-other/signing-probe.sh; the Linux migrator is 6-other/migrator-probe.sh.
#
# To run it by hand, without reprotest, from inside a lab:
#
#   cd /private/tmp/rb1-phoenix
#   env DOTNET_DIR=$HOME/.dotnet NODE_DIR=/private/tmp/rb1-node22 \
#       COMMIT_TIME=$(cut -d' ' -f2 /private/tmp/rb1-phoenix.commit) bash ~/Dev/dotnet-rebuild-experiments/1-phoenix/scripts/6-other/build.sh
#
# COMMIT_TIME is the commit's time, which make-lab.sh writes beside the
# lab. That leaves the build output in the lab, so make it again before
# rt.sh.
#
# shared/rt.sh passes all three in.

# Stop at the first command that fails (-e) and at any variable that is
# not set (-u).
set -eu

: "${COMMIT_TIME:?no commit time; make the lab again with make-lab.sh}"
lab=$PWD

# Stage 3 first. The Windows job gets only out/ from the frontend job, so
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
# (5031c5af). No locale: the Windows job pins none.
export GITHUB_ACTIONS=true
export APP_VERSION=v0.0.0-thesis

# No compiler server may live on from one build into the next. The trap
# also runs when a build fails.
dotnet build-server shutdown > /dev/null
trap 'dotnet build-server shutdown > /dev/null' EXIT

dotnet restore ./WS.Phoenix.sln
python3 scripts/verify-nuget-downloads.py
dotnet publish src/WebAPI/WebAPI.csproj --configuration Release --output release/win/ws-pems-win-x64 \
    --runtime win-x64 --self-contained true --no-restore -p:SkipSpaBuild=true
dotnet publish src/BackgroundJobExecutor/BackgroundJobExecutor.csproj --configuration Release --output release/win/ws-pems-job-worker-win-x64 \
    --runtime win-x64 --self-contained true --no-restore
dotnet publish src/DbMigrator/DbMigrator.csproj --configuration Release --output publish/migrator-win \
    --runtime win-x64 --self-contained true --no-restore
cp publish/migrator-win/ws-pems-db-migrator.exe "release/win/ws-pems-db-migrator-win-x64-$APP_VERSION.exe"

# The job's packing step, from release/win. Our zip is the one in
# /private/tmp/rb1-tools, the same that ci/ci-local.sh uses.
cd release/win
for d in ws-pems-win-x64 ws-pems-job-worker-win-x64; do
    PATH=/private/tmp/rb1-tools:$PATH SOURCE_DATE_EPOCH=$COMMIT_TIME \
        "$lab/scripts/pack-release-zip.sh" "$d" "../$d-$APP_VERSION.zip"
done
cd ../..

# One line per file: its SHA-256 and its path. -print0, sort -z and
# xargs -0 keep file names with spaces whole; LC_ALL=C sorts the same way
# on every machine.
find release -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > hashes.sha256
