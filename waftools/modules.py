#! /usr/bin/env python
# encoding: utf-8
import os
import shutil
import tarfile

from waflib.Configure import conf


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
def build_scons(ctx, target):
    module = "scons-2.3.0"
    srcpath = ctx.env.SRCPATH
    srcscript = """
        set -e
        base="%(module)s"
        pushd %(srcpath)s/3rdparty/site-packages
        rm -fr "$base"
        tar -xzf "$base.tar.gz"
        pushd "$base"
        python setup.py install
        popd
        rm -fr "$base"
        popd
    """ % locals()
    ctx.venv_exec(srcscript)


@conf
def build_mongo(ctx, target):
    module = "mongodb-src-r2.4.2"
    srcpath = ctx.env.SRCPATH
    srcscript = """
        set -e
        base="%(module)s"
        pushd %(srcpath)s/3rdparty
        rm -fr "$base"
        tar -xzf "$base.tar.gz"
        pushd "$base"
        scons --prefix="$VIRTUAL_ENV" install
        popd
        rm -fr "$base"
        popd
    """ % locals()
    ctx.venv_exec(srcscript)


@conf
def build_hbase(ctx, target):
    module = "hbase-0.94.6.1"
    srcpath = ctx.env.SRCPATH
    srcscript = """
        set -e
        base="%(module)s"
        pushd %(srcpath)s/3rdparty
        rm -fr "$base"
        tar -xzf "$base.tar.gz"
        rm -fr "$VIRTUAL_ENV/hbase"
        mv "$base" "$VIRTUAL_ENV/hbase"
        rm -fr "$VIRTUAL_ENV/hbase/conf/hbase-site.xml"
        (cat <<EOF
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>hbase.rootdir</name>
    <value>file://$VIRTUAL_ENV/hbase-data</value>
  </property>
  <property>
    <name>hbase.zookeeper.property.dataDir</name>
    <value>$VIRTUAL_ENV/zookeeper-data</value>
  </property>
</configuration>
EOF
) > "$VIRTUAL_ENV/hbase/conf/hbase-site.xml"
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


@conf
def pip_install(ctx, target):
    pkg = os.path.join(ctx.path.abspath(), "3rdparty", "site-packages")
    return ctx.venv("pip install %s --no-index -f file://%s" % (target, pkg))
