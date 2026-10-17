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

Target the package that is installed: on Mage-OS that is `mage-os/*`, never
`magento/*`. Check that `composer patch:list` lists a new patch before pushing.
The platform build fails for every `*.patch` file here that did not reach the
installed code, so an undeclared or skipped patch cannot ship silently. Do not rely
on the `extra.patches-search` folder scan: it drops a patch whose header names no
installed package. A file kept here that must not be applied carries `@skip` in its
header. Remove a patch once the fix is in the Mage-OS release you require.

Empty on purpose: this is how a vendor security fix ships before the upstream
release does.
