"""EcoNet thermostat"""

import logging
from enum import Enum
from typing import Tuple, Union, List

from . import Equipment

_LOGGER = logging.getLogger(__name__)


class ThermostatOperationMode(Enum):
    """Define the operation mode"""

    OFF = 1
    HEATING = 2
    COOLING = 3
    AUTO = 4
    FAN_ONLY = 5
    EMERGENCY_HEAT = 6
    UNKNOWN = 99

    @staticmethod
    def by_string(str_value: str):
        """Convert a string to a supported OperationMode"""
        _cleaned_string = str_value.rstrip().replace(" ", "_").upper()
        if _cleaned_string == ThermostatOperationMode.OFF.name.upper():
            return ThermostatOperationMode.OFF
        elif _cleaned_string == ThermostatOperationMode.HEATING.name.upper():
            return ThermostatOperationMode.HEATING
        elif _cleaned_string == ThermostatOperationMode.COOLING.name.upper():
            return ThermostatOperationMode.COOLING
        elif _cleaned_string == ThermostatOperationMode.AUTO.name.upper():
            return ThermostatOperationMode.AUTO
        elif _cleaned_string == ThermostatOperationMode.FAN_ONLY.name.replace("_", "").upper():
            return ThermostatOperationMode.FAN_ONLY
        elif _cleaned_string == ThermostatOperationMode.EMERGENCY_HEAT.name.replace("_", "").upper():
            return ThermostatOperationMode.EMERGENCY_HEAT
        else:
            _LOGGER.error("Unknown mode: [%s]", str_value)
            return ThermostatOperationMode.UNKNOWN


class ThermostatFanMode(Enum):
    """Define the operation mode"""

    AUTO = 1
    LOW = 2
    MEDLO = 3
    MEDIUM = 4
    MEDHI = 5
    HIGH = 6
    UNKNOWN = 99

    @staticmethod
    def by_string(str_value: str):
        """Convert a string to a supported OperationMode"""
        _cleaned_string = str_value.rstrip().replace(" ", "_").replace(".", "").upper()
        if _cleaned_string == ThermostatFanMode.AUTO.name.upper():
            return ThermostatFanMode.AUTO
        elif _cleaned_string == ThermostatFanMode.LOW.name.upper():
            return ThermostatFanMode.LOW
        elif _cleaned_string == ThermostatFanMode.MEDLO.name.upper():
            return ThermostatFanMode.MEDLO
        elif _cleaned_string == ThermostatFanMode.MEDIUM.name.upper():
            return ThermostatFanMode.MEDIUM
        elif _cleaned_string == ThermostatFanMode.MEDHI.name.upper():
            return ThermostatFanMode.MEDHI
        elif _cleaned_string == ThermostatFanMode.HIGH.name.upper():
            return ThermostatFanMode.HIGH
        else:
            _LOGGER.error("Unknown fan mode: [%s]", str_value)
            return ThermostatFanMode.UNKNOWN


