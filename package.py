#!/usr/bin/env python3
"""Package a built Jellyfin plugin into a release zip and add/refresh its entry in manifest.json.

Usage:
  python package.py --bin <dir with LDAP-Auth.dll + Novell dll> --version 23.0.1.0 --target-abi 10.11.9.0 \
                    --tag v23.0.1.0 --changelog "..." [--repo SirBiggin/jellyfin-plugin-ldapauth]

Produces dist/ldap-auth_<version>.zip (DLLs + meta.json at the zip root, as jprm does) and writes the
manifest entry with sourceUrl pointing at the GitHub release asset and the zip's MD5 checksum, which is
what Jellyfin verifies on install.
"""
import argparse, hashlib, json, pathlib, zipfile, datetime

GUID = "958aad66-3784-4d2a-b89a-a7b6fab6e25c"   # same as upstream: Jellyfin treats this as an update of the LDAP plugin
NAME = "LDAP Authentication"
ARTIFACTS = ["LDAP-Auth.dll", "Novell.Directory.Ldap.NETStandard.dll"]

ap = argparse.ArgumentParser()
ap.add_argument("--bin", required=True)
ap.add_argument("--version", required=True)
ap.add_argument("--target-abi", required=True)
ap.add_argument("--tag", required=True)
ap.add_argument("--changelog", required=True)
ap.add_argument("--repo", default="SirBiggin/jellyfin-plugin-ldapauth")
a = ap.parse_args()

root = pathlib.Path(__file__).resolve().parent
dist = root / "dist"; dist.mkdir(exist_ok=True)
binp = pathlib.Path(a.bin)
ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.0000000Z")

meta = {
    "category": "Administration",
    "changelog": a.changelog,
    "description": "Authenticate your Jellyfin users against an LDAP database, and optionally create users who do not yet exist automatically. This build adds a fix so password changes work against Active Directory (unicodePwd).",
    "guid": GUID,
    "name": "LDAP-Auth",
    "overview": "Authenticate users against an LDAP database (with Active Directory password-change fix)",
    "owner": "SirBiggin",
    "targetAbi": a.target_abi,
    "timestamp": ts,
    "version": a.version,
    "status": "Active",
    "autoUpdate": True,
    "imagePath": "",
    "assemblies": [],
}

zip_name = f"ldap-auth_{a.version}.zip"
zip_path = dist / zip_name
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for f in ARTIFACTS:
        src = binp / f
        if not src.exists():
            raise SystemExit(f"missing artifact: {src}")
        z.write(src, f)
    z.writestr("meta.json", json.dumps(meta, indent=2))
md5 = hashlib.md5(zip_path.read_bytes()).hexdigest()

entry = {
    "version": a.version,
    "changelog": a.changelog,
    "targetAbi": a.target_abi,
    "sourceUrl": f"https://github.com/{a.repo}/releases/download/{a.tag}/{zip_name}",
    "checksum": md5,
    "timestamp": ts,
}

mpath = root / "manifest.json"
manifest = json.loads(mpath.read_text()) if mpath.exists() else []
plugin = next((p for p in manifest if p["guid"] == GUID), None)
if plugin is None:
    plugin = {
        "guid": GUID,
        "name": NAME,
        "description": meta["description"],
        "overview": meta["overview"],
        "owner": "SirBiggin",
        "category": "Administration",
        "imageUrl": "https://repo.jellyfin.org/releases/plugin/images/jellyfin-plugin-ldapauth.png",
        "versions": [],
    }
    manifest.append(plugin)
plugin["versions"] = [v for v in plugin["versions"] if v["version"] != a.version]
plugin["versions"].insert(0, entry)
plugin["versions"].sort(key=lambda v: tuple(int(x) for x in v["version"].split(".")), reverse=True)
mpath.write_text(json.dumps(manifest, indent=2) + "\n")
print(f"{zip_path.name}  md5={md5}  targetAbi={a.target_abi}  -> {entry['sourceUrl']}")
