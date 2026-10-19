# Terraform

`av harden terraform` installs HashiCorp's Developer-ID-signed, Hardened Runtime
Terraform Target and replaces plaintext host API tokens with the Automic Vault
credential helper. The helper binds each `get`, `store`, or `forget` request to
the live Terraform process and exact hostname. An active Homebrew formula,
competing CLI configuration, and `TF_TOKEN_*` credentials are removed or refused
rather than silently taking precedence.

Running `av harden terraform` again checks the installed version against
HashiCorp's latest stable release and upgrades older installations after
confirmation. Packages reports the same update status. Version checks run only
a verified Target, without inherited credentials or project configuration.
Failed checks stop the upgrade; a newer installed version is kept. Downloads
retain the existing archive, digest, and Developer ID verification before the
installed Target is replaced.
