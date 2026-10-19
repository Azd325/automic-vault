# App Store assets — 2026-10-19

Captured from the current native SwiftUI views at source commit 031c283f (production build 11), using synthetic requests in an isolated simulator-only copy. No Secret Values or real user data appear. Production source does not contain screenshot fixtures.

- iPhone 17 Pro: 1206 × 2622
- iPhone 17 Pro Max: 1320 × 2868
- iPad Pro 13-inch (M5): 2064 × 2752
- Simulator runtime: iOS 26.5; light appearance; 9:41 status bar.
- Each device: Approval, Request History, Settings, in that order.

The fixture preparation script records the temporary model-state substitutions. It runs only against `/tmp/av-submission-20261019`, replaces model startup, disables notification refresh, supplies synthetic subscription/connection state, and uses an unreachable local relay URL. It is not a production build step. The screenshots show real views; no screenshot pixels were edited or resized.

Build 11 was archived separately from the unmodified production runtime, uploaded through Xcode, and selected in App Store Connect. Its privacy manifest declares Device ID for app functionality, not linked to the user and not used for tracking, matching the existing App Store disclosure.

The website privacy and terms changes are committed in av.www as daf3e4e. Site preparation, translation checks, and 26 input tests passed; static deployment completed. A physical-device purchase and Mac-to-iPhone approval test was not performed during this metadata refresh.

App Store Connect saved build 11 and all nine screenshots. Both subscriptions and their group are in the existing draft (three items). Adding the app version is blocked until App Privacy responses are published. Apple presents an explicit agreement about accuracy, applicable law, and future updates; that agreement awaits user confirmation. No final review submission or release was performed.

After explicit user approval, the App Privacy disclosure was published. The app version was then successfully added to the existing draft: App Store Connect shows “Items Ready to Submit (4)” containing iOS 1.0 (11), both subscriptions, and the iPhone Approval subscription group. Final Submit for Review remains unclicked.
