"""Description for all supported Entities."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from homeconnect_websocket.entities import Setting

from custom_components.homeconnect_ws.helpers import merge_dicts

from .common import COMMON_ENTITY_DESCRIPTIONS
from .consumer_products import CONSUMER_PRODUCTS_ENTITY_DESCRIPTIONS
from .cooking import COOKING_ENTITY_DESCRIPTIONS
from .descriptions_definitions import (
    EntityDescriptions,
    HCBinarySensorEntityDescription,
    HCButtonEntityDescription,
    HCEntityDescription,
    HCFanEntityDescription,
    HCLightEntityDescription,
    HCNumberEntityDescription,
    HCSelectEntityDescription,
    HCSensorEntityDescription,
    HCSwitchEntityDescription,
    _EntityDescriptionsDefinitionsType,
    _EntityDescriptionsType,
)
from .dishcare import DISHCARE_ENTITY_DESCRIPTIONS
from .laundry_care import LAUNDRY_ENTITY_DESCRIPTIONS
from .refrigeration import REFRIGERATION_ENTITY_DESCRIPTIONS

if TYPE_CHECKING:
    from homeconnect_websocket import HomeAppliance


ALL_ENTITY_DESCRIPTIONS: _EntityDescriptionsDefinitionsType | None = None

# Entities that change a value. When the setting is read only in the description of the appliance
# they are created hidden (see `_is_read_only_setting`): the access of a setting can change while
# the appliance is running (descriptionChange), so the entity must exist to start working then.
WRITING_ENTITY_TYPES = ("switch", "select", "number")


def get_all_entity_description() -> _EntityDescriptionsDefinitionsType:
    global ALL_ENTITY_DESCRIPTIONS  # noqa: PLW0603
    if ALL_ENTITY_DESCRIPTIONS is None:
        ALL_ENTITY_DESCRIPTIONS = merge_dicts(
            COMMON_ENTITY_DESCRIPTIONS,
            CONSUMER_PRODUCTS_ENTITY_DESCRIPTIONS,
            COOKING_ENTITY_DESCRIPTIONS,
            DISHCARE_ENTITY_DESCRIPTIONS,
            LAUNDRY_ENTITY_DESCRIPTIONS,
            REFRIGERATION_ENTITY_DESCRIPTIONS,
        )
    return ALL_ENTITY_DESCRIPTIONS


def _is_read_only_setting(appliance: HomeAppliance, description: HCEntityDescription) -> bool:
    """
    Check if the entity of the description is a setting that the appliance does not let us change.

    This is the access at the moment: it can change later, via a descriptionChange message.
    Only settings are checked. The access of options and commands changes with the selected
    program and the state of the appliance (for example `StartInRelative` of a dishwasher is read
    only until a program is selected, `AbortProgram` has no access until a program runs), so those
    can not be hidden based on the description. The access of a setting that is read only in the
    description (for example `PowerState` of a Gaggenau oven or hob, `ChildLock` of the hob) did
    not change in the profiles and diagnostics that were checked, but a descriptionChange can
    change it, so such an entity is only hidden by default, not left out.
    """
    if not description.entity or not description.available_access:
        return False
    entity = appliance.entities.get(description.entity)
    return isinstance(entity, Setting) and entity.access not in description.available_access


def get_available_entities(appliance: HomeAppliance) -> EntityDescriptions:
    """Get all available Entity descriptions."""
    available_entities: _EntityDescriptionsType = {
        "button": [],
        "active_program": [],
        "binary_sensor": [],
        "event_sensor": [],
        "number": [],
        "program": [],
        "select": [],
        "sensor": [],
        "start_button": [],
        "switch": [],
        "wifi": [],
        "light": [],
        "fan": [],
    }
    appliance_entities = set(appliance.entities)
    for description_type, descriptions in get_all_entity_description().items():
        # dynamic descriptions
        if description_type == "dynamic":
            for descriptions_fn in descriptions:
                dynamic_descriptions: _EntityDescriptionsType = descriptions_fn(appliance)
                for key, value in dynamic_descriptions.items():
                    available_entities[key].extend(value)
            continue
        for description in descriptions:
            if callable(description):
                if dynamic_description := description(appliance):
                    available_entities[description_type].append(dynamic_description)
            else:
                all_subscribed_entities = set()
                if description.entity:
                    all_subscribed_entities.add(description.entity)
                if description.entities:
                    all_subscribed_entities.update(description.entities)
                if appliance_entities.issuperset(all_subscribed_entities):
                    available_entities[description_type].append(description)
    # Also for the dynamic descriptions: switch, select and number of a read only setting are
    # created, but hidden by default. The entity stays (unavailable) while the setting is read
    # only and works as soon as the appliance allows to change it. The user can unhide it.
    for description_type in WRITING_ENTITY_TYPES:
        available_entities[description_type] = [
            replace(description, entity_registry_visible_default=False)
            if _is_read_only_setting(appliance, description)
            else description
            for description in available_entities[description_type]
        ]
    return available_entities


__all__ = [
    "EntityDescriptions",
    "HCBinarySensorEntityDescription",
    "HCButtonEntityDescription",
    "HCEntityDescription",
    "HCFanEntityDescription",
    "HCLightEntityDescription",
    "HCNumberEntityDescription",
    "HCSelectEntityDescription",
    "HCSensorEntityDescription",
    "HCSwitchEntityDescription",
    "_EntityDescriptionsType",
    "get_available_entities",
]
