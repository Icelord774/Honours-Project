import csv
from io import StringIO
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
import requests
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

statList = ["kills", "deaths", "assists", "killsDeathsRatio", "killsDeathsAssists"]
allStatList = ["kills", "deaths", "assists", "killsDeathsRatio", "killsDeathsAssists", "activitiesCleared",
               "resurrectionsPerformed", "resurrectionsReceived", "weaponKillsAutoRifle", "weaponKillsBow",
               "weaponKillsGlaive", "weaponKillsFusionRifle", "weaponKillsHandCannon", "weaponKillsTraceRifle",
               "weaponKillsMachineGun", "weaponKillsPulseRifle", "weaponKillsRocketLauncher", "weaponKillsScoutRifle",
               "weaponKillsShotgun", "weaponKillsSniper", "weaponKillsSubmachinegun", "weaponKillsSideArm",
               "weaponKillsSword", "weaponKillsGrenadeLauncher"]

allPvpStatList = ["kills", "deaths", "assists", "killsDeathsRatio", "killsDeathsAssists", "activitiesEntered",
                  "resurrectionsPerformed", "resurrectionsReceived", "weaponKillsAutoRifle", "weaponKillsBow",
                  "weaponKillsGlaive", "weaponKillsFusionRifle", "weaponKillsHandCannon", "weaponKillsTraceRifle",
                  "weaponKillsMachineGun", "weaponKillsPulseRifle", "weaponKillsRocketLauncher",
                  "weaponKillsScoutRifle",
                  "weaponKillsShotgun", "weaponKillsSniper", "weaponKillsSubmachinegun", "weaponKillsSideArm",
                  "weaponKillsSword", "weaponKillsGrenadeLauncher"]

values = []

headers = {
    "X-API-Key": "207ffa2b218540719501f16ea1551620"
}

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process-data', methods=['GET', 'POST'])
def process_data():
    if request.method == 'POST':
        platform = request.form['platform']
        username = request.form['username']
        if not username:
            flash("Please enter a Bungie name", 'error')
            return redirect(url_for('process_data'))

        mode = request.form['mode']
        return redirect(url_for('extract_data', platform=platform, username=username, mode=mode))
    else:
        return render_template('index.html')


@app.route('/extract-data')
def extract_data():
    platform = request.args.get('platform')
    mode = request.args.get('mode')
    username = request.args.get('username')
    altered_name = username.replace("#", "%23")
    if platform == "xbox":
        membership_type = 1
    elif platform == "ps":
        membership_type = 2
    else:
        membership_type = 3

    endpoint = f"https://www.bungie.net/Platform/Destiny2/SearchDestinyPlayer/{membership_type}/{altered_name}/"

    response = requests.get(endpoint, headers=headers)
    parsed_response = json.loads(response.text)

    if parsed_response.get('ErrorCode') != 1 or not parsed_response['Response']:
        flash("Please enter valid Bungie name ")
        return redirect(url_for('process_data'))

    membershipId = parsed_response['Response'][0]['membershipId']
    bungieName = parsed_response['Response'][0]['bungieGlobalDisplayName']
    bungieCode = parsed_response['Response'][0]['bungieGlobalDisplayNameCode']
    char_endpoint = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membershipId}/?components=200"
    char_response = requests.get(char_endpoint, headers=headers)
    parsed_char_response = json.loads(char_response.text)
    if parsed_char_response.get('ErrorCode') == 1601 or not parsed_response['Response']:
        flash("Please enter Bungie name for the platform you created your account ")
        return redirect(url_for('process_data'))
    data = parsed_char_response['Response']["characters"]["data"]
    for i in data:
        character_id = i
        break

    param_list = [membership_type, membershipId, character_id, bungieName, bungieCode]
    if mode == "strike":
        return redirect(
            url_for('strike_data', param=param_list))
    elif mode == "crucible":
        return redirect(
            url_for('crucible_data', param=param_list))
    elif mode == "gambit":
        return redirect(
            url_for('gambit_data', param=param_list))
    elif mode == "raid":
        return redirect(
            url_for('raid_data', param=param_list))
    elif mode == "story":
        return redirect(
            url_for('story_data', param=param_list))
    elif mode == "dungeon":
        return redirect(
            url_for('dungeon_data', param=param_list))
    elif mode == "dares":
        return redirect(
            url_for('dares_data', param=param_list))
    elif mode == "lostsector":
        return redirect(
            url_for('lostsector_data', param=param_list))
    elif mode == "nightmarehunt":
        return redirect(
            url_for('nightmarehunt_data', param=param_list))


