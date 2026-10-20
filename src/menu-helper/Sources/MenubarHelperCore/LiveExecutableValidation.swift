import CProcessInfo
import Darwin
import Foundation
import Security

public struct LiveProcessSigningInformation {
    public let information: [CFString: Any]
    public let matchesRequirement: Bool
    fileprivate let offset: Int64
}

/// Fresh signing evidence bound to one process execution. No Security object escapes or is cached.
public func liveProcessSigningInformation(pid: pid_t, requirement: SecRequirement? = nil) -> LiveProcessSigningInformation? {
    guard pid > 0 else { return nil }
    var before = AVProcessIdentity()
    var evidence = AVProcessSigningEvidence()
    guard av_process_identity(pid, &before), before.pidversion > 0,
          av_process_signing_evidence(pid, &evidence) else { return nil }
    let path = withUnsafePointer(to: &before.path) {
        $0.withMemoryRebound(to: CChar.self, capacity: 4096) { String(cString: $0) }
    }
    // Paths select a verification mechanism, never identity or eligibility.
    let bundled = URL(fileURLWithPath: path).pathComponents.contains {
        ["app", "framework", "bundle", "xpc", "appex"].contains(
            URL(fileURLWithPath: $0).pathExtension.lowercased()
        )
    }
    let informationFlags = SecCSFlags(rawValue: kSecCSSigningInformation | kSecCSRequirementInformation)
    var dictionary: [CFString: Any]
    let matchesRequirement: Bool
    if bundled {
        var live: SecCode?
        guard SecCodeCopyGuestWithAttributes(nil,
            [kSecGuestAttributePid as String: NSNumber(value: pid)] as CFDictionary, [], &live) == errSecSuccess,
            let live, SecCodeCheckValidity(live, [], nil) == errSecSuccess else { return nil }
        var info: CFDictionary?
        guard SecCodeCopySigningInformation(unsafeBitCast(live, to: SecStaticCode.self),
            SecCSFlags(rawValue: informationFlags.rawValue | kSecCSDynamicInformation), &info) == errSecSuccess,
            let values = info as? [CFString: Any] else { return nil }
        dictionary = values
        matchesRequirement = requirement.map { SecCodeCheckValidity(live, [], $0) == errSecSuccess } ?? false
    } else {
        // Dynamic SecCode lookup delegates bundle discovery to CodeSigningHelper. Instead,
        // validate the exact loaded slice through an open file and bind it to the kernel CDHash.
        let result = withExecutableCode(at: URL(fileURLWithPath: path), offset: evidence.offset) { code -> ([CFString: Any], Bool)? in
            // macOS enforces mapped-page integrity. Still validate the signature and ALL
            // non-executable components; missing external bundle metadata fails closed.
            let flags = SecCSFlags(rawValue: kSecCSDoNotValidateExecutable)
            guard SecStaticCodeCheckValidity(code, flags, nil) == errSecSuccess else { return nil }
            var info: CFDictionary?
            guard SecCodeCopySigningInformation(code, informationFlags, &info) == errSecSuccess,
                  let values = info as? [CFString: Any] else { return nil }
            return (values, requirement.map { SecStaticCodeCheckValidity(code, flags, $0) == errSecSuccess } ?? false)
        }
        guard let result else { return nil }
        dictionary = result.0
        matchesRequirement = result.1
        // Runtime and platform status come from the live kernel, not file metadata.
        dictionary[kSecCodeInfoStatus] = NSNumber(value: evidence.flags)
        dictionary.removeValue(forKey: kSecCodeInfoPlatformIdentifier)
        dictionary[kSecCodeInfoMainExecutable] = URL(fileURLWithPath: path)
    }
    let hash = withUnsafeBytes(of: evidence.cdhash) { Data($0) }
    var after = AVProcessIdentity()
    var current = AVProcessSigningEvidence()
    guard dictionary[kSecCodeInfoUnique] as? Data == hash,
          av_process_signing_evidence(pid, &current),
          current.flags == evidence.flags, current.offset == evidence.offset,
          withUnsafeBytes(of: current.cdhash, { Data($0) }) == hash,
          av_process_identity(pid, &after), before.pid == after.pid,
          before.pidversion == after.pidversion, before.start_usec == after.start_usec,
          before.euid == after.euid, before.audit_session_id == after.audit_session_id
    else { return nil }
    return LiveProcessSigningInformation(information: dictionary, matchesRequirement: matchesRequirement, offset: evidence.offset)
}

/// Validates a fresh live process and binds its signed identity to the selected file.
/// The caller must bind the process execution across this call and subsequent use.
public func liveExecutableCodeIdentity(pid: pid_t, executableURL: URL) -> Data? {
    guard let live = liveProcessSigningInformation(pid: pid),
          let liveHash = live.information[kSecCodeInfoUnique] as? Data else { return nil }
    let diskHash = withExecutableCode(at: executableURL, offset: live.offset) { code -> Data? in
        var info: CFDictionary?
        guard SecCodeCopySigningInformation(code, [], &info) == errSecSuccess else { return nil }
        return (info as? [CFString: Any])?[kSecCodeInfoUnique] as? Data
    }
    // Disk metadata grants no authority: its hash must match the validated live code.
    return diskHash == liveHash ? liveHash : nil
}

private func withExecutableCode<T>(at url: URL, offset: Int64, _ body: (SecStaticCode) -> T?) -> T? {
    let descriptor = open(url.path, O_RDONLY | O_CLOEXEC | O_NONBLOCK)
    guard descriptor >= 0 else { return nil }
    defer { close(descriptor) }
    var status = stat()
    guard fstat(descriptor, &status) == 0, status.st_mode & S_IFMT == S_IFREG else { return nil }
    var code: SecStaticCode?
    let descriptorURL = URL(fileURLWithPath: "/dev/fd/\(descriptor)")
    let attributes = [kSecCodeAttributeUniversalFileOffset as String: NSNumber(value: offset)] as CFDictionary
    guard SecStaticCodeCreateWithPathAndAttributes(descriptorURL as CFURL, [], attributes, &code) == errSecSuccess,
          let code else { return nil }
    return body(code)
}
