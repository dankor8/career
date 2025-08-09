### TODO
### finish documentation and type hints
### test that everything works normally
### test table style missing keys

### Special imports

from rich.progress import Progress
from time import sleep

### File variables

dirs = {
    'db': 'database/',
    'saves': 'saves/',
    'setups': 'setups/',
    'custom': 'customisation/'
}
files = {
    'nations': dirs['db'] + 'nations.db',
    'leagues': dirs['db'] + 'leagues.db',
    'positions': dirs['db'] + 'positions.db',
    'traits': dirs['db'] + 'traits.db',
    'settings': dirs['custom'] + 'settings.db',
    'style': dirs['custom'] + 'style.db'
}
comments = {file: '' for file in files.keys()}
dbFiles = {a: b for a, b in files.items() if dirs['db'] in b}
FILE_EXTENSION = '.plc'
DATABASE_FILE_EXTENSION = '.db'

### Constants (and a little bit more)

origPrint = print
origInput = input
DOUBLE_BACKSLASH_N = '\\n'
BACKSLASH_N = '\n'
SLASH = '/'
SINGLE_QUOTE = "'"
ALL_POINTS = 300
MAX_POINTS = 80
MIN_POINTS = 20

DEV_MODE = False

### Text functions

def input(*message, sep: str = ' ', default: str = "", completer = None) -> str:
    '''
    Like traditional input() but supports colored text in prompt_toolkit's HTML format.\n
    Can print strings, integers, tuples, etc., but not objects.\n
    Be careful when printing anything that contains < and > as these may cause an error in prompt_toolkit.\n
    Returns the string that the user inputs.
    '''
    message = sep.join([str(part) for part in message])
    return prompt(HTML(message), style = mainStyle, default = default, completer = completer)

def print(*values, sep: str = ' ', end: str = '\n') -> None:
    '''
    Like traditional input() but supports colored text in prompt_toolkit's HTML format.\n
    Can print strings, integers, tuples, etc., but not objects.\n
    Be careful when printing anything that contains < and > as these may cause an error in prompt_toolkit.
    '''
    values = sep.join([str(part) for part in values])
    print_formatted_text(HTML(values), end = end, style = mainStyle)

def richFormat(text: str) -> str:
    '''
    Formats prompt_toolkit's HTML formatted text to match Rich formatting.
    '''
    toReplace = {f'<{code}>': f'[{color.replace("bg:", "on ")}]' for code, color in mainStyleDict.items()}
    toReplace.update({f'</{code}>': '[/]' for code in mainStyleDict.keys()})
    for old, new in toReplace.items():
        text = text.replace(old, new)
    return text

def colorDoubleText(text: str, color: str) -> list[str]:
    '''
    Like colorText() but returns a list of 2 elements: colored usual text and colored capitalised text.
    '''
    return [colorText(text, color), colorText(text.capitalize(), color)]

def uncolorText(text: str) -> str:
    '''
    Deletes all HTML color codes from the given string.
    '''
    for code in mainStyleDict.keys():
        text = text.replace(f'<{code}>', '').replace(f'</{code}>', '')
    return text

def alignText(text: str, ucText: str, align: str, width: int, fill = ' ') -> str:
    '''
    Returns aligned text. Works with colored text, but needs its uncolored version (ucText).\n
    Align must be 'left', 'center' or 'right'.
    '''
    newWidth = width + len(text) - len(ucText)
    match align.lower():
        case 'left':
            text = text.ljust(newWidth, fill)
        case 'center':
            text = text.center(newWidth, fill)
        case 'right':
            text = text.rjust(newWidth, fill)
        case _:
            raise Exception(f'alignText(): align must be "left", "center" or "right", not {align}.')
    return text

def colorSettingValue(value: str, mode: str = 'html') -> str | list | None:
    '''
    Returns colored setting value (yes in green for yes, no in red for no, etc).\n
    Mode must be 'html' or 'color'.\n
    If mode is 'html' (default), returns {value} that's colored using prompt_toolkit's HTML format.
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
            raise Exception(f'colorSettingValue(): mode must be "html" or "color", not {mode}.')
    return None

def clear() -> None:
    '''
    Clears the terminal.
    '''
    if osName == 'nt':
        system('cls')
    else:
        system('clear')

### Encoding/decoding functions

def saveData(filePath: str, data, allowExceptions: bool = False) -> bool:
    '''
    Saves data to {filePath} in YAML.\n
    Returns True if saving was successful or False if there was an error.\n
    Raises an Exception instead of returning False if {allowException} is True.
    '''
    try:
        with open(filePath, 'wb') as f:
            f.write(dataToYAML(data))
        return True
    except Exception as e:
        if allowExceptions:
            raise Exception(f'Failed to save data to {filePath}:\n{e}\n')
        return False
    
def loadData(filePath: str, allowExceptions: bool = True, modifyComments: bool = False) -> bool:
    '''
    Loads data in YAML from {filePath}.\n
    Returns the data if loading was successful or False if there was an error.\n
    Raises an Exception instead of returning False if {allowException} is True.\n
    Saves the first comment (must start on character 1 of the file) to the comments dictionary if {modifyComments} is True.
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
            raise Exception(f'Failed to load data from {filePath}:\n{e}\n')
        return False

def dataToYAML(data) -> bytes:
    '''
    Shortcut for yaml.safe_dump().
    '''
    return safe_dump(data, encoding = 'utf-8', allow_unicode = True, sort_keys = False)

def yamlToHash(data: bytes) -> str:
    '''
    Returns a hash string of the data provided.
    '''
    return sha3_224(data + b'well... you weren\'t supposed to find this.').hexdigest()

def dataToHash(data) -> str:
    '''
    Shortcut for yamlToHash(dataToYAML(data)).
    '''
    return yamlToHash(dataToYAML(data))

def isValidChangeDate(file: str, changeDate) -> bool:
    '''
    Checks if the {changeDate} written in {file} matches it's system-coded change date.
    '''
    return getmtime(file) - float(changeDate) < .1

