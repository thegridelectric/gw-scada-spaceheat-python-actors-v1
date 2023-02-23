"""Scada implementation"""
import asyncio
import dataclasses
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence

import pendulum
from actors2 import ActorInterface
from actors2.message import ScadaDBG, ScadaDBGCommands
from actors.utils import QOS
from proactor.config import LoggerLevels
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from gwproto import (
    CallableDecoder,
    Decoders,
    MQTTCodec,
    MQTTTopic,
    create_message_payload_discriminator,
)
from gwproto.enums import TelemetryName
from gwproto.messages import (
    EventBase,
    GsPwr,
    GsPwr_Maker,
    GtDispatchBoolean_Maker,
    GtShCliAtnCmd_Maker,
    GtShStatus,
    GtShStatus_Maker,
    SnapshotSpaceheat,
    SnapshotSpaceheat_Maker,
)
from paho.mqtt.client import MQTTMessageInfo
from proactor.logger import ProactorLogger
from proactor.message import Message, MQTTReceiptPayload
from proactor.proactor_implementation import Proactor
from pydantic import BaseModel
from schema.enums import Role

from tests.atn import messages
from tests.atn.atn_config import AtnSettings

AtnMessageDecoder = create_message_payload_discriminator(
    model_name="AtnMessageDecoder",
    module_names=["gwproto.messages", "actors2.message"],
    modules=[messages],
)


class AtnMQTTCodec(MQTTCodec):
    hardware_layout: HardwareLayout

    def __init__(self, hardware_layout: HardwareLayout):
        self.hardware_layout = hardware_layout
        super().__init__(
            Decoders.from_objects(
                [
                    GtShStatus_Maker,
                    SnapshotSpaceheat_Maker,
                ],
                message_payload_discriminator=AtnMessageDecoder,
            ).add_decoder("p", CallableDecoder(lambda decoded: GsPwr_Maker(decoded[0]).tuple))
        )

    def validate_source_alias(self, source_alias: str):
        if source_alias != self.hardware_layout.scada_g_node_alias:
            raise Exception(f"alias {source_alias} not my Scada!")


class MessageStats:
    num_received: int
    num_received_by_topic: dict[str, int]
    num_received_by_message_type: dict[str, int]

    def __init__(self):
        self.reset()

    def reset(self):
        self.num_received = 0
        self.num_received_by_topic = defaultdict(int)
        self.num_received_by_message_type = defaultdict(int)

    def add_message(self, message: Message) -> None:
        self.num_received += 1
        self.num_received_by_message_type[message.Header.MessageType] += 1

    def add_mqtt_message(self, message: Message[MQTTReceiptPayload]) -> None:
        self.num_received_by_message_type[message.Header.MessageType] += 1
        self.num_received_by_topic[message.Payload.message.topic] += 1

    @property
    def num_status_received(self) -> int:
        return self.num_received_by_message_type[GtShStatus_Maker.type_alias]

    @property
    def num_snapshot_received(self) -> int:
        return self.num_received_by_message_type[SnapshotSpaceheat_Maker.type_alias]


class Telemetry(BaseModel):
    Value: int
    Unit: TelemetryName


class RecentRelayState(BaseModel):
    State: Optional[int] = None
    LastChangeTimeUnixMs: Optional[int] = None


class AtnData:
    latest_snapshot: Optional[SnapshotSpaceheat] = None
    latest_status: Optional[GtShStatus] = None


@dataclass
class _PausedAck:
    client: str
    message: Message
    qos: int
    context: Optional[Any]


