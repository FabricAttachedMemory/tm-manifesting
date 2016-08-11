#!/usr/bin/python3 -tt
"""
    Create TFTP environment for nodes to pick up custom FS images.
Each node must have its on grub menu, kernel (vmlinuz), and FS image (cpio)
under the TFTP server.  This script generates the grub menu files plus
a single master grub.cfg which is originally downloaded by grub.efi.

    Details: A node boots and system firmware (SFW) downloads (via TFTP)
a single file, the bootloader which is grub.efi.  Grub turns around and
grabs its master grub.cfg file.  All nodes will use this same grub.cfg.
grub.cfg content is based on the DHCP "ClientID" option, as opposed to
the traditional MAC address.  The ClientID contains the node's physical
location (enclosure and node number).  This is evaluated by grub to
choose a specific "menu" file.  Grub menu file is generated per each
node and is stored as env#/grub.node# file which represent each known
node coord. That menu specifies the precise kernel file (vmlinuz) and
customized FS image (.cpio file).
"""

import argparse
import os
import requests as HTTP_REQUESTS
import sys
import time

import dns.resolver as RES
from netaddr import IPNetwork, iter_iprange, IPAddress
import netifaces as NIF

from pdb import set_trace

from configs.build_config import ManifestingConfiguration
from utils.utils import make_dir, make_symlink, basepath

from tm_librarian.tmconfig import TMConfig

#--------------------------------------------------------------------------
# Templates for config files

_maxnodes = 40  # Revised FRD for 2016

# bootnetaa64.efi is compiled with most modules, such as all_video.   A few
# (like videoinfo) might be needed, so the modules directory will be supplied.
# Sometimes the EFI network is 0, sometimes 1, and I can't get
# inline variable substitution to work.  Take the easy way out,
# one of them will fire.

_grub_cfg_template = '''
# Command/data prefix is (tftp)/grub; module prefix is (tftp)/grub/arm64-efi
# so "insmod videoinfo" just works.

set gfxmode=auto
set gfxmodepayload=text
set linux_gfx_mode=text

# Fails on TMAS, no video modes per "videoinfo"
terminal_output gfxterm
background_image "(tftp)/grub/manifest.jpg"

configfile  "(tftp){menudir}/${{net_efinet0_hostname}}.menu"
configfile  "(tftp){menudir}/${{net_efinet1_hostname}}.menu"
'''

_grub_menu_template = '''
set default=0
set menu_color_highlight=white/brown
set timeout=10

menuentry '{hostname} L4TM ARM64' {{
    linux (tftp){images_dir}/{hostname}.vmlinuz.gz root=/dev/ram0 console=ttyAMA0 acpi=force rw
    initrd (tftp){images_dir}/{hostname}.cpio.gz
}}
'''

# Main grub.cfg template was started from a libvirt NAT setup.  See also
# https://github.com/ussjoin/piglet/blob/master/config/dnsmasq.conf
# dnsmasq --help dhcp

