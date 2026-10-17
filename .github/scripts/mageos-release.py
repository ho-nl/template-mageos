#!/usr/bin/env python3
"""Helpers for .github/workflows/update-mageos.yml.

  mageos-release.py versions            -> current=, latest=, newer= (GITHUB_OUTPUT format)
  mageos-release.py pin OLD NEW         -> repoint every mage-os/* requirement pinned at OLD to NEW
  mageos-release.py support OLD NEW     -> markdown: is NEW deployable on the platform?

Standard library only; run from the repository root.
"""
import json
import os
import re
import sys
import urllib.request

PACKAGE = "mage-os/product-community-edition"
REPO = "https://repo.mage-os.org"
BUILD_WORKFLOW = "https://raw.githubusercontent.com/ho-nl/deployyy/main/.github/workflows/magento2-build.yml"
CATALOG = "https://api.github.com/repos/ho-nl/kubernetes-cluster/contents/platform/deployyy/catalog/magento2-releases.yaml"


def key(version):
    return [int(p) for p in version.split(".")]


def fetch(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "template-mageos-updater", **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode()


def releases():
    """Every stable release of the metapackage, by version."""
    data = json.loads(fetch(f"{REPO}/p2/{PACKAGE}.json"))
    return {p["version"]: p for p in data["packages"][PACKAGE] if re.fullmatch(r"\d+(\.\d+)+", p["version"])}


def locked_version():
    with open("composer.lock") as f:
        lock = json.load(f)
    return next(p["version"] for p in lock["packages"] if p["name"] == PACKAGE).lstrip("v")


def versions():
    current = locked_version()
    latest = max(releases(), key=key)
    out = f"current={current}\nlatest={latest}\nnewer={'true' if key(latest) > key(current) else 'false'}\n"
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/stdout"), "a") as f:
        f.write(out)
    print(out, end="", file=sys.stderr)


def pin(old, new):
    with open("composer.json") as f:
        composer = json.load(f)
    for section in ("require", "require-dev"):
        for name, constraint in composer.get(section, {}).items():
            if name.startswith("mage-os/") and constraint == old:
                composer[section][name] = new
    # The root-update plugin round-trips composer.json through PHP, which writes
    # an empty extra.patches object as [].
    if composer.get("extra", {}).get("patches") == []:
        composer["extra"]["patches"] = {}
    with open("composer.json", "w") as f:
        f.write(json.dumps(composer, indent=4, ensure_ascii=False) + "\n")


def support(old, new):
    """The operator derives the line `mageos-<major>` from composer.json; the
    catalog row for that line inherits one Magento core. A new release is
    deployable when its line has a catalog row, the central build knows the
    line, and the release is still on the core the line was validated on."""
    rel = releases()
    major = new.split(".")[0]
    line = f"mageos-{major}"
    core_old = rel.get(old, {}).get("extra", {}).get("magento_version", "?")
    core_new = rel.get(new, {}).get("extra", {}).get("magento_version", "?")
    problems, facts = [], []

    if core_new != core_old:
        problems.append(f"Magento core changes from {core_old} to **{core_new}**. "
                        f"The `{line}` catalog row was validated on {core_old}; "
                        "a core change needs a validated row first.")
    else:
        facts.append(f"Magento core stays {core_new}.")

    build = fetch(BUILD_WORKFLOW)
    if re.search(rf'"{re.escape(PACKAGE)}",\s*"{major}\.",\s*"{line}"', build):
        facts.append(f"The central build (ho-nl/deployyy `magento2-build.yml`) knows line `{line}`.")
    else:
        problems.append(f"The central build (ho-nl/deployyy `magento2-build.yml`) has no line `{line}`.")

    token = os.environ.get("CATALOG_TOKEN")
    if token:
        try:
            catalog = fetch(CATALOG, {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.raw"})
            if re.search(rf"^\s*name:\s*{re.escape(line)}\s*$", catalog, re.M):
                facts.append(f"The platform catalog has a Magento2Release row `{line}`.")
            else:
                problems.append(f"The platform catalog (ho-nl/kubernetes-cluster) has **no Magento2Release row `{line}`**.")
        except Exception as e:  # noqa: BLE001 — an unreadable catalog is reported, never assumed fine
            problems.append(f"Could not read the platform catalog ({e}); check the `{line}` row by hand.")
    else:
        problems.append(f"The platform catalog (ho-nl/kubernetes-cluster) was not read: the repository has no "
                        f"`CATALOG_TOKEN` secret. Check that a Magento2Release row `{line}` exists before merging.")

    lines = ["### Platform support", ""]
    if problems:
        lines += ["> [!WARNING]", "> Not confirmed deployable on Deployyy. Do not merge blind.", ">"]
        lines += [f"> - {p}" for p in problems]
        lines.append("")
    lines += [f"- {f}" for f in facts]
    print("\n".join(lines))


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"versions": versions, "pin": pin, "support": support}[cmd](*args)
