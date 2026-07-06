# Documentation

## Setup

1. Install the add-on in Home Assistant.
2. Open the add-on configuration and set a `jwt_secret` with at least 32
   characters if you plan to connect Nextcloud or another production
   integration.
3. In the add-on **Network** section, set the host port for `80/tcp`. The
   default is `8080`.
4. Start the add-on.
5. Open `http://homeassistant.local:8080/` or your configured host/port.

## Nextcloud integration notes

In the Nextcloud Euro-Office/ONLYOFFICE connector, use the Document Server URL
that Nextcloud can reach, for example:

```text
http://homeassistant.local:8080/
```

Use the same JWT secret in Nextcloud and in this add-on. If Nextcloud is only
reachable through a private LAN address, enable `allow_private_ip_address`.

## Health check

Home Assistant watches:

```text
http://[HOST]:[PORT:80]/healthcheck
```

Euro-Office reports readiness when that endpoint returns `true`.
