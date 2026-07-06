# Changelog

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
