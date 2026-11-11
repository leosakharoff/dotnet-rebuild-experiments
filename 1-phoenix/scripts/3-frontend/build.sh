#!/bin/bash
#
# Stage 3: the frontend's static export. npm ci from our npm cache without
# network, then next build, then a hash of every file under out/.
# reprotest runs this inside its copy of the lab, once for the control
# build and once for the experiment. Stages 4 and 6 run it first too.
#
# The commands are the release's frontend job
# (.github/workflows/00-reusable-frontend-build.yml) as of 2cd85fd01
# (21 October 2026), as ci/ci-local.sh runs it, without lint. Before
# 456504fa2 the job ran npm ci without --ignore-scripts and without Next's
# two switches below.
#
# To run it by hand, without reprotest, from inside a lab:
#
#   cd /private/tmp/rb1-phoenix
#   env NODE_DIR=/private/tmp/rb1-node22 bash ~/Dev/dotnet-rebuild-experiments/1-phoenix/scripts/3-frontend/build.sh
#
# That leaves node_modules/, .next/ and out/ in the lab, so make it again
# before rt.sh.
#
# NODE_DIR is the Node folder; shared/rt.sh passes it in, chosen by the
# version in the frontend's .nvmrc.

# Stop at the first command that fails (-e) and at any variable that is
# not set (-u).
set -eu

app=src/WebAPI/ClientApp

export PATH=$NODE_DIR/bin:$PATH
if [ "$(node --version)" != "v$(cat $app/.nvmrc)" ]; then
    echo "build.sh: $NODE_DIR has Node $(node --version); .nvmrc asks for $(cat $app/.nvmrc)" >&2
    exit 1
fi

# The job's environment besides Node. GitHub sets CI=true in every step.
# Next takes APP_VERSION as its build ID (W37).
export CI=true
export npm_config_cache=/private/tmp/rb1-npm
export npm_config_update_notifier=false
export NEXT_TELEMETRY_DISABLED=1
export NEXT_DISABLE_SWC_WASM=1
export NEXT_IGNORE_INCORRECT_LOCKFILE=1
export APP_VERSION=v0.0.0-thesis

# --offline: every package comes from the cache, so the two builds cannot
# get different packages from the network. npm ci stops if one is missing.
(
    cd $app
    npm ci --ignore-scripts --offline --no-audit --no-fund
    npm run build
)

# One line per file: its SHA-256 and its path. -print0, sort -z and
# xargs -0 keep file names with spaces whole; LC_ALL=C sorts the same way
# on every machine.
find $app/out -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > hashes.sha256
