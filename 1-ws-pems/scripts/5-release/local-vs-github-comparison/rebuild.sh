#!/bin/bash
# Does our rebuild give the same bytes as GitHub's build of a tag? Step 1
# of 2: rebuild the release workflow's jobs here from the tag. compare.sh
# then compares the outputs with what GitHub built. On 14 October 2026
# every output of v0.0.0-thesis.6 was the same, the images too
# (data/phoenix-reference-release/arch-2026-10-14).
#
# Written 13 October 2026 as ci-local.sh; renamed on 16 November 2026.
#
#   OUT=<private folder> [REPO=<repository>] [MANIFEST=<build-manifest.json>] rebuild.sh TAG [JOBS]
#
# TAG is a tag in REPO (default: the WS worktree); each job gets its own
# shallow clone of it
# in /private/tmp/rb1-ci/<job>, with origin set to the URL actions/checkout
# gives the jobs, so Source Link and the SDK see what they see in CI: the
# commit (SourceRevisionId) and the repository's URL. Then, as the jobs do:
#
#   frontend   npm ci and npm run build with APP_VERSION=TAG (no lint, no
#              locale), from the offline npm cache, Node 22.23.3
#   linux      publish-linux: the export copied in, the locked restore, both
#              publishes, both zips with the commit's pack-release-zip.sh;
#              LC_ALL=C.UTF-8 as the job sets it
#   windows    the reusable Windows job without signing: the export, the
#              locked restore, three win-x64 publishes, the migrator copy,
#              both zips; no locale, as the job sets none
#   migrator   migration-bundles: the locked restore and the linux-x64
#              migrator; LC_ALL=C.UTF-8. Not the smoke test
#   sql        migration-bundles' idempotent SQL script: the locked restore,
#              dotnet tool restore, dotnet ef migrations script (added
#              14 October)
#   images     the images from a clone plus the export, with
#              SOURCE_DATE_EPOCH in buildx's environment and
#              rewrite-timestamp=true on the OCI exporter, as in the dry run's
#              docker-images job; no provenance or SBOM. The two .NET images,
#              and since 14 October the three MCP images, each from its own
#              context as the job builds them
#
# JOBS defaults to all six, in that order; frontend runs first because the
# others take its export. Every .NET job gets GITHUB_ACTIONS=true (the locked
# restore in Directory.Build.props) and APP_VERSION=TAG, the SDK in
# DOTNET_DIR, the NuGet cache in /tmp/dch, HOME there too, so no user
# secrets. The images job needs DOCKER_CONFIG with buildx and the builder
# rb1. Outputs land in $OUT/local/.
#
# Changed 14 October, evening: the script exits 1 when any job fails, and
# a failed image build now fails the images job (the loop's break used to
# report exit 0). The frontend job removes the previous export before it
# builds, so a failed build cannot leave an older export for the jobs after
# it; jobs run without frontend still reuse the export that is there.
#
# Changed 21 October: each job follows its tag's own workflow where the
# branch changed it. The frontend runs npm ci with --ignore-scripts and
# Next's two switches when the tag's frontend workflow does, and the .NET
# jobs run verify-nuget-downloads.py after their restores when the tag
# has it (from 12cb488e3). The sql job gives the CLI a home of its own and
# checks the tools with --tools when the tag's migration job does (from
# b3e0134ff).
#
# Also changed 21 October: every PATH ends in /bin as well, for macOS,
# where sh, chmod and rm live in /bin only. On Arch /bin is a link to
# /usr/bin, so the builds there see the same tools as before.
#
# Changed 24 November: a release from v0.0.0-thesis.7 on carries
# build-manifest.json, its own record of how to rebuild it (the tag's
# docs/release/build-manifest.md). When the release's copy is at
# $OUT/assets/build-manifest.json (where `gh release download` put the
# assets) or at MANIFEST, the script reads it with manifest.py and:
#
#   - stops unless TAG is the manifest's tag, the tag in REPO is the
#     manifest's commit, and the commit's time is its SOURCE_DATE_EPOCH;
#   - stops unless the tools for the jobs asked for are the pinned ones:
#     the SDK in DOTNET_DIR and its only runtime, Node and npm in NODE_DIR,
#     and the builder rb1's BuildKit version (its image digest is reported,
#     not enforced: buildx shows it only for a builder created with it);
#   - gives the builds the manifest's APP_VERSION, packs and dates the
#     images with its SOURCE_DATE_EPOCH, and sets origin to its repository.
#
# compare.sh then regenerates the manifest from the outputs.
#
# The commands. A tag whose scripts/release/ holds the job scripts (WS
# branch 2fc2fcf43 on; docs/release/build-manifest.md, "The job scripts")
# is built with those, the release workflow's own commands, run in each
# job's clone:
#
#   frontend   frontend-build.sh all (npm offline unless NPM_OFFLINE=false)
#   linux      publish-linux.sh, which packs the zips too
#   windows    publish-windows.sh build, then pack: unsigned, as before;
#              compare.sh pastes the published signatures on
#   migrator   migration-bundles.sh: the Linux migrator and the SQL script
#   sql        nothing more when migrator made the script in this run;
#              alone, migration-bundles.sh, keeping the script only
#   images     docker-images.sh oci on the builder rb1 (BUILDX_BUILDER), which
#              also writes each image's SBOM; it uses the builder's cache,
#              unlike the --no-cache builds below, so empty it first for a
#              clean rebuild (docker buildx prune --builder rb1 -af)
#
# with the manifest's APP_VERSION and SOURCE_DATE_EPOCH, TOOLS_DIR first on
# PATH for the packing step (on macOS it must also hold sha256sum, which the
# job scripts call and macOS keeps in /sbin), and the outputs copied to the same places in
# $OUT/local as before. For other tags each job is this script's own copy
# of the workflow's steps, chosen by what the tag's workflow says, as before.
# The WS repository's scripts/release/rebuild.sh does the whole check in one
# command from a tag on; this script keeps the experiment's layout, so
# compare.sh can also read a CI run's artifacts and older tags.
#
# Without a manifest (v0.0.0-thesis.6 and older) nothing changes.
#
# Also changed 24 November. The sql job takes dotnet ef's two projects from
# the tag's workflow: src/Infrastructure.Migrations for both since the merge
# of main (8f4227eb2), src/Infrastructure and src/WebAPI before; the lab
# patched a copy of this script for that on 23 and 24 November. NPM_CACHE
# names the npm cache (the same patch), CI_DIR the folder of the clones,
# BUILD_HOME the builds' HOME and NuGet folder, and TOOLS_DIR the folder
# with zip for the packing step; each defaults to the path used so far.
# Arrays that can be empty are expanded as ${a[@]+"${a[@]}"}: macOS's
# /bin/bash is 3.2, which calls "${a[@]}" of an empty array unbound under
# set -u. The Mac Studio rebuild of 23 November patched a copy for that.
set -u
OUT=${OUT:?set OUT to a private data folder}
TAG=${1:?TAG} JOBS=${2:-frontend linux windows migrator sql images}
repo=${REPO:-/home/leos/Dev/Weel-Sandvig/WS.Phoenix-repro}
url=https://github.com/Weel-Sandvig/WS.Phoenix
ci=${CI_DIR:-/private/tmp/rb1-ci} home=${BUILD_HOME:-/tmp/dch}
tools=${TOOLS_DIR:-/private/tmp/rb1-tools} npm_cache=${NPM_CACHE:-/private/tmp/rb1-npm}
DN=${DOTNET_DIR:-/private/tmp/rb1-dotnet10/sdk} NODE=${NODE_DIR:-/private/tmp/rb1-node22}
here=$(cd "$(dirname "$0")" && pwd)
L=$OUT/local; mkdir -p "$L" "$ci"

