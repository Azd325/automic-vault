# 0072: Explicit managed Tool updates

Status: accepted

## Context

Hardening establishes protection and can migrate credentials. Updating an
already managed release is a separate user intent. Package status belongs with
the Hardened Tool, rather than a separate dashboard destination or Doctor issue.

## Decision

Hardened Tools owns Update and Update All for installed directly managed
packages. `av harden` keeps valid installed releases; it still installs missing
or repairs invalid protection. Homebrew owns Homebrew-managed package updates.
There is no public update CLI command.

The app verifies that its installed CLI is current and trusted, then uses the
existing macOS administrator-approval flow. A private CLI operation accepts only
unique catalog package names, requires actual root privileges, rejects test
overrides, and rechecks installation and update eligibility. The app invokes it
with a cleared environment. Terraform version inspection drops child privileges
when invoked by the privileged updater. Downloads are constrained by the existing fixed
release sources, size limits, digest checks, and signature validation. Existing
privileged installers perform the replacement; metadata never grants authority.

The operation does not import credentials, edit configuration or Authorization
Policy, or install absent packages. Each package is independent: batch failures
are collected and shown, successful updates remain installed, and the dashboard
refreshes after success, cancellation, or failure. A missing or outdated CLI
must be installed through the existing verified CLI installer first.

## Consequences

Update approval is system administration, not a Secret Gate Approval. Existing
security and installer boundaries remain mandatory. A valid older release may
remain installed until the user chooses Update. Doctor continues to own broken
protection invariants; update-check failure is shown with the Tool.
