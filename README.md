# template-mageos

A ready-to-deploy **Mage-OS Open Source** shop, with sample data, as a GitHub
template repository. This is what "Clone a template → Mage-OS" generates a new
customer project from on the Deployyy platform.

Push a commit and the platform builds it. There is nothing else to set up.

---

## What you get

| | |
|---|---|
| Platform | Mage-OS `^3.4` (currently 3.4.0) — Magento core **2.4.9**, PHP **8.4** |
| Catalog | Full Mage-OS **sample data** (Luma storefront, ~2 000 products, CMS pages, reviews, cart rules) |
| Store setup | One website, one store, one store view, locale `en_US` |
| Packages | Public — `https://repo.mage-os.org/`, **no Magento Marketplace keys needed** |

A fresh environment is a plain `setup:install`: because the sample-data modules
are ordinary composer requirements baked into the image, the install lands a
stocked, browsable store with no runtime composer access and no separate seed step.

## How a push becomes a running shop

```
git push
  └─ .github/workflows/{build,preview-build}.yml
       └─ ho-nl/deployyy .github/workflows/magento2-build.yml   (central, public)
            ├─ reads composer.json  -> release line `mageos-3`
            ├─ applies that line's Dockerfile + .platform/ recipe
            │    (composer install — with patches/ applied — then the rest of the tree)
            └─ pushes ghcr.io/<owner>/<repo>:php-fpm-<sha7>
                                            :nginx-<sha7>
  └─ the deployyy operator sees the commit-keyed tags, and deploys them
```

Every branch builds, because on this platform **a branch is an environment**.
Images are keyed on the commit with no branch slug, so the same commit on two
branches is the same image — which is what makes a merge deploy instantly.

The repository's CI holds **zero cluster credentials**. It only builds and pushes;
the operator does the deploying, the database install, the DNS and the certificates.

## Variables and secrets

Your shop's variables and secrets live in **GitHub, and only there** — never in
this repository's files, and not in a separate store on the platform:

- **Repository level**: *Settings → Secrets and variables → Actions*. A
  secret for anything that must stay hidden (API keys, passwords, Composer's
  `COMPOSER_AUTH`), a variable for what may be read back (a public address, a
  feature flag). These apply to every branch.
- **Per environment**: create a GitHub Environment named after the branch
  (*Settings → Environments → New environment*, e.g. `main`) and give it its
  own variables and secrets. For that branch they override the repository's.
  Note that the Environment's protection rules (reviewers, wait timers) then
  apply to that branch's build.

Every one of them reaches **both the build and the running shop after the next
build** of the branch: push, or re-run the latest build. The build masks every
secret, gives the build steps all values as environment variables, and then
delivers the same set to the branch's environment on Deployyy, where
`app/etc/env.php` and `config.php` read them with `getenv()`. The Deployyy
console lists their names per environment, read-only, with links back to
these GitHub settings. A redeploy or rollback without a new build keeps the
values the last build delivered.

The two workflows hand everything over without naming a single value
(`vars: ${{ toJSON(vars) }}`, `secrets: all: ${{ toJSON(secrets) }}`), so you
never edit them when you add one. Mage-OS on public packages needs no
`COMPOSER_AUTH`.

## What is deliberately NOT in this repository

