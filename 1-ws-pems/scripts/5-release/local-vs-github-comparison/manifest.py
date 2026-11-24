#!/usr/bin/env python3
"""A release's build-manifest.json, read for rebuild.sh and compare.sh
(written 24 November 2026).

    manifest.py FILE shell            shell assignments (M_...) for eval
    manifest.py FILE diff REBUILT     FILE's subjects against REBUILT's

From v0.0.0-thesis.7 on, a WS.PEMS release carries build-manifest.json, an
in-toto Statement v1 written by the release job with the tag's
scripts/release/build-manifest.py and defined in the tag's
docs/release/build-manifest.md. It names the commit, the two values a
rebuild sets by hand (APP_VERSION and SOURCE_DATE_EPOCH), the pinned
inputs by URL and digest, and every file and image of the release by
digest (the subjects). It holds nothing about the run that made it, so a
rebuild that reproduces every subject regenerates it byte for byte.

shell prints one assignment per line:

    M_TAG M_COMMIT M_REPOSITORY      from externalParameters.source
    M_APP_VERSION M_SOURCE_DATE_EPOCH  from externalParameters.env
    M_WORKFLOW                       the release workflow's path
    M_SDK M_RUNTIME M_SDK_URL M_SDK_SHA512
    M_NODE M_NODE_URL M_NODE_SHA256
    M_NPM M_NPM_SHA512
    M_BUILDKIT M_BUILDKIT_SHA256     the builder's version and image digest
    M_REGISTRY M_IMAGES              from the image subjects' names
    M_SUBJECTS                       how many subjects

It stops, with exit 2, at anything it does not know: another predicate
type, a source path other than the whole tree, a value in env other than
the two above, or a missing pin. A value this reader skipped would be an
input the rebuild did not set.

diff prints one line per subject, "same" or "DIFF" with both digests, then
any other part of the two documents that differs, by its path, and a count.
Exit 0 when the two documents hold the same values, 1 when not. The byte
comparison (cmp) is compare.sh's; this says where a difference lies.

Python standard library only.
"""
import json
import re
import shlex
import sys

STATEMENT = "https://in-toto.io/Statement/v1"
TYPE = "https://github.com/Weel-Sandvig/WS.Phoenix/blob/main/docs/release/build-manifest.md#v1"
ENV = ("APP_VERSION", "SOURCE_DATE_EPOCH")
IMAGE = re.compile(r"pkg:docker/(?P<registry>.+)/(?P<name>[^/@]+)@(?P<tag>[^?]+)\?platform=linux%2Famd64")


def stop(message):
    sys.stderr.write(f"manifest.py: {message}\n")
    sys.exit(2)


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            document = json.load(f)
    except (OSError, ValueError) as error:
        stop(f"{path}: {error}")
    if document.get("_type") != STATEMENT:
        stop(f"{path}: not an in-toto Statement v1")
    if document.get("predicateType") != TYPE:
        stop(f"{path}: predicateType is {document.get('predicateType')!r}; this script reads {TYPE}")
    return document


def dependency(dependencies, pattern, what):
    """The one resolved dependency whose URI matches, with the match."""
    found = [(d, m) for d in dependencies for m in [re.fullmatch(pattern, d.get("uri", ""))] if m]
    if len(found) != 1:
        stop(f"expected one pinned {what} in resolvedDependencies, found {len(found)}")
    return found[0]


def digest(entry, algorithm, what):
    value = (entry.get("digest") or {}).get(algorithm, "")
    length = {"sha256": 64, "sha512": 128}[algorithm]
    if not re.fullmatch(rf"[0-9a-f]{{{length}}}", value):
        stop(f"{what}: no {algorithm} digest")
    return value


