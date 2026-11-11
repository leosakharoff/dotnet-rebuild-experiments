#!/bin/bash
#
# Stage 1: dotnet build of the two programs, then a hash of every file
# under src/*/bin. reprotest runs this inside its copy of the lab, once
# for the control build and once for the experiment.
#
# To run it by hand, without reprotest, from inside a lab:
#
#   cd /private/tmp/rb1-phoenix
#   env DOTNET_DIR=$HOME/.dotnet bash ~/Dev/dotnet-rebuild-experiments/1-phoenix/scripts/1-build/build.sh
#
# That leaves bin/ and obj/ in the lab, so export it again before rt.sh.
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

# No compiler server may live on from one build into the next. The trap
# also runs when a build fails.
dotnet build-server shutdown > /dev/null
trap 'dotnet build-server shutdown > /dev/null' EXIT

# The frontend is stage 3. Without SkipSpaBuild, WebAPI.csproj runs
# npm ci and npm run build itself.
dotnet build src/WebAPI/WebAPI.csproj -c Release -p:SkipSpaBuild=true
dotnet build src/BackgroundJobExecutor/BackgroundJobExecutor.csproj -c Release

# One line per file: its SHA-256 and its path. -print0, sort -z and
# xargs -0 keep file names with spaces whole; LC_ALL=C sorts the same way
# on every machine.
find src/*/bin -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > hashes.sha256
