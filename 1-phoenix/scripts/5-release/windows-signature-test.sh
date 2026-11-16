#!/bin/bash
#
# The signing, tested with a test certificate (written 14 October 2026,
# rewritten to be read on 16 November 2026).
#
#   OUT=<private folder> PACK=<pack-release-zip.sh> [KEYS=<folder>] \
#       windows-signature-test.sh RELEASE REBUILD EPOCH TAG
#
# The release's Windows job signs every unsigned .exe and .dll with
# Weel-Sandvig's certificate. A signature holds its own timestamp, so two
# signings of one build differ, and a rebuild never matches a signed
# release byte for byte. deployment/signing/README.md checks a rebuild by
# copying the release's signatures onto it. This script tests that, with
# a test certificate instead of Weel-Sandvig's:
#
#   0  both builds unzipped into trees; the release's trees packed again
#      must give its zips back
#   1  the release signed twice; only the unsigned PE files may change,
#      and the two signings differ
#   2  the signatures removed again, and compared with the release
#   3  each signature copied onto the rebuild's file, keeping the file's
#      mode; compared with the signed release, verified, packed
#   4  three negative controls, each of which must fail: a changed byte,
#      another file's signature, a changed migrator
#
# RELEASE and REBUILD are the assets/ folders of two unsigned builds, as
# run-stage.sh 5-release keeps them:
# LABEL/store/control/source-root/assets. Take them from two runs, such as
# 5-release none and 5-release all. When a run is identical, its
# experiment-1 is a link to its control, so the two folders of one run are
# one build. Only the Windows files are used: the
# two zips and db/'s migrator. EPOCH is the commit's time, for the
# packing. TAG is the version in the file names, v0.0.0-thesis.
#
# The signing image is ws-signing:rb-test (docker build deployment/signing),
# run as the release job runs it. KEYS holds the test certificate
# (test.p12, its password in password.txt) and verify.pem: the test CA and
# the Microsoft root the timestamps chain to. The default is OUT/keys.
# When KEYS has no test.p12, the script makes the keys there: a throwaway
# CA and code-signing certificate, valid three days, made with the openssl
# commands of 14 October. Keys that expire within the hour stop the run.
# On 16 November the keys of 14 October, expired on 17 October, were used
# again: the signing image signed all 177 files, then failed to verify
# them, and so did every pasted signature.
#
# Trees go to /private/tmp/rb1-sign, lists and logs to OUT.
#
# On 14 October step 3 first ran without the trust file, and
# attach-signature refused all 177 signatures. Step 3 here is the version
# that worked, then step 3b in signing-paste.sh, which also held two of
# the negative controls. The two scripts were merged on 16 November 2026.

set -u
release_in=${1:?RELEASE} rebuild_in=${2:?REBUILD} EPOCH=${3:?EPOCH} TAG=${4:?TAG}
OUT=${OUT:?set OUT to a private data folder}
PACK=${PACK:?set PACK to scripts/pack-release-zip.sh from the commit}
KEYS=${KEYS:-$OUT/keys}

L=/private/tmp/rb1-sign
IMAGE=ws-signing:rb-test
ZIPS="ws-pems-win-x64 ws-pems-job-worker-win-x64"
# The Windows migrator's place in a tree: in win/, beside the zips'
# folders, as in the Windows job's release/win. The signing finds it there.
MIGRATOR=win/ws-pems-db-migrator-win-x64-$TAG.exe
# The trust file, for attach-signature and verify.
TRUST="-CAfile /keys/verify.pem -TSA-CAfile /keys/verify.pem"

# Makes the test keys in KEYS. verify.pem is the test CA and the signing
# image's Microsoft root.
make_keys() {
    local day; day=$(LC_ALL=C date +'%-d %b %Y')
    mkdir -p "$KEYS" && chmod 700 "$KEYS" && cd "$KEYS" && umask 077 &&
    openssl rand -hex 16 > password.txt &&
    openssl req -x509 -newkey rsa:3072 -sha256 -days 3 -nodes \
        -subj "/CN=RB1 throwaway test CA (thesis, $day)" -keyout ca.key -out ca.pem \
        -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign" &&
    openssl req -newkey rsa:3072 -sha256 -nodes \
        -subj "/CN=RB1 throwaway test code signing (thesis, $day)" -keyout cs.key -out cs.csr &&
    printf 'basicConstraints=CA:FALSE\nkeyUsage=critical,digitalSignature\nextendedKeyUsage=codeSigning\n' > cs.ext &&
    openssl x509 -req -in cs.csr -CA ca.pem -CAkey ca.key -CAcreateserial -days 3 -sha256 \
        -extfile cs.ext -out cs.pem &&
    SIGN_KEYSTORE_PASSWORD=$(cat password.txt) openssl pkcs12 -export -inkey cs.key -in cs.pem \
        -certfile ca.pem -name test -out test.p12 -passout env:SIGN_KEYSTORE_PASSWORD &&
    { cat ca.pem; docker run --rm --entrypoint cat "$IMAGE" /opt/signing/microsoft-identity-verification-root-2020.pem; } > verify.pem &&
    chmod 644 test.p12 verify.pem && chmod 755 .
}

