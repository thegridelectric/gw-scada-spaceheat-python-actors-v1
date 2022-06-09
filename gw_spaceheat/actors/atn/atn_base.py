from abc import ABC, abstractmethod, abstractproperty
import paho.mqtt.client as mqtt
from typing import List
import uuid
import settings
import helpers
import json
import threading
from data_classes.sh_node import ShNode
from actors.actor_base import ActorBase
from actors.mqtt_utils import Subscription, QOS

from schema.gt.gt_telemetry.gt_telemetry_1_0_1_maker import  GtTelemetry101_Maker, GtTelemetry101
from schema.gs.gs_pwr_1_0_0_maker import GsPwr100_Maker, GsPwr100


MY_G_NODE_ALIAS = 'dw1.isone.nh.orange.1'
MY_SCADA_G_NODE_ALIAS = 'dw1.isone.nh.orange.1.ta.scada'

class Atn_Base(ABC):
    def __init__(self, node: ShNode):
        self.node = node
        self.logging_on = False
        self.gwMqttBroker = settings.GW_MQTT_BROKER_ADDRESS
        self.gw_publish_client_id = ('-').join(str(uuid.uuid4()).split('-')[:-1])
        self.gw_publish_client = mqtt.Client(self.gw_publish_client_id)
        self.gw_publish_client.username_pw_set(username=settings.GW_MQTT_USER_NAME , password=helpers.get_secret('GW_MQTT_PW'))
        self.gw_publish_client.connect(self.gwMqttBroker)
        self.gw_publish_client.loop_start()
        if self.logging_on:
            self.gw_publish_client.on_log = self.on_log
        self.gw_consume_client_id = ('-').join(str(uuid.uuid4()).split('-')[:-1])
        self.gw_consume_client = mqtt.Client(self.gw_consume_client_id)
        self.gw_consume_client.username_pw_set(username=settings.GW_MQTT_USER_NAME , password=helpers.get_secret('GW_MQTT_PW'))
        self.gw_consume_client.connect(self.gwMqttBroker)
        if self.logging_on:
            self.gw_consume_client.on_log = self.on_log
        self.gw_consume_thread = threading.Thread(target=self.gw_consume)

    def on_log(self, client, userdata, level, buf):
        self.screen_print(f"log: {buf}")
    
    def gw_subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'{self.my_scada.alias}/{GsPwr100_Maker.mp_alias}',Qos=QOS.AtMostOnce),
                Subscription(Topic=f'{self.my_scada.alias}/{GtTelemetry101_Maker.mp_alias}',Qos=QOS.AtLeastOnce)]

    def gw_consume(self):
        self.gw_consume_client.subscribe(list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.gw_subscriptions())))
        self.gw_consume_client.on_message = self.on_gw_message
        self.gw_consume_client.loop_forever()

    def on_gw_message(self, client, userdata, message):
        try:
            (from_alias, mp_alias) = message.topic.split('/')
        except:
            raise Exception(f"topic must be of format A/B")
        if not from_alias == MY_SCADA_G_NODE_ALIAS:
            raise Exception(f"alias {from_alias} not my AtomicTNode!")
        if mp_alias == GsPwr100_Maker.mp_alias:
            payload = GsPwr100_Maker.binary_to_type(message.payload)
            self.gs_pwr_100_received(payload=payload)
        elif mp_alias == GtTelemetry101_Maker.mp_alias:
            payload = GtTelemetry101_Maker.camel_dict_to_type(json.loads(message.payload))
            self.gt_telemetry_100_received(payload=payload)
        else:
            self.screen_print(f"{message.topic} subscription not implemented!")
       
    @abstractmethod
    def gs_pwr_100_received(self, payload: GsPwr100, from_node: ShNode):
        raise NotImplementedError
     
    @abstractmethod
    def gt_telemetry_100_received(self, payload: GtTelemetry101, from_node: ShNode):
        raise NotImplementedError

    def screen_print(self, note):
        header = f"{self.node.alias}: "
        print(header + note)
    
    @abstractproperty
    def my_scada(self) -> ShNode:
        return NotImplementedError
       

    