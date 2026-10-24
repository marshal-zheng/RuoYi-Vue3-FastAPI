from ports import (
    IAuditLogger,
    IBaseRepository,
    IBaseService,
    ICacheProvider,
    IEventBus,
    IRedisClient,
)


def test_ports_single_entrypoint_exports_contract_types() -> None:
    assert IBaseRepository is not None
    assert IBaseService is not None
    assert IRedisClient is not None
    assert ICacheProvider is not None
    assert IAuditLogger is not None
    assert IEventBus is not None
