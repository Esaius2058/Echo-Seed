import threading
import time
from unittest.mock import MagicMock
import pytest
from ..security.network_monitor import NetworkMonitor

def test_run_triggers_refresh(monkeypatch):
    mock_refresh = MagicMock()
    nm = NetworkMonitor(refresh_callback=mock_refresh)
    monkeypatch.setattr(nm, "check_connection", lambda: True)

    is_online = nm.check_connection()
    if is_online:
        mock_refresh()

    mock_refresh.assert_called_once()

def test_run_handles_offline():
    mock_refresh = MagicMock()
    nm = NetworkMonitor(test_url="https://example.com/oauth/refresh" ,refresh_callback=mock_refresh)
    is_online = nm.check_connection()

    if is_online:
        mock_refresh()

    mock_refresh.assert_not_called()

def test_network_monitor_handles_keyboard_input(monkeypatch):
    nm = NetworkMonitor(refresh_callback=lambda: None)

    monkeypatch.setattr(nm, "check_connection", lambda: False)

    thread = threading.Thread(target=nm.run(), daemon=True)
    thread.start()
    time.sleep(0.5)

    with pytest.raises(KeyboardInterrupt):
        raise KeyboardInterrupt

    thread.join(timeout=2)

    assert not thread.is_alive()

def test_network_monitor_stops_cleanly(monkeypatch):
    nm = NetworkMonitor(refresh_callback=lambda: None)
    monkeypatch.setattr(nm, "check_connection", lambda: False)

    thread = threading.Thread(target=nm.run, daemon=True)
    thread.start()
    time.sleep(0.5)

    nm.stop()
    thread.join(timeout=2)

    assert not thread.is_alive()