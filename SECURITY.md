# Security Policy

## Supported status

This repository is an experimental proof of concept. It is not a hardened multi-user service and does not include built-in authentication.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Report it privately through GitHub's private vulnerability reporting feature when available, or contact the repository owner directly through their verified GitHub profile.

Include the affected version, reproduction steps, impact, and any suggested mitigation. Do not include real credentials, customer information, or production network evidence.

## Deployment boundary

Run the service only on a trusted management network or behind an authenticated reverse proxy. Keep outbound access restricted to the data sources required for BGP analysis.

