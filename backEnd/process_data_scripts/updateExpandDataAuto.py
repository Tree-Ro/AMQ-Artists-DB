from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
from datetime import datetime
import time, os, json


# Call Listener to get expand data and store it in a new element that selenium is waiting for
getExpandScript = """
function getPromiseExpand() {
    return new Promise((resolve) => {
        new Listener("expandLibrary questions", (payload) => {
            hiddenInput = document.createElement("div");
            hiddenInput.setAttribute("type", "hidden");
            hiddenInput.setAttribute("id", "hiddenExpand")
            hiddenInput.variable = payload
            document.getElementById("mainPage").appendChild(hiddenInput)
            resolve();
        }).bindListener()
        socket.sendCommand({
            type: "library",
            command: "expandLibrary questions"
        })
    })
}

async function waitForExpandLoaded() {
    await getPromiseExpand()
}
waitForExpandLoaded().then((result) => {
    console.log("Promise done adding new element")
})
"""


def add_log(log):
    print(log)
    """Append given text as a new line at the end of file"""
    # Open the file in append & read mode ('a+')
    with open("updateLogs.txt", "a+") as file_object:
        # Move read cursor to the start of file.
        file_object.seek(0)
        # If file is not empty then append '\n'
        data = file_object.read(100)
        if len(data) > 0:
            file_object.write("\n")
        # Append text at the end of file
        file_object.write(log)


def selenium_retrieve_data(amq_url, amq_username, amq_password):
    # create driver and open amq
    option = webdriver.ChromeOptions()
    option.add_argument("headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)
    driver.get(amq_url)
    expand = None

    try:

        # Login
        driver.find_element(By.ID, "loginUsername").send_keys(amq_username)
        driver.find_element(By.ID, "loginPassword").send_keys(amq_password)
        driver.find_element(By.ID, "loginButton").click()

        # Wait few seconds to make sure page is loaded (need to find a better way)
        time.sleep(7)
        add_log("Connected to AMQ")

    finally:
        try:

            # Execute script
            driver.execute_script(getExpandScript)
            add_log("script executed, waiting for promise")

            # Wait for new element to be created and get data
            element = WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.ID, "hiddenExpand"))
            )
            expand = element.get_property("variable")
        finally:
            driver.quit()
            return expand


def similar_song_exist(source_anime, update_song):

    for song in source_anime["songs"]:
        if song["annSongId"] == -1 and (
            song["name"] == update_song["name"]
            or song["artist"] == update_song["artist"]
        ):
            return True
    return False


def update_data_with_expand(source_data, expand_data):

    for update_anime in expand_data:
        for update_song in update_anime["songs"]:
            flag_anime_found = False
            flag_song_found = False
            for source_anime in source_data:

                if source_anime["annId"] != update_anime["annId"]:
                    continue

                flag_anime_found = True

                if source_anime["name"] != update_anime["name"]:
                    add_log(
                        f"UPDATE ANIME NAME | {source_anime['name']} -> {update_anime['name']}"
                    )
                    source_anime["name"] = update_anime["name"]

                for i, source_song in enumerate(source_anime["songs"]):
                    if source_song["annSongId"] != update_song["annSongId"]:
                        continue
                    flag_song_found = True
                    if source_song["name"] != update_song["name"]:
                        add_log(
                            f"UPDATE SONG NAME | {source_song['annSongId']} {source_song['name']} -> {update_song['name']}"
                        )
                        source_song["name"] = update_song["name"]
                    if source_song["artist"] != update_song["artist"]:
                        add_log(
                            f"UPDATE SONG ARTIST | {source_song['annSongId']} {source_song['artist']} -> {update_song['artist']}"
                        )
                        source_song["artist"] = update_song["artist"]
                    if source_song["examples"] != update_song["examples"]:
                        add_log(
                            f"UPDATE SONG LINKS | {source_song['annSongId']} {source_song['examples']} -> {update_song['examples']}"
                        )
                        source_song["examples"] = update_song["examples"]
                    break

                if flag_song_found:
                    continue

                # If anime found but song not found
                update_song.pop("versions")
                source_anime["songs"].append(update_song)
                if similar_song_exist(source_anime, update_song):
                    add_log(f"ADD SONG - HIGH THREAT | {update_song}")
                elif -1 in [song["annSongId"] for song in source_anime["songs"]]:
                    add_log(f"ADD SONG - LOW THREAT | {update_song}")
                else:
                    add_log(f"ADD SONG | {update_song}")
                break

            # if anime not found
            if not flag_anime_found:
                songs = []
                add_log(f"ADD ANIME | {update_anime['annId']} - {update_anime['name']}")
                for song in update_anime["songs"]:
                    song.pop("versions")
                    add_log(f"ADD SONG TO NEW ANIME | {song}")
                    songs.append(song)
                source_data.append(
                    {
                        "annId": update_anime["annId"],
                        "name": update_anime["name"],
                        "songs": songs,
                    }
                )
    return source_data


def process():
    AMQ_USERNAME = "purplepinapple9"
    AMQ_PWD = "purplepinapple9"
    SOURCE_FILE_PATH = Path("../data/preprocessed/FusedExpand.json")

    expand_data = selenium_retrieve_data(
        "https://animemusicquiz.com/", AMQ_USERNAME, AMQ_PWD
    )
    expand_data = expand_data["questions"]
    if not expand_data:
        add_log("ERROR WARNING /!\ Couldn't Retrieve Expand: It is undefined")
    else:
        with open(SOURCE_FILE_PATH, encoding="utf-8") as json_file:
            source_data = json.load(json_file)

        updated_data = update_data_with_expand(source_data, expand_data)

        with open(SOURCE_FILE_PATH, "w", encoding="utf-8") as outfile:
            json.dump(updated_data, outfile)

        os.chdir("process_artists")
        os.system("map1_artist_id.py")
        os.system("map2_group_id.py")
        os.system("map3_alt_groups.py")
        os.system("map4_same_name.py")
        os.system("map5_member_of.py")
        os.system("map6_composers.py")
        os.system("convert_to_SQL.py")
        os.chdir("../")

        now = datetime.now()
        with open("../app/check_update.py", "a+") as file_object:
            # Move read cursor to the start of file.
            file_object.seek(0)
            # If file is not empty then append '\n'
            data = file_object.read(100)
            if len(data) > 0:
                file_object.write("\n")
            # Append text at the end of file
            file_object.write(f'"Update Done - {now.strftime("%d/%m/%Y %H:%M:%S")}"')

        add_log("Update Done - " + now.strftime("%d/%m/%Y %H:%M:%S"))
        os.system(
            "scp ../app/data/Enhanced-AMQ-Database.db anthony@anisongdb.com:~/AMQ-Artists-DB/backEnd/app/data/Enhanced-AMQ-Database.db"
        )
        os.system(
            "scp ../app/check_update.py anthony@anisongdb.com:~/AMQ-Artists-DB/backEnd/app/check_update.py"
        )
        print("Update sent")


if __name__ == "__main__":
    # schedule(process, interval=(1 / 10) * 60 * 60)
    # run_loop()
    process()
