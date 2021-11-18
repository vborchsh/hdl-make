entity gate3 is
  port (i : in bit;
        o : out bit);
end gate3;

architecture behav of gate3 is
  function f return natural is
  begin
    return 4;
  end;
begin
  inst: entity work.gate 
    port map (i, o);

  process
    function g return natural is
    begin
      return 5;
    end function;
  begin
    wait;
  end process;
end behav;
