# Layer 4: zip

This layer has no script of its own.

- `../shared/run.sh Z AXIS` builds the release (mode `R`) and then packs the
  zips two times: as CI packs them (`zip -r`) in `release/zip-ci`, and
  normalised in `release/zip-norm`. Set `ZEPOCH` to the commit's time, for
  example `ZEPOCH=$(git log -1 --format=%ct)`.
- `../ci/ci-compare.sh` compares CI's zips with a local rebuild, entry by entry.
