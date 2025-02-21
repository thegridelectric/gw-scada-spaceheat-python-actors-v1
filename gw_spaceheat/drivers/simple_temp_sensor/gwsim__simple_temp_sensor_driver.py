import random
import time

from result import Err
from result import Ok
from result import Result

from actors2.config import ScadaSettings
from data_classes.components.simple_temp_sensor_component import SimpleTempSensorComponent
from drivers.driver_result import DriverResult
from drivers.simple_temp_sensor.simple_temp_sensor_driver import SimpleTempSensorDriver
from schema.enums.make_model.make_model_map import MakeModel
from schema.enums.unit.unit_map import Unit


class Gwsim_SimpleTempSensorDriver(SimpleTempSensorDriver):
    READ_TIME_FUZZ_MULTIPLIER = 6
    read_count: int
    except_on_read: bool = False
    except_on_read_after: int = 0
    hang_on_read: bool = False
    hang_on_read_after: int = 0

    def __init__(self, component: SimpleTempSensorComponent, settings: ScadaSettings):
        super(Gwsim_SimpleTempSensorDriver, self).__init__(
            component=component,
            settings=settings,
        )
        if component.cac.make_model != MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION:
            raise Exception(f"Expected GridWorks__WaterTempHighPrecision, got {component.cac}")
        if component.cac.temp_unit == Unit.FAHRENHEIT:
            self._fake_temp_times_1000 = 67000
        elif component.cac.temp_unit == Unit.CELCIUS:
            self._fake_temp_times_1000 = 19444
        else:
            raise Exception(f"TempSensor unit {component.cac.temp_unit} not recognized!")
        self.read_count = 0
        self.except_on_read = False
        self.except_on_read_after = 0
        self.hang_on_read = False
        self.hang_on_read_after = 0


    def cmd_delay(self):
        typical_delay_ms = self.component.cac.typical_response_time_ms
        read_delay_ms = typical_delay_ms + int(self.READ_TIME_FUZZ_MULTIPLIER * random.random())
        time.sleep(read_delay_ms / 1000)

    def read_telemetry_value(self) -> Result[DriverResult[int | None], Exception]:
        self.read_count += 1
        if self.except_on_read or self.except_on_read_after or self.hang_on_read or self.hang_on_read_after:
            print(f"read_count: {self.read_count}")
        self.cmd_delay()
        self._fake_temp_times_1000 += 250 - int(500 * random.random())
        if self.except_on_read or 0 < self.except_on_read_after <= self.read_count:
            return Err(IOError("arg fizzle pop squark simulated driver error"))
        if self.hang_on_read or 0 < self.hang_on_read_after <= self.read_count:
            while True:
                print("Lunch time for this driver")
                time.sleep(10)
        return Ok(DriverResult(self._fake_temp_times_1000))