# Runs the shell script on stdin in the signing image, from inside L. Only
# L and the keys are mounted. TRUST and MIGRATOR are passed in.
in_image() {
    docker run --rm -i --user "$(id -u):$(id -g)" -v "$L:$L" -v "$KEYS:/keys:ro" -w "$L" \
        -e TRUST="$TRUST" -e MIGRATOR="$MIGRATOR" --entrypoint bash "$IMAGE" -s
}

# Unzips an assets folder's two Windows zips into a tree, and copies its
# Windows migrator from db/ into the tree's win/.
unzip_tree() {  # assets folder, tree
    mkdir -p "$2/win"
    for z in $ZIPS; do
        unzip -q "$1/$z-$TAG.zip" -d "$2/win" || return 1
    done
    cp "$1/db/$(basename "$MIGRATOR")" "$2/$MIGRATOR"
}

# Packs a tree into zips as the release job packs them.
pack_tree() {  # tree, folder for the zips
    mkdir -p "$2"
    ( cd "$1/win" && for z in $ZIPS; do
        env PATH=/private/tmp/rb1-tools:/usr/bin SOURCE_DATE_EPOCH="$EPOCH" "$PACK" "$z" "$2/$z-$TAG.zip" || exit 1
      done )
}

# Writes "same FILE" or "differ FILE" for each file in a list.
compare_trees() {  # tree, tree, list
    while read -r f; do
        if cmp -s "$1/$f" "$2/$f"; then echo "same $f"; else echo "differ $f"; fi
    done < "$3"
}

# "N same, M differ" for a list from compare_trees.
count() {
    echo "$(grep -c '^same' "$1") same, $(grep -c '^differ' "$1") differ"
}

# One line, "same" or "DIFF", and what was compared.
check_same() {  # file, file, what
    if cmp -s "$1" "$2"; then echo "same  $3"; else echo "DIFF  $3"; fi
}

# Flips bit 0 of one byte: the middle one, or the one 4096 before the end.
flip_bit() {  # file, middle or end
    python3 - "$1" "$2" <<'PY'
import sys
path, where = sys.argv[1:3]
with open(path, "r+b") as f:
    size = f.seek(0, 2)
    i = size // 2 if where == "middle" else size - 4096
    f.seek(i)
    b = f.read(1)
    f.seek(i)
    f.write(bytes([b[0] ^ 1]))
print(f"flipped bit 0 of byte {i} of {size}")
PY
}

echo "== 0 unzip $(date +%T)"
rm -rf "$L" && mkdir -p "$L" "$OUT"
if [ ! -f "$KEYS/test.p12" ]; then
    ( make_keys ) > "$OUT/keys.log" 2>&1 || { echo "making the test keys failed, see keys.log"; exit 1; }
    echo "test keys made in $KEYS"
fi
openssl x509 -in "$KEYS/cs.pem" -noout -checkend 3600 > /dev/null ||
    { echo "the test certificate in $KEYS expires within the hour: $(openssl x509 -in "$KEYS/cs.pem" -noout -enddate)"; exit 1; }
unzip_tree "$release_in" "$L/release" && unzip_tree "$rebuild_in" "$L/rebuild" || exit 1
pack_tree "$L/release" "$L/zips/release"
for z in $ZIPS; do
    check_same "$release_in/$z-$TAG.zip" "$L/zips/release/$z-$TAG.zip" "$z zip, packed again"
done

# The PE files, and those the release left unsigned: the ones signing
# changes.
( cd "$L/release" && find win -type f \( -iname '*.exe' -o -iname '*.dll' \) | LC_ALL=C sort ) > "$L/pe-files.txt"
in_image > "$OUT/pe-before.txt" 2>&1 <<'EOF'
cd release && python3 /opt/signing/pe-signed.py < ../pe-files.txt
EOF
awk '$1 == "unsigned" { sub(/^unsigned /, ""); print }' "$OUT/pe-before.txt" > "$L/to-sign.txt"
cp "$L/pe-files.txt" "$L/to-sign.txt" "$OUT/"
echo "PE files $(wc -l < "$L/pe-files.txt"), unsigned $(wc -l < "$L/to-sign.txt")"