def getTime() -> float:
    '''
    Shortcut for datetime.datetime.now.timestamp().
    '''
    return datetime.now().timestamp()

### Database functions

def getFiles(directory: str, extensions: list[str] = [FILE_EXTENSION, DATABASE_FILE_EXTENSION]) -> list[str]:
    '''
    Returns all flies from {directory} that share an extension with {extensions}.
    '''
    return [file for file in listdir(directory) if '.' + file.split('.')[-1] in extensions or not extensions]

def parseDatabase(pathsToCheck: list[str], funcsToCheck: list[function], outputsToReturn: list[str] = []) -> list:
    '''
    Checks that all paths in {pathsToCheck} exist and calls each function in {funcsToCheck}.\n
    Returns the output of a function if the file corresponding to it (taken from the files dictionary) is in {outputsToReturn}.
    '''
    def checkPaths(progressBars: bool = True):
        '''
        Basically does the job of the main function.\n
        Shows brogress bars if progressBars is True.
        '''
        toReturn = []
        for pathToCheck in pathsToCheck:
            if not exists(pathToCheck):
                errorList.append(f'{"Directory" if pathToCheck[-1] == SLASH else "File"} "{pathToCheck}" does not exist.')
            if progressBars:
                bar.update(task, advance = 1)
        for file, func in zip(files.values(), funcsToCheck):
            if exists(file):
                # func()
                try:
                    output = func()
                    if file in outputsToReturn:
                        toReturn.append(output)
                except Exception as e:
                    try:
                        if DEV_MODE or settings.excTraceback:
                            exc = '\n' + format_exc()
                        else:
                            raise Exception
                    except:
                        exc = e
                    errorList.append(f'{"DatabaseError" if type(e).__name__ == "Exception" else type(e).__name__} in {file}: {exc}')
            if progressBars:
                bar.update(task, advance = 2)
        return toReturn
    errorList = []
    if progressBarSetting():
        with Progress() as bar:
            task = bar.add_task('[green]Checking database data...', total = len(pathsToCheck) + len(funcsToCheck) * 2)
            toReturn = checkPaths()
    else:
        toReturn = checkPaths(False)
    sleep(1)
    if errorList:
        clear()
        origPrint(f'The database is incomplete.\nIf you moved or edited any files from the game directory, please revert the changes or reinstall the game in case you cannot.\n\nThe following error{"s" if len(errorList) > 1 else ""} occured:')
        for i, error in enumerate(errorList, 1):
            origPrint(f'{i}. {error}')
        raiseFatalError()
    return toReturn

def createLeagues() -> None:
    '''
    Creates all League and Club objects from the {files['leagues']} file.
    '''
    leaguesData = loadData(files['leagues'], modifyComments = True)
    for leagueData in leaguesData:
        leagueData['nation'] = Nation.find(leagueData['nation'], True)
        leagueClubs = []
        for clubData in leagueData['clubs']:
            if str(clubData['rating'])[-1] == '!':
                clubData['rating'] = OPTAtoRating(clubData['rating'][:-1])
            if not 27 <= clubData['rating'] <= 87:
                raise Exception(f'Rating of clubs must be between 27 and 87 (0 and 100 in OPTA power rankings), while {clubData["names"][0]}\'s is {clubData["rating"]}.')
            for name in clubData['names'] + [clubData['nickname']]:
                if not 1 <= len(name) <= 25:
                    raise Exception(f'Length of generic names and nicknames must be between 1 and 25, while {name}\'s is {len(name)}.')
            if len(clubData['shortName']) != 3:
                raise Exception(f'Length of club short names must be 3, while {clubData["shortName"]}\'s is {len(clubData["shortName"])}.')
            leagueClubs.append(Club(clubData['rating'], clubData['fullName'], clubData['names'], clubData['nickname'], clubData['shortName'], clubData['colors']))
        League(leagueData['name'], leagueData['nation'], leagueClubs)
    clubShortNames = [club.ucShortName for club in Club.instances]

    seenShortNames = set()
    duplicateShortNames = set()
    for x in clubShortNames:
        if x in seenShortNames:
            duplicateShortNames.add(x)
        else:
            seenShortNames.add(x)

    if duplicateShortNames:
        raise Exception(f'There {"are" if len(duplicateShortNames) > 1 else "is a"} duplicate club short name{"s" if len(duplicateShortNames) > 1 else ""}: {", ".join(duplicateShortNames)}.')
    
def createPositions() -> None:
    '''
    Creates all Position objects from the {files['positions']} file.
    '''
    positions = loadData(files['positions'])
    for position in positions:
        Position(position['shortName'], position['name'], position['color'], list(position['weightings'].values()), position['modifier'])

def createNations() -> None:
    '''
    Creates all Nation objects from the {files['nations']} file.
    '''
    nations = loadData(files['nations'])
    for i, nation in enumerate(nations, 1):
        Nation(nation['names'], nation['shortName'], nation['nationality'], nation['color'], i)

def createTraits() -> None:
    '''
    Creates all Trait objects from the {files['traits']} file.
    '''
    traits = loadData(files['traits'])
    for trait in traits:
        Trait(trait['name'], trait['description'], trait['color'], trait['category'])

def createStyle() -> dict[str: str]:
    '''
    Creates all Style objects from the {files['style']} file.
    '''
    data = loadData(files['style'])
    styleDict = {}
    for code, color in data.items():
        if code[-1] == '!':
            styleDict[code[:-1]] = color
            continue
        styleDict[code] = color
        styleDict[f'bg{code}'] = f'bg:{color}'
    return styleDict

