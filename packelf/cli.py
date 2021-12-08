#!/usr/bin/env python3

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Iterator, Optional, Set, Tuple

LDD_PATTERN = re.compile(r"^\s*(.+) => (.+) \(0x[0-9a-fA-F]+\)$")

# https://www.python.org/dev/peps/pep-0513/
MANYLINUX1 = {
    "libpanelw.so.5",
    "libncursesw.so.5",
    "libgcc_s.so.1",
    "libstdc++.so.6",
    "libm.so.6",
    "libdl.so.2",
    "librt.so.1",
    "libc.so.6",
    "libnsl.so.1",
    "libutil.so.1",
    "libpthread.so.0",
    "libresolv.so.2",
    "libX11.so.6",
    "libXext.so.6",
    "libXrender.so.1",
    "libICE.so.6",
    "libSM.so.6",
    "libGL.so.1",
    "libgobject-2.0.so.0",
    "libgthread-2.0.so.0",
    "libglib-2.0.so.0",
}

# https://www.python.org/dev/peps/pep-0571/
MANYLINUX2010 = {
    "libgcc_s.so.1",
    "libstdc++.so.6",
    "libm.so.6",
    "libdl.so.2",
    "librt.so.1",
    "libc.so.6",
    "libnsl.so.1",
    "libutil.so.1",
    "libpthread.so.0",
    "libresolv.so.2",
    "libX11.so.6",
    "libXext.so.6",
    "libXrender.so.1",
    "libICE.so.6",
    "libSM.so.6",
    "libGL.so.1",
    "libgobject-2.0.so.0",
    "libgthread-2.0.so.0",
    "libglib-2.0.so.0",
}

# https://www.python.org/dev/peps/pep-0599/
MANYLINUX2014 = {
    "libgcc_s.so.1",
    "libstdc++.so.6",
    "libm.so.6",
    "libdl.so.2",
    "librt.so.1",
    "libc.so.6",
    "libnsl.so.1",
    "libutil.so.1",
    "libpthread.so.0",
    "libresolv.so.2",
    "libX11.so.6",
    "libXext.so.6",
    "libXrender.so.1",
    "libICE.so.6",
    "libSM.so.6",
    "libGL.so.1",
    "libgobject-2.0.so.0",
    "libgthread-2.0.so.0",
    "libglib-2.0.so.0",
}

EXTERNAL_SHARED_LIBRARIES = MANYLINUX1 | MANYLINUX2010 | MANYLINUX2014

NON_ELF_EXTENSIONS = {
    ".py",
    ".pyc",
    ".pyi",
    ".txt",
    ".pem",
    ".json",
    ".rst",
    ".md",
    ".sh",
    ".h",
    ".c",
    ".o",  # .o is ELF but we don't patch so listed here
}

ELF_MAGIC_BYTES = b"\x7fELF"


def is_elf(path: Path) -> bool:
    with path.open(mode="rb") as fd:
        return fd.read(len(ELF_MAGIC_BYTES)) == ELF_MAGIC_BYTES


def patchelf(elf: Path, libs: Iterable[Path]) -> None:
    rpath = ":".join((r"$ORIGIN/%s" % os.path.relpath(lib, elf.parent) for lib in libs))
    print("Patch %s [%s]" % (elf, rpath))
    subprocess.run(["patchelf", "--set-rpath", rpath, str(elf)], check=True)


def iter_shared_objects(elf: Path) -> Iterator[Tuple[str, Path]]:
    """Iterate shared objects of a given ELF file"""
    r = subprocess.run(
        ["ldd", str(elf)],
        stdout=subprocess.PIPE,
        encoding=sys.getdefaultencoding(),
        check=True,
    )
    for line in r.stdout.splitlines():
        m = LDD_PATTERN.match(line)
        if m is None:
            continue
        yield (m.group(1), Path(m.group(2)).resolve())


def relocate_shared_objects(
    elf: Path, lib: Path, excludes: Optional[Set[str]] = None
) -> None:
    excludes_ = excludes or set()
    shared_objects = {
        (name, src) for name, src in iter_shared_objects(elf) if name not in excludes_
    }
    if not len(shared_objects):
        return
    lib.mkdir(parents=True, exist_ok=True)
    for name, src in shared_objects:
        dst = lib / name
        if dst.exists():
            print("Skip %s [%s -> %s]" % (name, src, dst))
        else:
            print("Copy %s [%s -> %s]" % (name, src, dst))
            shutil.copy(src, dst)
            # Recursively relocate shared objects
            relocate_shared_objects(dst, lib, excludes)
    patchelf(elf, [lib])


def packelf(path: Path, lib: Path, excludes: Optional[Set[str]] = None) -> None:
    """Pack ELF files in a given path by relocating shared objects"""
    for root, _dirs, files in os.walk(str(path)):
        root_ = Path(root)
        for f in (root_ / f for f in files):
            if f.suffix in NON_ELF_EXTENSIONS or not is_elf(f):
                continue
            relocate_shared_objects(f, lib, excludes)


def main():
    parser = argparse.ArgumentParser(
        description=("Pack ELF files in a given path by relocating shared objects")
    )
    parser.add_argument("-l", "--lib", default="./.lib")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("-a", "--copy-all", action='store_true')
    args = parser.parse_args()

    lib = Path(args.lib)
    for path in (Path(p) for p in args.paths):
        if args.copy_all:
            excludes = None
        else:
            excludes = EXTERNAL_SHARED_LIBRARIES
        packelf(path, path.joinpath(lib), excludes)


if __name__ == "__main__":
    main()