class SimpleOrangeAtn(ActorInterface, Proactor):
    SCADA_MQTT = "scada"

    settings: AtnSettings
    layout: HardwareLayout
    _node: ShNode
    data: AtnData
    stats: MessageStats
    my_sensors: Sequence[ShNode]
    my_relays: Sequence[ShNode]
    event_loop_thread: Optional[threading.Thread] = None
    acks_paused: bool
    needs_ack: list[_PausedAck]
    mqtt_messages_dropped: bool
    relay_state: Dict[ShNode, RecentRelayState]

    def __init__(
        self,
        name: str,
        settings: AtnSettings,
        hardware_layout: HardwareLayout,
    ):
        super().__init__(
            name=name, logger=ProactorLogger(**settings.logging.qualified_logger_names())
        )
        self._node = hardware_layout.node(name)
        self.data = AtnData()

        self.settings = settings
        self.layout = hardware_layout
        self.my_sensors = list(
            filter(
                lambda x: (
                    x.role == Role.TANK_WATER_TEMP_SENSOR
                    or x.role == Role.BOOLEAN_ACTUATOR
                    or x.role == Role.PIPE_TEMP_SENSOR
                    or x.role == Role.PIPE_FLOW_METER
                    or x.role == Role.POWER_METER
                ),
                list(self.layout.nodes.values()),
            )
        )
        self.my_relays = list(
            filter(lambda x: x.role == Role.BOOLEAN_ACTUATOR, list(self.layout.nodes.values()))
        )
        self.relay_state = {x: RecentRelayState() for x in self.my_relays}
        self._add_mqtt_client(SimpleOrangeAtn.SCADA_MQTT, self.settings.scada_mqtt, AtnMQTTCodec(self.layout))
        self._mqtt_clients.subscribe(
            SimpleOrangeAtn.SCADA_MQTT,
            MQTTTopic.encode_subscription(Message.type_name(), self.layout.scada_g_node_alias),
            QOS.AtMostOnce,
        )

        self.latest_status: Optional[GtShStatus] = None
        self.status_output_dir = self.settings.paths.data_dir / "status"
        self.status_output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = MessageStats()
        self.acks_paused = False
        self.needs_ack = []
        self.mqtt_messages_dropped = False

    @property
    def alias(self) -> str:
        return self._name

    @property
    def node(self) -> ShNode:
        return self._node

    @property
    def publication_name(self) -> str:
        return self.layout.atn_g_node_alias

    def pause_acks(self):
        self.acks_paused = True

    def release_acks(self, clear: bool = False):
        self.acks_paused = False
        needs_ack = self.needs_ack
        self.needs_ack = []
        if not clear:
            for paused_ack in needs_ack:
                self._publish_message(**dataclasses.asdict(paused_ack))

    def _publish_message(
        self, client, message: Message, qos: int = 0, context: Any = None
    ) -> MQTTMessageInfo:
        if self.acks_paused:
            self.needs_ack.append(_PausedAck(client, message, qos, context))
            return MQTTMessageInfo(-1)
        else:
            return super()._publish_message(client, message, qos=qos, context=context)

    def drop_mqtt(self, drop: bool):
        self.mqtt_messages_dropped = drop

    def _publish_to_scada(self, payload, qos: QOS = QOS.AtMostOnce) -> MQTTMessageInfo:
        message = Message(Src=self.publication_name, Payload=payload)
        return self._publish_message(SimpleOrangeAtn.SCADA_MQTT, message, qos=qos)

    async def process_message(self, message: Message):
        self.stats.add_message(message)
        await super().process_message(message)

    def _process_mqtt_message(self, message: Message[MQTTReceiptPayload]):
        if not self.mqtt_messages_dropped:
            self.stats.add_mqtt_message(message)
            super()._process_mqtt_message(message)

    def _derived_process_message(self, message: Message):
        self._logger.path(
            "++SimpleOrangeAtn._derived_process_message %s/%s", message.Header.Src, message.Header.MessageType
        )
        path_dbg = 0
        match message.Payload:
            case GtShCliAtnCmd_Maker():
                path_dbg |= 0x00000001
                self._publish_to_scada(message.Payload.tuple.asdict())
            case GtDispatchBoolean_Maker():
                path_dbg |= 0x00000002
                self._publish_to_scada(message.Payload.tuple.asdict())
            case ScadaDBG():
                path_dbg |= 0x00000004
                self._publish_to_scada(message.Payload)
            case _:
                path_dbg |= 0x00000008

        self._logger.path("--SimpleOrangeAtn._derived_process_message  path:0x%08X", path_dbg)

    def _derived_process_mqtt_message(self, message: Message[MQTTReceiptPayload], decoded: Any):
        self._logger.path("++SimpleOrangeAtn._derived_process_mqtt_message %s", message.Payload.message.topic)
        path_dbg = 0
        if message.Payload.client_name != self.SCADA_MQTT:
            raise ValueError(
                f"There are no messages expected to be received from [{message.Payload.client_name}] mqtt broker. "
                f"Received\n\t topic: [{message.Payload.message.topic}]"
            )
        self.stats.add_message(decoded)
        match decoded.Payload:
            case GsPwr():
                path_dbg |= 0x00000001
                self._process_pwr(decoded.Payload)
            case SnapshotSpaceheat():
                path_dbg |= 0x00000002
                self._process_snapshot(decoded.Payload)
            case GtShStatus():
                path_dbg |= 0x00000004
                self._process_status(decoded.Payload)
            case EventBase():
                path_dbg |= 0x00000008
                self._process_event(decoded.Payload)
            case _:
                path_dbg |= 0x00000010
        self._logger.path("--SimpleOrangeAtn._derived_process_mqtt_message  path:0x%08X", path_dbg)

    def _process_pwr(self, pwr: GsPwr) -> None:
        pass

    def _process_snapshot(self, snapshot: SnapshotSpaceheat) -> None:
        self.data.latest_snapshot = snapshot
        for node in self.my_relays:
            possible_indices = []
            for idx in range(len(snapshot.Snapshot.AboutNodeAliasList)):
                if (
                    snapshot.Snapshot.AboutNodeAliasList[idx] == node.alias
                    and snapshot.Snapshot.TelemetryNameList[idx] == TelemetryName.RelayState
                ):
                    possible_indices.append(idx)
            if len(possible_indices) != 1:
                raise Exception(
                    f"{node.alias} has {len(possible_indices)} possibilities for relay state! Should be 1"
                )
            idx = possible_indices[0]
            old_state = self.relay_state[node].State
            if old_state != snapshot.Snapshot.ValueList[idx]:
                self.relay_state[node].State = snapshot.Snapshot.ValueList[idx]
                self.relay_state[node].LastChangeTimeUnixMs = int(time.time() * 1000)

        s = "\n\nSnapshot received:\n"

        for i in range(len(snapshot.Snapshot.AboutNodeAliasList)):
            s += (
                f"  {snapshot.Snapshot.AboutNodeAliasList[i]}: "
                f"{snapshot.Snapshot.ValueList[i]} "
                f"{snapshot.Snapshot.TelemetryNameList[i].value}\n"
            )
        # s += f"snapshot is None:{snapshot is None}\n"
        # s += "json.dumps(snapshot.asdict()):\n"
        # s += json.dumps(snapshot.asdict(), sort_keys=True, indent=2)
        # s += "\n"
        self._logger.warning(s)
        # rich.print(snapshot)

    def _process_dbg_command(self, dbg: ScadaDBG):
        pass

    def _process_status(self, status: GtShStatus) -> None:
        self.data.latest_status = status
        status_file = self.status_output_dir / f"GtShStatus.{status.SlotStartUnixS}.json"
        with status_file.open("w") as f:
            f.write(status.as_type())
        self._logger.info(f"Wrote status file [{status_file}]")

    def _process_event(self, event: EventBase) -> None:
        event_dt = pendulum.from_timestamp(event.TimeNS / 1000000000)
        event_file = (
            self.settings.paths.event_dir
            / f"{event_dt.isoformat()}.{event.TypeName}.uid[{event.MessageId}].json"
        )
        with event_file.open("w") as f:
            f.write(event.json(sort_keys=True, indent=2))

    def snap(self):
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.name,
                Payload=GtShCliAtnCmd_Maker(
                    from_g_node_alias=self.layout.atn_g_node_alias,
                    from_g_node_id=self.layout.atn_g_node_id,
                    send_snapshot=True,
                ),
            )
        )

    def dbg(
        self,
        message_summary: int = -1,
        lifecycle: int = -1,
        comm_event: int = -1,
        command: Optional[ScadaDBGCommands | str] = None,
    ):
        if isinstance(command, str):
            command = ScadaDBGCommands(command)
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.name,
                Payload=ScadaDBG(
                    Levels=LoggerLevels(
                        message_summary=message_summary,
                        lifecycle=lifecycle,
                        comm_event=comm_event,
                    ),
                    Command=command,
                ),
            )
        )

    def set_relay(self, name: str, state: bool) -> None:
        self.send_threadsafe(
            Message(
                Src=self.name,
                Dst=self.name,
                Payload=GtDispatchBoolean_Maker(
                    about_node_name=name,
                    to_g_node_alias=self.layout.scada_g_node_alias,
                    from_g_node_alias=self.layout.atn_g_node_alias,
                    from_g_node_instance_id=self.layout.atn_g_node_id,
                    relay_state=int(state),
                    send_time_unix_ms=int(time.time() * 1000),
                ),
            )
        )

    def turn_on(self, relay_node: ShNode):
        self.set_relay(relay_node.alias, True)

    def turn_off(self, relay_node: ShNode):
        self.set_relay(relay_node.alias, False)

    def latest_simple_reading(self, node: ShNode) -> Optional[Telemetry]:
        """Provides the latest reported Telemetry value as reported in a snapshot
        message from the Scada, for a simple sensor.

        Args:
            node (ShNode): A Spaceheat Node associated to a simple sensor.

        Returns:
            Optional[int]: Returns None if no value has been reported.
            This will happen for example if the node is not associated to
            a simple sensor.
        """
        snap = self.data.latest_snapshot.Snapshot
        try:
            idx = snap.AboutNodeAliasList.index(node.alias)
        except ValueError:
            return None

        return Telemetry(Value=snap.ValueList[idx], Unit=snap.TelemetryNameList[idx])

    def start(self):
        if self.event_loop_thread is not None:
            raise ValueError("ERROR. start() already called once.")
        self.event_loop_thread = threading.Thread(target=asyncio.run, args=[self.run_forever()])
        self.event_loop_thread.start()

    def stop_and_join_thread(self):
        self.stop()
        if self.event_loop_thread is not None and self.event_loop_thread.is_alive():
            self.event_loop_thread.join()

    def summary_str(self) -> str:
        """Summarize results in a string"""
        s = (
            f"Atn [{self.node.alias}] total: {self.stats.num_received}  "
            f"status:{self.stats.num_status_received}  snapshot:{self.stats.num_snapshot_received}"
        )
        if self.stats.num_received_by_topic:
            s += "\n  Received by topic:"
            for topic in sorted(self.stats.num_received_by_topic):
                s += f"\n    {self.stats.num_received_by_topic[topic]:3d}: [{topic}]"
        if self.stats.num_received_by_message_type:
            s += "\n  Received by message_type:"
            for message_type in sorted(self.stats.num_received_by_message_type):
                s += f"\n    {self.stats.num_received_by_message_type[message_type]:3d}: [{message_type}]"

        return s
