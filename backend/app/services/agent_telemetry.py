"""Optional OpenTelemetry setup for the Strands agents."""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_configured = False


def configure_strands_telemetry() -> None:
    """Enable Strands tracing once per process when requested via settings.

    The exporters honor the standard OpenTelemetry environment variables
    (``OTEL_EXPORTER_OTLP_ENDPOINT``, ``OTEL_SERVICE_NAME``, ...). Setup is
    fail-safe: telemetry problems never break agent generation.
    """
    global _configured
    if _configured:
        return
    console = bool(getattr(settings, "strands_console_tracing", False))
    otlp = bool(getattr(settings, "strands_otlp_tracing", False))
    if not (console or otlp):
        return
    _configured = True
    try:
        from strands.telemetry import StrandsTelemetry

        telemetry = StrandsTelemetry()
        if console:
            telemetry.setup_console_exporter()
        if otlp:
            telemetry.setup_otlp_exporter()
        logger.info("Strands telemetry configured.")
    except Exception:
        logger.warning("Strands telemetry setup failed.", exc_info=True)
