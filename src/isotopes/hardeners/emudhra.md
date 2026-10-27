## What It Does

`av harden emudhra` previews removal of the emSign ECC Root CA - G3 and
AAA Certificate Services roots from `/etc/ssl/cert.pem`. Like `av harden sudo`,
it directs you to rerun as root:

```sh
sudo av harden emudhra
```

The privileged run validates the bundle, backs it up to `/etc/ssl/cert.pem.orig`
without overwriting an existing backup, removes only the two exact certificates,
and atomically installs a validated, nonempty bundle with mode 0644. It refuses
symlinked files, hard-linked files, and untrusted ownership or write permissions.
Other certificates and bundle comments are preserved. Scan owns the ongoing
check; this Hardener creates no Authorization Gate.

## Caveats

- Removing both roots also blocks legitimate sites that depend on them.
- This covers tools using `/etc/ssl/cert.pem`, not private CA bundles or all TLS clients.
- A macOS update can restore the roots. Scan the bundle again after updating.
- The backup retains the old trust roots; restoring it restores those trust paths.

Reference: [Apple's eMudhra advisory](https://support.apple.com/en-us/149555).
