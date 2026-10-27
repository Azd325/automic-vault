# eMudhra TLS trust paths

Compromised eMudhra intermediate CA keys can be used to impersonate websites.
Some macOS command-line tools, including Apple's curl, trust roots in
`/etc/ssl/cert.pem` without consulting Apple's automatic certificate block.

## What we check

This macOS Detector checks the certificate bytes for two SHA-256 fingerprints:

- emSign ECC Root CA - G3: `86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b`
- AAA Certificate Services: `d7a7a0fb5d7e2731d771e9484ebcdef71d5f0c3e0a2948782bc83ee0ea699ef4`

The latter is the alternate trust path for Sectigo's cross-signed intermediates.
These root certificates are not themselves the compromised intermediate keys.
Unreadable or invalid bundles produce a Finding rather than a clean result.

## Mitigation

Run `av harden emudhra` to preview the change, then `sudo av harden emudhra`
to apply it. See the [hardening reference](../../hardeners/emudhra.md).

Only `/etc/ssl/cert.pem` is covered. Safari and Mail use Apple's system trust
handling; tools with private CA bundles need separate updates. A clean result
is not evidence that all TLS clients are protected.

Reference: [Apple's eMudhra advisory](https://support.apple.com/en-us/149555).
