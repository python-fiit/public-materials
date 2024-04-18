import copy
import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
from minesweeper.game import Field, CellState, GameState


class FieldTest(unittest.TestCase):
    def test_save_and_load(self):
        field = Field.generate((10, 10), 15)
        self.assertEqual(field, Field.fromstr(str(field)))

    def test_load_bad(self):
        with self.assertRaises(ValueError):
            Field.fromstr('2;2;1,x,1')

    def test_eq_operator(self):
        f1 = Field.generate((10, 10), 5)
        f2 = Field.generate((10, 10), 6)
        f3 = Field.generate((6, 6), 5)
        fx = []
        self.assertNotEqual(f1, f2)
        self.assertNotEqual(f2, f3)
        self.assertNotEqual(f3, fx)
        self.assertEqual(f1, f1)

    def test_init_field(self):
        field = Field((3, "4"), {(0, 0), (2, 3), (0, 2)})
        self.assertEqual(3, field.bombs())
        self.assertTupleEqual((3, 4), field.size())
        for cell in ((0, 0), (2, 3), (0, 2)):
            self.assertTrue(field.check_bomb(cell))

        for cell in ((1, 1), (0, 1), (2, 2)):
            self.assertFalse(field.check_bomb(cell))

    def test_init_bad(self):
        for (width, height) in (([], 1), (1, []), ([], [])):
            with self.assertRaises(TypeError):
                Field((width, height), {})

        for (width, height) in ((0, 10), (-10, 10), (10, 0), (10, -10)):
            with self.assertRaises(ValueError):
                Field((width, height), {})

        for bombs in ({(4, 2)}, {(1, 1, 1)}):
            with self.assertRaises(ValueError):
                Field((3, 3), bombs)

        with self.assertRaises(ValueError):
            Field((2, 2, 2), {(0, 0)})

    def test_generate_bad(self):
        for (width, height) in (([], 1), (1, []), ([], [])):
            with self.assertRaises(TypeError):
                Field((width, height), 2)

        for bombs in (-10, 0, 9, 10):
            with self.assertRaises(ValueError):
                Field.generate((3, 3), bombs)

    def test_generate(self):
        field = Field.generate(('5', '7'), '10')
        self.assertEqual((5, 7), field.size())
        self.assertEqual(10, field.bombs())

    def test_checkparams(self):
        self.assertFalse(Field.check_params((10, 10), 0)[0])
        self.assertFalse(Field.check_params((10, 10), 200)[0])
        self.assertFalse(Field.check_params((3, 3, 3), 100)[0])
        self.assertFalse(Field.check_params((10,), 5)[0])
        self.assertTrue(Field.check_params((10, 10), 8)[0])
        self.assertTrue(Field.check_params((3, 3, 3), 10)[0])

    def test_neighbor(self):
        field = Field((3, 3), {(0, 0), (0, 1), (1, 0), (1, 1), (2, 2)})

        with self.assertRaises(ValueError):
            field.neighbor_bombs((1, 0, 1))

        for (c, cell) in ((3, (0, 0)), (4, (1, 1)), (2, (0, 2))):
            self.assertEqual(c, field.neighbor_bombs(cell))

    def test_coords_check(self):
        field = Field((10, 7), {})

        self.assertFalse(field.check_coords((1, 0, 1)))

        for cell in ((5, 5), (0, 0), (0, 6), (9, 0), (9, 6)):
            self.assertTrue(field.check_coords(cell))

        for cell in ((-1, 4), (1, -4), (-1, -4), (10, 4), (1, 7), (10, 7)):
            self.assertFalse(field.check_coords(cell))

    def test_neighbor_cells(self):
        field = Field((4, 4), {})

        with self.assertRaises(ValueError):
            set(field.neighbor_cells((1, 0, 1)))

        for (cell, ans) in (((0, 0), {(0, 1), (1, 0), (1, 1)}),
                            ((0, 1), {(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)}),
                            ((1, 1), {(0, 0), (0, 1), (0, 2), (1, 0), (1, 2),
                                      (2, 0), (2, 1), (2, 2)})):
            self.assertSetEqual(ans, set(field.neighbor_cells(cell)))


