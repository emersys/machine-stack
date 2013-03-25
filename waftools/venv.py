#! /usr/bin/env python
# encoding: utf-8
import os
import tempfile

from waflib.Configure import conf


print("→ loading the venv tool")


@conf
def venv(ctx, cmd):
    return "(source bin/activate && DYLD_LIBRARY_PATH=$VIRTUAL_ENV %s)" % cmd


@conf
def venv_exec(ctx, srcscript, log=False):
    ctx.start_msg("→ Executing script in python virtualenv...")
    srcscript = [
        "#!/bin/bash"
        "set -eu",
        "source %s" % os.path.join(ctx.out_dir, "bin", "activate"),
        "export DYLD_LIBRARY_PATH=$VIRTUAL_ENV",
        srcscript,
        "deactivate"]

    try:
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write("\n".join(srcscript))
        f.close()

        cmd = "bash %s" % f.name
        ret = ctx.cmd_and_log(cmd) if log is True else ctx.exec_command(cmd)
    finally:
        os.unlink(f.name)

    ctx.end_msg("→ Done executing script in virtualenv.")
    return ret
