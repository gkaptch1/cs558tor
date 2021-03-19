# Tor Assignment
Due: April 7, 2021 @ 9PM Eastern

Team Size: 2 Students Per Team

## Assignment Overview
In this assignment you are going to get an in-depth view on Tor. You are going to be writing the client logic to build circuits and implement the required logic to build hidden services. Because engineering

## Resources

### Tor
 - [Overview of Hidden Services](https://2019.www.torproject.org/docs/onion-services)
 - [Tor Protocol Specification](https://gitweb.torproject.org/torspec.git/plain/tor-spec.txt)
 - [TorPy Documentation](https://pypi.org/project/torpy)
### Docker
 - [Docker Documentation](https://docs.docker.com/get-started/overview/)
 - [Docker Cheat Sheet](https://github.com/wsargent/docker-cheat-sheet)
 - [Another Docker Cheat Sheet](https://www.docker.com/sites/default/files/d8/2019-09/docker-cheat-sheet.pdf)

## Setup
We will provide you with a virtual Tor network so that you can test your code and get it working. We will also be using this virtual Tor environment to do our autograding. To get started, clone the repository as `git clone https://github.com/gkaptch1/cs558tor`
to get all the starter code. Then, run a copy of the virtual Tor network with the following commands:

```shell
# Make sure Docker is running and ...
docker run -p 5000-5005:5000-5005 -p 7000-7005:7000-7005 -it wyatthowe/chutney bash
```

It will download an Alpine Linux Docker image with Tor Chutney and Nyx installed on it, and then instantiate it in interactive mode with the onion routing ports mapped to your host network.  Chutney is already configured with 3 directory authorities, 3 guard and middle nodes, and 3 exit nodes.  This test net is quite small, so be sure not to accidentally route through the same node twice, or you will fail a handshake.

The client code you are going to be running is in Python.
I suggest you set up a [virtual environment](https://docs.python.org/3/tutorial/venv.html) in order to test everything.
Everything in this assignment will be for [Python 3](https://pythonclock.org/).
You are going to need the following packages: cffi and cryptography.
They can be installed as follows:

```shell
# Python Tor client dependencies
pip install cffi cryptography  # Make sure you have these two libraries installed.
```

At this point you should be ready to start playing with your code.

Note: The first time you connect, it may take up to 10 seconds to download the Tor consensus (table of routers) from the 3 nodes serving as directory authorities.  You can watch this full process being logged within Nyx.

<!--We have noticed that occasionally there might be problems with the system properly configuring the ability to talk to the virtual environments. Below are some commands that will likely be helpful.

```shell
# Consensus troubleshooting
# After a minute the local Tor network should have arrived at a consensus about the list of nodes
docker-compose scale relay=5 exit=3
docker-compose up -d client

# You should be able to check that forwarding works by hitting the local proxy
curl --socks5 127.0.0.1:9050 ifconfig.me

# Restart Tor network
docker-compose kill; docker-compose rm -fsv
docker-compose up -d

# Print the list of nodes
python ./util/get_consensus.py
```-->

## Tasks
### Review Questions (10 pts)
In your own words, what is the difference between data and metadata? What metadata do TLS and encrypted email leak? Give us an imagined scenario for each of these protocols where this information leakages could have serious ramifications.

List and explain 2 benefits of using three nodes in a Tor circuit rather than simply using a single proxy server.

### Setting up a Tor Circuit (40 pts)
Recall from class that Tor creates circuits in a telescoping fashion: first the client creates a connection with the guard node using the CREATE cell, then proxies through the guard node to connect to the middle node with an EXTEND cell, and then finally proxies through both to connect to the exit node with an EXTEND cell. From there, it can initiate a TCP connection on the far side of the circuit using the BEGIN cell. Finally, the client can start sending traffic to the server using the RELAY cell.

In this task you are going to be implementing the client side logic to get this all working. We have provided you skeleton code in telescoping_circuit.py. There a bunch of helper functions that will help you abstractions away some of the trickier parts (eg. the detail of the actual crypto).

Concretely, you are expected to make your code do the following things:

 - Create a circuit through the virtual Tor network using the CREATE cell and two EXTEND cells
 - Open a new TCP stream using the BEGIN cell
 - Send an HTTP GET to a url which specified as command line parameter
 - Dump the HTML that you get in return to a file (name supplied on the command line)

You should be looking to fill in the contents of the following functions:

```python
def get(*url, **optional_addresses)

def circuit_from_guard(guard_router, circuit_id)

def circuit_build_hops(circuit, middle_router, exit_router)

def extend(circuit, node_router)
```

We would like your code to be runnable in two modes: in the RANDOM mode, it should generate a random circuit from the list of nodes extracted from the directory service. In the SPECIFIC mode, we should be able to give you a list of 3 node identifiers on the command line, and your code should open a circuit through those specific nodes.

We will run your code with the following interfaces

```shell
python telescoping_circuit.py --mode random --url http://example.com --outfile filename.txt
```

```shell
python telescoping_circuit.py --mode specific --guard 127.0.0.1:7001 --middle 127.0.0.1:7002 --exit 127.0.0.1:7003 --url http://example.com --outfile filename.txt
```

For _specific_ mode, we will ensure that we are passing IP addresses that are valid nodes in the virtual network.

### Setting up a Hidden Service (40 pts)
We are currently only releasing the first half of this assignment. We will edit this file to include instructions for part 2 at the beginning of next week.

### Point your code at live Tor (10 pts)
We are currently only releasing the first half of this assignment. We will edit this file to include instructions for part 2 at the beginning of next week.

## Deliverables, Checklist
### Task 1
 - PDF file with answers to the review questions.
### Task 2
 - Python script `telescoping_circuit.py`
 - Brief writeup explaining your code (no more than 200 words)

### Tasks 3 and 4
Coming Soon