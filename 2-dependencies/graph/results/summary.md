# Dependency graph: the counts in the README

## The graph

- 341 package versions and 5 Phoenix projects; 896 edges, the union over the three programs; 9 of them join the runtime and host packs to the programs; 1 package without edges (dotnet-ef)
- ring 1: 87 (83 named by a project, 3 packs, 1 tool); ring 2: 118; ring 3: 111; 4 or more: 25
- 21 sectors; Other repositories: 68; no repository: 11
- 20 nodes have edges to two versions of one package (the programs lock some packages at different versions)
- packages.tsv marks 85 rows direct, for 82 names; by version, 83 are named by a project

## Status counts

- 2a: not in 2a 117, with configuration 98, did not build 97, unreproducible 25, as is 4
- 2b: not in 2b 143, no package 71, built, but differs 64, no recipe 41, from the release 22

## Reproduced packages and their dependencies

| part | reproduced | no dependency with files | all dependencies reproduced | a dependency differs | a dependency did not build or has no package to compare | only dependencies not attempted |
|---|---|---|---|---|---|---|
| 2a | 102 | 34 | 11 | 16 | 39 | 2 |
| 2b | 22 | 13 | 2 | 3 | 4 | 0 |

## Highest in-degree

- Humanizer.Core/2.14.1: 54 dependents; 2a with configuration; 2b no package
- Microsoft.Extensions.Logging.Abstractions/10.0.12: 24 dependents; 2a did not build; 2b no package
- Microsoft.Extensions.Logging/10.0.12: 22 dependents; 2a did not build; 2b no package
- Microsoft.Extensions.DependencyInjection.Abstractions/10.0.12: 21 dependents; 2a did not build; 2b no package
- Microsoft.Extensions.Configuration.Abstractions/10.0.12: 18 dependents; 2a did not build; 2b no package
- Microsoft.CodeAnalysis.Common/5.0.0: 15 dependents; 2a with configuration; 2b built, but differs
- Microsoft.Extensions.Options/10.0.12: 15 dependents; 2a did not build; 2b no package
- Newtonsoft.Json/13.0.4: 14 dependents; 2a with configuration; 2b no recipe
- Serilog/4.2.0: 13 dependents; 2a with configuration; 2b from the release
- System.Security.Cryptography.ProtectedData/9.0.11: 13 dependents; 2a did not build; 2b no recipe
- 48 of the 54 dependents of Humanizer.Core/2.14.1 are its culture packages
- Microsoft.Extensions package versions in each program's edges: WebAPI 4, BackgroundJobExecutor 36, DbMigrator 22

## Reached through one direct dependency only

- Microsoft.VisualStudio.Web.CodeGeneration.Design/10.0.2: 71 package versions reached only through it; 48 Humanizer culture packages, 1 with no files (N0), 22 that ship assemblies, 13 of these not attempted in 2b
