# HDLmake testsuite
# Just run 'pytest' in this directory.

import hdlmake.main
from hdlmake.manifest_parser.configparser import ConfigParser
import os
import os.path
import pytest
import shutil

class Config(object):
    def __init__(self, path=None, my_os='unx', fakebin="linux_fakebin"):
        self.path = path
        self.prev_env_path = os.environ['PATH']
        self.prev_check_windows_commands = hdlmake.util.shell.check_windows_commands
        self.prev_check_windows_tools = hdlmake.util.shell.check_windows_tools
        assert my_os in ('unx', 'windows', 'cygwin')
        self.check_windows_commands = my_os == 'windows'
        self.check_windows_tools = my_os in ('windows', 'cygwin')
        self.fakebin = fakebin

    def __enter__(self):
        os.environ['PATH'] = ("../" + self.fakebin + ":"
            + os.path.abspath(self.fakebin) + ':'
            + self.prev_env_path)
        if self.path is not None:
            os.chdir(self.path)
        hdlmake.util.shell.check_windows_tools = (lambda : self.check_windows_tools)
        hdlmake.util.shell.check_windows_commands = (lambda : self.check_windows_commands)

    def __exit__(self, *_):
        if self.path is not None:
            os.chdir("..")
        os.environ['PATH'] = self.prev_env_path
        hdlmake.util.shell.check_windows_tools = self.prev_check_windows_tools
        hdlmake.util.shell.check_windows_commands = self.prev_check_windows_commands

def compare_makefile():
    # shutil.copy('Makefile', 'Makefile.ref')  # To regenerate
    with open('Makefile.ref', 'r') as f:
        ref = f.read()
    with open('Makefile', 'r') as f:
        out = f.read()
    assert out == ref
    os.remove('Makefile')

def compare_makefile_filter(start):
    with open('Makefile.ref', 'r') as f:
        ref = f.readlines()
    with open('Makefile', 'r') as f:
        out = f.readlines()
    out = [l for l in out if not l.startswith(start)]
    # open('Makefile.ref', 'w').writelines(out) # To regenerate
    assert out == ref
    os.remove('Makefile')

def run_compare(**kwargs):
    with Config(**kwargs) as _:
        hdlmake.main.hdlmake([])
        compare_makefile()

def run_compare_filter(filter, **kwargs):
    with Config(**kwargs) as _:
        hdlmake.main.hdlmake([])
        compare_makefile_filter(filter)

def run_compare_xilinx(**kwargs):
    # HDLmake make the path absolute.  Remove this line.
    run_compare_filter(filter="XILINX_INI_PATH", **kwargs)

def run(args, **kwargs):
    with Config(**kwargs) as _:
        hdlmake.main.hdlmake(args)

def test_ise_001():
    run_compare(path="001ise")

def test_ise_windows_071():
    run_compare(path="071ise_windows", my_os='windows')

def test_ise_cygwin_082():
    run_compare(path="082ise_cygwin", my_os='cygwin')

def test_makefile_002():
    run_compare(path="002msim")

def test_makefile_003():
    run_compare(path="003msim")

def test_makefile_004():
    run_compare(path="004msim")

def test_filename_opt_062():
    run(['-f', 'my.mk'], path="062filename_opt")
    os.remove("062filename_opt/my.mk")

def test_fetch_001():
    run(['fetch'], path="001ise")

def test_clean_001():
    run(['clean'], path="001ise")

def test_list_mods_none_001():
    run(['list-mods'], path="001ise")

def test_list_files_001():
    run(['list-files'], path="001ise")

def test_circular_dep_096():
    run(['list-files'], path="096circular_dep")

def test_noact_005():
    with Config(path="005noact") as _:
        hdlmake.main.hdlmake(['manifest-help'])
        hdlmake.main.hdlmake(['list-files'])
        hdlmake.main.hdlmake(['list-mods', '--with-files'])

def test_ahdl_006():
    run_compare(path="006ahdl", my_os='windows')

def test_diamond_007():
    run_compare(path="007diamond")

def test_ghdl_008():
    run_compare(path="008ghdl")

def test_icestorm_009():
    run_compare_filter(filter="TOOL_PATH", path="009icestorm")

def test_isim_010():
    run_compare_xilinx(path="010isim")

def test_isim_windows_060():
    run_compare_xilinx(path="060isim_windows",
                       my_os='windows', fakebin="windows_fakebin")

def test_icarus_012():
    run_compare(path="012icarus")

def test_icarus_include_083():
    run_compare(path="083icarus_include")

def test_libero_013():
    run_compare(path="013libero")

