#!/usr/bin/env python3
"""Консольная версия игры «Сапёр»"""

ERROR_EXCEPTION = 1
ERROR_WRONG_SETTINGS = 2
ERROR_PYTHON_VERSION = 3
ERROR_MODULES_MISSING = 4

import sys

if sys.version_info < (3, 4):
    print('Use python >= 3.4', file=sys.stderr)
    sys.exit(ERROR_PYTHON_VERSION)

import argparse
import enum
import inspect
import logging
import os
import re

if sys.platform.startswith('linux'):
    import readline

try:
    from minesweeper import driver, game, settings
except Exception as e:
    print('Game modules not found: "{}"'.format(e), file=sys.stderr)
    sys.exit(ERROR_MODULES_MISSING)


__version__ = '1.0'
__author__ = 'Samun Victor'
__email__ = 'victor.samun@gmail.com'

LOGGER_NAME = 'cmines'
LOGGER = logging.getLogger(LOGGER_NAME)


class CellChars(enum.Enum):
    """Текстовое представление клеток поля"""
    FLAG = 'F'
    BOMB = '*'
    MISTAKE = 'O'
    WRONG_FLAG = 'x'
    NOT_OPENED = '.'
    OPENED = lambda s: str(s or ' ')


CELL_PRINTER = {
    game.CellState.UNKNOWN: lambda *args: CellChars.NOT_OPENED.value,
    game.CellState.FLAG: lambda *args: CellChars.FLAG.value,
    game.CellState.OPENED:
        lambda game, cell: CellChars.OPENED(game.get_neighbors(cell))
}


def print_field(game_):
    """Печать игрового состояния поля в текстовом виде"""
    assert isinstance(game_, driver.Minesweeper)

    state = game_.get_state()
    assert state is not None

    for y in range(game_.size()[1]):
        for x in range(game_.size()[0]):
            print(CELL_PRINTER[state.get_state((x, y))](game_, (x, y)), end='')
        print()


def print_lose_field(state, field, cell):
    """Печать конечного состояния проигранной партии в текстовом виде"""
    assert isinstance(state, game.GameState)
    assert isinstance(field, game.Field)

    for y in range(field.size()[1]):
        for x in range(field.size()[0]):
            if cell == (x, y):
                s = CellChars.MISTAKE.value
            elif field.check_bomb((x, y)):
                if state.get_state((x, y)) == game.CellState.FLAG:
                    s = CellChars.FLAG.value
                else:
                    s = CellChars.BOMB.value
            elif state.get_state((x, y)) == game.CellState.FLAG:
                s = CellChars.WRONG_FLAG.value
            else:
                s = CellChars.OPENED(field.neighbor_bombs((x, y)))
            print(s, end='')
        print()


def norm_path(name, folder):
    """Возращает путь до файла `name` в каталоге `folder` если это возможно"""
    if os.sep in name:
        return name

    try:
        os.makedirs(folder, exist_ok=True)
    except Exception:
        return name

    result = os.path.join(folder, name)
    LOGGER.info('Normalize path: "%s" -> "%s"', name, result)
    return result


class ExitGame(Exception):
    """Сигнализирует о завершении игры"""
    pass


class BaseCommandsExecutor:
    """Базовый исполнитель команд пользователя"""
    CMD_PREFIX = '_cmd_'

    def __init__(self, config):
        self._config = config
        self._infos = {}

        for name in dir(self):
            if name.startswith(BaseCommandsExecutor.CMD_PREFIX):
                key = name[len(BaseCommandsExecutor.CMD_PREFIX):]
                method = getattr(self, name)
                self._infos[key] = (method, inspect.getfullargspec(method))

    def execute(self, name, *args):
        """Выполнение команды"""
        LOGGER.info('Execute "%s" with "%s"', name, ' '.join(args))

        if name not in self._infos:
            raise ValueError(self._config.string('wrong_cmd'))

        (method, info) = self._infos[name]

        if len(args) < len(info.args) - len(info.defaults or ()) - 1:
            raise ValueError(self._config.string('too_few_args'))

        if len(args) >= len(info.args):
            raise ValueError(self._config.string('too_many_args'))

        method(*args)


