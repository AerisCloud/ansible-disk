# Ansible Disk

This role allows:

- format disks or partitions and attach them to different mount points,
- resize filesystems (ext3/ext4, btrfs and xfs).

You can use it to create data directories for different services on a separate drive or partition.

## Configuration

### Inventory

The configuration for additional disks and partitions must be stored as YAML, so you should save it in `group_vars` (or `host_vars`).

```yaml
# inventory/group_vars/GROUP_NAME.yml
# or
# inventory/host_vars/HOST_NAME.yml
disk_additional_disks:
  - disk: /dev/sdb
    fstype: ext4
    mount_options: defaults
    mount: /ssd/wwwdata
    user: www-data
    group: www-data
    disable_periodic_fsck: false
  - disk: /dev/nvme0n1
    label: gpt
    parts:
      - fstype: xfs
        mount_options: defaults,noatime
        mount: /nvme/data1
        start: 0%
        end: 50%
      - fstype: xfs
        mount_options: defaults,noatime
        mount: /nvme/data2
        start: 50%
        end: 100%
  - device_name: /dev/sdf
    fstype: btrfs
    mount_options: defaults
    mount: /data3
```

- `disk` is the device you want to mount
- `label` sets the partition table label on the disk (optional).
- `parts` is the list of disk partitions (optional).
  - `name` is the partition name (optional).
  - `fstype` is the file system type for the partition.
  - `fsopts` is the file system option for the partition.
  - `mount` is the mount point for the partition.
  - `mount_options` lets you specify custom mount options for your partition.
  - `user` defines an owner of the mount directory (default: `root`).
  - `group` defines a group of the mount directory (default: `root`).
  - `disable_periodic_fsck` ...
- `fstype`is the file system type for the disk.
- `mount_options` lets you specify custom mount options for your new disk.
- `mount` is the mount point for the disk.
- `user` defines an owner of the mount directory (default: `root`).
- `group` defines a group of the mount directory (default: `root`).
- `disable_periodic_fsck` disables periodic checking of the ext3/4 file system on a new disk.

Translated with www.DeepL.com/Translator (free version)

The following filesystems are currently supported:

- [ext2](http://en.wikipedia.org/wiki/Ext2)
- [ext3](http://en.wikipedia.org/wiki/Ext3)
- [ext4](http://en.wikipedia.org/wiki/Ext4)
- [xfs](http://en.wikipedia.org/wiki/XFS) \*
- [btrfs](http://en.wikipedia.org/wiki/BTRFS) \*

\*) NOTE: To use these filesystems you have to define and install additional software packages. Please estimate the right package names for your operating system.

```yaml
# inventory/group_vars/GROUP_NAME
disk_additional_fs_utils:
  - xfsprogs # package for mkfs.xfs on RedHat / Ubuntu
  - btrfs-progs # package for mkfs.btrfs on CentOS / Debian
```

## How it works

It uses `parted` to partition the disk with a loop primary filesystem spanning the entire disk or with a list of primary partitions with GPT label.
The specified filesystem will then be created with `mkfs`.
Finally the new partition will be mounted to the specified mount path.
