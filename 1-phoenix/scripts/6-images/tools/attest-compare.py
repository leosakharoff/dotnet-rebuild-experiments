#!/usr/bin/env python3
"""Do two builds with attestations give the same image but another index?

    attest-compare.py A.oci.tar B.oci.tar

The release pushes each image with provenance and an SBOM (buildx
--provenance --sbom), and its tag points at the index that holds the image
and the attestations. Written on 14 October 2026 for W65 (Speciale2026
note 2026-10-14-phoenix-image-attestations): the image was the same, the
index and the attestations were not.

Prints whether the image manifest, the index around it and the attestation
manifest are the same, and for each attestation (provenance, SBOM) the paths
of the JSON fields that differ. Field paths only, no values, so the output
can go in a public log.
"""
import json
import sys
import tarfile


def load(path):
    tar = tarfile.open(path)

    def blob(digest):
        return tar.extractfile("blobs/sha256/" + digest.split(":")[1]).read()

    top = json.loads(tar.extractfile("index.json").read())["manifests"][0]
    if not top["mediaType"].endswith("image.index.v1+json"):
        return {"index": None, "image": top["digest"], "attestation": None, "statements": {}}
    entries = json.loads(blob(top["digest"]))["manifests"]
    kind = lambda m: m.get("annotations", {}).get("vnd.docker.reference.type")
    images = [m["digest"] for m in entries if kind(m) != "attestation-manifest"]
    attestations = [m["digest"] for m in entries if kind(m) == "attestation-manifest"]
    statements = {}
    for digest in attestations:
        for layer in json.loads(blob(digest))["layers"]:
            statement = json.loads(blob(layer["digest"]))
            statements[statement["predicateType"]] = statement
    return {"index": top["digest"], "image": " ".join(images),
            "attestation": " ".join(attestations) or None, "statements": statements}


def fields(value, path=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from fields(item, f"{path}.{key}")
    elif isinstance(value, list):
        for number, item in enumerate(value):
            yield from fields(item, f"{path}[{number}]")
    else:
        yield path, value


a, b = load(sys.argv[1]), load(sys.argv[2])
for key in ("image", "index", "attestation"):
    print(f"{key:12} {'same' if a[key] == b[key] else 'DIFF'}  {a[key]}  {b[key]}")
for kind in sorted(set(a["statements"]) | set(b["statements"])):
    fa = dict(fields(a["statements"].get(kind, {})))
    fb = dict(fields(b["statements"].get(kind, {})))
    differ = sorted(path for path in set(fa) | set(fb) if fa.get(path) != fb.get(path))
    print(f"{kind}: {len(differ)} of {len(set(fa) | set(fb))} fields differ")
    for path in differ[:40]:
        print(f"    {path}")
    if len(differ) > 40:
        print(f"    ... and {len(differ) - 40} more")
