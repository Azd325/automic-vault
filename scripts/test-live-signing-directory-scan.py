#!/usr/bin/env python3
"""Exercise actual Security.framework calls, with positive controls for both scan sites.

AV_TEST_SIGNING_IDENTITY enables the Developer ID Launcher/helper call-site checks.
Use --entries 560000 to match issue #400's directory size. This does not reproduce
Nix's optimize-while-running operation; it verifies the resulting kernel path.
"""
import argparse
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import time

REPO = Path(__file__).resolve().parents[1]
MARKER = "AV_TEST_DIRECTORY_ENUMERATION"


def run(args, **kwargs):
    try:
        return subprocess.run([str(arg) for arg in args], check=True, timeout=120, **kwargs)
    except subprocess.CalledProcessError as error:
        if error.stderr:
            print(error.stderr[-2000:], flush=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=int, default=2000)
    parser.add_argument("--menubar", type=Path)
    args = parser.parse_args()
    if args.entries < 1:
        parser.error("--entries must be positive")
    identity = os.environ.get("AV_TEST_SIGNING_IDENTITY", "-")
    if args.menubar and identity == "-":
        parser.error("--menubar requires AV_TEST_SIGNING_IDENTITY with a Developer ID certificate")
    with tempfile.TemporaryDirectory(prefix="av-signing-scan-") as temporary:
        root = Path(temporary).resolve()
        source = root / "fixture.c"
        source.write_text("#include <unistd.h>\nint main(void) { sleep(120); return 0; }\n")
        binary = root / "fixture"
        run(["xcrun", "clang", "-arch", "arm64", "-arch", "x86_64", source, "-o", binary])
        library = root / "scan.dylib"
        probe = root / "probe"
        run(["xcrun", "clang", "-dynamiclib", REPO / "scripts/fixtures/live-signing-scan.c", "-o", library])
        include = REPO / "src/menu-helper/Sources/CProcessInfo/include"
        (root / "module.modulemap").write_text(f'module CProcessInfo {{ header "{include / "CProcessInfo.h"}" export * }}\n')
        process_info = root / "process-info.o"
        run(["xcrun", "clang", "-c", "-I", include,
             REPO / "src/menu-helper/Sources/CProcessInfo/CProcessInfo.c", "-o", process_info])
        run(["xcrun", "swiftc",
             REPO / "src/menu-helper/Sources/MenubarHelperCore/LiveExecutableValidation.swift",
             REPO / "scripts/fixtures/live-signing-probe.swift", "-I", root,
             process_info, "-lbsm", "-o", probe])
        app = root / "Parent.app"
        main_executable = app / "Contents/MacOS/Parent"
        main_executable.parent.mkdir(parents=True)
        shutil.copyfile(binary, main_executable)
        main_executable.chmod(0o755)
        (app / "Contents/Info.plist").write_bytes(plistlib.dumps({
            "CFBundleExecutable": "Parent", "CFBundleIdentifier": "com.automicvault.scan.parent",
            "CFBundlePackageType": "APPL",
        }))
        executable = root / "helper"
        shutil.copyfile(binary, executable)
        executable.chmod(0o755)
        for target, identifier in [(app, "com.automicvault.scan.parent"), (executable, "com.automicvault.scan.helper")]:
            run(["codesign", "--force", "--sign", identity, "--timestamp=none",
                 "--options", "runtime", "--identifier", identifier, target])
        directory = root / ".links"
        directory.mkdir()
        alias = directory / f"{0:064x}"
        os.link(executable, alias)
        # Keep only the alias so vnode path caching cannot switch back to the staging name.
        executable.unlink()
        print(f"Creating {args.entries} directory entries", flush=True)
        for index in range(1, args.entries):
            (directory / f"{index:064x}").touch()
        environment = dict(os.environ, DYLD_INSERT_LIBRARIES=str(library),
                           AV_TEST_SCAN_DIRECTORY=str(directory))
        with subprocess.Popen([str(alias), "120"]) as child:
            try:
                for mode in ["live-control", "disk-control", "dynamic-control", "current"]:
                    started = time.monotonic()
                    result = run([probe, mode, child.pid, alias], env=environment, capture_output=True, text=True)
                    enumerations = result.stderr.count(MARKER)
                    helper_lookups = result.stderr.count("AV_TEST_SIGNING_HELPER_LOOKUP")
                    assert (enumerations > 0) == (mode in ["live-control", "disk-control"]), (mode, result.stderr)
                    assert (helper_lookups > 0) == (mode == "dynamic-control"), (mode, result.stderr)
                    print(f"{mode}: {enumerations} directory reads, {helper_lookups} signing-helper lookups, "
                          f"{time.monotonic() - started:.3f}s", flush=True)
                if args.menubar:
                    # Use an ad-hoc copy so DYLD interposition is allowed even for a signed build.
                    # The fixture process and parent app remain Developer ID signed and hardened.
                    menubar = root / "menubar"
                    shutil.copyfile(args.menubar, menubar)
                    menubar.chmod(0o755)
                    run(["codesign", "--force", "--sign", "-", menubar])
                    result = run([menubar, "--self-check-live-signing", child.pid, alias, app],
                                 env=environment, capture_output=True, text=True)
                    assert MARKER not in result.stderr, result.stderr
                    assert "AV_TEST_SIGNING_HELPER_LOOKUP" not in result.stderr, result.stderr
                    assert "live signing call sites passed" in result.stdout, result.stdout
                    print(result.stdout.strip(), flush=True)
                    # Keep the live kernel signature valid but corrupt disk signature metadata.
                    # Failed live verification must not fall through to ordinary path discovery.
                    with alias.open("r+b") as stream:
                        data = stream.read()
                        identifier = b"com.automicvault.scan.helper"
                        assert identifier in data
                        offset = data.find(identifier)
                        while offset >= 0:
                            stream.seek(offset)
                            stream.write(b"x")
                            offset = data.find(identifier, offset + len(identifier))
                    result = run([menubar, "--self-check-live-signing", child.pid, alias, app, "invalid"],
                                 env=environment, capture_output=True, text=True)
                    assert MARKER not in result.stderr, result.stderr
                    assert "AV_TEST_SIGNING_HELPER_LOOKUP" not in result.stderr, result.stderr
                    assert "invalid live signing call sites passed" in result.stdout, result.stdout
                    print(result.stdout.strip(), flush=True)
            except subprocess.CalledProcessError:
                print(f"Fixture process exit status: {child.poll()}", flush=True)
                raise
            finally:
                child.terminate()
                child.wait(timeout=10)


if __name__ == "__main__":
    main()