@app.route('/download_table', methods=['POST'])
def download_table():
    table_values_str = request.form.get('table_values')
    table_values = eval(table_values_str)

    table_values = [['Date', 'Kills', 'Deaths', 'Assists', 'K/D Ratio', 'K/D/A Ratio']] + table_values

    # Write the table values to a CSV file
    file = StringIO()
    writer = csv.writer(file)
    writer.writerows(table_values)

    # Set the response headers and return the file
    response = make_response(file.getvalue())
    response.headers.set('Content-Disposition', 'attachment', filename='table.txt')
    response.headers.set('Content-Type', 'text/plain')
    return response


def get_stats(response, statList):
    values = []
    for i in range(min(len(response['Response']['activities']), 20)):
        initial_time = response['Response']['activities'][i]['period']
        stat_time = initial_time.replace('T', ' ').replace('Z', '')
        kills = response['Response']['activities'][i]['values'][statList[0]]['basic']['value']
        deaths = response['Response']['activities'][i]['values'][statList[1]]['basic']['value']
        assists = response['Response']['activities'][i]['values'][statList[2]]['basic']['value']
        kdr = response['Response']['activities'][i]['values'][statList[3]]['basic']['value']
        kda = response['Response']['activities'][i]['values'][statList[4]]['basic']['value']
        values.append([stat_time, kills, deaths, assists, kdr, kda])
    return values


def get_allstats(response, allStatList, identifier):
    all_values = []
    for stat in allStatList:
        all_value = response['Response'][identifier]['allTime'][stat]['basic']['value']
        all_values.append(all_value)
    return all_values


def get_allpvpStats(response, allPvpStatList, identifier):
    all_values = []
    for stat in allPvpStatList:
        all_value = response['Response'][identifier]['allTime'][stat]['basic']['value']
        all_values.append(all_value)
    return all_values


@app.route('/strike-data')
def strike_data():
    param_list = request.args.getlist('param')
    strike_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/Activities/?count=20&mode=3&page=0"

    strike_response = requests.get(strike_endpoint, headers=headers)
    parsed_strike_response = json.loads(strike_response.text)

    strike_values = get_stats(parsed_strike_response, statList)

    allstrike_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/?groups=102&modes=3&periodType=AllTime"

    allstrike_response = requests.get(allstrike_endpoint, headers=headers)
    parsed_allstrike_response = json.loads(allstrike_response.text)
    allstrike_values = get_allstats(parsed_allstrike_response, allStatList, "strike")
    return render_template('strike.html', strike_values=strike_values, allstrike_values=allstrike_values)


@app.route('/crucible-data')
def crucible_data():
    param_list = request.args.getlist('param')
    crucible_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/Activities/?count=20&mode=5&page=0"

    crucible_response = requests.get(crucible_endpoint, headers=headers)
    parsed_crucible_response = json.loads(crucible_response.text)
    crucible_values = get_stats(parsed_crucible_response, statList)

    allcrucible_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/?groups=102&modes=5&periodType=AllTime"

    allcrucible_response = requests.get(allcrucible_endpoint, headers=headers)
    parsed_allcrucible_response = json.loads(allcrucible_response.text)
    allcrucible_values = get_allpvpStats(parsed_allcrucible_response, allPvpStatList, "allPvP")
    print(allcrucible_values[6])

    return render_template('crucible.html', crucible_values=crucible_values, allcrucible_values=allcrucible_values)


@app.route('/gambit-data')
def gambit_data():
    param_list = request.args.getlist('param')
    gambit_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/Activities/?count=20&mode=63&page=0"

    gambit_response = requests.get(gambit_endpoint, headers=headers)
    parsed_gambit_response = json.loads(gambit_response.text)
    gambit_values = get_stats(parsed_gambit_response, statList)

    allgambit_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/?groups=102&modes=63&periodType=AllTime"

    allgambit_response = requests.get(allgambit_endpoint, headers=headers)
    parsed_allgambit_response = json.loads(allgambit_response.text)
    allgambit_values = get_allpvpStats(parsed_allgambit_response, allPvpStatList, "pvecomp_gambit")

    return render_template('gambit.html', gambit_values=gambit_values, allgambit_values=allgambit_values)


@app.route('/raid-data')
def raid_data():
    param_list = request.args.getlist('param')
    raid_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/Activities/?count=20&mode=4&page=0"

    raid_response = requests.get(raid_endpoint, headers=headers)
    parsed_raid_response = json.loads(raid_response.text)
    raid_values = get_stats(parsed_raid_response, statList)

    allraid_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/?groups=102&modes=4&periodType=AllTime"

    allraid_response = requests.get(allraid_endpoint, headers=headers)
    parsed_allraid_response = json.loads(allraid_response.text)
    allraid_values = get_allstats(parsed_allraid_response, allStatList, "raid")

    return render_template('raid.html', raid_values=raid_values, allraid_values=allraid_values)


