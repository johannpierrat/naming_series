#!/usr/bin/python2.7

import os
import sys
import re
import webepisode

def get_season_episode(list_ep, ep_num):
    """
    Create the season number from a single episode number
    >>> get_season_episode(100)
    (3, 28)
    """
    season_num = 1
    ep_num_or = ep_num
    try:
        while ep_num >= len(list_ep[season_num]):
            ep_num = ep_num - len(list_ep[season_num])
            season_num += 1
    except KeyError:
        sys.stderr.write("Episode number not in list %d\n" % ep_num_or)
        return None, ep_num_or

    return season_num, ep_num


def get_episode_id(episode_name):
    """
    Extract the episode number and season number from the name
    episode_name -> season_num, episode_num
    Return None if one of those has not been found
    >>> get_episode_id('test_S01E12')
    (1, 12)
    >>> get_episode_id('test season 1 episode 12')
    (1, 12)
    >>> get_episode_id('test 1x12')
    (1, 12)
    """
    season_find = re.compile("(?:s|season)\s*\d+", re.IGNORECASE)
    episode_find = re.compile("(?:e|episode|^)\s*\d+", re.IGNORECASE)
    season_x_episode_find = re.compile("\d+x\d+", re.IGNORECASE)

    season_num = None
    episode_num = None

    for season_found in season_find.findall(episode_name):
        season_num = int(re.findall("\d+", season_found)[0])

    for episode_found in episode_find.findall(episode_name):
        episode_num = int(re.findall("\d+", episode_found)[0])

    for both_found in season_x_episode_find.findall(episode_name):
        season_num = int(re.findall("\d+", both_found)[0])
        episode_num = int(re.findall("\d+", both_found)[1])

    return season_num, episode_num

def walk_dir(root_dir):
    serie_name = os.path.basename(root_dir)

    list_episode = webepisode.get_episode_list(serie_name)
    if list_episode is None:
        sys.stderr.write("List episode name was not found for series %s\n"
                         % serie_name)
        return

    for root, dirs, files in os.walk(root_dir):
        for file_ in files:
            season_num, ep_num = get_episode_id(file_)
            if ep_num is None:
                sys.stderr.write("Episode Number is not found for file %s\n"
                                 % os.path.join(root,file_))
                continue
            if season_num is None:
                # When there is no season
                if len(list_episode) == 1:
                    season_num = 1
                else:
                    season_num, _ = get_episode_id(os.path.basename(root))
                    if season_num is None:
                        sys.stderr.write("Season Number is not found for"
                                         " file %s\n"
                                         % os.path.join(root,file_))
                        continue

            _, ext = os.path.splitext(file_)
            try:
                new_file = ("%s -S%02dE%02d- %s%s"
                            % (re.sub("_", " ",serie_name),
                               season_num,
                               ep_num,
                               list_episode[season_num][ep_num],
                               ext))
                new_file = re.sub("/", "-", new_file)
            except KeyError:
                sys.stderr.write("season %d, episode %d\n"
                                 % (season_num, ep_num))
                sys.stderr.write("Cannot find title for file %s\n"
                                 % file_)
                continue
            print("Moving file %s" % os.path.join(root, file_))
            print("         -> %s" % os.path.join(root, new_file))
            os.rename(os.path.join(root, file_), os.path.join(root, new_file))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        walk_dir(sys.argv[1])
    else:
        print "Usage: %s serie_dir" % sys.argv[0]
