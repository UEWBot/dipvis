# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2020 Chris Brand
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This module contains utility functions for scoring system classes.
"""


def _sorted_scores(scores, state):
    """
    Sorts a dict of scores so that they will be iterated in GreatPower order.

    Returns the sorted dict.
    """
    return {k: scores[k] for k in state.all_powers()}


def _normalise_scores(scores, total=100.0):
    """
    Adjusts all the scores to sum to total while keeping the same ratios.

    scores should be a dict, indexed by power, of raw scores.
    """
    old_total = sum(scores.values())
    for p in scores.keys():
        scores[p] = scores[p] * total / old_total


def _adjust_rank_score(centre_counts, rank_points):
    """
    Allocate points for rank

    Takes a list of (power, centre count) 2-tuples for one year of one game,
    ordered highest-to-lowest, and a list of ranking points for positions,
    ordered from first place to last.
    Returns a list of ranking points for positions, ordered to correspond to
    the centre counts, having made adjustments for any tied positions.
    Where two or more powers have the same number of SCs, the ranking points
    for their positions are shared evenly between them.
    """
    if not rank_points:
        # The rest of them get zero points
        return [] + [0.0] * len(centre_counts)
    # Work with a copy of rank_points
    rank_pts = rank_points.copy()
    # First count up how many powers tied at the top
    i = 0
    count = 0
    points = 0
    scs = centre_counts[0][1]
    while (i < len(centre_counts)) and (centre_counts[i][1] == scs):
        count += 1
        if i < len(rank_pts):
            points += rank_pts[i]
        i += 1
    # Now share the points between those tied players
    for j in range(0, i):
        if j < len(rank_pts):
            rank_pts[j] = points / count
        else:
            rank_pts.append(points / count)
    # And recursively continue
    return rank_pts[0:i] + _adjust_rank_score(centre_counts[i:],
                                              rank_pts[i:])


def _adjust_rank_score_lower(centre_counts, rank_points):
    """
    Allocate points for rank

    Takes a list of (power, centre count) 2-tuples for one year of one game,
    ordered highest-to-lowest, and a list of ranking points for positions,
    ordered from first place to last.
    Returns a list of ranking points for positions, ordered to correspond to
    the centre counts, having made adjustments for any tied positions.
    Where two or more powers have the same number of SCs, all tied players
    get the lower bonus points.
    """
    if not rank_points:
        # The rest of them get zero points
        return [] + [0.0] * len(centre_counts)
    # Work with a copy of rank_points
    rank_pts = rank_points.copy()
    # First identify powers tied at the top
    i = 0
    points = 0
    scs = centre_counts[0][1]
    while (i < len(centre_counts)) and (centre_counts[i][1] == scs):
        if i < len(rank_pts):
            points = rank_pts[i]
        else:
            points = 0
        i += 1
    # Now give the points to those tied players
    for j in range(0, i):
        if j < len(rank_pts):
            rank_pts[j] = points
        else:
            rank_pts.append(points)
    # And recursively continue
    return rank_pts[0:i] + _adjust_rank_score_lower(centre_counts[i:],
                                                    rank_pts[i:])


def _adjust_rank_score_lower_special(centre_counts, rank_points, two_way_rank_points):
    """
    Allocate points for rank

    Takes a list of (power, centre count) 2-tuples for one year of one game,
    ordered highest-to-lowest, and a list of ranking points for positions,
    ordered from first place to last.
    Also takes a second list of ranking points for positions, also
    ordered from first place to last, that is used if exactly two players are
    tied for a given rank.
    Returns a list of ranking points for positions, ordered to correspond to
    the centre counts, having made adjustments for any tied positions.
    Where three or more powers have the same number of SCs, all tied players
    get the lower bonus points.
    """
    if not rank_points:
        # The rest of them get zero points
        return [] + [0.0] * len(centre_counts)
    # Work with copies of rank_points and two_way_rank_points
    rank_pts = rank_points.copy()
    two_way_rank_pts = two_way_rank_points.copy()
    # First identify powers tied at the top
    i = 0
    points = 0
    scs = centre_counts[0][1]
    while (i < len(centre_counts)) and (centre_counts[i][1] == scs):
        if i < len(rank_pts):
            points = rank_pts[i]
        else:
            points = 0
        i += 1
    # If exactly two players are tied for the rank, use the alternate table
    if i == 2:
        if len(two_way_rank_pts):
            points = two_way_rank_pts[0]
        else:
            points = 0
    # Now give the points to those tied players
    for j in range(0, i):
        if j < len(rank_pts):
            rank_pts[j] = points
        else:
            rank_pts.append(points)
    # And recursively continue
    return rank_pts[0:i] + _adjust_rank_score_lower_special(centre_counts[i:],
                                                            rank_pts[i:],
                                                            two_way_rank_pts[i:])
