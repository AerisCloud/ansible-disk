#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import boto
import six

from pathlib import Path

from ansible.module_utils.basic import *

module = AnsibleModule(argument_spec=dict(
    config=dict(required=True, type='list'),
))


def update_disk(disk, mapping):
    if 'device_name' not in disk:
        return disk
    if disk['device_name'] not in mapping:
        return disk

    volume_id = mapping[disk['device_name']]['volume_id']
    link_path = '/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_vol%s' % volume_id[4:]
    resolved = str(Path(link_path).resolve())

    new_disk = dict(disk)
    new_disk['disk'] = resolved
    new_disk['part'] = '%sp1' % resolved
    return new_disk


def main():
    src_config = module.params['config']

    instance_id = requests.get('http://169.254.169.254/latest/meta-data/instance-id').text
    ec2 = boto.connect_ec2()
    attribute = ec2.get_instance_attribute(instance_id, 'blockDeviceMapping')
    mapping = {
        k: {'volume_id': v.volume_id, 'size': v.size, 'status': v.status}
        for k, v in six.iteritems(attribute['blockDeviceMapping'])
    }

    new_config = [
        update_disk(disk, mapping) for disk in src_config
    ]

    facts = {'blockDeviceMapping': mapping, 'config': new_config, 'source_config': src_config}
    result = {"changed": False, "ansible_facts": facts}
    module.exit_json(**result)


main()