class GeneralCommands(BaseCommandsExecutor):
    """Общие команды (доступны всё время)"""
    def __init__(self, config, game_driver):
        super().__init__(config)
        self._driver = game_driver

    def _save(self, name=None):
        if name is None:
            name = input(self._config.string('prompt_filename') + ' ')

        if not name:
            print(self._config.string('save_cancel'))
            return

        name = norm_path(name, self._config.savedir)
        self._driver.save_game(name)

    def _check_saved(self):
        if self._driver.saved():
            return

        if input(self._config.string('prompt_save') + '[y/N] ').upper() == 'Y':
            self._save()

    def _cmd_about(self):
        print(self._config.string('about').format(
            __version__, '{} <{}>'.format(__author__, __email__)))

    def _cmd_help(self, command=None):
        if command is None:
            print(self._config.string('commands'))
            print('\n'.join(sorted(self._infos.keys())))
            return

        if command not in self._infos:
            return

        _, info = self._infos[command]
        req_count = len(info.args) - len(info.defaults or ())

        arg_fmt = lambda s: info.annotations.get(s, s)
        help_str = [command]
        help_str.extend(arg_fmt(info.args[i]) for i in range(1, req_count))
        help_str.extend('[{}]'.format(arg_fmt(info.args[i]))
                        for i in range(req_count, len(info.args)))
        print(' '.join(help_str))

    def _cmd_lang(self, language=None):
        if language is None:
            language = self._config.language
            print('{} ({})'.format(language, self._config.langs[language]))
        else:
            self._config.language = language

    def _cmd_langs(self):
        print(self._config.string('langs'))
        for (name, descr) in self._config.langs.items():
            print('{} ({})'.format(name, descr))

    def _cmd_new(self, width=None, height=None, bombs=None):
        self._check_saved()

        size = self._driver.size() or (None, None)
        width = width or size[0]
        height = height or size[1]
        bombs = bombs or self._driver.bombs()

        try:
            self._driver.new_game((width, height), bombs)
        except Exception:
            print(self._config.string('start_game_error'), file=sys.stderr)

    def _cmd_load(self, filename=None):
        self._check_saved()

        if filename is None:
            filename = input(self._config.string('prompt_filename') + ' ')

        if not filename:
            print(self._config.string('open_cancel'))
            return

        filename = norm_path(filename, self._config.savedir)
        self._driver.load_game(filename)

    def _cmd_exit(self):
        self._check_saved()
        raise ExitGame


class GameCommands(GeneralCommands):
    """Игровые команды (доступны только во время игры)"""
    def __init__(self, config, game_driver, scoreboard):
        super().__init__(config, game_driver)
        self._scores = scoreboard

    def _cmd_show(self):
        print_field(self._driver)

    def _cmd_open(self, x, y):
        self._driver.open_cell((x, y))

    def _cmd_flag(self, x, y):
        self._driver.invert_flag((x, y))

    def _cmd_scores(self):
        if self._scores is None:
            return

        table = list(self._scores.get_scores(self._driver.size(),
                                             self._driver.bombs()))
        idx_width = len(str(len(table)))
        max_width = max(len(str(value)) for (_, value) in table)
        for (idx, (name, value)) in enumerate(table):
            print('{1:>{0}}  {3:>{2}}  {4}'.format(
                idx_width, idx + 1, max_width, value, name))

    def _cmd_time(self):
        print(self._driver.get_time())

    def _cmd_stat(self):
        print('{}/{}'.format(self._driver.flags(), self._driver.bombs()))

    def _cmd_undo(self):
        self._driver.undo()

    def _cmd_redo(self):
        self._driver.redo()

    def _cmd_save(self, filename=None):
        self._save(filename)


