### TODO
### settings.db comment
### main cycle?

### Imports

from rich.progress import Progress
# from rich.layout import Layout
from rich import inspect

from prompt_toolkit import print_formatted_text, prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from os import name as osName, system, listdir, chdir, get_terminal_size as terminalSize
from os.path import getmtime, exists, dirname, abspath

from random import random, choice, choices, randint, normalvariate
from questionary import select as questionary, Choice
from colorama import just_fix_windows_console
from pathvalidate import is_valid_filename
from yaml import safe_load, safe_dump
from traceback import format_exc
from sys import exit as sysExit
from datetime import datetime
from hashlib import sha3_224 as hash
from time import sleep, time

### File variables

dirs = {
    'db': 'database/',
    'saves': 'saves/',
    'setups': 'setups/',
    'custom': 'customisation/',
}
files = {
    'settings': dirs['custom'] + 'settings.db',
    'style': dirs['custom'] + 'style.db',
    'nations': dirs['db'] + 'nations.db',
    'names': dirs['db'] + 'names.db',
    'leagues': dirs['db'] + 'leagues.db',
    'positions': dirs['db'] + 'positions.db',
    'traits': dirs['db'] + 'traits.db',
    'frames': dirs['db'] + 'frames.db',
}
comments = {file: '' for file in files.keys()}
dbFiles = {a: b for a, b in files.items() if dirs['db'] in b}
FILE_EXTENSION = '.plc'
DATABASE_FILE_EXTENSION = '.db'

### Constants

origPrint = print
origInput = input
DOUBLE_BACKSLASH_N = '\\n'
BACKSLASH_N = '\n'
LINE = '\u2500'
SLASH = '/'
SINGLE_QUOTE = "'"
LESS = '&lt;'
MORE = '&gt;'
ALL_POINTS = 300
MAX_POINTS = 80
MIN_POINTS = 20

DEV_MODE = True

### Decorators

def timer(func):
    '''
    Prints how much time it took for a function to finish.
    '''
    def wrapper(*args, **kwargs):
        before = time()
        result = func(*args, **kwargs)
        delta = time() - before
        input(f'@timer:   {func.__name__}() returned the result in {delta}s.')
        return result
    return wrapper

### Text functions

def input(*message, sep: str = ' ', default: str = "", completer = None) -> str:
    '''
    Like traditional `input()` but supports colored text in prompt_toolkit's HTML format.\n
    Can print strings, integers, tuples, etc., but not objects.\n
    Be careful when printing anything that contains < and > as these may cause an error in prompt_toolkit.\n
    Returns the string that the user inputs.
    '''
    message = sep.join([str(part) for part in message])
    try:
        return prompt(HTML(message), style = mainStyle, default = default, completer = completer)
    except Exception:
        return origInput(message)

def print(*values, sep: str = ' ', end: str = '\n') -> None:
    '''
    Like traditional `input()` but supports colored text in prompt_toolkit's HTML format.\n
    Can print strings, integers, tuples, etc., but not objects.\n
    Be careful when printing anything that contains < and > as these may cause an error in prompt_toolkit.
    '''
    values = sep.join([str(part) for part in values])
    try:
        print_formatted_text(HTML(values), end = end, style = mainStyle)
    except Exception as e:
        origPrint(values)

def richFormat(text: str) -> str:
    '''Formats prompt_toolkit's HTML formatted text to match Rich formatting.'''
    toReplace = {f'<{code}>': f'[{color.replace("bg:", "on ")}]' for code, color in mainStyleDict.items()}
    toReplace.update({f'</{code}>': '[/]' for code in mainStyleDict.keys()})
    for old, new in toReplace.items():
        text = text.replace(old, new)
    return text

def colorDoubleText(text: str, color: str) -> list[str]:
    '''Like `colorText()` but returns a list of 2 elements: colored usual text and colored capitalised text.'''
    return [colorText(text, color), colorText(text.capitalize(), color)]

def uncolorText(text: str) -> str:
    '''Deletes all HTML color codes from `text`.'''
    try:
        for code in mainStyleDict.keys():
            text = text.replace(f'<{code}>', '').replace(f'</{code}>', '')
    except NameError:
        pass
    return text

def alignText(text: str, width: int, align: str, fill = ' ', autoFix = True) -> str:
    '''
    Returns aligned `text`. Designed to work with colored text.\n
    Align must be 'left', 'center' or 'right'.\n
    If `autoFix` is True and `fill` is not ' ', adds spaces between the fill and the separators to make the output look nicer. Set `autoFix` to False to disable this.\n
    `alignText('My liney header', 25, 'center', fill='\u2500')` -> `'\u2500\u2500\u2500\u2500 My liney header \u2500\u2500\u2500\u2500'\n`
    `alignText('My liney header', 25, 'center', fill='\u2500', autoFix=False)` -> `'\u2500\u2500\u2500\u2500\u2500My liney header\u2500\u2500\u2500\u2500\u2500'`
    '''
    if fill != ' ' and text and autoFix:
        text = f'{" " if align in ["center", "right"] else ""}{text}{" " if align in ["center", "left"] else ""}'
    newWidth = width + len(text) - len(uncolorText(text))
    match align.lower():
        case 'left':
            text = text.ljust(newWidth, fill)
        case 'center':
            text = text.center(newWidth, fill)
        case 'right':
            text = text.rjust(newWidth, fill)
        case _:
            raise ValueError(f'alignText(): align must be "left", "center" or "right", not {align}.')
    return text

def colorSettingValue(value: str, mode: str = 'html') -> str | list[str]:
    '''
    Returns colored `value` (Yes in green for Yes, No in red for No, etc).\n
    `mode` must be 'html' or 'color'.\n
    If `mode` is 'html' (default), returns `value` that is colored using prompt_toolkit's HTML format.\n
    If `mode` is 'color', returns [`value`, `color`], where `color` is 'green', for example.
    '''
    match mode:
        case 'html':
            if value.lower() == 'yes':
                return f'<ugreen>{value}</ugreen>'
            if value.lower() == 'no':
                return f'<ured>{value}</ured>'
        case 'color':
            if value.lower() == 'yes':
                return [value, 'green']
            if value.lower() == 'no':
                return [value, 'red']
        case _:
            raise ValueError(f'colorSettingValue(): mode must be "html" or "color", not {mode}.')

def clear() -> None:
    '''Clears the terminal.'''
    if osName == 'nt':
        system('cls')
    else:
        system('clear')

### Encoding/decoding functions

def saveData(filePath: str, data, allowExceptions: bool = False) -> bool:
    '''
    Saves `data` to `filePath` in YAML.\n
    Returns True if saving was successful or False if there was an error.\n
    Raises an Exception instead of returning False if `allowException` is True.
    '''
    try:
        with open(filePath, 'wb') as f:
            f.write(dataToYAML(data))
        return True
    except Exception as e:
        if allowExceptions:
            raise ValueError(f'Failed to save data to {filePath}:\n{e}\n')
        return False
    
def loadData(filePath: str, allowExceptions: bool = True, modifyComments: bool = False):
    '''
    Loads data in YAML from `filePath`.\n
    Returns the data if loading was successful or False if there was an error.\n
    Raises an Exception instead of returning False if `allowException` is True.\n
    Saves the first comment (must start on character 1 of the file) to the `comments` dictionary if `modifyComments` is True.
    '''
    try:
        with open(filePath, 'r', encoding = 'utf-8') as f:
            contents = f.read()
            splitContents = contents.splitlines()
            for commentLength, line in enumerate(splitContents):
                if not line or line[0] != '#':
                    break
            if modifyComments and commentLength:
                comments[filePath.split('/')[1]] = '\n'.join(splitContents[:commentLength])
            return safe_load(contents)
    except Exception as e:
        if allowExceptions:
            raise ValueError(f'Failed to load data from {filePath}:\n{e}\n')
        return False

def dataToYAML(data) -> bytes:
    '''Transforms `data` to YAML.'''
    return safe_dump(data, encoding = 'utf-8', allow_unicode = True, sort_keys = False)

def yamlToHash(data: bytes) -> str:
    '''
    Hashes `data`.
    `data` must be in YAML.
    '''
    return hash(data + b' - - - very, very secret key - - - ').hexdigest()

def dataToHash(data) -> str:
    '''Hashes `data`.'''
    return yamlToHash(dataToYAML(data))

def isValidChangeDate(file: str, changeDate) -> bool:
    '''Checks if `changeDate` matches the system-coded change date of the file.'''
    return getmtime(file) - float(changeDate) < .1

def getTime() -> float:
    '''Shortcut for `datetime.datetime.now.timestamp()`.'''
    return datetime.now().timestamp()

### Database functions

def getFiles(directory: str, extensions: list[str] = [FILE_EXTENSION, DATABASE_FILE_EXTENSION]) -> list[str]:
    '''Returns all flies from the given directory that share an extension with th given extensions.'''
    return [file for file in listdir(directory) if '.' + file.split('.')[-1] in extensions or not extensions]

def parseDatabase(pathsToCheck: list[str], funcsToCheck: list[callable], outputsToReturn: list[str] = [], progressValues: list[int] = [2 for _ in range(len(files.values()))]) -> list:
    '''
    Checks that all paths in `pathsToCheck` exist and calls each function in `funcsToCheck`.\n
    Returns the output of a function if the file corresponding to it (taken from the files dictionary) is in `outputsToReturn`.
    '''
    def checkPaths(progressBars: bool = True):
        toReturn = []
        for pathToCheck in pathsToCheck:
            if not exists(pathToCheck):
                errorList.append(f'{"Directory" if pathToCheck[-1] == SLASH else "File"} "{pathToCheck}" doesn\'t exist.')
            if progressBars:
                bar.update(task, advance = 1)
        for file, func, value in zip(files.values(), funcsToCheck, progressValues):
            if exists(file):
                try:
                    output = func(progressBars, bar if progressBars else None, task if progressBars else None, value if progressBars else 0)
                    if file in outputsToReturn:
                        toReturn.append(output)
                except Exception as e:
                    exc = e
                    try:
                        if DEV_MODE or settings.excTraceback:
                            exc = '\n' + format_exc()
                    except (NameError, AttributeError):
                        pass
                    errorList.append(f'{type(e).__name__} in {file}: {exc}')
        if progressBars:
            bar.update(task, advance=100)
        return toReturn
    errorList = []
    if progressBarSetting():
        with Progress() as bar:
            task = bar.add_task('[green]Checking database data...', total = len(pathsToCheck) + sum(progressValues))
            toReturn = checkPaths()
    else:
        toReturn = checkPaths(False)
    sleep(1)
    if errorList:
        clear()
        origPrint(f'The database is corrupted.\nIf you moved or edited any files from the game directory, please revert the changes or reinstall the game in case you can\'t.\n\nThe following error{"s" if len(errorList) > 1 else ""} occured:')
        for i, error in enumerate(errorList, 1):
            origPrint(f'{i}. {error}')
        raiseFatalError()
    return toReturn

