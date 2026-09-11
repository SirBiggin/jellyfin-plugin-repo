# Jellyfin plugin repository

Manifest-based plugin repository for patched Jellyfin plugins.

## Add to Jellyfin

Dashboard → Plugins → Repositories → **+** and enter:

```
https://raw.githubusercontent.com/SirBiggin/jellyfin-plugin-repo/main/manifest.json
```

Then Dashboard → Plugins → Catalog shows the plugins below. Jellyfin picks the newest
version whose `targetAbi` matches the running server, so the same repository serves
both the 10.11 and 12.x lines.

## Plugins

### LDAP Authentication (Active Directory password-change fix)

Fork of [jellyfin/jellyfin-plugin-ldapauth](https://github.com/jellyfin/jellyfin-plugin-ldapauth)
with one change: `ChangePassword` writes `unicodePwd` the way Active Directory requires
(password in double quotes, UTF-16LE encoded), so **Allow Password Change** works against AD.
Upstream issues [#164](https://github.com/jellyfin/jellyfin-plugin-ldapauth/issues/164) /
[#200](https://github.com/jellyfin/jellyfin-plugin-ldapauth/issues/200).

Also skips the Jellyfin user rename when the LDAP username differs from the Jellyfin username only by case
(upstream [#201](https://github.com/jellyfin/jellyfin-plugin-ldapauth/issues/201)); Jellyfin 10.11+ rejects
case-only renames, which made login and password change fail for such users.

Source: [SirBiggin/jellyfin-plugin-ldapauth](https://github.com/SirBiggin/jellyfin-plugin-ldapauth)
(branches `patch-v23` and `patch-v24`).
Technical breakdown of each patch:
[PATCHES.md](https://github.com/SirBiggin/jellyfin-plugin-ldapauth/blob/patch-v23/PATCHES.md).

| Version | Jellyfin | Based on | Branch |
|---|---|---|---|
| 23.0.2.0 | 10.11.x (`targetAbi` 10.11.9.0) | upstream v23 | `patch-v23` |
| 24.0.2.0 | 12.x (`targetAbi` 12.0.0.0) | upstream master/v24 | `patch-v24` |

The plugin keeps upstream's GUID, so Jellyfin sees it as an update of the stock LDAP plugin
and the existing configuration carries over. A later upstream release with a higher version
number will supersede it unless the patch is rebased and republished.

To use the fix, in the plugin settings set **LDAP Password Attribute** to `unicodePwd`, tick
**Allow Password Change**, and delegate *Reset Password* (plus write on `pwdLastSet`) on the
users' OU to the bind account. The connection must be LDAPS or StartTLS or AD refuses the write.

## Publishing a new version

```
python package.py --bin <build output dir> --version 23.0.2.0 --target-abi 10.11.9.0 \
                  --tag v23.0.2.0 --changelog "..."
gh release create v23.0.2.0 dist/ldap-auth_23.0.2.0.zip --repo SirBiggin/jellyfin-plugin-ldapauth --title "..." --notes "..."
git commit -am "..." && git push
```

`package.py` writes the zip (DLLs + `meta.json` at the root) and updates `manifest.json`
with the release asset URL and the zip's MD5, which Jellyfin verifies on install.
