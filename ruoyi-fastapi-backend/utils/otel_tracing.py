"""
OpenTelemetry bootstrap utilities.

Design goals:
- Keep instrumentation optional via config flag.
- Fail safe when dependencies are missing.
- Instrument FastAPI + SQLAlchemy + Redis in one place.
"""
from typing import Any, Dict, Optional

from config.env import AppConfig, OTelConfig
from utils.log_util import logger

_otel_initialized = False


def _parse_csv(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in str(value).split(',') if item.strip()]


def _parse_otlp_headers(value: str) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for item in _parse_csv(value):
        if '=' not in item:
            continue
        key, raw_value = item.split('=', 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if key:
            headers[key] = raw_value
    return headers


def _clamp_sample_ratio(value: Any) -> float:
    try:
        ratio = float(value)
    except Exception:
        ratio = 1.0
    return max(0.0, min(1.0, ratio))


def _load_otel_symbols() -> Optional[Dict[str, Any]]:
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
    except Exception:
        return None

    return {
        'trace': trace,
        'OTLPSpanExporter': OTLPSpanExporter,
        'FastAPIInstrumentor': FastAPIInstrumentor,
        'RedisInstrumentor': RedisInstrumentor,
        'SQLAlchemyInstrumentor': SQLAlchemyInstrumentor,
        'Resource': Resource,
        'TracerProvider': TracerProvider,
        'BatchSpanProcessor': BatchSpanProcessor,
        'ConsoleSpanExporter': ConsoleSpanExporter,
        'TraceIdRatioBased': TraceIdRatioBased,
    }


def init_otel_tracing(app, db_engine=None) -> bool:
    """
    Initialize OpenTelemetry tracing.

    Returns:
        bool: True when instrumentation is successfully initialized.
    """
    global _otel_initialized

    if _otel_initialized:
        return True

    if not OTelConfig.otel_enabled:
        logger.info('OpenTelemetry tracing is disabled by config')
        return False

    symbols = _load_otel_symbols()
    if symbols is None:
        logger.warning('OpenTelemetry dependencies are missing, tracing instrumentation skipped')
        return False

    try:
        trace = symbols['trace']
        Resource = symbols['Resource']
        TracerProvider = symbols['TracerProvider']
        TraceIdRatioBased = symbols['TraceIdRatioBased']
        BatchSpanProcessor = symbols['BatchSpanProcessor']
        ConsoleSpanExporter = symbols['ConsoleSpanExporter']
        OTLPSpanExporter = symbols['OTLPSpanExporter']
        FastAPIInstrumentor = symbols['FastAPIInstrumentor']
        SQLAlchemyInstrumentor = symbols['SQLAlchemyInstrumentor']
        RedisInstrumentor = symbols['RedisInstrumentor']

        resource = Resource.create(
            {
                'service.name': OTelConfig.otel_service_name or AppConfig.app_name,
                'service.namespace': OTelConfig.otel_service_namespace,
                'service.version': AppConfig.app_version,
                'deployment.environment': AppConfig.app_env,
            }
        )
        sampler = TraceIdRatioBased(_clamp_sample_ratio(OTelConfig.otel_traces_sample_ratio))
        tracer_provider = TracerProvider(resource=resource, sampler=sampler)

        processor_count = 0
        endpoint = str(OTelConfig.otel_otlp_endpoint or '').strip()
        if endpoint:
            exporter_kwargs = {
                'endpoint': endpoint,
                'timeout': int(OTelConfig.otel_exporter_timeout_ms),
            }
            headers = _parse_otlp_headers(OTelConfig.otel_otlp_headers)
            if headers:
                exporter_kwargs['headers'] = headers
            tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(**exporter_kwargs)))
            processor_count += 1

        if OTelConfig.otel_console_exporter or processor_count == 0:
            tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
            processor_count += 1

        trace.set_tracer_provider(tracer_provider)

        excluded_urls = ','.join(_parse_csv(OTelConfig.otel_excluded_urls))
        FastAPIInstrumentor.instrument_app(app, excluded_urls=excluded_urls or None)

        if db_engine is not None:
            target_engine = getattr(db_engine, 'sync_engine', db_engine)
            SQLAlchemyInstrumentor().instrument(engine=target_engine)

        RedisInstrumentor().instrument()

        _otel_initialized = True
        logger.info(
            f'OpenTelemetry tracing enabled: endpoint={endpoint or "console-only"} '
            f'sample_ratio={_clamp_sample_ratio(OTelConfig.otel_traces_sample_ratio)}'
        )
        return True
    except Exception as exc:
        logger.warning(f'OpenTelemetry tracing init failed: {exc}')
        return False


def reset_otel_state_for_tests() -> None:
    """
    Reset singleton state for unit tests.
    """
    global _otel_initialized
    _otel_initialized = False