def saveSetup(hero) -> None:
    '''
    Saves {hero} into a file.
    '''
    clear()
    while True:
        filePath = input('<ugreen>Let\'s save your starting setup!</ugreen>\n<uyellow>Choose the name of the file it will be saved in:</uyellow> ', default = hero.ucFullName) + FILE_EXTENSION
        print()
        if not filePath:
            print('<ured>The name of your setup cannot be empty.</ured>')
            sleep(1)
        if filePath in getFiles(dirs['setups']):
            if not yesNoMenu(f'There is already a setup called {removeExtension(filePath)}. Do you want to replace it with this one?'):
                clear()
                continue
        try:
            heroPrep = {
                'hero': hero.toDict(),
                'time': getTime()
            }
            heroPrep['hash'] = dataToHash(heroPrep)
            saveData(dirs['setups'] + filePath, heroPrep)
        except Exception as e:
            input(f'<ured>An error accured while trying to save your setup:\n{e}\nPlease try a different file name.\nPress Enter to continue.</red>\n\n ')
            continue
        print('\n<dgreen>Your setup was successfully saved!</dgreen>')
        sleep(1)
        break

def loadSetup():
    '''
    Loads a hero setup, creates a Hero object and returns it.
    '''
    hero = 0
    while True:
        setupFiles = sorted(getFiles(dirs['setups']), key = lambda x: -getmtime(dirs['setups'] + x))
        setupNumber = menu('Choose a setup to load:', [MenuOption(removeExtension(option), value = i) for i, option in enumerate(setupFiles, 1)] + [MenuOption('Quit', 'dred', 'Quit to the main menu.', -1)])
        if setupNumber == -1:
            break
        filePath = dirs['setups'] + setupFiles[setupNumber - 1]
        try:
            decodedHeroPrep = loadData(filePath)
            decodedHash = decodedHeroPrep.pop('hash')
            try:
                hashFlag = decodedHash != dataToHash(decodedHeroPrep)
                timeFlag = not isValidChangeDate(filePath, decodedHeroPrep['time'])
                if hashFlag and timeFlag:
                    raise Exception('B001')
                if hashFlag:
                    raise Exception('H001')
                if timeFlag:
                    raise Exception('T001')
            except Exception as e:
                print(f'<ured>This setup was modified. Flag reason: {e}.</ured>\n\n')
                continue
            heroData = decodedHeroPrep['hero']
            hero = Hero('fromDict', heroData)
            print('<dgreen>Your setup was successfully loaded!</dgreen>')
            sleep(1)
            break
        except Exception as e:
            print(f'<ured>This setup is corrupted.\n{e}</ured>\n\n')
    return hero

### Shortcut functions

def menu(title: str, options: list, help: str = ' ', default = None):
    '''
    Asks a questionary and returns the chosen answer.\n
    Options must be instances of MenuOption class.
    '''
    menuOptions = [Choice(option if isinstance(option, str) else [('class:' + option.color, option.text)], value = option.returnValue, description = option.description.replace('\n', '\n               ') if option.description else option.description) for option in options]
    return questionary(title, menuOptions, instruction = help, qmark = '', style = mainStyle, default = default).ask()

def notReadyWarning():
    print('<dyellow>This feature is temporarily unavailable and will be coming in a future update.\nStay tuned!\n</dyellow>')
    input('<yellow>Press Enter to continue.</yellow> ')

def raiseFatalError() -> None:
    '''
    Exits the application after an error.
    '''
    origInput('\nPress Enter to terminate the application. ')
    sysExit()

### Menus

def yesNoMenu(text, default = 'Yes') -> bool:
    '''
    Creates a simple Yes or No menu with a title of {text} with the pointer set to {default}.\n
    Returns True if Yes was chosen and False otherwise.
    '''
    options = [MenuOption('Yes', color = 'ugreen'), MenuOption('No', color = 'ured')]
    choice = menu(text, options, default = default)
    return choice == 'Yes'

def startingMenu():
    '''
    Creates the starting menu.\n
    Returns\:\n
    -1: Quit;\n
    1: Load a game;\n
    2: Start a new game with an existing hero;\n
    3: Create a hero;\n
    4: Go to settings;\n
    5: View rankings.
    '''
    clear()
    options = [
        MenuOption('Create your first hero!', 'ugreen', 'Let\'s start your first game! Your hero is destined for success.', 3),
        MenuOption('View nation, league or club rankings', 'uyellow', 'View worldwide nation, league or club rankings.', 5),
        MenuOption('Go to settings', 'bold', 'Customise your game.', 4),
        MenuOption('Quit', 'dred', 'Quit the game.\nBut you will not pick this, right?', -1)
    ]
    if saveFiles:
        options.insert(1, MenuOption('Load a game', 'gyellow', 'Load a game from an existing save file.', 1))
        options[0].text = 'Start a new game'
        options[0].description = 'Create a new hero and start a new game with him.'
    if setupFiles:
        options.insert(1, MenuOption('Start a new game with an existing hero', 'ygreen', 'Choose a hero you have already created and start a new game with him.\nThe career will begin when he is 16 years old.', 2))
        options[0].text = 'Start a new game with a new hero'
        options[0].description = 'Create a new hero and start a new game with him.'
    return menu('Welcome to Career! What do you want to do?', options, help = '(use arrow keys, then press Enter)')

def rankingsMenu():
    '''
    Creates the rankings menu.\n
    Returns\:\n
    -1: Quit;\n
    1: Leagues;\n
    2: Nations;\n
    3: Clubs.
    '''
    clear()
    options = [
        MenuOption('Nations', 'ugreen', 'View FIFA nation rankings.', 1),
        MenuOption('Leagues', 'cgreen', 'View worldwide league rankings based on the average rating of their clubs.', 2),
        MenuOption('Clubs', 'gcyan', 'View worldwide rankings of every club in the game based on their rating.', 3),
        MenuOption('Quit', 'dred', 'Quit to the main menu.', -1)
    ]
    toReturn = menu('Which rankings do you want to view?', options)
    clear()
    return toReturn

### Misc functions

