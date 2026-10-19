from pathlib import Path
root=Path('/tmp/av-submission-20261019/src/ios/ApprovalApp')
p=root/'ApprovalApp.swift'
s=p.read_text()
old='    func start() async {\n        guard !started else { return }'
assert s.count(old)==1
s=s.replace(old,'''    func start() async {
        loadScreenshotFixtures()
        return
    }

    private func loadScreenshotFixtures() {
        let now = UInt64(Date().timeIntervalSince1970 * 1_000)
        func request(_ tool: String, _ command: String, _ reason: String) -> PhoneApprovalRequest {
            try! PhoneApprovalRequest(createdAtMilliseconds: now - 12000,
                macName: "MacBook Pro", launcher: "Terminal", tool: tool,
                command: command, cwd: "/Users/alex/Projects/website",
                secretNames: ["GITHUB_TOKEN"], reason: reason, risks: [.routine],
                details: [.init(title: "Target", rows: [.init(label: "Executable", value: "/usr/local/bin/gh")])])
        }
        let release = request("GitHub", "gh release create v2.4.0 --generate-notes", "This operation publishes a release on GitHub.")
        let pull = request("GitHub", "gh pr create --title 'Update documentation'", "This operation creates a pull request on GitHub.")
        let remove = request("GitHub", "gh repo delete alex/old-website --yes", "This operation deletes a GitHub repository.")
        activity = [
            .init(request: pull, outcome: .approved, respondedAtMilliseconds: now - 180000),
            .init(request: remove, outcome: .denied, respondedAtMilliseconds: now - 900000),
            .init(canceled: release, at: now - 3600000)
        ]
        pending = ProcessInfo.processInfo.arguments.contains("--approval") ? [release] : []
        notificationAuthorizationStatus = .authorized
        notificationsAreOff = false
        state = .connected
        isStarting = false
    }

    private func unusedProductionStart() async {
        guard !started else { return }''')
s=s.replace('    func refreshNotificationSettings() async {','    func refreshNotificationSettings() async { return }\n\n    private func unusedRefreshNotificationSettings() async {')
p.write_text(s)
p=root/'ApprovalSubscription.swift'; s=p.read_text(); s=s.replace('    func start() async {','    func start() async { state = .active; productsAvailable = true }\n\n    private func unusedProductionStart() async {'); p.write_text(s)
p=root/'ApprovalViews.swift'; s=p.read_text(); s=s.replace('@State private var selectedTab = ApprovalTab.requests','@State private var selectedTab = ProcessInfo.processInfo.arguments.contains("--settings") ? ApprovalTab.settings : ApprovalTab.requests'); p.write_text(s)
p=root/'Info.plist'; s=p.read_text().replace('https://approval-relay.automicvault.com','http://127.0.0.1:1'); p.write_text(s)
