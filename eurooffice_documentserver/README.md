# Euro-Office Document Server

Runs the official Euro-Office Document Server image as a Home Assistant
app/add-on.

## Port

Set `portnumber` in the add-on configuration. The default is `8080`.

The web UI URL is:

```text
http://homeassistant.local:<portnumber>/
```

If the example app is enabled, it is available at:

```text
http://homeassistant.local:<portnumber>/example/
```

## Configuration

- `jwt_enabled`: enable JWT validation. Keep this enabled for integrations.
- `portnumber`: host port used by Euro-Office Document Server.
- `jwt_secret`: optional shared JWT secret. If empty, Euro-Office generates one
  and stores it in persistent add-on data. For Nextcloud, use at least 32
  characters.
- `jwt_header`: HTTP header used for JWT, usually `Authorization`.
- `example_enabled`: enables the built-in example app. Do not enable it for
  untrusted networks.
- `wopi_enabled`: enables WOPI protocol support.
- `allow_private_ip_address`: allows the server to fetch documents from private
  network addresses. Enable only when your integration needs private LAN URLs.
- `generate_fonts`: regenerates the font cache on startup.
- `nginx_worker_processes`: number of nginx workers inside the container.

## Persistent data

The wrapper stores Euro-Office runtime data under `/data/euro-office`, including
the generated JWT secret, Data directory, logs, PostgreSQL, Redis, and RabbitMQ
state.
