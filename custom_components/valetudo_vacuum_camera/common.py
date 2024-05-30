"""
Common functions for the Valetudo Vacuum Camera integration.
Version: 2024.06.0
"""

from __future__ import annotations

import logging

from homeassistant.components.mqtt import DOMAIN as MQTT_DOMAIN
from homeassistant.components.mqtt.models import MqttData
from homeassistant.components.vacuum import DOMAIN as VACUUM_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.util.hass_dict import HassKey
from homeassistant.helpers import device_registry as dr, entity_registry as er

_LOGGER: logging.Logger = logging.getLogger(__name__)


def get_device_info(
    config_entry_id: str, hass: HomeAssistant
) -> tuple[str, DeviceEntry] | None:
    """
    Fetches the vacuum's entity ID and Device from the
    entity registry and device registry.
    """
    vacuum_entity_id = er.async_resolve_entity_id(er.async_get(hass), config_entry_id)
    _LOGGER.debug(f"Vacuum entity ID: {vacuum_entity_id}")
    if not vacuum_entity_id:
        _LOGGER.error("Unable to lookup vacuum's entity ID. Was it removed?")
        return None

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    vacuum_device = device_registry.async_get(
        entity_registry.async_get(vacuum_entity_id).device_id
    )
    _LOGGER.debug(f"Vacuum device: {vacuum_device}")
    if not vacuum_device:
        _LOGGER.error("Unable to locate vacuum's device ID. Was it removed?")
        return None

    return vacuum_entity_id, vacuum_device


def get_entity_identifier_from_mqtt(
    mqtt_identifier: str, hass: HomeAssistant
) -> str | None:
    """
    Fetches the vacuum's entity_registry id from the mqtt topic identifier.
    Returns None if it cannot be found.
    """
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    device = device_registry.async_get_device(
        identifiers={(MQTT_DOMAIN, mqtt_identifier)}
    )
    _LOGGER.debug(f"Device: {device}")
    entities = er.async_entries_for_device(entity_registry, device_id=device.id)
    for entity in entities:
        if entity.domain == VACUUM_DOMAIN:
            return entity.id

    return None


def get_vacuum_mqtt_topic(vacuum_entity_id: str, hass: HomeAssistant) -> str | None:
    """
    Fetches the mqtt topic identifier from the MQTT integration. Returns None if it cannot be found.
    """
    try:
        DATA_MQTT: HassKey[MqttData] = HassKey("mqtt")
        return list(
            hass.data[DATA_MQTT]
            .debug_info_entities.get(vacuum_entity_id)
            .get("subscriptions")
            .keys()
        )[0]
    except AttributeError:
        return None


def get_vacuum_unique_id_from_mqtt_topic(vacuum_mqtt_topic: str) -> str:
    """
    Returns the unique_id computed from the mqtt_topic for the vacuum.
    """
    return vacuum_mqtt_topic.split("/")[1].lower() + "_camera"


async def update_options(bk_options, new_options):
    """
    Keep track of the modified options.
    Returns updated options after editing in Config_Flow.
    version: 1.6.0
    """
    # Initialize updated_options as an empty dictionary
    updated_options = {}

    keys_to_update = [
        "rotate_image",
        "margins",
        "aspect_ratio",
        "offset_top",
        "offset_bottom",
        "offset_left",
        "offset_right",
        "auto_zoom",
        "zoom_lock_ratio",
        "show_vac_status",
        "vac_status_size",
        "vac_status_position",
        "vac_status_font",
        "get_svg_file",
        "enable_www_snapshots",
        "color_charger",
        "color_move",
        "color_wall",
        "color_robot",
        "color_go_to",
        "color_no_go",
        "color_zone_clean",
        "color_background",
        "color_text",
        "alpha_charger",
        "alpha_move",
        "alpha_wall",
        "alpha_robot",
        "alpha_go_to",
        "alpha_no_go",
        "alpha_zone_clean",
        "alpha_background",
        "alpha_text",
        "color_room_0",
        "color_room_1",
        "color_room_2",
        "color_room_3",
        "color_room_4",
        "color_room_5",
        "color_room_6",
        "color_room_7",
        "color_room_8",
        "color_room_9",
        "color_room_10",
        "color_room_11",
        "color_room_12",
        "color_room_13",
        "color_room_14",
        "color_room_15",
        "alpha_room_0",
        "alpha_room_1",
        "alpha_room_2",
        "alpha_room_3",
        "alpha_room_4",
        "alpha_room_5",
        "alpha_room_6",
        "alpha_room_7",
        "alpha_room_8",
        "alpha_room_9",
        "alpha_room_10",
        "alpha_room_11",
        "alpha_room_12",
        "alpha_room_13",
        "alpha_room_14",
        "alpha_room_15",
    ]
    try:
        for key in keys_to_update:
            if key in new_options:
                updated_options[key] = new_options[key]
            else:
                updated_options[key] = bk_options[key]
    except KeyError as e:
        _LOGGER.warning(f"Error in migrating options, please re-setup the camera: {e}")
        return bk_options
    # updated_options is a dictionary containing the merged options
    updated_bk_options = updated_options  # or backup_options, as needed
    return updated_bk_options
