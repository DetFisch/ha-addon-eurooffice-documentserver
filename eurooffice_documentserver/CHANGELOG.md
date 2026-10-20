# Changelog

## 0.2.2 - 2026-10-20

- Build and publish versioned container images in GitHub Actions for faster Home Assistant installations and updates.
- Preserve release tags and build every architecture declared by the add-on.

## 0.2.1

- Fail fast with a clear error when JWT is enabled but `jwt_secret` is empty.
- Document the Nextcloud `Invalid token` troubleshooting path.

## 0.2.0

- Add `portnumber` to the add-on configuration.
- Run on the host network so `portnumber` is the actual host port.
- Rewrite Euro-Office nginx listen settings during startup.

## 0.1.0

- Initial Home Assistant app/add-on wrapper for the official Euro-Office
  Document Server image.
- Exposes container port `80` with default host port `8080`.
- Adds Home Assistant options for JWT, WOPI, example app, private IP fetches,
  font generation, and nginx workers.
- Persists runtime data under `/data/euro-office`.
