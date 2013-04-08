Sets up a python virtualenv with numpy/scipy/ipython/matplotlib installed.


Requirements
============

Python 2.7 with distutils and virtualenv installed.


Usage
=====

The machine-stack repo must be included as a submodule to your main git repo.
It can be named anything. The top level of the repo must include a wscript file
which should look something like:


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