def test_planahead_014():
    run_compare(path="014planahead")

def test_quartus_015():
    run_compare(path="015quartus")

def test_quartus_016():
    run_compare(path="016quartus_nofam")

def test_quartus_033():
    run_compare(path="033quartus")

def test_quartus_windows102():
    assert hdlmake.util.shell.check_windows_tools() is False
    run_compare(path="102quartus_windows", my_os='windows')

def test_quartus_034():
    run([], path="034quartus_prop")
    os.remove("034quartus_prop/Makefile")

def test_quartus_035():
    with pytest.raises(SystemExit) as _:
        run([], path="035quartus_err")
    print(os.getcwd())

def test_quartus_036():
    with pytest.raises(SystemExit) as _:
        run([], path="036quartus_err")

def test_quartus_037():
    with pytest.raises(SystemExit) as _:
        run([], path="037quartus_err")

def test_quartus_038():
    with pytest.raises(SystemExit) as _:
        run([], path="038quartus_err")

def test_quartus_039():
    with pytest.raises(SystemExit) as _:
        run([], path="039quartus_err")
    #os.remove('039quartus_err/Makefile')

def test_riviera_017():
    run_compare(path="017riviera")

def test_vivado_018():
    run_compare(path="018vivado")

def test_vivado_props_054():
    run_compare(path="054vivado_props")

def test_vivado_sim_019():
    run_compare(path="019vsim")

def test_git_fetch_020():
    with Config(path="020git_fetch") as _:
        hdlmake.main.hdlmake(['list-files'])
        hdlmake.main.hdlmake(['fetch'])
        hdlmake.main.hdlmake(['list-mods'])
        # Full clean
        shutil.rmtree('ipcores', ignore_errors=True)
        # To debug (keep old):
        #  shutil.rmtree('ipcores.old', ignore_errors=True)
        #  shutil.move('ipcores', 'ipcores.old')

def test_git_fetch_branch_055():
    with Config(path="055git_fetch_branch") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_git_fetch_rev_056():
    with Config(path="056git_fetch_rev") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_git_fetch_url_073():
    with Config(path="073git_fetch_url") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_git_fetch_url2_074():
    with Config(path="074git_fetch_url") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_git_fetch_err_075():
    with pytest.raises(SystemExit) as _:
        run(['fetch'], path="075err_git")
    shutil.rmtree('ipcores', ignore_errors=True)

def test_svn_fetch_err_094():
    with pytest.raises(SystemExit) as _:
        run(['--full-error', 'fetch'], path="094err_svn")
    shutil.rmtree('094err_svn/ipcores', ignore_errors=True)

def test_svn_fetch_021():
    with Config(path="021svn_fetch") as _:
        hdlmake.main.hdlmake(['list-mods'])
        hdlmake.main.hdlmake(['fetch'])
        hdlmake.main.hdlmake(['list-mods', '--with-files'])
        shutil.rmtree('ipcores')

def test_svn_fetch_rev_072():
    with Config(path="072svn_fetch_rev") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_gitsm_fetch_022():
    with Config(path="022gitsm_fetch") as _:
        hdlmake.main.hdlmake(['fetch'])
        hdlmake.main.hdlmake(['list-mods'])
        hdlmake.main.hdlmake(['clean'])
        shutil.rmtree('ipcores')

def test_git_fetch_cmds_065():
    with Config(path="065fetch_pre_post") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_sub_fetch_095():
    with Config(path="095sub_fetch") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_err_fetch_065():
    with pytest.raises(SystemExit) as _:
        run([], path="065fetch_pre_post")
        assert False

def test_xci_023():
    run_compare(path="023xci")

def test_xci_104():
    run_compare(path="104xci")

def test_xci_json_105():
    run_compare(path="105xci_json")

def test_xcix_106():
    run_compare(path="106xcix")

def test_vlog_parser_024():
    run_compare(path="024vlog_parser")

def test_vlog_parser_025():
    run_compare(path="025vlog_parser")

def test_vlog_parser_099():
    run_compare(path="099vlog_parser")

def test_vlog_inc_103():
    run_compare(path="103vlog_inc")

def test_vlog_attr131():
    run_compare(path="131vlog_attr")

def test_vlog_comment132():
    run_compare(path="132vlog_comment")

def test_gitsm_fetch_026():
    with Config(path="026gitsm_fetch") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_vhdl_parser_027():
    run_compare(path="027vhdl_parser")

def test_vhdl_parser_100():
    run_compare(path="100vhdl_parser")

def test_vhdl_context_101():
    run_compare(path="101vhdl_context")

def test_manifest_print_028():
    run([], path="028manifest_print")
    os.remove('028manifest_print/Makefile')