def viewNationRankings() -> None:
    '''
    Prints the nation rankings.
    '''
    tableHeaders = ['№', Header('Code ', columnAlign = 'center'), 'Nation', 'Best league']
    tableRows = []
    for nation in Nation.instances:
        tableRows.append([nation.fifaRanking, nation.shortName, nation.name, nation.leagues[0].name if nation.leagues else '!fill:—', ])
    Table(tableRows, tableHeaders, '<uyellow>Worldwide national team rankings:</uyellow>', '<uyellow>Press Enter to go back to the start menu: </uyellow>').print(True)

def viewLeagueRankings() -> None:
    '''
    Prints the league rankings.
    '''
    tableHeaders = ['№', Header('Rating', columnAlign = 'center'), 'Code', 'League', 'Best clubs']
    tableRows = []
    for i, league in enumerate(sorted(League.instances, key = lambda x: -x.rating), 1):
        tableRows.append([i, league.rating, league.shortName, league.name, ', '.join([club.name for club in league.sortedClubs[:3]])])
    Table(tableRows, tableHeaders, '<uyellow>Worldwide football league rankings:</uyellow>', '<uyellow>Press Enter to go back to the start menu: </uyellow>').print(True)

def viewClubRankings() -> None:
    '''
    Prints the club rankings.
    '''
    tableHeaders = ['№', Header('Rating', columnAlign = 'center'), Header('Country', columnAlign = 'center'), 'Colors', Header('Code ', columnAlign = 'center'), 'Generic name', 'Full name', 'Nickname']
    tableRows = []
    for i, club in enumerate(sorted(Club.instances, key = lambda x: -x.rating), 1):
        tableRows.append([i, club.rating, club.nation.shortName, club.colorText('   ', bg = True) + club.color2Text('   ', bg = True), club.shortName, club.name, club.fullName, club.nickname])
    Table(tableRows, tableHeaders, '<uyellow>Worldwide football club rankings:</uyellow>', '<uyellow>Press Enter to go back to the start menu: </uyellow>').print(True)

def OPTAtoRating(optaPowerRanking):
    '''
    Converts an OPTA Power Ranking to the in-game rating using this formula:\n
    inGameRating = {optaPowerRanking} * 3 / 5 + 27
    '''
    return round(float(optaPowerRanking) * 3 / 5 + 27, 1)

