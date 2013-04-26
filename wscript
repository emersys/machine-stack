#! /usr/bin/env python
# encoding: utf-8
import os
import sys


def options(ctx):
    toolsdir = os.path.join(ctx.path.abspath(), "waftools")
    ctx.load("venv", tooldir=toolsdir)
    ctx.load("modules", tooldir=toolsdir)


def configure(ctx):
    print("→ configuring the project in " + ctx.path.abspath())
    toolsdir = os.path.join(ctx.path.abspath(), "waftools")
    ctx.load("venv", tooldir=toolsdir)
    ctx.load("modules", tooldir=toolsdir)
    ctx.env.SRCPATH = ctx.path.abspath()


def build(ctx):
    ctx(rule="virtualenv --distribute .", target="../bin/activate")
    ctx.module(
        "pkg-config-0.27.1", "--disable-debug --with-internal-glib",
        source="../bin/activate", target="../bin/pkg-config")

    ctx.module("libpng-1.5.13", source="../bin/pkg-config", target="../bin/libpng-config")
    ctx.module("zeromq-3.2.2", source="../bin/pkg-config", target="../lib/libzmq.a")
    ctx(rule=ctx.build_freetype2, source="../bin/pkg-config", target="../bin/freetype-config")
    ctx(rule=ctx.build_hbase, source="../bin/pkg-config", target="../hbase/bin/start-hbase.sh")
    # ctx.module("apache-couchdb-1.3.0", source="../bin/pkg-config", target="../bin/couchdb")
    # ctx(rule=ctx.build_mongo, source="../bin/pkg-config", target="../bin/mongod")
    # ctx(rule=ctx.build_scons, source="../bin/pkg-config", target="../bin/scons")

    pkg = os.path.join(ctx.path.abspath(), "3rdparty", "site-packages")
    if sys.platform == "darwin":
        ctx(rule=ctx.build_gfortran, source="../bin/pkg-config", target="../bin/gfortran")
        readlinetar = "%s/readline-6.2.4.1.tar.gz" % pkg
        readlinecmd = ctx.venv("easy_install --no-find-links %s && touch ${TGT}" % readlinetar)
        ctx(rule=readlinecmd, source="../bin/pkg-config", target="../.readline-done")
        platform_deps = ["../bin/gfortran", "../.readline-done"]
    else:
        # We assume that a fortran compiler with lapack is installed.
        # It may be installed using:
        # sudo apt-get install liblapack-dev gfortran
        ctx(rule=ctx.build_blas, source="../bin/pkg-config", target="../lib/libblas.a")
        platform_deps = ["../lib/libblas.a"]

    # qt_configure_flags = (
    #     "-opensource -fast -no-qt3support -no-phonon "
    #     "-no-declarative -no-openssl -no-cups -no-iconv -no-dbus "
    #     "-no-nis --confirm-license=yes")
    #
    # ctx.module(
    #     "qt-everywhere-opensource-src-4.8.4", qt_configure_flags, 1,
    #     source="../bin/pkg-config", target="../bin/qmake")

    # Install numpy separately due to bug in scipy install script.
    site_packages = os.path.join("..", "lib", "python2.7", "site-packages")
    numpy = os.path.join(site_packages, "numpy", "__init__.py")
    ctx(rule=ctx.venv("pip install numpy==1.6.2 --no-index -f file://%s" % pkg),
        source=platform_deps, target=numpy)

    # Install cvxopt separately due to misplaced setup.py file.
    cvxopt = os.path.join(site_packages, "cvxopt", "__init__.py")
    ctx(rule=ctx.build_cvxopt, source=numpy, target=cvxopt)

    # Install iPython separately from requirements in order to build mathjax.
    ctx(rule=ctx.pip_install("ipython==0.13.1"), source=numpy, target="../bin/ipython")
    ctx(rule=ctx.build_mathjax, source="../bin/ipython", target="../.mathjax-done")

    reqs = "%s/requirements.txt" % ctx.path.abspath()
    ctx(
        rule=ctx.venv("pip install --no-index -f file://%s -r %s && touch ${TGT}" % (pkg, reqs)),
        source=platform_deps + [
            numpy,
            # "../bin/qmake",
            "../.mathjax-done",
            "../bin/ipython",
            "../bin/freetype-config",
            "../bin/libpng-config",
            "../lib/libzmq.a",
        ],
        target="../.requirements-done")

    ctx.add_manual_dependency(reqs, "../.requirements-done")
    ctx(rule="touch ${TGT}", source="../.requirements-done", target="../../.build-done")
