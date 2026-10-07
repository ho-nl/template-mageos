# patches/

Vendor patches, applied by `vaimo/composer-patches` during `composer install`.
Declare each one in `extra.patches` of composer.json (package => label => path):

```json
"extra": {
    "patches": {
        "mage-os/magento2-base": {
            "What the patch fixes": "patches/the-fix.patch"
        }
    }
}
```

Check that `composer patch:list` lists a new patch before pushing. The platform
build fails for every `*.patch` file here that did not reach the installed code, so
an undeclared or skipped patch can no longer ship silently. Not the
`extra.patches-search` folder scan: it drops a patch whose header names no installed
package, and every patch for a branch install (`dev-main`) unless the header carries
`@version *` — a green build that logged "Nothing to patch". A file kept here that
must not be applied carries `@skip` in its header. See the project README.

Empty on purpose: the StyleSmuggler DI-scanner guard that lived here
(Sansec 2026-09-05) was removed once Mage-OS 3.5.0 shipped Adobe's official fix
(CVE-2026-75650, APSB26-146); composer.json requires ^3.5 so no install resolves
to a release without it.
