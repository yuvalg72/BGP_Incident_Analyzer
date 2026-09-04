# Third-party notices

This file records third-party software that is directly incorporated into, installed by, or used to build BGP Incident Analyzer. It is informational and does not replace or modify any third-party license.

BGP Incident Analyzer's first-party source code and documentation are licensed under the Apache License 2.0 unless a file states otherwise. Third-party software remains under its own license terms and is not relicensed under Apache-2.0.

## CAIDA BGPStream container and libBGPStream

The production Dockerfile is based on the pinned CAIDA image:

`caida/bgpstream:2.3.0@sha256:d808116911c107926451f882295d85c80940285791ff38c7e6999976d355e3d4`

Upstream projects:

- CAIDA BGPStream Docker: https://github.com/CAIDA/bgpstream-docker
- CAIDA libBGPStream: https://github.com/CAIDA/libbgpstream

Primary upstream license: BSD-2-Clause.

Copyright (C) 2014 The Regents of the University of California.

A verbatim copy of the CAIDA BSD license is retained at `LICENSES/CAIDA-BGPStream-BSD-2-Clause.txt` and referenced from `NOTICE`.

CAIDA's libBGPStream documentation states that individual embedded and external components can carry different licenses and that file headers are authoritative. The currently documented upstream set includes:

- `cc-common`: components under BSD, MIT, and LGPL licenses.
- `libparsebgp`: BSD licensed.
- `bgpstream_utils_patricia.c`: MIT licensed.
- `libwandio`: required external dependency under LGPL v3.
- `librdkafka`: optional dependency under BSD and compatible licenses.
- SQLite: optional dependency released by its upstream project as public domain.

These upstream components retain their original copyright and license notices.

## Direct Python runtime dependencies

The exact versions distributed by this project are pinned in `requirements.txt`.

| Package | Version | License |
| --- | --- | --- |
| FastAPI | 0.141.1 | MIT |
| Starlette | 1.6.0 | BSD-3-Clause |
| Uvicorn | 0.52.4 | BSD-3-Clause |
| HTTPX | 0.28.1 | BSD-3-Clause |
| Pydantic | 2.13.5 | MIT |

Transitive Python packages installed by these dependencies retain their own licenses. Their installed distribution metadata and upstream license files remain authoritative for the exact dependency graph of a built image.

## Node development tooling

Node tooling is used only for repository asset rendering and JavaScript validation. `package-lock.json` records the resolved packages and their published license metadata. These packages are not copied into the production application image by this repository's Dockerfile.

## Distribution note

The repository currently validates container builds in CI but does not automatically publish a pre-built container image. Before adding image publication or another binary-distribution channel, audit the exact built image for all bundled third-party licenses and notices, preserve any source or relinking obligations that apply to LGPL components, and retain the licensing materials required by the pinned CAIDA base image and installed Python packages.

See `docs/licensing.md` for the project's licensing and release-maintenance policy.
