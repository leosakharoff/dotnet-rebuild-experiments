#!/usr/bin/env bash
# Would a rebuild a year from now still pass the MCP images' build tests?
#
#   C=<clean clone> OUT=<folder> [SHIFT=+365d] faketime-tests.sh
#
# The MCP server and the chat server run their tests inside the image
# build, so a test that reads the date can fail a later rebuild. Written on
# 21 October 2026 (Speciale2026 note 2026-10-21-phoenix-pins, item 9): a
# year ahead, both images' tests passed.
#
# Each Dockerfile is copied with one step added to its build stage:
# faketime from the image's Debian snapshot, and the test command run
# under libfaketime, SHIFT ahead. The build stops after that stage and
# exports nothing.
set -uo pipefail
C=${C:?a clean clone} OUT=${OUT:?a folder} SHIFT=${SHIFT:-+365d}
mkdir -p "$OUT"
for img in server chat-server; do
  f=$C/mcp/Dockerfile
  [ "$img" = chat-server ] && f=$C/mcp/chat-server/Dockerfile
  python3 - "$f" "$OUT/$img.Dockerfile" "$SHIFT" <<'EOF'
import sys
src, dst, shift = sys.argv[1:4]
s = open(src).read()
fake = f"env LD_PRELOAD=/usr/lib/x86_64-linux-gnu/faketime/libfaketimeMT.so.1 FAKETIME={shift}"
add = ("ARG DEBIAN_SNAPSHOT\n"
       "RUN rm -f /etc/apt/sources.list.d/debian.sources \\\n"
       "    && echo \"deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] http://snapshot.debian.org/archive/debian/$DEBIAN_SNAPSHOT bookworm main\" > /etc/apt/sources.list.d/snapshot.list \\\n"
       "    && apt-get -o Acquire::Check-Valid-Until=false update && apt-get install -y --no-install-recommends faketime\n")
old = "RUN npm run build \\\n    && npm test \\\n"
assert s.count(old) == 1, src
s = s.replace(old, add + f"RUN npm run build \\\n    && {fake} date -u \\\n    && {fake} npm test \\\n")
open(dst, "w").write(s)
EOF
  echo "$img $SHIFT start $(date +%T)"
  docker buildx build --builder rb1 --no-cache --progress plain --target build -f "$OUT/$img.Dockerfile" \
    --output type=cacheonly "$C/mcp" > "$OUT/$img$SHIFT.log" 2>&1
  echo "$img $SHIFT exit $? $(date +%T)"
done
