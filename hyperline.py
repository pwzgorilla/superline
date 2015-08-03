__author__ = 'nmg'

import asyncio
import json
import websockets
import log as logging

from protocol import HyperLineProtocol
from protocol import WSProtocol
from handlers import MessageHandler
# from session import SessionManager
from messages import Message
from messages import MessageFormatError
from validators import validate_format, ValidatedError

logger = logging.getLogger(__name__)

class HyperLine(HyperLineProtocol):
    """
    Every new clients connection will create one HyperLine object for message handling.

        new connection -> HyperLine()
    """

    def __init__(self):

        self.handler = MessageHandler()  # singleton

        self.transport = None

    def connection_made(self, transport):

        self.transport = transport

    def message_received(self, msg):
        """
        The real message handler
        @param msg: a full message without prefix length
        @return: None
        """
        # Convert bytes msg to python dictionary
        msg = json.loads(msg.decode("utf-8"))

        # Handler msg
        return self.handler.handle(msg, self.transport)


class WSHyperLine(WSProtocol):

    def __init__(self):

        self.handler = MessageHandler()  # singleton
        self.message = Message()

    @asyncio.coroutine
    def connection_made(self, connection):
        # """
        # Every connection will create one new Session
        # """
        """
        Populated session attribute `transport` with `ws` from connection
        """
        logger.info('New connection made')

        # connection.session.transport = connection.ws
        # connection.session.path = connection.path

        # yield from connection.transport.send('welcome')

    @asyncio.coroutine
    def message_received(self, message, connection):
        """
        Decoding Json object to python dictionary. If it failed, raise error and return.
        """
        try:
            message = json.loads(message)  # message is json object
        except ValueError:
            raise MessageFormatError('message is not json object')
            return

        # Message format validate
        if not validate_format()(message):
            raise MessageFormatError('type fields must be specified')
            return

        logger.info("Send message {}".format(message))
        try:
            return self.handler.handle(self.message(message), connection)
        except ValidatedError as exc:
            return logger.error(exc.args[0])
        except MessageFormatError as exc:
            return logger.error(exc.args[0])

class HyperLineServer(object):
    def __init__(self, protocol_factory, host, port, ws_host, ws_port):

        self.host = host
        self.port = port
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.protocol_factory = protocol_factory

    def start(self):
        loop = asyncio.get_event_loop()
        logger.info('Socket server listened on {}:{}'.format(self.host, self.port))
        loop.run_until_complete(loop.create_server(self.protocol_factory, self.host, self.port))
        logger.info('Websocket server listened on {}:{}'.format(self.ws_host, self.ws_port))
        loop.run_until_complete(websockets.serve(WSHyperLine(), self.ws_host, self.ws_port))

        loop.run_forever()

