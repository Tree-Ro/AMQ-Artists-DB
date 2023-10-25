"""
Convert the mapping in JSON generated by process_artists scripts to an SQL database for production use
"""

import sqlite3
import json
from pathlib import Path

database = Path("../app/data/Enhanced-AMQ-Database.db")
nerfedDatabase = Path("../app/data/Enhanced-AMQ-Database-Nerfed.db")
song_database_path = Path("../app/data/song_database.json")
artist_database_path = Path("../app/data/artist_database.json")

with open(song_database_path, encoding="utf-8") as json_file:
    song_database = json.load(json_file)
with open(artist_database_path, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)


RESET_DB_SQL = """
PRAGMA foreign_keys = 0;
DROP TABLE IF EXISTS animes;
DROP TABLE IF EXISTS artist_names;
DROP TABLE IF EXISTS artists;
DROP TABLE IF EXISTS groups;
DROP TABLE IF EXISTS link_artist_group;
DROP TABLE IF EXISTS link_song_arranger;
DROP TABLE IF EXISTS link_song_artist;
DROP TABLE IF EXISTS link_song_composer;
DROP TABLE IF EXISTS link_anime_genre;
DROP TABLE IF EXISTS link_anime_tag;
DROP TABLE IF EXISTS link_anime_altNames;
DROP TABLE IF EXISTS songs;
DROP VIEW IF EXISTS artistsNames;
DROP VIEW IF EXISTS artistsMembers;
DROP VIEW IF EXISTS artistsLineUps;
DROP VIEW IF EXISTS artistsGroups;
DROP VIEW IF EXISTS artistsFull;
DROP VIEW IF EXISTS animesFull;
DROP VIEW IF EXISTS songsAnimes;
DROP VIEW IF EXISTS songsArtists;
DROP VIEW IF EXISTS songsComposers;
DROP VIEW IF EXISTS songsArrangers;
DROP VIEW IF EXISTS songsFull;

PRAGMA foreign_keys = 1;

CREATE TABLE animes (
    "annId" INTEGER NOT NULL PRIMARY KEY,
    "animeExpandName" VARCHAR(255) NOT NULL, 
    "animeENName" VARCHAR(255),
    "animeJPName" VARCHAR(255),
    "animeVintage" VARCHAR(255),
    "animeType" VARCHAR(255)
);

CREATE TABLE songs (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "annSongId" INTEGER,
    "annId" INTEGER NOT NULL,
    "songType" INTEGER NOT NULL,
    "songNumber" INTEGER NOT NULL,
    "songName" VARCHAR(255) NOT NULL,
    "songArtist" VARCHAR(255) NOT NULL,
    "songDifficulty" FLOAT,
    "songCategory" VARCHAR(255),
    "HQ" VARCHAR(255),
    "MQ" VARCHAR(255),
    "audio" VARCHAR(255),
    FOREIGN KEY ("annId")
        REFERENCES animes ("annId")
);

CREATE TABLE artists (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "vocalist" BIT NOT NULL,
    "composer" BIT NOT NULL
);

CREATE TABLE groups (
    "artist_id" INTEGER NOT NULL,
    "line_up_id" INTEGER NOT NULL,
    FOREIGN KEY ("artist_id")
        REFERENCES artists ("id"),
    PRIMARY KEY (artist_id, line_up_id)
);

CREATE TABLE artist_names (
    "inserted_order" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "artist_id" INTEGER NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    FOREIGN KEY ("artist_id")
        REFERENCES artist ("id"),
    UNIQUE (artist_id, name)
);

CREATE TABLE link_song_artist (
    "song_id" INTEGER NOT NULL,
    "artist_id" INTEGER NOT NULL,
    "artist_line_up_id" INTEGER NOT NULL,
    FOREIGN KEY ("song_id")
        REFERENCES songs ("id"),
    FOREIGN KEY ("artist_id")
        REFERENCES artists ("id"),
    FOREIGN KEY ("artist_line_up_id")
        REFERENCES groups ("line_up_id"),
    PRIMARY KEY (song_id, artist_id, artist_line_up_id)
);

CREATE TABLE link_song_composer (
    "song_id" INTEGER NOT NULL,
    "composer_id" INTEGER NOT NULL,
    FOREIGN KEY ("song_id")
        REFERENCES songs ("id"),
    FOREIGN KEY ("composer_id")
        REFERENCES artists ("id"),
    PRIMARY KEY (song_id, composer_id)
);

CREATE TABLE link_song_arranger (
    "song_id" INTEGER NOT NULL,
    "arranger_id" INTEGER NOT NULL,
    FOREIGN KEY ("song_id")
        REFERENCES songs ("id"),
    FOREIGN KEY ("arranger_id")
        REFERENCES artists ("id"),
    PRIMARY KEY (song_id, arranger_id)
);

create TABLE link_artist_group (
    "group_id" INTEGER NOT NULL,
    "group_line_up_id" INTEGER NOT NULL,
    "member_id" INTEGER NOT NULL,
    "member_line_up_id" INTEGER NOT NULL,
    FOREIGN KEY ("member_id")
        REFERENCES artists ("id"),
    FOREIGN KEY ("member_line_up_id")
        REFERENCES groups ("line_up_id"),
    FOREIGN KEY ("group_id")
        REFERENCES artists ("artist_id"),
    FOREIGN KEY ("group_line_up_id")
        REFERENCES groups ("line_up_id"),
    PRIMARY KEY (group_id, group_line_up_id, member_id, member_line_up_id)
);


create TABLE link_anime_genre (
    "annId" INTEGER NOT NULL,
    "genre" VARCHAR(255),
    FOREIGN KEY ("annId")
        REFERENCES animes ("annId"),
    PRIMARY KEY (annId, genre)
);


create TABLE link_anime_tag (
    "annId" INTEGER NOT NULL,
    "tag" VARCHAR(255),
    FOREIGN KEY ("annId")
        REFERENCES animes ("annId"),
    PRIMARY KEY (annId, tag)
);

create TABLE link_anime_altNames (
    "annId" INTEGER NOT NULL,
    "name" VARCHAR(255),
    FOREIGN KEY ("annId")
        REFERENCES animes ("annId"),
    PRIMARY KEY (annId, name)
);

CREATE VIEW artistsNames AS 
SELECT orderedNames.inserted_order, artists.id, group_concat(orderedNames.name, "\$") AS names, artists.vocalist, artists.composer
FROM artists
LEFT JOIN (SELECT * FROM artist_names ORDER BY artist_names.inserted_order) AS orderedNames
ON artists.id = orderedNames.artist_id
GROUP BY artists.id;

CREATE VIEW artistsMembers AS 
SELECT artists.id, group_concat(link_artist_group.member_id) AS members, group_concat(link_artist_group.member_line_up_id) as members_line_up 
FROM artists
LEFT JOIN link_artist_group ON artists.id = link_artist_group.group_id 
GROUP BY artists.id;

CREATE VIEW artistsGroups AS 
SELECT artists.id, group_concat(link_artist_group.group_id) AS groups, group_concat(link_artist_group.group_line_up_id) as groups_line_up 
FROM artists 
LEFT JOIN link_artist_group ON artists.id = link_artist_group.member_id 
GROUP BY artists.id;

CREATE VIEW artistsLineUps AS 
SELECT artists.id, artistsNames.names, link_artist_group.group_line_up_id, group_concat(link_artist_group.member_id) AS members, group_concat(link_artist_group.member_line_up_id) as members_line_up 
FROM artists 
LEFT JOIN link_artist_group ON artists.id = link_artist_group.group_id
LEFT JOIN artistsNames ON artists.id = artistsNames.id
GROUP BY artists.id, link_artist_group.group_line_up_id;

CREATE VIEW artistsFull AS
SELECT artistsNames.id, artistsNames.names, artistsNames.vocalist, artistsNames.composer, artistsMembers.members, artistsMembers.members_line_up, artistsGroups.groups, artistsGroups.groups_line_up
FROM artistsNames
INNER JOIN artistsMembers ON artistsNames.id = artistsMembers.id
INNER JOIN artistsGroups ON artistsNames.id = artistsGroups.id;

CREATE VIEW animesFull AS
SELECT animes.annId, animes.animeExpandName, animes.animeJPName, animes.animeENName, group_concat(link_anime_altNames.name, "\$") AS altNames, animes.animeType, animes.animeVintage
FROM animes
LEFT JOIN link_anime_altNames
ON animes.annId = link_anime_altNames.annId
GROUP BY animes.annId;

CREATE VIEW songsAnimes AS
SELECT animesFull.annId, animesFull.animeExpandName, animesFull.animeJPName, animesFull.animeENName, animesFull.altNames, animesFull.animeVintage, animesFull.animeType, 
songs.id as songId, songs.annSongId, songs.songType, songs.songNumber, songs.songName, songs.songArtist, songs.songDifficulty, songs.songCategory, songs.HQ, songs.MQ, songs.audio
FROM animesFull
LEFT JOIN songs ON animesFull.annId = songs.annId;

CREATE VIEW songsArtists AS
SELECT songs.id as songId, group_concat(link_song_artist.artist_id) AS artists, group_concat(link_song_artist.artist_line_up_id) AS artists_line_up
FROM songs 
LEFT JOIN link_song_artist ON songs.id = link_song_artist.song_id
GROUP BY songs.id;

CREATE VIEW songsComposers AS
SELECT songs.id as songId, group_concat(link_song_composer.composer_id) AS composers
FROM songs
LEFT JOIN link_song_composer ON songs.id = link_song_composer.song_id
GROUP BY songs.id;

CREATE VIEW songsArrangers AS
SELECT songs.id as songId, group_concat(link_song_arranger.arranger_id) AS arrangers
FROM songs
LEFT JOIN link_song_arranger ON songs.id = link_song_arranger.song_id
GROUP BY songs.id;

CREATE VIEW songsFull AS
SELECT songsAnimes.annId, songsAnimes.animeExpandName, songsAnimes.animeJPName, songsAnimes.animeENName, songsAnimes.altNames, songsAnimes.animeVintage, songsAnimes.animeType, 
songsAnimes.songId, songsAnimes.annSongId, songsAnimes.songType, songsAnimes.songNumber, songsAnimes.songName, songsAnimes.songArtist, songsArtists.artists, songsArtists.artists_line_up, songsComposers.composers, songsArrangers.arrangers, songsAnimes.songDifficulty, songsAnimes.songCategory, songsAnimes.HQ, songsAnimes.MQ, songsAnimes.audio
FROM songsAnimes
INNER JOIN songsArtists ON songsAnimes.songId = songsArtists.songId
INNER JOIN songsComposers ON songsAnimes.songId = songsComposers.songId
INNER JOIN songsArrangers ON songsAnimes.songId = songsArrangers.songId;
"""

