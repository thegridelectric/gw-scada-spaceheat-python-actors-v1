"""Makes gt.electric.meter.component.100 type"""
import json
from typing import Optional
from data_classes.components.electric_meter_component import ElectricMeterComponent

from schema.gt.gt_electric_meter_component.gt_electric_meter_component import GtElectricMeterComponent
from schema.errors import MpSchemaError


class GtElectricMeterComponent_Maker:
    type_alias = "gt.electric.meter.component.100"

    def __init__(self,
                 component_attribute_class_id: str,
                 component_id: str,
                 display_name: Optional[str],
                 hw_uid: Optional[str],
                 modbus_host: Optional[str],
                 modbus_port: Optional[int],
                 modbus_power_register: Optional[int],
                 modbus_hw_uid_register: Optional[int],
                ):

        gw_tuple = GtElectricMeterComponent(
            ComponentAttributeClassId=component_attribute_class_id,
            DisplayName=display_name,
            ComponentId=component_id,
            HwUid=hw_uid,
            ModbusHost=modbus_host,
            ModbusPort=modbus_port,
            ModbusPowerRegister=modbus_power_register,
            ModbusHwUidRegister=modbus_hw_uid_register,
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtElectricMeterComponent) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtElectricMeterComponent:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtElectricMeterComponent:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "ComponentAttributeClassId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentAttributeClassId")
        if "DisplayName" not in new_d.keys():
            new_d["DisplayName"] = None
        if "ComponentId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentId")
        if "HwUid" not in new_d.keys():
            new_d["HwUid"] = None
        if "ModbusHost" not in new_d.keys():
            new_d["ModbusHost"] = None
        if "ModbusPort" not in new_d.keys():
            new_d["ModbusPort"] = None
        if "ModbusPowerRegister" not in new_d.keys():
            new_d["ModbusPowerRegister"] = None
        if "ModbusHwUidRegister" not in new_d.keys():
            new_d["ModbusHwUidRegister"] = None
 
        gw_tuple = GtElectricMeterComponent(
            TypeAlias=new_d["TypeAlias"],
            ComponentAttributeClassId=new_d["ComponentAttributeClassId"],
            DisplayName=new_d["DisplayName"],
            ComponentId=new_d["ComponentId"],
            HwUid=new_d["HwUid"],
            ModbusHost=new_d["ModbusHost"],
            ModbusPort=new_d["ModbusPort"],
            ModbusPowerRegister=new_d["ModbusPowerRegister"],
            ModbusHwUidRegister=new_d["ModbusHwUidRegister"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple

    @classmethod
    def tuple_to_dc(cls, t: GtElectricMeterComponent) -> ElectricMeterComponent:
        s = {
            "display_name": t.DisplayName,
            "component_id": t.ComponentId,
            "hw_uid": t.HwUid,
            "modbus_host": t.ModbusHost,
            "modbus_port": t.ModbusPort,
            "modbus_power_register": t.ModbusPowerRegister,
            "modbus_hw_uid_register": t.ModbusHwUidRegister,
            "component_attribute_class_id": t.ComponentAttributeClassId,
            #
        }
        if s["component_id"] in ElectricMeterComponent.by_id.keys():
            dc = ElectricMeterComponent.by_id[s["component_id"]]
        else:
            dc = ElectricMeterComponent(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ElectricMeterComponent) -> GtElectricMeterComponent:
        if dc is None:
            return None
        t = GtElectricMeterComponent(
            DisplayName=dc.display_name,
            ComponentId=dc.component_id,
            HwUid=dc.hw_uid,
            ModbusHost=dc.modbus_host,
            ModbusPort=dc.modbus_port,
            ModbusPowerRegister=dc.modbus_power_register,
            ModbusHwUidRegister=dc.modbus_hw_uid_register,
            ComponentAttributeClassId=dc.component_attribute_class_id,
            #
        )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> ElectricMeterComponent:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: ElectricMeterComponent) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> ElectricMeterComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