# The release's own record, when it has one: the source and the two values a
# rebuild sets by hand. A manifest that MANIFEST names must exist.
stop() { echo "rebuild.sh: $*" >&2; exit 2; }
manifest=${MANIFEST:-$OUT/assets/build-manifest.json} app_version=$TAG
if [ -f "$manifest" ]; then
  vars=$(python3 "$here/manifest.py" "$manifest" shell) || exit 2
  eval "$vars"
  echo "manifest $manifest: $M_SUBJECTS subjects, commit $M_COMMIT"
  [ "$M_TAG" = "$TAG" ] || stop "the manifest is for $M_TAG, not $TAG"
  at=$(git -C "$repo" rev-parse --verify -q "$TAG^{commit}") || stop "no tag $TAG in $repo"
  [ "$at" = "$M_COMMIT" ] || stop "$TAG is $at in $repo; the manifest names $M_COMMIT"
  when=$(git -C "$repo" show -s --format=%ct "$M_COMMIT")
  [ "$when" = "$M_SOURCE_DATE_EPOCH" ] || stop "the commit's time is $when; the manifest's SOURCE_DATE_EPOCH is $M_SOURCE_DATE_EPOCH"
  url=$M_REPOSITORY app_version=$M_APP_VERSION
  # The release job writes the tag here. Another value is the record's, so the
  # builds take it, but compare.sh's regenerated manifest (the tag's) will differ.
  [ "$M_APP_VERSION" = "$TAG" ] || echo "NOTE: the manifest's APP_VERSION is $M_APP_VERSION, not the tag $TAG; the builds take the manifest's"
