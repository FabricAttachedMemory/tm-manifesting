#!/usr/bin/python3 -tt
"""
    Create TFTP environment for nodes to pick up custom FS images.
This script generates node-specific the grub menu files plus a single master
grub.cfg.  It also generates config files for the PXE server "dnsmasq".

Details: SFW constructs a ClientID based on the node's physical coordinates.
That ClientID is passed in a DHCP request.  The DHCP server (dnsmasq) looks
up an IP address and hostname based on ClientID.  The DHCP response also
includes a TFTP server (also dnsmasq) from which to obtain a boot loader.

SFW downloads (via TFTP) a single file, the bootloader which is "grub".
Grub turns around and TFTPs the master grub.cfg file common to all nodes.
grub.cfg evaluates the hostname of the running node to choose a menu file.
That menu specifies the precise kernel file (vmlinuz) and customized FS image
(.cpio file) for the node.
"""
__author__ = "Zakhar Volchak, Rocky Craig"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Zakhar Volchak, Rocky Craig"
__email__ = "zach.bender@tutanota.com, rocky.craig@hpe.com"


import argparse
import os
import requests as HTTP_REQUESTS
import sys
import time

import dns.resolver as RES
from netaddr import IPNetwork, iter_iprange, IPAddress
import netifaces as NIF

from pdb import set_trace

from tm_librarian.tmconfig import TMConfig

# Imports are relative to parent directory with setup.py because implicit
# Python path "tmms" may not exist yet.

from configs.build_config import ManifestingConfiguration
from utils.utils import basepath, piper, setDhcpClientId
from utils.file_utils import make_symlink, make_dir

###########################################################################
# Templates for config files

# /boot/grub.cfg ----------------------------------------------------------
# bootnetaa64.efi is compiled with most modules, such as all_video.   A few
# (like videoinfo) might be needed, so the modules directory will be supplied.
# Sometimes the EFI network is 0, sometimes 1, and I can't get
# inline variable substitution to work.  Take the easy way out,
# one of them will fire.

_grub_cfg_template = '''
# Command/data prefix is (tftp)/grub; module prefix is (tftp)/grub/arm64-efi
# so "insmod videoinfo" just works.  Both TMAS and FAME have a countdown
# multiplier of about ten, but since we're on real hardware now...
# timeout doesn't seem to work here, see the menu template.
# set timeout=10

set gfxmode=auto
set gfxmodepayload=text
set linux_gfx_mode=text

# Fails on TMAS, no video modes per "videoinfo"
terminal_output gfxterm
background_image "(tftp)/grub/manifest.jpg"

# Originally for SNBU but worth keeping
set debug=linux,linuxefi,efi
set pager=1

configfile  "(tftp){menudir}/${{net_efinet0_hostname}}.menu"
configfile  "(tftp){menudir}/${{net_efinet1_hostname}}.menu"
'''

# /grub/menus/nodeXX.menu -------------------------------------------------
# First cut was "root=/dev/ram0" but that invokes (old, inflexible) ramfs
# behavior.  "mount" claims that / is type rootfs (a special kind of tmpfs)
# but "df /" is nothing but zeroes.  From 2013:
# https://lwn/net/Articles/559176/ says don't specify root= but DO specify
# rootfstype=tmpfs (assumes CONFIG_TMPFS). df is now happy, although mount
# claims / is type rootfs.  As it turns out, specifying neither root= or
# rootfstype= works just fine.

_grub_menu_template = '''
set default=0
set menu_color_highlight=white/brown

# FAME and TMAS jack this X10.  The global in grub.cfg should work, but if not, uncomment this.
set timeout=8

# Originally for SNBU but worth keeping
set debug=linux,linuxefi,efi
set pager=1

menuentry '{hostname} L4TM ARM64' {{
    linux (tftp){images_dir}/{hostname}.vmlinuz.gz {append}
    initrd (tftp){images_dir}/{hostname}.cpio.gz
}}
'''

# .../dnsmasq/<INTERFACE>.conf and more -----------------------------------
# Main grub.cfg template was started from a libvirt NAT setup.  See also
# https://github.com/ussjoin/piglet/blob/master/config/dnsmasq.conf
# dnsmasq --help dhcp

