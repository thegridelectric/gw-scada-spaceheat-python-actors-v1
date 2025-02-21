"""Makes multipurpose.sensor.component.gt.000 type"""
import json
from typing import Optional
from typing import List
from data_classes.components.multipurpose_sensor_component import MultipurposeSensorComponent
from schema.enums import (
    TelemetryName,
    TelemetryNameMap,
)

from schema.gt.multipurpose_sensor_component_gt.multipurpose_sensor_component_gt import MultipurposeSensorComponentGt
from schema.errors import MpSchemaError
from schema.gt.telemetry_reporting_config.telemetry_reporting_config_maker import (
    TelemetryReportingConfig,
    TelemetryReportingConfig_Maker,
)

class MultipurposeSensorComponentGt_Maker:
    type_alias = "multipurpose.sensor.component.gt.000"

    def __init__(self,
                 component_id: str,
                 component_attribute_class_id: str,
                 channel_list: List[int],
                 config_list: List[TelemetryReportingConfig],
                 display_name: Optional[str],
                 hw_uid: Optional[str],
                 ):

        gw_tuple = MultipurposeSensorComponentGt(
            ComponentId=component_id,
            ComponentAttributeClassId=component_attribute_class_id,
            ChannelList=channel_list,
            ConfigList=config_list,
            DisplayName=display_name,
            HwUid=hw_uid,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: MultipurposeSensorComponentGt) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> MultipurposeSensorComponentGt:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> MultipurposeSensorComponentGt:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "ComponentId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentId")
        if "ComponentAttributeClassId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentAttributeClassId")

        if "ChannelList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ChannelList")
        if "ConfigList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ConfigList")
        config_list = []
        for elt in new_d["ConfigList"]:
            if not isinstance(elt, dict):
                raise MpSchemaError(
                    f"elt {elt} of ConfigList must be "
                    "TelemetryReportingConfig but not even a dict!"
                )
            config_list.append(
                TelemetryReportingConfig_Maker.dict_to_tuple(elt)
            )
            new_d["ConfigList"] =config_list
        if "HwUid" not in new_d.keys():
            new_d["HwUid"] = None
        if "DisplayName" not in new_d.keys():
            new_d["DisplayName"] = None
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")

        gw_tuple = MultipurposeSensorComponentGt(
            ComponentId=new_d["ComponentId"],
            ComponentAttributeClassId=new_d["ComponentAttributeClassId"],
            ChannelList=new_d["ChannelList"],
            ConfigList=new_d["ConfigList"],
            HwUid=new_d["HwUid"],
            DisplayName=new_d["DisplayName"],
            TypeAlias=new_d["TypeAlias"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple

    @classmethod
    def tuple_to_dc(cls, t: MultipurposeSensorComponentGt) -> MultipurposeSensorComponent:
        s = {
            "component_id": t.ComponentId,
            "component_attribute_class_id": t.ComponentAttributeClassId,
            "channel_list": t.ChannelList,
            "config_list": t.ConfigList,
            "hw_uid": t.HwUid,
            "display_name": t.DisplayName,
        }
        if s["component_id"] in MultipurposeSensorComponent.by_id.keys():
            dc = MultipurposeSensorComponent.by_id[s["component_id"]]
        else:
            dc = MultipurposeSensorComponent(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: MultipurposeSensorComponent) -> MultipurposeSensorComponentGt:
        if dc is None:
            return None
        t = MultipurposeSensorComponentGt(
            ComponentId=dc.component_id,
            ComponentAttributeClassId=dc.component_attribute_class_id,
            ChannelList=dc.channel_list,
            ConfigList=dc.config_list,
            HwUid=dc.hw_uid,
            DisplayName=dc.display_name,
            #
        )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> MultipurposeSensorComponent:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: MultipurposeSensorComponent) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> MultipurposeSensorComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
