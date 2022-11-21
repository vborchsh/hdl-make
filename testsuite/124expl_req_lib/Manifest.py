action = "synthesis"
language = "vhdl"

syn_device = "xc6slx45t"
syn_grade = "-3"
syn_package = "fgg484"

syn_top = "gate3"
syn_project = "gate3.xise"

syn_tool = "ise"


files = [ "../files/gate3.vhd",
         # the file and what is provided.
         ("gate.ngc", "gate", ["mylib.mygate"]),
         ("mygate.ngc", "mylib.mygate") ]