else
  [ -z "${MANIFEST:-}" ] || stop "no manifest at $MANIFEST"
  echo "no build-manifest.json at $manifest: the tag and its workflow alone decide the build"
  manifest=
fi

base=(env -i HOME="$home" USER="$USER" LOGNAME="$LOGNAME" SHELL=/bin/bash PATH=/usr/local/bin:/usr/bin:/bin)
net=("${base[@]}" DOTNET_ROOT="$DN" PATH="$DN:/usr/local/bin:/usr/bin:/bin" DOTNET_CLI_HOME="$home" DOTNET_NOLOGO=1
     MSBUILDDISABLENODEREUSE=1 GITHUB_ACTIONS=true APP_VERSION="$app_version")

pinned() {  # the tools for the jobs asked for, against the manifest's pins
  local wrong=0 v
  case " $JOBS " in *" frontend "*)
    v=$("${base[@]}" PATH="$NODE/bin:/usr/bin:/bin" node --version 2>&1)
    [ "$v" = "v$M_NODE" ] || { echo "Node in $NODE is $v; the manifest pins $M_NODE: $M_NODE_URL, sha256 $M_NODE_SHA256"; wrong=1; }
    v=$("${base[@]}" PATH="$NODE/bin:/usr/bin:/bin" npm --version 2>&1)
    [ "$v" = "$M_NPM" ] || { echo "npm in $NODE is $v; the manifest pins $M_NPM, sha512 $M_NPM_SHA512"; wrong=1; } ;;
  esac
  case " $JOBS " in *" linux "*|*" windows "*|*" migrator "*|*" sql "*)
    v=$(cd "$L" && "${net[@]}" dotnet --version 2>&1)
    [ "$v" = "$M_SDK" ] || { echo "the SDK in $DN is $v; the manifest pins $M_SDK: $M_SDK_URL, sha512 $M_SDK_SHA512"; wrong=1; }
    v=$(cd "$L" && "${net[@]}" dotnet --list-runtimes 2>&1 | awk '{print $2}' | LC_ALL=C sort -u | tr '\n' ' ')
    [ "$v" = "$M_RUNTIME " ] || { echo "the runtimes in $DN are $v; the manifest's SDK runs on $M_RUNTIME alone"; wrong=1; } ;;
  esac
  case " $JOBS " in *" images "*)
    v=$(docker buildx inspect --bootstrap rb1 2>&1)
    [ "$(sed -n 's/^BuildKit version: *//p' <<< "$v" | head -1)" = "$M_BUILDKIT" ] \
      || { echo "the builder rb1's BuildKit is $(sed -n 's/^BuildKit version: *//p' <<< "$v" | head -1); the manifest pins $M_BUILDKIT"; wrong=1; }
    if grep -q "$M_BUILDKIT_SHA256" <<< "$v"; then echo "builder rb1: BuildKit $M_BUILDKIT, image sha256:$M_BUILDKIT_SHA256"
    else echo "builder rb1: BuildKit $M_BUILDKIT; its image digest is NOT CONFIRMED (the manifest pins sha256:$M_BUILDKIT_SHA256)"; fi ;;
  esac
  return $wrong
}
[ -z "$manifest" ] || pinned || stop "the tools are not the ones the manifest pins"

