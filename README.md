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

The server listens on container port `80`. Home Assistant exposes that through
the add-on **Network** setting. The default host port is `8080`; change the host
port there if another number is needed.