def createLeagues(progress: bool = False, bar = None, task = None, value: int | float = 0) -> None:
    '''
    Creates all League and Club objects from `files['leagues']`.
    Generates all Player objects using `files['frames']` and `files['names']` as well.\n
    If `progress` is True, updates `bar`'s `task` smoothly until all settings are created.
    The amount the bar will move by is determined by `value`.
    '''
    Player.instances = []
    Club.instances = []
    League.instances = []
    global freeAgents
    freeAgents = Club(0, 'Free agents', ['Free agents'], 'Free agents', '\u2500' * 3, ['ublack', 'uwhite'])
    freeAgents.players = []
    Nation(['Free agents'], 'u\2500' * 3, 'free agent', 'ublack', -1, [], [])
    League('Free agents', Nation.instances.pop(), [freeAgents])
    League.instances.pop()
    global frames
    frames = loadData(files['frames'])
    leaguesData = loadData(files['leagues'], modifyComments = True)
    if progress:
        bar.update(task, advance=value / 2)
    for leagueData in leaguesData:
        leagueData['nation'] = Nation.find(leagueData['nation'], True)
        leagueClubs = []
        for clubData in leagueData['clubs']:
            if str(clubData['rating'])[-1] == '!':
                clubData['rating'] = OPTAtoRating(clubData['rating'][:-1])
            if not 27 <= clubData['rating'] <= 87:
                raise DatabaseError(f'Rating of clubs must be between 27 and 87 (0 and 100 in OPTA power rankings), while {clubData["names"][0]}\'s is {clubData["rating"]}.')
            for name in clubData['names'] + [clubData['nickname']]:
                if not 1 <= len(name) <= 25:
                    raise DatabaseError(f'Length of generic names and nicknames must be between 1 and 25, while {name}\'s is {len(name)}.')
            if len(clubData['shortName']) != 3:
                raise DatabaseError(f'Length of club short names must be 3, while {clubData["shortName"]}\'s is {len(clubData["shortName"])}.')
            leagueClubs.append(Club(clubData['rating'], clubData['fullName'], clubData['names'], clubData['nickname'], clubData['shortName'], clubData['colors']))
            club = leagueClubs[-1]
            foreignPercent = 1 - (clubData['rating'] - 40) ** 1.5 / 550 - max(0, 70 - clubData['rating']) / 150
            club.players = []
            playerCount = randint(26, 39)
            positionProbs = {pos: 1 for pos in Position.instances}
            for i in range(playerCount):
                i *= 40 / (playerCount - 1)
                pos = choices(list(positionProbs.keys()), list(positionProbs.values()))[0]
                positionProbs[pos] /= 4
                rating = clubData['rating'] - 1.2 * i ** .5 - max(0, i - 10) ** 2 / 60 + 6 * random() + 3
                age = max(15, round(normalvariate(29 - (i + 1) ** 3 / 6400, 3.5 + i / 20)))
                potential = rating + max(0, 30 - age) ** ((age + 25) / 30) * (i - 10) ** 2 / 1600 + random() * (35 - age) / 3 - 2
                nation = leagueData['nation'] if random() < foreignPercent else choices(Nation.instances, [(len(Nation.instances) - j + 100) ** 8 for j in range(101, len(Nation.instances) + 101)])[0]
                club.players.append(Player(
                    nation=nation,
                    rating=rating,
                    potential=potential,
                    position=pos,
                    age=age,
                    squad='first team',
                ))
                club.players[-1].club = club
            freeAgent = choice(sorted(club.players, key=lambda x: x.rating, reverse=True)[11:])
            freeAgent.club.players.remove(freeAgent)
            freeAgent.club = freeAgents
        League(leagueData['name'], leagueData['nation'], leagueClubs)
        if progress:
            bar.update(task, advance= value / len(leaguesData))

    clubShortNames = [club.ucShortName for club in Club.instances]
    seenShortNames = set()
    duplicateShortNames = set()
    for x in clubShortNames:
        if x in seenShortNames:
            duplicateShortNames.add(x)
        else:
            seenShortNames.add(x)
    if duplicateShortNames:
        raise DatabaseError(f'There {"are" if len(duplicateShortNames) > 1 else "is a"} duplicate club short name{"s" if len(duplicateShortNames) > 1 else ""}: {", ".join(duplicateShortNames)}.')

def createPositions(progress: bool = False, bar = None, task = None, value: int | float = 0) -> None:
    '''
    Creates all Position objects from `files['positions']`.\n
    If `progress` is True, updates `bar`'s `task` smoothly until all settings are created.
    The amount the bar will move by is determined by `value`.
    '''
    Position.instances = []
    positions = loadData(files['positions'])
    if progress:
        bar.update(task, advance=value / 2)
    for position in positions:
        Position(position['shortName'], position['name'], position['color'], list(position['weightings'].values()), position['setPieceKoe'], position['modifier'])
        if progress:
            bar.update(task, advance=value / len(positions))

def createNations(progress: bool = False, bar = None, task = None, value: int | float = 0) -> None:
    '''
    Creates all Nation objects from `files['nations']` and `files['names']`.\n
    If `progress` is True, updates `bar`'s `task` smoothly until all settings are created.
    The amount the bar will move by is determined by `value`.
    '''
    Nation.instances = []
    nations = loadData(files['nations'])
    names = loadData(files['names'])
    if progress:
        bar.update(task, advance=value / 2)
    for i, data in enumerate(zip(nations, names), 1):
        nation, names = data
        for name in names['firstNames'] + names['lastNames']:
            if not 2 <= len(name) <= 25:
                raise Exception(f'Length of people names must be between 2 and 25, while {name}\'s is {len(name)}.')
        Nation(nation['names'], nation['shortName'], nation['nationality'], nation['color'], i, names['firstNames'], names['lastNames'])
        if progress:
            bar.update(task, advance=value / len(nations) / 2)

def createTraits(progress: bool = False, bar = None, task = None, value: int | float = 0) -> None:
    '''
    Creates all Trait objects from `files['traits']`.\n
    If `progress` is True, updates `bar`'s `task` smoothly until all settings are created.
    The amount the bar will move by is determined by `value`.
    '''
    Trait.instances = []
    traits = loadData(files['traits'])
    wfExists = False
    if progress:
        bar.update(task, advance=value / 2)
    for trait in traits:
        if trait['name'] == 'Weak Foot':
            wfExists = True
        Trait(trait['name'], trait['description'], trait['color'], trait['category'])
        if progress:
            bar.update(task, advance=value / len(traits))
    if not wfExists:
        raise Exception('A trait with the name "Weak Foot" must exist.')

def createStyle(progress: bool = False, bar = None, task = None, value: int | float = 0) -> dict[str: str]:
    '''
    Creates all Style objects from `files['style']`.\n
    If `progress` is True, updates `bar`'s `task` smoothly until all settings are created.
    The amount the bar will move by is determined by `value`.
    '''
    data = loadData(files['style'])
    if progress:
        bar.update(task, advance=value / 2)
    styleDict = {}
    for code, color in data.items():
        if progress:
            bar.update(task, advance=value / len(data.values()))
        if code[-1] == '!':
            styleDict[code[:-1]] = color
            continue
        styleDict[code] = color
        styleDict[f'bg{code}'] = f'bg:{color}'
    return styleDict

def saveSetup(hero) -> None:
    '''Saves the `hero` to a file.'''
    while True:
        clear()
        filePath = input('<ugreen>Let\'s save your starting setup!</ugreen>\n<uyellow>Choose the name of the file it will be saved in:</uyellow> ', default = hero.ucFullName) + FILE_EXTENSION
        print()
        if filePath == FILE_EXTENSION:
            input('<ured>The name of your setup can\'t be empty.\nPress Enter to continue:</ured> ')
            continue
        if not is_valid_filename(filePath):
            input('<ured>This file name is invalid, please try another one.\nPress Enter to continue:</ured> ')
            continue
        if filePath in getFiles(dirs['setups']):
            if not yesNoMenu(f'There is already a setup called {removeExtension(filePath)}. Do you want to replace it with this one?'):
                continue
        try:
            heroPrep = {
                'hero': hero.toDict(),
                'time': getTime()
            }
            heroPrep['hash'] = dataToHash(heroPrep)
            saveData(dirs['setups'] + filePath, heroPrep, True)
        except Exception as e:
            print('<ured>An error occured while trying to save your setup:</ured>', end=' ')
            origPrint(e)
            input('\n<ured>Please try a different file name.\nPress Enter to continue.</ured> ')
            continue
        print('\n<dgreen>Your setup was successfully saved!</dgreen>')
        sleep(1)
        break

