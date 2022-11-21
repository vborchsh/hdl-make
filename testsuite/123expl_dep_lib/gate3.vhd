entity gate3 is
  port (i : in bit;
        o : out bit);
end gate3;

architecture behav of gate3 is
begin
  inst: entity mylib.gate 
    port map (i, o);
end behav;
