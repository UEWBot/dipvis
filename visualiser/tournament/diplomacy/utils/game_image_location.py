import os

def game_image_location(instance, filename):
    """
    Function that determines where to store the file.
    """
    return os.path.join('games', 'starting_positions', filename)