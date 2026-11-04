# Rebuild against nuget.org, summary (198 packages)

## 1. The release build

### All 198

| group | match or outcome | packages |
|---|---|---|
| reproduced (22) | identical | 14 |
|  | identical without signatures | 8 |
| built, but differs (64) | same code | 9 |
|  | other code | 55 |
| not built (112) | no package | 71 |
|  | no recipe | 41 |
| | total | 198 |

### Third-party (59)

| group | match or outcome | packages |
|---|---|---|
| reproduced (17) | identical | 14 |
|  | identical without signatures | 3 |
| built, but differs (25) | same code | 9 |
|  | other code | 16 |
| not built (17) | no package | 12 |
|  | no recipe | 5 |
| | total | 59 |

### Microsoft (139)

| group | match or outcome | packages |
|---|---|---|
| reproduced (5) | identical without signatures | 5 |
| built, but differs (39) | other code | 39 |
| not built (95) | no package | 59 |
|  | no recipe | 36 |
| | total | 139 |

### Not built, by cause

| outcome | cause | packages |
|---|---|---|
| no package | the build failed | 63 |
| no package | the build ran, but packed no package of that name and version | 7 |
| no package | the runner job left no output | 1 |
| no recipe | the compiler is in no public SDK | 25 |
| no recipe | the compiler ran on .NET Framework, which no dotnet SDK bundles | 10 |
| no recipe | the commit is not reachable at the repository | 2 |
| no recipe | no single project with the assembly name | 2 |
| no recipe | the derivation failed | 1 |
| no recipe | no PDB with a compiler record | 1 |

### Against part 2a's levels

Of the 86 packages compared, 86 have a package listing. Level 1 (package file): 0; nuget.org's package carries its repository signature (`.signature.p7s`) in 86 of them, which no rebuild can produce. Level 2 (package entries without NuGet's packaging files and that signature): 9. Level 3 (assemblies: every DLL under lib/, ref/, runtimes/): 11. The DLL that ships in Phoenix, identical: 14.

### A against A2 (our own repeat)

Of the 86 compared: equal 76, differ 9, not compared 1. Differ: Microsoft.IdentityModel.Abstractions 8.23.0, Microsoft.IdentityModel.JsonWebTokens 8.23.0, Microsoft.IdentityModel.Logging 8.23.0, Microsoft.IdentityModel.LoggingExtensions 8.7.0, Microsoft.IdentityModel.Protocols 8.7.0, Microsoft.IdentityModel.Protocols.OpenIdConnect 8.7.0, Microsoft.IdentityModel.Tokens 8.23.0, Microsoft.IdentityModel.Validators 8.7.0, System.IdentityModel.Tokens.Jwt 8.23.0.

### Per package, by match

