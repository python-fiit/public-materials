"""Модуль реализует логику игры «Сапёр»"""

from collections import defaultdict
import enum
import itertools
import functools
import operator
import random
from . import utils


__all__ = ['Field', 'CellState', 'GameState']


class Field:
    """Игровое поле"""
    def __init__(self, size, bombs):
        """Создание поля с заданным размером и расположением бомб"""
        (ok, msg) = Field.check_params(size)
        if not ok:
            raise ValueError(msg)

        self._size = utils.to_int(size)

        self._field = set()
        for bomb in bombs:
            bomb = utils.to_int(bomb)
            if len(bomb) != len(size) or not self.check_coords(bomb):
                raise ValueError('bombs')
            self._field.add(bomb)

    @staticmethod
    def fromstr(string):
        """Создание поля из его текстового представления"""
        (*size, bombs) = string.split(';')
        return Field(size, (bomb.split(',') for bomb in bombs.split(':')))

    @staticmethod
    def check_params(size, bombs=None):
        """Проверка параметров поля"""
        size = utils.to_int(size)

        if len(size) < 2:
            return (False, 'size')

        for (idx, item) in enumerate(size):
            if item <= 0:
                return (False, idx)

        if bombs is not None:
            if not 0 < int(bombs) < functools.reduce(operator.mul, size, 1):
                return (False, 'bombs')

        return (True, None)

    @staticmethod
    def generate(size, bombs_count):
        """Генерация поля с заданными размерами и количеством бомб"""
        (ok, msg) = Field.check_params(size, bombs_count)
        if not ok:
            raise ValueError(msg)

        size = utils.to_int(size)
        bombs_count = int(bombs_count)

        bombs = set()
        while len(bombs) < bombs_count:
            cell = tuple(random.randrange(0, m) for m in size)
            bombs.add(cell)

        return Field(size, bombs)

    def size(self):
        """Размеры поля"""
        return self._size

    def check_coords(self, cell):
        """Проверка принадлежности координат полю"""
        if len(cell) != len(self._size):
            return False

        return all(0 <= int(x) < self._size[i] for (i, x) in enumerate(cell))

    def bombs(self):
        """Число бомб"""
        return len(self._field)

    def check_bomb(self, cell):
        """Возвращает True если в данной клетке содержится бомба"""
        return utils.to_int(cell) in self._field

    def neighbor_cells(self, cell):
        """Сосдение клетки"""
        cell = utils.to_int(cell)
        if len(cell) != len(self._size):
            raise ValueError('cell')

        for delta in itertools.product((-1, 0, 1), repeat=len(self._size)):
            c = tuple(map(sum, zip(cell, delta)))
            if any(delta) and self.check_coords(c):
                yield c

    def neighbor_bombs(self, cell):
        """Количество бомб в соседних клетках"""
        cell = utils.to_int(cell)
        if len(cell) != len(self._size):
            raise ValueError('cell')

        return sum(1 for c in self.neighbor_cells(cell) if c in self._field)

    def __eq__(self, other):
        """Проверка равенства полей"""
        if not isinstance(other, Field):
            return False

        return (self._size, self._field) == (other._size, other._field)

    def __str__(self):
        """Текстовое представление поля"""
        bombs = ':'.join(','.join(map(str, bomb)) for bomb in self._field)
        return ';'.join(list(map(str, self._size)) + [bombs])


class CellState(enum.Enum):
    """Состояние клетки поля:
        UNKNOWN - неизвестно
        OPENED  - открыта
        FLAG    - установлен флаг
    """
    UNKNOWN = 0
    OPENED = 1
    FLAG = 2


