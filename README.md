# Sparta International 
Calcualtes the money owed by each person for a round of golf using Sparta Rules.
It could be the only golf gambling game that requires recursion to calcuate the money.

## The Math
10 players
.10 per hole
.50 per 9
1.00 total
Everyone plays everyone
One guy losses every hole

.90 (lost to 9 players) x 18 = 16.20
.50 x 9 = 4.50 x 2 = 9.00
1.00 x 9 players = 9.00
Total:  34.20

34.20/18 = 1.90 max loss per player with 10 total players

15 players
14 x .10 x 18 = 25.20
.50 x 14 = 7.00 x 2 = 14.00
1.00 x 14  = 14 for total
53.20/18  = 2.95 per hole max
