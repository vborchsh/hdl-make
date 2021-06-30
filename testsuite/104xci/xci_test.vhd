library ieee;
use ieee.std_logic_1164.all;

entity xci_test is
  port(
    clk_i: in std_logic;
    data_o: out std_logic_vector(63 downto 0)
    );
end xci_test;

architecture xci_test_arch of xci_test is
begin
  cmp_vio_din2_w64_dout2_w64 : entity work.vio_din2_w64_dout2_w64
  port map (
    clk        => clk_i,
    probe_in0  => (others => '0'),
    probe_in1  => (others => '0'),
    probe_out0 => data_o,
    probe_out1 => open
    );
end xci_test_arch;
