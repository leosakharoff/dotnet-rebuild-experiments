#!/bin/bash
# Does our rebuild give the same bytes as GitHub's build of a tag? Step 2
# of 2: a CI run's artifacts against rebuild.sh's outputs.
#
# Written 13 October 2026 as ci-compare.sh; renamed on 16 November 2026.
#
#   compare.sh P TAG
#
# P holds ci/, the run's artifacts as `gh run download` writes them (one
# folder per artifact), and local/, rebuild.sh's outputs. One line per
# output: "same" or "DIFF". For a zip that differs, the entries are
# compared too: their names, contents (from the unpacked trees) and
# metadata (zipinfo -v, one listing per side). Images are compared with
# oci-diff.py. Everything lands in P/compare.
#
# Added 14 October: when the run signed the Windows binaries with a
# throwaway certificate (the artifact thesis-test-ca), the local unsigned
# build gets CI's signatures pasted, as deployment/signing/README.md says a
# rebuild is checked: paste-signatures.sh in SIGNING_IMAGE, then the
# commit's pack-release-zip.sh; its zips and migrator are compared with
# CI's. Also the SQL script, all five images, and SHA256SUMS, written here
# over the local outputs with the release job's command. CLONE is a clone
# of the tag (for the packing script, the signing root and upgrade.sh).
#
# Added 14 October, for the second dry run, which ran only the frontend
# and Windows jobs: an output whose artifact the run did not make is
# reported as "not in this run" instead of compared.
#
# Added 14 October, for the reference release: SIGNED says how CI signed
# the Windows binaries. test is the dry runs' throwaway certificate (the
# artifact thesis-test-ca, trusted with Microsoft's root); azure is a real
# release, WS's certificate, trusted through Microsoft's root alone; none
# compares the unsigned files as they are. The default follows
# thesis-test-ca, as before.
#
# Changed 14 October, evening: the script counts every output that differs
# and every step that fails, ends with a summary line, and exits 1 unless
# the count is 0; it used to exit 0 whatever it found. SHA256SUMS is
# rewritten in the form the release used: db/ paths before the release job
# named every line by its asset name (WS branch 28371c9e), flat names
# after. An image is the same only when oci-diff.py's first line says
# "manifest same".
#
# The dry runs are its negative control: it said DIFF where outputs
# differed. v0.0.0-thesis.2 (13 October) differed in all four zips and
# both migrators, v0.0.0-thesis.3 (14 October) in the Windows zips and
# migrator; v0.0.0-thesis.6 was the same in everything after the fixes
# (data/phoenix-ci-dry-run, data/phoenix-reference-release).
# ci-compare-tests.sh, which tested the verdicts on a fake run, was
# removed on 16 November 2026.
#
# Added 24 November: the release's own verdict. A release from
# v0.0.0-thesis.7 on carries build-manifest.json, which lists every file
# and each image's linux/amd64 manifest by digest and holds nothing about
# the run that made it (the tag's docs/release/build-manifest.md). When the
# release's copy is there, at MANIFEST, P/assets/build-manifest.json (the
# release as `gh release download` wrote it) or
# P/ci/dry-run-release/release/build-manifest.json (a dry run's artifact),
# the script ends by regenerating it from the rebuild: the tag's own
# scripts/release/build-manifest.py in CLONE, over the folder SHA256SUMS
# was written in above (the rebuilt files, the Windows ones with the
# signatures pasted) and local/images, with the repository and registry
# the published manifest names. cmp of the two is one more counted output,
# and manifest.py lists the subjects, same or DIFF. Without a manifest
# nothing is added. From the WS branch's stage 2 (ab0815a50) each image's
# SBOM, <image>-<tag>.spdx.json, is a release asset and a subject: each one
# beside the published manifest is compared with the rebuild's (rebuild.sh
# puts them in local/images), and the rebuilt ones join the folder the
# manifest is regenerated from. The registry is not read here: that a tag in GHCR
# points at the manifest's image is still ghcr-manifests.py's check.
#
# Also 24 November. The run's artifacts are read under the names the
# release workflow gives them now as well as October's: the export in
# frontend-export or release-frontend-export, SHA256SUMS in sha256sums or
# release-checksums. A run without an export artifact (a published
# release: GitHub keeps the artifact five days, and the export ships
# inside the zips) is reported as "not in this run"; before, the script
# compared the rebuilt export with nothing and counted a DIFF. CI_DIR and
# TOOLS_DIR name the clones' folder and the folder with zip, as in
# rebuild.sh; each defaults to the path used so far.
set -u
P=${1:?P} TAG=${2:?TAG}
CLONE=${CLONE:-${CI_DIR:-/private/tmp/rb1-ci}/windows} SIGNING_IMAGE=${SIGNING_IMAGE:-ws-signing:rb-dry}
tools=${TOOLS_DIR:-/private/tmp/rb1-tools}
here=$(cd "$(dirname "$0")" && pwd)
C=$P/ci L=$P/local R=$P/compare S=$P/compare/sums
rm -rf "$R" && mkdir -p "$R"
artifact() { local d; for d in "$@"; do [ ! -d "$C/$d" ] || { echo "$C/$d"; return; }; done; echo "$C/$1"; }  # the first of these artifacts the run has
exported=$(artifact frontend-export release-frontend-export) sums=$(artifact sha256sums release-checksums)

