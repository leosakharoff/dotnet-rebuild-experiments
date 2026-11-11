#!/bin/bash
#
# Stage 2: what the release job publishes for Linux. A locked restore,
# then WebAPI and BackgroundJobExecutor published self-contained for
# linux-x64 into release/, then a hash of every file under release/.
# reprotest runs this inside its copy of the lab, once for the control
# build and once for the experiment.
#
# The commands are the publish-linux job in .github/workflows/03-release.yml
# as of 4e5237a33 (24 September 2026), with the tag v0.0.0-thesis. They
# fit the commits from 84d73a2f6 to before 5031c5af. Before 84d73a2f6 the
# projects name no runtime, so the restore leaves linux-x64 out and the
# publish stops with NETSDK1047. From 5031c5af the job sets the version
# with APP_VERSION instead.
#
# To run it by hand, without reprotest, from inside a lab:
#
#   cd /private/tmp/rb1-phoenix
#   env DOTNET_DIR=$HOME/.dotnet bash ~/Dev/dotnet-rebuild-experiments/1-phoenix/scripts/2-publish/build.sh
#
# That leaves bin/, obj/ and release/ in the lab, so make it again before
# rt.sh.
#
# DOTNET_DIR is the SDK folder; shared/rt.sh passes it in. The lab's
# global.json chooses the version inside it.

# Stop at the first command that fails (-e) and at any variable that is
# not set (-u).
set -eu

export DOTNET_ROOT=$DOTNET_DIR
export PATH=$DOTNET_DIR:$PATH
export DOTNET_CLI_HOME=/tmp/dch
export DOTNET_NOLOGO=1
export MSBUILDDISABLENODEREUSE=1

# The release job pins the locale from 4e5237a33 on, because the compiler
# in SDK 9 sorts some generated types by the culture (W26). Like the job,
# this pins it only when the commit's workflow does, and then overrides
# reprotest's locales variation. On earlier commits the variation reaches
# the compiler, so the before commit in commits.md shows W26.
if grep -q 'LC_ALL: C.UTF-8' .github/workflows/03-release.yml; then
    export LC_ALL=C.UTF-8
fi

# No compiler server may live on from one build into the next. The trap
# also runs when a build fails.
dotnet build-server shutdown > /dev/null
trap 'dotnet build-server shutdown > /dev/null' EXIT

# The job takes the version from the tag; ours is v0.0.0-thesis. Used
# without quotes below, so it splits into two arguments.
version='/p:Version=0.0.0-thesis /p:InformationalVersion=v0.0.0-thesis'

# Directory.Build.props turns on locked mode only on GitHub Actions
# (84d73a2f6), so we ask for it here. Commits before 84d73a2f6 have no
# lock files.
dotnet restore ./WS.Phoenix.sln --locked-mode $version
dotnet publish ./src/WebAPI/WebAPI.csproj -c Release -o ./release/ws-pems-linux-x64 \
    -r linux-x64 --self-contained true --no-restore /p:SkipSpaBuild=true $version
dotnet publish ./src/BackgroundJobExecutor/BackgroundJobExecutor.csproj -c Release -o ./release/ws-pems-job-worker-linux-x64 \
    -r linux-x64 --self-contained true --no-restore $version

# One line per file: its SHA-256 and its path. -print0, sort -z and
# xargs -0 keep file names with spaces whole; LC_ALL=C sorts the same way
# on every machine.
find release -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > hashes.sha256