def test_manifest_quit_029():
    with pytest.raises(SystemExit) as _:
        run([], path="029manifest_quit")
        assert False

def test_manifest_syntax_030():
    with pytest.raises(SystemExit) as _:
        run([], path="030manifest_syntax")
        assert False

def test_manifest_except_031():
    with pytest.raises(SystemExit) as _:
        run([], path="031manifest_except")
        assert False

def test_manifest_nameerr_098():
    with pytest.raises(SystemExit) as _:
        run([], path="098manifest_nameerr")
        assert False

def test_manifest_vars_032():
    run([], path="032manifest_vars")

def test_srcfiles_040():
    run_compare(path="040srcfiles")

def test_no_syn_tool_041():
    with pytest.raises(SystemExit) as _:
        run([], path="041err_syn")
        assert False

def test_no_files_042():
    run([], path="042nofiles")
    os.remove("042nofiles/Makefile")

def test_no_bin_061():
    run_compare_xilinx(path="061err_nobin", fakebin="no_fakebin")

def test_local_043():
    run_compare(path="043local_fetch")

def test_files_dir_044():
    # Not sure we want to keep this feature: allow to specify a directory
    # as a file (will be replaced by all the files in the directory)
    run_compare(path="044files_dir")

def test_incl_makefile_045():
    run_compare(path="045incl_makefile")

def test_incl_makefiles_046():
    run_compare(path="046incl_makefiles")

def test_abs_local_047():
    with pytest.raises(SystemExit) as _:
        run([], path="047err_abs_local")
        assert False

def test_two_manifest_048():
    d = "048err_two_manifest"
    # Create manifest.py dynamically so that you can clone the
    # repo on windows/macosx
    shutil.copy(d + "/Manifest.py", d + "/manifest.py")
    with pytest.raises(SystemExit) as _:
        run([], path=d)
    os.remove(d + "/manifest.py")

def test_no_manifest_049():
    with pytest.raises(SystemExit) as _:
        run([], path="049err_no_manifest")

def test_configparser_bad_descr():
    # More like a unittest
    with pytest.raises(ValueError) as _:
        _ = ConfigParser(description=1)

def test_configparser_dup_option():
    p = ConfigParser()
    p.add_option("a", type={})
    with pytest.raises(ValueError) as _:
        p.add_option("a", type=0)

def test_configparser_bad_option():
    p = ConfigParser()
    with pytest.raises(ValueError) as _:
        p.add_option("a", type=0, unknown=True)

def test_configparser_key():
    p = ConfigParser()
    p.add_option("a", type={})
    p.add_allowed_key("a", key="k")
    with pytest.raises(ValueError) as _:
        p.add_allowed_key("a", key=1)

def test_configparser_bad_type():
    # More like a unittest
    p = ConfigParser()
    with pytest.raises(RuntimeError) as _:
        p.add_type("a", type_new=[])

def test_configparser_unexpected_key():
    # More like a unittest
    p = ConfigParser()
    with pytest.raises(RuntimeError) as _:
        p.add_allowed_key("a", key="k1")
    p.add_option("a", type=[])
    with pytest.raises(RuntimeError) as _:
        p.add_allowed_key("a", key="k")

def test_err_manifest_type_050():
    with pytest.raises(SystemExit) as _:
        run([], path="050err_manifest_type")

def test_err_manifest_key_051():
    with pytest.raises(SystemExit) as _:
        run([], path="051err_manifest_key")

def test_svlog_parser_052():
    run_compare(path="052svlog_parser")

def test_err_vlog_include_077():
    with pytest.raises(SystemExit) as _:
        run([], path="077err_vlg_include")

def test_err_vlog_define_078():
    with pytest.raises(SystemExit) as _:
        run([], path="078err_vlg_define")

def test_err_vlog_no_macro_079():
    run_compare(path="079err_vlg_macro")

def test_err_vlog_recursion_080():
    with pytest.raises(SystemExit) as _:
        run([], path="080err_vlg_recursion")

def test_vlog_ifdef_elsif_else_081():
    run_compare(path="081vlog_ifdef_elsif_else")

def test_dep_level_053():
    run(['list-files'], path="053vlog_dep_level")
    run(['list-files', '--delimiter', ','], path="053vlog_dep_level")
    run(['list-files', '--reverse'], path="053vlog_dep_level")
    run(['list-files', '--top', 'level2'], path="053vlog_dep_level")

def test_modelsim_windows_057():
    assert hdlmake.util.shell.check_windows_tools() is False
    run_compare(path="057msim_windows", my_os='windows')

