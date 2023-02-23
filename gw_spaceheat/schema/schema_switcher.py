from typing import Dict, List

from gwproto.messages import  GsDispatch_Maker
from gwproto.messages import  GsPwr_Maker
from gwproto.messages import  GtDispatchBoolean_Maker
from gwproto.messages import  GtDispatchBooleanLocal_Maker
from gwproto.messages import  GtDriverBooleanactuatorCmd_Maker
from gwproto.messages import GtShBooleanactuatorCmdStatus_Maker
from gwproto.messages import  GtShCliAtnCmd_Maker
from gwproto.messages import  TelemetrySnapshotSpaceheat_Maker
from gwproto.messages import  GtShStatus_Maker
from gwproto.messages import  SnapshotSpaceheat_Maker
from gwproto.messages import  GtShTelemetryFromMultipurposeSensor_Maker
from gwproto.messages import  GtTelemetry_Maker
from gwproto.messages import HeartbeatB_Maker

TypeMakerByAliasDict: Dict[str, GtTelemetry_Maker] = {}

new_makers: List[HeartbeatB_Maker] = [
    GtDispatchBoolean_Maker,
    GtDispatchBooleanLocal_Maker,
    HeartbeatB_Maker,
    GtDriverBooleanactuatorCmd_Maker,
    GtShBooleanactuatorCmdStatus_Maker,
    GtShCliAtnCmd_Maker,
]

schema_makers: List[GtTelemetry_Maker] = [
    GsDispatch_Maker,
    GsPwr_Maker,
    TelemetrySnapshotSpaceheat_Maker,
    GtShStatus_Maker,
    SnapshotSpaceheat_Maker,
    GtShTelemetryFromMultipurposeSensor_Maker,
    GtTelemetry_Maker,
]

for maker in schema_makers:
    TypeMakerByAliasDict[maker.type_alias] = maker

for maker in new_makers:
    TypeMakerByAliasDict[maker.type_name] = maker