def floor(num) -> int:
    '''
    Rounds {num} to the lowest integer of the two nearest ones.
    '''
    return int(num // 1)

def removeExtension(file, extension = FILE_EXTENSION) -> str:
    '''
    Removes {extension} from {file}.
    '''
    return file.replace(extension, '')

def importPackages():
    '''
    Imports packages.
    '''
    global inspect, print_formatted_text, prompt, WordCompleter, HTML, Style, osName, system, chdir, path, listdir
    global getmtime, exists, fixWin, questionary, Choice, sysExit, datetime, format_exc
    global sha3_224, random, shuffle, choice, choices, safe_load, safe_dump, Layout, get_terminal_size

    from rich import inspect
    yield
    from rich.layout import Layout
    yield

    from prompt_toolkit import print_formatted_text, prompt
    yield
    from prompt_toolkit.completion import WordCompleter
    yield
    from prompt_toolkit.formatted_text import HTML
    yield
    from prompt_toolkit.styles import Style
    yield

    from os import name as osName, system, chdir, path, listdir, get_terminal_size
    yield
    from os.path import getmtime, exists
    yield

    from colorama import just_fix_windows_console as fixWin
    yield
    from questionary import select as questionary, Choice
    yield
    from random import random, shuffle, choice, choices
    yield
    from traceback import format_exc
    yield
    from yaml import safe_load, safe_dump
    yield
    from sys import exit as sysExit
    yield
    from datetime import datetime
    yield
    from hashlib import sha3_224
    yield

def progressBarSetting() -> bool:
    '''
    Same as settings.viewProgress but works before settings were created.
    '''
    try:
        with open(files['settings'], encoding = 'utf-8') as f:
            return f.readlines()[3].find('Yes') != -1
    except:
        return False

### Classes

class Find:
    '''
    Placeholder for the find() function.
    '''
    @classmethod
    def find(cls, name, allowExceptions: bool = False):
        '''
        Returns a {cls} object that corresponds to {name} or -1 if object was not found.
        Raises an Exception if {allowExceptions} is True.\n
        Each {cls} instance must have a _searchOptions attribute containing strings that the instance can be found by.
        All strings in _searchOptions must be uncolored and lowercase.
        '''
        name = str(name).lower()
        for obj in cls.instances:
            if name in obj._searchOptions:
                return obj
        if allowExceptions:
            raise Exception(f'Could not find a {cls.__name__.lower()} named "{name}".')
        return -1

class ColorText:
    '''
    Placeholder for the colorText() function.
    '''
    def colorText(self, text, color = 'default') -> str:
        '''
        Colors {text} with {color} (color code, not hex!) in prompt_toolkit's HTML format.
        '''
        if not color:
            return text
        if color == 'default':
            color = self.color
        return f'<{color}>{text}</{color}>'

class Settings:
    '''
    Loads data in YAML from {files['settings']} and creates Setting objects from it.
    The settings are accessible from this object.\n
    A list of all settings:
        .viewProgress;
        .excTraceback;
        .allowRussia.
    '''
    def __init__(self):
        self._contents = loadData(files['settings'])
        self.viewProgress = self.newSetting()
        self.excTraceback = self.newSetting()
        self.allowRussia = self.newSetting()
        inspect(self.viewProgress)
        inspect(self.excTraceback)
        inspect(self.allowRussia)
        origInput()
    
    @property
    def settings(self):
        return Setting.instances
    
    def save(self):
        '''
        Saves itself to {files['settings']}.
        '''
        data = []
        for setting in self.settings:
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
        '''
        Removes the first setting from self._contents, creates a new Setting object and returns it.
        '''
        return Setting(self._contents.pop(0))

    def edit(self):
        '''
        Creates a pretty menu that allows the user to edit the settings.
        '''
        while True:
            print(self)
            setting = menu('Choose a setting to edit:', [MenuOption(setting.name, description = setting.description, value = setting) for setting in self.settings] + [MenuOption('Quit', 'dred', 'Quit to the main menu.', -1)])
            if setting == -1:
                break
            setting.edit()
        self.save()
    
    def __str__(self):
        return f'\n\n<uyellow>Your settings:</uyellow>\n\n{"".join([setting.view() for setting in self.settings])}'

class Setting:
    '''
    The class for a setting.\n
    Attributes:
        .name: The name of the setting.
        .description: The description of the setting.
        .setTo: The value that the setting is set to.
        .values: A list of values that the setting can be set to.
    '''
    instances = []
    def __init__(self, data):
        '''
        Arguments:
            data: A dictionary that contains the setting's name, description, setTo and values.
        '''
        Setting.instances.append(self)
        self.name = data['name']
        self.description = data['description'].replace(DOUBLE_BACKSLASH_N, BACKSLASH_N)
        self.setTo = data['setTo']
        self.values = data['values']
        if not self.setTo in self.values:
            raise Exception(f'{self.name} setting: {self.setTo} is not in {self.values}.')
    
    def view(self) -> str:
        '''
        Get the string representation of the setting that is suitable for showing to the user.
        '''
        return f'{self.name}: {colorSettingValue(self.setTo)}.\n<ugrey>{self.description}</ugrey>\n\n'

    def edit(self):
        '''
        Creates a pretty menu that allows the user to edit a setting.
        '''
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
    The class for a menu option.
    Attributes:
        .text: The text of the option.
        .color: The color of the text of the option.
        .description: The description of the option (shown at the bottom while choosing).
        .returnValue: Whatever the menu() function will return if the user chooses this option. .text by default.
    '''
    def __init__(self, text, color: str | None = None, description: str | None = None, value = None):
        '''
        Arguments:
            text: The text of the option.
            color: The color of the option. The option will have the default color if this is set to None.
            description: The description of the option. The option will not have a description if this is set to None.
            value: Whatever the menu() function will return if the user chooses this option. {text} by default.
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
    The class for a table.
    Supports prompt_toolkit's HTML formatted text.
    Attributes:
        .style: The table's style. To view an example of a style print Table.defaultStyle.
        .title: The table's title.
        .caption: The table's caption. Printed after the table.
        .noHeaders: True if the table has no headers, False otherwise.
        .headers: A list of Header objects. If the table has no headers, this will be full of automatically generated empty Header objects. Use .noHeaders to check for that if you need to.
        .data: A list of Row objects.
        .columns: Like .data, but instead of containing data grouped by rows in contains data grouped by columns.It is still a list of Row objects though.
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

    'fill': ' '}

    def __init__(self, data: list, headers: list | None = None, title: str | None = None, caption: str | None = None, style: dict = None):
        '''
        Arguments:
            data: The table's rows. Can be a list of Row objects or a list of lists of cell values. Doesn't include headers.
            headers: The table's headers. Can be a list of Header objects or a list of strings. If set to None, the table will have no headers.
            title: The table's title. 
            caption: Printed below the table.
            style: Table.defaultStyle if set to None.
        '''        
        if style:
            self.style = style
        else:
            self.style = Table.defaultStyle
        
        leftStyleKeys = []
        warning = []
        for key in self.style:
            try:
                leftStyleKeys.remove(key)
            except:
                warning.append(key)
        if leftStyleKeys:
            raise Exception(f'Table style is missing the following keys: {", ".join(leftStyleKeys)}.{f" Warning: your style has additional keys that are not necessary ({', '.join(warning)})." if warning else ""}')

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
        '''
        Get the table's representation as a string.
        '''
        columnLens = [max(len(header.ucText), *[len(text) for text in column.ucCells]) for header, column in zip(self.headers, self.columns)]

        if not self.title:
            table = ''
        else:
            table = alignText(self.title, uncolorText(self.title), 'center', len(columnLens) * 3 + sum(columnLens) + 1) + '\n'

        if not self.noHeaders:
            table += f"{self.style['leftTop']}"
            for columnLen in columnLens:
                table += f"{self.style['headerHor'] * (columnLen + 2)}{self.style['middleTop']}"
            table = table[:-1] + self.style['rightTop'] + '\n'
            
            for columnLen, header in zip(columnLens, self.headers):
                table += self.style['headerVert'] + self.style['fill'] + alignText(header.text, header.ucText, header.selfAlign, columnLen, fill = self.style['fill']) + self.style['fill']
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
            for columnLen, header, cell, ucCell in zip(columnLens, self.headers, row.cells, row.ucCells):
                fill = self.style['fill']
                if cell.find('!fill:') != -1:
                    fill = cell[-1]
                    cell = ''
                    ucCell = ''
                table += self.style['dataVert'] + self.style['fill'] + alignText(colorText(cell, header.columnColor), ucCell, header.columnAlign, columnLen, fill = fill) + self.style['fill']
            table += self.style['dataVert'] + '\n'

        table += f"{self.style['leftBottom']}"
        for columnLen in columnLens:
            table += f"{self.style['dataHor'] * (columnLen + 2)}{self.style['middleBottom']}"
        table = table[:-1] + self.style['rightBottom'] + '\n'

        if self.caption:
            table += self.caption

        return table
    
    def print(self, inputToo: bool = False) -> None | str:
        '''
        Prints the table.
        Returns the user input if inputToo is True.
        '''
        for line in self.getPrintable().splitlines(inputToo):
            print(line, end = '' if inputToo else '\n')
        if inputToo:
            return input()

class Header:
    '''
    The class for a table header.
    Attributes:
        .text: The header's text.
        .ucText: The header's uncolored text.
        .selfAlign: The header's alignment. Can be 'left', 'right' or 'center'.
        .columnAlign: The alignment of every cell in the header's column. Can be 'left', 'right' or 'center'.
        .columnColor: The color of every cell in the header's column.
    '''
    def __init__(self, text, selfAlign: str = 'center', columnAlign: str = 'left', columnColor: None | str = None):
        '''
        Arguments:
            text: The header's text.
            selfAlign: The header's alignment. Can be 'left', 'right' or 'center'.
            columnAlign: The alignment of every cell in the header's column. Can be 'left', 'right' or 'center'.
            columnColor: The color of every cell in the header's column.
        '''
        self.text = str(text)
        self.ucText = uncolorText(text)
        self.selfAlign = selfAlign
        self.columnAlign = columnAlign
        self.columnColor = columnColor

