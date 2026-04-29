import asyncio
import base64
import hashlib
import json
import uuid
import random
import sys
import time
import traceback
from enum import Enum
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

peer_connections = set()
private_key = None
public_key = None

seen_messages = []
message_queue = []

'''
=====================================
============ Misc Helpers ===========
=====================================
'''

async def get_peer_list_from_input():
    peers = []

    print('Enter peer host:port (empty line to finish):')
    while True:
        line = await asyncio.to_thread(input, '> ')
        if not line:
            break
        host, port = line.split(':')
        port = int(port)
        peers.append((host, port))

    return peers

'''
=====================================
========= Asymmetric Key Ops ========
=====================================
'''

def public_key_to_base64(public_key):
    raw_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return base64.b64encode(raw_bytes).decode()

def base64_to_public_key(base64_string):
    raw_bytes = base64.b64decode(base64_string)
    return Ed25519PublicKey.from_public_bytes(raw_bytes)

def generate_keys():
    global private_key
    global public_key
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

'''
=====================================
========== Message Encoding =========
=====================================
'''

class MessageType(Enum):
    REGISTRATION = 1
    VOTE = 2
    # TODO: some message to get the initial chain

def encode_json(message):
    return json.dumps(message, sort_keys=True, separators=(",", ":")).encode()

def sign_message_in_place(message, key):
    json_message = encode_json(message)
    signature = key.sign(json_message)
    message['signature'] = base64.b64encode(signature).decode()

def hash(b):
    return hashlib.sha256(b).digest().hex()

def verify_message_signature(message):
    try:
        raw_message = message.copy()
        signature = raw_message.pop('signature', None)
        if signature is None:
            return False

        json_message = encode_json(raw_message)

        public_key_base64_string = raw_message['voter_pubkey']
        public_key = base64_to_public_key(public_key_base64_string)
        public_key.verify(base64.b64decode(signature.encode()), json_message)
        print(f'signature verification succeeded for {message}')
        return True
    except Exception as e:
        traceback.print_exc()
        print(f'signature verification failed for {message} {e}')
        return False

def encode_registration_message():
    message = {
        'type': MessageType.REGISTRATION.value,
    }
    # TODO:
    pass

def encode_vote_message(candidate_id):
    message = {
        'type': MessageType.VOTE.value,
        'voter_pubkey': public_key_to_base64(public_key),
        'candidate_id': candidate_id,
        'timestamp': time.time(),
    }

    json_message = encode_json(message)
    sig = private_key.sign(json_message)
    public_key.verify(sig, json_message)

    sign_message_in_place(message, private_key)

    if not verify_message_signature(message):
        print("message veritficaiotn failed");
    return message

'''
=====================================
========= Outgoing Messaging ========
=====================================
'''

async def braodcast_message(message):
    for _, _, _, writer in peer_connections:
        json_message = (json.dumps(message) + '\n').encode()
        writer.write(json_message)
        await writer.drain()

# TODO: one-to-one communication, with tracker?

'''
=====================================
========= Incoming Messaging ========
=====================================
'''

def handle_vote_message(message):
    if message in seen_messages:
        return

    if not verify_message_signature(message):
        return

    # TODO: validate further
    # TODO: return if voter exists in message queue
    # TODO: return if voterTX exists in blockchain
    # TODO: return if voter key is not signed by Tracker

    seen_messages.append(message)
    message_queue.append(message)
    print(f'queued {message}')
    pass

# TODO: handle other types of messages

'''
=====================================
============ Worker Loops ===========
=====================================
'''

async def user_input_worker():
    while True:
        print('Cast your vote:')
        candidate_id = await asyncio.to_thread(input, '> ')
        # TODO: ensure candidate_id is valid
        message = encode_vote_message(candidate_id)
        await braodcast_message(message)

async def message_worker(reader):
    while True:
        try:
            message = await reader.readline()
            if not message:
                break
            message = json.loads(message.decode())
            print(f'receieved {message}')
            if message['type'] == MessageType.VOTE.value:
                handle_vote_message(message)

        except Exception as e:
            traceback.print_exc()
            print(f'message_worker error: {e}')
            break

# TODO: probably want a mining worker to mine the next block

'''
=====================================
======== Connection Handling ========
=====================================
'''

'''
Handle peer connections initiated by peer
'''
async def handle_incoming_peer(reader, writer):
    host, port = writer.get_extra_info('peername')
    peer_connections.add((host, port, reader, writer))
    print(f'connected by {host}:{port}')

    await message_worker(reader)

    peer_connections.remove((host, port, reader, writer))
    writer.close()
    await writer.wait_closed()

'''
Handle peer connections initiated by us
'''
async def connect_to_peer(host, port):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        peer_connections.add((host, port, reader, writer))
        print(f'connected to {host}:{port}')
        await message_worker(reader)
    except Exception as e:
        print(e)
    finally:
        peer_connections.discard(writer)
        writer.close()
        await writer.wait_closed()

'''
=====================================
================ Main ===============
=====================================
'''

async def peer_main(listen_host, listen_port):
    server = await asyncio.start_server(handle_incoming_peer, listen_host, listen_port)

    # FIXME: register with real tracker, get active peers
    peers = await get_peer_list_from_input()
    # FIXME: get real keys, persist?
    generate_keys()

    for host, port in peers:
        asyncio.create_task(connect_to_peer(host, port))

    asyncio.create_task(user_input_worker())

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    listen_host = sys.argv[1]
    listen_port = int(sys.argv[2])
    asyncio.run(peer_main(listen_host, listen_port))
