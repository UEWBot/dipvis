from django.db import models

SPRING = 'S'
FALL = 'F'
SEASONS = (
    (SPRING, 'spring'),
    (FALL, 'fall'),
)

class GreatPower(models.Model):
    """
    One of the seven great powers that can be played
    """
    name = models.CharField(max_length=20, unique=True)
    abbreviation = models.CharField(max_length=1, unique=True)

class Player(models.Model):
    """
    A person who played Diplomacy
    """
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    wdd_player_id = models.PositiveIntegerField(unique=True)

class Tournament(models.Model):
    """
    A Diplomacy tournament
    """
    name = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()

class Round(models.Model):
    """
    A single round of a tournament
    """
    tournament = models.ForeignKey(Tournament)
    number = models.PositiveSmallIntegerField()

class Game(models.Model):
    """
    A single game of Diplomacy
    """
    name = models.CharField(max_length=20)
    started_at = models.DateTimeField()
    is_finished = models.BooleanField(default=False)
    is_top_board = models.BooleanField(default=False)
    the_round = models.ForeignKey(Round, verbose_name='round')

class GamePlayer(models.Model):
    """
    A person who played a Great Power in a Game
    """
    player = models.ForeignKey(Player)
    game = models.ForeignKey(Game)
    power = models.ForeignKey(GreatPower)
    first_year = models.PositiveSmallIntegerField(default=1)
    first_season = models.CharField(max_length=1, choices=SEASONS, default=SPRING)
    last_year = models.PositiveSmallIntegerField(blank=True)
    last_season = models.CharField(max_length=1, choices=SEASONS, blank=True)
    score = models.FloatField(blank=True)

class CentreCount(models.Model):
    """
    The number of centres owned by one power at the end of a given game year
    """
    power = models.ForeignKey(GreatPower)
    game = models.ForeignKey(Game)
    year = models.PositiveSmallIntegerField()
    count = models.PositiveSmallIntegerField()

