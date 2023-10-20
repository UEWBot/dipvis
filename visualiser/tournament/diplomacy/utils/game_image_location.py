from pathlib import Path

def game_image_location(instance, filename):
    """
    Function that determines where to store the file.
    """
    return Path('games/starting_positions', filename)
