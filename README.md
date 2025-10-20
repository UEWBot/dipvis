# Diplomacy Tournament Visualiser

Inspired by the TV coverage for sports events, Dipvis was originally designed to
provide something analogous for Diplomacy tournaments. The goal of Dipvis is to
allow spectators (and players) to follow the tournament. However, Dipvis has evolved 
to be mostly a Tournament Director aid - seeding boards, scoring tournaments,
etc. The live tracking of scores is also used a lot by players at tournaments.

This project has been used for several tournaments already at https://diplomacytv.com/

This project was created using [python](https://www.python.org/) code, HTML, 
and [Django](https://www.djangoproject.com/) templates.

You can:
- create tournaments, consisting of a number of rounds 
- add players to games
- track game, round, and tournament progress
- it supports many scoring systems and also team rounds

Dipvis will automatically generate "commentary" on things related to player history and
can read from the World Diplomacy Database and/or World Diplomacy Reference if given:
- appropriate player id
- tournament history
- game progress

When viewing a tournament, the window can be subdivided into frames and each 
frame can show an aspect of a game, round, or tournament.

## Instructions

Can be found [here](https://github.com/UEWBot/dipvis/blob/master/INSTRUCTIONS)

This section contains useful information for setting up Dipvis for a game.

## User guide

Can be found [here](https://github.com/UEWBot/dipvis/blob/master/TD_USER_GUIDE)

This section contains a manual that goes into more detail about how to track the game
and some basic concepts about the game. It also holds some do's and don'ts regarding
how Dipvis should be used.

## Setup for testing

1. Ensure Python is installed.

2. Install the requirements.
    - `pip install -r requirements.txt`

3. Proceed to testing.

## Testing

Can be found [here](https://github.com/UEWBot/dipvis/blob/master/TESTING)

## Licensing

[License](https://github.com/UEWBot/dipvis/blob/master/LICENSE)
