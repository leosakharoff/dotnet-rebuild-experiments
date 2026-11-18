#!/bin/bash
#
# Stage 6: the release's images, each built twice and compared (written
# 13 October 2026 as image-probe.sh, rewritten and renamed on 16 November
# 2026).
#
#   OUT=<private folder> build-twice.sh COMMIT LABEL
#
# The images are built as the release job (.github/workflows/03-release.yml,
# job docker-images) builds them at COMMIT:
#
#   1  COMMIT exported with git archive to a new, empty lab, without
#      .claude/, which no image copies into its final stage
#   2  the frontend's static export built in the lab by 3-frontend/build.sh,
#      the release's frontend job; the WebAPI image takes it, as in CI
#   3  each image built twice with buildx, from its own Dockerfile and
#      context, with the job's build arguments
#   4  the two builds compared with oci-diff.py: image manifest, config,
#      and layer by layer
#
# Where the release dates its images by the commit (rewrite-timestamp in
# its workflow, from fa60ea974 on), the builds get the commit's time as
# SOURCE_DATE_EPOCH and the exporter's rewrite-timestamp=true, as the job
# does. Before that, they get neither, as the job then did.
#
# Three things differ from the job, and none changes the image manifest,
# which is what is compared (E1-S6-04): no cache, so each build starts from
# nothing; no provenance or SBOM, which differ in every build; and the
# images go to OCI tarballs instead of the registry.
#
# IMAGES picks the images; the default is the five the release builds:
# webapi, worker, mcp, chat and broker. "migrations" is the migrations
# image, which scripts/docker-build-push.sh builds and the release does not.
# NODE_DIR is the Node for the export, /private/tmp/rb1-node22 by default;
# 3-frontend/build.sh stops if it is not the version in .nvmrc.
# DOCKER_CONFIG must hold the buildx builder rb1.
#
# The lab is /private/tmp/rb1-img/x and the tarballs go to
# /private/tmp/rb1-img-out/LABEL. OUT/LABEL gets the logs, the export's
# hashes, the build settings and one comparison per image. The last line
# says how many images were the same; the exit status is 1 if any was not.

set -u
OUT=${OUT:?set OUT to a private data folder}
commit=${1:?COMMIT} label=${2:?LABEL}
here=$(cd "$(dirname "$0")" && pwd)
repo=/home/leos/Dev/Weel-Sandvig/WS.Phoenix-repro
lab=/private/tmp/rb1-img/x
IMAGES=${IMAGES:-webapi worker mcp chat broker}
NODE_DIR=${NODE_DIR:-/private/tmp/rb1-node22}
# The release's version: 3-frontend/build.sh gives the export the same one.
TAG=v0.0.0-thesis
out=$OUT/$label
tars=/private/tmp/rb1-img-out/$label
buildkit=$(docker buildx inspect rb1 2> /dev/null | awk -F': *' '/BuildKit version/ {print $2}')
[ -n "$buildkit" ] || { echo "no buildx builder rb1 (DOCKER_CONFIG)"; exit 2; }
rm -rf "$tars" && mkdir -p "$out" "$tars"

echo "== 1 the lab $(date +%T)"
# A new, empty folder holds exactly the commit's files, as in make-lab.sh.
rm -rf /private/tmp/rb1-img && mkdir -p "$lab"
git -C "$repo" archive "$commit" -- . ':(exclude).claude' | tar -x -C "$lab" || exit 1

if [[ " $IMAGES " == *" webapi "* ]]; then
  echo "== 2 the frontend export $(date +%T)"
  # A clean environment, so no ~/.npmrc or shell setting reaches npm. Its
  # HOME sits beside the lab, not in it: the lab is the build context.
  # GitHub's runners use the C.UTF-8 locale.
  ( cd "$lab" && env -i HOME=/private/tmp/rb1-img PATH=/usr/bin:/bin LC_ALL=C.UTF-8 NODE_DIR="$NODE_DIR" \
      bash "$here/../3-frontend/build.sh" ) > "$out/frontend.log" 2>&1 \
    || { echo "frontend build failed, see frontend.log"; exit 1; }
  # The export's hashes say which export went into the image.
  # .dockerignore keeps node_modules and .next out of the context; they go
  # from the lab too.
  mv "$lab/hashes.sha256" "$out/frontend-hashes.sha256"
  rm -rf "$lab/src/WebAPI/ClientApp/node_modules" "$lab/src/WebAPI/ClientApp/.next"
  echo "export: $(wc -l < "$out/frontend-hashes.sha256") files"
fi

echo "== 3 the images $(date +%T)"
# Dated by the commit where the release's workflow dates them.
date_env=() rewrite=""
if git -C "$repo" grep -q 'rewrite-timestamp=true' "$commit" -- .github/workflows; then
  date_env=(SOURCE_DATE_EPOCH="$(git -C "$repo" log -1 --format=%ct "$commit")")
  rewrite=",rewrite-timestamp=true"
fi
echo "commit $commit, BuildKit $buildkit, dated by the commit: ${date_env[*]:-no}" | tee "$out/build-settings.txt"
same=0
for img in $IMAGES; do
  context=$lab args=()
  case $img in
    webapi) file=src/WebAPI/Dockerfile; args=(--build-arg "APP_VERSION=$TAG" --build-arg SKIP_SPA_BUILD=true) ;;
    worker) file=src/BackgroundJobExecutor/Dockerfile; args=(--build-arg "APP_VERSION=$TAG") ;;
    migrations) file=deployment/migrations/Dockerfile; args=(--build-arg "APP_VERSION=$TAG") ;;
    mcp) file=mcp/Dockerfile; context=$lab/mcp ;;
    chat) file=mcp/chat-server/Dockerfile; context=$lab/mcp ;;
    broker) file=mcp/auth-broker/Dockerfile; context=$lab/mcp/auth-broker ;;
    *) echo "unknown image $img"; exit 2 ;;
  esac
  for n in 1 2; do
    env "${date_env[@]}" docker buildx build --builder rb1 --no-cache --provenance=false -f "$lab/$file" "${args[@]}" \
      --output "type=oci,dest=$tars/$img-$n.oci.tar$rewrite" "$context" > "$out/$img-$n.log" 2>&1
    rc=$?
    echo "$img-$n exit $rc $(date +%T)"
    [ "$rc" = 0 ] || { echo "build failed, see $img-$n.log"; exit 1; }
  done
  echo "== 4 $img, the two builds compared"
  python3 "$here/oci-diff.py" "$tars/$img-1.oci.tar" "$tars/$img-2.oci.tar" > "$out/$img-diff.txt" 2>&1
  head -3 "$out/$img-diff.txt"
  case $(head -1 "$out/$img-diff.txt") in "manifest same:"*) same=$((same + 1)) ;; esac
done
count=$(wc -w <<< "$IMAGES")
echo "== done $(date +%T): $same of $count images the same in two builds"
[ "$same" = "$count" ]
