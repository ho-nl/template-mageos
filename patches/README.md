# patches/

Vendor patches, applied by `vaimo/composer-patches` during `composer install`
(`extra.patches-search` in composer.json points here). See the project README.

Empty on purpose: the StyleSmuggler DI-scanner guard that lived here
(Sansec 2026-09-05) was removed once Mage-OS 3.5.0 shipped Adobe's official fix
(CVE-2026-75650, APSB26-146); composer.json requires ^3.5 so no install resolves
to a release without it.
