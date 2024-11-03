"""
Convert the mapping in JSON generated by process_artists scripts to an SQL database for production use
"""

import sqlite3
import json
from pathlib import Path

database = Path("../app/data/Enhanced-AMQ-Database.db")
song_database_path = Path("../app/data/song_database.json")
artist_database_path = Path("../app/data/artist_database.json")

with open(song_database_path, encoding="utf-8") as json_file:
    song_database = json.load(json_file)
with open(artist_database_path, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)


RESET_DB_SQL = """
PRAGMA foreign_keys = 0;
DROP TABLE IF EXISTS animes;
DROP TABLE IF EXISTS link_anime_genre;
DROP TABLE IF EXISTS link_anime_tag;
DROP TABLE IF EXISTS link_anime_alt_name;
DROP TABLE IF EXISTS artists;
DROP TABLE IF EXISTS link_artist_name;
DROP TABLE IF EXISTS line_ups;
DROP TABLE IF EXISTS link_artist_line_up;
DROP TABLE IF EXISTS songs;
DROP TABLE IF EXISTS link_song_arranger;
DROP TABLE IF EXISTS link_song_artist;
DROP TABLE IF EXISTS link_song_composer;
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
    "malId" INTEGER,
    "anidbId" INTEGER,
    "anilistId" INTEGER,
    "kitsuId" INTEGER,
    "animeENName" VARCHAR(255),
    "originalJPName" VARCHAR(255),
    "animeJPName" VARCHAR(255),
    "animeVintage" VARCHAR(255),
    "animeType" VARCHAR(255),
    "animeCategory" VARCHAR(255)
);

CREATE TABLE songs (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "annSongId" INTEGER,
    "amqSongId" INTEGER NOT NULL,
    "annId" INTEGER NOT NULL,
    "songType" INTEGER NOT NULL,
    "songNumber" INTEGER NOT NULL,
    "originalSongName" VARCHAR(255),
    "romajiSongName" VARCHAR(255),
    "originalSongArtist" VARCHAR(255),
    "romajiSongArtist" VARCHAR(255),
    "originalSongComposer" VARCHAR(255),
    "romajiSongComposer" VARCHAR(255),
    "originalSongArranger" VARCHAR(255),
    "romajiSongArranger" VARCHAR(255),
    "songDifficulty" FLOAT,
    "songCategory" VARCHAR(255),
    "isDub" boolean,
    "isRebroadcast" boolean,
    "songLength" FLOAT,
    "HQ" VARCHAR(255),
    "MQ" VARCHAR(255),
    "audio" VARCHAR(255),
    FOREIGN KEY ("annId")
        REFERENCES animes ("annId")
);

CREATE TABLE artists (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "disambiguation" VARCHAR(255),
    "type" TEXT CHECK(type IN ('person', 'group', 'choir', 'orchestra')) NOT NULL
);

CREATE TABLE line_ups (
    "artist_id" INTEGER NOT NULL,
    "line_up_id" INTEGER NOT NULL,
    "line_up_type" TEXT CHECK(line_up_type IN ('vocalists', 'composers')) NOT NULL,
    FOREIGN KEY ("artist_id")
        REFERENCES artists ("id"),
    PRIMARY KEY (artist_id, line_up_id)
);

CREATE TABLE link_artist_name (
    "inserted_order" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "artist_id" INTEGER NOT NULL,
    "original_name" VARCHAR(255),
    "romaji_name" VARCHAR(255) NOT NULL,
    FOREIGN KEY ("artist_id")
        REFERENCES artist ("id"),
    UNIQUE (artist_id, romaji_name)
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
        REFERENCES line_ups ("line_up_id"),
    PRIMARY KEY (song_id, artist_id, artist_line_up_id)
);

CREATE TABLE link_song_composer (
    "song_id" INTEGER NOT NULL,
    "composer_id" INTEGER NOT NULL,
    "composer_line_up_id" INTEGER NOT NULL,
    FOREIGN KEY ("song_id")
        REFERENCES songs ("id"),
    FOREIGN KEY ("composer_id")
        REFERENCES artists ("id"),
    PRIMARY KEY (song_id, composer_id)
);

CREATE TABLE link_song_arranger (
    "song_id" INTEGER NOT NULL,
    "arranger_id" INTEGER NOT NULL,
    "arranger_line_up_id" INTEGER NOT NULL,
    FOREIGN KEY ("song_id")
        REFERENCES songs ("id"),
    FOREIGN KEY ("arranger_id")
        REFERENCES artists ("id"),
    PRIMARY KEY (song_id, arranger_id)
);

create TABLE link_artist_line_up (
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

create TABLE link_anime_alt_name (
    "annId" INTEGER NOT NULL,
    "lang" VARCHAR(255),
    "original_name" VARCHAR(255),
    "romaji_name" VARCHAR(255),
    FOREIGN KEY ("annId")
        REFERENCES animes ("annId"),
    PRIMARY KEY (annId, romaji_name)
);

CREATE VIEW artistsNames AS 
SELECT orderedNames.inserted_order, artists.id, group_concat(orderedNames.original_name, "\\$") AS original_names, group_concat(orderedNames.romaji_name, "\\$") AS romaji_names, artists.disambiguation, artists.type
FROM artists
LEFT JOIN (SELECT * FROM link_artist_name ORDER BY link_artist_name.inserted_order) AS orderedNames
ON artists.id = orderedNames.artist_id
GROUP BY artists.id;

CREATE VIEW artistsMembers AS 
SELECT artists.id, group_concat(link_artist_line_up.member_id) AS members, group_concat(link_artist_line_up.member_line_up_id) as members_line_up 
FROM artists
LEFT JOIN link_artist_line_up ON artists.id = link_artist_line_up.group_id 
GROUP BY artists.id;

CREATE VIEW artistsGroups AS 
SELECT artists.id, group_concat(link_artist_line_up.group_id) AS groups, group_concat(link_artist_line_up.group_line_up_id) as groups_line_up 
FROM artists 
LEFT JOIN link_artist_line_up ON artists.id = link_artist_line_up.member_id 
GROUP BY artists.id;

CREATE VIEW artistsLineUps AS 
SELECT artists.id, artistsNames.names, link_artist_line_up.group_line_up_id, group_concat(link_artist_line_up.member_id) AS members, group_concat(link_artist_line_up.member_line_up_id) as members_line_up 
FROM artists 
LEFT JOIN link_artist_line_up ON artists.id = link_artist_line_up.group_id
LEFT JOIN artistsNames ON artists.id = artistsNames.id
GROUP BY artists.id, link_artist_line_up.group_line_up_id;

CREATE VIEW artistsFull AS
SELECT artistsNames.id, artistsNames.names, artistsMembers.members, artistsMembers.members_line_up, artistsGroups.groups, artistsGroups.groups_line_up
FROM artistsNames
INNER JOIN artistsMembers ON artistsNames.id = artistsMembers.id
INNER JOIN artistsGroups ON artistsNames.id = artistsGroups.id;

CREATE VIEW animesFull AS
SELECT animes.annId, animes.malId, animes.anidbId, animes.anilistId, animes.kitsuId, animes.originalJPName, animes.animeJPName, animes.animeENName, group_concat(link_anime_alt_name.original_name, "\\$") AS original_alt_names, group_concat(link_anime_alt_name.romaji_name, "\\$") AS romaji_alt_names, animes.animeType, animes.animeCategory, animes.animeVintage
FROM animes
LEFT JOIN link_anime_alt_name
ON animes.annId = link_anime_alt_name.annId
GROUP BY animes.annId;

CREATE VIEW songsAnimes AS
SELECT animesFull.annId, animesFull.malId, animesFull.anidbId, animesFull.anilistId, animesFull.kitsuId, animesFull.originalJPName, animesFull.animeJPName, animesFull.animeENName, animesFull.original_alt_names, animesFull.romaji_alt_names, animesFull.animeVintage, animesFull.animeType, animesFull.animeCategory,
songs.id as songId, songs.amqSongId, songs.annSongId, songs.songType, songs.songNumber, songs.songCategory, songs.originalSongName, songs.romajiSongName, songs.originalSongArtist, songs.romajiSongArtist, songs.originalSongComposer, songs.romajiSongComposer, songs.originalSongArranger, songs.romajiSongArranger, songs.songDifficulty, songs.isDub, songs.isRebroadcast, songs.songLength, songs.HQ, songs.MQ, songs.audio
FROM animesFull
LEFT JOIN songs ON animesFull.annId = songs.annId;

CREATE VIEW songsArtists AS
SELECT songs.id as songId, group_concat(link_song_artist.artist_id) AS artists, group_concat(link_song_artist.artist_line_up_id) AS artists_line_up
FROM songs 
LEFT JOIN link_song_artist ON songs.id = link_song_artist.song_id
GROUP BY songs.id;

CREATE VIEW songsComposers AS
SELECT songs.id as songId, group_concat(link_song_composer.composer_id) AS composers, group_concat(link_song_composer.composer_line_up_id) AS composers_line_up
FROM songs
LEFT JOIN link_song_composer ON songs.id = link_song_composer.song_id
GROUP BY songs.id;

CREATE VIEW songsArrangers AS
SELECT songs.id as songId, group_concat(link_song_arranger.arranger_id) AS arrangers, group_concat(link_song_arranger.arranger_line_up_id) AS arrangers_line_up
FROM songs
LEFT JOIN link_song_arranger ON songs.id = link_song_arranger.song_id
GROUP BY songs.id;

CREATE VIEW songsFull AS
SELECT songsAnimes.annId, songsAnimes.malId, songsAnimes.anidbId, songsAnimes.anilistId, songsAnimes.kitsuId, songsAnimes.originalJPName, songsAnimes.animeJPName, songsAnimes.animeENName, songsAnimes.original_alt_names, songsAnimes.romaji_alt_names, songsAnimes.animeVintage, songsAnimes.animeType, songsAnimes.animeCategory,
songsAnimes.songId, songsAnimes.annSongId, songsAnimes.amqSongId, songsAnimes.songType, songsAnimes.songNumber, songsAnimes.songCategory, songsAnimes.originalSongName, songsAnimes.romajiSongName, songsAnimes.originalSongArtist, songsAnimes.romajiSongArtist, songsArtists.artists, songsArtists.artists_line_up, songsAnimes.originalSongComposer, songsAnimes.romajiSongComposer, songsComposers.composers, songsComposers.composers_line_up, songsAnimes.originalSongArranger, songsAnimes.romajiSongArranger, songsArrangers.arrangers, songsArrangers.arrangers_line_up, songsAnimes.songDifficulty, songsAnimes.isDub, songsAnimes.isRebroadcast, songsAnimes.songLength, songsAnimes.HQ, songsAnimes.MQ, songsAnimes.audio
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


def insert_new_artist(cursor, id, disambiguation, type):
    """
    Insert a new artist in the database
    """

    if type not in ["person", "group", "choir", "orchestra"]:
        print("Error: Invalid artist type")
        exit()

    sql_insert_artist = "INSERT INTO artists(id, disambiguation, type) VALUES(?, ?, ?);"

    run_sql_command(cursor, sql_insert_artist, [id, disambiguation, type])

    return cursor.lastrowid


def insert_new_line_up(cursor, artist_id, line_up_id, line_up_type):
    """
    Add a new line_up configuration
    """

    command = (
        "INSERT INTO line_ups(artist_id, line_up_id, line_up_type) VALUES(?, ?, ?);"
    )
    run_sql_command(cursor, command, [artist_id, line_up_id, line_up_type])


def insert_artist_alt_names(cursor, id, names):
    """
    Insert all alternative names corresponding to a single artist
    """

    for name in names:

        original_name = name["original_name"]
        romaji_name = name["romaji_name"]

        sql_insert_artist_name = "INSERT INTO link_artist_name(artist_id, original_name, romaji_name) VALUES(?, ?, ?);"

        run_sql_command(
            cursor, sql_insert_artist_name, (id, original_name, romaji_name)
        )


def add_artist_to_group(cursor, group_id, group_line_up_id, artist_id, artist_line_up):
    """
    Add an artist to a group
    """

    sql_add_artist_to_group = "INSERT INTO link_artist_line_up(group_id, group_line_up_id, member_id, member_line_up_id) VALUES(?, ?, ?, ?)"

    run_sql_command(
        cursor,
        sql_add_artist_to_group,
        (group_id, group_line_up_id, artist_id, artist_line_up),
    )


def insert_anime(
    cursor,
    annId,
    malId,
    anidbId,
    anilistId,
    kitsuId,
    animeENName,
    originalJPName,
    animeJPName,
    animeVintage,
    animeType,
    animeCategory,
):
    """
    Insert a new anime in the database
    """

    sql_insert_anime = "INSERT INTO animes(annId, malId, anidbId, anilistId, kitsuId, animeENName, originalJPName, animeJPName, animeVintage, animeType, animeCategory) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"

    run_sql_command(
        cursor,
        sql_insert_anime,
        (
            annId,
            malId,
            anidbId,
            anilistId,
            kitsuId,
            animeENName,
            originalJPName,
            animeJPName,
            animeVintage,
            animeType,
            animeCategory,
        ),
    )


def insert_song(
    cursor,
    annSongId,
    amqSongId,
    annId,
    songType,
    songNumber,
    originalSongName,
    romajiSongName,
    originalSongArtist,
    romajiSongArtist,
    originalSongComposer,
    romajiSongComposer,
    originalSongArranger,
    romajiSongArranger,
    songDifficulty,
    songCategory,
    isDub,
    isRebroadcast,
    songLength,
    HQ=-1,
    MQ=-1,
    audio=-1,
):
    """
    Insert a new song in the database and return the newly created song ID
    """

    data = (
        annSongId,
        amqSongId,
        annId,
        songType,
        songNumber,
        songCategory,
        originalSongName,
        romajiSongName,
        originalSongArtist,
        romajiSongArtist,
        originalSongComposer,
        romajiSongComposer,
        originalSongArranger,
        romajiSongArranger,
        songDifficulty,
        isDub,
        isRebroadcast,
        songLength,
    )

    if HQ != -1:
        sql_insert_song = "INSERT INTO songs(annSongId, amqSongId, annId, songType, songNumber, songCategory, originalSongName, romajiSongName, originalSongArtist, romajiSongArtist, originalSongComposer, romajiSongComposer, originalSongArranger, romajiSongArranger, songDifficulty, isDub, isRebroadcast, songLength, HQ, MQ, audio) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        data = (
            *data,
            HQ,
            MQ,
            audio,
        )
    else:
        sql_insert_song = "INSERT INTO songs(annSongId, amqSongId, annId, songType, songNumber, songCategory, originalSongName, romajiSongName, originalSongArtist, romajiSongArtist, originalSongComposer, romajiSongComposer, originalSongArranger, songDifficulty, isDub, isRebroadcast, songLength) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"

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


def link_song_composer(cursor, song_id, composer_id, composer_line_up_id):
    """
    Add a new link between an song and a composer in the table
    """

    sql_link_song_composer = "INSERT INTO link_song_composer(song_id, composer_id, composer_line_up_id) VALUES(?, ?, ?);"

    run_sql_command(
        cursor, sql_link_song_composer, (song_id, composer_id, composer_line_up_id)
    )


def link_song_arranger(cursor, song_id, arranger_id, arranger_line_up_id):
    """
    Add a new link between an song and an arranger in the table
    """

    sql_link_song_arranger = "INSERT INTO link_song_arranger(song_id, arranger_id, arranger_line_up_id) VALUES(?, ?, ?);"

    run_sql_command(
        cursor, sql_link_song_arranger, (song_id, arranger_id, arranger_line_up_id)
    )


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


def link_anime_alt_name(cursor, annId, alt_name):
    """
    Add a new link between an anime and an alternative name
    """

    lang = alt_name["lang"]
    original_name = alt_name["original_name"]
    romaji_name = alt_name["romaji_name"]

    sql_link_anime_altName = "INSERT INTO link_anime_alt_name(annId, lang, original_name, romaji_name) VALUES(?, ?, ?, ?);"

    run_sql_command(
        cursor, sql_link_anime_altName, (annId, lang, original_name, romaji_name)
    )


def extract_catbox_link_id(link):

    return link.split("/")[-1] if link else None


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
        artist_database[artist_id]["disambiguation"],
        artist_database[artist_id]["type"],
    )

    insert_artist_alt_names(cursor, new_artist_id, artist_database[artist_id]["names"])

    if len(artist_database[artist_id]["members"]) > 0:
        for i, line_up in enumerate(artist_database[artist_id]["members"]):
            insert_new_line_up(cursor, new_artist_id, i, line_up["type"])
            for member in line_up["members"]:
                add_artist_to_group(cursor, new_artist_id, i, int(member[0]), member[1])

nb_songs = 0
max_songs = 9999999
for annId in song_database:

    if nb_songs >= max_songs:
        break

    anime = song_database[annId]
    insert_anime(
        cursor,
        anime["annId"],
        (
            anime["linked_ids"]["myanimelist"]
            if "linked_ids" in anime and "myanimelist" in anime["linked_ids"]
            else None
        ),
        (
            anime["linked_ids"]["anidb"]
            if "linked_ids" in anime and "anidb" in anime["linked_ids"]
            else None
        ),
        (
            anime["linked_ids"]["anilist"]
            if "linked_ids" in anime and "anilist" in anime["linked_ids"]
            else None
        ),
        (
            anime["linked_ids"]["kitsu"]
            if "linked_ids" in anime and "kitsu" in anime["linked_ids"]
            else None
        ),
        anime["animeENName"] if "animeENName" in anime else None,
        anime["originalJPName"] if "originalJPName" in anime else None,
        anime["animeJPName"] if "animeJPName" in anime else None,
        anime["animeVintage"] if "animeVintage" in anime else None,
        anime["animeType"] if "animeType" in anime else None,
        anime["animeCategory"] if "animeCategory" in anime else None,
    )

    if "tags" in anime and anime["tags"]:
        for tag in anime["tags"]:
            link_anime_tag(cursor, anime["annId"], tag)

    if "genres" in anime and anime["genres"]:
        for genre in anime["genres"]:
            link_anime_genre(cursor, anime["annId"], genre)

    if "altNames" in anime and anime["altNames"]:
        for altName in anime["altNames"]:
            link_anime_alt_name(cursor, anime["annId"], altName)

    for song in anime["songs"]:

        nb_songs += 1

        links = song["links"]

        song_id = insert_song(
            cursor,
            song["annSongId"],
            song["amqSongId"],
            anime["annId"],
            song["songType"],
            song["songNumber"],
            song["originalSongName"],
            song["romajiSongName"],
            song["originalSongArtist"],
            song["romajiSongArtist"],
            song["originalSongComposer"],
            song["romajiSongComposer"],
            song["originalSongArranger"],
            song["romajiSongArranger"],
            song["songDifficulty"] if "songDifficulty" in song else None,
            song["songCategory"] if "songCategory" in song else None,
            song["isDub"],
            song["isRebroadcast"],
            song["songLength"] if "songLength" in song else None,
            extract_catbox_link_id(links["HQ"]) if "HQ" in links.keys() else None,
            extract_catbox_link_id(links["MQ"]) if "MQ" in links.keys() else None,
            extract_catbox_link_id(links["audio"]) if "audio" in links.keys() else None,
        )

        for artist in song["artist_ids"]:
            link_song_artist(cursor, song_id, int(artist[0]), artist[1])

        if "composer_ids" in song:
            for composer_id, composer_line_up_id in song["composer_ids"]:
                link_song_composer(
                    cursor, song_id, int(composer_id), int(composer_line_up_id)
                )

        if "arranger_ids" in song:
            for arranger_id, arranger_line_up_id in song["arranger_ids"]:
                # print(song["annSongId"], arranger)
                link_song_arranger(
                    cursor, song_id, int(arranger_id), int(arranger_line_up_id)
                )


sqliteConnection.commit()
cursor.close()
sqliteConnection.close()
print("Convertion Done :) - normal")
print()
