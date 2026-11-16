#!/bin/bash
#
# Stage 5: the whole release, the nine files a user downloads from its
# page. Stage 4's Linux zips, then the release workflow's other jobs, one
# after the other:
#
# 1. publish-linux: stage 4's build.sh, which runs stage 3's first.
# 2. publish-windows, built on Linux and unsigned: three self-contained
#    win-x64 publishes, the migrator's copy, both folders packed.
# 3. migration-bundles: the linux-x64 database migrator and the
#    idempotent SQL script.
# 4. checksums: the four zips, upgrade.sh and the three database files
#    gathered in assets/, as the release page offers them, and SHA256SUMS
#    over them.
#
# Then a hash of every file under assets/.
#
# The commands are .github/workflows/03-release.yml and
# 00-reusable-windows-publish.yml as of 2cd85fd01 (21 October 2026), as
# local-vs-github-comparison/rebuild.sh runs them. Left out, because they
# need what we do not have: the signing (Weel-Sandvig's certificate;
# windows-signature-test.sh tests it with a test certificate), the
# migrator's smoke test (a database), the Windows smoke test (a Windows
# machine) and the images (stage 6).
#
# local-vs-github-comparison/ asks another question: does a rebuild of a
# tag give the same bytes as GitHub's own build of it? This stage cannot
# answer it. Its lab has no .git, so the commit and the repository's URL
# never reach the binaries, and its version is v0.0.0-thesis, not a tag.
#
# To run it by hand, without reprotest, from inside a lab:
#
#   cd /private/tmp/rb1-phoenix
#   env DOTNET_DIR=$HOME/.dotnet NODE_DIR=/private/tmp/rb1-node22 \
#       COMMIT_TIME=$(cut -d' ' -f2 /private/tmp/rb1-phoenix.commit) bash ~/Dev/dotnet-rebuild-experiments/1-phoenix/scripts/5-release/build.sh
#
# COMMIT_TIME is the commit's time, which make-lab.sh writes beside the
# lab. That leaves the build output in the lab, so make it again before
# run-stage.sh.
#
# shared/run-stage.sh passes all three in.

# Stop at the first command that fails (-e) and at any variable that is
# not set (-u).
set -eu

: "${COMMIT_TIME:?no commit time; make the lab again with make-lab.sh}"
lab=$PWD

# 1. publish-linux, with the frontend before it. Leaves the Linux zips in
# release/.
bash "$(dirname "$0")/../4-zip/build.sh"

export DOTNET_ROOT=$DOTNET_DIR
export PATH=$DOTNET_DIR:$PATH
export DOTNET_CLI_HOME=/tmp/dch
export DOTNET_NOLOGO=1
export MSBUILDDISABLENODEREUSE=1

# Every job's environment. GITHUB_ACTIONS turns on the locked restore in
# Directory.Build.props (84d73a2f6). The version comes from the tag
# (5031c5af).
export GITHUB_ACTIONS=true
export APP_VERSION=v0.0.0-thesis

# No compiler server may live on from one build into the next. The trap
# also runs when a build fails.
dotnet build-server shutdown > /dev/null
trap 'dotnet build-server shutdown > /dev/null' EXIT

# 2. publish-windows. In CI every job has a checkout of its own, so the
# previous job's bin/ and obj/ go first. The job takes the frontend's
# export, which stays in the lab, and pins no locale.
rm -rf src/*/bin src/*/obj tests/bin tests/obj
dotnet restore ./WS.Phoenix.sln
python3 scripts/verify-nuget-downloads.py
dotnet publish src/WebAPI/WebAPI.csproj --configuration Release --output release/win/ws-pems-win-x64 \
    --runtime win-x64 --self-contained true --no-restore -p:SkipSpaBuild=true
dotnet publish src/BackgroundJobExecutor/BackgroundJobExecutor.csproj --configuration Release --output release/win/ws-pems-job-worker-win-x64 \
    --runtime win-x64 --self-contained true --no-restore
dotnet publish src/DbMigrator/DbMigrator.csproj --configuration Release --output publish/migrator-win \
    --runtime win-x64 --self-contained true --no-restore
cp publish/migrator-win/ws-pems-db-migrator.exe "release/win/ws-pems-db-migrator-win-x64-$APP_VERSION.exe"

# The job packs from release/win and leaves the zips in release/, beside
# the Linux ones. Our zip is the one in /private/tmp/rb1-tools, the same
# that local-vs-github-comparison/rebuild.sh uses.
cd release/win
for d in ws-pems-win-x64 ws-pems-job-worker-win-x64; do
    PATH=/private/tmp/rb1-tools:$PATH SOURCE_DATE_EPOCH=$COMMIT_TIME \
        "$lab/scripts/pack-release-zip.sh" "$d" "../$d-$APP_VERSION.zip"
done
cd "$lab"

# 3. migration-bundles, from a checkout of its own again. It pins the
# locale and gives the .NET CLI a home of its own, in RUNNER_TEMP in CI
# and in the lab here; the packages stay where the other jobs put them.
# It takes no frontend export, and needs none: only a publish of WebAPI
# reads it.
rm -rf src/*/bin src/*/obj tests/bin tests/obj
export LC_ALL=C.UTF-8
export NUGET_PACKAGES=/tmp/dch/.nuget/packages
export DOTNET_CLI_HOME=$lab/dotnet-cli-home
dotnet restore ./WS.Phoenix.sln
dotnet tool restore
python3 scripts/verify-nuget-downloads.py --tools
dotnet publish ./src/DbMigrator/DbMigrator.csproj -c Release -o ./publish/migrator \
    -r linux-x64 --self-contained true --no-restore
mkdir -p bundles
cp publish/migrator/ws-pems-db-migrator "bundles/ws-pems-db-migrator-linux-x64-$APP_VERSION"
dotnet ef migrations script --idempotent --configuration Release \
    --context DatabaseContext \
    -p src/Infrastructure/Infrastructure.csproj \
    -s src/WebAPI/WebAPI.csproj \
    -o "bundles/bootstrap-postgresql-$APP_VERSION.sql"

# 4. checksums. The job downloads every job's zips into release/ and the
# three database files into release/db; assets/ is that folder here,
# because release/ holds the publish folders too. LC_ALL=C makes both
# globs list the files in the same order everywhere (97038d737).
export LC_ALL=C
mkdir -p assets/db
cp release/*.zip assets/
cp "release/win/ws-pems-db-migrator-win-x64-$APP_VERSION.exe" bundles/* assets/db/
cp scripts/upgrade.sh assets/
cd assets
{ sha256sum *.zip upgrade.sh; (cd db && sha256sum -- *); } > SHA256SUMS
cd "$lab"

# One line per file: its SHA-256 and its path. -print0, sort -z and
# xargs -0 keep file names with spaces whole; LC_ALL=C sorts the same way
# on every machine.
find assets -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > hashes.sha256

# CI throws each job's runner away and keeps only the files it uploads.
# Here that keeps the build small enough for reprotest, which builds in
# /tmp, in memory, and keeps the control build while the experiment runs:
# with every job's output left in both, the run of 16 November filled it.
rm -rf release publish bundles dotnet-cli-home src/*/bin src/*/obj tests/bin tests/obj
