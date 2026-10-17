# template-mageos

The **Mage-OS** template of the Deployyy platform: what
*New project → Mage-OS* copies into a new customer project. A stock
`composer create-project mage-os/project-community-edition` with the Mage-OS sample
data, so a fresh environment installs a stocked Luma store.

**Version: Mage-OS 3.6.0** (Magento core 2.4.9, PHP 8.4, platform line `mageos-3`).
Packages come from `https://repo.mage-os.org/`; no Adobe Marketplace keys needed.

## What is in the repository, and why

| | |
|---|---|
| `composer.json`, `composer.lock` | The project. Stock Mage-OS, plus the sample-data packages, `vaimo/composer-patches` and `config.platform.php` 8.4.0 so a local `composer update` resolves what the build resolves. |
| `app/etc/config.php` | The module contract (`composer install --no-dev && bin/magento module:enable --all`), committed so a version bump never brings a module that is neither enabled nor disabled. |
| `patches/` | Vendor patches, applied during the build's `composer install`; see `patches/README.md`. |
| `.github/workflows/build.yml`, `preview-build.yml` | Call the platform build ([`ho-nl/deployyy` `magento2-build.yml`](https://github.com/ho-nl/deployyy/blob/main/.github/workflows/magento2-build.yml)): every branch is built into commit-keyed images, which the Deployyy operator deploys. The Dockerfile and `.platform/` files come from that repository's `mageos-3` recipe, so they are not committed here. |
| `.gitignore`, `.dockerignore` | Keep what Composer installs (`vendor/`, `bin/`, `pub/`, `setup/`, …) and local files out of git and out of the image. |

Variables and secrets live in GitHub (*Settings → Secrets and variables →
Actions*, or a GitHub Environment named after the branch); the build hands all of
them to the image and the environment.

## Keeping it current: `update-mageos.yml`

`.github/workflows/update-mageos.yml` runs every Monday and on demand
(*Actions → Update Mage-OS → Run workflow*). It compares the newest stable
`mage-os/product-community-edition` on repo.mage-os.org with composer.lock. When a
newer release exists it follows Mage-OS's upgrade procedure:

```bash
composer require-commerce mage-os/product-community-edition <version> --no-update
composer update
composer install --no-dev && bin/magento module:enable --all   # refresh config.php
```

and opens a pull request from `auto/mageos-update` titled *Mage-OS &lt;version&gt;*,
with the changelog link, or updates the pull request already open. It then starts
the preview build on that branch, so the pull request shows whether the platform
builds the release.

The pull request also says whether the platform supports the release: the
Magento core must stay the one the `mageos-3` line was validated on, and the
central build must know the line. With a `CATALOG_TOKEN` secret (read access to
`ho-nl/kubernetes-cluster`) it also checks the platform catalog for the
Magento2Release row; without one the pull request says the catalog was not checked.

The workflow only runs in `ho-nl/template-mageos`, not in projects copied from it.
