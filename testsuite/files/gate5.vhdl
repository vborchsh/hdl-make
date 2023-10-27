entity gate5 is
  port (i : in bit;
        o : out bit);
end gate5;

library work;
use work.pkg5.all;

architecture behav of gate5 is
begin
  if c_invert then
    o <= not i;
  else
    o <= i;

end behav;
