import sqlite3
from pathlib import Path
import functools

local_path = Path("data")
database_path = local_path / Path("Enhanced-AMQ-Database.db")


def run_sql_command(cursor, sql_command, data=None):

    """
    Run the SQL command with nice looking print when failed (no)
    """

    try:
        if data is not None:
            cursor.execute(sql_command, data)
        else:
            cursor.execute(sql_command)

        record = cursor.fetchall()

        return record

    except sqlite3.Error as error:

        if data is not None:
            for param in data:
                if type(param) == str:
                    sql_command = sql_command.replace("?", '"' + str(param) + '"', 1)
                else:
                    sql_command = sql_command.replace("?", str(param), 1)

        print(
            "\nError while running this command: \n",
            sql_command,
            "\n",
            error,
            "\nData: ",
            data,
            "\n",
        )
        return None


def connect_to_database(database_path):

    """
    Connect to the database and return the connection's cursor
    """

    try:
        sqliteConnection = sqlite3.connect(database_path)
        cursor = sqliteConnection.cursor()
        return cursor
    except sqlite3.Error as error:
        print("\n", error, "\n")
        exit(0)


def get_anime_info_from_anime_id(cursor, anime_id):

    """
    Return the content of animes table for that anime ID
    {
        annId
        animeExpandName
        animeJPName
    }
    """

    command = "SELECT * FROM animes WHERE annId == ?;"
    anime = run_sql_command(cursor, command, [anime_id])[0]
    return {"annId": anime[0], "animeExpandName": anime[1], "animeJPName": anime[2]}


def get_songs_ID_from_anime_ID(cursor, anime_id):

    """
    Return the list of songs ID linked to the anime ID
    """

    command = "SELECT song_id FROM link_anime_song WHERE anime_id == ?;"
    return {song[0] for song in run_sql_command(cursor, command, [anime_id])}


def get_song_info_from_song_ID(cursor, song_id):

    """
    Return the content of songs table for that song id
    {
        songId
        annSongId
        songType
        songNumber
        songName
        songArtist
        HQ
        MQ
        audio
    }
    """

    command = "SELECT * FROM songs WHERE id == ?;"
    song = run_sql_command(cursor, command, [song_id])[0]
    return {
        "songId": song[0],
        "annSongId": song[1],
        "songType": song[2],
        "songNumber": song[3],
        "songName": song[4],
        "songArtist": song[5],
        "HQ": song[6],
        "MQ": song[7],
        "audio": song[8],
    }


def get_song_artists_from_song_ID(cursor, song_id):

    """
    Return the list of (artists ID, id_of_set_of_artists) for that song id
    """

    command = "SELECT artist_id, artist_alt_members_id FROM link_song_artist WHERE song_id == ?;"
    return run_sql_command(cursor, command, [song_id])


def get_songs_with_artist_ID(cursor, artist_id):

    """
    Return every song ID that has the artist in it
    """

    command = "SELECT song_id FROM link_song_artist WHERE artist_id == ?;"
    return {song[0] for song in run_sql_command(cursor, command, [artist_id])}


def is_artist_a_group(cursor, artist_id):

    """
    Return True if the artist is a group
    Return False if not
    """

    command = "SELECT * FROM link_artist_group WHERE group_id == ?;"
    return True if run_sql_command(cursor, command, [artist_id]) else False


def get_members_list(cursor, artist_id, set_id=-1):

    """
    Return the list of artists presents in the couple (artist_id, artist_alt_members_id)
    I.E:    if set_id == -1: return every member for every version of the group
            else: list the members in that version of the group
    """
    if is_artist_a_group(cursor, artist_id):
        if set_id == -1:
            command = "SELECT artist_id FROM link_artist_group WHERE group_id == ?;"
            return {
                artist[0] for artist in run_sql_command(cursor, command, [artist_id])
            }
        else:
            command = "SELECT artist_id FROM link_artist_group WHERE group_id == ? AND group_alt_members_id == ?;"
            return {
                artist[0]
                for artist in run_sql_command(cursor, command, [artist_id, set_id])
            }
    else:
        return []


def get_groups_list(cursor, artist_id):

    """
    Return the list of groups the artist is in
    """

    command = "SELECT group_id, group_alt_members_id FROM link_artist_group WHERE artist_id == ?;"
    return run_sql_command(cursor, command, [artist_id])


def get_artist_names_from_artist_id(cursor, artist_id):

    """
    Return the list of names linked to the artist id
    """

    command = "SELECT name FROM artist_alt_names WHERE artist_id == ?;"
    return {name[0] for name in run_sql_command(cursor, command, [artist_id])}


def get_all_artistIds(cursor):

    """
    Return the ID of every artist in the DB
    """

    command = "SELECT DISTINCT id FROM artists;"
    return run_sql_command(cursor, command)


def get_all_annIDs(cursor):

    """
    Return every annID in the DB
    """

    command = "SELECT DISTINCT annId from animes;"
    return run_sql_command(cursor, command)


def get_all_songIds(cursor):
    """
    Return every songId in the DB
    """

    command = "SELECT DISTINCT id from songs;"
    return run_sql_command(cursor, command)


