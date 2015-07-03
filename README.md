Disk
====

This role allows you to format extra disks and attach them to different mount points.

You can use it to move the data of different services to another disk.

Configuration
-------------

### Inventory

Because the configuration for additional disks must be stored using the YAML
syntax, you have to write it in a `group_vars` directory.

```yaml
# inventory/group_vars/GROUP_NAME
disk_additional_disks:
- disk: /dev/sdb
  fstype: ext4
  mount_options: defaults
  mount: /data
```

* `disk` is the device, you want to mount.
* `fstype` allows you to choose the filesystem to use with the new disk.
* `mount_options` allows you to specify custom mount options.
* `mount` is the directory where the new disk should be mounted.

You can add:
* `disk_user` sets owner of the mount directory (default: root)
* `disk_group` sets group of the mount directory (default: root)

The following filesystems are currently supported:
- [ext2](http://en.wikipedia.org/wiki/Ext2)
- [ext3](http://en.wikipedia.org/wiki/Ext3)
- [ext4](http://en.wikipedia.org/wiki/Ext4)

How it works
------------

It uses `sfdisk` to partition the disk with a single primary partition spanning the entire disk.
The specified filesystem will then be created with `mkfs`.
Finally the new partition will be mounted to the specified mount path.
