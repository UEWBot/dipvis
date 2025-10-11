This module provide classes to score a Diplomacy game.

The game is represented by a GameState object, which provides methods to query the state of the game.
With the current interface for GameState, certain restrictions are imposed on the scoring:
- all powers are equal. i.e. if the centre counts for two powers were swapped, the score would also be swapped
- all supply centres are equal. GameState provides counts of supply centres owned, no details of which centres they are.
- only powers matter, not players.

To add a new scoring system, create a new class derived from the GameScoringSystem abstract base class. You will need
to implement two methods - __init__() and scores(). You may also want to override description().
__init__() must set self.name. If a Great Power's score can change after they have been eliminated (e.g. if a player
solos the game) then it must also set self.dead_score_can_change to True.
scores() is passed a GameState and must return a dict, indexed by great power, of floats. It should ensure that the
highest score is added to the dict first (possibly using _sorted_scores()).
By default, the class docstring will be used for the description property, so it should provide full details of the
scoring system.

Ideally, the scoring system code should avoid hard-coding things like number of powers or supply centres, so as to be
usable for variants. To this end, it may want to use TOTAL_SCS, WINNING_SCS, and FIRST_YEAR from
diplomacy.values.diplomacy_values.