def loadSetup():
    '''Loads a hero setup, creates a Hero object and returns it.'''
    hero = 0
    while True:
        clear()
        setupFiles = sorted(getFiles(dirs['setups']), key=lambda x: getmtime(dirs['setups'] + x), reverse=True)
        setupNumber = menu('Choose a setup to load:', [MenuOption(removeExtension(option), description=datetime.fromtimestamp(getmtime(dirs['setups'] + option)).strftime('This hero setup was created at %H:%M %B %d, %Y.'), value = i) for i, option in enumerate(setupFiles, 1)] + [MenuOption('Quit', 'dred', 'Quit to the main menu.', 'quit')], default='quit')
        if setupNumber == 'quit':
            break
        filePath = dirs['setups'] + setupFiles[setupNumber - 1]
        try:
            decodedHeroPrep = loadData(filePath)
            decodedHash = decodedHeroPrep.pop('hash')
            try:
                hashFlag = decodedHash != dataToHash(decodedHeroPrep)
                timeFlag = not isValidChangeDate(filePath, decodedHeroPrep['time'])
                if hashFlag and timeFlag:
                    raise ValueError('B001')
                if hashFlag:
                    raise ValueError('H001')
                if timeFlag:
                    raise ValueError('T001')
            except ValueError as e:
                input(f'<ured>This setup was modified.\nPress Enter to continue:</ured> ')
                continue
            hero = Hero(decodedHeroPrep['hero'])
            hero.club.players.append(hero)
            print('<dgreen>Your setup was successfully loaded!</dgreen>')
            sleep(1)
            break
        except Exception as e:
            print(f'<ured>This setup is corrupted. The following error occured:</ured>', end=' ')
            origPrint(f'{e}')
            input(f'<ured>Press Enter to continue:</ured> ')
    return hero

### Shortcut functions

def menu(title: str, options: list, help: str = ' ', default = None):
    '''
    Asks a questionary and returns the chosen answer.\n
    `options` must be instances of the MenuOption class.
    '''
    sleep(.1)
    menuOptions = [Choice(option if isinstance(option, str) else [('class:' + option.color, option.text)], value = option.returnValue, description = option.description.replace('\n', '\n               ') if option.description else option.description) for option in options]
    result = questionary(title.replace('\n', '\n '), menuOptions, instruction = help, qmark = '', style = mainStyle, default = default).ask()
    if result == None:
        return menu(title, options, help, default)
    if result == '!None':
        return
    return result

def notReadyWarning():
    print('<dyellow>This feature is temporarily unavailable and will be coming in a future update.\nStay tuned!\n</dyellow>')
    input('<uyellow>Press Enter to continue.</uyellow> ')

def raiseFatalError() -> None:
    '''Exits the application after an error.'''
    origInput('\nPress Enter to terminate the application. ')
    sysExit()

### Menus and rankings

def yesNoMenu(text, default = 'Yes') -> bool:
    '''
    Creates a simple Yes or No menu with a title of `text` and with the pointer set to `default`.\n
    Returns True if Yes was chosen and False otherwise.
    '''
    options = [MenuOption('Yes', color = 'ugreen'), MenuOption('No', color = 'ured')]
    choice = menu(text, options, default = default)
    return choice == 'Yes'

def startingMenu() -> str:
    '''
    Creates the starting menu. Can return:
    - 'new-hero'
    - 'load-setup'
    - 'load-game'
    - 'rankings'
    - 'settings'
    - 'quit'
    '''
    clear()
    options = [
        MenuOption('Create your first hero!', 'ugreen', 'Let\'s start your first game! Your hero is destined for success.', 'new-hero'),
        MenuOption('View rankings', 'uyellow', 'View worldwide rankings of football leagues, clubs, etc.', 'rankings'),
        MenuOption('Go to settings', 'uwhite', 'Customise your game.', 'settings'),
        MenuOption('Quit', 'dred', 'Quit the game.\nBut you won\'t pick this, right?', 'quit')
    ]
    if saveFiles:
        options.insert(1, MenuOption('Load a game', 'gyellow', 'Load a game from an existing save file.', 'load-game'))
        options[0].text = 'Start a new game'
        options[0].description = 'Create a new hero and start a new game with him.'
    if setupFiles:
        options.insert(1, MenuOption('Start a new game with an existing hero', 'ygreen', 'Choose a hero you have already created and start a new game with him.\nThe career will begin when he is 16 years old.', 'load-setup'))
        options[0].text = 'Start a new game with a new hero'
        options[0].description = 'Create a new hero and start a new game with him.'
    return menu('Welcome to Career! What do you want to do?', options, help = ' ' if setupFiles or saveFiles else '(use arrow keys, press Enter to confirm your choice)')

def rankingsMenu() -> str:
    '''
    Creates the rankings menu. Can return:
    - 'nations'
    - 'leagues'
    - 'clubs'
    - 'players'
    - 'quit'
    '''
    clear()
    options = [
        MenuOption('Nations', 'ugreen', 'View FIFA nation rankings.', 'nations'),
        MenuOption('Leagues', 'cgreen', 'View worldwide rankings of every league in the game based on the rating of their clubs.', 'leagues'),
        MenuOption('Clubs', 'gcyan', 'View worldwide rankings of every club in the game based on their rating.', 'clubs'),
        MenuOption('Players', 'ucyan', 'View worldwide rankings of every player in the game based on their rating or potential.', 'players'),
        MenuOption('Quit', 'dred', 'Quit to the main menu.', 'quit'),
    ]
    toReturn = menu('Which rankings do you want to view?', options, default='quit')
    clear()
    return toReturn

def leagueRankingsMenu():
    '''
    Creates the league rankings menu. Can return:
    - 'average'
    - 'top'
    - 'median'
    - 'quit'
    '''
    clear()
    leagueOptions = [
        MenuOption('Average (default)', 'ugreen', 'Sorts the leagues by the average rating of their clubs.', 'average'),
        MenuOption('Top half average', 'cgreen', 'Sorts the leagues by the average rating of their clubs that are in the top half of the table by this parameter.', 'top'),
        MenuOption('Median', 'gcyan', 'Sorts the leagues by the median rating of their clubs.', 'median'),
        MenuOption('Quit', 'dred', 'Quit to the rankings menu.', 'quit'),
    ]
    toReturn = menu('What do you want to sort them by?', leagueOptions)
    clear()
    return toReturn

def playerRankingsMenu():
    '''
    Creates the player rankings menu. Can return:
    - 'rating'
    - 'potential'
    - 'quit'
    '''
    clear()
    leagueOptions = [
        MenuOption('Rating (default)', 'gcyan', 'Sorts the players by their rating.', 'rating'),
        MenuOption('Potential', 'ucyan', 'Sorts the players by their potential.', 'potential'),
        MenuOption('Quit', 'dred', 'Quit to the rankings menu.', 'quit'),
    ]
    toReturn = menu('What do you want to sort them by?', leagueOptions)
    clear()
    return toReturn

def academyMenu(hero: dict):
    '''
    Generates offers made for the player from academies and lets the user select between them.
    Returns the club the user has chosen. Needs `hero` (data) to work.
    '''
    offersFrom = []
    while len(offersFrom) < 2:
        offersFrom = list(set(choices(Club.instances, [(i + (len(Club.instances) if club.nation is hero['nation'] else 1)) ** 1.5 for i, club in enumerate(Club.instances)], k=choice([2] * 3 + [3] * 4 + [4] * 2 + [5]))))
    options = [MenuOption(club.ucName, club.colors[0], f'{club.ucName} want {hero['fullName']} to join their academy.\nTheir senior team plays in the {club.league.ucName} which is {club.nation.ucName}\'s {"top flight" if club.league.level == 1 else f"{ordinal(club.league.level)} division"}.', club) for club in offersFrom] + [MenuOption('Reject all offers', 'dred', 'Reject all offers and stay without a club.', freeAgents)]
    try:
        while True:
            clear()
            result = menu('Your skills have attracted interest from multiple clubs! Pick the one you want to examine or sign a contract with.', options)
            if not result is freeAgents:
                result.viewProfile('<uyellow>Press Enter to continue:</uyellow> ')
            while True:
                if yesNoMenu(f'{"Do" if not result is freeAgents else "Are you sure"} you want to {f"sign a contract with {result.ucName}" if not result is freeAgents else " reject all offers and stay a free agent"}?', default='No'):
                    clear()
                    if input(f'<uorange>This is an important decision and there is no going back.</uorange>\n<uyellow>Type "{"sign" if not result is freeAgents else "free"}" if you truly want to {f"sign a contract with {result.ucName}" if not result is freeAgents else "stay a free agent"}.</uyellow> ').lower() in ['sign', '"sign"', 'free', '"free"']:
                        raise QuitError
                else:
                    break
    except QuitError:
        pass
    print(f'\n{"<dgreen>Great choice!</dgreen>\n<dyellow>Now " if not result is freeAgents else "<rorange>Bold choice...</rorange>\n<uorange>But who knows, maybe it will pay off?</uorange>\n<dyellow>Regardless, "}let\'s continue.</dyellow>')
    sleep(3 if not result is freeAgents else 6)
    return result

def viewNationRankings() -> None:
    '''Prints worldwide nation rankings.'''
    tableHeaders = ['№', Header('Code ', columnAlign = 'center'), 'Nation', 'Best league']
    tableRows = []
    for nation in Nation.instances:
        tableRows.append([nation.fifaRanking, nation.shortName, nation.name, nation.leagues[0].name if nation.leagues else f'!fill {LINE}', ])
    Table(tableRows, tableHeaders, '<bold>Worldwide national team rankings:</bold>', '<uyellow>Press Enter to go back to the start menu: </uyellow>').input()

def viewLeagueRankings(mode = 'average') -> None:
    '''Prints worldwide league rankings.'''
    tableHeaders = ['№', 'Rating', 'Code', 'League', 'Best clubs']
    tableRows = []
    for i, league in enumerate(sorted(League.instances, key = lambda x: x.getRating(mode), reverse=True), 1):
        tableRows.append([i, str(league.getRating(mode)).ljust(5, '0'), league.shortName, league.name, ', '.join([club.name for club in league.sortedClubs[:3]])])
    Table(tableRows, tableHeaders, '<bold>Worldwide football league rankings:</bold>', '<uyellow>Press Enter to go back to the start menu: </uyellow>').input()