def run(args, config, scoreboard, game_driver):
    """Запуск логики «Сапёра»"""
    @game_driver.event_handler(driver.EventTypes.PLAYER_WIN)
    def win_handler(field):
        print(config.string('win'))

        if scoreboard is None:
            return

        player_name = input(config.string('prompt_name') + ' ')
        if player_name:
            scoreboard.add_score(field, player_name, game_driver.get_time())

    @game_driver.event_handler(driver.EventTypes.PLAYER_LOSE)
    def lose_handler(field, cell):
        print(config.string('lose'))
        print_lose_field(game_driver.get_state(), field, cell)

    @game_driver.event_handler(driver.EventTypes.CELL_CHANGED)
    def cell_handler(cell, state):
        if state == game.CellState.FLAG:
            print('+ FLAG {} {}'.format(*cell))
        elif state == game.CellState.OPENED:
            print('OPEN {} {} ({})'.format(cell[0], cell[1],
                                           game_driver.get_neighbors(cell)))
        else:
            print('- OPEN {} {}'.format(*cell))

    @game_driver.event_handler(driver.EventTypes.NEW_GAME)
    def new_handler(size, bombs):
        print(config.string('new_game'))
        nonlocal newgame_started
        newgame_started = True

    newgame_started = False

    if args.load:
        LOGGER.info('Processing `load` parameter')
        try:
            game_driver.load_game(norm_path(args.load, config.savedir))
        except Exception as e:
            print(config.string('load_game_error'), file=sys.stderr)
            if not args.interactive:
                raise

    if args.game:
        LOGGER.info('Processing `game` parameter')
        try:
            *size, bombs = args.game
            game_driver.new_game(size, bombs)
        except Exception as e:
            print(config.string('start_game_error'), file=sys.stderr)
            if not args.interactive:
                raise

    game_cmds = GameCommands(config, game_driver, scoreboard)
    gen_cmds = GeneralCommands(config, game_driver)

    def do_commands(executor, stop_cond):
        SPLIT_RE = re.compile(r'\s+')

        while not stop_cond():
            try:
                command = input().strip()
                if command:
                    executor.execute(*SPLIT_RE.split(command))
            except ExitGame:
                raise
            except KeyboardInterrupt:
                executor.execute('exit')
            except Exception as e:
                print(e, file=sys.stderr)

    while True:
        if newgame_started:
            LOGGER.info('`GAME` mode')
            do_commands(game_cmds,
                        lambda: game_driver.is_win() or game_driver.is_lose())

        if args.interactive:
            LOGGER.info('`GLOBAL` mode')
            newgame_started = False
            do_commands(gen_cmds, lambda: newgame_started)
        else:
            break


def parse_args():
    """Разбор аргументов запуска"""
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTIONS]',
        description='Minesweeper game. Version {}'.format(__version__),
        epilog='Author: {} <{}>'.format(__author__, __email__))

    parser.add_argument(
        '-c', '--config', type=str,
        metavar='FILENAME', default='settings.ini', help='configuration file')
    parser.add_argument(
        '-d', '--debug',
        action='store_true', help='debug mode')
    arg_group = parser.add_mutually_exclusive_group()
    arg_group.add_argument(
        '-l', '--load', type=str,
        metavar='FILENAME', help='load and continue game')
    arg_group.add_argument(
        '-g', '--game', nargs=3, type=int,
        metavar=('WIDTH', 'HEIGHT', 'BOMBS'), help='start game')
    parser.add_argument(
        '-i', '--interactive',
        action='store_true', help='interactive mode')

    return parser.parse_args()


def main():
    """Точка входа в приложение"""
    args = parse_args()

    log = logging.StreamHandler(sys.stderr)
    log.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s <%(name)s>] %(message)s'))

    for module in (sys.modules[__name__], settings, driver):
        logger = logging.getLogger(module.LOGGER_NAME)
        logger.setLevel(logging.DEBUG if args.debug else logging.ERROR)
        logger.addHandler(log)

    LOGGER.info('Application started')
    try:
        config = settings.Settings(args.config)
    except Exception as e:
        print('Error while reading settings file\n{}'.format(e),
              file=sys.stderr)
        sys.exit(ERROR_WRONG_SETTINGS)
    else:
        LOGGER.info('Settings OK')

    if not args.interactive and not (args.load or args.game):
        LOGGER.warning('Using default game')
        args.game = config.default_game

    scoreboard = None
    try:
        scoreboard = driver.Scoreboard(config.scoreboard)
    except Exception as e:
        print('\n'.join((config.string('scoreboard_error'), str(e))),
              file=sys.stderr)
    else:
        LOGGER.info('Scoreboard OK')

    game_driver = driver.Minesweeper()
    LOGGER.info('Driver OK')

    try:
        LOGGER.info('Preparing complete. Run!')
        run(args, config, scoreboard, game_driver)
    except ExitGame:
        LOGGER.info('Exiting')
        sys.exit(0)
    except BaseException as e:
        import traceback
        LOGGER.error('Error: %s\n%s', e,
                     ''.join(traceback.format_tb(sys.exc_info()[-1])))
        print(e, file=sys.stderr)
        sys.exit(ERROR_EXCEPTION)


if __name__ == '__main__':
    main()
