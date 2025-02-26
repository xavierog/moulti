# Install Moulti

## Technical requirements (abridged)

Moulti requires:

- Linux, BSD or MacOS
- Python ≥ 3.10
- Textual 1.0.x

!!! question "Wondering why?"
    Refer to the [complete technical requirements](technical-requirements.md).

## Set up Moulti

### From PyPI

Moulti is available as a [Python package on PyPI](https://pypi.org/project/moulti/) and can thus be installed using `pip` or, more conveniently, `pipx`:

```shell
pipx install moulti
pipx ensurepath
```

[pipx](https://pipx.pypa.io/latest/installation/) is available as a standard system package on the vast majority of Linux and BSD distributions.
On macOS, it is available through [Homebrew](https://brew.sh/), i.e. in the worst-case scenario, macOS users should install Homebrew, then pipx, then Moulti.

### Distribution packages

#### ArchLinux

Moulti is available on the Arch User Repository (AUR) as [python-moulti](https://aur.archlinux.org/packages/python-moulti).

Other distribution packages are of course welcome.

## Set up shell completion (optional)

Moulti is compatible with [argcomplete global completion](https://kislyuk.github.io/argcomplete/#global-completion).
This means that, depending on your system and installed packages, shell completion for Moulti may work out of the box.
This should be true for:

- Debian (bash, but also zsh)
- Fedora (bash only)

... as long as packages `bash-completion` and `python3-argcomplete` are installed.

Otherwise, refer to the [argcomplete documentation](https://kislyuk.github.io/argcomplete/).

!!! warning "Limitation"
    Shell completion helps typing subcommands and options but is technically unable to suggest existing step names.

## Start using Moulti

The `moulti` command should now be available in your shell, along with [a few others](commands.md).
You can thus start using Moulti. If you are not familiar with Moulti, head to [first steps](first-steps.md).