def read(document):
    definition = document["predicate"]["buildDefinition"]
    if definition.get("buildType") != TYPE:
        stop(f"buildType is {definition.get('buildType')!r}; this script reads {TYPE}")
    external = definition["externalParameters"]

    source = external["source"]
    uri = re.fullmatch(r"git\+(?P<repository>https://.+)@refs/tags/(?P<tag>[^@]+)", source.get("uri", ""))
    if not uri:
        stop(f"source.uri is not git+<repository>@refs/tags/<tag>: {source.get('uri')!r}")
    commit = (source.get("digest") or {}).get("gitCommit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        stop("source.digest.gitCommit is not a full commit")
    if source.get("path") != ".":
        stop(f"source.path is {source.get('path')!r}; the scripts build from the whole tree ('.')")

    env = external["env"]
    unknown = sorted(set(env) - set(ENV))
    if unknown:
        stop(f"env holds {', '.join(unknown)}; the scripts do not know where the build reads them")
    missing = [name for name in ENV if not env.get(name)]
    if missing:
        stop(f"env lacks {', '.join(missing)}")
    if not re.fullmatch(r"[0-9]+", env["SOURCE_DATE_EPOCH"]):
        stop("env.SOURCE_DATE_EPOCH is not seconds since 1970")

    dependencies = definition["resolvedDependencies"]
    sdk, _ = dependency(dependencies, r"https://.+/dotnet-sdk-[^/]+\.(tar\.gz|zip)", ".NET SDK archive")
    annotations = sdk.get("annotations") or {}
    if not annotations.get("sdk") or not annotations.get("runtime"):
        stop("the SDK archive has no sdk and runtime annotations")
    node, node_match = dependency(dependencies, r"https://nodejs\.org/dist/v([0-9.]+)/node-v[^/]+", "Node archive")
    npm, npm_match = dependency(dependencies, r"https://registry\.npmjs\.org/npm/-/npm-([0-9.]+)\.tgz", "npm")
    buildkit, buildkit_match = dependency(dependencies, r"pkg:docker/moby/buildkit@(.+)", "BuildKit image")

    registries, images = set(), []
    for subject in document["subject"]:
        m = IMAGE.fullmatch(subject["name"])
        if m:
            if m.group("tag") != uri.group("tag"):
                stop(f"image subject {subject['name']} is not for tag {uri.group('tag')}")
            registries.add(m.group("registry"))
            images.append(m.group("name"))
        elif subject["name"].startswith("pkg:"):
            stop(f"subject {subject['name']}: not an image name this script knows")
    if len(registries) > 1:
        stop(f"image subjects name several registries: {', '.join(sorted(registries))}")

    return {
        "M_TAG": uri.group("tag"),
        "M_COMMIT": commit,
        "M_REPOSITORY": uri.group("repository"),
        "M_APP_VERSION": env["APP_VERSION"],
        "M_SOURCE_DATE_EPOCH": env["SOURCE_DATE_EPOCH"],
        "M_WORKFLOW": (external.get("workflow") or {}).get("path", ""),
        "M_SDK": annotations["sdk"],
        "M_RUNTIME": annotations["runtime"],
        "M_SDK_URL": sdk["uri"],
        "M_SDK_SHA512": digest(sdk, "sha512", "the SDK archive"),
        "M_NODE": node_match.group(1),
        "M_NODE_URL": node["uri"],
        "M_NODE_SHA256": digest(node, "sha256", "the Node archive"),
        "M_NPM": npm_match.group(1),
        "M_NPM_SHA512": digest(npm, "sha512", "npm"),
        "M_BUILDKIT": buildkit_match.group(1),
        "M_BUILDKIT_SHA256": digest(buildkit, "sha256", "the BuildKit image"),
        "M_REGISTRY": "".join(registries),
        "M_IMAGES": " ".join(images),
        "M_SUBJECTS": str(len(document["subject"])),
    }


def subjects(document):
    out = {}
    for subject in document.get("subject", []):
        name = subject["name"]
        if name in out:
            stop(f"two subjects named {name}")
        out[name] = (subject.get("digest") or {}).get("sha256", "")
    return out


def paths(a, b, at=""):
    """The paths at which two JSON values differ."""
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                yield f"{at}.{key} (only in the {'published' if key in a else 'rebuilt'} one)"
            else:
                yield from paths(a[key], b[key], f"{at}.{key}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            yield from paths(x, y, f"{at}[{i}]")
    elif a != b:
        yield at


def diff(published, rebuilt):
    a, b = subjects(published), subjects(rebuilt)
    same = differ = 0
    for name in sorted(set(a) | set(b), key=lambda n: n.encode("utf-8")):
        if name not in b:
            print(f"DIFF  {name}: only in the published manifest ({a[name]})")
            differ += 1
        elif name not in a:
            print(f"DIFF  {name}: only in the rebuilt manifest ({b[name]})")
            differ += 1
        elif a[name] != b[name]:
            print(f"DIFF  {name}: published {a[name]}, rebuilt {b[name]}")
            differ += 1
        else:
            print(f"same  {name}  {a[name]}")
            same += 1
    rest_a = {k: v for k, v in published.items() if k != "subject"}
    rest_b = {k: v for k, v in rebuilt.items() if k != "subject"}
    others = list(paths(rest_a, rest_b))
    for path in others:
        print(f"DIFF  outside the subjects: {path}")
    print(f"subjects: {same} same, {differ} differ; {len(others)} other differences")
    return 0 if differ == 0 and not others else 1


def main():
    if len(sys.argv) == 3 and sys.argv[2] == "shell":
        for name, value in read(load(sys.argv[1])).items():
            print(f"{name}={shlex.quote(value)}")
    elif len(sys.argv) == 4 and sys.argv[2] == "diff":
        sys.exit(diff(load(sys.argv[1]), load(sys.argv[3])))
    else:
        sys.exit(__doc__.split("\n\n")[1])


if __name__ == "__main__":
    try:
        main()
    except KeyError as error:
        stop(f"the manifest has no {error}")
