<h1 align="center">Companion Intelligence Scoop Bucket</h1>

<p align="center"><strong>Scoop bucket for Companion Intelligence desktop apps.</strong></p>

<p align="center"><a href="#install-companion-hub-windows">Get started</a> · <a href="https://docs.ci.computer/docs/reference/open-source-systems">Systems map</a></p>


## Install Companion Hub (Windows)

```powershell
scoop bucket add companionintelligence https://github.com/companionintelligence/scoop-bucket
scoop install companion-hub
```

## Update

```powershell
scoop update companion-hub
```

Manifests are generated from [CI-Hub `distribution/`](https://github.com/companionintelligence/CI-Hub/tree/dev/distribution) on each desktop release.

<!-- companion-hub-readme-deep-review -->

## Windows package behavior

| Item | Behavior |
|---|---|
| Platform | Windows x64 installer |
| Install | Scoop runs the Hub installer silently |
| Version source | Manifest checks Companion Hub GitHub releases |
| Upgrade and uninstall | User data is preserved; the uninstall hook removes only managed Docker containers and networks |

Scoop may run uninstall hooks during upgrades, so the manifest intentionally avoids deleting persistent application data. Back up Hub data using the Hub's own backup workflow before manually removing it.

