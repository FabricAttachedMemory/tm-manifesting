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
import sys
import time

import dns.resolver as RES
from netaddr import IPNetwork, iter_iprange, IPAddress
import netifaces as NIF

from pdb import set_trace

from configs.build_config import ManifestingConfiguration
from utils.utils import make_dir, basepath

#--------------------------------------------------------------------------
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
dhcp-boot=/boot/bootaarch64.efi
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
        - boot/
          grub.cfg
          - menus/
            nodeXX.menu (menu files)
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

        # Absolute paths are for writing files.  tftp_xxxx are file contents.
        self.tftp_images_dir = manconfig['TFTP_IMAGES']
        self.tftp_grub_dir = manconfig['TFTP_GRUB']
        self.tftp_grub_menus_dir = self.tftp_grub_dir + '/menus'
        make_dir(self.tftp_grub_menus_dir)

        self.dnsmasq_dir = manconfig['DNSMASQ_CONFIGS']
        self.pxe_interface = manconfig['PXE_INTERFACE']
        self.tmdomain = manconfig['TMDOMAIN']

        # Relative to TFTP, these supply content to the files.
        self.tftp_root = manconfig['TFTP_ROOT']
        self.chroot_images_dir = basepath(self.tftp_images_dir, self.tftp_root)
        self.chroot_grub_dir = basepath(self.tftp_grub_dir, self.tftp_root)
        self.chroot_grub_menus_dir = self.chroot_grub_dir + '/menus'

        # Last but not least, the master grub config file loaded by grub
        # and the EFI executable that reads it
        self.tftp_grub_cfg = self.tftp_grub_dir + '/grub.cfg'
        self.tftp_grub_efi = self.tftp_root + '/boot/bootaarch64.efi'

    @property
    def hostnames(self):
        return ('node%02d' % n for n in range(1, 41))   # generator

    def configure_dnsmasq(self):
        '''Started from a libvirt setup'''

        # Legal interface? FIXME: move this to build_config
        assert self.pxe_interface in NIF.interfaces(), \
            'PXE_INTERFACE: no such interface "%s"' % self.pxe_interface
        ifaceaddr = NIF.ifaddresses(self.pxe_interface).get(NIF.AF_INET, False)
        if ifaceaddr:
            assert len(ifaceaddr) == 1, \
                'PXE_INTERFACE "%s" has multiple IPs assigned to it' % self.pxe_interface
            ifaceaddr = ifaceaddr.pop()
            self.morehosts = '%s torms' % ifaceaddr['addr']
            self.broadcast = ifaceaddr['broadcast']
            self.netmask = ifaceaddr['netmask']
        else:
            self.morehosts = '# This file left intentionally blank'
            # other fields will be filled in by specific kludges

        iface = 1

        # Which form is tmdomain? FIXME: move this to build_config
        elems = self.tmdomain.split(',')
        self.tmdomain = elems.pop(0)

        if not elems:           # DNS lookup for all nodes
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
        else:
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
                    if i >= 40:
                        break
                    self.hostIPs.append(str(h))
            elif '-' in tmp:    # Inclusive range
                try:
                    elems = tmp.split('-')
                    iprange = list(iter_iprange(elems[0], elems[1]))[:40]
                except Exception as e:
                    raise RuntimeError(
                        'TMDOMAIN: illegal range notation: %s' % str(e))
                assert len(iprange) == 40, 'TMDOMAIN IP range is too small'
                self.hostIPs = [ str(h) for h in iprange ]
                if not ifaceaddr:
                    # Kludge.  The smallest possible netmask is 6 bits (64)
                    # but if the range crossed boundaries...Assume class C
                    # containment.  iprange_to_cidrs() seems like it ought
                    # to help but it ate my brain.
                    self.netmask = '255.255.255.0'
                    self.network = str(IPAddress(iprange[0].value & 0xFFFFFF00))
                    self.broadcast = str(IPAddress(iprange[0].value | 0xFF))
            else:               # Single IP address
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
                    self.hostIPs = [
                        str(IPAddress(ipaddr.value + i)) for i in range(40) ]

        assert len(self.hostIPs) == 40, \
            'TMDOMAIN form only yields %d IP addresses' % len(self.hostIPs)

        size = os.stat(self.tftp_grub_efi).st_size
        self.boot_file_size_512_blocks = size // 512
        assert self.boot_file_size_512_blocks * 512 == size, \
            'EFI file "%s" size is not a multiple of 512' % self.tftp_grub_efi
        conf = _dnsmasq_conf_template.format(**vars(self))

        prepath = '%s/%s' % (self.dnsmasq_dir, self.pxe_interface)

        with open(prepath + '.conf', 'w') as f:
            f.write(conf)

        self.coords = [ 'enclosure/%d/node/%d' % ((i // 10) + 1, (i % 10) + 1)
                        for i in range(40) ]
        zipped = zip(self.coords, self.hostIPs, self.hostnames)
        with open(prepath + '.hostsfile', 'w') as f:
            for h in zipped:
                f.write('id:%s,%s,%s\n' % h)

        # Static assignments
        with open(prepath + '.morehosts', 'w') as f:
            f.write(self.morehosts)

    def create_environment(self):
        """
            Create tftp environment: grub menu files based off
        node's hostname, which is implicitly the node's physical location.
        These files are static over the lifetime of a machine instance. Then
        create filesystem image directories per these coords for PXE boot
        to pick up on boot .cpio and .vmlinuz.  manifest_api will populate
        those directories when nodes are bound.
        """

        grub_cfg_content = self.grub_cfg_compose()
        with open(self.tftp_grub_cfg, 'w') as file_obj:
            file_obj.write(grub_cfg_content)

        for hostname in self.hostnames:
            tftp_node_fs = self.tftp_images_dir + '/' + hostname
            make_dir(tftp_node_fs)
            grub_menu_content = self.grub_menu_compose(hostname)
            menu_fname = '%s/%s.menu' % (self.tftp_grub_menus_dir, hostname)
            with open(menu_fname, 'w') as file_obj:
                file_obj.write(str(grub_menu_content))

        self.configure_dnsmasq()

    def grub_menu_compose(self, hostname):
        """
            Return grub menu content that contains .format anchors:
        {hostname} - name of the node
        {tftp_dir} - TFTP-relative path to the node's filesystem image
                    .cpio and .vmlinuz.
        """
        tftp_dir = '%s/%s' % (self.chroot_images_dir, hostname)
        template = """set default=0
set menu_color_highlight=white/brown

menuentry '{hostname} L4TM ARM64'
  linux (tftp){tftp_dir}/l4tm.vmlinuz
  append root=/dev/ram0 console=ttyAMA0 acpi=force rw
  initrd (tftp){tftp_dir}/l4tm.cpio
"""
        return template.format(hostname=hostname, tftp_dir=tftp_dir)

    def grub_cfg_compose(self):
        """
            Template string for a grub.cfg that references grub menu
        for each node on PXE boot.
        """
        header_tplt = """set gfxmode=auto
insmod efi_gop
insmod efi_uga
insmod gfxterm
terminal_output gfxterm
"""

        lines = header_tplt.split('\n')

        configfile = '%s/${net_efinet1_hostname}' % (self.chroot_grub_menus_dir)
        lines.append('configfile "(tftp)%s' % configfile)

        return '\n'.join(lines)


def main(config_file):
    """
        Configure TFTP environment.
    """

    manconfig = ManifestingConfiguration(config_file, autoratify=False)
    missing = manconfig.ratify(dontcare=('GOLDEN_IMAGE', 'TMCONFIG'))
    if missing:
        raise RuntimeError('\n'.join(missing))
    grubby = TMgrub(manconfig)
    grubby.create_environment()
    print('Master GRUB configuration in', grubby.tftp_grub_cfg)
    print('      Per-node grub menus in', grubby.tftp_grub_menus_dir)
    print('      Per-node image dirs in', grubby.tftp_images_dir)
    print('           dnsmasq config in %s/%s.*' % (
        grubby.dnsmasq_dir, grubby.pxe_interface))


if __name__ == '__main__':
    """ Parse command line arguments. """
    parser = argparse.ArgumentParser(description='Generate GRUB2 config files')
    parser.add_argument('--config',
                        help='Manifest API server configuration file',
                        default=None)
    args, _ = parser.parse_known_args(sys.argv[1:])

    if args.config is None:
        args.config = os.path.realpath(__file__)
        args.config = os.path.dirname(args.config) + '/manifest_config.py'

    msg = 0     # establish scope
    try:
        main(args.config)
    except Exception as e:
        msg = str(e)
    raise SystemExit(msg)