clone() {  # a fresh shallow clone of TAG for one job, as actions/checkout makes it
  rm -rf "${ci:?}/$1"
  git clone -q --depth 1 --branch "$TAG" "file://$repo" "$ci/$1" 2> /dev/null && git -C "$ci/$1" remote set-url origin "$url" || return 1
  [ -z "$manifest" ] || [ "$(git -C "$ci/$1" rev-parse HEAD)" = "$M_COMMIT" ] || { echo "the clone for $1 is not at the manifest's commit"; return 1; }
}
check() {  # the NuGet check the tag's jobs run after restore, if the tag has it
  [ ! -f scripts/verify-nuget-downloads.py ] || "${base[@]}" python3 scripts/verify-nuget-downloads.py "$@"
}
export_in() { rm -rf "$ci/$1/src/WebAPI/ClientApp/out" && cp -r "$L/frontend-out" "$ci/$1/src/WebAPI/ClientApp/out"; }
epoch() {  # the commit's time; with a manifest its SOURCE_DATE_EPOCH, checked above to be the same
  if [ -n "$manifest" ]; then echo "$M_SOURCE_DATE_EPOCH"; else git -C "$ci/$1" log -1 --format=%ct; fi
}
build_images() {  # the images job's builds, one per image; stops at the first failure
  local img ctx file name extra version
  for img in ${IMAGES:-webapi worker mcp chat broker}; do
    ctx=$ci/images version=(--build-arg "APP_VERSION=$app_version")
    case $img in
      webapi) file=src/WebAPI/Dockerfile; extra=("${version[@]}" --build-arg SKIP_SPA_BUILD=true); name=ws-pems ;;
      worker) file=src/BackgroundJobExecutor/Dockerfile; extra=("${version[@]}"); name=ws-pems-job-worker ;;
      mcp) file=mcp/Dockerfile; ctx=$ci/images/mcp; extra=(); name=wspems-mcp-server ;;
      chat) file=mcp/chat-server/Dockerfile; ctx=$ci/images/mcp; extra=(); name=wspems-chat-server ;;
      broker) file=mcp/auth-broker/Dockerfile; ctx=$ci/images/mcp/auth-broker; extra=(); name=wspems-mcp-auth-broker ;;
      *) echo "unknown image $img"; return 2 ;;
    esac
    env SOURCE_DATE_EPOCH="$(epoch images)" docker buildx build --builder rb1 --no-cache --provenance=false \
      -f "$ci/images/$file" ${extra[@]+"${extra[@]}"} \
      --output "type=oci,dest=$L/images/$name.oci.tar,rewrite-timestamp=true" "$ctx" > "$L/images/$name.log" 2>&1 \
      || { echo "image $name failed, see $L/images/$name.log"; return 1; }
  done
}
pack() {  # job folder, release dir, zip suffix dirs...: the job's packing step
  local j=$1 dir=$2; shift 2
  ( cd "$ci/$j/$dir" && for d in "$@"; do
      env PATH="$tools:/usr/bin:/bin" SOURCE_DATE_EPOCH="$(epoch "$j")" "$ci/$j/scripts/pack-release-zip.sh" "$d" "$ci/$j/release/$d-$TAG.zip" || exit 1
    done )
}

workflow=${M_WORKFLOW:-.github/workflows/03-release.yml}  # the release workflow, as the manifest names it

# The tag's own job scripts, when it has them (see the header).
jobscripts=
if git -C "$repo" cat-file -e "$TAG:scripts/release/publish-linux.sh" 2> /dev/null; then
  jobscripts=1
  echo "the tag has scripts/release/*.sh: the jobs run those"
