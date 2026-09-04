# Licensing and third-party software

## Project license

BGP Incident Analyzer's first-party source code and documentation are licensed under the Apache License 2.0 unless a file explicitly states otherwise. The complete license text is in the repository root `LICENSE` file.

Apache-2.0 is also declared through machine-readable metadata where the repository has a native field for it, including `package.json` and the OCI image license label in `Dockerfile`.

## Third-party boundary

Third-party software is not relicensed under Apache-2.0. It remains subject to the license terms supplied by its copyright holders.

`THIRD_PARTY_NOTICES.md` records the directly incorporated runtime and build dependencies that require licensing context. The CAIDA BGPStream BSD notice used by the pinned container base is retained verbatim at `LICENSES/CAIDA-BGPStream-BSD-2-Clause.txt` and summarized in `NOTICE`.

The CAIDA BGPStream project also documents embedded and external components under BSD, MIT, LGPL, and other compatible terms. In particular, its required `libwandio` dependency is licensed under LGPL v3. Upstream file headers and license files are authoritative when they are more specific than this repository's summary.

## Container distribution boundary

The Dockerfile builds on a digest-pinned CAIDA BGPStream image and copies this project's `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`, and `LICENSES/` directory into `/usr/share/licenses/bgp-incident-analyzer/` in the resulting image.

The repository's CI builds and tests that image, but it does not automatically publish a pre-built image. Before introducing image publication, release artifacts, installers, or another binary-distribution channel:

1. Reconfirm the exact base-image digest and its upstream license notices.
2. Inventory the exact third-party packages present in the distributable artifact, including transitive Python and operating-system packages.
3. Preserve required copyright, attribution, and license texts.
4. Satisfy any source-availability or relinking obligations that apply to LGPL components in the actual distribution model.
5. Generate or retain an SBOM and license inventory when a release pipeline starts publishing binary artifacts.
6. Verify that the final artifact still contains this project's licensing materials.

This boundary prevents a source-code license decision from being mistaken for a complete legal review of every future binary distribution.

## Contributions

Unless a contributor explicitly states otherwise, a contribution intentionally submitted for inclusion in this repository is provided under Apache License 2.0 Section 5, without additional terms or conditions. A separate contribution agreement, if one is introduced later, can supersede that default only where its terms expressly apply.

Contributors must not submit code, assets, generated output, datasets, or documentation that they do not have the right to contribute. New third-party code or dependencies must retain their original notices and must be reflected in `THIRD_PARTY_NOTICES.md` when required.

## Maintenance controls

Licensing is treated as a release control rather than a one-time repository decoration.

When dependencies, container bases, bundled assets, or distribution methods change:

- review the relevant upstream license and notice files;
- update `THIRD_PARTY_NOTICES.md` and `LICENSES/` when the obligations or directly bundled components change;
- update machine-readable license metadata if the project license changes;
- run `python scripts/validate_licenses.py` and `python scripts/validate_repository.py`;
- allow CI to rebuild the exact container candidate before release.

The licensing validator checks repository-level consistency. It does not replace legal review when ownership, patent rights, third-party compatibility, or a new distribution model creates a material legal question.
