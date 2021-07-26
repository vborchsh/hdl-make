target = "xilinx"
action = "synthesis"

syn_device = "xc6slx45t"
syn_grade = "-3"
syn_package = "fgg484"
syn_top = "repinned_top"
syn_project = "hdlmake.xise"
syn_tool = "ise"

modules = {
  "local" : [ "rtl/lib_c" ],
}

