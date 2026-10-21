# Euro-Office DocumentServer Home Assistant Add-on

Home Assistant add-on repository for the Euro-Office Document Server.

## Included app

- `eurooffice_documentserver`: runs the official
  `ghcr.io/euro-office/documentserver:latest` container image inside Home
  Assistant Supervisor.

## Installation

Add this repository URL in Home Assistant under
**Settings -> Add-ons -> Add-on Store**:

```text
https://github.com/DetFisch/ha-addon-eurooffice-documentserver
```

For local development, copy the `eurooffice_documentserver` directory into the
Home Assistant local add-ons folder and refresh the add-on store.

## Port

Set `portnumber` in the add-on configuration. The default is `8080`.

## Pre-built Home Assistant images

Home Assistant installs and updates this add-on from the container image declared
in its configuration. It downloads the matching version for the host architecture
instead of building the Dockerfile locally. GitHub Actions builds on every push
to the default branch and publishes after all declared architectures pass.
Existing release tags are kept; increase the add-on version for a new release.

See [.github/ADDON_IMAGES.md](.github/ADDON_IMAGES.md) for the build and release workflow.

## Local regression checks

The persistence tests require Linux root to check numeric UID/GID migrations.
They use temporary directories only and do not start any services or containers:

```sh
bash -n eurooffice_documentserver/run.sh
bash -n eurooffice_documentserver/persist.sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```
