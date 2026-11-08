"""Tests for hiding switch, select and number of settings that can not be changed (yet)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.homeconnect_ws import entity_descriptions
from homeconnect_websocket.entities import Access, DeviceDescription, EntityDescription

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType


def _description(power_state_access: Access) -> DeviceDescription:
    """Appliance with a power state (Off, On), a setting, and an option as on a dishwasher."""
    return DeviceDescription(
        setting=[
            EntityDescription(
                uid=539,
                name="BSH.Common.Setting.PowerState",
                access=power_state_access,
                available=True,
                enumeration={"1": "Off", "2": "On"},
            ),
        ],
        option=[
            # Read only in the description of a dishwasher, writable when a program is selected
            EntityDescription(
                uid=558,
                name="BSH.Common.Option.StartInRelative",
                access=Access.READ,
                available=True,
            ),
        ],
    )


def _keys(descriptions: list) -> set[str]:
    return {description.key for description in descriptions}


def _hidden(descriptions: list) -> dict[str, bool]:
    """Map the key of each description to: hidden by default."""
    return {d.key: d.entity_registry_visible_default is False for d in descriptions}


async def test_read_only_setting_is_hidden(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """
    A power state that is read only (Gaggenau oven and hob) keeps its switch, hidden.

    The access can change while the appliance runs (descriptionChange), so the entity has to
    exist to start working then. Only the visibility by default is turned off.
    """
    appliance = await mock_homeconnect_appliance(description=_description(Access.READ))

    available = entity_descriptions.get_available_entities(appliance)

    # Only one of switch and select for the power state (the select only repeats the switch)
    assert _hidden(available["switch"]).get("switch_power_state") is True
    assert "select_power_state" not in _keys(available["select"])
    assert "sensor_power_state" in _keys(available["sensor"])


async def test_writable_setting_keeps_switch(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """A power state that can be changed keeps its switch."""
    appliance = await mock_homeconnect_appliance(description=_description(Access.READ_WRITE))

    available = entity_descriptions.get_available_entities(appliance)

    assert _hidden(available["switch"]).get("switch_power_state") is False


async def test_read_only_option_keeps_number(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """An option is not hidden: its access changes with the selected program."""
    appliance = await mock_homeconnect_appliance(description=_description(Access.READ))

    available = entity_descriptions.get_available_entities(appliance)

    assert _hidden(available["number"]).get("number_start_in") is False
