"""Модуль реализует управление игрой (создание, скорборд, ...)"""

import copy
import datetime
import enum
import itertools
import json
import logging
import os.path
import operator
import zlib
from . import game, utils


__all__ = ['Minesweeper', 'EventTypes', 'Scoreboard',
           'LOGGER_NAME',
           'LoadError', 'SaveError']

LOGGER_NAME = 'minesweeper.driver'
LOGGER = logging.getLogger(LOGGER_NAME)


class Scoreboard:
    """Скорборд"""
    PARAMS_SEP = ':'
    SCOREBOARD_FILE = 'scores.dat'

    def __init__(self, filename=SCOREBOARD_FILE):
        """Загрузка скорборда из файла"""
        LOGGER.info('Loading scoreboard file "%s"', filename)
        self._filename = filename

        if not os.path.exists(filename):
            LOGGER.info('Scoreboard file is missing and will be created')
            with open(filename, 'x') as f:
                json.dump({}, f)

        with open(filename) as f:
            self._scores = self._check(json.load(f, parse_int=float))

        LOGGER.info('Scoreboard was loaded')

    def _check(self, scores):
        LOGGER.info('Checking scoreboard data...')
        result = {}

        if not isinstance(scores, dict):
            LOGGER.error('Invalid type of data: "%s". Scoreboard not loaded',
                         type(scores))
            return result

        errors = len(scores)
        for (key, values) in scores.items():
            params = [utils.parse_int(x)
                      for x in key.split(Scoreboard.PARAMS_SEP)]
            if len(params) < 3:
                LOGGER.warning('Wrong key of entry: "%s". Skip', key)
                continue

            params_errors = False
            for (idx, value) in enumerate(params):
                if value is None or value <= 0:
                    LOGGER.warning('Wrong %d key: "%s". Skip', idx, value)
                    params_errors = True
                    break

            if params_errors:
                continue

            items = []
            if not isinstance(values, list):
                LOGGER.warning(
                    'Invalid type of entry\'s "%s" values: "%s". Skip',
                    key, type(values))
                continue

            errors += len(values)
            for value in values:
                if not isinstance(value, list):
                    LOGGER.warning(
                        'Invalid type of scoreboard item in "%s": "%s". Skip',
                        key, type(value))
                    continue
                if len(value) != 2:
                    LOGGER.warning('Wrong scoreboard item: "%s". Skip', value)
                    continue
                if not isinstance(value[0], str):
                    LOGGER.warning(
                        'Invalid type of `name` in scoreboard item: '
                        '"%s". Skip', type(value[0]))
                    continue
                if not isinstance(value[1], float):
                    LOGGER.warning(
                        'Invalid type of `time` in scoreboard item: '
                        '"%s". Skip', type(value[1]))
                    continue
                value[1] = int(value[1])
                if value[1] <= 0:
                    LOGGER.warning(
                        'Invalid value of `time` in scoreboard item: '
                        '"%s". Skip', value[1])
                    continue
                errors -= 1
                items.append(tuple(value))

            errors -= 1
            result[key] = items

        if errors:
            LOGGER.warning('Scoreboard file has %d errors', errors)

        return result

    def add_score(self, field, name, time):
        """Добавление рекорда в скорборд"""
        if not isinstance(field, game.Field):
            raise TypeError('field')
        name = str(name)
        time = int(time)
        if time <= 0:
            raise ValueError('time')

        key = Scoreboard.PARAMS_SEP.join(
            map(str, list(field.size()) + [field.bombs()]))
        LOGGER.info('Adding new record in "%s": <"%s", "%s">', key, name, time)
        if key not in self._scores:
            self._scores[key] = []
        self._scores[key].append((name, time))

        with open(self._filename, 'w') as f:
            json.dump(self._scores, f)
        LOGGER.info('Record written')

    def get_params(self):
        """Параметры полей в скорборде"""
        for key in self._scores.keys():
            (*size, bombs) = [int(x) for x in key.split(Scoreboard.PARAMS_SEP)]
            yield (tuple(size), bombs)

    def get_scores(self, size, bombs):
        """Скорборд полей с заданными параметрами"""
        key = Scoreboard.PARAMS_SEP.join(map(str, list(size) + [bombs]))
        return sorted(self._scores.get(key, []), key=operator.itemgetter(1))


