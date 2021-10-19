import json
import config_edge_cases
from pathlib import Path

song_database = Path("../../app/data/expand_mapping.json")
artist_database = Path("../../app/data/artist_mapping.json")
results_output_path = Path("../../app/data/")

results_output_path.mkdir(parents=False, exist_ok=True)

with open(song_database, encoding="utf-8") as json_file:
    song_database = json.load(json_file)

with open(artist_database, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)

same_name_edge_case = config_edge_cases.same_name_edge_case
same_group_different_artists = config_edge_cases.same_group_different_artists


def get_artist_id(artist_ids_mapping, artist):

    for id in artist_ids_mapping.keys():
        for artist_alt_name in artist_ids_mapping[id]["names"]:
            if artist_alt_name == artist:
                return id
    print(artist, "not found... adding it")
    id = len(artist_ids_mapping.keys())
    artist_ids_mapping[id] = {"names": [artist], "groups": [], "members": []}
    return id


def update_song(song_database, song_id, new_artist, artist_id):

    flag_valid = False
    for anime in song_database:
        for song in anime["songs"]:
            if song["annSongId"] == song_id:
                flag_valid = True
                new_artist_ids = []
                for artist in song["artist_ids"]:
                    flag_to_update = False
                    for artist_name in artist_database[str(artist[0])]["names"]:
                        if artist_name in new_artist["artist_name"]:
                            flag_to_update = True
                    if flag_to_update:
                        if new_artist["members"] != []:
                            new_artist_ids.append([artist_id, 0])
                        else:
                            new_artist_ids.append([artist_id, -1])
                    else:
                        new_artist_ids.append(artist)
                song["artist_ids"] = new_artist_ids
    if not flag_valid:
        print("\n", "WARNING: Song", song_id, "NOT FOUND: WARNING", "\n")


def add_new_artist(artist_database, new_artist):

    last_id = int(list(artist_database.keys())[-1])
    artist_database[last_id + 1] = {
        "names": new_artist["artist_name"],
        "groups": [],
        "members": [],
    }
    if len(new_artist["members"]) > 0:
        id_list = []
        for artist in new_artist["members"]:
            id_list.append(get_artist_id(artist_database, artist))
        artist_database[last_id + 1]["members"].append(id_list)

    return last_id + 1


for edge_case in same_name_edge_case:

    new_id = add_new_artist(artist_database, edge_case["new_artist"])
    for song_id in edge_case["linked_song"]:
        update_song(song_database, song_id, edge_case["new_artist"], new_id)

for edge_case in same_group_different_artists:
    flag_valid = False
    group_id = get_artist_id(artist_database, edge_case["group"])
    for i, alt_config in enumerate(edge_case["alternate_configs"]):
        id_list = []
        for artist in alt_config["members"]:
            id_list.append(get_artist_id(artist_database, artist))
        artist_database[group_id]["members"].append(id_list)
        for anime in song_database:
            for song in anime["songs"]:
                if song["annSongId"] in alt_config["linked_song"] or (
                    song["annSongId"] == -1
                    and edge_case["group"] in song["artist"]
                    and song["name"] in alt_config["linked_song"]
                ):
                    flag_valid = True
                    for artist in song["artist_ids"]:
                        if int(artist[0]) == int(group_id):
                            artist[1] = i + 1
    if not flag_valid:
        print("\n", "WARNING: Song", song_id, "NOT FOUND: WARNING", "\n")


with open(
    results_output_path / Path("artist_mapping.json"), "w", encoding="utf-8"
) as outfile:
    json.dump(artist_database, outfile)

with open(
    results_output_path / Path("expand_mapping.json"), "w", encoding="utf-8"
) as outfile:
    json.dump(song_database, outfile)

