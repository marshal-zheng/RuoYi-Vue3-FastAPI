from fastapi import FastAPI

from utils import otel_tracing


def test_init_otel_tracing_disabled(monkeypatch):
    otel_tracing.reset_otel_state_for_tests()
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_enabled', False)

    result = otel_tracing.init_otel_tracing(app=FastAPI(), db_engine=None)
    assert result is False


def test_init_otel_tracing_missing_dependencies(monkeypatch):
    otel_tracing.reset_otel_state_for_tests()
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_enabled', True)
    monkeypatch.setattr(otel_tracing, '_load_otel_symbols', lambda: None)

    result = otel_tracing.init_otel_tracing(app=FastAPI(), db_engine=None)
    assert result is False


def test_init_otel_tracing_success(monkeypatch):
    otel_tracing.reset_otel_state_for_tests()

    class DummyTrace:
        def __init__(self):
            self.provider = None

        def set_tracer_provider(self, provider):
            self.provider = provider

    class DummyResource:
        @staticmethod
        def create(attrs):
            return {'attrs': attrs}

    class DummyTraceIdRatioBased:
        def __init__(self, ratio):
            self.ratio = ratio

    class DummyTracerProvider:
        def __init__(self, resource=None, sampler=None):
            self.resource = resource
            self.sampler = sampler
            self.processors = []

        def add_span_processor(self, processor):
            self.processors.append(processor)

    class DummyBatchSpanProcessor:
        def __init__(self, exporter):
            self.exporter = exporter

    class DummyConsoleSpanExporter:
        pass

    class DummyOTLPSpanExporter:
        instances = []

        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.__class__.instances.append(self)

    class DummyFastAPIInstrumentor:
        calls = []

        @classmethod
        def instrument_app(cls, app, excluded_urls=None):
            cls.calls.append({'app': app, 'excluded_urls': excluded_urls})

    class DummySQLAlchemyInstrumentor:
        calls = []

        def instrument(self, engine=None):
            self.__class__.calls.append(engine)

    class DummyRedisInstrumentor:
        calls = 0

        def instrument(self):
            self.__class__.calls += 1

    dummy_trace = DummyTrace()
    symbols = {
        'trace': dummy_trace,
        'OTLPSpanExporter': DummyOTLPSpanExporter,
        'FastAPIInstrumentor': DummyFastAPIInstrumentor,
        'RedisInstrumentor': DummyRedisInstrumentor,
        'SQLAlchemyInstrumentor': DummySQLAlchemyInstrumentor,
        'Resource': DummyResource,
        'TracerProvider': DummyTracerProvider,
        'BatchSpanProcessor': DummyBatchSpanProcessor,
        'ConsoleSpanExporter': DummyConsoleSpanExporter,
        'TraceIdRatioBased': DummyTraceIdRatioBased,
    }

    monkeypatch.setattr(otel_tracing, '_load_otel_symbols', lambda: symbols)
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_enabled', True)
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_service_name', 'ruoyi-backend')
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_service_namespace', 'ruoyi')
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_traces_sample_ratio', 0.5)
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_otlp_endpoint', 'http://127.0.0.1:4318/v1/traces')
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_otlp_headers', 'k=v,foo=bar')
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_exporter_timeout_ms', 5000)
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_console_exporter', False)
    monkeypatch.setattr(otel_tracing.OTelConfig, 'otel_excluded_urls', '/health,/metrics')

    class DummyEngine:
        sync_engine = 'sync-engine'

    app = FastAPI()
    first = otel_tracing.init_otel_tracing(app=app, db_engine=DummyEngine())
    second = otel_tracing.init_otel_tracing(app=app, db_engine=DummyEngine())

    assert first is True
    assert second is True
    assert isinstance(dummy_trace.provider, DummyTracerProvider)
    assert isinstance(dummy_trace.provider.sampler, DummyTraceIdRatioBased)
    assert dummy_trace.provider.sampler.ratio == 0.5
    assert len(dummy_trace.provider.processors) == 1
    assert isinstance(dummy_trace.provider.processors[0].exporter, DummyOTLPSpanExporter)
    assert DummyOTLPSpanExporter.instances[0].kwargs['endpoint'] == 'http://127.0.0.1:4318/v1/traces'
    assert DummyOTLPSpanExporter.instances[0].kwargs['timeout'] == 5000
    assert DummyOTLPSpanExporter.instances[0].kwargs['headers'] == {'k': 'v', 'foo': 'bar'}
    assert len(DummyFastAPIInstrumentor.calls) == 1
    assert DummyFastAPIInstrumentor.calls[0]['excluded_urls'] == '/health,/metrics'
    assert DummySQLAlchemyInstrumentor.calls == ['sync-engine']
    assert DummyRedisInstrumentor.calls == 1

