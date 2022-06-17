"""BooleanActuatorCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.cacs.boolean_actuator_cac_base import BooleanActuatorCacBase
from schema.gt.gt_boolean_actuator_cac.gt_boolean_actuator_cac import GtBooleanActuatorCac
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName


class BooleanActuatorCac(BooleanActuatorCacBase):
    by_id: Dict[str, "BooleanActuatorCac"] = {}

    def __init__(self, component_attribute_class_id: str,
                 make_model_gt_enum_symbol: str,
                 typical_response_time_ms: Optional[int],
                 display_name: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(component_attribute_class_id=component_attribute_class_id,
                                             display_name=display_name,
                                             make_model_gt_enum_symbol=make_model_gt_enum_symbol,
                                             typical_response_time_ms=typical_response_time_ms
                                             )
        BooleanActuatorCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def _check_update_axioms(self, type: GtBooleanActuatorCac):
        pass

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"

    @property
    def telemetry_name(self):
        return TelemetryName.RELAY_STATE
