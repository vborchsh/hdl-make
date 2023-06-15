library ieee;
use ieee.std_logic_1164.all;

entity xcix_test is
  port(
    clk_i: in std_logic;
    data_o: out std_logic_vector(63 downto 0)
    );
end xcix_test;

architecture xcix_test_arch of xcix_test is
begin
  --  Incomplete...
  cmp_adc_memory : entity work.adc_memory
  port map (
    clk_a      => clk_i,
    clk_b      => clk_i
    );
end xcix_test_arch;
