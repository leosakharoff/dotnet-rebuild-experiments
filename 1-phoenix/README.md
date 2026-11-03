# Rebuilding Phoenix

We test what is needed to rebuild a Phoenix release byte for byte across
machines. The method and results will be added here.

- [experiment-1.md](experiment-1.md): the short version of method and results,
  layer by layer.
- [figures/](figures/): `build-publish-pack` (the steps of `dotnet build`,
  `publish` and `pack`), `sdk-processes` (how one build chooses its
  processes' runtimes) and `npm-build` (the frontend's `npm ci` and
  `npm run build`). Each as `.drawio` and exported `.drawio.png`;
  [figures/README.md](figures/README.md) explains every file and step.