bad=0 skipped=0
hashes() { ( cd "$1" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum ); }
report() { if cmp -s "$1" "$2"; then echo "same  $3"; return 0; else echo "DIFF  $3"; return 1; fi; }
same() { report "$@" || { bad=$((bad + 1)); return 1; }; }  # one output, counted when it differs
skip() { echo "not in this run  $1"; skipped=$((skipped + 1)); }
zipdiff() {  # ci zip, local zip, label
  local u=$R/unzipped/$3
  mkdir -p "$u/ci" "$u/local"
  unzip -q "$1" -d "$u/ci" && unzip -q "$2" -d "$u/local"
  hashes "$u/ci" > "$u/ci.sha256"; hashes "$u/local" > "$u/local.sha256"
  report "$u/ci.sha256" "$u/local.sha256" "  $3: entries' contents ($(wc -l < "$u/ci.sha256") / $(wc -l < "$u/local.sha256") files)" \
    || diff "$u/ci.sha256" "$u/local.sha256" | head -20
  zipinfo -v "$1" | tail -n +2 > "$u/ci.zipinfo"; zipinfo -v "$2" | tail -n +2 > "$u/local.zipinfo"
  report "$u/ci.zipinfo" "$u/local.zipinfo" "  $3: zipinfo -v" || diff "$u/ci.zipinfo" "$u/local.zipinfo" | head -20
}

if [ -d "$exported" ]; then
  hashes "$exported" > "$R/frontend-ci.sha256"
  hashes "$L/frontend-out" > "$R/frontend-local.sha256"
  same "$R/frontend-ci.sha256" "$R/frontend-local.sha256" \
    "frontend export ($(wc -l < "$R/frontend-ci.sha256") / $(wc -l < "$R/frontend-local.sha256") files)" \
    || diff "$R/frontend-ci.sha256" "$R/frontend-local.sha256" | head -20
else
  skip "frontend export as an artifact (it ships inside the zips)"
fi

for z in ws-pems-linux-x64 ws-pems-job-worker-linux-x64; do
  [ -d "$C/release-zips-linux" ] || { skip "$z-$TAG.zip"; continue; }
  same "$C/release-zips-linux/$z-$TAG.zip" "$L/linux/$z-$TAG.zip" "$z-$TAG.zip" \
    || zipdiff "$C/release-zips-linux/$z-$TAG.zip" "$L/linux/$z-$TAG.zip" "$z"
