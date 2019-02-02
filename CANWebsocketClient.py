import websocket
import time
import json
import datetime as dt
import logging
from datetime import datetime
import os


def pedalbox2_parse(can_id, data):
    data = {
        'id': can_id,
        'throttle_1': int(data[:4], 16),
        'throttle_2': int(data[4:8], 16),
        'break_1': int(data[8:12], 16),
        'break_2': int(data[12:16], 16),
        'parsed': True,
        'timestamp': dt.datetime.now()
    }
    return data


def pedalbox1_parse(can_id, data):
    data = {
        'id': can_id,
        'throttle_value': int(data[:4], 16),
        'break_value': int(data[4:8], 16),
        'parsed': True
    }

    return data


def no_parse_function_found(can_id, data):
    # print("No parse function found for " + str(can_id) + " with data: " +
    #       str(data))
    return {'id': can_id, 'data': data, 'parsed': False}


def parse_CAN_frame(can_id, data):
    id_parse_functions = {
        '500': pedalbox1_parse,
        '501': pedalbox2_parse,
    }

    parse_function = id_parse_functions.get(
        can_id,
        no_parse_function_found)
    return parse_function(can_id, data)


def parseRawMessage(message):

    can_frame_data = parse_CAN_frame(
        message['id'],
        message['message'])

    # if can_frame_data['parsed']:
    return can_frame_data


class CANWebsocketClient():
    def __init__(self, callback, on_close, debug=False):
        self.callback = callback
        self.on_close = on_close
        self.is_debug = debug
        self.ws = None

    def on_message(self, message):
        data = json.loads(message)

        # When running from localhost, messages are sent in strings,
        # not JSON objects. They need to be parsed yet again...
        if self.is_debug and isinstance(data, str):
            data = json.loads(data)
            if 'type' not in data:
                return
        print(data['type'])
        if data['type'] == 'data':
            payload = data['payload']
            self.onRecvData(payload)

    def onRecvData(self, payload):
        buffer = []
        for m_id in payload:
            buffer.append(payload[m_id])
        self.callback(buffer)

    def on_error(ws, error):
        print(error)

    def start(self, address):
        if self.ws is not None:
            self.ws.close()
            self.ws = None

        self.ws = websocket.WebSocketApp(address,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.run_forever()