echo "== 1 sign the release twice $(date +%T)"
for c in signed-1 signed-2; do
    cp -a "$L/release" "$L/$c"
    docker run --rm --user "$(id -u):$(id -g)" -v "$L:$L" -v "$KEYS:/keys:ro" -w "$L/$c" \
        -e SIGN_WITH_KEYSTORE=/keys/test.p12 -e SIGN_KEYSTORE_PASSWORD="$(cat "$KEYS/password.txt")" \
        -e SIGN_KEYSTORE_ALIAS=test -e VERIFY_CAFILE=/keys/verify.pem "$IMAGE" win > "$OUT/sign-$c.log" 2>&1
    rc=$?
    echo "sign $c: exit $rc"
    [ "$rc" = 0 ] || { echo "signing failed, see sign-$c.log"; exit 1; }
    pack_tree "$L/$c" "$L/zips/$c"
done
compare_trees "$L/release" "$L/signed-1" "$L/pe-files.txt" > "$OUT/release-vs-signed-1.txt"
compare_trees "$L/release" "$L/signed-2" "$L/pe-files.txt" > "$OUT/release-vs-signed-2.txt"
compare_trees "$L/signed-1" "$L/signed-2" "$L/pe-files.txt" > "$OUT/signed-1-vs-signed-2.txt"
for t in release-vs-signed-1 release-vs-signed-2 signed-1-vs-signed-2; do
    echo "$t: $(count "$OUT/$t.txt")"
done
if grep '^differ' "$OUT/release-vs-signed-1.txt" | sed 's/^differ //' | cmp -s - "$L/to-sign.txt"; then
    echo "same  the files signing changed, against the unsigned ones"
else
    echo "DIFF  the files signing changed, against the unsigned ones"
fi
( cd "$L/release" && find win -type f ! \( -iname '*.exe' -o -iname '*.dll' \) | LC_ALL=C sort |
    while read -r f; do cmp -s "$f" "../signed-1/$f" || echo "$f"; done ) > "$OUT/non-pe-changed.txt"
echo "non-PE files changed by signing: $(wc -l < "$OUT/non-pe-changed.txt")"
for z in $ZIPS; do
    check_same "$L/zips/signed-1/$z-$TAG.zip" "$L/zips/signed-2/$z-$TAG.zip" "$z zip, signed-1 against signed-2"
done

echo "== 2 remove the signatures $(date +%T)"
in_image <<'EOF'
while read -r f; do
    mkdir -p "stripped/$(dirname "$f")"
    osslsigncode remove-signature -in "signed-1/$f" -out "stripped/$f" > /dev/null 2>&1 || echo "FAILED $f"
done < to-sign.txt
EOF
# For each file that differs: both sizes, the number of differing bytes,
# and the offsets of the first four.
( cd "$L" && while read -r f; do
    if cmp -s "release/$f" "stripped/$f"; then
        echo "same $f"
    else
        echo "differ $f $(stat -c %s "release/$f") $(stat -c %s "stripped/$f")" \
             "$(cmp -l "release/$f" "stripped/$f" 2> /dev/null | wc -l)" \
             "$(cmp -l "release/$f" "stripped/$f" 2> /dev/null | head -4 | awk '{printf "%d ", $1 - 1}')"
    fi
  done < to-sign.txt ) > "$OUT/strip.txt"