- identical (14): CsvHelper 33.1.0, FluentValidation.DependencyInjectionExtensions 11.11.0, Markdig 1.2.0, Npgsql 10.0.3, Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3, ScottPlot 5.1.57, Serilog.Sinks.File 6.0.0, Serilog.Sinks.Seq 9.0.0, TimeZoneConverter 7.0.0, UnitsNet 6.0.0-pre012, RBush 4.0.0, FluentValidation 11.11.0, Serilog 4.2.0, Ardalis.GuardClauses 5.0.0
- identical without signatures (8): Hangfire.InMemory 1.0.0, NodaTime 3.2.0, Cronos 0.9.0, Microsoft.Identity.Abstractions 9.0.0, Microsoft.Identity.Web.Certificateless 3.8.2, Microsoft.Identity.Web.Diagnostics 3.8.2, Microsoft.Identity.Web.TokenCache 3.8.2, Microsoft.OpenApi 1.6.22
- same code (9): Ardalis.Specification 8.0.0, Ardalis.Specification.EntityFrameworkCore 8.0.0, AutoMapper 13.0.1, MediatR 12.4.1, Quartz 3.13.1, Quartz.AspNetCore 3.13.1, Quartz.Extensions.DependencyInjection 3.13.1, Quartz.Extensions.Hosting 3.13.1, SendGrid 9.29.3
- other code (55): Bogus 35.6.1, ExCSS 4.3.1, FluentModbus 5.3.2, Google.Protobuf 3.21.9, MediatR.Contracts 2.0.1, MediatR.Extensions.Microsoft.DependencyInjection 11.1.0, Serilog.Settings.Configuration 8.0.4, SharpZipLib 1.4.2, ShimSkiaSharp 5.1.1, Stateless 5.16.0, Swashbuckle.AspNetCore.Annotations 7.2.0, Swashbuckle.AspNetCore.ReDoc 7.2.0, Swashbuckle.AspNetCore.Swagger 7.2.0, Swashbuckle.AspNetCore.SwaggerGen 7.2.0, Swashbuckle.AspNetCore.SwaggerUI 7.2.0, YamlDotNet 16.2.1, Azure.Communication.Email 1.0.1, Azure.Core 1.50.0, Azure.Identity 1.17.1, Azure.Security.KeyVault.Certificates 4.6.0, Azure.Security.KeyVault.Secrets 4.6.0, Azure.Storage.Blobs 12.20.0, Azure.Storage.Common 12.19.0, Microsoft.Build.Framework 18.0.2, Microsoft.CodeAnalysis.CSharp 5.0.0, Microsoft.CodeAnalysis.CSharp.Features 5.0.0, Microsoft.CodeAnalysis.CSharp.Workspaces 5.0.0, Microsoft.CodeAnalysis.Common 5.0.0, Microsoft.CodeAnalysis.Features 5.0.0, Microsoft.CodeAnalysis.Scripting.Common 5.0.0, Microsoft.CodeAnalysis.Workspaces.Common 5.0.0, Microsoft.Data.Sqlite.Core 10.0.12, Microsoft.DiaSymReader 2.0.0, Microsoft.EntityFrameworkCore 10.0.12, Microsoft.EntityFrameworkCore.Abstractions 10.0.12, Microsoft.EntityFrameworkCore.Design 10.0.12, Microsoft.EntityFrameworkCore.InMemory 10.0.12, Microsoft.EntityFrameworkCore.Relational 10.0.12, Microsoft.EntityFrameworkCore.SqlServer 10.0.12, Microsoft.EntityFrameworkCore.Sqlite.Core 10.0.12, Microsoft.IO.RecyclableMemoryStream 3.0.0, Microsoft.Identity.Web 3.8.2, Microsoft.Identity.Web.Certificate 3.8.2, Microsoft.Identity.Web.TokenAcquisition 3.8.2, Microsoft.IdentityModel.Abstractions 8.23.0, Microsoft.IdentityModel.JsonWebTokens 8.23.0, Microsoft.IdentityModel.Logging 8.23.0, Microsoft.IdentityModel.LoggingExtensions 8.7.0, Microsoft.IdentityModel.Protocols 8.7.0, Microsoft.IdentityModel.Protocols.OpenIdConnect 8.7.0, Microsoft.IdentityModel.Tokens 8.23.0, Microsoft.IdentityModel.Validators 8.7.0, Serilog.Extensions.Logging 8.0.0, System.ClientModel 1.8.0, System.IdentityModel.Tokens.Jwt 8.23.0

## 2. The publisher's build (Arcade repositories)

### All 96, Roslyn without the release-branding properties

| group | match or outcome | packages |
|---|---|---|
| reproduced (35) | identical without signatures | 35 |
| built, but differs (58) | same code | 29 |
|  | other code | 29 |
| not built (3) | no package | 3 |
| | total | 96 |

### On windows-2022 (42)

| group | match or outcome | packages |
|---|---|---|
| reproduced (35) | identical without signatures | 35 |
| built, but differs (4) | same code | 4 |
| not built (3) | no package | 3 |
| | total | 42 |

### On Linux (the VMR builds) (54)

| group | match or outcome | packages |
|---|---|---|
| built, but differs (54) | same code | 25 |
|  | other code | 29 |
| | total | 54 |

### All 96, every repository with the release-branding properties (Roslyn too)

| group | match or outcome | packages |
|---|---|---|
| reproduced (27) | identical without signatures | 27 |
| built, but differs (66) | same code | 29 |
|  | other code | 37 |
| not built (3) | no package | 3 |
| | total | 96 |

## 3. Per package

The category comes from the release build alone. The publisher's build, run for the Arcade packages, is a diagnostic beside it.

| category | packages | publisher's build ran | reproduces | without the Roslyn rule |
|---|---|---|---|---|
| from the release | 22 | 0 | 0 | 0 |
| not reproduced | 64 | 17 | 8 | 1 |
| no package | 71 | 51 | 5 | 4 |
| no recipe | 41 | 28 | 22 | 22 |
| total | 198 | 96 | 35 | 27 |

Not reproduced, by match: same code 9, other code 55.
