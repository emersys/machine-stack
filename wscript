#! /usr/bin/env python
# encoding: utf-8
import os
import shutil
import sys
import tarfile

from waflib.Configure import conf


def options(ctx):
    ctx.load("venv", tooldir=os.path.join(ctx.path.abspath(), "waftools"))


def configure(ctx):
    print("→ configuring the project in " + ctx.path.abspath())
    ctx.load("venv", tooldir=os.path.join(ctx.path.abspath(), "waftools"))
    ctx.env.SRCPATH = ctx.path.abspath()


@conf
def module_builder(ctx, module, configure="", numthreads=4):
    srcpath = ctx.env.SRCPATH
    return """
        base="%(module)s"
        pushd %(srcpath)s/3rdparty
        rm -fr "$base"
        tar xzf "$base.tar.gz"
        pushd "$base"
        ./configure --prefix=$VIRTUAL_ENV %(configure)s
        make -j%(numthreads)d
        make install
        popd
        rm -fr "$base"
        popd
    """ % locals()


@conf
def module(ctx, module, configure="", numthreads=4, **kwargs):
    srcscript = ctx.module_builder(module, configure, numthreads)
    return ctx(rule=lambda target: ctx.venv_exec(srcscript), **kwargs)


@conf
def build_freetype2(ctx, target):
    srcscript = ctx.module_builder("freetype-2.1.10")
    ctx.venv_exec(srcscript)

    includepath = os.path.join(ctx.out_dir, "include")
    srcpath = os.path.join(includepath, "ft2build.h")
    dstpath = os.path.join(includepath, "freetype2", "ft2build.h")
    os.symlink(srcpath, dstpath)


@conf
def build_gfortran(ctx, target):
    binpath = os.path.join(ctx.out_dir, "bin")
    manpath = os.path.join(ctx.out_dir, "share", "man", "man1")
    includepath = os.path.join(ctx.out_dir, "include")

    binfiles = os.listdir(binpath)
    manfiles = os.listdir(manpath)
    srcpath = ctx.env.SRCPATH

    ctx.venv_exec("""
        base="gcc-42-5666.3-darwin11"
        pushd %(srcpath)s/3rdparty
        rm -fr "$base"
        mkdir -p "$base"
        pushd "$base"
        xar -xf "../$base.pkg"
        mv *.pkg/Payload Payload.gz
        pax --insecure -rz -f Payload.gz -s ",./usr,$VIRTUAL_ENV,"
        ln -sf "$VIRTUAL_ENV/bin/gfortran-4.2" "$VIRTUAL_ENV/bin/gfortran"
        popd
        rm -fr "$base"
        popd
    """ % locals())

    # Delete other files installed
    shutil.rmtree(os.path.join(includepath, "gcc"))

    for f in os.listdir(binpath):
        if f not in binfiles and not "gfortran" in f:
            os.unlink(os.path.join(binpath, f))

    for f in os.listdir(manpath):
        if f not in manfiles and not "gfortran" in f:
            os.unlink(os.path.join(manpath, f))


@conf
def build_mathjax(ctx, target):
    cmd = "from IPython.frontend.html import notebook; print notebook.__file__"
    nbfile = ctx.venv_exec("echo \"%s\" | python" % cmd, log=True)
    static = os.path.join(os.path.dirname(nbfile), "static")
    tarpath = os.path.join(ctx.env.SRCPATH, "3rdparty", "mathjax-1.1.0.tar.gz")
    tar = tarfile.open(name=tarpath, mode="r:gz")
    topdir = tar.firstmember.path
    tar.extractall(static)
    ctx.cmd_and_log("mv -f %s %s && touch %s" % (
        os.path.join(static, topdir),
        os.path.join(static, "mathjax"),
        os.path.join(ctx.out_dir, ".mathjax-done")))


@conf
def build_blas(ctx, target):
    srcpath = ctx.env.SRCPATH
    libpath = os.path.join(ctx.out_dir, "lib")
    srcscript = """
        set -e
        base="blas"
        pushd %(srcpath)s/3rdparty
        rm -fr BLAS
        tar -xzf "$base.tgz"
        pushd BLAS
        gfortran -shared -O2 *.f -o libblas.so -fPIC
        gfortran -O2 -c *.f
        ar cr libblas.a *.o
        cp libblas.a libblas.so %(libpath)s
        popd
        rm -fr BLAS
        popd
    """ % locals()
    ctx.venv_exec(srcscript)


@conf
def build_cvxopt(ctx, target):
    srcpath = ctx.env.SRCPATH
    module = "cvxopt-1.1.5"

    # setup file is in the "src"
    srcscript = """
        base="%(module)s"
        pushd %(srcpath)s/3rdparty/site-packages
        rm -fr "$base"
        tar xzf "$base.tar.gz"
        pushd "$base/src"
        python setup.py install
        popd
        rm -fr "$base"
        popd
    """ % locals()
    ctx.venv_exec(srcscript)


def build(ctx):
    ctx(rule="virtualenv --distribute .", target="../bin/activate")
    ctx.module(
        "pkg-config-0.27.1", "--disable-debug --with-internal-glib",
        source="../bin/activate", target="../bin/pkg-config")

    ctx.module("libpng-1.5.13", source="../bin/pkg-config", target="../bin/libpng-config")
    ctx.module("zeromq-3.2.2", source="../bin/pkg-config", target="../lib/libzmq.a")
    ctx(rule=ctx.build_freetype2, source="../bin/pkg-config", target="../bin/freetype-config")

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
        source="../bin/pkg-config", target=numpy)

    # Install cvxopt separately due to misplaced setup.py file.
    cvxopt = os.path.join(site_packages, "cvxopt", "__init__.py")
    ctx(rule=ctx.build_cvxopt, source=numpy, target=cvxopt)

    reqs = "%s/requirements.txt" % ctx.path.abspath()
    ctx(
        rule=ctx.venv("pip install --no-index -f file://%s -r %s && touch ${TGT}" % (pkg, reqs)),
        source=[
            numpy,
            "../bin/freetype-config",
            "../bin/libpng-config",
            # "../bin/qmake",
            "../lib/libzmq.a",
        ] + platform_deps,
        target="../.requirements-done")

    ctx.add_manual_dependency("../.requirements-done", reqs)
    ctx(rule=ctx.build_mathjax, source="../.requirements-done", target="../.mathjax-done")
    ctx(rule="touch ${TGT}", source="../.mathjax-done", target="../.done")
