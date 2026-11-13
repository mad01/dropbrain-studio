---
title: "python protobuf over http"
date: 2016-01-11
slug: python-protobuf-over-http
description: "The point of this is a smal example on how you could use protobuf to send data over http. In this example i will be using Python and the packet falcon for the server. A command…"
tags: protobuf, python, http
---
The point of this is a smal example on how you could use protobuf to send data over http. In this example i will be using Python and the packet falcon for the server. A command line tool as the client. The example will just be a simple ping/pong containing a message, channel, and PING or PONG sent to the server. The server will respond with the same message and channel and a PONG.

lets first start with the structure of the files is like the following. all files used can be found on github see source in the end of the post. a note some in the source there is some extra code that is removed to not clutter the example.
```bash
protobuf
├── client.py
├── lib
│   ├── __init__.py
│   ├── client_api.py
│   ├── py_proto.proto
│   ├── py_proto_pb2.py
│   └── server_api.py
├── requirements.txt
├── server.py
└── tests
    └── test_proto.py
```


to get started we need a protobuf file that sets the format of messages that should be used.
a enum is used to hold the name/value that we like for a pingId. a PingDTO that will hold the message values that we like in the PingDTO. We then use this PingDTO in the PingCommand and the PingDocument. The PingCommand will be used to send to the server and the response will be the PingDocument.
```bash
package api;

enum PingIdDTO {
    PING = 1;
    PONG = 2;
}

message PingDTO {
    required string msg = 1;
    required string channel = 2;
    required PingIdDTO pingId = 3;
}

message PingCommand {
    required PingDTO ping = 1;
}

message PingDocument {
    required PingDTO ping = 1;
}
```

to build the proto python file. you will get py\_proto\_pb2.py which is the protobuf python class file that you later  use to build a proto client and server.
```bash
$ protoc --python_out=. lib/py_proto.proto
```


Server api. The server uses the generated protobuf python file to parse the command sent, and to return the document to the client.
```python
#!/usr/bin/env python3
import falcon
from . import py_proto_pb2 as proto

def proto_http_type():
    return 'application/x-protobuf'

class Ping(object):

    def __init__(self):
        self.proto = proto

    def on_post(self, req, resp):
            command = proto.PingCommand()
            command.ParseFromString(req.stream.read())

            cmd = proto.PingDocument()
            cmd.ping.msg = command.ping.msg
            cmd.ping.channel = command.ping.channel
            cmd.ping.pingId = proto.PONG

            print('msg: %s' % command.ping.msg)
            print('channel: %s' % command.ping.channel)

            resp.content_type = proto_http_type()
            resp.status = falcon.HTTP_201
            resp.data = cmd.SerializeToString()
```


Server function made to run the falcon app.
```python
#!/usr/bin/env python3
import falcon
from lib import server_api

api = falcon.API()
api.add_route('/api/ping', server_api.Ping())
```


Starting the server by using gunicorn and calling the api falcon api
```bash
$ gunicorn server:api
```


Client api. Like in the server we use the same python generated proto file. To send a command to the server and get back the response document that will be printed to stdout.
```python
#!/usr/bin/env python3
import requests
from . import py_proto_pb2 as proto

class Client(object):

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/x-protobuf",
            "Accept": "application/x-protobuf"
        })

    def pingId(self, ping):
        return proto.PingIdDTO.Value(ping)

    def build_url(self, urn):
        url = 'http://%s:8000/%s' % ('127.0.0.1', urn)
        return url

    def send_ping(self, msg='', channel='', pingId=''):
        url = self.build_url('api/ping')
        command = proto.PingCommand()
        command.ping.msg = str(msg)
        command.ping.channel = str(channel)
        command.ping.pingId = self.pingId(pingId)

        res = self.session.post(url, data=command.SerializeToString())
        cmd = proto.PingDocument()
        cmd.ParseFromString(res.content)
        return cmd
```


Client made as a command line tool to be able to just send some commands and then print the response. You send PING which is id 1 and you should get back id 2 from the server
```python
#!/usr/bin/env python3
import argparse
from lib import client_api

def call(msg='', channel=''):
    api = client_api.Client()
    cmd = api.send_ping(
        msg=msg,
        channel=channel,
        pingId='PING'
        )

    print('Response: %s' % cmd.ping.pingId)
    print('message sent: %s' % cmd.ping.msg)
    print('to channel: %s' % cmd.ping.channel)

def main():
    description = 'command line tool send messages to a channel'
    parser = argparse.ArgumentParser(description)
    parser.add_argument('-m', '--message', required=True)
    parser.add_argument('-c', '--channel', required=True)
    args = parser.parse_args()
    call(
        msg=args.message,
        channel=args.channel
        )

if __name__ == '__main__':
    main()
```


The example can be found here. [Source](https://github.com/mad01/examples/tree/master/protobuf)
