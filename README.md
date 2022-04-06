# Tor Assignment
Due: April 25th, 2022 @ 9PM Eastern

Team Size: 2 Students Per Team

## Assignment Overview
In this assignment you are going to get an in-depth view on Tor. You are going to be writing the client logic to build circuits and implement the required logic to build hidden services.

## Resources

### Tor
 - [Overview of Hidden Services](https://2019.www.torproject.org/docs/onion-services)
 - [Tor Protocol Specification](https://gitweb.torproject.org/torspec.git/plain/tor-spec.txt)
 - [Tor Rendezvous Specification](https://gitweb.torproject.org/torspec.git/plain/rend-spec-v2.txt)
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
docker run -p 5000-5005:5000-5005 -p 7000-7005:7000-7005 -it gkaptchuk/cs558tor22 bash
```

It will download an Alpine Linux Docker image with Tor Chutney and Nyx installed on it, and then instantiate it in interactive mode with the onion routing ports mapped to your host network.  Chutney is already configured with 3 directory authorities, 3 guard and middle nodes, and 3 exit nodes.  This test net is quite small, so be sure not to accidentally route through the same node twice, or you will fail a handshake.

Be aware, that on macOS, you may find that one of these ports is already in use.  You can free up this port by turning off AirPlay Receiver in your system preferences

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

In this task you are going to be implementing the client side logic to get this all working. We have provided you skeleton code in `telescoping_circuit.py`. There a bunch of helper functions that will help you abstractions away some of the trickier parts (eg. the detail of the actual crypto).

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

### Connecting to a Hidden Service (40 pts)
Now that you can make circuits, we are going to use them to build connections to Tor hidden services in our virtual Tor network.  First, take the web server program we give you in a docker.  This is going to be the hidden service server, and when you run `./start.sh` it will start accepting requests send to its address: `http://erppk6uy6eaxjbnx.onion`.  The rest of the network is set up the same as the previous part.  Note there is an added `-hs` in `cs558tor22-hs` in the command for the network with a hidden service.

```shell
docker run -p 5000-5005:5000-5005 -p 7000-7005:7000-7005 -it gkaptchuk/cs558tor22-hs bash
```

To connect to our hidden service, you will need to do 4 things:

- Take an already built 3-hop circuit (like you made in part 1) and connect a TCP stream
- Find out which nodes are designated as introduction points for the hidden service
- Implement the TAP handshake and use it at an introduction point to agree upon a rendezvous point
- Have the client connect the rendezvous point through the extended circuit and request a web page from the hidden service

We have set up all the hidden service code, so it will be ready to go.  All you have to do is fill in the appropriate functions in the ```hidden_service.py``` file.  Note that all the code for this part is separate from the code from the part above — you don't need to re-use any code, and you may even begin part 2 before finishing part 1 if you'd like.  You should fill in code for

```python
def get(hs_name, port, path, live)

def extend_to_hidden(circuit, hidden_service)

def set_up_intro_point(base_circuit, introduction_point_router, rendezvous_point_router, hidden_service, rendezvous_cookie)
```

<!--These functions will be called automatically when you run the ```hidden_service.py ``` — don't worry about how the code gets called (its called from within the TorClient provided by Torpy).  Theres a comment in the code:

```python
#
#  --- Part I functionalities ---
#  (You can ignore from here on.)
#
```

Everything after that deals with running the client and it will automatically call the code you provide in the two functions for which you need to add code.  As it notes, you can basically ignore all that stuff.-->


In the third function, you are interacting with the introduction point.  Follow the comments in the code and look at the spec (both the full and rendezvous versions) to understand that process.<!--  This first function is a helper for the second to actually connect to the hidden service.-->

You can test you code by directing the client to erppk6uy6eaxjbnx.onion:

```shell
python hidden_service.py --mode random --url http://erppk6uy6eaxjbnx.onion --outfile filename.txt
```

### Point your code at live Tor (10 pts)

All the code that you have written in this assignment is real Tor code -- it will work with real Tor!  To celebrate that, you will actually be pointing your code at live Tor.  To do you, you can either generate a specific circuit through live Tor, or just get the consensus from live Tor.

For this second option, just query `http://127.0.0.1:7001/tor/status-vote/current/consensus/` in `curl` or any web browser.  IPs with ports 7000-7002 on our virtual network are the directory authorities who form the official consensus.  You can find a copy of the real consensus at `http://128.31.0.34:9131/tor/status-vote/current/consensus` which is the Tor authority managed by MIT.  TorPy handles this all automatically.  Take a quick look, but don't worry about handling this document in your code.

To go live, either pass the `--live` flag to `hidden_service.py`, or pass the parameter `use_local_directories=True` to the `TorClient` constructor in `telescoping_circuit.py`.

First, use ```telescoping_circuit.py``` to connect to example.com through the real network.  To get an idea of the overhead, please time how long it takes to get a response (see the ```time``` utility).  Please send us in a zip your logs for the 10 runs and the timing information you collected.  Please include the log for the i^th run in a file called ```log_i.log``` (eg. ```log_7.log```) and the timing information in a file ```time_i.txt``` (eg. ```time_7.txt```)

Either modify `telescoping_circuit.py`, or run it repeatedly to generate 10 or more circuits to `example.com` on the live Tor network.  Be sure to save your log.

Finally, use your code in `hidden_service.py` to request `http://expyuzz4wqqyqhjn.onion` 10 times, and save the response html and header content into a file.  Also, as before, time the interaction to see how long it took.  Please send us in a zip (1) your logs, (2) the html response you get back each time, and (3) the timing information you collected.  Please include the log for the i^th run in a file called ```log_i.log``` (eg. ```log_7.log```), the timing information in a file ```time_i.txt``` (eg. ```time_7.txt```), and the response you get as ```response_i.html``` (eg. ```response_7.html```)


## Deliverables, Checklist

### Task 1

* PDF file with anwsers to the review questions.

### Task 2

* Python script ```telescoping_circuit.py```

* Brief writeup explaining your code (no more than 200 words)

### Tasks 3

* Python script ```hidden_service.py```

* Brief writeup explaining your code (no more than 200 words)

### Tasks 4

* Zip drive containing your files for connecting to `example.com`

* Zip drive containing your files for connecting to `http://expyuzz4wqqyqhjn.onion`