def viewClubRankings() -> None:
    '''Prints worldwide club rankings.'''
    tableHeaders = ['№', Header('Rating', columnAlign = 'center'), Header('League', columnAlign = 'center'), 'Colors', Header('Code ', columnAlign = 'center'), 'Generic name', 'Nickname']
    tableRows = []
    for i, club in enumerate(sorted(Club.instances, key = lambda x: x.rating, reverse=True), 1):
        tableRows.append([i, str(round(club.rating, 2)).ljust(5, '0'), club.league.shortName, club.colorText('   ', bg = True) + club.color2Text('   ', bg = True), club.shortName, club.name, club.nickname])
    Table(tableRows, tableHeaders, '<bold>Worldwide football club rankings:</bold>', '<uyellow>Press Enter to go back to the start menu: </uyellow>').input()

def viewPlayerRankings(mode = 'rating') -> None:
    '''Prints worldwide player rankings.'''
    match mode:
        case 'rating':
            sortFunc = lambda x: x.rating
        case 'potential':
            sortFunc = lambda x: x.potential
    tableHeaders = ['№', 'Full name', 'Nation', 'Club', 'Pos', '2poses', Header('Pac', columnColor='uyellow'), Header('Sho', columnColor='ured'), Header('Pas', columnColor='ucyan'), Header('Dri', columnColor='umagenta'), Header('Dfn', columnColor='ugreen'), Header('Phy', columnColor='uwhite'), Header('Foot', 'left', columnColor='uorange'), Header('Age', columnColor='lbrown'), Header('OVR', columnColor='uwhite'), Header('POT', columnColor='dgreen')]
    tableRows = [[i, p.fullName, p.nation.name, p.club.shortName, p.position.shortName, p.shortSecondaryPositions, *p.iattributes, p.foot, p.age, p.irating, p.ipotential] for i, p in enumerate(sorted(Player.instances, key=sortFunc, reverse=True)[:1000], 1)]
    Table(tableRows, tableHeaders, '<bold>Top 1000 players in the database:</bold>', '<uyellow>Press Enter to go back to the start menu: </uyellow>').input()

### Misc functions

def OPTAtoRating(optaPowerRanking) -> float:
    '''
    Converts an OPTA Power Ranking to the in-game rating using this formula:\n
    `inGameRating = optaPowerRanking * 3 / 5 + 27`
    '''
    return round(float(optaPowerRanking) * 3 / 5 + 27, 1)

def removeExtension(file: str, extension: str = FILE_EXTENSION) -> str:
    '''Removes the given extension from the given file path.'''
    return file.replace(extension, '')

def progressBarSetting() -> bool:
    '''Same as `settings.viewProgress` but works before `settings` were created.'''
    try:
        return str(settings.viewProgress).lower() == 'yes'
    except:
        try:
            with open(files['settings'], encoding = 'utf-8') as f:
                return f.readlines()[3].find('Yes') != -1
        except:
            return False

def terminalWidth() -> int:
    return terminalSize()[0]

def terminalHeight() -> int:
    return terminalSize()[1]

def ordinal(n: int):
    if 11 <= (n % 100) <= 13:
        suff = 'th'
    else:
        suff = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suff

### Error classes

class DatabaseError(ValueError):
    pass

class QuitError(Exception):
    pass

### Placeholder classes

class Find:
    '''Placeholder for `find()`.'''
    @classmethod
    def find(cls, name, allowExceptions: bool = False):
        '''
        Returns an instance that corresponds to the given `name` or -1 if object was not found.
        Raises an Exception instead of returning -1 if `allowExceptions` is True.\n
        Each instance must have a `_searchOptions` attribute containing strings that the instance can be found by.
        All strings in `_searchOptions` must be uncolored and lowercase.
        '''
        newName = str(name).lower()
        if newName == 'free agents' or (hasattr(name, 'ucName') and name.ucName.lower() == 'free agents'):
            return freeAgents
        for obj in cls.instances:
            if newName in obj._searchOptions or name is obj:
                return obj
        if allowExceptions:
            raise DatabaseError(f'Couldn\'t find a {cls.__name__.lower()} named "{name}".')
        return -1

class ColorText:
    '''Placeholder for `colorText()`.'''
    def colorText(self, text: str, color: str = 'default') -> str:
        '''Colors `text` with `color` in prompt_toolkit's HTML format.'''
        if not color:
            return text
        if color == 'default':
            color = self.color
        return f'<{color}>{text}</{color}>'

### Classes

class Settings:
    '''
    Loads data in YAML from `files['settings']` and creates Setting objects from it.\n
    The settings are accessible from this object.\n
    Settings:
    - `.viewProgress`
    - `.excTraceback`
    - `.allowRussia`
    '''
    def __init__(self, progress: bool = False, bar = None, task = None, value: int | float = 0):
        '''
        If `progress` is True, updates `bar`'s `task` smoothly until all settings are created.
        The amount the bar will move by is determined by `value`.
        '''
        Setting.instances = []
        self._contents = loadData(files['settings'])
        if progress:
            bar.update(task, advance=value / 2)
        self._progress = progress
        self._bar = bar
        self._task = task
        self._value = value
        self.viewProgress = self.newSetting()
        self.excTraceback = self.newSetting()
        self.allowRussia = self.newSetting()
        del self._contents, self._progress, self._bar, self._task, self._value
    
    def save(self) -> None:
        '''Saves itself to `files['settings']`.'''
        data = []
        for setting in Setting.instances:
            data.append({
                'name': setting.name,
                'description': setting.description,
                'setTo': setting.setTo,
                'values': setting.values
            })
        if not saveData(files['settings'], data):
            clear()
            input('<ured>An error occured while trying to save the settings.\nPress Enter to continue: </ured>')

    def newSetting(self):
        '''Removes the first setting from `self._contents`, creates a new Setting object and returns it.'''
        if self._progress:
            self._bar.update(self._task, advance=self._value / len(self._contents))
        return Setting(self._contents.pop(0))

    def edit(self) -> None:
        '''Creates a pretty menu that allows the user to edit the settings.'''
        while True:
            print(self)
            setting = menu('Choose a setting to edit:', [MenuOption(setting.name, description = setting.description, value = setting) for setting in Setting.instances] + [MenuOption('Quit', 'dred', 'Quit to the main menu.', -1)])
            if setting == -1:
                break
            setting.edit()
        self.save()
    
    def __str__(self):
        return f'\n\n<uyellow>Your settings:</uyellow>\n\n{"".join([setting.view() for setting in Setting.instances])}'

class Setting:
    '''
    The class for a setting.\n
    Attributes:
    - `.name`: The name of the setting.
    - `.description`: The description of the setting.
    - `.setTo`: The value that the setting is set to.
    - `.values`: A list of values that the setting can be set to.
    - `.instances`: A list of all Setting instances.
    '''
    instances = []
    def __init__(self, data):
        '''
        Arguments:
        - `data`: A dictionary that contains the setting's `name`, `description`, `setTo` and `values`.
        '''
        self.__class__.instances.append(self)
        self.name = data['name']
        self.description = data['description'].replace(DOUBLE_BACKSLASH_N, BACKSLASH_N)
        self.setTo = data['setTo']
        self.values = data['values']
        if not self.setTo in self.values:
            raise DatabaseError(f'{self.name} setting: {self.setTo} is not in {self.values}.')
    
    def view(self) -> str:
        '''Get the string representation of the setting that is suitable for showing to the user.'''
        return f'{self.name}: {colorSettingValue(self.setTo)}.\n<ugrey>{self.description}</ugrey>\n\n'

    def edit(self) -> None:
        '''Creates a pretty menu that allows the user to edit a setting.'''
        self.setTo = menu('What do you want to change this setting to?', [MenuOption(*colorSettingValue(value, mode = 'color'), self.description, value) for value in self.values])
        clear()

    def __eq__(self, other):
        if isinstance(other, Setting):
            return self.__dict__ == other.__dict__
        return self.setTo == other
    
    def __str__(self):
        return self.setTo

class MenuOption:
    '''
    The class for a menu option.\n
    Attributes:
    - `.text`: The text of the option.
    - `.color`: The color of the text of the option.
    - `.description`: The description of the option (shown at the bottom while choosing).
    - `.returnValue`: Whatever `menu()` will return if the user chooses this option. .text by default.
    '''
    def __init__(self, text, color: str | None = None, description: str | None = None, value = None):
        '''
        Arguments:
        - `text`: The text of the option.
        - `color`: The color of the option. The option will have the default color if this is set to None.
        - `description`: The description of the option. The option will not have a description if this is set to None.
        - `value`: Whatever `menu()` will return if the user chooses this option. `text` by default.
        '''
        if not value:
            value = text
        if not color:
            color = ''
        self.color = color
        self.text = text
        self.description = description
        self.returnValue = value