_dnsmasq_conf_template = '''# Auto-generated by {user} on {timestamp}

pid-file=/var/run/tmms/dnsmasq.{pxe_interface}.pid
log-facility=/var/log/tmms/dnsmasq.{pxe_interface}.log
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

dhcp-leasefile=/var/lib/tmms/dnsmasq/{pxe_interface}.leases
dhcp-script=/bin/echo		# "add|del" MAC IP hostname
dhcp-range={network},static				# netmask computed
dhcp-match=TMAS-EFI,option:client-arch,11		# EFI
dhcp-hostsfile=/var/lib/tmms/dnsmasq/{pxe_interface}.hostsfile
addn-hosts=/var/lib/tmms/dnsmasq/{pxe_interface}.morehosts		# DNS only
dhcp-no-override
dhcp-boot=/grub/grubnetaa64.efi
# 512-byte blocks.  TM SFW does ask but it's not done automatically
dhcp-option-force=option:boot-file-size,{boot_file_size_512_blocks}

enable-tftp
tftp-root={tftp_root}
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

        self.user = os.getlogin()
        self.timestamp = time.ctime()
        self.tmconfig = TMConfig(manconfig['TMCONFIG'])

        # Absolute paths are for writing files.  tftp_xxxx are file contents.
        # Dirs keyed from manconfig were already created.
        self.tftp_images_dir = manconfig['TFTP_IMAGES']
        self.tftp_grub_dir = manconfig['TFTP_GRUB']     # already created
        self.tftp_grub_menus_dir = self.tftp_grub_dir + '/menus'
        make_dir(self.tftp_grub_menus_dir)
        make_symlink(   # Present all EFI modules to grub for "insmod"
            '/usr/lib/grub/arm64-efi', self.tftp_grub_dir + '/arm64-efi')

        self.tftp_grub_cfg = self.tftp_grub_dir + '/grub.cfg'
        self.tftp_grub_efi = self.tftp_grub_dir + '/grubnetaa64.efi'

        self.dnsmasq_dir = manconfig['DNSMASQ_CONFIGS']
        self.pxe_interface = manconfig['PXE_INTERFACE']
        self.tmdomain = manconfig['TMDOMAIN']

        # Relative to TFTP, these supply content to the files.
        self.tftp_root = manconfig['TFTP_ROOT']
        self.chroot_images_dir = basepath(self.tftp_images_dir, self.tftp_root)
        self.chroot_grub_dir = basepath(self.tftp_grub_dir, self.tftp_root)
        self.chroot_grub_menus_dir = basepath(
            self.tftp_grub_menus_dir, self.tftp_root)

        # This file is also in the Debian package "grub-efi-arm64-signed"
        # (w/ appropriate revision) but Linn Crosetto keeps it here.
        # The grub-mkimage command is in the source deb under build/xxxx

        grubURL = manconfig['L4TM_MIRROR'] + \
            '/dists/catapult/main/uefi/grub2-arm64/' +\
            'current/grubnetaa64.efi.signed'
        try:
            r = HTTP_REQUESTS.get(grubURL)
            assert r.status_code == 200, 'Cannot retrieve "%s"' % grubURL
            assert len(r.content) == int(r.headers['Content-Length']), \
                'Length mismatch on "%s"' % grubURL
        except Exception as e:
            raise SystemExit(str(e))
        with open(self.tftp_grub_efi, 'wb') as f:
            f.write(r.content)

    @property
    def hostnames(self):
        return ('node%02d' % n for n in range(1, 41))   # generator

    def evaluate_tmdomain(self, ifaceaddr):
        '''
        manifest_config.py TTMDOMAIN variable has simple form like
           TMDOMAIN = 'have.it.your.way'
        By decree of the LATC, TMCF contains no MAC or IP addresses,
        only hostnames.  There is only hostname to IP address binding.
        The authoritative source for that is DNS, as set up by HPE site IT,
        since all instances of The Machine will always be connected to
        HPE site LAN.  Thus given the domain name, each host IP can be
        resolved by DNS.  40 nodes must be available in DNS.

        In case DNS is not prepped properly :-), one extended element is
        available in the TMDOMAIN data.  It has three variants:
        1) Domain name,ipaddr : grab 40 IP addresses starting at ipaddr
           TMDOMAIN = 'have.it.your.way,192.168.122.111'
        2) Domain name,ipaddr1-ipaddr2 : grab IP addresses in inclusive range
           TMDOMAIN = 'have.it.your.way,192.168.122.111-192.168.122.160'
        3) Domain name,network/bits : grab 40 IPs @ start of network x.y.z.1
           TMDOMAIN = 'have.it.your.way,10.11.10.0/24'

        Only the last has a definitive netmask defined, the other two
        assume class C.
        '''

        elems = self.tmdomain.split(',')
        self.tmdomain = elems.pop(0)

        if not elems:           # No extension == DNS lookup for all nodes
            self.hostIPs = []
            for num in range(1, 41):
                FQDN = 'node%02d.%s' % (num, self.tmdomain)
                try:    # dns.resolver is weird, even with raise_on_no_answer
                    answer = RES.query(FQDN, 'A')
                    assert len(answer) == 1
                except Exception as e:
                    raise RuntimeError('TMDOMAIN: cannot resolve "%s"' % FQDN)
                A = next(iter(answer))
                self.hostIPs.append(A.address)
                pass

            # Oh yeah...
            try:
                FQDN = 'torms.' + self.tmdomain
                answer = RES.query(FQDN, 'A')
                assert len(answer) == 1
                self.torms = next(iter(answer)).address
            except Exception as e:
                raise RuntimeError('TMDOMAIN: cannot resolve "%s"' % FQDN)

            if not ifaceaddr:
                # Kludge.  Since this is Corporate IT, assume the position
                self.netmask = '255.255.240.0'
                tmp = IPAddress(A.address)  # any of them will do
                self.network = str(IPAddress(tmp.value & 0xFFFFF000))
                self.broadcast = str(IPAddress(tmp.value | 0xFFF))

        else:   # Extended element(s) are available
            assert len(elems) == 1, 'Too many CSV fields in TMDOMAIN'
            tmp = elems[0]

            if '/' in tmp:      # CIDR network
                try:
                    network = IPNetwork(tmp)
                except Exception as e:
                    raise RuntimeError(
                        'TMDOMAIN: illegal CIDR notation: %s' % str(e))
                self.network = str(network.network)
                self.netmask = str(network.netmask)
                self.broadcast = str(network.broadcast)
                self.hostIPs = []
                for i, h in enumerate(network.iter_hosts()):  # no broadcasts
                    if i >= _maxnodes:
                        break
                    self.hostIPs.append(str(h))

            elif '-' in tmp:    # Inclusive IP address range
                try:
                    elems = tmp.split('-')
                    iprange = list(
                        iter_iprange(elems[0], elems[1]))[:_maxnodes]
                except Exception as e:
                    raise RuntimeError(
                        'TMDOMAIN: illegal range notation: %s' % str(e))
                assert len(iprange) == _maxnodes, \
                    'TMDOMAIN IP range is not %d addresses' % _maxnodes
                self.hostIPs = [str(h) for h in iprange]
                if not ifaceaddr:
                    # Kludge.  The smallest possible netmask is 6 bits (64)
                    # but if the range crossed boundaries...Assume class C
                    # containment.  iprange_to_cidrs() seems like it ought
                    # to help but it ate my brain.
                    self.netmask = '255.255.255.0'
                    self.network = str(
                        IPAddress(iprange[0].value & 0xFFFFFF00))
                    self.broadcast = str(IPAddress(iprange[0].value | 0xFF))

            else:   # Single IP address
                try:
                    ipaddr = IPAddress(tmp)
                except Exception as e:
                    raise RuntimeError(
                        'TMDOMAIN: illegal IP address notation: %s' % str(e))
                if not ifaceaddr:
                    # See "Kludge" comment above: class C or get more data
                    self.netmask = '255.255.255.0'
                    self.network = str(IPAddress(ipaddr.value & 0xFFFFFF00))
                    self.broadcast = str(IPAddress(ipaddr.value | 0xFF))
                    self.hostIPs = [str(IPAddress(ipaddr.value + i))
                                    for i in range(_maxnodes)]

    def configure_dnsmasq(self):

        # Legal interface? FIXME: move this to build_config
        assert self.pxe_interface in NIF.interfaces(), \
            'PXE_INTERFACE: no such interface "%s"' % self.pxe_interface
        ifaceaddr = NIF.ifaddresses(self.pxe_interface).get(NIF.AF_INET, False)
        if ifaceaddr:
            assert len(ifaceaddr) == 1, \
                'PXE_INTERFACE "%s" has multiple IPs assigned to it' % \
                self.pxe_interface
            ifaceaddr = ifaceaddr.pop()
            self.morehosts = '%s torms' % ifaceaddr['addr']
            self.broadcast = ifaceaddr['broadcast']
            self.netmask = ifaceaddr['netmask']
        else:
            self.morehosts = '# This file left intentionally blank'
            # other fields will be filled in by specific kludges

        self.evaluate_tmdomain(ifaceaddr)

        assert len(self.hostIPs) == _maxnodes, \
            'TMDOMAIN form yielded %d IP addresses, not %d' % (
                len(self.hostIPs), _maxnodes)

        size = os.stat(self.tftp_grub_efi).st_size
        self.boot_file_size_512_blocks = (size // 512) + 1

        conf = _dnsmasq_conf_template.format(**vars(self))

        prepath = '%s/%s' % (self.dnsmasq_dir, self.pxe_interface)

        with open(prepath + '.conf', 'w') as f:
            f.write(conf)

        # AA programs MFW with "rack prefix".  MFW appends EncNum/X/Node/Y.
        # The rack enumerator and "Enclosure" locator are omitted.  Maybe.
        nodefmt = '%s/EncNum/%%d/Node/%%d' % self.tmconfig.racks[0].coordinate
        self.coords = [nodefmt % ((i // 10) + 1, (i % 10) + 1)
                       for i in range(_maxnodes)]
        self.MACs = ['52:54:48:50:45:%02d' % (i + 1)
                       for i in range(_maxnodes)]
        with open(prepath + '.hostsfile', 'w') as f:
            zipped = zip(self.coords, self.hostIPs, self.hostnames)
            for h in zipped:
                f.write('id:%s,%s,%s\n' % h)
            # TM SFW will not run under QEMU/FAME.   Fall back to MAC-based
            # assignments (since we own the MACs in this case).
            f.write('# FAME/QEMU MAC assistance for generic EFI FW\n')
            zipped = zip(self.MACs, self.hostIPs, self.hostnames)
            for h in zipped:
                f.write('%s,%s,%s\n' % h)

        # Static assignments
        with open(prepath + '.morehosts', 'w') as f:
            f.write(self.morehosts)

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

    def compose_grub_menu(self, hostname):
        """Return grub menu content keyed on hostname."""
        # Node binding places {hostname}.vmlinuz and {hostname}.cpio here
        images_dir = '%s/%s' % (self.chroot_images_dir, hostname)
        return _grub_menu_template.format(
            hostname=hostname, images_dir=images_dir)

    def compose_grub_cfg(self):
        """
            Template string for a grub.cfg that references grub menu
        for each node on PXE boot.
        """

        return _grub_cfg_template.format(menudir=self.chroot_grub_menus_dir)


def main(config_file):
    """
        Configure TFTP environment.
    """

    manconfig = ManifestingConfiguration(config_file, autoratify=False)
    missing = manconfig.ratify(dontcare=('GOLDEN_IMAGE', ))
    if missing:
        raise RuntimeError('\n'.join(missing))
    grubby = TMgrub(manconfig)
    grubby.create_tftp_environment()
    print('Master GRUB configuration in', grubby.tftp_grub_cfg)
    print('      Per-node grub menus in', grubby.tftp_grub_menus_dir)
    print('      Per-node image dirs in', grubby.tftp_images_dir)
    print('           dnsmasq config in %s/%s.*' % (
        grubby.dnsmasq_dir, grubby.pxe_interface))


if __name__ == '__main__':
    """ Parse command line arguments. """
    parser = argparse.ArgumentParser(description='Generate GRUB2 config files')
    ManifestingConfiguration.parser_add_config(parser)
    args, _ = parser.parse_known_args(sys.argv[1:])
    print('Using config file', args.config)

    if args.config is None:
        args.config = os.path.realpath(__file__)
        args.config = os.path.dirname(args.config) + '/manifest_config.py'
        print('Using config file', args.config)

    msg = None     # establish scope
    try:
        main(args.config)
    except Exception as e:
        msg = str(e)
    raise SystemExit(msg)