class GameStateTest(unittest.TestCase):
    def test_save_and_load(self):
        field = Field((4, 4), {(0, 2), (3, 1), (1, 1), (2, 3), (0, 1), (1, 0)})
        state = GameState(field)
        state.open_cell((0, 0))
        for cell in ((1, 0), (0, 1), (1, 1)):
            state.set_flag(cell)
        self.assertEqual(state, GameState.fromstr(str(state), field))

    def test_str(self):
        field = Field((4, 4), {(0, 0), (3, 3)})
        state = GameState(field)
        self.assertEqual(state, GameState.fromstr(str(state), field))

    def test_load_bad(self):
        with self.assertRaises(ValueError):
            GameState.fromstr('1,1,0:2;0,0:1', Field((3, 3), {}))

    def test_eq_operator(self):
        field = Field((3, 3), {(0, 1), (1, 0), (1, 1)})
        state0 = GameState(field)
        state1 = GameState(field)
        self.assertEqual(state0, state1)

        state0.set_flag((1, 1))
        self.assertNotEqual(state0, state1)
        state0.unset_flag((1, 1))
        self.assertEqual(state0, state1)

        state2 = GameState(field)
        state2.open_cell((0, 0))
        self.assertNotEqual(state1, state2)

        state3 = GameState(field)
        state3.open_cell((2, 2))
        self.assertNotEqual(state1, state3)

        self.assertNotEqual(state0, [])
        self.assertNotEqual(GameState(Field.generate((2, 2), 1)),
                            GameState(Field.generate((2, 2), 2)))

    def test_clone(self):
        calls = 0

        def handler(*args):
            nonlocal calls
            calls += 1

        state = GameState(Field.generate((10, 15), 21))
        state.add_cell_handler(handler)

        state2 = copy.copy(state)
        self.assertEqual(state, state2)
        state2.set_flag((0, 0))
        self.assertNotEqual(state, state2)
        self.assertEqual(1, calls)
        state2.remove_cell_handler(handler)
        state2.set_flag((1, 0))
        self.assertEqual(1, calls)
        state.set_flag((5, 0))
        self.assertEqual(2, calls)

    def test_init_state(self):
        field = Field((2, 2), {(0, 0), (1, 1)})
        state = GameState(field)
        self.assertEqual(0, state.flags())
        self.assertEqual(4, state.unmarked_cells())
        for cell in ((0, 0), (1, 0), (0, 1), (1, 1)):
            self.assertEqual(CellState.UNKNOWN, state.get_state(cell))
        self.assertFalse(state.check_win())

    def test_init_bad(self):
        with self.assertRaises(TypeError):
            GameState([])

    def test_flags(self):
        def check_state(state, flags, unmarked, cells=()):
            self.assertEqual(flags, state.flags())
            self.assertEqual(unmarked, state.unmarked_cells())
            for cell in cells:
                self.assertEqual(cell[1], state.get_state(cell[0]))

        state = GameState(Field((5, 4), {(1, 0), (1, 2), (3, 2)}))
        check_state(state, 0, 20, [((2, 2), CellState.UNKNOWN)])

        self.assertFalse(state.unset_flag((2, 2)))
        check_state(state, 0, 20, [((2, 2), CellState.UNKNOWN)])

        self.assertTrue(state.set_flag((2, 2)))
        check_state(state, 1, 19, [((2, 2), CellState.FLAG)])
        self.assertFalse(state.set_flag((2, 2)))
        check_state(state, 1, 19, [((2, 2), CellState.FLAG)])

        self.assertTrue(state.unset_flag((2, 2)))
        check_state(state, 0, 20, [((2, 2), CellState.UNKNOWN)])

        self.assertFalse(state.set_flag((10, 10)))
        check_state(state, 0, 20)

        self.assertFalse(state.unset_flag((10, 10)))
        check_state(state, 0, 20)

        state.open_cell((4, 0))
        check_state(state, 0, 14)
        self.assertFalse(state.set_flag((4, 1)))
        check_state(state, 0, 14)

    def test_neighbor_flags(self):
        state = GameState(Field((4, 4), {(0, 0)}))
        for cell in ((0, 0), (2, 0), (1, 2)):
            state.set_flag(cell)

        for (cell, ans) in (((0, 0), 0), ((1, 1), 3), ((1, 0), 2)):
            self.assertEqual(ans, state.neighbor_flags(cell))

    def test_handler_bad(self):
        state = GameState(Field.generate((2, 2), 1))
        with self.assertRaises(TypeError):
            state.add_cell_handler([])

    def test_handler_flag(self):
        state = GameState(Field.generate((5, 5), 8))
        callargs = []
        state.add_cell_handler(lambda *args: callargs.append(args))

        state.set_flag((2, 4))
        self.assertEqual(1, len(callargs))
        self.assertEqual(((2, 4), CellState.FLAG), callargs[-1])

        state.set_flag((2, 4))
        self.assertEqual(1, len(callargs))

        state.unset_flag((2, 4))
        self.assertEqual(2, len(callargs))
        self.assertEqual(((2, 4), CellState.UNKNOWN), callargs[-1])

    def test_handler_open(self):
        state = GameState(Field((3, 3), {(1, 0)}))
        callargs = []
        state.add_cell_handler(lambda *args: callargs.append(args))

        state.open_cell((0, 0))
        self.assertEqual(1, len(callargs))
        self.assertEqual(((0, 0), CellState.OPENED), callargs[-1])

        state.open_cell((2, 2))
        self.assertEqual(7, len(callargs))
        self.assertSetEqual(
            {((x, y), CellState.OPENED) for x in (0, 1, 2) for y in (1, 2)},
            set(callargs[1:]))

    def test_handler_load(self):
        field = Field((3, 3), {(1, 0)})
        state = GameState(field)
        state.set_flag((0, 0))
        state.open_cell((2, 2))

        callargs = []
        loaded = GameState.fromstr(str(state), field,
                                   lambda *args: callargs.append(args))

        self.assertEqual(7, len(callargs))
        self.assertSetEqual(
            {((x, y), CellState.OPENED) for x in (0, 1, 2) for y in (1, 2)} |
            {((0, 0), CellState.FLAG)},
            set(callargs))

    def test_handler_remove(self):
        state = GameState(Field.generate((2, 2), 2))

        callargs = []
        handler = lambda *args: callargs.append(args)

        state.add_cell_handler(handler)
        state.set_flag((0, 0))
        self.assertEqual(1, len(callargs))

        state.remove_cell_handler(handler)
        state.set_flag((1, 1))
        self.assertEqual(1, len(callargs))

    def test_open_cell(self):
        field = Field((4, 3), {(0, 0), (2, 0)})

        state1 = GameState(field)

        self.assertTrue(state1.open_cell((10, 10)))
        self.assertEqual(GameState(field), state1)

        self.assertTrue(state1.open_cell((3, 2)))
        self.assertEqual(4, state1.unmarked_cells())
        self.assertSetEqual(
            {state1.get_state((x, y)) for x in (0, 1, 2, 3) for y in (1, 2)},
            {CellState.OPENED})

        self.assertFalse(state1.open_cell((0, 0)))
        self.assertEqual(4, state1.unmarked_cells())

        state2 = GameState(field)
        state2.set_flag((2, 2))
        self.assertTrue(state2.open_cell((3, 2)))
        self.assertEqual(8, state2.unmarked_cells())
        self.assertSetEqual(
            {state2.get_state((x, y)) for x in (2, 3) for y in (1, 2)},
            {CellState.OPENED, CellState.FLAG})

        self.assertTrue(state2.open_cell((2, 2)))
        self.assertEqual(8, state2.unmarked_cells())

    def test_win(self):
        state = GameState(Field((4, 3), {(0, 0), (2, 0)}))
        self.assertFalse(state.check_win())

        state.set_flag((0, 0))
        state.set_flag((2, 0))
        self.assertFalse(state.check_win())
        state.unset_flag((0, 0))
        state.unset_flag((2, 0))

        state.open_cell((2, 2))
        self.assertFalse(state.check_win())

        state.set_flag((0, 0))
        state.open_cell((1, 0))
        state.open_cell((3, 0))
        self.assertFalse(state.check_win())

        state.set_flag((2, 0))
        self.assertTrue(state.check_win())


if __name__ == '__main__':
    unittest.main()