class Table:
    '''
    The class for a table.\n
    Supports prompt_toolkit's HTML formatted text.\n
    Attributes:
    - `.style`: The table's style. To view an example of a style print `Table.defaultStyle`.
    - `.title`: The table's title.
    - `.caption`: The table's caption. Printed after the table.
    - `.noHeaders`: True if the table has no headers, False otherwise.
    - `.headers`: A list of Header objects. If the table has no headers, this will be full of automatically generated empty Header objects. Use `.noHeaders` to check for that if you need to.
    - `.data`: A list of Row objects.
    - `.columns`: Like `.data`, but instead of containing data grouped by rows in contains data grouped by columns. It is still a list of Row objects though.
    '''
    defaultStyle = {
    'leftTop': '┏',
    'leftTopBackup': '┌',
    'middleTop': '┳',
    'middleTopBackup': '┬',
    'rightTop': '┓',
    'rightTopBackup': '┐',
    'headerHor': '━',
    'headerVert': '┃',

    'leftMiddle': '┡',
    'middleMiddle': '╇',
    'rightMiddle': '┩',

    'leftBottom': '└',
    'middleBottom': '┴',
    'rightBottom': '┘',
    'dataHor': '─',
    'dataVert': '│',

    'fill': ' ',
    'headerFill': ' ',}

    def __init__(self, data: list, headers: list | None = None, title: str | None = None, caption: str | None = None, style: dict[str: str] = None):
        '''
        Arguments:
        - `data`: The table's rows. Can be a list of Row objects or a list of lists of cell values. Does not include headers.
        - `headers`: The table's headers. Can be a list of Header objects or a list of strings. If set to None, the table will have no headers.
        - `title`: The table's title. 
        - `caption`: Printed below the table.
        - `style`: `Table.defaultStyle` if set to None.
        '''        
        if style:
            self.style = style
            leftStyleKeys = Table.defaultStyle
            warning = []
            for key in self.style:
                try:
                    del leftStyleKeys[key]
                except KeyError:
                    warning.append(key)
            if leftStyleKeys:
                raise ValueError(f'The table\'s style is missing the following key{"s" if len(leftStyleKeys) > 1 else ""}: {", ".join(leftStyleKeys)}.{f" Warning: your style has additional keys that are not necessary ({', '.join(warning)})." if warning else ""}')
        else:
            self.style = Table.defaultStyle
        
        self.title = str(title) if title else title
        self.caption = str(caption) if caption else caption

        self.noHeaders = not headers
        self.headers = []
        if not self.noHeaders:
            for header in headers:
                if isinstance(header, str):
                    self.headers.append(Header(header))
                elif isinstance(header, (list, tuple)):
                    self.headers.append(Header(*header))
                else:
                    self.headers.append(header)
        else:
            self.headers = [Header('') for _ in data[0]]

        self.data = []
        for row in data:
            if isinstance(row, Row):
                self.data.append(row)
            else:
                self.data.append(Row(*row))
                
        self.columns = [Row(*column) for column in zip(*[row.cells for row in self.data])]
    
    def getPrintable(self) -> str:
        '''Get the representation of the table as a string.'''
        columnLens = [max(len(header.ucText), *[len(text) for text in column.ucCells]) for header, column in zip(self.headers, self.columns)]

        if not self.title:
            table = ''
        else:
            table = alignText(self.title, len(columnLens) * 3 + sum(columnLens) + 1, 'center', self.style['headerFill']) + '\n'

        if not self.noHeaders:
            table += f"{self.style['leftTop']}"
            for columnLen in columnLens:
                table += f"{self.style['headerHor'] * (columnLen + 2)}{self.style['middleTop']}"
            table = table[:-1] + self.style['rightTop'] + '\n'
            
            for columnLen, header in zip(columnLens, self.headers):
                table += self.style['headerVert'] + self.style['fill'] + alignText(header.text, columnLen, header.selfAlign, self.style['fill']) + self.style['fill']
            table += self.style['headerVert'] + '\n'
            
            table += f"{self.style['leftMiddle']}"
            for columnLen in columnLens:
                table += f"{self.style['headerHor'] * (columnLen + 2)}{self.style['middleMiddle']}"
            table = table[:-1] + self.style['rightMiddle'] + '\n'
        else:
            table += f"{self.style['leftTopBackup']}"
            for columnLen in columnLens:
                table += f"{self.style['dataHor'] * (columnLen + 2)}{self.style['middleTopBackup']}"
            table = table[:-1] + self.style['rightTopBackup'] + '\n'

        for row in self.data:
            for columnLen, header, cell in zip(columnLens, self.headers, row.cells):
                fill = self.style['fill']
                if cell.find('!fill ') != -1:
                    fill = cell[-1]
                    cell = ''
                table += self.style['dataVert'] + self.style['fill'] + alignText(colorText(cell, header.columnColor), columnLen, header.columnAlign, fill) + self.style['fill']
            table += self.style['dataVert'] + '\n'

        table += f"{self.style['leftBottom']}"
        for columnLen in columnLens:
            table += f"{self.style['dataHor'] * (columnLen + 2)}{self.style['middleBottom']}"
        table = table[:-1] + self.style['rightBottom'] + '\n'

        if self.caption:
            table += self.caption

        return table
    
    def input(self) -> str:
        '''Prints the table, captures the user's input and returnes it.'''
        return self.print(True)

    def print(self, inputToo: bool = False) -> None | str:
        '''
        Prints the table.
        Works like `input()` if `inputToo` is True.
        '''
        printable = self.getPrintable().splitlines()
        for line in printable[:-len(self.caption.splitlines()) if inputToo and self.caption else len(printable)]:
            print(line)
        if inputToo:
            return input(self.caption + ('' if uncolorText(self.caption)[-len(self.caption.splitlines())] == ' ' else ' ') if self.caption else '')

class Header:
    '''
    The class for a table header.\n
    Attributes:
    - `.text`: The header's text.
    - `.ucText`: The header's uncolored text.
    - `.selfAlign`: The header's alignment. Can be 'left', 'right' or 'center'.
    - `.columnAlign`: The alignment of every cell in the header's column. Can be 'left', 'right' or 'center'.
    - `.columnColor`: The color of every cell in the header's column.
    '''
    def __init__(self, text, selfAlign: str = 'center', columnAlign: str = 'left', columnColor: None | str = None):
        '''
        Arguments:
        - `text`: The header's text.
        - `selfAlign`: The header's alignment. Can be 'left', 'right' or 'center'.
        - `columnAlign`: The alignment of every cell in the header's column. Can be 'left', 'right' or 'center'.
        - `columnColor`: The color of every cell in the header's column.
        '''
        self.text = str(text)
        self.ucText = uncolorText(text)
        self.selfAlign = selfAlign
        self.columnAlign = columnAlign
        self.columnColor = columnColor

class Row:
    '''
    The class for a table row.\n
    Attributes:
    - `.cells`: A list of cell values.
    - `.ucCells`: Same as .cells, but contains uncolored text only.
    '''
    def __init__(self, *cells):
        '''
        Arguments:
        - `*cells`: Cell values.
        '''
        self.cells = [str(cell) for cell in cells]
        self.ucCells = [uncolorText(cell) for cell in self.cells]

class Nation(ColorText, Find):
    '''
    The class for a nation.\n
    Attributes:
    - `.fifaRanking`: The FIFA ranking of the nation.
    - `.leagues`: A list of League objects that belong to the nation.
    - `.clubs`: A list of Club objects that belong to the nation.
    - `.color`: The main color of the nation.
    - `.names`: A list of all names of the nation.
    - `.name`: The main name of the nation. Same as `.names[0]`.
    - `.shortName`: A unique 3 letter code that can be used to identify the nation.
    - `.nationality`: The nationality of people from the nation. Example: Finnish.
    - `.firstNames`: A list of first names of people from the nation.
    - `.lastNames`: A list of last names of people from the nation.
    - `.uc{Attribute}`: Same as `.{attribute}` but contains uncolored text instead of colored.
    - `.instances`: A list of all Nation instances.
    '''
    instances = []
    def __init__(self, names: list[str], shortName: str, nationality: str, color: str, fifaRanking: int, firstNames: list[str], lastNames: list[str]):
        '''
        Arguments:
        - `nationNames`: All names of the nation.
        - `shortName`: A unique 3 letter code that can be used to identify the nation.
        - `nationality`: The nationality of people from the nation. Example: Finnish.
        - `color`: The main color of the nation.
        - `fifaRanking`: The FIFA ranking of the nation.
        - `firstNames`: Some first names of the people of the nation.
        - `lastNames`: Some last names of the people of the nation.
        '''
        self.__class__.instances.append(self)
        self.color = color
        self.ucName = names[0]
        self.ucNames = names
        names = [self.colorText(name) for name in names]
        self.name = names[0]
        self.names = names
        self.shortName = self.colorText(shortName)
        self.ucShortName = shortName
        self.nationality = self.colorText(nationality)
        self.ucNationality = nationality
        self.fifaRanking = fifaRanking
        self.firstNames = firstNames
        self.lastNames = lastNames
        self.leagues = []
        self.clubs = []
        self._searchOptions = [str(self.fifaRanking), self.ucShortName.lower()] + [nationName.lower() for nationName in self.ucNames]

class Trait(ColorText, Find):
    '''
    Attributes:
    - `.color`: The color of the trait.
    - `.num`: The number of the trait. Starts at 1.
    - `.name`: The name of the trait.
    - `.description`: The description of the trait.
    - `.category`: The category of the trait.
    - `.uc{Attribute}`: Same as `.{attribute}` but contains uncolored text instead of colored.
    - `.instances`: A list of all Trait instances.
    '''
    instances = []
    def __init__(self, name: str, description: str, color: str, category: str):
        '''
        Arguments:
        - `name`: The name of the trait.
        - `description`: The description of the trait.
        - `color`: The color of the trait.
        - `category`: The category of the trait.
        '''
        self.__class__.instances.append(self)
        self.color = color
        self.num = self.colorText(len(self.__class__.instances))
        self.name = self.colorText(name)
        self.description = self.colorText(description)
        self.category = self.colorText(category)
        self.ucNum = len(self.__class__.instances)
        self.ucName = name
        self.ucDescription = description
        self.ucCategory = category
        self._searchOptions = [str(self.ucNum), self.ucName.lower()]

    @classmethod
    def printInstances(cls) -> None:
        '''Prints all of the traits.'''
        longestName = 0
        for instance in cls.instances:
            longestName = max(longestName, len(instance.ucName))
        for instance in cls.instances:
            print(f'{instance.num}{instance.colorText(".")}{"" if instance.ucNum >= 10 or len(Trait.instances) < 10 else " "} {instance.name}{" " * (longestName - len(instance.ucName))} {instance.colorText(LINE)} {instance.description}')

class Position(ColorText):
    '''
    The class for a position.\n
    Attributes:
    - `.weightings`: The weightings used to calculate the overall of a player.
    - `.setPieceKoe`: The probability of a player in this position having a set piece related trait.
    - `.modifier`: The modifier used to calculate the overall of a player.
    - `.color`: The color of the position.
    - `.name`: The full name of the position.
    - `.shortName`: The short name of the position.
    - `.uc{Attribute}`: Same as `.{attribute}` but contains uncolored text instead of colored.
    - `.instances`: A list of all Position instances.
    '''
    instances = []
    def __init__(self, shortName: str, name: str, color: str, weightings: list[float], setPieceKoe: float, modifier: float):        
        '''
        Arguments:
        - `shortName`: The short name of the position.
        - `name`: The full name of the position.
        - `color`: The color of the position.
        - `weightings`: The weightings used to calculate the overall of a player.
        - `setPieceKoe`: The probability of a player in this position having a set piece related trait.
        - `modifier`: The modifier used to calculate the overall of a player.
        '''
        self.__class__.instances.append(self)
        self.weightings = weightings
        self.setPieceKoe = setPieceKoe
        self.modifier = modifier
        self.color = color
        self.shortName = self.colorText(shortName)
        self.name = self.colorText(name)
        self.ucShortName = shortName
        self.ucName = name