RESET_DB_SQL_NERFED = """
PRAGMA foreign_keys = 0;
DROP TABLE IF EXISTS animes;
DROP TABLE IF EXISTS artist_names;
DROP TABLE IF EXISTS artists;
DROP TABLE IF EXISTS groups;
DROP TABLE IF EXISTS link_artist_group;
DROP TABLE IF EXISTS link_song_arranger;
DROP TABLE IF EXISTS link_song_artist;
DROP TABLE IF EXISTS link_song_composer;
DROP TABLE IF EXISTS link_anime_genre;
DROP TABLE IF EXISTS link_anime_tag;
DROP TABLE IF EXISTS link_anime_altNames;
DROP TABLE IF EXISTS songs;
DROP VIEW IF EXISTS artistsNames;
DROP VIEW IF EXISTS artistsMembers;
DROP VIEW IF EXISTS artistsLineUps;
DROP VIEW IF EXISTS artistsGroups;
DROP VIEW IF EXISTS artistsFull;
DROP VIEW IF EXISTS animesFull;
DROP VIEW IF EXISTS songsAnimes;
DROP VIEW IF EXISTS songsArtists;
DROP VIEW IF EXISTS songsComposers;
DROP VIEW IF EXISTS songsArrangers;
DROP VIEW IF EXISTS songsFull;

PRAGMA foreign_keys = 1;

CREATE TABLE animes (
    "annId" INTEGER NOT NULL PRIMARY KEY,
    "animeExpandName" VARCHAR(255) NOT NULL, 
    "animeENName" VARCHAR(255),
    "animeJPName" VARCHAR(255),
    "animeVintage" VARCHAR(255),
    "animeType" VARCHAR(255)
);

CREATE TABLE songs (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "annSongId" INTEGER,
    "annId" INTEGER NOT NULL,
    "songType" INTEGER NOT NULL,
    "songNumber" INTEGER NOT NULL,
    "songName" VARCHAR(255) NOT NULL,
    "songArtist" VARCHAR(255) NOT NULL,
    "songDifficulty" FLOAT,
    "songCategory" VARCHAR(255),
    FOREIGN KEY ("annId")
        REFERENCES animes ("annId")
);

CREATE TABLE artists (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "vocalist" BIT NOT NULL,
    "composer" BIT NOT NULL
);

CREATE TABLE groups (
    "artist_id" INTEGER NOT NULL,
    "line_up_id" INTEGER NOT NULL,
    FOREIGN KEY ("artist_id")
        REFERENCES artists ("id"),
    PRIMARY KEY (artist_id, line_up_id)
);

CREATE TABLE artist_names (
    "inserted_order" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "artist_id" INTEGER NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    FOREIGN KEY ("artist_id")
        REFERENCES artist ("id"),
    UNIQUE (artist_id, name)
);

CREATE TABLE link_song_artist (
    "song_id" INTEGER NOT NULL,
    "artist_id" INTEGER NOT NULL,
    "artist_line_up_id" INTEGER NOT NULL,
    FOREIGN KEY ("song_id")
        REFERENCES songs ("id"),
    FOREIGN KEY ("artist_id")
        REFERENCES artists ("id"),
    FOREIGN KEY ("artist_line_up_id")
        REFERENCES groups ("line_up_id"),
    PRIMARY KEY (song_id, artist_id, artist_line_up_id)
);

CREATE TABLE link_song_composer (
    "song_id" INTEGER NOT NULL,
    "composer_id" INTEGER NOT NULL,
    FOREIGN KEY ("song_id")
        REFERENCES songs ("id"),
    FOREIGN KEY ("composer_id")
        REFERENCES artists ("id"),
    PRIMARY KEY (song_id, composer_id)
);

CREATE TABLE link_song_arranger (
    "song_id" INTEGER NOT NULL,
    "arranger_id" INTEGER NOT NULL,
    FOREIGN KEY ("song_id")
        REFERENCES songs ("id"),
    FOREIGN KEY ("arranger_id")
        REFERENCES artists ("id"),
    PRIMARY KEY (song_id, arranger_id)
);

create TABLE link_artist_group (
    "group_id" INTEGER NOT NULL,
    "group_line_up_id" INTEGER NOT NULL,
    "member_id" INTEGER NOT NULL,
    "member_line_up_id" INTEGER NOT NULL,
    FOREIGN KEY ("member_id")
        REFERENCES artists ("id"),
    FOREIGN KEY ("member_line_up_id")
        REFERENCES groups ("line_up_id"),
    FOREIGN KEY ("group_id")
        REFERENCES artists ("artist_id"),
    FOREIGN KEY ("group_line_up_id")
        REFERENCES groups ("line_up_id"),
    PRIMARY KEY (group_id, group_line_up_id, member_id, member_line_up_id)
);


create TABLE link_anime_genre (
    "annId" INTEGER NOT NULL,
    "genre" VARCHAR(255),
    FOREIGN KEY ("annId")
        REFERENCES animes ("annId"),
    PRIMARY KEY (annId, genre)
);


create TABLE link_anime_tag (
    "annId" INTEGER NOT NULL,
    "tag" VARCHAR(255),
    FOREIGN KEY ("annId")
        REFERENCES animes ("annId"),
    PRIMARY KEY (annId, tag)
);

create TABLE link_anime_altNames (
    "annId" INTEGER NOT NULL,
    "name" VARCHAR(255),
    FOREIGN KEY ("annId")
        REFERENCES animes ("annId"),
    PRIMARY KEY (annId, name)
);

CREATE VIEW artistsNames AS 
SELECT orderedNames.inserted_order, artists.id, group_concat(orderedNames.name, "\$") AS names, artists.vocalist, artists.composer
FROM artists
LEFT JOIN (SELECT * FROM artist_names ORDER BY artist_names.inserted_order) AS orderedNames
ON artists.id = orderedNames.artist_id
GROUP BY artists.id;

CREATE VIEW artistsMembers AS 
SELECT artists.id, group_concat(link_artist_group.member_id) AS members, group_concat(link_artist_group.member_line_up_id) as members_line_up 
FROM artists
LEFT JOIN link_artist_group ON artists.id = link_artist_group.group_id 
GROUP BY artists.id;

CREATE VIEW artistsGroups AS 
SELECT artists.id, group_concat(link_artist_group.group_id) AS groups, group_concat(link_artist_group.group_line_up_id) as groups_line_up 
FROM artists 
LEFT JOIN link_artist_group ON artists.id = link_artist_group.member_id 
GROUP BY artists.id;

CREATE VIEW artistsLineUps AS 
SELECT artists.id, artistsNames.names, link_artist_group.group_line_up_id, group_concat(link_artist_group.member_id) AS members, group_concat(link_artist_group.member_line_up_id) as members_line_up 
FROM artists 
LEFT JOIN link_artist_group ON artists.id = link_artist_group.group_id
LEFT JOIN artistsNames ON artists.id = artistsNames.id
GROUP BY artists.id, link_artist_group.group_line_up_id;

CREATE VIEW artistsFull AS
SELECT artistsNames.id, artistsNames.names, artistsNames.vocalist, artistsNames.composer, artistsMembers.members, artistsMembers.members_line_up, artistsGroups.groups, artistsGroups.groups_line_up
FROM artistsNames
INNER JOIN artistsMembers ON artistsNames.id = artistsMembers.id
INNER JOIN artistsGroups ON artistsNames.id = artistsGroups.id;

CREATE VIEW animesFull AS
SELECT animes.annId, animes.animeExpandName, animes.animeJPName, animes.animeENName, group_concat(link_anime_altNames.name, "\$") AS altNames, animes.animeType, animes.animeVintage
FROM animes
LEFT JOIN link_anime_altNames
ON animes.annId = link_anime_altNames.annId
GROUP BY animes.annId;

CREATE VIEW songsAnimes AS
SELECT animesFull.annId, animesFull.animeExpandName, animesFull.animeJPName, animesFull.animeENName, animesFull.altNames, animesFull.animeVintage, animesFull.animeType, 
songs.id as songId, songs.annSongId, songs.songType, songs.songNumber, songs.songName, songs.songArtist, songs.songDifficulty, songs.songCategory
FROM animesFull
LEFT JOIN songs ON animesFull.annId = songs.annId;

CREATE VIEW songsArtists AS
SELECT songs.id as songId, group_concat(link_song_artist.artist_id) AS artists, group_concat(link_song_artist.artist_line_up_id) AS artists_line_up
FROM songs 
LEFT JOIN link_song_artist ON songs.id = link_song_artist.song_id
GROUP BY songs.id;

CREATE VIEW songsComposers AS
SELECT songs.id as songId, group_concat(link_song_composer.composer_id) AS composers
FROM songs
LEFT JOIN link_song_composer ON songs.id = link_song_composer.song_id
GROUP BY songs.id;

CREATE VIEW songsArrangers AS
SELECT songs.id as songId, group_concat(link_song_arranger.arranger_id) AS arrangers
FROM songs
LEFT JOIN link_song_arranger ON songs.id = link_song_arranger.song_id
GROUP BY songs.id;

CREATE VIEW songsFull AS
SELECT songsAnimes.annId, songsAnimes.animeExpandName, songsAnimes.animeJPName, songsAnimes.animeENName, songsAnimes.altNames, songsAnimes.animeVintage, songsAnimes.animeType, 
songsAnimes.songId, songsAnimes.annSongId, songsAnimes.songType, songsAnimes.songNumber, songsAnimes.songName, songsAnimes.songArtist, songsArtists.artists, songsArtists.artists_line_up, songsComposers.composers, songsArrangers.arrangers, songsAnimes.songDifficulty, songsAnimes.songCategory
FROM songsAnimes
INNER JOIN songsArtists ON songsAnimes.songId = songsArtists.songId
INNER JOIN songsComposers ON songsAnimes.songId = songsComposers.songId
INNER JOIN songsArrangers ON songsAnimes.songId = songsArrangers.songId;
"""


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
        exit()


