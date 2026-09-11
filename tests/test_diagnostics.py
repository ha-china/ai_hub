"""Tests for diagnostics helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from custom_components.ai_hub import _async_remove_legacy_diagnostic_entities
from custom_components.ai_hub.consts import DOMAIN
from custom_components.ai_hub.diagnostics import _get_statistics_diagnostics


class TestStatisticsDiagnostics:
    """Tests for runtime statistics diagnostics."""

    def test_returns_minimal_runtime_info_without_entry_data(self):
        hass = SimpleNamespace(data={DOMAIN: {"other": {}}})
        entry = SimpleNamespace(entry_id="entry-1")

        stats = _get_statistics_diagnostics(hass, entry)

        assert stats == {
            "integration_data_available": True,
            "entry_has_runtime_data": False,
        }

    def test_includes_cached_stats_when_available(self):
        hass = SimpleNamespace(
            data={
                DOMAIN: {
                    "entry-1": {
                        "stats": {"total_calls": 3},
                    }
                }
            }
        )
        entry = SimpleNamespace(entry_id="entry-1")

        stats = _get_statistics_diagnostics(hass, entry)

        assert stats["integration_data_available"] is True
        assert stats["entry_has_runtime_data"] is True
        assert stats["cached_stats"] == {"total_calls": 3}

    def test_handles_missing_domain_data(self):
        hass = SimpleNamespace(data={})
        entry = SimpleNamespace(entry_id="entry-1")

        stats = _get_statistics_diagnostics(hass, entry)

        assert stats == {
            "integration_data_available": False,
            "entry_has_runtime_data": False,
        }


class TestLegacyDiagnosticCleanup:
    """Tests for removing legacy diagnostic entities and devices."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_removes_legacy_diagnostic_entities_and_device(monkeypatch):
        entity_registry = MagicMock()
        device_registry = MagicMock()

        legacy_entity = SimpleNamespace(
            unique_id="ai_hub_entry-1_health_sensor",
            entity_id="sensor.ai_hub_health_status",
        )
        keep_entity = SimpleNamespace(
            unique_id="something_else",
            entity_id="sensor.keep_me",
        )
        legacy_device = SimpleNamespace(id="device-1")

        monkeypatch.setattr(
            "custom_components.ai_hub.er",
            SimpleNamespace(
                async_get=lambda hass: entity_registry,
                async_entries_for_config_entry=lambda registry, entry_id: [legacy_entity, keep_entity],
            ),
        )
        monkeypatch.setattr(
            "custom_components.ai_hub.dr",
            SimpleNamespace(async_get=lambda hass: device_registry),
        )
        device_registry.async_get_device_by_identifier.return_value = legacy_device

        hass = SimpleNamespace()
        entry = SimpleNamespace(entry_id="entry-1")

        await _async_remove_legacy_diagnostic_entities(hass, entry)

        entity_registry.async_remove.assert_called_once_with("sensor.ai_hub_health_status")
        device_registry.async_get_device_by_identifier.assert_called_once_with(
            (DOMAIN, "entry-1_diagnostic"), "entry-1"
        )
        device_registry.async_remove_device.assert_called_once_with("device-1")

    @staticmethod
    @pytest.mark.asyncio
    async def test_skips_cleanup_when_no_legacy_device_found(monkeypatch):
        entity_registry = MagicMock()
        device_registry = MagicMock()

        monkeypatch.setattr(
            "custom_components.ai_hub.er",
            SimpleNamespace(
                async_get=lambda hass: entity_registry,
                async_entries_for_config_entry=lambda registry, entry_id: [],
            ),
        )
        monkeypatch.setattr(
            "custom_components.ai_hub.dr",
            SimpleNamespace(async_get=lambda hass: device_registry),
        )
        device_registry.async_get_device_by_identifier.return_value = None

        hass = SimpleNamespace()
        entry = SimpleNamespace(entry_id="entry-1")

        await _async_remove_legacy_diagnostic_entities(hass, entry)

        entity_registry.async_remove.assert_not_called()
        device_registry.async_remove_device.assert_not_called()