class Row:
    '''
    The class for a table row.
    Attributes:
        .cells: A list of cell values.
        .ucCells: Same as .cells, but contains uncolored text only.
    '''
    def __init__(self, *cells):
        '''
        Arguments:
            *cells: A list of cell values.
        '''
        self.cells = [str(cell) for cell in cells]
        self.ucCells = [uncolorText(cell) for cell in self.cells]

class Nation(ColorText, Find):
    instances = []
    def __init__(self, names, shortName, nationality, color, fifaRanking):
        Nation.instances.append(self)
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
        self.leagues = []
        self.clubs = []
        self._searchOptions = [str(self.fifaRanking), self.ucShortName.lower()] + [nationName.lower() for nationName in self.ucNames]

class Trait(ColorText, Find):
    instances = []
    def __init__(self, name, description, color = 'lgrey', category = None):
        Trait.instances.append(self)
        self.color = color
        self.num = self.colorText(len(Trait.instances))
        self.name = self.colorText(name)
        self.description = self.colorText(description)
        self.category = self.colorText(category)
        self.ucNum = len(Trait.instances)
        self.ucName = name
        self.ucDescription = description
        self.ucCategory = category
        self._searchOptions = [str(self.ucNum), self.ucName.lower()]

    @staticmethod
    def printInstances():
        longestName = 0
        for instance in Trait.instances:
            longestName = max(longestName, len(instance.ucName))
        for instance in Trait.instances:
            print(f'{instance.num}{instance.colorText(".")}{"" if instance.ucNum >= 10 or len(Trait.instances) < 10 else " "} {instance.name}{" " * (longestName - len(instance.ucName))} {instance.colorText("-")} {instance.description}')

class Position(ColorText):
    instances = []
    def __init__(self, shortName, name, colorName, weightings, modifier):        
        Position.instances.append(self)
        self.weightings = weightings
        self.modifier = modifier
        self.color = colorName
        self.shortName = self.colorText(shortName)
        self.name = self.colorText(name)
        self.ucShortName = shortName
        self.ucName = name
    
class Player:
    instances = []
    def __init__(self, nation = 'Already set', overall = 0, potential = 0):
        Player.instances.append(self)
        self.potential = potential if potential else round(80 + 15 * random())
        self.age = 16
        if not overall:
            return self
        self.nation = nation
        self.position = Position.getRandomPosition()
        # blah blah blah
        # define all the attributes!

    @property
    def primaryPosition(self):
        return self.positions[0]
        
    @property
    def secondaryPositions(self):
        toReturn = []
        primaryPosScore = self.getPositionScore(self.primaryPosition)
        positions = self.positions
        for position in positions[1:]:
            if primaryPosScore - self.getPositionScore(position) > 2:
                break
            toReturn.append(position)
        return toReturn
    
    @property
    def formattedSecondaryPositions(self):
        return ', '.join([pos.name for pos in self.secondaryPositions]) if self.secondaryPositions else 'none'
    
    @property
    def positions(self):
        return sorted(Position.instances, key = self.getPositionScore, reverse = True)

    @property
    def ucDescription(self):
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
        return list(descriptions.keys())[list(descriptions.values()).index(sorted(descriptions.values(), reverse = True)[0])] + ' ' + self.primaryPosition.ucName

    @property
    def description(self):
        # input(descriptions)
        return self.primaryPosition.colorText(self.ucDescription)
    
    @property
    def attributes(self):
        return [self.pac, self.sho, self.pas, self.dri, self.dfn, self.phy]
    
    def getPositionScore(self, position):
        score = self.pac * position.weightings[0] + self.sho * position.weightings[1] + self.pas * position.weightings[2] + self.dri * position.weightings[3] + self.dfn * position.weightings[4] + self.phy * position.weightings[5] + (99 if self.foot == 'left' or self.hasTrait('Weak Foot') else 1) * position.weightings[6] + (99 if self.foot == 'right' or self.hasTrait('Weak Foot') else 1) * position.weightings[7] + position.modifier
        return score

    def hasTrait(self, targetTrait):
        return targetTrait in self.traits or Trait.find(targetTrait) in self.traits

    def viewProfile(self):
        # input('\n' + '\n'.join([str(i) + '. ' + pos.shortName + ' ' + str(self.getPositionScore(pos)) for i, pos in enumerate(self.positions, 1)]) + '\n')
        clear()
        print(f'<bold>{(self.fullName + f"{SINGLE_QUOTE}s profile:").center(35 + len(self.fullName) - len(self.ucFullName))}</bold>\n')
        print(f'<bold>Age:</bold>                <uyellow>{self.age}</uyellow>.')
        print(f'<bold>Preferred position:</bold> {self.primaryPosition.name}.')
        print(f'<bold>Other positions:</bold>    {self.formattedSecondaryPositions}.')
        print(f'<bold>Fan description:</bold>    {self.description}.')
        print(f'<bold>Nationality:</bold>        {self.nation.nationality}.\n')
        Table(list(zip(Attributes + [PreferredFoot], self.attributes + [self.foot])), title = f'<uyellow>{type(self).__name__} attributes:</uyellow>').print()
        print(f'\n<bold>{type(self).__name__} traits:</bold>')
        for trait in self.traits:
            print(f'{trait.name}{" " * (max([len(trait.ucName) for trait in self.traits]) - len(trait.ucName))} {trait.colorText("-")} {trait.description}')
        input('\n<uyellow>Press Enter to continue.</uyellow> ')
    
    def colorText(self, text):
        if isinstance(self, Hero):
            return '<underline>' + self.nation.colorText(text) + '</underline>'
        return self.nation.colorText(text)

    def getDifferenceFromMax(self, attribute):
        attributes = self.attributes
        attributes.remove(attribute)
        return attribute - max(attributes)

