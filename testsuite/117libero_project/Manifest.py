target = "microsemi"
action = "synthesis"
syn_tool = "liberosoc"

syn_family = "IGLOO2"
syn_device = "M2GL025"
syn_grade = "-1"
syn_package = "484 FBGA"

syn_top = "gate"
syn_project = "demo"
project_opt = "-adv_options {RESTRICTPROBEPINS:0}"

files = [ "../files/gate.vhdl" ]
