#!/usr/bin/python
# -*- coding: utf-8 -*-

from ctypes import *
from fcntl import ioctl
from pathlib import Path
import json
import os
import subprocess

from ansible.module_utils.basic import *

module = AnsibleModule(argument_spec=dict(
    config=dict(required=True, type='list'),
))


NVME_ADMIN_IDENTIFY = 0x06
NVME_IOCTL_ADMIN_CMD = 0xC0484E41
AMZN_NVME_VID = 0x1D0F
AMZN_NVME_EBS_MN = "Amazon Elastic Block Store"

class nvme_admin_command(Structure):
    _pack_ = 1
    _fields_ = [("opcode", c_uint8),      # op code
                ("flags", c_uint8),       # fused operation
                ("cid", c_uint16),        # command id
                ("nsid", c_uint32),       # namespace id
                ("reserved0", c_uint64),
                ("mptr", c_uint64),       # metadata pointer
                ("addr", c_uint64),       # data pointer
                ("mlen", c_uint32),       # metadata length
                ("alen", c_uint32),       # data length
                ("cdw10", c_uint32),
                ("cdw11", c_uint32),
                ("cdw12", c_uint32),
                ("cdw13", c_uint32),
                ("cdw14", c_uint32),
                ("cdw15", c_uint32),
                ("reserved1", c_uint64)]

class nvme_identify_controller_amzn_vs(Structure):
    _pack_ = 1
    _fields_ = [("bdev", c_char * 32),  # block device name
                ("reserved0", c_char * (1024 - 32))]

class nvme_identify_controller_psd(Structure):
    _pack_ = 1
    _fields_ = [("mp", c_uint16),       # maximum power
                ("reserved0", c_uint16),
                ("enlat", c_uint32),     # entry latency
                ("exlat", c_uint32),     # exit latency
                ("rrt", c_uint8),       # relative read throughput
                ("rrl", c_uint8),       # relative read latency
                ("rwt", c_uint8),       # relative write throughput
                ("rwl", c_uint8),       # relative write latency
                ("reserved1", c_char * 16)]

class nvme_identify_controller(Structure):
    _pack_ = 1
    _fields_ = [("vid", c_uint16),          # PCI Vendor ID
                ("ssvid", c_uint16),        # PCI Subsystem Vendor ID
                ("sn", c_char * 20),        # Serial Number
                ("mn", c_char * 40),        # Module Number
                ("fr", c_char * 8),         # Firmware Revision
                ("rab", c_uint8),           # Recommend Arbitration Burst
                ("ieee", c_uint8 * 3),      # IEEE OUI Identifier
                ("mic", c_uint8),           # Multi-Interface Capabilities
                ("mdts", c_uint8),          # Maximum Data Transfer Size
                ("reserved0", c_uint8 * (256 - 78)),
                ("oacs", c_uint16),         # Optional Admin Command Support
                ("acl", c_uint8),           # Abort Command Limit
                ("aerl", c_uint8),          # Asynchronous Event Request Limit
                ("frmw", c_uint8),          # Firmware Updates
                ("lpa", c_uint8),           # Log Page Attributes
                ("elpe", c_uint8),          # Error Log Page Entries
                ("npss", c_uint8),          # Number of Power States Support
                ("avscc", c_uint8),         # Admin Vendor Specific Command Configuration
                ("reserved1", c_uint8 * (512 - 265)),
                ("sqes", c_uint8),          # Submission Queue Entry Size
                ("cqes", c_uint8),          # Completion Queue Entry Size
                ("reserved2", c_uint16),
                ("nn", c_uint32),            # Number of Namespaces
                ("oncs", c_uint16),         # Optional NVM Command Support
                ("fuses", c_uint16),        # Fused Operation Support
                ("fna", c_uint8),           # Format NVM Attributes
                ("vwc", c_uint8),           # Volatile Write Cache
                ("awun", c_uint16),         # Atomic Write Unit Normal
                ("awupf", c_uint16),        # Atomic Write Unit Power Fail
                ("nvscc", c_uint8),         # NVM Vendor Specific Command Configuration
                ("reserved3", c_uint8 * (704 - 531)),
                ("reserved4", c_uint8 * (2048 - 704)),
                ("psd", nvme_identify_controller_psd * 32),     # Power State Descriptor
                ("vs", nvme_identify_controller_amzn_vs)]  # Vendor Specific

class ebs_nvme_device:
    def __init__(self, device):
        self.device = device
        self.ctrl_identify()

    def _nvme_ioctl(self, id_response, id_len):
        admin_cmd = nvme_admin_command(opcode = NVME_ADMIN_IDENTIFY,
                                       addr = id_response,
                                       alen = id_len,
                                       cdw10 = 1)

        with open(self.device, "w") as nvme:
            ioctl(nvme, NVME_IOCTL_ADMIN_CMD, admin_cmd)

    def ctrl_identify(self):
        self.id_ctrl = nvme_identify_controller()
        self._nvme_ioctl(addressof(self.id_ctrl), sizeof(self.id_ctrl))

    def is_ebs(self):
        if self.id_ctrl.vid != AMZN_NVME_VID:
            return False
        if self.id_ctrl.mn.strip() != AMZN_NVME_EBS_MN:
            return False
        return True

    def get_volume_id(self):
        vol = self.id_ctrl.sn.decode('utf-8')

        if vol.startswith("vol") and vol[3] != "-":
            vol = "vol-" + vol[3:]

        return vol.strip()

    def get_block_device(self, stripped=False):
        dev = self.id_ctrl.vs.bdev.decode('utf-8')

        if stripped and dev.startswith("/dev/"):
            dev = dev[5:]

        return dev.strip()


def update_disk(disk, mapping):
    if 'device_name' not in disk:
        return disk

    device_name = disk['device_name'][5:]
    if device_name not in mapping:
        return disk

    volume_id = mapping[device_name]
    link_path = '/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_vol%s' % volume_id[4:]
    resolved = str(Path(link_path).resolve())

    new_disk = dict(disk)
    new_disk['disk'] = resolved
    new_disk['part'] = '%sp1' % resolved
    return new_disk


def main():
    src_config = module.params['config']

    lsblkOutput = subprocess.check_output(['lsblk', '-J'])
    lsblk = json.loads(lsblkOutput.decode('utf-8'))
    mapping = {}
    for blockdevice in lsblk['blockdevices']:
        try:
            dev = ebs_nvme_device('/dev/%s' % blockdevice['name'])
        except OSError:
            continue
        if dev.is_ebs():
            continue
        mapping[dev.get_block_device()] = dev.get_volume_id()

    new_config = [
        update_disk(disk, mapping) for disk in src_config
    ]

    facts = {'blockDeviceMapping': mapping, 'config': new_config, 'source_config': src_config}
    result = {"changed": False, "ansible_facts": facts}
    module.exit_json(**result)


main()
