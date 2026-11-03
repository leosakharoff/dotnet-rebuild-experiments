# Rebuilding Phoenix

We test what is needed to rebuild a Phoenix release byte for byte across
machines. The method and results will be added here.

- [experiment-1.md](experiment-1.md): the short version of method and results,
  layer by layer.
- [figures/](figures/): `build-publish-pack` (the steps of `dotnet build`,
  `publish` and `pack`) and `sdk-processes` (how one build chooses its
  processes' runtimes). Each as `.drawio` and exported `.drawio.png`.