class Player(ColorText):
    '''
    The class for a player.\n
    Attributes:
    - `.age`: The age of the player.
    - `.nation`: The nation of the player.
    - `.attributes`: Shortcut for `[.pac, .sho, .pas, .dri, .dfn, .phy]`.
    - `.foot`: The primary foot of the player (`'left'` or `'right'`).
    - `.traits`: A list of traits that the player has.
    - `.suit`: A dictionary containing a `float` for every position. The higher the `float`, the better the player is suited to this position. 0 is the maximum value of the `float`.
    - `.position`: The primary position of the player.
    - `.positions`: A list of all positions sorted by `.suit[position]` in descending order.
    - `.secondaryPositions`: A list of the secondary positions the player has.
    - `.fullSecondaryPositions`: A string that contains nicely formatted full names of the secondary positions the player has.
    - `.shortSecondaryPositions`: Same as `.fullSecondaryPositions` but contains short names insted of full.
    - `.squad`: The squad that the player is in. For example, `'U18'`.
    - `.description`: How the player is described by fans and media.
    - `.rating`: The short name of the position.
    - `.potential`: The short name of the position.
    - `.fullName`: The short name of the position.
    - `.shirtName`: The short name of the position.
    - `.uc{Attribute}`: Same as `.{attribute}` but contains uncolored text instead of colored.
    - `.i{attribute}`: Same as `.{attribute}` but is of type `int` instead of `float`.
    - `.instances`: A list of all Position instances.
    '''
    instances = []
    def __init__(self, nation: Nation | None, rating: float | None, potential: float | None, position: Position | None = None, age: int | float = 16, squad: str = ''):
        '''
        Arguments:
        - `nation`: The nation of the player.
        - `rating`: The rating of the player.
        - `potential`: The potential of the player.
        - `position`: The primary position of the player.
        - `age`: The age of the player.
        - `squad`: The squad that the player is currently in. For example, `'U18'`.
        '''
        self.__class__.instances.append(self)
        self.age = age
        if isinstance(self, Hero):
            self.squad = 'U18'
            self.potential = 80 + 15 * random()
            return self
        self.nation = nation
        self.attributes = [min(99, attrib + rating + sum([random() - .5 for _ in range(6)])) for attrib in choice(frames[round(rating)][position.ucShortName])]
        self.foot = 'right' if random() < .8 else 'left'
        self.traits = []
        categories = [(self.phy + self.pac) / 2, self.sho, (self.pas + self.dri) / 2, self.dfn]
        weightings = [cat ** 15 for cat in categories]
        wsum = sum(weightings)
        weightings = [w / wsum / (1 + position.setPieceKoe) for w in weightings] + [position.setPieceKoe]
        traitNum = max(1, round(normalvariate(2.5, 1)))
        while len(self.traits) < traitNum:
            toAppend = Trait.instances[choices([randint(i, i + 4) for i in range(0, 21, 5)], weights=weightings)[0]]
            if not toAppend in self.traits:
                self.traits.append(toAppend)
        self.suit = self.genSuit(position)
        # input(str({a.ucName: self.rating + b for a, b in zip(self.suit.keys(), self.suit.values())}) + '\n' + str(self.attributes) + '\n')
        self.potential = min(99, max(self.rating, potential))
        self.squad = squad
        self.ucShirtName = choice(self.nation.lastNames)
        self.ucFullName = f'{choice(self.nation.firstNames)} {self.ucShirtName}'
        self.fullName = self.colorText(self.ucFullName)
        self.shirtName = self.colorText(self.ucShirtName)

    @property
    def position(self) -> Position:
        return self.positions[0]
        
    @property
    def secondaryPositions(self) -> list[Position]:
        toReturn = []
        positions = self.positions
        positions.remove(self.position)
        for position in positions[1:]:
            if self.suit[position] >= -.5:
                toReturn.append(position)
        return toReturn
    
    @property
    def fullSecondaryPositions(self) -> str:
        return ', '.join([pos.name for pos in self.secondaryPositions]) if self.secondaryPositions else 'none'
    
    @property
    def shortSecondaryPositions(self) -> str:
        sp = self.secondaryPositions
        if len(sp) > 3:
            return ', '.join([pos.shortName for pos in sp[:2]]) + ', ...'
        elif sp:
            return ', '.join([pos.shortName for pos in sp])
        return 'none'
    
    @property
    def positions(self) -> list[Position]:
        return sorted(Position.instances, key = lambda x: self.suit[x] if hasattr(self, 'suit') else self.getPositionScore(x), reverse=True)

    @property
    def ucDescription(self) -> str:
        descriptions = {
            ### Age based
            'young': 3 - (self.age - 16) ** 2 / 3,
            'promising': 3 - (self.age - 18) ** 2 / 2,
            'veteran': 1.3 ** (self.age - 33),
            ### Attribute based
            'pacey': self.getDifferenceFromMax(self.pac) / 5,
            'lethal': self.getDifferenceFromMax(self.sho) / 3,
            'creative': self.getDifferenceFromMax(self.pas) / 3,
            'skillful': self.getDifferenceFromMax(self.dri) / 3,
            'tenacious': self.getDifferenceFromMax(self.dfn) / 3,
            'robust': self.getDifferenceFromMax(self.phy) / 5,
            ### Profile based
            'versatile': len(self.secondaryPositions) ** 1.5 / 3,
            self.nation.ucNationality: 1
        }
        return list(descriptions.keys())[list(descriptions.values()).index(sorted(descriptions.values(), reverse = True)[0])] + ' ' + self.position.ucName

    @property
    def description(self) -> str:
        # input(descriptions)
        return self.position.colorText(self.ucDescription)
    
    @property
    def ipac(self) -> int:
        return round(self.pac)
    
    @property
    def isho(self) -> int:
        return round(self.sho)
    
    @property
    def ipas(self) -> int:
        return round(self.pas)
    
    @property
    def idri(self) -> int:
        return round(self.dri)
    
    @property
    def idfn(self) -> int:
        return round(self.dfn)
    
    @property
    def iphy(self) -> int:
        return round(self.phy)

    @property
    def attributes(self) -> list[int | float]:
        return [self.pac, self.sho, self.pas, self.dri, self.dfn, self.phy]
    
    @property
    def iattributes(self) -> list[int]:
        return [self.ipac, self.isho, self.ipas, self.idri, self.idfn, self.iphy]

    @attributes.setter
    def attributes(self, frame):
        self.pac, self.sho, self.pas, self.dri, self.dfn, self.phy = frame
    
    @property
    def rating(self) -> int | float:
        return self.getPositionScore(self.position)
    
    @property
    def irating(self) -> int:
        return round(self.getPositionScore(self.position))
    
    @property
    def ipotential(self) -> int:
        return round(self.potential)

    def genSuit(self, position: Position) -> dict:
        suit = {p: -max(0, sum([3 * random() - .5 for _ in range(max(1, int(self.getPositionScore(position) - self.getPositionScore(p) + 1.5 * random())))])) for p in Position.instances}
        mx = max(suit.values())
        for p in Position.instances:
            suit[p] -= mx
        return suit

    def getPositionScore(self, position: Position) -> float:
        '''Returns the overall of the player in the given position.'''
        score = self.pac * position.weightings[0] + self.sho * position.weightings[1] + self.pas * position.weightings[2] + self.dri * position.weightings[3] + self.dfn * position.weightings[4] + self.phy * position.weightings[5] + (99 if self.foot == 'left' or self.hasTrait('Weak Foot') else 1) * position.weightings[6] + (99 if self.foot == 'right' or self.hasTrait('Weak Foot') else 1) * position.weightings[7] + position.modifier
        try:
            return min(99, score) + self.suit[position]
        except AttributeError:
            return min(99, score)

    def hasTrait(self, targetTrait: Trait) -> bool:
        '''
        Returns True if `targetTrait` is one of the traits of the player, False otherwise.
        `targetTrait` must be a Trait object or be in ._searchOptions.
        '''
        return targetTrait in self.traits or Trait.find(targetTrait) in self.traits

    def viewProfile(self, end=True) -> None:
        '''Shows the profile of the player.'''
        # input('\n' + '\n'.join([str(i) + '. ' + pos.shortName + ' ' + str(self.getPositionScore(pos)) for i, pos in enumerate(self.positions, 1)]) + '\n')
        clear()
        print(f'''<bold>{alignText(self.fullName + f"{SINGLE_QUOTE}s profile:", terminalWidth(), 'center', LINE)}</bold>
<bold>Age:</bold>                <uyellow>{self.age}</uyellow>.\
{f'\n<uorange>Rating:             {round(self.rating, 2)}</uorange>.' if DEV_MODE else ''}\
{f'\n<uorange>Potential:          {round(self.potential, 2)}</uorange>.' if DEV_MODE else ''}
<bold>Preferred position:</bold> {self.position.name}.
<bold>Other positions:</bold>    {self.fullSecondaryPositions}.
<bold>Fan description:</bold>    {self.description}.
<bold>Nationality:</bold>        {self.nation.nationality}.
<bold>Club:</bold>               {self.club.name}.
<bold>League:</bold>             {self.club.league.name}.
''')
        Table(list(zip(Attributes + [PreferredFoot], self.iattributes + [self.foot])), title = f'<uyellow>{type(self).__name__} attributes:</uyellow>').print()
        print(f'\n<underline>The traits of the {type(self).__name__.lower()}:</underline>')
        for trait in self.traits:
            print(f'{trait.name}{" " * (max([len(trait.ucName) for trait in self.traits]) - len(trait.ucName))} {trait.colorText(LINE)} {trait.description}')
        if end:
            input('\n<uyellow>Press Enter to continue.</uyellow> ')
        clear()
    
    def colorText(self, text: str) -> str:
        '''Colors `text` in the color of the nation of the player and underlines it.'''
        return self.nation.colorText(text)

    def getDifferenceFromMax(self, attribute: int) -> int:
        '''Returns the difference between `attribute` and the biggest attribute that is not `attribute` itself.'''
        attributes = self.attributes
        attributes.remove(attribute)
        return attribute - max(attributes)

