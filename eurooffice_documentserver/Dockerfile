ARG BUILD_VERSION=0.2.4
ARG BUILD_ARCH

FROM ghcr.io/euro-office/documentserver:latest

ARG BUILD_VERSION=0.2.4
ARG BUILD_ARCH

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}"

COPY run.sh /ha-run.sh
COPY persist.sh /persist.sh
RUN chmod a+x /ha-run.sh

ENTRYPOINT ["/ha-run.sh"]
