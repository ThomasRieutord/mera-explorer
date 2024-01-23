How to create the filesystem TXT files?
=======================================

  1. At the root directory containing MERA data (the parent directory of `mera`) run:
```
ls mera/*/*/*/* > $MERAEXPDIR/filesystems/merafiles_$FSNAME.txt
```
with `FSNAME` an explicit shortname to identify the filesystem and `MERAEXPDIR` the path to the `mera_explorer` package.

  2. Add the following lines at the top of the created file
```
#!HOSTNAME=<host name of IP adress to reach the machine where is the data (ex: hpc-login)>
#!MERAROOT=<path to the root dir containing mera file (ex: /scratch/dui)>
```

  3. Gather all file systems into one
```
cd $MERAEXPDIR/filesystems
cat merafiles_*.txt > allmerafiles.txt
```


Why do we do that?
------------------
MERA data are scattered across multiple locations: the hard drives at met Eireann HQ (`reaext*`), ATOS account of people retrieving it from ECFS (`ecfs*`).
These TXT files export the list of files present in a given filesystem.
It gives a quick way to check what data are available and where are they.
