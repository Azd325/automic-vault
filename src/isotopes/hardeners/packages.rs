//! Diagnostic package inventory. No status here grants authority or installs code.
use std::fs;
use std::path::Path;

use serde::Serialize;

use super::{aws_release, doctl, hcloud, isotope, terraform, terraform_release, uv_cli};

#[derive(Serialize)]
pub(crate) struct PackageStatus {
    name: &'static str,
    #[serde(skip)]
    managed: bool,
    installation: &'static str,
    update: &'static str,
    detail: String,
    target_path: String,
}

impl PackageStatus {
    fn new(name: &'static str, target: &Path, valid: bool) -> Self {
        let present = !matches!(fs::symlink_metadata(target), Err(error) if error.kind() == std::io::ErrorKind::NotFound);
        Self {
            name,
            managed: true,
            installation: if valid {
                "Installed"
            } else if present {
                "Needs repair"
            } else {
                "Not installed"
            },
            update: "Not checked",
            detail: format!("Run `av harden {name}` to install or repair this package."),
            target_path: target.display().to_string(),
        }
    }

    fn is_installed_and_managed(&self) -> bool {
        self.managed && self.installation != "Not installed"
    }

    fn update_result(&mut self, result: Result<bool, String>) {
        match result {
            Ok(true) => {
                self.update = "Update available";
                self.detail = format!(
                    "Run `av harden {}` to install the current verified release.",
                    self.name
                );
            }
            Ok(false) => {
                self.update = "Up to date";
                self.detail = "The installed release is current.".into();
            }
            Err(error) => {
                self.update = "Check failed";
                self.detail =
                    format!("Could not check for updates: {error}\n\nRefresh Packages to retry.");
            }
        }
    }
}

pub(crate) fn statuses() -> Vec<PackageStatus> {
    // Each manifest fetch has a timeout; concurrent checks keep dashboard refresh bounded.
    let mut packages = std::thread::scope(|scope| {
        let workers: Vec<_> = isotope::PACKAGES.iter().map(|&spec| scope.spawn(move || {
            let target = isotope::target(spec);
            let valid = isotope::installed(spec, &target);
            let mut package = PackageStatus::new(spec.hardener, &target, valid);
            package.managed = isotope::is_direct_target(spec, &target);
            if valid {
                if package.managed {
                    package.update_result(direct_update(
                        &isotope::receipt_path(spec),
                        || isotope::current_sha(&isotope::formula_url(spec), spec.repository),
                    ));
                } else {
                    package.update = "Managed by Homebrew";
                    package.detail = format!("Homebrew owns updates for `automic-vault/isotopes/{}`. Use `brew outdated automic-vault/isotopes/{}` to check for updates.", spec.formula, spec.formula);
                }
            }
            package
        })).collect();
        workers
            .into_iter()
            .map(|worker| worker.join().expect("package status worker panicked"))
            .collect::<Vec<_>>()
    });
    let target = aws_release::target_path();
    let mut aws = PackageStatus::new("aws", &target, aws_release::current_release_valid().is_ok());
    if aws.installation == "Installed" {
        aws.update_result(aws_release::current_version().and_then(|installed| {
            aws_release::latest_version()
                .and_then(|latest| aws_release::update_available(&installed, &latest))
        }));
    }
    packages.push(aws);
    for (name, target, version, verify) in [
        (
            "uv",
            crate::uv::TARGET,
            crate::uv::VERSION,
            uv_cli::verify_installation as fn() -> Result<(), String>,
        ),
        (
            "hcloud",
            hcloud::TARGET,
            hcloud::VERSION,
            hcloud::verify_installation,
        ),
        (
            "doctl",
            doctl::TARGET,
            doctl::VERSION,
            doctl::verify_installation,
        ),
    ] {
        let mut package = PackageStatus::new(name, Path::new(target), verify().is_ok());
        if package.installation == "Not installed"
            && Path::new(target)
                .ancestors()
                .nth(2)
                .is_some_and(Path::exists)
        {
            package.installation = "Needs repair";
        }
        package.update = "Pinned release";
        package.detail = format!(
            "Automic Vault pins the reviewed release {version}. New reviewed releases ship with Automic Vault.\n\nRun `av harden {name}` to install or repair the pinned release."
        );
        packages.push(package);
    }
    let target = Path::new(terraform_release::TARGET_PATH);
    let mut package = PackageStatus::new(
        "terraform",
        target,
        terraform::verify_target(terraform::Tool::Terraform, target).is_ok(),
    );
    // The direct installer writes a regular file, never a package-manager link.
    package.managed =
        fs::symlink_metadata(target).is_ok_and(|metadata| metadata.file_type().is_file());
    if package.managed && package.installation == "Installed" {
        package.update_result(
            terraform_release::update_version(target).map(|version| version.is_some()),
        );
    }
    packages.push(package);
    packages.retain(PackageStatus::is_installed_and_managed);
    packages.sort_by_key(|package| package.name);
    packages
}

