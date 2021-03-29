import logging
import os

from argparse import ArgumentParser
from urllib.parse import urlparse

from dependency.torpy.ext.cells import \
    CellRelayEstablishRendezvous, CellRelayIntroduce1, \
    CellRelayRendezvousEstablished, CellRelayIntroduceAck
from dependency.torpy.crypto_common import dh_public_from_bytes
from dependency.torpy.ext import TorClient
from dependency.torpy.circuit import random
from dependency.torpy.ext.circuit import CircuitNode
from dependency.torpy.ext.crypto import kdf_tor
from dependency.torpy.ext.crypto_common import dh_shared, dh_private, dh_public, dh_public_to_bytes
from dependency.torpy.documents.network_status import RouterFlags
from dependency.torpy.ext.hiddenservice import HiddenServiceConnector, IntroductionPoint, ResponsibleDir
from dependency.torpy.ext.keyagreement import TapKeyAgreement, KeyAgreementError, KeyAgreement
from dependency.torpy.ext.stream import StreamState
from dependency.torpy.utils import register_logger

logger = logging.getLogger("")
register_logger(verbose=0)

#
# --- Helper functions ---
#

# Builds a RELAY_COMMAND_ESTABLISH_RENDEZVOUS Tor cell
"def CellRelayEstablishRendezvous(rendezvous_cookie, circuit_id)"

# Builds a RELAY_COMMAND_INTRODUCE1 #Tor cell
"def CellRelayIntroduce1(intro_router, public_key, rendez_router, rendez_cookie, auth, desc, id)"

# The KDF-TOR function in Section 5.2.1
"def kdf_tor(shared_secret: bytes)"

def new_tcp_stream(circuit):
    return circuit.streams.create_new()

def stream_prepare_address(tor_stream, hostname, port):
    return tor_stream._prepare_address((hostname, port))

def connect_tor_stream(stream, address):
    stream._state = StreamState.Connecting
    stream.connect(address)

# returns a Python generator that yields a directory object of knowledgeable of the hidden service
def get_directories(circuit, hidden_service):
    # At any given time, there are 6 hidden service directories
    # responsible for keeping replicas of node descriptors
    connector = HiddenServiceConnector(circuit, circuit._guard.consensus)
    for i, responsible_router in enumerate(connector._consensus.get_responsibles(hidden_service)):
        replica = 1 if i >= 3 else 0
        yield ResponsibleDir(responsible_router, replica, connector._circuit, connector._consensus)

# returns a Python generator that yields the router object of a valid introduction point
def get_introduction_routers(hs_directory, hidden_service):
    descriptor_id = hidden_service.get_descriptor_id(hs_directory.replica)
    response = hs_directory._fetch_descriptor(descriptor_id)

    return hs_directory._get_intro_points(response, hidden_service.descriptor_cookie)

def random_router(tor_nodes):
    tor_node = random.choice(tor_nodes)
    router = tor_node.router
    logger.info('Selected node %s:%d AKA %s' % (router.ip, router.dir_port, router.nickname))
    return router

# Send a Tor cell and await another cell back as the response
def send_relay_cell(circuit, cell, response_type):
    return circuit.send_relay_cell(cell, response_type)

# Diffie-Hellman key extension (defined in Section 0.3)
def raise_exponent(base, exponent):
    return dh_shared(exponent, base)

def random_bytes(count):
    return os.urandom(count)


#
# --- Your implementation: Part II ---
#