class Hero (Player):
    def __init__(self, mode, data = None):
        def getAttribute(attribute, pointsSpent = 0, attributesLeft = 0):
            upperBound = min(MAX_POINTS, ALL_POINTS - pointsSpent - attributesLeft * MIN_POINTS)
            lowerBound = max(MIN_POINTS, ALL_POINTS - pointsSpent - attributesLeft * MAX_POINTS)
            while True:
                value = input(f'You have <uyellow>{ALL_POINTS - pointsSpent}</uyellow> points. How many will you allocate to {attribute}?{" (enter a number, then press Enter)" if not setupFiles and attributesLeft == 5 else ""} ')
                if value == '/quit':
                    raise EOFError
                try:
                    value = int(value)
                    if lowerBound <= value <= upperBound:
                        return value
                    raise Exception
                except:
                    print(f'<ured>You need to input a number between {lowerBound} and {upperBound}.\nAll points have to be used.</ured>\n')

        def getTrait(message):
            while True:
                traitNum = input(message)
                if traitNum == '/quit':
                    raise EOFError
                try:
                    traitNum = int(traitNum)
                    result = Trait.instances[traitNum - 1]
                    if 1 <= traitNum:
                        if result in self.traits:
                            print(f'<ured>You already selected {result.name}.</ured>')
                            continue
                        self.traits.append(result)
                        break
                    raise Exception
                except:
                    print(f'<ured>You need to input a number between 1 and {len(Trait.instances)} which corresponds to a trait.</ured>\n')

        match mode:
            case 'fromInputs':
                clear()
                menu('If you want to quit to the main menu, type /quit instead of your input.', [MenuOption('Got it!', color = 'dgreen')])
                clear()
                print('<bold>Step 1. Who is your hero?</bold>\n\n')
                while True:
                    self.fullName = input(f'<uyellow>Enter his full name{" (press Enter to confirm)" if not setupFiles else ""}:</uyellow> ')
                    if self.fullName == '/quit':
                        raise EOFError
                    if len(self.fullName.replace(' ', '')) < 2:
                        print('<ured>The hero\'s full name must be at least 2 characters long.</ured>\n\n')
                        continue
                    try:
                        self.fullName.encode()
                    except:
                        print('<ured>This full name contains invalid characters.\nPlease pick a different one.</ured>')
                        continue
                    self.shirtName = self.fullName.split()
                    self.shirtName = self.shirtName[-1] if len(self.shirtName) > 1 else self.fullName
                    snUserSuggestion = input(f'\n<uyellow>Enter his shirt name{" (you can edit this text!)" if not setupFiles else ""}:</uyellow> ', default=self.shirtName)
                    if snUserSuggestion == '/quit':
                        raise EOFError
                    if len(snUserSuggestion.replace(' ', '')) < 2:
                        print('<ured>The hero\'s shirt name must be at least 2 characters long.</ured>', '\n\n')
                        continue
                    self.shirtName = snUserSuggestion
                    try:
                        self.shirtName.encode()
                    except:
                        print('<ured>This shirt name contains invalid characters.\nPlease pick a different one.</ured>')
                        continue
                    while True:
                        nationSuggestion = input(f'<uyellow>\nEnter his nation\'s name or code{" (type the beginning, then use arrow keys)" if not setupFiles else ""}:</uyellow> ', completer = WordCompleter(nationNames, ignore_case = True)).lower()
                        if nationSuggestion == '/quit':
                            raise EOFError
                        self.nation = Nation.find(nationSuggestion)
                        if self.nation != -1:
                            break
                        print('<ured>Nation not found.</ured>\n\n')
                    print(f'\n\n<uyellow>Let\'s check.</uyellow>\nThe hero\'s full name is {self.fullName}.\nHis shirt name is {self.shirtName}.\nHis nation is {self.nation.name}.')
                    if yesNoMenu('Is everything here correct?'):
                        break
                    print('\n\n')
                
                clear()
                print('<bold>Step 2. Time to determine his strengths and weaknesses!</bold>\n\n')
                while True:
                    print(f'You have <uyellow>{ALL_POINTS}</uyellow> points to allocate.\nThey must be distributed among 6 attributes: {pace}, {shooting}, {passing}, {dribbling}, {defending} and {physicality}.\nEach attribute must have from <uyellow>{MIN_POINTS}</uyellow> to <uyellow>{MAX_POINTS}</uyellow> points assigned to it.\n')
                    self.pac = getAttribute(pace, attributesLeft = 5)
                    self.sho = getAttribute(shooting, self.pac, 4)
                    self.pas = getAttribute(passing, self.pac + self.sho, 3)
                    self.dri = getAttribute(dribbling, self.pac + self.sho + self.pas, 2)
                    self.dfn = getAttribute(defending, self.pac + self.sho + self.pas + self.dri, 1)
                    self.phy = getAttribute(physicality, self.pac + self.sho + self.pas + self.dri + self.dfn)
                    self.foot = menu('Choose the preferred foot of your hero!', [MenuOption('left', color = 'uyellow', value = 'left'), MenuOption('right', color = 'uyellow', value = 'right')])
                    print(f'\n\n<uyellow>Let\'s check.</uyellow>')
                    Table(list(zip(Attributes + [PreferredFoot], self.attributes + [self.foot])), title = f'<uyellow>The hero\'s attributes are:</uyellow>').print()
                    if yesNoMenu('Is everything here correct?'):
                        break
                    print('\n\n')

                clear()
                while True:
                    print(f'<bold>Step 3. And, finally, let\'s look at his traits!</bold>\n\n<uyellow>Pick 3 traits for your hero.</uyellow>\n')
                    Trait.printInstances()
                    print(f'\nInput the trait number, for example, <uyellow>1</uyellow> for {Trait.instances[0].name}, <uyellow>2</uyellow> for {Trait.instances[1].name} and so on.\n')
                    self.traits = []
                    for i, message in enumerate(['What trait do you pick?', 'Pick another one!', 'And the last one:'], 1):
                        getTrait(f'<uyellow>({i}/3) {message}</uyellow> ')
                    self.traits = sorted(self.traits, key = lambda x: x.ucNum)

                    print(f'\n\n<uyellow>Let\'s check.</uyellow>\nThe hero\'s traits are: {self.traits[0].name}, {self.traits[1].name}, {self.traits[2].name}.')
                    if yesNoMenu('Is everything here correct?'):
                        break
                    print('\n\n')

            case 'fromDict':
                data['nation'] = Nation.find(data['nation'], True)
                data['traits'] = [Trait.instances[trait - 1] for trait in data['traits']]
                self.__dict__ = data
                self.ucFullName = uncolorText(self.fullName)
                self.ucShirtName = uncolorText(self.shirtName)

            case _:
                raise Exception(f'Hero(): invalid "mode" argument ({mode}).')
        super().__init__()
        self.fullName, self.ucFullName = [self.colorText(self.fullName), self.fullName]
        self.shirtName, self.ucShirtName = [self.colorText(self.shirtName), self.shirtName]

    def toDict(self):
        data = {a: b for a, b in self.__dict__.items()}
        data['nation'] = data['nation'].ucName
        data['traits'] = [trait.ucNum for trait in data['traits']]
        data['fullName'] = data['ucFullName']
        data['shirtName'] = data['ucShirtName']
        data.pop('potential')
        data.pop('ucFullName')
        data.pop('ucShirtName')
        return data

