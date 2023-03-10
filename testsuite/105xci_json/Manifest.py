target = "xilinx"
action = "synthesis"

syn_device = "xc7a200t"
syn_grade = "-2"
syn_package = "ffg1156"
syn_top = "xci_test"
syn_project = "xci_test"
syn_tool = "vivado"

files = [
    "adc_memory.xci",
    "xci_test.vhd",
]
