#target = "altera"
action = "synthesis"


syn_top = "lib_c.repinned_top"
syn_project = "demo"
syn_tool = "ghdl"


modules = {
   "local" : [ "../113_ise_libraries/rtl/lib_c" ],
}