class Thermostat(Equipment):

    @property
    def running(self) -> bool:
        """Return if the thermostat is running or not"""
        return self._equipment_info.get("@RUNNINGSTATUS") == "Running"

    @property
    def beep_enabled(self) -> bool:
        """Return if thermostat beep is enabled or not"""
        beep = self._equipment_info.get("@BEEP")
        if beep is not None:
            return beep["value"] == 1
        else:
            return False

    @property
    def cool_set_point(self) -> int:
        """Return the current cool set point"""
        return self._equipment_info.get("@COOLSETPOINT")["value"]

    @property
    def cool_set_point_limits(self) -> Tuple:
        """Returns a tuple of the lower limit and upper limit for the cool set point"""
        set_point = self._equipment_info.get("@COOLSETPOINT")["constraints"]
        return set_point["lowerLimit"], set_point["upperLimit"]

    @property
    def heat_set_point(self) -> int:
        return self._equipment_info.get("@HEATSETPOINT")["value"]

    @property
    def heat_set_point_limits(self) -> Tuple:
        """Returns a tuple of the lower limit and upper limit for the heat set point"""
        set_point = self._equipment_info.get("@HEATSETPOINT")["constraints"]
        return set_point["lowerLimit"], set_point["upperLimit"]

    @property
    def deadband(self) -> int:
        return self._equipment_info.get("@DEADBAND")["value"]

    @property
    def deadband_set_point_limits(self) -> Tuple:
        """Returns a tuple of the lower limit and upper limit for the cool set point"""
        set_point = self._equipment_info.get("@DEADBAND")["constraints"]
        return set_point["lowerLimit"], set_point["upperLimit"]

    @property
    def dehumidifier_set_point(self) -> int:
        return self._equipment_info.get("@DEHUMSETPOINT")["value"]

    @property
    def dehumidifier_set_point_limits(self) -> Tuple:
        """Returns a tuple of the lower limit and upper limit for the dehumidifier set point"""
        set_point = self._equipment_info.get("@DEHUMSETPOINT")["constraints"]
        return set_point["lowerLimit"], set_point["upperLimit"]

    @property
    def dehumidifier_enabled(self) -> bool:
        return self._equipment_info.get("@DEHUMENABLE")["value"] == 1

    def set_dehumidifier_set_point(self, humidity):
        """Set the provided humidity"""
        lower, upper = self.dehumidifier_set_point_limits
        if lower <= humidity <= upper:
            payload = {"@DEHUMSETPOINT": humidity}
            self._api.publish(payload, self.device_id, self.serial_number)
        else:
            _LOGGER.error("Set point out of range. Lower: %s Upper: %s Humidity set point: %s", lower, upper, humidity)

    @property
    def humidity(self) -> int:
        """Returns the current humidity"""
        return self._equipment_info.get("@HUMIDITY")["value"]

    @property
    def screen_locked(self) -> bool:
        return self._equipment_info.get("@SCREENLOCK")["value"] == 1

    @property
    def modes(self) -> List[ThermostatOperationMode]:
        """Return a list of supported operation modes"""
        _supported_modes = []
        _modes = self._equipment_info.get("@MODE")["constraints"]["enumText"]
        for _mode in _modes:
            _op_mode = ThermostatOperationMode.by_string(_mode)
            if _op_mode is not ThermostatOperationMode.UNKNOWN:
                _supported_modes.append(_op_mode)
        return _supported_modes

    @property
    def mode(self) -> Union[ThermostatOperationMode, None]:
        """Return the current mode"""
        return self.modes[self._equipment_info.get("@MODE")["value"]]

    def set_mode(self, mode: ThermostatOperationMode):
        """Set the provided mode"""
        payload = {}
        text_modes = self._equipment_info["@MODE"]["constraints"]["enumText"]
        count = 0
        for text_mode in text_modes:
            if mode == ThermostatOperationMode.by_string(text_mode):
                payload["@MODE"] = count
            count = count + 1
        self._api.publish(payload, self.device_id, self.serial_number)

    @property
    def fan_modes(self) -> List[ThermostatFanMode]:
        """Return a list of supported operation modes"""
        _supported_modes = []
        _modes = self._equipment_info.get("@FANSPEED")["constraints"]["enumText"]
        for _mode in _modes:
            _op_mode = ThermostatFanMode.by_string(_mode)
            if _op_mode is not ThermostatOperationMode.UNKNOWN:
                _supported_modes.append(_op_mode)
        return _supported_modes

    @property
    def fan_mode(self) -> Union[ThermostatFanMode, None]:
        """Return the current mode"""
        return self.fan_modes[self._equipment_info.get("@FANSPEED")["value"]]

    def set_fan_mode(self, mode: ThermostatFanMode):
        """Set the provided mode"""
        payload = {}
        text_modes = self._equipment_info["@FANSPEED"]["constraints"]["enumText"]
        count = 0
        for text_mode in text_modes:
            if mode == ThermostatOperationMode.by_string(text_mode):
                payload["@FANSPEED"] = count
            count = count + 1
        self._api.publish(payload, self.device_id, self.serial_number)