def test_nosim_tool_063():
    with pytest.raises(SystemExit) as _:
        run([], path="063err_nosim_tool")

def test_err_action_064():
    with pytest.raises(SystemExit) as _:
        run([], path="064err_action")

def test_err_loglevel_002():
    with pytest.raises(SystemExit) as _:
        run(['--log', 'unknown', 'makefile'], path="002msim")

def test_err_noaction_002():
    run(['--log', 'warning'], path="002msim")
    os.remove("002msim/Makefile")

def test_all_files_002():
    run(['-a', 'makefile'], path="002msim")
    os.remove("002msim/Makefile")

def test_err_sim_top_006():
    with pytest.raises(SystemExit) as _:
        run([], path="066err_sim_top")

def test_err_syn_dev_067():
    with pytest.raises(SystemExit) as _:
        run([], path="067err_syndev")
        assert False

def test_err_syn_grade_068():
    with pytest.raises(SystemExit) as _:
        run([], path="068err_syngrade")
        assert False

def test_err_syn_package_069():
    with pytest.raises(SystemExit) as _:
        run([], path="069err_synpackage")
        assert False

def test_err_syn_top_070():
    run_compare(path="070err_syntop")

def test_extra_modules_076():
    run_compare(path="076extra_modules")

def test_err_syntool_084():
    with pytest.raises(SystemExit) as _:
        run([], path="084bad_syn")
        assert False

def test_err_simtool_085():
    with pytest.raises(SystemExit) as _:
        run([], path="085bad_sim")
        assert False

def test_err_ise_no_family_086():
    with pytest.raises(SystemExit) as _:
        run([], path="086ise_no_family")
        assert False

def test_many_modules_087():
    run_compare(path="087many_modules")

def test_file_abs_088():
    run_compare(path="088bad_file_abs")

def test_err_missing_file_089():
    with pytest.raises(SystemExit) as _:
        run([], path="089missing_file")
        assert False

def test_err_missing_module_090():
    with pytest.raises(SystemExit) as _:
        run([], path="090missing_module")
        assert False

def test_library_091():
    run_compare(path="091library")

def test_err_filetype_092():
    with pytest.raises(SystemExit) as _:
        run([], path="092bad_filetype")
        assert False

def test_multi_sat_093():
    with Config(path="093multi_sat"):
        hdlmake.main.hdlmake([])
        # Output is not deterministic
        ref1 = open('Makefile.ref1', 'r').read()
        ref2 = open('Makefile.ref2', 'r').read()
        out = open('Makefile', 'r').read()
        assert out == ref1 or out == ref2
        os.remove('Makefile')

def test_sys_package_097():
    run_compare_xilinx(path="097sys_package")

def test_vhdl_libraries_ise_113():
    run_compare(path="113_ise_libraries")

def test_vhdl_libraries_liberosoc_114():
    run_compare(path="114_libero_libraries")

def test_vhdl_libraries_GHDLSyn_115():
    run_compare_filter(filter="TOOL_PATH", path="115_ghdlsyn_libraries")

def test_vhdl_parser_116():
    run_compare(path="116vhdl_parser")

def test_linerosoc_project_opt_117():
    run_compare(path="117libero_project")

def test_wildcards_118():
    run_compare(path="118wildcards")

def test_order_119():
    run_compare(path="119order")

def test_explicit_dep_120():
    run_compare(path="120explicit_dep")

def test_explicit_err_121():
    run_compare(path="121explicit_err")

def test_quartus_qip_122():
    run_compare(path="122quartus_qip")

def test_explicit_dependency_lib_123():
    run_compare(path="123expl_dep_lib")

def test_explicit_required_lib_124():
    run_compare(path="124expl_req_lib")

def test_arch_in_separate_file_125():
    run_compare(path="125arch_in_separate_file")

def test_package_body_in_separate_file_126():
    run_compare(path="126package_body_in_separate_file")

def test_arch_in_separate_file_127():
    run_compare(path="127arch_in_separate_file")

def test_nvc_128():
    run_compare(path="128nvc")

def test_specify_top_library_129():
    run_compare(path="129specify_top_library")

def test_specify_top_library_explict_130():
    run_compare(path="130specify_top_library_explicit")

def test_vivado_jobs_133():
    run_compare(path="133vivado_jobs")

def test_gowin_134():
    run_compare(path="134gowin")

@pytest.mark.xfail
def test_xfail():
    """This is a self-consistency test: the test is known to fail"""
    run_compare(path="011xfail")

def test_xfail_cleanup():
    """Cleanup after test_xfail"""
    os.remove("011xfail/Makefile")
