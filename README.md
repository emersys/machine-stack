Machine-Stack
============
Sets up a python virtualenv with various scientific packages.
Includes: numpy, scipy, ipython, matplotlib


Requirements
============

Python 2.7 with distutils and virtualenv installed.


Usage
=====

The machine-stack repo must be included as a submodule to your main git repo.
It can be named anything. The top level of the repo must include a wscript file
which should look something like:


```python
APPNAME = <APPNAME>
VERSION = <VERSION>

top = "."
out = "env"


def options(ctx):
    ctx.recurse("src")


def configure(ctx):
    ctx.recurse("src")


def build(ctx):
    ctx.recurse("src")
```

To build the stack, run the following command from the top level of the repo.

On Ubuntu, you must first install a fortran compiler with lapack.

```
$ sudo apt-get install gfortran liblapack-dev
```

To build the stack run:

```
$ src/waf configure clean build
```
