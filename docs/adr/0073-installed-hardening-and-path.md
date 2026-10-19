# 0073: Installed hardening and command resolution

Status: accepted

## Context

The app inherits a GUI PATH that omits /usr/local/bin. AWS and generic Isotope
hardening detection inspect installed protection independently of PATH, while
several credential-helper hardeners included command resolution in their
hardened flag. Consequently, valid installations disappeared from Hardened
Tools and lost access to managed updates. The dashboard already suppresses
shell-specific Doctor warnings because its PATH does not describe the user's shell.

## Decision

Installed hardening status depends on each Tool's existing Target, configuration,
and helper checks, not the inspecting process's command resolution. Keep
command-resolution diagnostics in Doctor and install-time resolution checks in
hardeners. Apply this consistently to Terraform/OpenTofu, Railway, Fastly,
SQLCMD, Goat, Plumber, OrderCLI, OpenHue, Oxide, UAA, and Alibaba Cloud.
Alibaba Cloud retains the shared Isotope PATH diagnostic.

## Security consequences

This changes diagnostic classification, not authorization. Signature validation,
credential routing, helper validation, and runtime authorization remain intact.
A visible Hardened Tool does not assert that every shell invokes it. CLI Doctor
continues to report missing or shadowed commands. Do not fabricate a GUI PATH or
execute shell startup files to make installation detection succeed.