class GameState:
    """Состояние игрового поля"""
    def __init__(self, field):
        """Создание начального состояния поля"""
        if not isinstance(field, Field):
            raise TypeError('field')

        self._field = field
        self._state = defaultdict(lambda: CellState.UNKNOWN)
        self._cell_handlers = []

    @staticmethod
    def fromstr(string, field, handler=None):
        """Создание состояния из его текстового представления и поля"""
        state = GameState(field)
        if handler is not None:
            state.add_cell_handler(handler)

        for cell_info in filter(None, string.split(';')):
            (cell, st) = cell_info.split(':')
            cell = tuple(map(int, cell.split(',')))

            if not field.check_coords(cell):
                raise ValueError('string')

            state._change_cell(cell, CellState(int(st)))

        return state

    def _change_cell(self, cell, value):
        if self._state[cell] == value:
            return False

        self._state[cell] = value

        for handler in self._cell_handlers:
            handler(cell, value)

        return True

    def add_cell_handler(self, handler):
        """Добавление обработчика изменения состояния клетки.

        Обработчику передаётся tuple из координат клетки и новое состояние
        """
        if not callable(handler):
            raise TypeError('handler')

        self._cell_handlers.append(handler)

    def remove_cell_handler(self, handler):
        """Удаление обработчика изменения состояния клетки"""
        self._cell_handlers.remove(handler)

    def set_flag(self, cell):
        """Установка флага в клетке. Возвращается True в случае успеха"""
        cell = utils.to_int(cell)
        if not self._field.check_coords(cell):
            return False

        if self._state.get(cell) != CellState.OPENED:
            return self._change_cell(cell, CellState.FLAG)

    def unset_flag(self, cell):
        """Удаление флага из клетки. Возвращается True в случае успеха"""
        cell = utils.to_int(cell)
        if not self._field.check_coords(cell):
            return False

        if self._state.get(cell) == CellState.FLAG:
            return self._change_cell(cell, CellState.UNKNOWN)

    def flags(self):
        """Количество установленных флагов"""
        return sum(1 for v in self._state.values() if v == CellState.FLAG)

    def neighbor_flags(self, cell):
        """Количество флагов в соседних клетках"""
        return sum(1 for c in self._field.neighbor_cells(cell)
                   if self._state[c] == CellState.FLAG)

    def unmarked_cells(self):
        """Количество неразмеченных клеток"""
        return (functools.reduce(operator.mul, self._field.size(), 1) -
                sum(1 for v in self._state.values() if v != CellState.UNKNOWN))

    def get_state(self, cell):
        """Состояние клетки поля"""
        return self._state[cell]

    def open_cell(self, cell):
        """Открытие клетки. Возвращается True в случае непопадания на бомбу"""
        cell = utils.to_int(cell)
        if not self._field.check_coords(cell):
            return True

        if self._state.get(cell) == CellState.FLAG:
            return True

        if self._field.check_bomb(cell):
            return False

        queue = [cell]
        visited = set(queue)
        while queue:
            _cell = queue.pop(0)
            bombs = self._field.neighbor_bombs(_cell)
            self._change_cell(_cell, CellState.OPENED)

            if bombs:
                continue

            for cell in self._field.neighbor_cells(_cell):
                if cell in visited:
                    continue

                if self._state[cell] == CellState.UNKNOWN:
                    queue.append(cell)
                    visited.add(cell)

        return True

    def check_win(self):
        """Возвращает True, если игра успешно завершена"""
        return (self.flags() == self._field.bombs() and
                not self.unmarked_cells())

    def __copy__(self):
        """Создает копию текущего состояния"""
        result = GameState.fromstr(str(self), self._field)
        result._cell_handlers = self._cell_handlers[:]
        return result

    def __eq__(self, other):
        """Проверка равенства состояний"""
        if not isinstance(other, GameState):
            return False

        if self._field != other._field:
            return False

        for (lhs, rhs) in ((self, other), (other, self)):
            for (cell, state) in lhs._state.items():
                if state != CellState.UNKNOWN and rhs._state[cell] != state:
                    return False

        return True

    def __str__(self):
        """Текстовое представление игрового состояния поля"""
        return ';'.join(map(
            lambda item: ':'.join((','.join(map(str, item[0])),
                                   str(item[1].value))),
            self._state.items()))
