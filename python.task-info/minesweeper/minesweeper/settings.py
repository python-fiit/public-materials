"""Модуль настроек игры"""
from collections import OrderedDict
import configparser
import enum
import logging
from . import game


__all__ = ['Settings', 'SettingsError',
           'LOGGER_NAME']

LOGGER_NAME = 'minesweeper.settings'
LOGGER = logging.getLogger(LOGGER_NAME)


class SettingsError(Exception):
    """Ошибка в настройках"""
    pass


def _parse_int_list(name, value, items):
    result = value.split(',')
    if len(result) != items:
        LOGGER.warning('Invalid %s: "%s". Skip', name, value)
        return None

    for (idx, item) in enumerate(result):
        try:
            item = int(item.strip())
            if item <= 0:
                raise ValueError
            result[idx] = item
        except ValueError as e:
            LOGGER.warning('Invalid item in %s: "%s". Skip', name, item)
            return None

    return tuple(result)


class Settings:
    """Класс реализует доступ к настройкам"""
    _SECTIONS = ('GLOBAL', 'GAMES', 'PICTURES', 'LANGS')
    _GLOBAL_KEYS = ('scoreboard', 'savedir', 'language',
                    'defaultgame', 'picture_size')
    _STR_PREFIX = 'STRINGS'

    def __init__(self, filename='settings.ini'):
        """Чтение настроек"""
        self._config = configparser.ConfigParser(default_section='')
        self._config.optionxform = str
        LOGGER.info('Reading config from "%s"', filename)
        self._config.read(filename, encoding='utf8')
        self._prepare()

    def _prepare(self):
        for section in self._config:
            if (section and section not in Settings._SECTIONS and
                    not section.startswith(Settings._STR_PREFIX)):
                LOGGER.warning('Unknown section: "%s". Skip', section)

        for section in Settings._SECTIONS:
            if section not in self._config:
                LOGGER.error('Error: section "%s" not found', section)
                raise SettingsError

        for key in self._global():
            if key not in Settings._GLOBAL_KEYS:
                LOGGER.warning('Unknown key "%s" in `GLOBAL`. Skip', key)

        for key in Settings._GLOBAL_KEYS:
            if key not in self._global():
                LOGGER.error('Error: key "%s" not found in `GLOBAL`', key)
                raise SettingsError

        self._lang = self._global()['language']
        if self._strings() is None:
            LOGGER.error('Error: unknown default language "%s"', self._lang)
            raise SettingsError

        self._picture_size = _parse_int_list(
            'picture_size', self._global()['picture_size'], 2)

        self._langs = {}
        for (key, value) in self._config['LANGS'].items():
            if self._strings(key) is None:
                LOGGER.warning('`STRINGS` is missing for "%s". Skip', key)
            else:
                self._langs[key] = value

        self._games = OrderedDict()
        for (key, value) in self._config['GAMES'].items():
            val = _parse_int_list('game', value, 3)
            if val is None:
                continue

            (ok, msg) = game.Field.check_params(val)
            if ok:
                self._games[key] = val
                continue

            LOGGER.warning('Error in game description: "%s". Skip', msg)

        self._defaultgame = self._global()['defaultgame']
        if self._defaultgame not in self._games:
            LOGGER.warning('Warning: unknown default game "%s". Try to skip',
                           self._defaultgame)
            self._defaultgame = None
            for key in self._games:
                LOGGER.warning('Now game "%s" is default', key)
                self._defaultgame = key

            if self._defaultgame is None:
                LOGGER.error('Error: no default game')
                raise SettingsError

    def _global(self):
        return self._config['GLOBAL']

    def _strings(self, lang=None):
        try:
            if lang is None:
                lang = self._lang

            return self._config['.'.join((Settings._STR_PREFIX, self._lang))]
        except KeyError:
            return None

    @property
    def scoreboard(self):
        """Название файла со скорбордом"""
        return self._global()['scoreboard']

    @property
    def savedir(self):
        """Название директории сохранения и загрузки игр"""
        return self._global()['savedir']

    @property
    def picture_size(self):
        """Размер картинок"""
        return self._picture_size

    @property
    def langs(self):
        """Доступные языки"""
        return self._langs

    @property
    def language(self):
        """Текущий язык"""
        return self._lang

    @language.setter
    def language(self, value):
        """Смена текущего языка"""
        if value not in self._langs:
            raise ValueError('value')

        self._lang = value

    @property
    def default_games(self):
        """Информация о предопределённых играх.
        Возвращается в виде (название, (ширина, высота, число_бомб))"""
        for (name, params) in self._games.items():
            yield (self.string('GAMES.{}'.format(name)), params)

    @property
    def default_game(self):
        """Название игры по умолчанию"""
        return self._games[self._defaultgame]

    def picture(self, name):
        """Имя файла с изображением `name`"""
        return self._config['PICTURES'].get(name, None)

    def string(self, name):
        """Строка с названием `name` и учётом текущего языка"""
        return self._strings().get(name, None)
