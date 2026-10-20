import Darwin
import Foundation
import Security

@main struct Probe {
    static func main() {
        let mode = CommandLine.arguments[1]
        let pid = Int32(CommandLine.arguments[2])!
        let executable = URL(fileURLWithPath: CommandLine.arguments[3])
        if mode == "current" {
            guard liveExecutableCodeIdentity(pid: pid, executableURL: executable) != nil else { exit(1) }
        } else if mode == "dynamic-control" {
            var code: SecCode?
            guard SecCodeCopyGuestWithAttributes(nil, [
                kSecGuestAttributePid as String: NSNumber(value: pid),
                kSecGuestAttributeDynamicCode as String: kCFBooleanTrue as Any,
            ] as CFDictionary, [], &code) == errSecSuccess,
                let code, SecCodeCheckValidity(code, [], nil) == errSecSuccess else { exit(1) }
        } else if mode == "disk-control" {
            var code: SecStaticCode?
            guard SecStaticCodeCreateWithPath(executable as CFURL, [], &code) == errSecSuccess,
                  let code else { exit(1) }
            var info: CFDictionary?
            guard SecCodeCopySigningInformation(code, [], &info) == errSecSuccess else { exit(1) }
        } else {
            // Positive control: the pre-fix live lookup must enumerate the watched directory.
            var code: SecCode?
            guard SecCodeCopyGuestWithAttributes(nil,
                [kSecGuestAttributePid as String: NSNumber(value: pid)] as CFDictionary,
                [], &code) == errSecSuccess,
                let code, SecCodeCheckValidity(code, [], nil) == errSecSuccess else { exit(1) }
        }
    }
}