def insert_new_artist(cursor, id, is_vocalist, is_composer):
    """
    Insert a new artist in the database
    """

    sql_insert_artist = "INSERT INTO artists(id, vocalist, composer) VALUES(?, ?, ?);"

    run_sql_command(cursor, sql_insert_artist, [id, is_vocalist, is_composer])

    return cursor.lastrowid


def insert_new_group(cursor, artist_id, set_id):
    """
    Add a new group configuration
    """

    command = "INSERT INTO groups(artist_id, line_up_id) VALUES(?, ?);"
    run_sql_command(cursor, command, [artist_id, set_id])


def insert_artist_alt_names(cursor, id, names):
    """
    Insert all alternative names corresponding to a single artist
    """

    for name in names:
        sql_insert_artist_name = (
            "INSERT INTO artist_names(artist_id, name) VALUES(?, ?);"
        )

        run_sql_command(cursor, sql_insert_artist_name, (id, name))


def add_artist_to_group(cursor, group_id, group_line_up_id, artist_id, artist_line_up):
    """
    Add an artist to a group
    """

    sql_add_artist_to_group = "INSERT INTO link_artist_group(group_id, group_line_up_id, member_id, member_line_up_id) VALUES(?, ?, ?, ?)"

    run_sql_command(
        cursor,
        sql_add_artist_to_group,
        (group_id, group_line_up_id, artist_id, artist_line_up),
    )