@functools.lru_cache(maxsize=1)
def extract_song_database():

    """
    Extract the song database
    """

    command = """
    SELECT animes.annId, animes.animeExpandName, animes.animeJPName, animes.animeENName, animes.animeVintage, animes.animeType, songs.annSongId, songs.songType, songs.songNumber, 
    songs.songName, songs.songArtist, songs.songDifficulty, songs.HQ, songs.MQ, songs.audio, group_concat(link_song_artist.artist_id) 
    AS artists_ids, group_concat(link_song_artist.artist_line_up_id) AS artists_ids_set, group_concat(link_song_composer.composer_id) as composer_ids, group_concat(link_song_arranger.arranger_id) as arranger_ids
    FROM animes
    INNER JOIN songs ON animes.annId = songs.annId
    LEFT JOIN link_song_artist ON songs.id = link_song_artist.song_id
    LEFT JOIN link_song_composer ON songs.id = link_song_composer.song_id
    LEFT JOIN link_song_arranger ON songs.id = link_song_arranger.song_id
    GROUP BY songs.id;
    """
    cursor = connect_to_database(database_path)
    song_database = []
    for song in run_sql_command(cursor, command):

        artist_ids = []
        if song[15]:
            for id, sets in zip(song[15].split(","), song[16].split(",")):
                if int(id) in [int(temp[0]) for temp in artist_ids]:
                    continue
                artist_ids.append([int(id), int(sets)])

        composer_ids = []
        if song[17]:
            for id in song[17].split(","):
                if int(id) in composer_ids:
                    continue
                composer_ids.append(int(id))

        arranger_ids = []
        if song[18]:
            for id in song[18].split(","):
                if int(id) in arranger_ids:
                    continue
                arranger_ids.append(int(id))

        song_database.append(
            {
                "annId": song[0],
                "animeExpandName": song[1],
                "animeJPName": song[2],
                "animeENName": song[3],
                "animeVintage": song[4],
                "animeType": song[5],
                "annSongId": song[6],
                "songType": song[7],
                "songNumber": song[8],
                "songName": song[9],
                "songArtist": song[10],
                "songDifficulty": song[11],
                "HQ": song[12],
                "MQ": song[13],
                "audio": song[14],
                "artists_ids": artist_ids,
                "composers_ids": composer_ids,
                "arrangers_ids": arranger_ids,
            }
        )

    return song_database


@functools.lru_cache(maxsize=1)
def extract_artist_database():

    """
    Extract the artist database
    """

    cursor = connect_to_database(database_path)
    artist_database = {}

    extract_basic_info = """
    SELECT artists.id, group_concat(artist_names.name, "\$") AS names, artists.vocalist, artists.composer
    FROM artists
    LEFT JOIN artist_names ON artists.id = artist_names.artist_id
    GROUP BY artists.id
    """

    basic_info = run_sql_command(cursor, extract_basic_info)

    extract_artist_groups = """
    SELECT artists.id, group_concat(link_artist_group.group_id) AS groups, group_concat(link_artist_group.group_line_up_id) as groups_line_up
    FROM artists
    LEFT JOIN link_artist_group ON artists.id = link_artist_group.member_id
	GROUP BY artists.id
    """

    artist_groups = run_sql_command(cursor, extract_artist_groups)

    extract_group_members = """
    SELECT artists.id, group_concat(link_artist_group.member_id) AS members, group_concat(link_artist_group.member_line_up_id) as members_line_up
    FROM artists
    LEFT JOIN link_artist_group ON artists.id = link_artist_group.group_id
	GROUP BY artists.id
    """

    group_members = run_sql_command(cursor, extract_group_members)

    if len(basic_info) != len(artist_groups) or len(basic_info) != len(group_members):
        print("ERROR EXTRACTING ARTIST DATABASE")
        return {}

    artist_database = {}
    for info, groups in zip(basic_info, artist_groups):

        if info[0] != groups[0]:
            print("ERROR EXTRACTING ARTIST DATABASE")
            return {}

        artist_database[str(info[0])] = {
            "names": info[1].split("\$"),
            "groups": [
                [group, int(line_up)]
                for group, line_up in zip(groups[1].split(","), groups[2].split(","))
            ]
            if groups[1]
            else [],
            "members": [],
            "vocalist": True if info[2] else False,
            "composer": True if info[3] else False,
        }

    for info, members in zip(basic_info, group_members):

        if info[0] != members[0]:
            print("ERROR EXTRACTING ARTIST DATABASE")
            return {}

        if not members[1]:
            continue

        for member_id, line_up in zip(members[1].split(","), members[2].split(",")):
            member = artist_database[str(member_id)]
            for group_id, group_line_up in member["groups"]:
                if int(group_id) == int(info[0]):
                    while (
                        len(artist_database[str(info[0])]["members"]) <= group_line_up
                    ):
                        artist_database[str(info[0])]["members"].append([])
                    if member_id not in [
                        mid[0]
                        for mid in artist_database[str(info[0])]["members"][
                            group_line_up
                        ]
                    ]:
                        artist_database[str(info[0])]["members"][group_line_up].append(
                            [member_id, int(line_up)]
                        )

    return artist_database
