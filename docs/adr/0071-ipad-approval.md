# ADR 0071: Extend iPhone Approval to iPad

Status: accepted; amends ADR 0012's iPad exclusion

## Context

The companion app must support iPhone Duo resizing and native iPad windows.
ADR 0012 excluded iPad from distribution even though the transport uses Apple
account possession and device registration rather than a phone-specific identity.

## Decision

Enable iPad distribution for the app and notification extension. Keep the
canonical feature name iPhone Approval. An eligible iPad joins the same account
and may carry Approval for any enrolled Mac, under the existing account-wide
trust model. This expands the supported Approval carriers; it creates no new
pairing, policy, or response format.

Retain iCloud Keychain possession, notification authorization, APNs registration,
locally verified subscription eligibility for allow responses, and optional
per-device biometric-only authentication. Denial remains available without
subscription or biometrics. The Mac still verifies the complete immutable
request, rejects stale responses, records, and enforces the decision.

Keep Mac Catalyst, designed-for-iPhone/iPad-on-Mac, and visionOS distribution
disabled. A keyboard, pointer, fold, rotation, or window resize never triggers
Approval. Native navigation and safe areas adapt the existing review controls;
no request detail or security warning is removed to fit a smaller window.

## Consequences

Every eligible iPad holding the account key joins the same trust surface as an
eligible iPhone. Biometric protection remains a separate choice on each device;
physical separation is not guaranteed when it is disabled. Account-wide recovery
continues to invalidate all registrations. No per-device revocation is added.

Build with iOS 27.1 or later for iPhone Duo's full edge-to-edge native bars and
verify fold transitions in its simulator before claiming full Duo validation.
The minimum supported operating system remains iOS/iPadOS 26.1.