def get_anime_ID(cursor, animeExpandName, animeJPName):
    """
    Get the first anime it finds that matches the provided parameters
    """

    sql_get_anime_ID = "SELECT annId WHERE animeExpandName = ? and animeJPName = ?;"

    anime_id = run_sql_command(cursor, sql_get_anime_ID, (animeExpandName, animeJPName))
    if anime_id is not None and len(anime_id) > 0:
        return anime_id[0][0]
    return None


def insert_anime(
    cursor, annId, animeExpandName, animeENName, animeJPName, animeVintage, animeType
):
    """
    Insert a new anime in the database
    """

    sql_insert_anime = "INSERT INTO animes(annId, animeExpandName, animeENName, animeJPName, animeVintage, animeType) VALUES(?, ?, ?, ?, ?, ?);"

    run_sql_command(
        cursor,
        sql_insert_anime,
        (annId, animeExpandName, animeENName, animeJPName, animeVintage, animeType),
    )


def insert_song(
    cursor,
    annSongId,
    annId,
    songType,
    songNumber,
    songName,
    songArtist,
    songDifficulty,
    songCategory,
    HQ=-1,
    MQ=-1,
    audio=-1,
):
    """
    Insert a new song in the database and return the newly created song ID
    """

    data = (
        annSongId,
        annId,
        songType,
        songNumber,
        songName,
        songArtist,
        songDifficulty,
        songCategory,
    )

    if HQ != -1:
        sql_insert_song = "INSERT INTO songs(annSongId, annId, songType, songNumber, songName, songArtist, songDifficulty, songCategory, HQ, MQ, audio) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        data = (
            *data,
            HQ,
            MQ,
            audio,
        )
    else:
        sql_insert_song = "INSERT INTO songs(annSongId, annId, songType, songNumber, songName, songArtist, songDifficulty, songCategory) VALUES(?, ?, ?, ?, ?, ?, ?, ?);"

    run_sql_command(cursor, sql_insert_song, data)

    return cursor.lastrowid


