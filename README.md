# packelf

A _packelf_ packs ELF files by relocating linked shared objects.
It copies linked shared objects into `.lib` directory of the given path and rewrite `rpath` of ELF files by [patchelf][] to make them relocatable.

## Requirements

- [patchelf][]

[patchelf]: https://nixos.org/patchelf.html

## Limitation

- It may break ELF files which already use `rpath` to change reference of shared objects

## See also

- [refreeze-scripts](https://github.com/fixpoint/refreeze-scripts) - Make EXE files in `Scripts` directory relocatable
