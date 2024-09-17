# Send a single message to set the mood
MQTT_CONFIG = {
    "homeassistant/climate/dhw/config": {
        "device_class": "climate",
        "temperature_state_topic": "homeassistant/dhw_set_temperature/state",
        "current_temperature_topic ": "homeassistant/dhw_current_temperature/state",
        "mode_state_topic": "homeassistant/dhw_mode/state",
        "mode_command_topic": "homeassistant/dhw_mode/set",
        "preset_mode_state_topic": "homeassistant/dhw_preset_mode/state",
        "preset_mode_command_topic": "homeassistant/dhw_preset_mode/set",
        "unique_id": "samsungmimb19n_dhw",
        "device": {
            "identifiers": [
                f"heat_pump"
            ],
            "name": "Heat Pump"
        },
        "name": "Hot water",
        "modes": ["off", "heat"],
        "preset_modes": ["Eco", "Normal", "Boost"]
    },
    "homeassistant/climate/radiators/config": {
        "device_class": "climate",
        # "temperature_state_topic": "homeassistant/radiators_set_temperature/state",
        "current_temperature_topic": "homeassistant/radiators_current_temperature/state",
        "temperature_command_topic": "homeassistant/radiators_set_temperature/set",
        "mode_state_topic": "homeassistant/radiators_mode/state",
        "mode_command_topic": "homeassistant/radiators_mode/set",
        "unique_id": "samsungmimb19n_radiators",
        "max_temp": 55.0,
        "min_temp": 35.0,
        "device": {
            "identifiers": [
                f"heat_pump"
            ],
            "name": "Heat Pump"
        },
        "name": "Heat pump Radiators Water",
        "modes": ["off", "heat"],
    },
    "homeassistant/sensor/outdoor_temperature/config": {
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "state_topic": "homeassistant/outdoor_temperature/state",
        "unique_id": "samsungmimb19n_dhw",
        "device": {
            "identifiers": [
                f"heat_pump"
            ],
            "name": "Heat Pump"
        },
        "name": "Outdoor Temperature",
    },
    "homeassistant/sensor/compressor_frequency/config": {
        "unit_of_measurement": "Hz",
        "state_topic": "homeassistant/compressor_frequency/state",
        "unique_id": "samsungmimb19n_compressor_frequency",
        "device": {
            "identifiers": [
                f"heat_pump"
            ],
            "name": "Heat Pump"
        },
        "name": "Compressor Frequency",
    }
}