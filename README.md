#### TM-Manifesting API guide

tm-manifesting (available in L4TM as a deb package) is developed on L4TM systems
for use in The Machine environment. Support for any other distro, even Debian or 
HPE Linux, is optional and discretionary.

---
#### MANIFESTING: THE MACHINE CONFIGURATION FILE (/etc/tmconfig)

TMCF (The Machine Configuration File) is the large JSON file that completely
describes the topology of an instance of The Machine.  Every instance needs
its own custom file.  Creation of that file is outside the scope of
manifesting.

TMCF is needed for most of the setup steps listed below.  You also need
TMCF to actually run the API server "manifest_api.py".   When you get your
file you should save it in the default location /etc/tmconfig.  Note:
the Librarian also uses this file.

---
#### MANIFESTING SETUP: MANIFESTING CONFIGURATION FILE (/etc/tmms)

The sample manifesting configuration file supplied with the repo is "tmms".
Yes, it is Python syntax. The default config installed with the package does
not provide booting of the node copabilities, BUT, still allowes you to use
API full functionality. This is due to unknown networking state of the each
individual system (e.g. NIC and TMDOMAIN).

Instructions on configuring your netwrok will be provided bellow.

---
#### MANIFESTING SETUP and Configuration

###### Prerequisite: L4TM system

##### Package install

To install manifesting:

```bash
sudo apt update
sudo apt install tm-manifesting
```

As part of the package install process, it will create the following for you to
use:
```bash
tm-manifest
tm-manifest-server
```

_Note: ManPage also available for each of the tools to read_
```bash
man tm-manifest
man tm-manifest-server
```

NOTE: we are not done yet configuring the API. Read next "Configuration: SETUP".

---

##### Configuration: _SETUP_

###### Prerequisite: /etc/tmconfig
Obtain a copy of TMCF for your TM instance and put it at /etc/tmconfig

An easy way is through the librarian.  Copy these lines to "fame40.ini":
```
[global]
node_count = 40
book_size_bytes = 8M
nvm_size_per_node = 512B
```

Then run
```bash
book_register.py -j fame40.ini > /tmp/tmconfig
sudo mv /tmp/tmconfig /etc/tmconfig
```
---

Next, we need to configure your system before you can start tm-manifest-server.
Though, this can be done with one command that runs through all the setup
phases, you can manually run each of them separatly (discussed below):
```bash
tm-manifest setup
```

By default (no arguments), or specifying "all", setup will start the
first of several phases of setup, and proceed through all of them.  That
is the recommended invocation.

You may see some package installation output from apt-get depending on
the packages currently on your system.

The configuration file chosen will be display, then a summary of
operations performed.

Hopefully all error messages are clear on the nature of any problem(s)
and suggestive as to a remedy.  Most of them will refer to a problem
in the values you store in /etc/tmms.  You should be familiar with the
keys and values in that file so you recognized them in error messages.

For example, the error message

PXE_INTERFACE: no such interface "net_accessP"

means you need to set PXE_INTERFACE to the NIC which is actually connected
to your nodes.  No, all permutations of error messages will not be listed.
If you get confused, ask for help.

---

##### Configuration: _SETUP ENVIRONMENT_

This is the first phase of "tm-manifest setup all".   It may be explicitly 
invoked via:
```bash
sudo tm-manifest setup environment
```

It creates the overall directory structure needed to support other
configuration steps.  If this phase is not done first, the other phases
will most likely fail.

---

##### Configuration: _SETUP NETWORKING_

Networking phase configures the DHCP\TFTP server, dnsmasq, firewalls and etc.
It can be manually invoked via:

```bash
sudo tm-manifest setup networking
```

Error messages are intended to be suggestive of their own remedy.

---

##### Configuration: _SETUP GOLDEN IMAGE__

The finally step of the setup process is generating a golden image. It should
happen automatically if you did "setup.py all", or you can invoke only this
stage with:

```bash
sudo tm-manifest setup golden_image
```

This will take about twenty minutes, as the tasks involve building a
file system under QEMU-static control (for aarch64).  Be patient.

---
#### Starting the Server

When all the configurations are finished successully, you should be able to
start an API server.

To start is in a foreground mode:
```bash
sudo tm-manifest-server
```
To start it as a daemon:
```bash
sudo tm-manifest-server -D
```
To Stop the server:
```bash
sudo tm-manifest-server --daemon-stop
```

For more options to control the daemon:
```bash
sudo tm-manifest-server --help
```

---

#### Configuring manifesting to boot nodes in a FAME environment

To get this working, read [this documentation](https://github.hpe.com/hpelinux/manifesting/blob/master/unittests/QAscripts/1stREADME)
