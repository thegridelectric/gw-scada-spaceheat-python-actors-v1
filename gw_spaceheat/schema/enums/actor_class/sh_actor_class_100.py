"""sh.actor.class.100 definition"""
from abc import ABC
import enum
from typing import List


class ActorClass(enum.Enum):
    
    @classmethod
    def values(cls):
        return [elt.value for elt in cls]

    SCADA = "Scada"
    BOOLEAN_ACTUATOR = "BooleanActuator"
    POWER_METER = "PowerMeter"
    ATN = "Atn"
    SIMPLE_SENSOR = "SimpleSensor"
    NONE = "None"
    

class ShActorClass100GtEnum(ABC):
    symbols: List[str] = ["6d37aa41",
                          "fddd0064",
                          "2ea112b9",
                          "b103058f",
                          "dae4b2f0",
                          "99a5f20d",
                          ]
