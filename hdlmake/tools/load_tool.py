"""Module providing the synthesis functionality for writing Makefiles"""


import logging

def load_syn_tool(tool_name):
    """Funtion that checks the provided module_pool and generate an
    initialized instance of the the appropriated synthesis tool"""
    from .ise import ToolISE
    from .planahead import ToolPlanAhead
    from .vivado import ToolVivado
    from .quartus import ToolQuartus
    from .diamond import ToolDiamond
    from .libero import ToolLibero
    from .liberosoc import ToolLiberoSoC
    from .icestorm import ToolIcestorm
    from .ghdl_syn import GhdlSyn
    available_tools = {'ise': ToolISE,
                       'planahead':  ToolPlanAhead,
                       'vivado': ToolVivado,
                       'quartus': ToolQuartus,
                       'diamond': ToolDiamond,
                       'libero': ToolLibero,
                       'liberosoc': ToolLiberoSoC,
                       'icestorm': ToolIcestorm,
                       'ghdl': GhdlSyn}
    if tool_name in available_tools:
        logging.debug("Synthesis tool to be used found: %s", tool_name)
        return available_tools[tool_name]()
    else:
        raise Exception("Unknown synthesis tool: " + tool_name
                        + ", supported synthesis tools are: {}".format(', '.join(available_tools.keys())))


def load_sim_tool(tool_name):
    """Funtion that checks the provided module_pool and generate an
    initialized instance of the the appropriated simulation tool"""
    from .iverilog import ToolIVerilog
    from .isim import ToolISim
    from .modelsim import ToolModelsim
    from .active_hdl import ToolActiveHDL
    from .riviera import ToolRiviera
    from .ghdl import ToolGHDL
    from .nvc import ToolNVC
    from .vivado_sim import ToolVivadoSim
    available_tools = {'iverilog': ToolIVerilog,
                       'isim': ToolISim,
                       'modelsim':  ToolModelsim,
                       'active_hdl': ToolActiveHDL,
                       'riviera':  ToolRiviera,
                       'ghdl': ToolGHDL,
                       'nvc': ToolNVC,
                       'vivado_sim': ToolVivadoSim}
    if tool_name in available_tools:
        logging.debug("Simulation tool to be used found: %s", tool_name)
        return available_tools[tool_name]()
    else:
        raise Exception("Unknown simulation tool: " + tool_name + '\n'
                        + "Supported simulation tools are " + ' '.join(available_tools.keys()))
