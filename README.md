# Diplomacy Tournament Visualiser

If you are running a Diplomacy tournament, there's a whole lot of things that you
need to do, including:
- registering players, and tracking who has paid any fees
- tracking who is actually there to play each round
- assigning players to games
- recording how each game ended
- scoring individual games
- combining game scores to calculate tournament scores

Dipvis supports all the above.

Inspired by the TV coverage for sports events, Dipvis was originally designed to
provide something analogous for Diplomacy tournaments. The goal of Dipvis was to
allow spectators (and players) to follow the tournament. However, Dipvis has evolved 
to be mostly a Tournament Director aid - seeding boards, scoring tournaments,
etc. The live tracking of scores is also used a lot by players at tournaments.

This project has been used for several tournaments already at https://diplomacytv.com/

This project uses [python](https://www.python.org/) code, HTML, 
and [Django](https://www.djangoproject.com/) templates.

You can:
- create tournaments, consisting of a number of rounds 
- register players and record who is present to play each round
- add players to games
- track game, round, and tournament progress
- calculate player scores (using many scoring systems) and team scores

Dipvis will automatically generate "commentary" on things related to player history and
can read from the World Diplomacy Reference and/or World Diplomacy Database if given:
- appropriate player id
- tournament history
- game progress

When viewing a tournament, the window can be subdivided into frames and each 
frame can show an aspect of a game, round, or tournament.

## Instructions

Can be found [here](https://github.com/UEWBot/dipvis/blob/master/INSTRUCTIONS)

This section contains useful information for setting up Dipvis for a tournament.

## User guide

Can be found [here](https://github.com/UEWBot/dipvis/blob/master/TD_USER_GUIDE)

This section contains a manual that goes into more detail about how to track the tournament
and some basic concepts about the tournament. It also holds some do's and don'ts regarding
how Dipvis should be used.

## Setup for testing

1. Ensure Python is installed.

2. Install the requirements.
    - `pip install -r requirements.txt`

3. Proceed to testing.

## Testing

Can be found [here](https://github.com/UEWBot/dipvis/blob/master/TESTING)

## Contributions

Contributions are very welcome. There's a list of issues at https://github.com/UEWBot/dipvis/issues
- the vast majority are enhancement ideas rather than bugfixes. The test suite is quite extensive with
good coverage, so you can be fairly confident that breaking changes will be picked up by the tests.
The code does need quite a lot of cleanup. It started out as a small project but has grown sigificantly.
Issues are mostly catagorised by type of issue (bug, question, enhancement), part of the codebase
(scoring, user interface, board seeding, player background), and others (techical debt, good first
issue). For a lot of issues, experience of a Diplomacy tournament or at least having played the game
would be useful, but there are a lot of issues where knowledge of Django or python are more significant.
As with most open source projects, there's plenty of room for improvement in documentation and testing,
too. Feel free to comment on existing issues, or to volunteer to work to address one.

## Licensing

[License](https://github.com/UEWBot/dipvis/blob/master/LICENSE)