def link_song_artist(cursor, song_id, artist_id, artist_line_up_id):
    """
    Add a new link between an song and an artist in the table
    """

    sql_link_song_artist = "INSERT INTO link_song_artist(song_id, artist_id, artist_line_up_id) VALUES(?, ?, ?);"

    run_sql_command(
        cursor, sql_link_song_artist, (song_id, artist_id, artist_line_up_id)
    )


def link_song_composer(cursor, song_id, composer_id):
    """
    Add a new link between an song and a composer in the table
    """

    sql_link_song_composer = (
        "INSERT INTO link_song_composer(song_id, composer_id) VALUES(?, ?);"
    )

    run_sql_command(cursor, sql_link_song_composer, (song_id, composer_id))


def link_song_arranger(cursor, song_id, arranger_id):
    """
    Add a new link between an song and an arranger in the table
    """

    sql_link_song_arranger = (
        "INSERT INTO link_song_arranger(song_id, arranger_id) VALUES(?, ?);"
    )

    run_sql_command(cursor, sql_link_song_arranger, (song_id, arranger_id))


def link_anime_tag(cursor, annId, tag):
    """
    Add a new link between an anime and a tag
    """

    sql_link_anime_tag = "INSERT INTO link_anime_tag(annId, tag) VALUES(?, ?);"

    run_sql_command(cursor, sql_link_anime_tag, (annId, tag))