class Club(Find):
    instances = []
    def __init__(self, ovr, fullName, names, nickname, shortName, colors):
        Club.instances.append(self)
        self.rating = ovr
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
        self._searchOptions = [self.ucFullName.lower(), self.ucNickname.lower(), self.ucShortName.lower()] + [clubName.lower() for clubName in self.ucNames]
    
    def colorText(self, text, bg = False):
        return f'<{"bg" if bg else ""}{self.colors[0]}>{text}</{"bg" if bg else ""}{self.colors[0]}>'
    
    def color2Text(self, text, bg = False):
        return f'<{"bg" if bg else ""}{self.colors[1]}>{text}</{"bg" if bg else ""}{self.colors[1]}>'
    
    def colorFullText(self, text):
        return f'<{self.colors[0]}><bg{self.colors[1]}>{text}</bg{self.colors[1]}></{self.colors[0]}>'
    
class League(Find):
    instances = []
    def __init__(self, name, nation, clubs):
        League.instances.append(self)
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
    
    def colorText(self, text):
        return self.nation.colorText(text)
    
    @property
    def rating(self):
        return self.getRating()
    
    def getRating(self, mode = 'average'):
        match mode:
            case 'average':
                return round(sum([club.rating for club in self.clubs]) / self.capacity, 2)
            case 'top':
                return round(sum([club.rating for club in self.clubs[:8]]) / 8, 2)
            case 'median':
                return self.sortedClubs[self.capacity // 2]
    
    @property
    def sortedClubs(self):
        return sorted(self.clubs, key = lambda x: -x.rating)

### Imports

if progressBarSetting():
    with Progress() as bar:
        importCount = 19
        completedCount = 3
        task = bar.add_task('[green]Importing code other people wrote...', total = importCount, completed = completedCount)
        
        for _ in importPackages():
            bar.update(task, advance = 1)
        bar.advance(task, 1)
else:
    for _ in importPackages():
        pass
    
### Preset variables

colorText = lambda text, color: ColorText().colorText(text, color)

pace, Pace = colorDoubleText('pace', 'uyellow')
shooting, Shooting = colorDoubleText('shooting', 'ured')
passing, Passing = colorDoubleText('passing', 'ucyan')
dribbling, Dribbling = colorDoubleText('dribbling', 'umagenta')
defending, Defending = colorDoubleText('defending', 'ugreen')
physicality, Physicality = colorDoubleText('physicality', 'bold')
preferredFoot, PreferredFoot = colorDoubleText('preferred foot', 'uorange')

attributes = [pace, shooting, passing, dribbling, defending, physicality]
Attributes = [Pace, Shooting, Passing, Dribbling, Defending, Physicality]

### Preparation code

fixWin()
chdir(path.dirname(path.abspath(__file__)))
settings, mainStyleDict = parseDatabase(list(files.values()) + list(dirs.values()), [createNations, createLeagues, createPositions, createTraits, Settings, createStyle], [files['settings'], files['style']])
mainStyle = Style.from_dict(mainStyleDict)
nationNames = [option for nation in Nation.instances for option in nation._searchOptions]

### Testing



### Game loop

while True:
    setupFiles = getFiles(dirs['setups'])
    saveFiles = getFiles(dirs['saves'])
    try:
        match startingMenu():
            case -1:
                if yesNoMenu('Are you sure you want to quit?', default = 'No'):
                    clear()
                    print('<uorange>Bye then... Hope to see you soon!</uorange>')
                    sleep(2)
                    sysExit()
                continue
            case 1:
                notReadyWarning()
                continue
            case 2:
                hero = loadSetup()
                if not hero:
                    continue
            case 3:
                if setupFiles and not yesNoMenu('Are you sure you want to create a new hero?', default = 'No'):
                    continue
                hero = Hero('fromInputs')
                saveSetup(hero)
            case 4:
                settings.edit()
                continue
            case 5:
                while True:
                    clear()
                    match rankingsMenu():
                        case 1:
                            viewNationRankings()
                        case 2:
                            viewLeagueRankings()
                        case 3:
                            viewClubRankings()
                        case -1:
                            break
                continue
    except EOFError:
        continue
    hero.viewProfile()
    
    clear()
    input('<dred>There will be a career here soon... For now, though, press Enter:</dred> ')