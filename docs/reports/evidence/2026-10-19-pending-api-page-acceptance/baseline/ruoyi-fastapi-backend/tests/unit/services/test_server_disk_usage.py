from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from modules.system.application.services import server_service as target


@pytest.mark.asyncio
async def test_disk_usage_reads_mountpoint_instead_of_device_directory(monkeypatch):
    monkeypatch.setattr(
        target.psutil,
        'disk_partitions',
        lambda: [SimpleNamespace(device='/dev/owned', mountpoint='/owned-volume', fstype='test')],
    )
    usage = Mock(return_value=SimpleNamespace(total=1024**3, used=1024**2, free=1024**3 - 1024**2, percent=0.1))
    monkeypatch.setattr(target.psutil, 'disk_usage', usage)
    result = await target.ServerService.get_server_monitor_info()
    usage.assert_called_once_with('/owned-volume')
    assert result.sys_files[0].total == '1.0GB'
    assert result.sys_files[0].usage == '0.1%'
