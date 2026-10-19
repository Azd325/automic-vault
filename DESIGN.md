# Design context

## Companion Approval app

Scope: `src/ios/ApprovalApp`. Other product surfaces retain their existing design.
The authoritative model is [domain language](docs/domain-language.md),
[architecture](docs/architecture.md), and [positioning](docs/positioning.md).

The app helps a person review the complete operation and make a deliberate
Approval decision away from their Mac. Prioritize legibility and explicit scope.
Use native SwiftUI navigation, forms, controls, and system accessibility behavior.

- `ApprovalRootView` owns adaptive Requests/Settings navigation. Preserve each
  stack across resizing; notification review selects Requests and clears its path.
- `ApprovalDetailView` owns the review presentation. Keep the command, reason,
  metadata, and expanded details before the response controls in reading order.
  Constrain the review to 720 points inside the current safe area, without
  constraining the window. Content scrolls at narrow widths and large text sizes.
- `ApprovalMetadata` owns multiline request fields; full values remain selectable.
- `ApprovalModel` and `ApprovalSubscription` own pending, busy, error, authentication,
  and entitlement state. Views do not infer authorization from presentation state.
- Use semantic text styles, system grouped backgrounds, and the existing purple
  app tint from `ApprovalApp.swift`. Warnings use symbols and readable primary
  text; color alone never carries meaning. Reduce Motion disables transitions.
- SwiftUI owns date formatting, scrollbars, focus, and keyboard/pointer behavior.
  English copy uses canonical domain names; dates follow the system locale.

Before release, build with iOS 27.1 or later and inspect compact phone, unfolded
Duo, and resizable iPad windows in light/dark appearance and accessibility text
sizes. Check notification review, cancellation, busy responses, subscription
sheets, and rotation/folding without triggering an Approval. See
[Apple's Duo preparation guide](https://developer.apple.com/iphone-duo/prepare/).

## macOS Packages

`DashboardSidebarView` owns navigation; Packages reuses `DashboardModel` search
and selection, `DashboardRow`, and the existing `InfoBlock` detail presentation.
Native SwiftUI owns focus, keyboard navigation, scrollbars, and semantic colors.
Package rows include only installed releases managed directly by Automic Vault,
including installations needing repair. They show installation and update status
in text, including unknown and failed checks. Details give the existing Hardener
command. The shared refresh action reloads status; no package action grants
authority or bypasses the existing installation flow.
