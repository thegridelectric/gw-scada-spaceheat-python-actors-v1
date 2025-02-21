from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import cast
from typing import List
from typing import Optional
from typing import Tuple

from gwproto import Message
from gwproto.messages import CommEvent
from gwproto.messages import EventT
from gwproto.messages import PingMessage
from paho.mqtt.client import MQTT_ERR_SUCCESS

from actors2 import Scada2
from actors2.config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from proactor.message import MQTTSubackPayload
from proactor.mqtt import MQTTClientWrapper
from proactor.stats import LinkStats
from proactor.stats import ProactorStats


def split_subscriptions(client_wrapper: MQTTClientWrapper) -> Tuple[int, Optional[int]]:
    for i, (topic, qos) in enumerate(client_wrapper.subscription_items()):
        MQTTClientWrapper.subscribe(client_wrapper, topic, qos)
    return MQTT_ERR_SUCCESS, None

@dataclass
class LinkStats2(LinkStats):
    comm_events: list[CommEvent] = field(default_factory=list)

    def __str__(self) -> str:
        s = super().__str__()
        if self.comm_events:
            s += "\n  Comm events:"
            for comm_event in self.comm_events:
                s += f"\n    {comm_event}"
        return s

class ProactorStats2(ProactorStats):

    @classmethod
    def make_link(cls, link_name: str) -> LinkStats2:
        return LinkStats2(link_name)


class Scada2Recorder(Scada2):

    suppress_status: bool
    subacks_paused: bool
    pending_subacks: list[Message]
    ack_timeout_seconds: float = 5.0

    def __init__(self, name: str, settings: ScadaSettings, hardware_layout: HardwareLayout, actor_nodes: Optional[List[ShNode]] = None):
        self.suppress_status = False
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout, actor_nodes=actor_nodes)
        self.subacks_paused = False
        self.pending_subacks = []

    @classmethod
    def make_stats(cls) -> ProactorStats2:
        return ProactorStats2()

    def time_to_send_status(self) -> bool:
        return not self.suppress_status and super().time_to_send_status()

    def generate_event(self, event: EventT) -> None:
        if isinstance(event, CommEvent):
            cast(LinkStats2, self.stats.link(event.PeerName)).comm_events.append(event)
        super().generate_event(event)

    def split_client_subacks(self, client_name: str):
        client_wrapper = self._mqtt_clients.client_wrapper(client_name)

        def member_split_subscriptions():
            return split_subscriptions(client_wrapper)
        client_wrapper.subscribe_all = member_split_subscriptions

    def restore_client_subacks(self, client_name: str):
        client_wrapper = self._mqtt_clients.client_wrapper(client_name)
        client_wrapper.subscribe_all = MQTTClientWrapper.subscribe_all

    def pause_subacks(self):
        self.subacks_paused = True

    def release_subacks(self, num_released: int = -1):
        self.subacks_paused = False
        if num_released < 0:
            num_released = len(self.pending_subacks)
        release = self.pending_subacks[:num_released]
        self.pending_subacks = self.pending_subacks[num_released:]
        for message in release:
            self._receive_queue.put_nowait(message)

    async def process_message(self, message: Message):
        if self.subacks_paused and isinstance(message.Payload, MQTTSubackPayload):
            self.pending_subacks.append(message)
        else:
            await super().process_message(message)

    def summary_str(self):
        s = str(self.stats)
        s += f"\nsubacks_paused: {self.subacks_paused}  pending_subacks: {len(self.pending_subacks)}\n"
        s += "Link states:\n"
        for link_name in self.stats.links:
            s += f"  {link_name:10s}  {self._link_states.link_state(link_name).value}\n"
        return s

    def _start_ack_timer(self, client_name: str, message_id: str, context: Any = None, delay: Optional[float] = None) -> None:
        if delay is None:
            delay = self.ack_timeout_seconds
        super()._start_ack_timer(client_name, message_id, context=context, delay=delay)

    def ping_atn(self):
        self._publish_message(
            self.GRIDWORKS_MQTT,
            PingMessage(Src=self.publication_name)
        )

    def summarize(self):
        self._logger.info(self.summary_str())
