## Prerequisites

We recommend running the scripted data processing pipelines in a WSL Linux environment.

Ensure the following prerequisites are installed:

- Windows 10 or later.
- [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install) with Ubuntu 22.04 or later.
- Python 3.12 or later installed within WSL.
- [GAMS](https://www.gams.com/) installed on Windows, with a valid license. Note that the model is too large to work on trial versions of GAMS.

- [uv](https://docs.astral.sh/uv/) for Python dependency management.
- [git lfs](https://git-lfs.com/) for handling large data files. 

Some Windows tools, such as Veda or Windows GAMS installations, may also be helpful. Working in an exclusively Windows environment is not currently supported. 

Once the above tools are available, clone this reposiitory: 

```bash
git clone git@github.com:EECA-NZ/TIMES-NZ-Model-Files.git
```


```{note}
Legacy installations may also benefit from a working VEDA (VEDA 2.0 localhost) installation in your Windows user directory. See instructions [here](https://github.com/kanors-emr/Veda2.0-Installation/tree/master).

```