_dnsmasq_conf_template = '''{timestamp}

pid-file={dnsmasq_pidfile}
log-facility={dnsmasq_logfile}
# log-dhcp

bind-interfaces
interface={pxe_interface}
except-interface=lo
local-service

# resolv.conf handling
# resolv-file=
# no-poll
# strict-order
all-servers

domain={tmdomain}
clear-on-reload
# never forward simple names
domain-needed
# srv-host=_librarian._tcp,torms,9093
selfmx

dhcp-leasefile={dnsmasq_prepath}.leases
dhcp-script=/bin/echo		# "add|del" MAC IP hostname
dhcp-range={first_addr},static   # sets IPV4 mode, but only from hostsfile
dhcp-match=TMAS-EFI,option:client-arch,11		# EFI
dhcp-hostsfile={dnsmasq_hostsfile}
addn-hosts={dnsmasq_dnslookupfile}
dhcp-no-override
dhcp-boot=/grub/grubnetaa64.efi
# 512-byte blocks.  TM SFW does ask but it's not sent by default.
dhcp-option-force=option:boot-file-size,{boot_file_size_512_blocks}

# Routing.  Default for FAME and most TMAS is to let dnsmasq supply the
# default route of its host.  Real TM nodes are connected to a separate
# firewall that also provides the gateway.  "setup networking" will look 
# that up and supply the real value.
{dnsmasq_defaultroute}

enable-tftp
tftp-root={tftp_root}
'''

# /var/lib/tmms/dnsmasq/<PXE_INTERFACE>.iptables --------------------------
# Created libvirt networks of forward=route with DHCP to get FW rules to
# isolate DHCP on the given network.

_iptables_template = '''{timestamp}
-t mangle -{{action}} POSTROUTING -o {pxe_interface} -p udp -m udp --dport 68 -j CHECKSUM --checksum-fill
-t filter -{{action}} INPUT -i {pxe_interface} -p udp -m udp --dport 53 -j ACCEPT
-t filter -{{action}} INPUT -i {pxe_interface} -p tcp -m tcp --dport 53 -j ACCEPT
-t filter -{{action}} INPUT -i {pxe_interface} -p udp -m udp --dport 67 -j ACCEPT
-t filter -{{action}} INPUT -i {pxe_interface} -p tcp -m tcp --dport 67 -j ACCEPT
-t filter -{{action}} FORWARD -d {network} -o {pxe_interface} -j ACCEPT
-t filter -{{action}} FORWARD -s {network} -i {pxe_interface} -j ACCEPT
-t filter -{{action}} FORWARD -i {pxe_interface} -o {pxe_interface} -j ACCEPT
-t filter -{{action}} FORWARD -o {pxe_interface} -j REJECT --reject-with icmp-port-unreachable
-t filter -{{action}} FORWARD -i {pxe_interface} -j REJECT --reject-with icmp-port-unreachable
-t filter -{{action}} OUTPUT -o {pxe_interface} -p udp -m udp --dport 68 -j ACCEPT
'''

#--------------------------------------------------------------------------