# Send a RELAY_COMMAND_INTRODUCE1 (client's point of view) cell
def set_up_intro_point(base_circuit, introduction_point_router, rendezvous_point_router, hidden_service, rendezvous_cookie):
    def cb(response, intro_circuit):
        # We have a new `intro_circuit` for accessing the introduction point (2 nodes; guard and introduction point)
        original_circuit = base_circuit  # The original circuit of which to add the rendezvous point (3 nodes now, will soon be 4)
        introduction_point = intro_circuit.last_node  # Introduction point (approved by the hidden service)
        # We have a `rendezvous_point_router` passed as parameter (picked at our/client's convenience)

        # For INTRODUCE1 we must use the last type of Tor key agreement: a TAP handshake
        introduction_point = CircuitNode(introduction_point.router, key_agreement_cls=TapKeyAgreement)

        # Section 5.1.3 of the Tor Protocol Specification
        #     The "TAP" handshake
        # This handshake uses Diffie-Hellman in Z_p and RSA to compute a set of
        # shared keys which the client knows are shared only with a particular
        # server, and the server knows are shared with whomever sent the
        # original handshake (or with nobody at all).  It's not very fast and
        # not very good.  (See Goldberg's "On the Security of the Tor
        # Authentication Protocol".)
        #
        # You are to fill in the first portion with the DH operations, and the
        # (legacy) hybrid encryption portion will be handled for you.

        x = dh_private()  # Client's private key, x
        X = dh_public(x)  # Client's public key, X = g^x

        X_bytes = dh_public_to_bytes(X)

        # Send (INTRODUCE1) CellRelayIntroduce1 cell and expect a CellRelayIntroduceAck cell response
        # Section 1.8+ in the Tor Rendezvous Specification (the v3 intro protocol)
        introduce_cell = CellRelayIntroduce1(
            #your-code-here#,
            #your-code-here#,
            #your-code-here#,
            #your-code-here#,
            hidden_service.auth_type,
            hidden_service.descriptor_cookie,
            #your-code-here#
        )
        cell_acknowledgement =  #your-code-here#
        logger.info('Introduced (%r)', cell_acknowledgement)

        rendezvous2_cell = response.get()

        handshake_response = rendezvous2_cell.handshake_data
        auth = handshake_response[128:]  # Derivative key data (as in Sections 5.1.3 and 5.2)
        Y_bytes = handshake_response[:128]  # Client's public key, g^y = Y, in bytes

        HASH_LEN =  #your-code-here#
        if len(auth) != HASH_LEN:  # Should be HASH_LEN bytes according to the spec.
            raise KeyAgreementError('Received wrong length SHA1 digest.')

        Y = dh_public_from_bytes(Y_bytes)  # Y = g^y

        shared_secret =  #your-code-here#

        computed_auth, key_material =  #your-code-here#  # Referenced in 5.1.3 & 5.2.1

        if computed_auth != auth:
            raise KeyAgreementError('Auth input does not match.')

        shared_secret_key = key_material[:KeyAgreement.KEY_MATERIAL_LENGTH]  # Cut unused bytes

        introduction_point.store_key(shared_secret_key)

        return introduction_point

    return IntroductionPoint(introduction_point_router, base_circuit).connect(hidden_service, rendezvous_cookie, callback=cb)


# Sends a RELAY_COMMAND_ESTABLISH_RENDEZVOUS cell
def extend_to_hidden(circuit, hidden_service):
    circuit.associated_hs = hidden_service

    # Section 1.7 in the Tor Rendezvous Specification
    # Send CellRelayEstablishRendezvous and expect CellRelayRendezvousEstablished
    rendezvous_cookie =  #your-code-here#
    establish_cell =  #your-code-here#
    cell_established =  #your-code-here#
    logger.info('Rendezvous established (%r)', cell_established)

    # Pick a hidden service directory to look up possible introduction point
    hs_directory_generator =  #your-code-here#
    hs_directory =  #your-code-here#

    # Pick an introduction point (router object) to the hidden service
    introduction_router_generator =  #your-code-here#
    introduction_point_router =  #your-code-here#

    # And then also pick a rendezvous point of which to proceed with server requests/communications
    convenient_rendezvous_points = circuit.get_circuit_nodes()
    rendezvous_point_router =  #your-code-here#

    # Set up an introduction point for the hidden service
    introduction_point =  #your-code-here#

    # Add the introduction point as the next hop in the circuit
    circuit.circuit_nodes.append(introduction_point)


def get(hs_name, port=80, path="", live=False):
    request_template = b'GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n'
    tor = TorClient(use_local_directories=(not live))
    with tor.create_circuit(3) as circuit:
        request = request_template % (path.encode(), hs_name.encode())

        # Create a new stream attached to our usual (3-hop) circuit.
        # Parse (prepare) the hidden service's hostname and port
        # and save its info in a HiddenService object.
        tor_stream =  #your-code-here#
        hidden_service, address =  #your-code-here#

        # Extend the typical 3-hop circuit to have a fourth (introduction
        # point) node that is also one accessible by the hidden service.
        logger.info('Extending #%x circuit for hidden service %s', circuit.id, hidden_service.hostname)
        #your-code-here#

        # Open the stream to the hidden service's onion address
        logger.info('Stream #%i: connecting to %r', tor_stream.id, address)
        #your-code-here#

        with tor_stream as stream:
            # Send a GET request through the Tor stream
            # as if it were an ordinary HTTP connection.
            stream.send(request)
            recv = b""
            while stream.state == StreamState.Connected:
                recv = recv + stream.recv(1024)
            return recv.decode('utf-8')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--url', help='url', required=True)
    parser.add_argument('--mode', default='random')
    parser.add_argument('--outfile', default="", type=str, help='output file path')
    parser.add_argument('--live', action='store_true', help='connect to the real Tor network')
    args = parser.parse_args()
    url = urlparse(args.url)

    response = get(url.hostname, url.port or 80, url.path, args.live)

    # Write response to args.outfile or stdout
    if args.outfile == "":
        print('response', response)
    else:
        outfile = open(args.outfile, "w")
        outfile.write(response)
        outfile.close()