def link_anime_genre(cursor, annId, genre):
    """
    Add a new link between an anime and a genre
    """

    sql_link_anime_genre = "INSERT INTO link_anime_genre(annId, genre) VALUES(?, ?);"

    run_sql_command(cursor, sql_link_anime_genre, (annId, genre))


def link_anime_altNames(cursor, annId, altName):
    """
    Add a new link between an anime and an alternative name
    """

    sql_link_anime_altName = (
        "INSERT INTO link_anime_altNames(annId, name) VALUES(?, ?);"
    )

    run_sql_command(cursor, sql_link_anime_altName, (annId, altName))


try:
    sqliteConnection = sqlite3.connect(database)
    cursor = sqliteConnection.cursor()
    for command in RESET_DB_SQL.split(";"):
        run_sql_command(cursor, command)
    sqliteConnection.commit()
    cursor.close()
    sqliteConnection.close()
    print("Reset successful :)")
except sqlite3.Error as error:
    print("\n", error, "\n")

try:
    sqliteConnection = sqlite3.connect(database)
    cursor = sqliteConnection.cursor()
    print("Connection successful :)")
except sqlite3.Error as error:
    print("\n", error, "\n")


for artist_id in artist_database:
    new_artist_id = insert_new_artist(
        cursor,
        artist_id,
        artist_database[artist_id]["vocalist"],
        artist_database[artist_id]["composer"],
    )

    insert_artist_alt_names(cursor, new_artist_id, artist_database[artist_id]["names"])

    if len(artist_database[artist_id]["members"]) > 0:
        for i, member_sets in enumerate(artist_database[artist_id]["members"]):
            insert_new_group(cursor, new_artist_id, i)
            for member in member_sets:
                add_artist_to_group(cursor, new_artist_id, i, int(member[0]), member[1])

