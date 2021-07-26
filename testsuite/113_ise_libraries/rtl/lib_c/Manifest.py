import os, errno
from pathlib import Path

exec(open(Path('../_rtl_version.py')).read())

try:
    __version__
except Exception:
    __version__ = "NO_VERSION_FILE_OR_VAL"  # default if for some reason the exec did not work


files = [
    "merged_top.vhd",
    "repinned_top.vhd",
]

library = "lib_c"  + __version__

modules = { "local" : ["../lib_a",
                       "../lib_b",
                      ]
}

# if we are simulating this will be handy... 
vcom_opt = "-93 +check_synthesis -mixedsvh -check_synthesis"