class Hero (Player):
    '''
    The class for a hero.\n
    Shares all attributes with the Player class.
    '''
    def __init__(self, data: dict):
        '''
        Creates a Hero object from the given `data`.\n
        `data` must be a dictionary containing all attributes of the hero except his uncolored attributes,
        age and potential. You can include these attributes in the dictionary, but they will be overwritten.
        '''
        data['nation'] = Nation.find(data['nation'], True)
        data['traits'] = [trait if isinstance(trait, Trait) else Trait.instances[trait - 1] for trait in data['traits']]
        data['club'] = Club.find(data['club'], True) if data['club'] else None
        self.__dict__ = data
        super().__init__(None, None, None)
        self.suit = self.genSuit(self.position)
        self.ucFullName, self.fullName = [self.fullName, self.colorText(self.fullName)]
        self.ucShirtName, self.shirtName = [self.shirtName, self.colorText(self.shirtName)]

    @classmethod
    def fromInputs(cls):
        '''
        Constructs a Hero object from the inputs of the user and returns it.
        '''
        def getAttribute(attribute: str, pointsSpent: int = 0, attributesLeft: int = 0) -> int:
            '''
            Makes the user select a value for the given attribute.\n
            They will be prompted with the given message.\n
            Returns the selected value.
            '''
            upperBound = min(MAX_POINTS, ALL_POINTS - pointsSpent - attributesLeft * MIN_POINTS)
            lowerBound = max(MIN_POINTS, ALL_POINTS - pointsSpent - attributesLeft * MAX_POINTS)
            while True:
                value = input(f'You have <uyellow>{ALL_POINTS - pointsSpent}</uyellow> points. How many will you allocate to {attribute}?{" (enter a number, then press Enter)" if not setupFiles and attributesLeft == 5 else ""} ')
                if value == '/quit':
                    raise QuitError
                try:
                    value = int(value)
                    if lowerBound <= value <= upperBound:
                        return value
                    raise ValueError
                except ValueError:
                    print(f'<ured>You need to input a number between {lowerBound} and {upperBound}.\nAll points have to be used.</ured>\n')

        def getTrait(message: str):
            '''
            Makes the user select a trait.\n
            They will be prompted with the given message.\n
            Returns the selected trait.
            '''
            while True:
                traitNum = input(message)
                if traitNum == '/quit':
                    raise QuitError
                try:
                    traitNum = int(traitNum)
                    result = Trait.instances[traitNum - 1]
                    if 1 <= traitNum:
                        if result in data['traits']:
                            print(f'<ured>You already selected {result.name}.</ured>')
                            continue
                        data['traits'].append(result)
                        break
                    raise ValueError
                except ValueError:
                    print(f'<ured>You need to input a number between 1 and {len(Trait.instances)} which corresponds to a trait.</ured>\n')

        data = {}

        clear()
        menu('If you want to quit to the main menu, type /quit instead of your input.', [MenuOption('Got it!', color = 'dgreen')])
        clear()
        print('<bold>Step 1. Who is your hero?</bold>\n\n')
        while True:
            data['fullName'] = input(f'<uyellow>Enter his full name{" (press Enter to confirm)" if not setupFiles else ""}:</uyellow> ')
            if data['fullName'] == '/quit':
                raise QuitError
            if len(data['fullName'].replace(' ', '')) < 2:
                print('<ured>The hero\'s full name must be at least 2 characters long.</ured>\n\n')
                continue
            try:
                data['fullName'].encode()
            except UnicodeEncodeError:
                print('<ured>This full name contains invalid characters.\nPlease pick a different one.</ured>')
                continue
            data['shirtName'] = data['fullName'].split()
            data['shirtName'] = data['shirtName'][-1] if len(data['shirtName']) > 1 else data['fullName']
            snUserSuggestion = input(f'<uyellow>Enter his shirt name{" (you can edit this text!)" if not setupFiles else ""}:</uyellow> ', default=data['shirtName'])
            if snUserSuggestion == '/quit':
                raise QuitError
            if len(snUserSuggestion.replace(' ', '')) < 2:
                print('<ured>The hero\'s shirt name must be at least 2 characters long.</ured>', '\n\n')
                continue
            data['shirtName'] = snUserSuggestion
            try:
                data['shirtName'].encode()
            except UnicodeEncodeError:
                print('<ured>This shirt name contains invalid characters.\nPlease pick a different one.</ured>')
                continue
            while True:
                nationSuggestion = input(f'<uyellow>Enter his nation\'s name or its 3 letter code{" (type the beginning, then use arrow keys)" if not setupFiles else ""}:</uyellow> ', completer = WordCompleter(nationNames, ignore_case = True)).lower()
                if nationSuggestion == '/quit':
                    raise QuitError
                data['nation'] = Nation.find(nationSuggestion)
                if data['nation'] != -1:
                    break
                print('\n<ured>Sorry, we couldn\'t find your nation. Please make sure that they are a member of FIFA.</ured>\n\n')
            print(f'\n\n<uyellow>Let\'s check.</uyellow>\nThe hero\'s full name is {data['fullName']}.\nHis shirt name is {data['shirtName']}.\nHis nation is {data['nation'].name}.')
            if yesNoMenu('Is everything here correct?'):
                break
            print('\n\n')
        
        clear()
        print('<bold>Step 2. Time to determine his strengths and weaknesses!</bold>\n\n')
        while True:
            print(f'You have <uyellow>{ALL_POINTS}</uyellow> points to allocate.\nThey must be distributed among 6 attributes: {pace}, {shooting}, {passing}, {dribbling}, {defending} and {physicality}.\nEach attribute must have from <uyellow>{MIN_POINTS}</uyellow> to <uyellow>{MAX_POINTS}</uyellow> points assigned to it.\n')
            data['pac'] = getAttribute(pace, attributesLeft = 5)
            data['sho'] = getAttribute(shooting, data['pac'], 4)
            data['pas'] = getAttribute(passing, data['pac'] + data['sho'], 3)
            data['dri'] = getAttribute(dribbling, data['pac'] + data['sho'] + data['pas'], 2)
            data['dfn'] = getAttribute(defending, data['pac'] + data['sho'] + data['pas'] + data['dri'], 1)
            data['phy'] = getAttribute(physicality, data['pac'] + data['sho'] + data['pas'] + data['dri'] + data['dfn'])
            data['foot'] = menu('Choose the preferred foot of your hero!', [MenuOption('left', color = 'uyellow', value = 'left'), MenuOption('right', color = 'uyellow', value = 'right')])
            print(f'\n\n<uyellow>Let\'s check.</uyellow>')
            Table(list(zip(Attributes + [PreferredFoot], [data['pac'], data['sho'], data['pas'], data['dri'], data['dfn'], data['phy'], data['foot']])), title = f'<uyellow>The hero\'s attributes are:</uyellow>').print()
            if yesNoMenu('Is everything here correct?'):
                break
            print('\n\n')

        clear()
        while True:
            print(f'<bold>Step 3. And, finally, let\'s look at his traits!</bold>\n\n<uyellow>Pick 3 traits for your hero.</uyellow>\n')
            Trait.printInstances()
            print(f'\nInput the trait number, for example, <uyellow>1</uyellow> for {Trait.instances[0].name}, <uyellow>2</uyellow> for {Trait.instances[1].name} and so on.\n')
            data['traits'] = []
            for i, message in enumerate(['What trait do you pick?', 'Pick another one!', 'And the last one:'], 1):
                getTrait(f'<uyellow>({i}/3) {message}</uyellow> ')
            data['traits'] = sorted(data['traits'], key = lambda x: x.ucNum)

            print(f'\n\n<uyellow>Let\'s check.</uyellow>\nThe hero\'s traits are: {', '.join(map(lambda x: x.name, data['traits']))}.')
            if yesNoMenu('Is everything here correct?'):
                break
            print('\n\n')
        
        data['club'] = academyMenu(data)
        
        try:
            hero = Hero(data)
            hero.club.players.append(hero)
            return hero
        except Exception as e:
            print(f'<ured>An error occured while trying to create your hero:</ured>\n')
            origPrint(e)
            if DEV_MODE:
                origPrint(format_exc())
            input('<ured>Press Enter to continue:</ured> ')
            raise QuitError

    def toDict(self) -> dict:
        '''Returns itself as a dictionary that is ready to be used for saving.'''
        data = {a: b for a, b in self.__dict__.items()}
        data['nation'] = data['nation'].ucName
        data['traits'] = [trait.ucNum for trait in data['traits']]
        data['club'] = data['club'].ucName if data['club'] else None
        data['fullName'] = data['ucFullName']
        data['shirtName'] = data['ucShirtName']
        data.pop('potential')
        data.pop('ucFullName')
        data.pop('ucShirtName')
        data.pop('suit')
        return data
    
    def colorText(self, text: str) -> str:
        '''Colors `text` in the color of the nation of the hero and underlines it.'''
        return '<underline>' + self.nation.colorText(text) + '</underline>'

    @property
    def ipotential(self) -> str:
        return '??'