done
mig=ws-pems-db-migrator-win-x64-$TAG.exe
win=$L/windows
SIGNED=${SIGNED:-$([ -f "$C/thesis-test-ca/ca.pem" ] && echo test || echo none)}
if [ "$SIGNED" != none ]; then
  W=$R/windows; win=$W/zips
  mkdir -p "$W/ci" "$W/local" "$W/keys" "$win"
  for z in ws-pems-win-x64 ws-pems-job-worker-win-x64; do
    unzip -q "$C/release-zips-windows/$z-$TAG.zip" -d "$W/ci" && unzip -q "$L/windows/$z-$TAG.zip" -d "$W/local"
  done
  # A downloaded migrator has no mode; both get 0644, as the README says.
  cp "$C/db-migration-bundles-windows/$mig" "$W/ci/" && cp "$L/windows/$mig" "$W/local/" && chmod 644 "$W/ci/$mig" "$W/local/$mig"
  if [ "$SIGNED" = test ]; then
    cat "$C/thesis-test-ca/ca.pem" "$CLONE/deployment/signing/microsoft-identity-verification-root-2020.pem" > "$W/keys/verify.pem"
  else
    cp "$CLONE/deployment/signing/microsoft-identity-verification-root-2020.pem" "$W/keys/verify.pem"
  fi
  docker run --rm --user "$(id -u):$(id -g)" -v "$W:$W" -w "$W" -e VERIFY_CAFILE="$W/keys/verify.pem" \
    --entrypoint /opt/signing/paste-signatures.sh "$SIGNING_IMAGE" ci local pasted > "$R/paste.log" 2>&1
  rc=$?
  echo "paste-signatures.sh, CI's signatures onto the local build: exit $rc, $(tail -1 "$R/paste.log")"
  [ "$rc" -eq 0 ] || bad=$((bad + 1))
  epoch=$(git -C "$CLONE" log -1 --format=%ct)
  ( cd "$W/pasted" && for z in ws-pems-win-x64 ws-pems-job-worker-win-x64; do
      env PATH="$tools:/usr/bin:/bin" SOURCE_DATE_EPOCH="$epoch" "$CLONE/scripts/pack-release-zip.sh" "$z" "$win/$z-$TAG.zip" || exit 1
    done ) > "$R/pack-pasted.log" 2>&1 \
    || { echo "FAIL  packing the pasted Windows zips, see $R/pack-pasted.log"; bad=$((bad + 1)); }
  cp "$W/pasted/$mig" "$win/"
fi
for z in ws-pems-win-x64 ws-pems-job-worker-win-x64; do
  same "$C/release-zips-windows/$z-$TAG.zip" "$win/$z-$TAG.zip" "$z-$TAG.zip" \
    || zipdiff "$C/release-zips-windows/$z-$TAG.zip" "$win/$z-$TAG.zip" "$z"
done

if [ -d "$C/db-migration-bundles-linux" ]; then
  same "$C/db-migration-bundles-linux/ws-pems-db-migrator-linux-x64-$TAG" \
    "$L/migrator/ws-pems-db-migrator-linux-x64-$TAG" "ws-pems-db-migrator-linux-x64-$TAG"
else
  skip "ws-pems-db-migrator-linux-x64-$TAG and the SQL script"
fi
same "$C/db-migration-bundles-windows/$mig" "$win/$mig" "$mig"
if [ -d "$C/db-migration-bundles-linux" ] && [ -f "$L/migrator/bootstrap-postgresql-$TAG.sql" ]; then
  same "$C/db-migration-bundles-linux/bootstrap-postgresql-$TAG.sql" "$L/migrator/bootstrap-postgresql-$TAG.sql" "bootstrap-postgresql-$TAG.sql"