@app.route('/story-data')
def story_data():
    param_list = request.args.getlist('param')
    story_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/Activities/?count=20&mode=2&page=0"

    story_response = requests.get(story_endpoint, headers=headers)
    parsed_story_response = json.loads(story_response.text)
    story_values = get_stats(parsed_story_response, statList)

    allstory_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/?groups=102&modes=2&periodType=AllTime"

    allstory_response = requests.get(allstory_endpoint, headers=headers)
    parsed_allstory_response = json.loads(allstory_response.text)
    allstory_values = get_allstats(parsed_allstory_response, allStatList, "story")

    return render_template('story.html', story_values=story_values, allstory_values=allstory_values)


@app.route('/dungeon-data')
def dungeon_data():
    param_list = request.args.getlist('param')
    dungeon_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/Activities/?count=20&mode=82&page=0"

    dungeon_response = requests.get(dungeon_endpoint, headers=headers)
    parsed_dungeon_response = json.loads(dungeon_response.text)
    dungeon_values = get_stats(parsed_dungeon_response, statList)

    alldungeon_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/?groups=102&modes=82&periodType=AllTime"

    alldungeon_response = requests.get(alldungeon_endpoint, headers=headers)
    parsed_alldungeon_response = json.loads(alldungeon_response.text)
    alldungeon_values = get_allstats(parsed_alldungeon_response, allStatList, "dungeon")

    return render_template('dungeon.html', dungeon_values=dungeon_values, alldungeon_values=alldungeon_values)


@app.route('/dares-data')
def dares_data():
    param_list = request.args.getlist('param')
    dares_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/Activities/?count=20&mode=85&page=0"

    dares_response = requests.get(dares_endpoint, headers=headers)
    parsed_dares_response = json.loads(dares_response.text)
    dares_values = get_stats(parsed_dares_response, statList)

    alldares_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/?groups=102&modes=85&periodType=AllTime"

    alldares_response = requests.get(alldares_endpoint, headers=headers)
    parsed_alldares_response = json.loads(alldares_response.text)
    alldares_values = get_allstats(parsed_alldares_response, allStatList, "dares")

    return render_template('dares.html', dares_values=dares_values, alldares_values=alldares_values)


@app.route('/lostsector-data')
def lostsector_data():
    param_list = request.args.getlist('param')
    lostsector_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/Activities/?count=20&mode=87&page=0"

    lostsector_response = requests.get(lostsector_endpoint, headers=headers)
    parsed_lostsector_response = json.loads(lostsector_response.text)
    lostsector_values = get_stats(parsed_lostsector_response, statList)

    alllostsector_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/?groups=102&modes=87&periodType=AllTime"

    alllostsector_response = requests.get(alllostsector_endpoint, headers=headers)
    parsed_alllostsector_response = json.loads(alllostsector_response.text)
    alllostsector_values = get_allstats(parsed_alllostsector_response, allStatList, "lost_sector")

    return render_template('lost-sector.html', lostsector_values=lostsector_values,
                           alllostsector_values=alllostsector_values)


@app.route('/nightmarehunt-data')
def nightmarehunt_data():
    param_list = request.args.getlist('param')
    nightmarehunt_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/Activities/?count=20&mode=79&page=0"

    nightmarehunt_response = requests.get(nightmarehunt_endpoint, headers=headers)
    parsed_nightmarehunt_response = json.loads(nightmarehunt_response.text)
    nightmarehunt_values = get_stats(parsed_nightmarehunt_response, statList)

    allnightmarehunt_endpoint = f"https://www.bungie.net/Platform/Destiny2/{param_list[0]}/Account/{param_list[1]}/Character/{param_list[2]}/Stats/?groups=102&modes=79&periodType=AllTime"

    allnightmarehunt_response = requests.get(allnightmarehunt_endpoint, headers=headers)
    parsed_allnightmarehunt_response = json.loads(allnightmarehunt_response.text)
    allnightmarehunt_values = get_allstats(parsed_allnightmarehunt_response, allStatList, "nightmare_hunt")

    return render_template('nightmarehunt.html', nightmarehunt_values=nightmarehunt_values,
                           allnightmarehunt_values=allnightmarehunt_values)


if __name__ == '__main__':
    app.run()
