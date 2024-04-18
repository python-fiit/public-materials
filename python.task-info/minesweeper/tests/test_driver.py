from contextlib import contextmanager
import os
import logging
import stat
import sys
import time
import tempfile
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
from minesweeper.game import Field, CellState
from minesweeper.driver import Minesweeper, Scoreboard, EventTypes
from minesweeper import driver


class ScoreboardTest(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            self.fn = f.name
            f.write(b'{}')

        self.lh = logging.NullHandler()
        logging.getLogger(driver.LOGGER_NAME).addHandler(self.lh)

    def test_create_file(self):
        with tempfile.NamedTemporaryFile() as f:
            name = f.name

        self.assertFalse(os.path.exists(name))
        _ = Scoreboard(name)
        self.assertTrue(os.path.exists(name))
        os.remove(name)

    @unittest.skipIf(sys.platform.startswith('win'), 'Windows not supported')
    def test_load_unreadable(self):
        old_mode = stat.S_IMODE(os.stat(self.fn).st_mode)
        try:
            os.chmod(self.fn, 0)
            with self.assertRaises(PermissionError):
                Scoreboard(self.fn)
        finally:
            os.chmod(self.fn, old_mode)

    def test_load_bad(self):
        with open(self.fn, 'w') as f:
            f.write("[]")

        self.assertFalse(list(Scoreboard(self.fn).get_params()))

    def test_load(self):
        with open(self.fn, 'w') as f:
            f.write("""{
    "8:8:10" : [
        ["gamer1", 8000],
        ["gamer2", 12000]
    ],

    "8" : [ ["name", 123] ],
    "8:8" : [ ["name", 123] ],
    "8:8:8:8:8" : [ ["name", 123] ],

    "x:8:10" : [ ["name", 123] ],
    "0:8:10" : [ ["name", 123] ],
    "-1:8:10" : [ ["name", 123] ],

    "8:x:10" : [ ["name", 123] ],
    "8:0:10" : [ ["name", 123] ],
    "8:-1:10" : [ ["name", 123] ],

    "8:8:x" : [ ["name", 123] ],
    "8:8:0" : [ ["name", 123] ],
    "8:8:-1" : [ ["name", 123] ],

    "8:8:11" : "wrong",
    "8:8:12" : 12345,
    "10:10:10" : [
        "wrong",
        12345,
        ["user", 100],
        ["wrong1", -100],
        ["wrong2", 0],
        ["wrong3", 200, 200],
        ["gamer", 4500.1],
        [500, 200],
        ["wrong", "value"]
    ],

    "8:8:16" : []
}""")

        scoreboard = Scoreboard(self.fn)
        self.assertSetEqual({((8, 8), 10), ((8, 8), 16), ((10, 10), 10),
                             ((8, 8, 8, 8), 8)},
                            set(scoreboard.get_params()))
        self.assertSetEqual(set(), set(scoreboard.get_scores((8, 8), 16)))
        self.assertSetEqual({("gamer1", 8000), ("gamer2", 12000)},
                            set(scoreboard.get_scores((8, 8), 10)))
        self.assertSetEqual({("user", 100), ("gamer", 4500)},
                            set(scoreboard.get_scores((10, 10), 10)))

    def test_add_score_bad(self):
        scoreboard = Scoreboard(self.fn)

        with self.assertRaises(TypeError):
            scoreboard.add_score([], "player", 100)

        with self.assertRaises(ValueError):
            scoreboard.add_score(Field((6, 6), ()), "player", 0)

        with self.assertRaises(ValueError):
            scoreboard.add_score(Field((6, 6), ()), "player", -100)

    def test_add_score(self):
        scoreboard = Scoreboard(self.fn)

        params = ((8, 8), 10)
        self.assertListEqual([], scoreboard.get_scores(*params))

        scoreboard.add_score(Field.generate(*params), "u1", 1500)
        scoreboard.add_score(Field.generate(*params), "u2", 400)
        scoreboard.add_score(Field.generate(*params), "u3", 5000)
        self.assertListEqual([("u2", 400.0), ("u1", 1500.0), ("u3", 5000.0)],
                             scoreboard.get_scores(*params))

        _ = Scoreboard(self.fn)
        self.assertEqual(3, len(scoreboard.get_scores(*params)))

    def tearDown(self):
        logging.getLogger(driver.LOGGER_NAME).removeHandler(self.lh)
        os.remove(self.fn)


@contextmanager
def patch_field_generator(field):
    prev_gen = Field.generate
    Field.generate = lambda *args: field
    yield
    Field.generate = prev_gen


class MinesweeperTest(unittest.TestCase):
    def setUp(self):
        self.lh = logging.NullHandler()
        logging.getLogger(driver.LOGGER_NAME).addHandler(self.lh)
        self.game = Minesweeper()

    def test_new_game(self):
        self.assertIsNone(self.game.size())
        self.assertIsNone(self.game.bombs())
        self.assertIsNone(self.game.flags())
        self.assertFalse(self.game.is_win())
        self.assertFalse(self.game.is_lose())
        self.assertTrue(self.game.saved())
        self.assertEqual(0, self.game.get_time())

        self.game.new_game((5, 6), 8)
        self.assertEqual((5, 6), self.game.size())
        self.assertEqual(8, self.game.bombs())
        self.assertEqual(0, self.game.flags())
        self.assertFalse(self.game.is_win())
        self.assertFalse(self.game.is_lose())
        self.assertTrue(self.game.saved())
        self.assertEqual(0, self.game.get_time())

    def test_handlers(self):
        counter = {event_type: 0 for event_type in EventTypes}

        def handle(event):
            counter[event] += 1

        handlers = {}
        for evt_type in EventTypes:
            handlers[evt_type] = (lambda e=evt_type: lambda *args: handle(e))()
            self.game.add_event_handler(evt_type, handlers[evt_type])

        def remove_handler(event):
            self.game.remove_event_handler(event, handlers[event])

        with patch_field_generator(Field((2, 1), {(0, 0)})):
            self.game.new_game((2, 1), 1)

        with self.subTest('changed handler'):
            self.assertEqual(0, counter[EventTypes.CELL_CHANGED])
            self.game.invert_flag((0, 0))
            self.assertEqual(1, counter[EventTypes.CELL_CHANGED])
            remove_handler(EventTypes.CELL_CHANGED)
            self.game.invert_flag((0, 0))
            self.assertEqual(1, counter[EventTypes.CELL_CHANGED])

        with self.subTest('win handler'):
            self.game.again()
            self.assertEqual(0, counter[EventTypes.PLAYER_WIN])
            self.game.open_cell((1, 0))
            self.game.invert_flag((0, 0))
            self.assertEqual(1, counter[EventTypes.PLAYER_WIN])
            self.game.again()
            remove_handler(EventTypes.PLAYER_WIN)
            self.game.open_cell((1, 0))
            self.game.invert_flag((0, 0))
            self.assertEqual(1, counter[EventTypes.PLAYER_WIN])

        with self.subTest('lose handler'):
            self.game.again()
            self.assertEqual(0, counter[EventTypes.PLAYER_LOSE])
            self.game.open_cell((0, 0))
            self.assertEqual(1, counter[EventTypes.PLAYER_LOSE])
            self.game.again()
            remove_handler(EventTypes.PLAYER_LOSE)
            self.game.open_cell((0, 0))
            self.assertEqual(1, counter[EventTypes.PLAYER_LOSE])

        with self.subTest('new_game handler'):
            counter[EventTypes.NEW_GAME] = 0
            self.game.again()
            self.assertEqual(1, counter[EventTypes.NEW_GAME])
            remove_handler(EventTypes.NEW_GAME)
            self.game.again()
            self.assertEqual(1, counter[EventTypes.NEW_GAME])

        with self.subTest('end_change handler'):
            counter[EventTypes.END_CHANGE] = 0
            self.game.again()
            self.assertEqual(1, counter[EventTypes.END_CHANGE])
            self.game.invert_flag((0, 0))
            self.assertEqual(2, counter[EventTypes.END_CHANGE])
            self.game.invert_flag((0, 0))
            self.assertEqual(3, counter[EventTypes.END_CHANGE])
            self.game.open_cell((1, 0))
            self.assertEqual(4, counter[EventTypes.END_CHANGE])
            self.game.undo()
            self.assertEqual(5, counter[EventTypes.END_CHANGE])
            self.game.redo()
            self.assertEqual(6, counter[EventTypes.END_CHANGE])
            remove_handler(EventTypes.END_CHANGE)
            self.game.undo()
            self.assertEqual(6, counter[EventTypes.END_CHANGE])

    def test_handler_decorator(self):
        callargs = []

        @self.game.event_handler(EventTypes.NEW_GAME)
        def handler(*args):
            callargs.append(args)

        self.game.new_game((5, 5), 10)
        self.assertListEqual([((5, 5), 10)], callargs)

    def test_open_cell(self):
        callargs = []
        self.game.add_event_handler(EventTypes.CELL_CHANGED,
                                    lambda *args: callargs.append(args))

        self.game.open_cell((0, 0))
        self.assertListEqual([], callargs)

        with patch_field_generator(Field((4, 3), {(0, 0), (2, 0)})):
            self.game.new_game((4, 3), 2)

        self.game.open_cell((3, 2))
        self.assertEqual(8, len(callargs))
        self.assertSetEqual(
            {e[0] for e in callargs if e[1] == CellState.OPENED},
            {(x, y) for x in (0, 1, 2, 3) for y in (1, 2)})

        self.game.again()
        callargs = []
        self.game.open_cell(('3', '2'))
        self.assertEqual(8, len(callargs))

        self.assertFalse(self.game.is_win())
        self.game.open_cell((3, 2))
        self.assertEqual(8, len(callargs))

    def test_autocomplete(self):
        callargs = []
        self.game.add_event_handler(EventTypes.CELL_CHANGED,
                                    lambda *args: callargs.append(args))

        with patch_field_generator(Field((3, 3), {(0, 0), (2, 0)})):
            self.game.new_game((3, 3), 2)

        self.game.open_cell((1, 2))
        self.game.open_cell((1, 0))
        self.assertFalse(self.game.is_win())

        self.game.again()
        self.game.open_cell((1, 2))
        self.game.open_cell((1, 0), True)
        self.assertTrue(self.game.is_win())
        self.assertSetEqual({(0, 0), (2, 0)},
                            {e[0] for e in callargs if e[1] == CellState.FLAG})

        self.game.again()
        self.game.invert_flag((1, 0))
        self.game.open_cell((1, 2), True)
        self.assertFalse(self.game.is_win())

    def test_neighbors(self):
        self.assertIsNone(self.game.get_neighbors((0, 0)))

        with patch_field_generator(Field((3, 3), {(0, 0), (2, 0)})):
            self.game.new_game((3, 3), 2)

        self.game.open_cell((2, 2))
        self.assertListEqual(
            [1, 2, 1], [self.game.get_neighbors((x, 1)) for x in (0, 1, 2)])
        self.assertListEqual(
            [1, 2, 1], [self.game.get_neighbors((x, '1')) for x in (0, 1, 2)])
        self.assertListEqual(
            [0, 0, 0], [self.game.get_neighbors((x, 2)) for x in (0, 1, 2)])

    def test_state(self):
        self.assertIsNone(self.game.get_state())

        with patch_field_generator(Field((2, 2), {(0, 0)})):
            self.game.new_game((2, 2), 1)

        callargs = []
        self.game.add_event_handler(EventTypes.CELL_CHANGED,
                                    lambda *args: callargs.append(args))

        self.game.open_cell((1, 1))
        state = self.game.get_state()
        self.assertEqual(CellState.OPENED, state.get_state((1, 1)))

        self.assertEqual(1, len(callargs))
        state.open_cell((1, 0))
        self.assertEqual(1, len(callargs))
        state.set_flag((0, 0))
        self.assertEqual(0, self.game.flags())

    def test_time(self):
        with self.subTest('flags'):
            self.game.new_game((3, 3), 2)

            self.assertEqual(0, self.game.get_time())
            time.sleep(0.1)
            self.assertEqual(0, self.game.get_time())

            self.game.invert_flag((0, 0))
            time.sleep(0.1)
            self.assertGreaterEqual(self.game.get_time(), 10)

        with self.subTest('open'):
            with patch_field_generator(Field((3, 3), {(0, 0), (2, 0)})):
                self.game.new_game((3, 3), 2)

            self.assertEqual(0, self.game.get_time())
            self.game.open_cell((2, 2))
            time.sleep(0.2)
            self.assertGreaterEqual(self.game.get_time(), 20)

        with self.subTest('load'):
            self.game.again()
            self.game.open_cell((2, 2))
            time.sleep(0.15)

            try:
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    name = f.name

                self.game.save_game(name)

                self.game.new_game((10, 10), 10)
                self.game.load_game(name)

                self.assertGreaterEqual(self.game.get_time(), 15)
                time.sleep(0.1)
                self.assertGreaterEqual(self.game.get_time(), 25)
            finally:
                if os.path.exists(name):
                    os.remove(name)

    def test_flags(self):
        callargs = []
        self.game.add_event_handler(EventTypes.CELL_CHANGED,
                                    lambda *args: callargs.append(args))

        self.game.invert_flag((0, 0))
        self.assertListEqual([], callargs)

        with patch_field_generator(Field((4, 3), {(0, 0), (2, 0)})):
            self.game.new_game((4, 3), 2)

        self.game.invert_flag((0, 2))
        self.assertListEqual([((0, 2), CellState.FLAG)], callargs)
        self.game.open_cell((3, 2))
        self.assertEqual(8, len(callargs))

        self.game.invert_flag(('0', '2'))
        self.assertEqual(((0, 2), CellState.UNKNOWN), callargs[-1])

        self.game.invert_flag((0, 0))
        self.assertFalse(self.game.is_lose())
        self.game.open_cell((0, 0))
        self.assertFalse(self.game.is_lose())

    def test_new_game_handler(self):
        callargs = []
        self.game.add_event_handler(EventTypes.NEW_GAME,
                                    lambda *args: callargs.append(args))

        self.game.new_game((4, 3), 2)
        self.assertEqual(((4, 3), 2), callargs[0])

        self.game.new_game((8, 8), 10)
        self.assertEqual(((8, 8), 10), callargs[1])

        self.game.again()
        self.assertEqual(((8, 8), 10), callargs[2])

        self.game.new_game((5, 4), 7)
        self.assertEqual(((5, 4), 7), callargs[3])

        self.game.again()
        self.assertEqual(((5, 4), 7), callargs[4])

        self.game.again()
        self.assertEqual(((5, 4), 7), callargs[5])

    def test_again(self):
        with patch_field_generator(Field((2, 2), {(0, 0)})):
            self.game.new_game((2, 2), 1)

        self.game.invert_flag((0, 0))
        self.assertEqual(1, self.game.flags())
        self.game.again()
        self.assertEqual(0, self.game.flags())

        for coords in ((0, 1), (1, 0), (1, 1)):
            self.game.open_cell(coords)
        self.assertFalse(self.game.is_win())
        self.game.invert_flag((0, 0))
        self.assertTrue(self.game.is_win())
        self.game.again()
        self.assertFalse(self.game.is_win())

        self.assertFalse(self.game.is_lose())
        self.game.open_cell((0, 0))
        self.assertTrue(self.game.is_lose())
        self.game.again()
        self.assertFalse(self.game.is_lose())

    def test_win(self):
        field = Field((3, 3), {(0, 0), (2, 0)})
        with patch_field_generator(field):
            self.game.new_game((3, 3), 2)

        callargs = []
        self.game.add_event_handler(EventTypes.PLAYER_WIN,
                                    lambda *args: callargs.append(args))

        self.game.open_cell((1, 2))
        self.assertFalse(self.game.is_win())
        self.assertListEqual([], callargs)

        self.game.open_cell((1, 0))
        self.assertFalse(self.game.is_win())
        self.assertListEqual([], callargs)

        self.game.invert_flag((0, 0))
        self.game.invert_flag((2, 0))
        self.assertTrue(self.game.is_win())
        self.assertTrue(self.game.saved())
        self.assertListEqual([(field,)], callargs)

    def test_lose(self):
        field = Field((3, 3), {(0, 0), (2, 0)})
        with patch_field_generator(field):
            self.game.new_game((3, 3), 2)

        callargs = []
        self.game.add_event_handler(EventTypes.PLAYER_LOSE,
                                    lambda *args: callargs.append(args))

        self.game.open_cell((1, 2))
        self.assertFalse(self.game.is_lose())
        self.assertListEqual([], callargs)

        self.game.open_cell((0, 0))
        self.assertTrue(self.game.is_lose())
        self.assertTrue(self.game.saved())
        self.assertListEqual([(field, (0, 0))], callargs)

    def test_undo_redo(self):
        with patch_field_generator(Field((4, 3), {(0, 0), (3, 1)})):
            self.game.new_game((4, 3), 2)

        callargs = []
        self.game.add_event_handler(EventTypes.CELL_CHANGED,
                                    lambda *args: callargs.append(args))

        self.assertFalse(self.game.can_undo())
        self.assertFalse(self.game.can_redo())

        self.game.undo()
        self.game.redo()
        self.assertListEqual([], callargs)

        with self.subTest('flags'):
            self.game.invert_flag((0, 0))
            self.assertTrue(self.game.can_undo())
            self.assertEqual(1, self.game.flags())

            self.game.undo()
            self.assertFalse(self.game.can_undo())
            self.assertTrue(self.game.can_redo())
            self.assertEqual(0, self.game.flags())

            self.game.invert_flag((0, 0))
            self.assertFalse(self.game.can_redo())
            self.assertEqual(1, self.game.flags())

            self.game.undo()
            self.assertEqual(0, self.game.flags())
            self.game.redo()
            self.assertEqual(1, self.game.flags())

            self.assertEqual(5, len(callargs))

        with self.subTest('again'):
            self.assertTrue(self.game.can_undo() or self.game.can_redo())
            self.game.again()
            self.assertFalse(self.game.can_undo() or self.game.can_redo())

        with self.subTest('wrong_flags'):
            self.game.open_cell((2, 2))
            self.game.invert_flag((2, 2))
            self.game.undo()
            self.assertFalse(self.game.can_undo())

        with self.subTest('open'):
            self.game.again()
            callargs = []
            self.game.open_cell((2, 0))
            self.game.open_cell((0, 2))
            self.game.open_cell((1, 0))
            self.assertTrue(self.game.can_undo())
            self.game.undo()
            self.assertEqual(CellState.UNKNOWN, callargs[-1][1])
            self.assertEqual(CellState.OPENED, callargs[-2][1])

            self.assertTrue(self.game.can_undo())
            self.game.undo()
            self.assertListEqual([CellState.UNKNOWN]*6,
                                 [x[1] for x in callargs[-6:]])

            self.game.redo()
            self.assertListEqual([CellState.OPENED]*6,
                                 [x[1] for x in callargs[-6:]])

            self.assertTrue(self.game.can_redo())
            self.game.open_cell((1, 2))

        with patch_field_generator(Field((2, 1), {(0, 0)})):
            self.game.new_game((2, 1), 1)

        with self.subTest('lose'):
            self.game.open_cell((1, 0))
            self.assertFalse(self.game.is_lose())
            self.game.open_cell((0, 0))
            self.assertTrue(self.game.is_lose())
            self.assertFalse(self.game.can_undo() or self.game.can_redo())

        with self.subTest('win'):
            self.game.again()
            self.game.open_cell((1, 0))
            self.assertFalse(self.game.is_win())
            self.game.invert_flag((0, 0))
            self.assertTrue(self.game.is_win())
            self.assertFalse(self.game.can_undo() or self.game.can_redo())

    @unittest.skipIf(sys.platform.startswith('win'), 'Windows not supported')
    def test_load_bad(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            name = f.name
            f.write(b'BAD DATA')

        old_mode = stat.S_IMODE(os.stat(name).st_mode)

        try:
            with self.assertRaises(driver.LoadError):
                self.game.load_game(name)

            self.game.new_game((4, 4), 3)
            self.game.save_game(name)
            self.assertTrue(os.path.exists(name))
            os.chmod(name, 0)
            with self.assertRaises(driver.LoadError):
                self.game.load_game(name)

            self.game.new_game((4, 4), 3)
            self.game.invert_flag((0, 0))

            os.remove(name)
            self.assertFalse(os.path.exists(name))
            with self.assertRaises(driver.LoadError):
                self.game.load_game(name)

            self.assertTrue(1, self.game.flags())
        finally:
            if os.path.exists(name):
                os.chmod(name, old_mode)
                os.remove(name)

    def test_save_bad(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            name = f.name

        old_mode = stat.S_IMODE(os.stat(name).st_mode)

        try:
            with self.assertRaises(driver.SaveError):
                self.game.save_game(name)

            self.game.new_game((4, 4), 3)
            os.chmod(name, 0)
            with self.assertRaises(driver.SaveError):
                self.game.save_game(name)
        finally:
            if os.path.exists(name):
                os.chmod(name, old_mode)
                os.remove(name)

    def test_save_load(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            name = f.name

        try:
            with patch_field_generator(Field((4, 3), {(0, 0), (3, 1)})):
                self.game.new_game((4, 3), 2)

            self.game.open_cell((0, 2))
            self.game.invert_flag((0, 0))
            self.game.invert_flag((1, 0))
            time.sleep(0.3)
            self.game.undo()
            self.assertFalse(self.game.saved())
            self.game.save_game(name)
            self.assertTrue(self.game.saved())
            self.game.new_game((5, 5), 10)

            callargs = []
            for evt_type in (EventTypes.NEW_GAME, EventTypes.CELL_CHANGED):
                self.game.add_event_handler(
                    evt_type, lambda *args: callargs.append(args))

            self.game.load_game(name)
            self.assertEqual(((4, 3), 2), callargs[0])
            self.assertSetEqual(
                {(0, 0)}, {x[0] for x in callargs if x[1] == CellState.FLAG})
            self.assertSetEqual(
                {(x, y) for x in (0, 1, 2) for y in (1, 2)},
                {x[0] for x in callargs if x[1] == CellState.OPENED})
            self.assertSetEqual(
                {(1, 0), (2, 0), (3, 0), (3, 1), (3, 2)},
                {x[0] for x in callargs if x[1] == CellState.UNKNOWN})
            self.assertGreaterEqual(self.game.get_time(), 30)
            self.assertTrue(self.game.can_undo())
        finally:
            if os.path.exists(name):
                os.remove(name)

    def tearDown(self):
        logging.getLogger(driver.LOGGER_NAME).removeHandler(self.lh)


if __name__ == '__main__':
    unittest.main()