fi
if [ -f "$sums/SHA256SUMS" ]; then
  mkdir -p "$S/db"
  cp "$L/linux/"*.zip "$win/"*.zip "$S/" && cp "$L/migrator/"* "$win/$mig" "$S/db/" && cp "$CLONE/scripts/upgrade.sh" "$S/"
  if grep -q '  db/' "$sums/SHA256SUMS"; then  # the release job before 28371c9e
    ( cd "$S" && export LC_ALL=C && sha256sum *.zip db/* upgrade.sh > SHA256SUMS )
  else
    ( cd "$S" && export LC_ALL=C && { sha256sum *.zip upgrade.sh; (cd db && sha256sum -- *); } > SHA256SUMS )
  fi
  same "$sums/SHA256SUMS" "$S/SHA256SUMS" "SHA256SUMS ($(wc -l < "$S/SHA256SUMS") lines)" \
    || diff "$sums/SHA256SUMS" "$S/SHA256SUMS"
fi

for n in ws-pems ws-pems-job-worker wspems-mcp-server wspems-chat-server wspems-mcp-auth-broker; do
  # A pushed image has no artifact; ghcr-manifests.py compares it with the rebuild.
  [ -f "$C/image-$n/$n.oci.tar" ] || { skip "image $n as an OCI artifact"; continue; }
  python3 "$here/../../6-images/oci-diff.py" "$C/image-$n/$n.oci.tar" "$L/images/$n.oci.tar" > "$R/$n-image-diff.txt" 2>&1
  first=$(head -1 "$R/$n-image-diff.txt")
  echo "image $n: $first"
  case $first in "manifest same:"*) ;; *) bad=$((bad + 1)) ;; esac
done

# The release's own record, regenerated from the rebuild (see the header).
manifest=${MANIFEST:-}
for m in "$P/assets/build-manifest.json" "$C/dry-run-release/release/build-manifest.json"; do
  [ -n "$manifest" ] || [ ! -f "$m" ] || manifest=$m
done
# The images' SBOMs, release assets beside the manifest from stage 2 on.
if [ -n "$manifest" ]; then
  for sbom in "$(dirname "$manifest")"/*-"$TAG".spdx.json; do
    [ -f "$sbom" ] || continue
    name=$(basename "$sbom")
    if [ -f "$L/images/$name" ]; then
      same "$sbom" "$L/images/$name" "$name" || diff <(python3 -m json.tool "$sbom") <(python3 -m json.tool "$L/images/$name") | head -20
    else
      echo "DIFF  $name: the rebuild made none"; bad=$((bad + 1))
    fi
    [ ! -d "$S" ] || [ ! -f "$L/images/$name" ] || cp "$L/images/$name" "$S/"
  done
fi
if [ -n "$manifest" ]; then
  G=$R/manifest; mkdir -p "$G"
  # Only the OCI files: the generator (9192fd4db) reads every *.json there as an
  # image index, and from stage 2 the SBOMs sit in the same folder.
  images=(); mkdir -p "$G/images"
  for f in "$L/images/"*.oci.tar; do [ ! -f "$f" ] || ln -sf "$f" "$G/images/"; done
  [ -z "$(ls "$G/images")" ] || images=(--images "$G/images")
  if ! vars=$(python3 "$here/manifest.py" "$manifest" shell 2> "$G/read.log"); then
    echo "FAIL  build-manifest.json: $(tail -1 "$G/read.log")"; bad=$((bad + 1))
  elif eval "$vars"; [ "$M_TAG" != "$TAG" ]; then
    echo "FAIL  build-manifest.json: $manifest is for $M_TAG, not $TAG"; bad=$((bad + 1))
  elif [ ! -f "$S/SHA256SUMS" ]; then
    echo "FAIL  build-manifest.json: no SHA256SUMS was written from the rebuilt files above, so there is no folder to regenerate it from"; bad=$((bad + 1))
  elif ! python3 "$CLONE/scripts/release/build-manifest.py" --commit "$M_COMMIT" --tag "$M_TAG" --assets "$S" ${images[@]+"${images[@]}"} \
         --repo-dir "$CLONE" --repository "$M_REPOSITORY" --registry "$M_REGISTRY" --output "$G/build-manifest.json" > "$G/generate.log" 2>&1; then
    echo "FAIL  build-manifest.json: the tag's build-manifest.py on the rebuilt outputs: $(tail -1 "$G/generate.log")"; bad=$((bad + 1))
  else
    same "$manifest" "$G/build-manifest.json" "build-manifest.json, regenerated from the rebuilt outputs ($M_SUBJECTS subjects)"
    python3 "$here/manifest.py" "$manifest" diff "$G/build-manifest.json" | sed 's/^/  /'
  fi
fi

echo "summary: $bad differ or failed, $skipped not in this run"
[ "$bad" -eq 0 ]