fi
sx=("${net[@]}" PATH="$tools:$DN:/usr/local/bin:/usr/bin:/bin")  # a .NET job script: the zip packing needs TOOLS_DIR first
made_sql=
script_job() {  # job: the tag's script for it, in its clone; outputs copied as the old jobs copy them
  local j=$1
  case $j in
    frontend)
      ( cd "$ci/frontend" && "${base[@]}" PATH="$NODE/bin:/usr/bin:/bin" CI=true npm_config_cache="$npm_cache" \
          npm_config_update_notifier=false npm_config_offline="${NPM_OFFLINE:-true}" npm_config_audit=false npm_config_fund=false \
          APP_VERSION="$app_version" bash scripts/release/frontend-build.sh all ) > "$L/frontend.log" 2>&1 \
        && cp -r "$ci/frontend/src/WebAPI/ClientApp/out" "$L/frontend-out" ;;
    linux)
      ( cd "$ci/linux" && "${sx[@]}" SOURCE_DATE_EPOCH="$(epoch linux)" bash scripts/release/publish-linux.sh ) > "$L/linux.log" 2>&1 \
        && mkdir -p "$L/linux" && cp "$ci/linux/release/"*-linux-x64-"$TAG".zip "$L/linux/" ;;
    windows)
      ( cd "$ci/windows" && "${sx[@]}" SOURCE_DATE_EPOCH="$(epoch windows)" bash scripts/release/publish-windows.sh build \
          && "${sx[@]}" SOURCE_DATE_EPOCH="$(epoch windows)" bash scripts/release/publish-windows.sh pack ) > "$L/windows.log" 2>&1 \
        && mkdir -p "$L/windows" && cp "$ci/windows/release/"*-win-x64-"$TAG".zip "$ci/windows/release/win/"*.exe "$L/windows/" ;;
    migrator|sql)
      [ "$j" = sql ] && [ -n "$made_sql" ] && { echo "the SQL script came from migration-bundles.sh in the migrator job"; return 0; }
      rm -rf "${ci:?}/$j-cli-home"
      ( cd "$ci/$j" && "${sx[@]}" NUGET_PACKAGES="$home/.nuget/packages" DOTNET_CLI_HOME="$ci/$j-cli-home" \
          bash scripts/release/migration-bundles.sh ) > "$L/$j.log" 2>&1 \
        && mkdir -p "$L/migrator" && cp "$ci/$j/bundles/bootstrap-postgresql-$TAG.sql" "$L/migrator/" \
        && if [ "$j" = migrator ]; then cp "$ci/$j/bundles/ws-pems-db-migrator-linux-x64-$TAG" "$L/migrator/" && made_sql=1; fi ;;
    images)
      mkdir -p "$L/images" \
        && ( cd "$ci/images" && env APP_VERSION="$app_version" SOURCE_DATE_EPOCH="$(epoch images)" BUILDX_BUILDER=rb1 \
             bash scripts/release/docker-images.sh oci "$L/images" ) > "$L/images.log" 2>&1 \
        || { echo "the images failed, see $L/images.log"; return 1; } ;;
  esac
}
failed=
for job in $JOBS; do
  echo "$job start $(date +%T)"
  if [ -n "$jobscripts" ]; then
    case $job in
      frontend) rm -rf "$L/frontend-out" && clone frontend && script_job frontend ;;
      linux|windows|images) clone "$job" && export_in "$job" && script_job "$job" ;;
      migrator) clone migrator && script_job migrator ;;
      sql) { [ -n "$made_sql" ] || clone sql; } && script_job sql ;;
      *) echo "unknown job $job"; exit 2 ;;
    esac
  else case $job in
    frontend)
      rm -rf "$L/frontend-out" && clone frontend && scripts= next=() \
        && if grep -q 'npm ci --ignore-scripts' "$ci/frontend/.github/workflows/00-reusable-frontend-build.yml"; then
             scripts=--ignore-scripts next=(NEXT_DISABLE_SWC_WASM=1 NEXT_IGNORE_INCORRECT_LOCKFILE=1); fi \
        && ( cd "$ci/frontend/src/WebAPI/ClientApp" && "${base[@]}" PATH="$NODE/bin:/usr/bin:/bin" CI=true \
          npm_config_cache="$npm_cache" npm_config_update_notifier=false NEXT_TELEMETRY_DISABLED=1 APP_VERSION="$app_version" ${next[@]+"${next[@]}"} \
          sh -c "npm ci $scripts --offline --no-audit --no-fund && npm run build" ) > "$L/frontend.log" 2>&1 \
        && cp -r "$ci/frontend/src/WebAPI/ClientApp/out" "$L/frontend-out" ;;
    linux)
      clone linux && export_in linux && ( cd "$ci/linux" \
        && "${net[@]}" LC_ALL=C.UTF-8 dotnet restore ./WS.Phoenix.sln && check \
        && "${net[@]}" LC_ALL=C.UTF-8 dotnet publish ./src/WebAPI/WebAPI.csproj -c Release -o ./release/ws-pems-linux-x64 -r linux-x64 --self-contained true --no-restore /p:SkipSpaBuild=true \
        && "${net[@]}" LC_ALL=C.UTF-8 dotnet publish ./src/BackgroundJobExecutor/BackgroundJobExecutor.csproj -c Release -o ./release/ws-pems-job-worker-linux-x64 -r linux-x64 --self-contained true --no-restore ) > "$L/linux.log" 2>&1 \
        && pack linux release ws-pems-linux-x64 ws-pems-job-worker-linux-x64 >> "$L/linux.log" 2>&1 \
        && mkdir -p "$L/linux" && cp "$ci/linux/release/"*.zip "$L/linux/" ;;
    windows)
      clone windows && export_in windows && ( cd "$ci/windows" \
        && "${net[@]}" dotnet restore ./WS.Phoenix.sln && check \
        && "${net[@]}" dotnet publish src/WebAPI/WebAPI.csproj --configuration Release --output release/win/ws-pems-win-x64 --runtime win-x64 --self-contained true --no-restore -p:SkipSpaBuild=true \
        && "${net[@]}" dotnet publish src/BackgroundJobExecutor/BackgroundJobExecutor.csproj --configuration Release --output release/win/ws-pems-job-worker-win-x64 --runtime win-x64 --self-contained true --no-restore \
        && "${net[@]}" dotnet publish src/DbMigrator/DbMigrator.csproj --configuration Release --output publish/migrator-win --runtime win-x64 --self-contained true --no-restore \
        && cp publish/migrator-win/ws-pems-db-migrator.exe "release/win/ws-pems-db-migrator-win-x64-$TAG.exe" ) > "$L/windows.log" 2>&1 \
        && pack windows release/win ws-pems-win-x64 ws-pems-job-worker-win-x64 >> "$L/windows.log" 2>&1 \
        && mkdir -p "$L/windows" && cp "$ci/windows/release/"*.zip "$ci/windows/release/win/"*.exe "$L/windows/" ;;
    migrator)
      clone migrator && ( cd "$ci/migrator" \
        && "${net[@]}" LC_ALL=C.UTF-8 dotnet restore ./WS.Phoenix.sln && check \
        && "${net[@]}" LC_ALL=C.UTF-8 dotnet publish ./src/DbMigrator/DbMigrator.csproj -c Release -o ./publish/migrator -r linux-x64 --self-contained true --no-restore ) > "$L/migrator.log" 2>&1 \
        && mkdir -p "$L/migrator" && cp "$ci/migrator/publish/migrator/ws-pems-db-migrator" "$L/migrator/ws-pems-db-migrator-linux-x64-$TAG" ;;
    sql)
      clone sql && cli=() flag= && rm -rf "$ci/sql-cli-home" \
        && projects=(-p src/Infrastructure/Infrastructure.csproj -s src/WebAPI/WebAPI.csproj) \
        && if grep -q 'DOTNET_CLI_HOME=$RUNNER_TEMP/dotnet-cli-home' "$ci/sql/$workflow"; then
             cli=(NUGET_PACKAGES="$home/.nuget/packages" DOTNET_CLI_HOME="$ci/sql-cli-home") flag=--tools; fi \
        && if grep -q -e '-p src/Infrastructure.Migrations/Infrastructure.Migrations.csproj' "$ci/sql/$workflow"; then
             projects=(-p src/Infrastructure.Migrations/Infrastructure.Migrations.csproj -s src/Infrastructure.Migrations/Infrastructure.Migrations.csproj); fi \
        && ( cd "$ci/sql" \
        && "${net[@]}" ${cli[@]+"${cli[@]}"} LC_ALL=C.UTF-8 dotnet restore ./WS.Phoenix.sln \
        && "${net[@]}" ${cli[@]+"${cli[@]}"} LC_ALL=C.UTF-8 dotnet tool restore && check $flag \
        && "${net[@]}" ${cli[@]+"${cli[@]}"} LC_ALL=C.UTF-8 dotnet ef migrations script --idempotent --configuration Release --context DatabaseContext \
             "${projects[@]}" -o "bundles/bootstrap-postgresql-$TAG.sql" ) > "$L/sql.log" 2>&1 \
        && mkdir -p "$L/migrator" && cp "$ci/sql/bundles/bootstrap-postgresql-$TAG.sql" "$L/migrator/" ;;
    images)
      clone images && export_in images && mkdir -p "$L/images" && build_images ;;
    *) echo "unknown job $job"; exit 2 ;;
  esac; fi
  rc=$?
  echo "$job exit $rc $(date +%T)"
  [ "$rc" -eq 0 ] || failed="$failed $job"
done
if [ -n "$failed" ]; then
  echo "failed:$failed"
  exit 1
fi
