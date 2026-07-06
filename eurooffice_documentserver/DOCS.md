# Documentation

## Setup

1. Install the add-on in Home Assistant.
2. Open the add-on configuration and set `portnumber`.
3. Set a `jwt_secret` with at least 32
   characters if you plan to connect Nextcloud or another production
   integration.
4. Start the add-on.
5. Open `http://homeassistant.local:<portnumber>/`.

## Nextcloud integration notes

In the Nextcloud Euro-Office/ONLYOFFICE connector, use the Document Server URL
that Nextcloud can reach, for example:

```text
http://homeassistant.local:<portnumber>/
```

Use the same JWT secret in Nextcloud and in this add-on. If Nextcloud is only
reachable through a private LAN address, enable `allow_private_ip_address`.

## Port behavior

This add-on runs with `host_network: true` so the configured `portnumber` is the
actual host port. Make sure no other service already uses that port.
