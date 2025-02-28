"""Entity Factory"""
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Sequence

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity import EntityDescription

from ..common.entity_controller import EntityController
from ..common.register_type import RegisterType
from .inverter_model_spec import InverterModelSpec

# HA introduced a FrozenOrThawed metaclass which is used by EntityDescription.
# This conflicts with ABC's metaclass.
# If EntityDescription has a metaclass (FrozenOrThawed), we need to combine that with
# ABC's metaclass, see https://github.com/nathanmarlor/foxess_modbus/issues/480.
# This is to allow HA to move to frozen entity descriptions (to aid caching), and will
# start logging deprecation warnings in 2024.x.
if type(EntityDescription) == type(type):  # type: ignore
    _METACLASS = type(ABC)
    ENTITY_DESCRIPTION_KWARGS = {}
else:

    class EntityFactoryMetaclass(type(EntityDescription), type(ABC)):  # type: ignore
        """
        Metaclass to use for EntityFactory.
        """

    _METACLASS = EntityFactoryMetaclass
    ENTITY_DESCRIPTION_KWARGS = {"frozen": True}


class EntityFactory(ABC, metaclass=_METACLASS):  # type: ignore
    """Factory which can create entities"""

    @property
    @abstractmethod
    def entity_type(self) -> type[Entity]:
        """Fetch the type of entity that this factory creates"""

    @abstractmethod
    def create_entity_if_supported(
        self,
        hass: HomeAssistant,
        controller: EntityController,
        inverter_model: str,
        register_type: RegisterType,
        entry: ConfigEntry,
        inv_details: dict[str, Any],
    ) -> Entity | None:
        """Instantiate a new entity. The returned type must match self.entity_type"""

    def _supports_inverter_model(
        self,
        address_specs: Sequence[InverterModelSpec],
        inverter_model: str,
        register_type: RegisterType,
    ) -> bool:
        """Helper to determine whether this entity description supports the given inverter model and register type"""

        result = False
        for spec in address_specs:
            addresses = spec.addresses_for_inverter_model(inverter_model, register_type)
            if addresses is not None:
                # We shouldn't get more than one spec which matches
                assert not result, f"{self}: more than one address spec defined for ({inverter_model}, {register_type})"
                result = True
        return result

    def _address_for_inverter_model(
        self,
        address_specs: Sequence[InverterModelSpec],
        inverter_model: str,
        register_type: RegisterType,
    ) -> int | None:
        """
        Helper to fetch single address of an entity, on this inverter model and connection type combination, given the
        set of InverterModelSpec which was given to the entity description. Returns None if this entity is not supported
        on the model/connection type combination.

        This will assert if the InverterModelSpec gives more than one address, or more than one member in address_specs
        matches.
        """

        result: int | None = None
        for spec in address_specs:
            addresses = spec.addresses_for_inverter_model(inverter_model, register_type)
            if addresses is not None:
                assert len(addresses) == 1, f"{self}: != 1 addresses defined for ({inverter_model}, {register_type})"
                # We shouldn't get more than one spec which matches
                assert (
                    result is None
                ), f"{self}: more than one address spec defined for ({inverter_model}, {register_type})"
                result = addresses[0]
        return result

    def _addresses_for_inverter_model(
        self,
        address_specs: Sequence[InverterModelSpec],
        inverter_model: str,
        register_type: RegisterType,
    ) -> list[int] | None:
        """Helper to fetch the addresses of an entity, on this inverter and connection type combination, given the
        set of which was given to the entity description. Returns None if this entity is not supported
        on the model/connection type combination.

        This will assert if more than one member in address_specs matches.
        """

        result: list[int] | None = None
        for spec in address_specs:
            addresses = spec.addresses_for_inverter_model(inverter_model, register_type)
            if addresses is not None:
                # We shouldn't get more than one spec which matches
                assert (
                    result is None
                ), f"{self}: more than one address spec defined for ({inverter_model}, {register_type})"
                result = addresses
        return result