class Club(Find):
    '''
    The class for a club.\n
    Attributes:
    - `.rating`: The in-game overall rating of the club.
    - `.colors`: A list of the main colors of the club.
    - `.names`: A list of all generic names of the club.
    - `.name`: The main generic name of the club.
    - `.fullName`: The official name of the club.
    - `.nickname`: The nickname of the club.
    - `.shortName`: A unique 3 letter code that can be used to identify the club.
    - `.uc{Attribute}`: Same as `.{attribute}` but contains uncolored text instead of colored.
    - `.i{attribute}`: Same as `.{attribute}` but is of type `int` instead of `float`.
    - `.players`: A list of all players currently at the club.
    - `.instances`: A list of all Club instances.
    '''
    instances = []
    def __init__(self, ovr: float, fullName: str, names: list[str], nickname: str, shortName: str, colors: list[str]):
        '''
        Arguments:
        - `ovr`: The in-game overall rating of the club.
        - `fullName`: The official name of the club.
        - `names`: A list of all generic names of the club.
        - `nickname`: The nickname of the club.
        - `shortName`: A unique 3 letter code that can be used to identify the club.
        - `colors`: A list of the main colors of the club.
        '''
        self.origRating = ovr
        self.colors = colors
        self.ucName = names[0]
        self.ucNames = names
        self.names = [self.colorText(name) for name in self.ucNames]
        self.name = self.names[0]
        self.fullName = self.colorText(fullName)
        self.ucFullName = fullName
        self.nickname = self.colorText(nickname)
        self.ucNickname = nickname
        self.shortName = self.colorText(shortName)
        self.ucShortName = shortName
        if self.ucName.lower() == 'free agents':
            return
        self._searchOptions = [self.ucFullName.lower(), self.ucNickname.lower(), self.ucShortName.lower()] + [clubName.lower() for clubName in self.ucNames]
        self.__class__.instances.append(self)
    
    @property
    def rating(self) -> float:
        return sum(map(lambda x: x.rating, sorted(self.players, key=lambda x: x.rating, reverse=True)[:11])) / 11
    
    @property
    def irating(self) -> int:
        return round(self.rating)
    
    def viewProfile(self, caption='<uyellow>Press Enter to go back to the start menu: </uyellow>', end=True) -> None:
        '''Shows the profile of the club.'''
        clear()
        if self is freeAgents:
            return
        print(f'''{alignText(f"<bold>{self.fullName}'s profile:</bold>", terminalWidth(), 'center', LINE)}
<bold>Recognised name:</bold> {self.name}.
<bold>Nickname:</bold>        {self.nickname}.
<bold>Colors:</bold>          {self.colorText('   ', True)}{self.color2Text('   ', True)}.
<bold>League:</bold>          {self.league.name}.\
{f'\n<uorange>Rating:          {round(self.rating, 2)}</uorange>.' if DEV_MODE else ''}''')
        t = Table([[i, p.position.shortName, p.nation.name, p.fullName, *p.iattributes, p.age, p.irating, p.ipotential] for i, p in enumerate(sorted(self.players, key=lambda x: x.rating, reverse=True), 1)], ['№', 'Pos', 'Nation', 'Full name', Header('Pac', columnColor='uyellow'), Header('Sho', columnColor='ured'), Header('Pas', columnColor='ucyan'), Header('Dri', columnColor='umagenta'), Header('Dfn', columnColor='ugreen'), Header('Phy', columnColor='uwhite'), Header('Age', columnColor='lbrown'), Header('OVR', columnColor='uwhite'), Header('POT', columnColor='dgreen')], f"<bold>{self.fullName}'s senior squad:</bold>", caption if end else None)
        if end:
            t.input()
        else:
            t.print()
        clear()

    def colorText(self, text, bg = False) -> str:
        '''
        Colors the `text` with the first color of the club.\n
        Colors the background instead of the text if `bg` is True.
        '''
        return f'<{"bg" if bg else ""}{self.colors[0]}>{text}</{"bg" if bg else ""}{self.colors[0]}>'
    
    def color2Text(self, text, bg = False) -> str:
        '''
        Colors the `text` with the second color of the club.
        Colors the background instead of the text if `bg` is True.
        '''
        return f'<{"bg" if bg else ""}{self.colors[1]}>{text}</{"bg" if bg else ""}{self.colors[1]}>'
    
    def colorFullText(self, text) -> str:
        '''Colors the `text` with the first color of the club and colors the background with the second color of the club.'''
        return self.color2Text(self.colorText(text), True)
    
class League(Find):
    '''
    The class for a league.
    Attributes:
    - `.nation`: The nation the league corresponds to.
    - `.level`: The level of the league in the league pyramid of the nation of the league. Example: 2 for the English Champtionship.
    - `.shortName`: A unique 4 symbol code that can be used to identify the league.
    - `.name`: The name of the league.
    - `.clubs`: A list of all clubs that participate in the league.
    - `.sortedClubs`: Same as `.clubs` but sorted by their rating in descending order.
    - `.capacity`: How many clubs participate in the league.
    - `.rating`: Shortcut for `.getRating()`.
    '''
    instances = []
    def __init__(self, name: str, nation, clubs: list):
        '''
        Arguments:
        - `name`: The name of the league.
        - `nation`: The nation the league corresponds to.
        - `clubs`: A list of all clubs that participate in the league.
        '''
        self.__class__.instances.append(self)
        self.nation = nation
        self.nation.leagues.append(self)
        self.level = len(self.nation.leagues)
        self.shortName = self.nation.shortName + self.nation.colorText(self.level)
        self.ucShortName = self.nation.ucShortName + str(self.level)
        self.ucName = name
        self.name = self.colorText(self.ucName)
        self.clubs = clubs
        for club in clubs:
            club.league = self
            club.nation = self.nation
            self.nation.clubs.append(club)
        self.capacity = len(self.clubs)
        self._searchOptions = [self.ucName.lower(), self.ucShortName] + [f'{nationName.lower()} {self.level}' for nationName in self.nation.ucNames]
    
    def colorText(self, text: str) -> str:
        '''Colors the `text` with the main color of the nation.'''
        return self.nation.colorText(text)
    
    @property
    def rating(self) -> float:
        return self.getRating()
    
    def getRating(self, mode = 'average') -> float:
        '''
        Returns the rating of the league calculated using the given `mode`.\n
        `mode` can be:
        - 'average': Calculates the average of all ratings of the clubs in the league.
        - 'top': Calculates the average of the ratings of the clubs in the top half of the league (sorted by their rating).
        - 'median': Calculates the median rating of all of the clubs in the league.
        '''
        match mode:
            case 'average':
                return round(sum([club.rating for club in self.clubs]) / self.capacity, 2)
            case 'top':
                return round(sum([club.rating for club in self.clubs[:self.capacity // 2]]) / (self.capacity // 2), 2)
            case 'median':
                return round((self.sortedClubs[self.capacity // 2].rating + self.sortedClubs[(self.capacity - 1) // 2].rating) / 2, 2)
    
    @property
    def sortedClubs(self) -> list[Club]:
        return sorted(self.clubs, key = lambda x: x.rating, reverse=True)
    
### Preset variables and preparation code

colorText = lambda text, color: ColorText().colorText(text, color)

pace, Pace = colorDoubleText('pace', 'uyellow')
shooting, Shooting = colorDoubleText('shooting', 'ured')
passing, Passing = colorDoubleText('passing', 'ucyan')
dribbling, Dribbling = colorDoubleText('dribbling', 'umagenta')
defending, Defending = colorDoubleText('defending', 'ugreen')
physicality, Physicality = colorDoubleText('physicality', 'uwhite')
preferredFoot, PreferredFoot = colorDoubleText('preferred foot', 'uorange')

attributes = [pace, shooting, passing, dribbling, defending, physicality]
Attributes = [Pace, Shooting, Passing, Dribbling, Defending, Physicality]

just_fix_windows_console()
chdir(dirname(abspath(__file__)))

### Game loop

while True:
    settings, mainStyleDict = parseDatabase(list(files.values()) + list(dirs.values()), [Settings, createStyle, createNations, createPositions, createTraits, createLeagues], [files['settings'], files['style'], ], [2, 2, 10, 2, 2, 5])
    mainStyle = Style.from_dict(mainStyleDict)
    nationNames = [str(nation.fifaRanking) for nation in Nation.instances]
    for nation in Nation.instances:
        nationNames += nation.ucNames
    nationNames += [nation.ucShortName for nation in Nation.instances]

    viewPlayerRankings('rating')
    viewPlayerRankings('potential')
    for club in sorted(Club.instances, key=lambda x: x.rating + random() * 10, reverse=True):
        club.viewProfile()
    cnt = {p.name: 0 for p in Position.instances}
    for pl in Player.instances:
        cnt[pl.position.name] += 1
    for k, v in zip(cnt.keys(), cnt.values()):
        cnt[k] = [v, f'{round(v / len(Player.instances) * 100, 2)}%', v / len(Player.instances) * 11]
    input(cnt)

    while True:
        setupFiles = getFiles(dirs['setups'])
        saveFiles = getFiles(dirs['saves'])
        try:
            match startingMenu():
                case 'quit':
                    if yesNoMenu('Are you sure you want to quit?', default = 'No'):
                        clear()
                        print('<uorange>Bye then... Hope to see you soon!</uorange>')
                        sleep(2)
                        sysExit()
                    continue
                case 'load-game':
                    notReadyWarning()
                    continue
                case 'load-setup':
                    hero = loadSetup()
                    if not hero:
                        continue
                case 'new-hero':
                    if setupFiles and not yesNoMenu('Are you sure you want to create a new hero?', default = 'No'):
                        continue
                    hero = Hero.fromInputs()
                    saveSetup(hero)
                case 'settings':
                    settings.edit()
                    continue
                case 'rankings':
                    entered = True
                    while entered:
                        result = rankingsMenu()
                        match result:
                            case 'nations':
                                viewNationRankings()
                            case 'leagues':
                                while True:
                                    result = leagueRankingsMenu()
                                    if result == 'quit':
                                        entered = False
                                        break
                                    viewLeagueRankings(result)
                            case 'clubs':
                                viewClubRankings()
                            case 'players':
                                while True:
                                    result = playerRankingsMenu()
                                    if result == 'quit':
                                        entered = False
                                        break
                                    viewPlayerRankings(result)
                            case 'quit':
                                break
                    continue
        except QuitError:
            continue
        hero.viewProfile()
        hero.club.viewProfile()

        input('<rorange>There will be a career here soon... For now, though, press Enter:</rorange> ')
        break
