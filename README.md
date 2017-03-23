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
   user: www-data
   group: www-data
   disable_periodic_fsck: false
```

* `disk` is the device, you want to mount.
* `fstype` allows you to choose the filesystem to use with the new disk.
* `mount_options` allows you to specify custom mount options.
* `mount` is the directory where the new disk should be mounted.
* `user` sets owner of the mount directory (default: `root`).
* `group` sets group of the mount directory (default: `root`).
* `disable_periodic_fsck` deactivates the periodic ext3/4 filesystem check for the new disk.

You can add:
* `disk_package_use` is the required package manager module to use (yum, apt, etc). The default 'auto' will use existing facts or try to autodetect it.

The following filesystems are currently supported:
- [ext2](http://en.wikipedia.org/wiki/Ext2)
- [ext3](http://en.wikipedia.org/wiki/Ext3)
- [ext4](http://en.wikipedia.org/wiki/Ext4)
- [xfs](http://en.wikipedia.org/wiki/XFS) *
- [btrfs](http://en.wikipedia.org/wiki/BTRFS) *

*) Note: To use these filesystems you have to define and install additional software packages. Please estimate the right package names for your operating system.

```yaml
# inventory/group_vars/GROUP_NAME
additional_fs_utils:
  - xfsprogs     # package for mkfs.xfs on RedHat / Ubuntu
  - btrfs-progs  # package for mkfs.btrfs on CentOS / Debian
```

How it works
------------

It uses `sfdisk` to partition the disk with a single primary partition spanning the entire disk.
The specified filesystem will then be created with `mkfs`.
Finally the new partition will be mounted to the specified mount path.