class EventTypes(enum.Enum):
    """Игровое событие:
        NEW_GAME     - создана новая игра
        CELL_CHANGED - изменилось состояние клетки
        END_CHANGE   - закончилось изменение состояний
        PLAYER_WIN   - игра завершена, игрок выиграл
        PLAYER_LOSE  - игра завершена, игрок проиграл
    """
    NEW_GAME = 1
    CELL_CHANGED = 2
    END_CHANGE = 3
    PLAYER_WIN = 4
    PLAYER_LOSE = 5


class LoadError(Exception):
    """Ошибка при загрузке игры"""
    pass


class SaveError(Exception):
    """Ошибка при сохранении игры"""
    pass


class Minesweeper:
    """Игровая логика с поддержкой партий ("драйвер" игр)"""

    def _game_init(self, field=None, states=None):
        self._field = field

        self._states = states or []
        if field is not None:
            if states is None:
                self._states.append(game.GameState(field))
            for state in self._states:
                state.add_cell_handler(self._cell_handler)

        self._redo_states = []
        self._spent_time = 0
        self._start_time = None
        self._win = False
        self._lose = False
        self._saved = True

        if field is not None:
            self._fire_event(EventTypes.NEW_GAME, field.size(), field.bombs())

    def _fire_event(self, event, *args):
        for handler in self._handlers[event]:
            handler(*args)

    def _cell_handler(self, *args):
        self._fire_event(EventTypes.CELL_CHANGED, *args)

    def _end_change(self):
        self._fire_event(EventTypes.END_CHANGE)

    def _propagate(self, state, prev=None):
        for cell in itertools.product(*(range(s) for s in self._field.size())):
            st = state.get_state(cell)
            if prev is None or prev.get_state(cell) != st:
                self._fire_event(EventTypes.CELL_CHANGED, cell, st)

    def _run(self):
        self._start_time = datetime.datetime.now()

    def _load(self, f):
        data = json.loads(zlib.decompress(f.read()).decode('utf-8'))

        for key in data:
            if key not in ('field', 'states', 'time'):
                LOGGER.warning('Unknown field in file: "%s". Skip', key)

        for (name, ftype) in (('field', str), ('states', list), ('time', int)):
            if not isinstance(data[name], ftype):
                LOGGER.error('Invalid type of `%s` field: "%s"',
                             name, type(data[name]))
                raise TypeError(name)

        LOGGER.info('Parsing field')
        field = game.Field.fromstr(data['field'])

        states = []
        for (idx, state) in enumerate(data['states']):
            try:
                LOGGER.info('Parsing state %d/%d...', idx, len(data['states']))
                states.append(game.GameState.fromstr(state, field))
            except Exception as e:
                LOGGER.warning('Error while parsing state "%s": "%s". Skip',
                               state, e)

        LOGGER.info('Preparing game')
        self._game_init(field, states)
        self._spent_time = data['time']
        self._run()
        self._propagate(self._state())

    def _save(self, f):
        data = {
            'field': str(self._field),
            'states': [str(state) for state in self._states],
            'time': self.get_time()
        }
        f.write(zlib.compress(json.dumps(data).encode('utf-8')))

    def _append_state(self, state, clean_redo=True):
        assert self._field is not None

        if self._start_time is None:
            self._run()

        if clean_redo:
            self._redo_states = []

        self._states.append(state)
        self._saved = False

        if state.check_win():
            self._do_win()

    def _end_game(self):
        self._spent_time = self.get_time()
        self._start_time = None
        self._states = [self._state()]
        self._redo_states = []

    def _do_win(self):
        LOGGER.info('Player win!')
        self._win = True
        self._end_game()
        self._fire_event(EventTypes.PLAYER_WIN, self._field)

    def _do_lose(self, cell):
        LOGGER.info('Player lose!')
        self._lose = True
        self._end_game()
        self._fire_event(EventTypes.PLAYER_LOSE, self._field, cell)

    def _state(self):
        return self._states[-1]

    def _complete(self):
        state = copy.copy(self._state())

        for cell in itertools.product(*(range(s) for s in self.size())):
            if self._state().get_state(cell) == game.CellState.UNKNOWN:
                state.set_flag(cell)

        self._append_state(state)

    def __init__(self):
        """Создание "драйвера" игр"""
        self._game_init()
        self._handlers = {event: [] for event in EventTypes}

    def new_game(self, size, bombs):
        """Создание новой игры с заданными размерами и числом бомб"""
        LOGGER.info('Creating new game %s with %s bombs', size, bombs)
        with utils.at_exit(self._end_change):
            self._game_init(game.Field.generate(size, bombs))

    def again(self):
        """Повтор игры сначала"""
        LOGGER.info('Playing again')
        with utils.at_exit(self._end_change):
            self._game_init(self._field)

    def load_game(self, filename):
        """Загрузка игры из файла"""
        with utils.at_exit(self._end_change):
            try:
                with open(filename, 'rb') as f:
                    self._load(f)
            except Exception as e:
                LOGGER.error('Failed to load game from "%s": "%s"',
                             filename, e)
                raise LoadError from e
            else:
                LOGGER.info('Loaded game from "%s"', filename)

    def save_game(self, filename):
        """Сохранение игры в файл"""
        if self._field is None:
            raise SaveError()

        try:
            with open(filename, 'wb') as f:
                self._save(f)
        except Exception as e:
            LOGGER.error('Failed to save game to "%s": "%s"',
                         filename, e)
            raise SaveError from e
        else:
            self._saved = True
            LOGGER.info('Saved game to "%s"', filename)

    def size(self):
        """Размер игрового поля"""
        return self._field.size() if self._field else None

    def bombs(self):
        """Количество бомб"""
        return self._field.bombs() if self._field else None

    def flags(self):
        """Количество установленных флагов"""
        return self._state().flags() if self._states else None

    def invert_flag(self, cell):
        """Инвертирование флага в клетке"""
        if not self._states:
            return

        LOGGER.info('Inverting flag @ %s', cell)
        with utils.at_exit(self._end_change):
            state = copy.copy(self._state())
            if state.set_flag(cell):
                self._append_state(state)
            elif state.unset_flag(cell):
                self._append_state(state)

    def open_cell(self, cell, autocomplete=False):
        """Открытие клетки"""
        if not self._states:
            return

        LOGGER.info('Open cell @ %s', cell)
        with utils.at_exit(self._end_change):
            state = copy.copy(self._state())
            res_open = state.open_cell(cell)

            if not res_open:
                self._append_state(state)
                self._do_lose(cell)
                return

            if state != self._state():
                self._append_state(state)

            if not autocomplete:
                return

            if self.flags() + self._state().unmarked_cells() == self.bombs():
                LOGGER.info('Completing game')
                self._complete()

    def can_undo(self):
        """Возвращается True, если есть ходы для отмены"""
        return len(self._states) > 1

    def undo(self):
        """Отмена хода"""
        if not self.can_undo():
            LOGGER.info("Can't undo turn': stack is empty")
            return

        assert self._start_time is not None

        LOGGER.info('Undo turn')
        with utils.at_exit(self._end_change):
            prev = self._state()
            self._redo_states.append(self._states.pop())
            self._saved = False
            self._propagate(self._state(), prev)

    def can_redo(self):
        """Возвращается True, если есть ходы для возврата"""
        return bool(self._redo_states)

    def redo(self):
        """Повтор хода"""
        if not self.can_redo():
            LOGGER.info("Can't redo turn: stack is empty")
            return

        assert self._start_time is not None

        LOGGER.info('Redo turn')
        with utils.at_exit(self._end_change):
            prev = self._state()
            self._append_state(self._redo_states.pop(), False)
            self._propagate(self._state(), prev)

    def event_handler(self, event):
        """Декоратор добавления обработчика событий"""
        def wrapper(func):
            self.add_event_handler(event, func)
            return func
        return wrapper

    def add_event_handler(self, event, handler):
        """Добавление обработчика событий"""
        if event not in self._handlers:
            return

        self._handlers[event].append(handler)

    def remove_event_handler(self, event, handler):
        """Удаление обработчика событий"""
        self._handlers[event].remove(handler)

    def get_state(self):
        """Текущее состояние игрового поля"""
        if self._field is None:
            return None

        result = copy.copy(self._state())
        result.remove_cell_handler(self._cell_handler)
        return result

    def get_neighbors(self, cell):
        """Число бомб в соседних клетках"""
        if self._field is None:
            return None

        return self._field.neighbor_bombs(cell)

    def get_time(self):
        """Пройденное время в сотых долях секунд"""
        current_time = datetime.datetime.now()

        if self._start_time is None:
            return self._spent_time

        delta = current_time - self._start_time
        return self._spent_time + int(100*delta.total_seconds())

    def is_win(self):
        """Возвращается True, если текущая партия выиграна"""
        return self._win

    def is_lose(self):
        """Возвращается True, если текущая партия проиграна"""
        return self._lose

    def saved(self):
        """Отсутствие несохранённых изменений в игре.

        Возвращается True, если текущее состояние было сохранено, либо
        игра уже завершена
        """
        return self._saved or self._win or self._lose