fn direct_update(
    receipt: &Path,
    current: impl FnOnce() -> Result<String, String>,
) -> Result<bool, String> {
    let installed = fs::read_to_string(receipt)
        .map_err(|error| format!("could not read installation receipt: {error}"))?;
    isotope::validate_sha256(installed.trim())?;
    current().map(|current| installed.trim() != current)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn inventory_only_keeps_installed_directly_managed_packages() {
        let mut package = PackageStatus::new("gh", Path::new("/missing/gh"), true);
        assert!(package.is_installed_and_managed());
        package.managed = false;
        assert!(!package.is_installed_and_managed());
        package.managed = true;
        package.installation = "Not installed";
        assert!(!package.is_installed_and_managed());
        package.installation = "Needs repair";
        assert!(package.is_installed_and_managed());
    }

    #[test]
    fn missing_receipt_is_unknown_not_an_available_update() {
        assert!(
            direct_update(Path::new("/nonexistent/av-package-receipt"), || panic!(
                "must not fetch without a receipt"
            ))
            .is_err()
        );
    }

    #[test]
    fn update_failure_cannot_look_current() {
        let mut package = PackageStatus::new("gh", Path::new("/missing/gh"), true);
        package.update_result(Ok(false));
        assert_eq!(package.update, "Up to date");
        package.update_result(Err("offline".into()));
        assert_eq!(package.update, "Check failed");
        assert!(package.detail.contains("offline"));
        package.update_result(Ok(true));
        assert_eq!(package.update, "Update available");
        assert!(package.detail.contains("av harden gh"));
    }

    #[test]
    fn receipt_comparison_distinguishes_current_changed_and_invalid() {
        let directory = std::env::temp_dir().join(format!(
            "av-packages-{}-{}",
            std::process::id(),
            isotope::now_nanos()
        ));
        fs::create_dir_all(&directory).unwrap();
        let receipt = directory.join("receipt");
        let digest = "a".repeat(64);
        fs::write(&receipt, format!("{digest}\n")).unwrap();
        assert_eq!(direct_update(&receipt, || Ok(digest.clone())), Ok(false));
        assert_eq!(direct_update(&receipt, || Ok("b".repeat(64))), Ok(true));
        assert!(direct_update(&receipt, || Err("offline".into())).is_err());
        fs::write(&receipt, "invalid").unwrap();
        assert!(direct_update(&receipt, || panic!("invalid receipt")).is_err());
        let missing = PackageStatus::new("gh", &directory.join("missing"), false);
        assert_eq!(missing.installation, "Not installed");
        let damaged = PackageStatus::new("gh", &receipt, false);
        assert_eq!(damaged.installation, "Needs repair");
        fs::remove_dir_all(directory).unwrap();
    }

    #[test]
    fn catalog_has_unique_packages_and_includes_opentofu() {
        let names: std::collections::BTreeSet<_> =
            isotope::PACKAGES.iter().map(|spec| spec.hardener).collect();
        assert_eq!(names.len(), isotope::PACKAGES.len());
        assert!(names.contains("opentofu"));
    }
}
