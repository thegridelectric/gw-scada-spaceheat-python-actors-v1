"""Base for multipurpose.sensor.component.gt.000"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format
from schema.gt.telemetry_reporting_config.telemetry_reporting_config import TelemetryReportingConfig
from schema.enums import (
    TelemetryName,
    TelemetryNameMap,
)

class MultipurposeSensorComponentGtBase(NamedTuple):
    ComponentId: str  #
    ComponentAttributeClassId: str
    ChannelList: List[int]
    ConfigList: List[TelemetryReportingConfig]
    DisplayName: Optional[str] = None
    HwUid: Optional[str] = None
    TypeAlias: str = "multipurpose.sensor.component.gt.000"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["HwUid"] is None:
            del d["HwUid"]
        config_list = []
        for elt in self.ConfigList:
            config_list.append(elt.asdict())
        d["ConfigList"] = config_list
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(
                    f"DisplayName {self.DisplayName} must have type str."
                )
        if not isinstance(self.ComponentId, str):
            errors.append(
                f"ComponentId {self.ComponentId} must have type str."
            )
        if not property_format.is_uuid_canonical_textual(self.ComponentId):
            errors.append(
                f"ComponentId {self.ComponentId}"
                " must have format UuidCanonicalTextual"
            )
        if not isinstance(self.ComponentAttributeClassId, str):
            errors.append(
                f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have type str."
            )
        if not property_format.is_uuid_canonical_textual(self.ComponentAttributeClassId):
            errors.append(
                f"ComponentAttributeClassId {self.ComponentAttributeClassId}"
                " must have format UuidCanonicalTextual"
            )
        if not isinstance(self.ChannelList, list):
            errors.append(
                f"ChannelList {self.ChannelList} must have type list."
            )
        else:
            for elt in self.ChannelList:
                if not isinstance(elt, int):
                    errors.append(
                        f"elt {elt} of ChannelList must have type int"
                    )
        if not isinstance(self.ConfigList, list):
            errors.append(
                f"TelemetryNameList {self.ConfigList} must have type list."
            )
        else:
            for elt in self.ConfigList:
                if not isinstance(elt, TelemetryReportingConfig):
                    errors.append(
                        f"elt {elt} of ConfigList must have type TelemetryReportingConfig."
                    )

        if self.HwUid:
            if not isinstance(self.HwUid, str):
                errors.append(
                    f"HwUid {self.HwUid} must have type str."
                )
        if self.TypeAlias != "multipurpose.sensor.component.gt.000":
            errors.append(
                f"Type requires TypeAlias of multipurpose.sensor.component.gt.000, not {self.TypeAlias}."
            )

        return errors