echo "stripped: $(count "$OUT/strip.txt"), against the release"
# Names the differing bytes: the PE checksum, the certificate table entry,
# or another offset. One line per kind, with how many files have it.
python3 - "$L" "$OUT/strip.txt" > "$OUT/strip-offsets.txt" <<'PY'
import struct, sys
root, listing = sys.argv[1:3]
kinds = {}
for line in open(listing):
    parts = line.split()
    if parts[0] != "differ":
        continue
    f = parts[1]
    data = open(f"{root}/release/{f}", "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    checksum = opt + 64
    certdir = opt + (112 if magic == 0x20B else 96) + 4 * 8
    names = []
    for o in map(int, parts[5:]):
        if checksum <= o < checksum + 4: names.append("checksum")
        elif certdir <= o < certdir + 8: names.append("certificate-table entry")
        else: names.append(f"offset {o}")
    kind = ", ".join(sorted(set(names))) + (f"; size {parts[2]} -> {parts[3]}" if parts[2] != parts[3] else "")
    kinds.setdefault(kind, []).append(f)
for kind, files in sorted(kinds.items(), key=lambda kv: -len(kv[1])):
    print(f"{len(files)} files: {kind}; e.g. {files[0]}")
PY
cat "$OUT/strip-offsets.txt"

echo "== 3 copy the signatures onto the rebuild $(date +%T)"
cp -a "$L/rebuild" "$L/pasted"
in_image > "$OUT/paste.log" 2>&1 <<'EOF'
while read -r f; do
    mkdir -p "signatures/$(dirname "$f")"
    osslsigncode extract-signature -in "signed-1/$f" -out "signatures/$f.p7" > /dev/null 2>&1 ||
        echo "EXTRACT FAILED $f"
    if osslsigncode attach-signature $TRUST -sigin "signatures/$f.p7" -in "rebuild/$f" -out "pasted/$f.tmp" > /tmp/a.log 2>&1; then
        chmod --reference="rebuild/$f" "pasted/$f.tmp" && mv "pasted/$f.tmp" "pasted/$f"
    else
        echo "ATTACH FAILED $f"
        tail -3 /tmp/a.log
    fi
done < to-sign.txt
EOF
echo "extract or attach failures: $(grep -c 'FAILED' "$OUT/paste.log")"
compare_trees "$L/signed-1" "$L/pasted" "$L/pe-files.txt" > "$OUT/paste.txt"
echo "pasted against signed-1: $(count "$OUT/paste.txt")"
( cd "$L/signed-1" && find win -type f -printf '%m %p\n' | LC_ALL=C sort ) > "$OUT/modes-signed-1.txt"
( cd "$L/pasted" && find win -type f -printf '%m %p\n' | LC_ALL=C sort ) > "$OUT/modes-pasted.txt"
check_same "$OUT/modes-signed-1.txt" "$OUT/modes-pasted.txt" \
    "every file's mode and path, pasted against signed-1 ($(wc -l < "$OUT/modes-signed-1.txt") files)"
in_image > "$OUT/paste-verify.txt" <<'EOF'
while read -r f; do
    if osslsigncode verify $TRUST -ignore-crl -in "pasted/$f" > /tmp/v.log 2>&1 &&
       grep -q 'Timestamp Server Signature verification: ok' /tmp/v.log; then
        echo "ok $f"
    else
        echo "FAILED $f"
    fi
done < to-sign.txt
EOF
echo "pasted signatures verified: $(grep -c '^ok' "$OUT/paste-verify.txt") ok, $(grep -c '^FAILED' "$OUT/paste-verify.txt") failed"
pack_tree "$L/pasted" "$L/zips/pasted"
for z in $ZIPS; do
    check_same "$L/zips/signed-1/$z-$TAG.zip" "$L/zips/pasted/$z-$TAG.zip" "$z zip, pasted against signed-1"
done
check_same "$L/signed-1/$MIGRATOR" "$L/pasted/$MIGRATOR" "the migrator, pasted against signed-1"

echo "== 4 negative controls, each must fail $(date +%T)"
mkdir -p "$L/negative"
cp "$L/rebuild/win/ws-pems-win-x64/ApplicationCore.dll" "$L/negative/changed-byte.dll"
flip_bit "$L/negative/changed-byte.dll" middle
cp "$L/rebuild/win/ws-pems-win-x64/ApplicationCore.dll" "$L/negative/wrong-signature.dll"
cp "$L/rebuild/$MIGRATOR" "$L/negative/changed-migrator.exe"
flip_bit "$L/negative/changed-migrator.exe" end
in_image <<'EOF'
# Attaches a signature and prints the exit status and the verdict.
attach() {  # what, signature, file
    osslsigncode attach-signature $TRUST -sigin "$2" -in "$3" -out "$3.signed" > "$3.log" 2>&1
    echo "$1: attach exit $?"
    grep -E 'MISMATCH|Signature verification' "$3.log" | head -2
}
attach "a. one byte changed" signatures/win/ws-pems-win-x64/ApplicationCore.dll.p7 negative/changed-byte.dll
attach "b. another file's signature" signatures/win/ws-pems-win-x64/Infrastructure.dll.p7 negative/wrong-signature.dll
attach "c. the migrator changed" "signatures/$MIGRATOR.p7" negative/changed-migrator.exe
EOF
echo "== end $(date +%T)"
