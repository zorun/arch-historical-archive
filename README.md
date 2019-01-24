# Arch Linux Historical Archive

See <https://wiki.archlinux.org/index.php/Arch_Linux_Archive#Historical_Archive> for general
documentation.

## Usage

You need to configure the Internet Archive client first: <https://archive.org/services/docs/api/internetarchive/quickstart.html#configuring>

The script uploads all files for a given package name to archive.org:

    ./upload_pkg_internetarchive.py /srv/archive/packages/l/lucene++

It possible to restrict the upload to a list of years (see end of script).

To upload *all* packages or at least a large subset, combine `find` and `parallel`:

    find /srv/archive/packages -mindepth 2 -maxdepth 2 -type d | parallel --bar -j16 ~/upload_pkg_internetarchive.py > result.txt

The script outputs to stdout any package name it couldn't completely upload.
This may be due to archive.org load issues or rate limiting.

## How it works

- for the given package name, walk the filesystem on `orion` to find all files
  for the given years (both `*.pkg.tar.xz` and `*.sig`)

- parse .PKGINFO from the most recent package in this list to extract the pkgdesc,
  license, and upstream url

- upload all files in this list to archive.org

- if one of the files fails to upload, report the package name to stdout.  The script needs
  to be run again for this package name.