for anime in song_database:
    insert_anime(
        cursor,
        anime["annId"],
        anime["animeExpandName"],
        anime["animeENName"] if "animeENName" in anime else None,
        anime["animeJPName"] if "animeJPName" in anime else None,
        anime["animeVintage"] if "animeVintage" in anime else None,
        anime["animeType"] if "animeType" in anime else None,
    )

    if "tags" in anime and anime["tags"]:
        for tag in anime["tags"]:
            link_anime_tag(cursor, anime["annId"], tag)

    if "genres" in anime and anime["genres"]:
        for genre in anime["genres"]:
            link_anime_genre(cursor, anime["annId"], genre)

    if "altNames" in anime and anime["altNames"]:
        for altName in anime["altNames"]:
            link_anime_altNames(cursor, anime["annId"], altName)

    for song in anime["songs"]:
        links = song["links"]

        song_id = insert_song(
            cursor,
            song["annSongId"],
            anime["annId"],
            song["songType"],
            song["songNumber"],
            song["songName"],
            song["songArtist"],
            song["songDifficulty"] if "songDifficulty" in song else None,
            song["songCategory"] if "songCategory" in song else None,
            links["HQ"] if "HQ" in links.keys() else None,
            links["MQ"] if "MQ" in links.keys() else None,
            links["audio"] if "audio" in links.keys() else None,
        )

        for artist in song["artist_ids"]:
            link_song_artist(cursor, song_id, int(artist[0]), artist[1])

        if "composer_ids" in song:
            for composer in song["composer_ids"]:
                link_song_composer(cursor, song_id, int(composer[0]))

        if "arranger_ids" in song:
            for arranger in song["arranger_ids"]:
                # print(song["annSongId"], arranger)
                link_song_arranger(cursor, song_id, int(arranger[0]))


