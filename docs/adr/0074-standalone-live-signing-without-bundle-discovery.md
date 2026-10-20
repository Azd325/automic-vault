# ADR 0074: Verify standalone live code without bundle discovery

Status: accepted

## Problem

Issue #400 shows that a signed helper can reach CoreFoundation directory
enumeration through live code lookup. A kernel-reported Nix hard-link alias may
sit in a directory with hundreds of thousands of entries. The negative signing
prefilter from #398 cannot reject a legitimate Developer ID helper.

`kSecGuestAttributeDynamicCode` is insufficient. It avoids local bundle
discovery but can invoke `com.apple.CodeSigningHelper`, which performs ordinary
code lookup. A prototype appeared scan-free under local `readdir` observation
yet still took seconds in the large-directory fixture. The regression test
therefore observes both directory enumeration and signing-helper delegation.

## Decision

For standalone live executables, validate a fresh file signature through an
open descriptor, using Security.framework and the kernel-reported offset of
the loaded Mach-O slice. `/dev/fd/<descriptor>` avoids discovering a bundle in
the executable's parent directory. Reject nonregular files and failed opens.

Use `SecStaticCodeCheckValidity` with `kSecCSDoNotValidateExecutable` only.
Security.framework must still validate the signature, CodeDirectory,
non-executable components, and applicable resources. No entitlement, requirement,
or file metadata supplies authority before the validated CDHash matches the
kernel's current CDHash. A declared but unavailable external component fails
closed; an arbitrary directory does not become a trusted bundle.

Require fresh kernel `CS_SIGNED` and `CS_VALID` status. Use the live status for
runtime and platform eligibility, never a copied file's platform metadata.
Read kernel status, CDHash, and loaded-slice offset again after validation.
Require unchanged evidence and process execution: PID, nonzero PID version,
start time, effective user, and audit session. Unavailable or changed evidence
returns no verified identity. No `SecCode`, static code object, or successful
result is cached across calls.

Recognized bundle paths retain ordinary fresh dynamic validation, including
signed Info.plist validation. Path suffixes only select a verification
mechanism; both mechanisms must prove the signed live identity.

Helper attribution still compares the selected helper file with that live
identity, validates the parent app and applicable resource seal, then repeats
the live and selected-file checks with execution binding. Failed standalone
ancestor verification does not fall back to path-based signing discovery:
static metadata cannot repair failed live verification. App-bundle fallback
retains its existing behavior.

This refines ADR 0066's verification mechanism for standalone code. It retains
the same mapped-page integrity boundary: an unread damaged executable page
need not fail this check, but macOS must prevent its execution. It does not
weaken pre-execution Target verification, Launcher Bundle enrollment, parent
app validation, runtime requirements, policy, or record-before-release.

## Validation and limits

`scripts/test-live-signing-directory-scan.py` runs the production verifier.
Ordinary live lookup and ordinary static lookup are positive controls for the
directory observer; dynamic lookup is a positive control for signing-helper
delegation. The new path must succeed with neither. With a Developer ID
certificate, `--menubar` additionally exercises real standalone Launcher,
helper association, retained ancestry, integrity, and diagnostic call sites.
It then corrupts disk signature metadata while the kernel still classifies
the running fixture as a signing candidate, and requires rejection without a
directory-scanning fallback.

The Swift tests cover live/file mismatch, replacement, `exec`, exit, invalid
PIDs and file types, signed metadata, resource seals, runtime exceptions,
loaded universal slices, and kernel enforcement of damaged executable pages.

Local measurements on Apple silicon, macOS 27.0.1 (26A434), with 560,000
directory entries and a Developer ID-signed universal fixture:

| Probe | Directory reads observed | Signing-helper calls | Wall time |
| --- | ---: | ---: | ---: |
| Ordinary live lookup | 1,120,006 | 0 | 2.637 s |
| Ordinary disk lookup | 1,120,006 | 0 | 2.761 s |
| Dynamic-mode prototype | 0 | 1 | 1.839 s |
| Production live/file verifier | 0 | 0 | 0.017 s |

These are separate fresh probe processes under observation, whose logging adds
overhead to the scanning controls, not an end-to-end Secret Use benchmark.
The fixture verifies that the kernel reports the hard-link alias;
it does not reproduce Nix's optimize-while-running transition. The observer
does not trace every process on the system. The explicit delegation control
guards against the known false positive discovered in the prototype.

The Darwin queries are also used by Apple's code-signing implementation;
unsupported queries fail closed. Local execution does not certify every
supported macOS version. Ordinary app bundle inspection and other static
Target verification can still perform filesystem work. Confirmation with the
reporter's original workload remains necessary before closing #400.

Implementation references: Apple's
[kernel code identity checks](https://github.com/apple-oss-distributions/Security/blob/main/OSX/libsecurity_codesigning/lib/cskernel.cpp),
[static validation driver](https://github.com/apple-oss-distributions/Security/blob/main/OSX/libsecurity_codesigning/lib/StaticCode.cpp),
and [signing-helper lookup](https://github.com/apple-oss-distributions/Security/blob/main/OSX/libsecurity_codesigning/CodeSigningHelper/main.cpp).

Run the scan regression with:

```sh
python3 scripts/test-live-signing-directory-scan.py
AV_TEST_SIGNING_IDENTITY='Developer ID Application: …' \
  python3 scripts/test-live-signing-directory-scan.py --entries 560000 \
  --menubar src/menu-helper/.build/debug/AutomicVaultMenubar
```
