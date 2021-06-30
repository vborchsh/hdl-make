target = "xilinx"
action = "synthesis"

syn_device = "xc7a200t"
syn_grade = "-2"
syn_package = "ffg1156"
syn_top = "xci_test"
syn_project = "xci_test"
syn_tool = "vivado"

files = [
    "vio_din2_w64_dout2_w64.xci",
    "xci_test.vhd",
]