**No `Dockerfile`, no `.platform/` directory.** They come from the `mageos-3`
recipe in the public [`ho-nl/deployyy`](https://github.com/ho-nl/deployyy) repo,
which carries the build-correctness rules that each cost a real outage to learn
(nginx fastcgi header buffers, the `config.php` scope inject-then-strip around the
DB-less `static-content:deploy`, the `env.php` install marker, the generated
`cache_types` list, the `host-store.map` include for multi-store).

A generated repository is **never re-synced with its template**, so anything
version-specific committed here would be frozen at the day it was generated.
Keeping the recipe central is what lets a security bump reach every project.

If you genuinely need to diverge: a `Dockerfile` in the repo root replaces the
recipe Dockerfile wholesale, and a file in `.platform/` overrides just that one
recipe file. Both are escape hatches — you now own that file forever.

**No `deployyy.json`, no admin path, no crypt key, no base URL.** Environment
facts belong to the platform, not the repository. The admin front name comes from
the `Magento2App` CR, the crypt key is minted at install, and the base URL comes
from the environment.

**No media binaries.** The sample-data images arrive through composer
(`mage-os/sample-data-media`) and are installed into `pub/media` inside the build.

## Committed on purpose

**`composer.lock`** — reproducible builds. Every environment of every branch
resolves to the same dependency tree.

**`app/etc/config.php`** — the module contract, and the one place this repository
departs from Magento's stock `.gitignore`. A Mage-OS version bump brings vendor
modules with it, and a module absent from this file is neither deliberately enabled
nor deliberately disabled; two production incidents came out of exactly that gap.
It lists modules only — no `scopes` block, because the build injects scopes for the
DB-less static-content deploy and strips them again, and `setup:install` owns scope
creation in the database.

**`patches/`** — vendor patches, applied by
[`vaimo/composer-patches`](https://github.com/vaimo/composer-patches) during
`composer install`. Declare each one in `extra.patches` of composer.json, keyed by
the package it patches:

```json
"extra": {
    "patches": {
        "mage-os/magento2-base": {
            "What the patch fixes": "patches/the-fix.patch"
        }
    }
}
```

The recipe copies this directory into the build context *before* the install, so a
patch committed here is in the image the platform deploys — that is how a vendor
security fix ships before the upstream release does (first use: the StyleSmuggler
DI-scanner guard, Sansec 2026-09-05, removed again once Mage-OS 3.5.0 shipped Adobe's
official fix). Target the package that is installed: on Mage-OS that is `mage-os/*`,
never `magento/*`. A patch that does not apply fails the build, and so does a
`*.patch` file in `patches/` that did not reach the installed code (the platform
build checks every one after the install). Do not rely on the `extra.patches-search`
folder scan instead: it skips a patch whose header names no installed package, and
every patch for a branch install (`dev-main`) unless the header carries
`@version *` — the build said "Nothing to patch", stayed green and shipped the code
unpatched. A file kept in `patches/` that must not be applied carries `@skip` in its
header. Remove a patch once the fix is in the upstream release you require.

After any dependency change, regenerate and commit it:

```bash
composer update            # or composer require <package>
composer install --no-dev
php bin/magento module:enable --all
git add composer.json composer.lock app/etc/config.php
```

## Local development

```bash
composer install
```

Requires PHP 8.4 with the extensions Mage-OS declares (`bcmath ctype curl dom gd
hash iconv intl mbstring openssl pdo_mysql simplexml soap sodium xsl zip`).
`config.platform.php` is pinned to `8.4.0` so a local `composer update` resolves
exactly what the build resolves.

To rehearse the platform build locally, fetch the recipe first:

```bash
curl -sfL https://raw.githubusercontent.com/ho-nl/deployyy/main/recipes/mageos-3/Dockerfile -o Dockerfile
mkdir -p .platform && for f in env.php nginx-default.conf sendmail-tagged; do
  curl -sfL "https://raw.githubusercontent.com/ho-nl/deployyy/main/recipes/mageos-3/platform/$f" -o ".platform/$f"
done
printf '{}' > auth.json        # Mage-OS is public; an empty auth.json is enough
docker build --target php-fpm --build-arg PLATFORM_LOCALES=en_US -t shop:php-fpm .
docker build --target nginx    --build-arg PLATFORM_LOCALES=en_US -t shop:nginx .
rm Dockerfile auth.json && rm -rf .platform   # do not commit the recipe
```

## Upgrading Mage-OS

`composer.json` requires `^3.4`, so security releases inside the Mage-OS 3 line
(3.5, 3.6, …) are picked up by `composer update` — they share the same Magento
core and the same service stack, which is why the platform treats the line as one
release row. A new major is a core change and needs a validated platform row
before it can be deployed.

## Adding store views

Locales for the build-time static-content deploy come from the repository Actions
variable `DEPLOYYY_MAGENTO_LOCALES`, which the operator converges from the
`Magento2App`'s `magento.buildLocales`. **Do not edit that variable by hand** — set
the locales on the app. A store view whose locale is missing from the build renders
HTTP 200 and then 404s every stylesheet and script, because production mode never
generates static content on demand.
