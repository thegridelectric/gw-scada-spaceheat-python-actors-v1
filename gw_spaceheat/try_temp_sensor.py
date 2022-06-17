import load_house
from actors.tank_water_temp_sensor import TankWaterTempSensor
from data_classes.sh_node import ShNode


def main(input_json_file='input_data/houses.json'):
    load_house.load_all(input_json_file=input_json_file)
    thermo_node = ShNode.by_alias["a.tank.temp0"]
    thermo = TankWaterTempSensor(thermo_node)
    thermo.start()


if __name__ == "__main__":
    main()