class TMgrub(object):
    """
        Generate all grub grub config files under the TFTP hierarchy.
        At "tftp" element of hierarchy (default /var/lib/tmms/tftp):
        - grub/
          grubnetaa64.efi
          grub.cfg
          - menus/
            node01.menu thru node40.menu
        -images/
          - nodeXX/ (directories)
            nodeXX.vmlinuz and nodeXX.cpio
    """

    def __init__(self, manconfig):
        """
        :param 'manconfig': dictionary with many ratified paths and other data
        """
        # Fields are used in template interpolation and file writing.  Some
        # are directly copied from manconfig, others are calculated.

        self.user = os.getlogin()
        self.timestamp = '# Auto-generated on %s; DO NOT MODIFY!' % (
            time.ctime())
        self.tmconfig = TMConfig(manconfig['TMCONFIG'])
        if self.tmconfig.errors:
            raise SystemExit('%s has errors:\n%s' % (
                manconfig['TMCONFIG'], '\n'.join(self.tmconfig.errors)))
        if self.tmconfig.FTFY:
            print('!!! %s has these annoyances (defaults were used):\n%s' % (
                manconfig['TMCONFIG'], '\n'.join(self.tmconfig.FTFY)))

        for node in self.tmconfig.allNodes:
            setDhcpClientId(node)

        # Begin movement of /etc/tmms values to /etc/tmconfig.
        TMDOMAIN = None
        tmcfDomains = getattr(self.tmconfig, 'domains', None)
        if tmcfDomains:
            TMDOMAIN = getattr(tmcfDomains, 'publicData', None)
            if TMDOMAIN:
                manconfig['TMDOMAIN'] = TMDOMAIN
        assert 'TMDOMAIN' in manconfig, 'Missing DNS domain'

        # Absolute paths are for writing files.  tftp_xxxx are file contents.
        # manconfig dirs were already created by "setup.py environment".
        self.tftp_images_dir = manconfig['TFTP_IMAGES']
        self.tftp_grub_dir = manconfig['TFTP_GRUB']
        self.tftp_grub_menus_dir = self.tftp_grub_dir + '/menus'
        make_dir(self.tftp_grub_menus_dir)
        make_symlink(   # Present all EFI modules to grub for "insmod"
            '/usr/lib/grub/arm64-efi', self.tftp_grub_dir + '/arm64-efi')

        self.tftp_grub_cfg = self.tftp_grub_dir + '/grub.cfg'
        self.tftp_grub_efi = self.tftp_grub_dir + '/grubnetaa64.efi'

        # SDHC images need a different GRUB because the memdisk core code
        # is different from grubnetaa64.efi.  Stick it in TFTP dir for
        # convenience and continuity but it will never be used by PXE.
        self.sdhc_grub_efi = self.tftp_grub_dir + '/grubaa64.efi'

        self.dnsmasq_configs = manconfig['DNSMASQ_CONFIGS']
        self.dnsmasq_logfile = manconfig['DNSMASQ_LOGFILE']
        self.dnsmasq_pidfile = manconfig['DNSMASQ_PIDFILE']
        self.dnsmasq_prepath = manconfig['DNSMASQ_PREPATH']
        self.dnsmasq_hostsfile = self.dnsmasq_prepath + '.hostsfile'
        self.dnsmasq_dnslookupfile = self.dnsmasq_prepath + '.dnslookup'
        self.dnsmasq_defaultroute = '# dhcp-option=option:router,1.2.3.4'
        self.pxe_interface = manconfig['PXE_INTERFACE']
        self.tmdomain = manconfig['TMDOMAIN']

        if 'PXE_SUBNET' not in manconfig:
            self.pxe_subnet = None
        else:
            self.pxe_subnet = manconfig['PXE_SUBNET']
            if self.pxe_subnet.lower() == 'none':
                self.pxe_subnet = None

        # Relative to TFTP, these supply content to the files.
        self.tftp_root = manconfig['TFTP_ROOT']
        self.chroot_images_dir = basepath(self.tftp_images_dir, self.tftp_root)
        self.chroot_grub_dir = basepath(self.tftp_grub_dir, self.tftp_root)
        self.chroot_grub_menus_dir = basepath(
            self.tftp_grub_menus_dir, self.tftp_root)

        # These files are also in the Debian package "grub-efi-arm64-signed"
        # (w/ appropriate revision) but Linn Crosetto keeps them here.
        # The grub-mkimage command is in the source deb under build/xxxx

        for dest in (self.tftp_grub_efi, self.sdhc_grub_efi):
            base = os.path.basename(dest)
            grubURL = manconfig['L4TM_MIRROR'] + \
                '/dists/catapult/main/uefi/grub2-arm64/' +\
                'current/%s.signed' % base
            try:
                r = HTTP_REQUESTS.get(grubURL)
                assert r.status_code == 200, 'Cannot retrieve "%s"' % grubURL
                assert len(r.content) == int(r.headers['Content-Length']), \
                    'Length mismatch on "%s"' % grubURL
            except Exception as e:
                raise SystemExit(str(e))
            with open(dest, 'wb') as f:
                f.write(r.content)

    @property
    def hostnames(self):
        return list([node.hostname for node in self.tmconfig.allNodes])

    def evaluate_TMDOMAIN(self):
        '''
        manifest_config.py TTMDOMAIN variable has simple form like
           TMDOMAIN = 'have.it.your.way'
        By decree of the LATC, TMCF contains no MAC or IP addresses,
        only hostnames.  There is only hostname to IP address binding.
        The authoritative source for that is DNS, as set up by HPE site IT,
        since all instances of The Machine will always be connected to
        HPE site LAN.  Thus given the domain name, each host IP can be
        resolved by DNS.  40 nodes plus "torms" must be available in DNS.

        In case DNS is not prepped properly :-) or a FAME environment there's
        one more variable of interest: PXE_SUBNET.  It has two variants:
        1) None: it's all in DNS through TMDOMAIN (came from TMCF)
        2) ipaddr/bits: PXE_SUBNET = '10.11.10.42/24'
           grab 40 IPs @ ipaddr
           netmask from bits
           if ipaddr is the network zero address, first address is x.y.z.1

           Each case has its own method to calculate a network CIDR.
           "torms" will be set to the last legal IP address (ie, 254 in
           a class C network).
        '''

        self.hostIPs = []
        noDNS = []
        if self.pxe_subnet is None:         # DNS lookup for all nodes
            for node in self.tmconfig.allNodes:
                FQDN = '%s.%s' % (node.hostname, self.tmdomain)
                try:    # dns.resolver is weird, even with raise_on_no_answer
                    answer = RES.query(FQDN, 'A')
                    assert len(answer) == 1, '"%s" has CNAMES' % FQDN
                except (RES.NXDOMAIN, AssertionError) as e:
                    noDNS.append(FQDN)
                    continue
                A = next(iter(answer))
                self.hostIPs.append(A.address)

            # Oh yeah...
            try:
                FQDN = 'torms.' + self.tmdomain
                answer = RES.query(FQDN, 'A')
                assert len(answer) == 1
                self.torms = str(next(iter(answer)).address)
            except (RES.NXDOMAIN, AssertionError) as e:
                noDNS.append(FQDN)
            try:
                FQDN = 'firewall.' + self.tmdomain
                answer = RES.query(FQDN, 'A')
                assert len(answer) == 1
                self.dnsmasq_defaultroute = 'dhcp-option=option:router,%s' % (
                    str(next(iter(answer)).address))
            except (RES.NXDOMAIN, AssertionError) as e:
                # Not fatal
                print('Cannot DNS resolve "%s", manually fix dnsmasq config' %
                    FQDN, file=sys.stderr)

            if noDNS:
                raise SystemExit(
                    'Required FQDN(s) that failed DNS lookup:\n%s' %
                        '\n'.join(noDNS))

            # Since this is Corporate IT, use the known value.
            kludge_network = self.network

        else:   # Synthesize host names and IP addresses
            try:
                assert '/' in self.pxe_subnet, 'CIDR address missing slash'
                kludge_network = IPNetwork(self.pxe_subnet).cidr
                tmp = self.pxe_subnet.split('/')[0]
                if tmp != str(IPAddress(kludge_network.first)):
                    first_addr = IPAddress(tmp)
                else:
                    first_addr = IPAddress(kludge_network.first + 1)
            except Exception as e:
                raise RuntimeError(
                    'PXE_SUBNET: bad CIDR notation: %s' % str(e))

        if self.network is None:
            self.network = kludge_network
        else:
            assert self.network == kludge_network, \
                'Networking mismatch between NIC and TMDOMAIN'
        if not self.hostIPs:    # enumerator properly skips Sun broadcast
            self.hostIPs = [IPAddress(first_addr.value + (node.node_id - 1))
                                for node in self.tmconfig.allNodes]
            assert all(map(lambda a: a in self.network, self.hostIPs)), \
                'Auto-generated IP address extend beyond network'
        self.first_addr = str(self.hostIPs[0])

    def configure_dnsmasq(self):
        # Try to carry on in the face of errors.  dnsmasq may not start but
        # manifest_api should still run.
        self.torms = None
        self.addr = None        # Might become a string
        self.network = None     # WILL become an IPNetwork object
        if self.pxe_interface is None:
            return
        try:
            assert self.pxe_interface in NIF.interfaces(), \
                'PXE_INTERFACE: no such interface "%s"' % self.pxe_interface
            ifaceaddr = NIF.ifaddresses(
                self.pxe_interface).get(NIF.AF_INET, False)
            if ifaceaddr:
                assert len(ifaceaddr) == 1, \
                    'PXE_INTERFACE "%s" has multiple IPs assigned to it' % \
                    self.pxe_interface
                ifaceaddr = ifaceaddr.pop()
                self.addr = ifaceaddr['addr']      # Convenience attrs
                # Check the __doc__ string for this class.  It's AWESOME!
                self.network = IPNetwork(
                    self.addr + '/' + ifaceaddr['netmask'])
                self.torms = str(self.addr)
        except Exception as e:
            print(str(e))

        self.evaluate_TMDOMAIN()

        size = os.stat(self.tftp_grub_efi).st_size
        self.boot_file_size_512_blocks = (size // 512) + 1

        conf = _dnsmasq_conf_template.format(**vars(self))
        with open(self.dnsmasq_prepath + '.conf', 'w') as f:
            f.write(conf)

        # Build parallel lists of node coordinates and FAME MACs for DHCP.
        # AA programs MFW with "rack/enc prefix"; MFW appends EncNum/X/Node/Y.
        # TM SFW will not run under QEMU/FAME.   Fall back to MAC-based
        # assignments (since we own the MACs in this case).  This format
        # will trigger lfs_fuse.py to extract the node_id at invocation.
        self.FAMEMACs = ['52:54:42:%02d:%02d:%02d' % ((node.node_id, ) * 3)
                         for node in self.tmconfig.allNodes]

        self.clientIds = [ n.DhcpClientId for n in self.tmconfig.allNodes ]

        # MAC and ClientID must be on the same line or else dnsmasq bitches
        # about duplicate IPs and skips the second set.
        assert len(self.hostIPs) == len(self.tmconfig.allNodes), \
            'TMDOMAIN form yielded %d IP addresses, not %d' % (
                len(self.hostIPs), len(self.tmconfig.allNodes))

        zipped = zip(self.FAMEMACs,
                     self.clientIds,
                     self.hostIPs,
                     self.hostnames)
        with open(self.dnsmasq_hostsfile, 'w') as f:
            f.write(self.timestamp + '\n')
            f.write('# FAME/QEMU MAC,ClientID,IP address,hostname\n')
            for h in zipped:
                f.write('%s,id:%s,%s,%s\n' % h)

        # Static assignments.  First and foremost torms, but without the rest
        # dnsmasq only resolves running (leased) nodes.
        zipped = zip(self.hostIPs, self.hostnames)
        with open(self.dnsmasq_dnslookupfile, 'w') as f:
            f.write(self.timestamp + '\n\n')
            f.write('%s\ttorms\n' % self.torms)
            for h in zipped:
                f.write('%s\t%s\n' % h)

    def configure_iptables(self):
        '''Create the meat of "iptables -A" or "iptables -D".'''
        tmp = _iptables_template.format(**vars(self))
        with open(self.dnsmasq_prepath + '.iptables', 'w') as f:
            f.write(tmp)

    def create_tftp_environment(self):
        """
            Create subdirectories under TFTP and add grub menu files based on
        node's hostname, which is implicitly the node's physical location.
        These files are static over the lifetime of a machine instance. Then
        create filesystem image directories per these coords for PXE boot
        to pick up on boot .cpio and .vmlinuz.  manifest_api will populate
        those directories when nodes are bound.
        """

        grub_cfg_content = self.compose_grub_cfg()
        with open(self.tftp_grub_cfg, 'w') as file_obj:
            file_obj.write(grub_cfg_content)

        for hostname in self.hostnames:
            tftp_node_fs = self.tftp_images_dir + '/' + hostname
            make_dir(tftp_node_fs)
            grub_menu_content = self.compose_grub_menu(hostname)
            menu_fname = '%s/%s.menu' % (self.tftp_grub_menus_dir, hostname)
            with open(menu_fname, 'w') as file_obj:
                file_obj.write(str(grub_menu_content))

        self.configure_dnsmasq()
        self.configure_iptables()

    def compose_grub_menu(self, hostname):
        """Return grub menu content keyed on hostname."""
        # Node binding places {hostname}.vmlinuz and {hostname}.cpio here
        images_dir = '%s/%s' % (self.chroot_images_dir, hostname)
        return _grub_menu_template.format(
            hostname=hostname,
            images_dir=images_dir,
            append='rw earlycon=pl011,0x402020000 ignore_loglevel'
            )
            # append='rw console=ttyAMA0 acpi=force'    # FAME/TMAS

    def compose_grub_cfg(self):
        """
            Template string for a grub.cfg that references grub menu
        for each node on PXE boot.
        """

        return _grub_cfg_template.format(menudir=self.chroot_grub_menus_dir)


def main(args):
    """
        Configure TFTP environment.
    """
    manconfig = ManifestingConfiguration(args.config, autoratify=False)
    missing = manconfig.ratify(dontcare=('GOLDEN_IMAGE', ))
    if missing:
        raise RuntimeError('\n'.join(missing))

    grubby = TMgrub(manconfig)

    try:
        grubby.create_tftp_environment()
    except OSError as err:
        raise RuntimeError('Failed to create tftp environment! [%s]' % err)

    print('Master GRUB configuration in', grubby.tftp_grub_cfg)
    print('      Per-node grub menus in', grubby.tftp_grub_menus_dir)
    print('      Per-node image dirs in', grubby.tftp_images_dir)
    if grubby.pxe_interface is None:
        print(
            'dnsmasq config has been suppressed. Fix /etc/tmms[PXE_INTERFACE]')
    else:
        print('  dnsmasq/iptables config in %s/%s.*' % (
            grubby.dnsmasq_configs, grubby.pxe_interface))

    # Eventually this message will never be emitted again.

    if any([ node.DhcpClientId != node.coordinate for node in
        grubby.tmconfig.allNodes ]):
        print('\n   NOTE: Redfish has provided some PXE Client IDs')

if __name__ == '__main__':
    # Not worth working around this
    raise SystemExit('Can only be run from top-level setup.py')