sqliteConnection.commit()
cursor.close()
sqliteConnection.close()
print("Convertion Done :) - normal")
print()

try:
    sqliteConnection = sqlite3.connect(nerfedDatabase)
    cursor = sqliteConnection.cursor()
    for command in RESET_DB_SQL_NERFED.split(";"):
        run_sql_command(cursor, command)
    sqliteConnection.commit()
    cursor.close()
    sqliteConnection.close()
    print("Reset successful :)")
except sqlite3.Error as error:
    print("\n", error, "\n")

try:
    sqliteConnection = sqlite3.connect(nerfedDatabase)
    cursor = sqliteConnection.cursor()
    print("Connection successful :)")
except sqlite3.Error as error:
    print("\n", error, "\n")


for artist_id in artist_database:
    new_artist_id = insert_new_artist(
        cursor,
        artist_id,
        artist_database[artist_id]["vocalist"],
        artist_database[artist_id]["composer"],
    )

    insert_artist_alt_names(cursor, new_artist_id, artist_database[artist_id]["names"])

    if len(artist_database[artist_id]["members"]) > 0:
        for i, member_sets in enumerate(artist_database[artist_id]["members"]):
            insert_new_group(cursor, new_artist_id, i)
            for member in member_sets:
                add_artist_to_group(cursor, new_artist_id, i, int(member[0]), member[1])

for anime in song_database:
    insert_anime(
        cursor,
        anime["annId"],
        anime["animeExpandName"],
        anime["animeENName"] if "animeENName" in anime else None,
        anime["animeJPName"] if "animeJPName" in anime else None,
        anime["animeVintage"] if "animeVintage" in anime else None,
        anime["animeType"] if "animeType" in anime else None,
    )

    if "tags" in anime and anime["tags"]:
        for tag in anime["tags"]:
            link_anime_tag(cursor, anime["annId"], tag)

    if "genres" in anime and anime["genres"]:
        for genre in anime["genres"]:
            link_anime_genre(cursor, anime["annId"], genre)

    if "altNames" in anime and anime["altNames"]:
        for altName in anime["altNames"]:
            link_anime_altNames(cursor, anime["annId"], altName)

    for song in anime["songs"]:
        links = song["links"]

        song_id = insert_song(
            cursor,
            song["annSongId"],
            anime["annId"],
            song["songType"],
            song["songNumber"],
            song["songName"],
            song["songArtist"],
            song["songDifficulty"] if "songDifficulty" in song else None,
            song["songCategory"] if "songCategory" in song else None,
        )

        for artist in song["artist_ids"]:
            link_song_artist(cursor, song_id, int(artist[0]), artist[1])

        if "composer_ids" in song:
            for composer in song["composer_ids"]:
                link_song_composer(cursor, song_id, int(composer[0]))

        if "arranger_ids" in song:
            for arranger in song["arranger_ids"]:
                # print(song["annSongId"], arranger)
                link_song_arranger(cursor, song_id, int(arranger[0]))


sqliteConnection.commit()
cursor.close()
sqliteConnection.close()
print("Convertion Done :) - nerfed")
