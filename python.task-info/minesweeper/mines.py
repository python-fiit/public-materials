#!/usr/bin/env python3
"""Графическая версия игры «Сапёр»"""

ERROR_EXCEPTION = 1
ERROR_WRONG_SETTINGS = 2
ERROR_PYTHON_VERSION = 3
ERROR_MODULES_MISSING = 4
ERROR_QT_VERSION = 5

import sys

if sys.version_info < (3, 4):
    print('Use python >= 3.4', file=sys.stderr)
    sys.exit(ERROR_PYTHON_VERSION)

import argparse
from contextlib import contextmanager
import itertools
import logging

try:
    from minesweeper import driver, game, settings, utils
except Exception as e:
    print('Game modules not found: "{}"'.format(e), file=sys.stderr)
    sys.exit(ERROR_MODULES_MISSING)

try:
    from PyQt5 import QtGui, QtCore, QtWidgets, QtWebKitWidgets
except Exception as e:
    print('PyQt5 not found: "{}". Use console version (cmines)'.format(e),
          file=sys.stderr)
    sys.exit(ERROR_QT_VERSION)


__version__ = '1.0'
__author__ = 'Samun Victor'
__email__ = 'victor.samun@gmail.com'

LOGGER_NAME = 'mines'
LOGGER = logging.getLogger(LOGGER_NAME)


def time_to_str(time):
    """Текстовое представление времени"""
    return '{:.2f}'.format(time / 100)


def is_active(game_driver):
    """Возвращает True если игра не находится в конечном состоянии"""
    return not (game_driver.is_win() or game_driver.is_lose())


@contextmanager
def temp_painter(device):
    painter = QtGui.QPainter()
    painter.begin(device)
    yield painter
    painter.end()


class GuiField(QtWidgets.QFrame):
    """Компонент «игровое поле»"""
    def __init__(self, window, config, game_driver, parent=None):
        super().__init__(parent)
        self._window = window
        self._config = config
        self._driver = game_driver
        self._parent = parent

        (self.cx, self.cy) = self._config.picture_size

        self._init_driver()
        self._load_pictures()

    def _init_driver(self):
        @self._driver.event_handler(driver.EventTypes.NEW_GAME)
        def new_handler(size, bombs):
            dx = self._window.width() - self._parent.width()
            dy = self._window.height() - self._parent.height()

            app = QtCore.QCoreApplication.instance()
            geom = app.desktop().availableGeometry()
            (max_w, max_h) = (geom.width(), geom.height())
            max_h -= app.style().pixelMetric(
                QtWidgets.QStyle.PM_TitleBarHeight)

            self.resize(self.cx*size[0], self.cy*size[1])
            self._window.setMaximumSize(
                min(max_w, dx + self.width()),
                min(max_h, dy + self.height()))
            self._window.setFixedSize(self._window.maximumSize())

            self._canvas = QtGui.QImage(self.size(), QtGui.QImage.Format_RGB32)
            for x in range(self._driver.size()[0]):
                for y in range(self._driver.size()[1]):
                    self._draw_cell((x, y), game.CellState.UNKNOWN)

            self.repaint()

        @self._driver.event_handler(driver.EventTypes.PLAYER_LOSE)
        def lose_handler(field, cell):
            state = self._driver.get_state()
            for x in range(self._driver.size()[0]):
                for y in range(self._driver.size()[1]):
                    self._draw_diff((x, y), state, field, cell)

            self.repaint()

        @self._driver.event_handler(driver.EventTypes.CELL_CHANGED)
        def cell_handler(cell, state):
            self._draw_cell(cell, state)

        @self._driver.event_handler(driver.EventTypes.END_CHANGE)
        def end_change_hander():
            self.repaint()

    def _load(self, filename):
        try:
            image = QtGui.QImage()
            if not image.load(filename):
                raise Exception('error')

            if image.size() != QtCore.QSize(self.cx, self.cy):
                LOGGER.warning('Picture "%s" has incorrect size and '
                               'will be scaled', filename)
                image = image.scaled(self.cx, self.cy)
        except Exception as e:
            LOGGER.warning('Error while loading picture "%s": "%s". Skip',
                           filename, e)
            return None
        else:
            LOGGER.info('Picture "%s" loaded', filename)
            return image

    def _picture_or_box(self, name, color):
        if name is not None:
            result = self._load(self._config.picture(name))
            if result is not None:
                return result

        result = QtGui.QImage(self.cx, self.cy, QtGui.QImage.Format_RGB32)
        with temp_painter(result) as p:
            p.setBrush(QtGui.QBrush(color))
            p.setPen(QtGui.QPen(QtCore.Qt.black))
            p.drawRect(0, 0, self.cx - 1, self.cy - 1)

        return result

    def _load_pictures(self):
        self._pic_numbers = []

        for i in range(9):
            pic = self._load(self._config.picture('pic{}'.format(i)))
            if pic is None:
                pic = self._picture_or_box(None, QtCore.Qt.lightGray)
                with temp_painter(pic) as p:
                    p.drawText(0, 0, self.cx, self.cy,
                               QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter,
                               str(i or ' '))
            self._pic_numbers.append(pic)

        self._pic_base = self._picture_or_box('base', QtCore.Qt.white)
        self._pic_bomb = self._picture_or_box('bomb', QtCore.Qt.black)
        self._pic_flag = self._picture_or_box('flag', QtCore.Qt.red)

        self._pic_wflag = self._picture_or_box('wrong_flag', QtCore.Qt.red)
        if not self._pic_wflag:
            with temp_painter(self._pic_wflag) as p:
                p.setPen(QtGui.QPen(QtGui.QBrush(QtCore.Qt.black), 3))
                p.drawLine(0, 0, self.cx, self.cy)
                p.drawLine(0, self.cx, self.cy, 0)

        self._pic_mistake = self._picture_or_box('mistake', QtCore.Qt.red)
        if not self._pic_mistake:
            with temp_painter(self._pic_mistake) as p:
                p.setBrush(QtGui.QBrush(QtCore.Qt.black))
                p.drawEllipse(QtCore.QPoint(self.cx // 2, self.cy // 2),
                              max(0, self.cx // 2 - 3),
                              max(0, self.cy // 2 - 3))

    def _draw_cell(self, cell, state):
        with temp_painter(self._canvas) as p:
            if state == game.CellState.FLAG:
                pic = self._pic_flag
            elif state == game.CellState.UNKNOWN:
                pic = self._pic_base
            else:
                pic = self._pic_numbers[self._driver.get_neighbors(cell)]

            p.drawImage(cell[0]*self.cx, cell[1]*self.cy, pic)

    def _draw_diff(self, cell, state, field, cell_):
        with temp_painter(self._canvas) as p:
            if cell_ == cell:
                pic = self._pic_mistake
            elif field.check_bomb(cell):
                if state.get_state(cell) == game.CellState.FLAG:
                    pic = self._pic_flag
                else:
                    pic = self._pic_bomb
            elif state.get_state(cell) == game.CellState.FLAG:
                pic = self._pic_wflag
            else:
                pic = self._pic_numbers[field.neighbor_bombs(cell)]

            p.drawImage(cell[0]*self.cx, cell[1]*self.cy, pic)

    def mousePressEvent(self, event):
        if not is_active(self._driver):
            return

        cell = (event.x() // self.cx, event.y() // self.cy)
        LOGGER.info('Click at %s:%s', event.x(), event.y())

        if event.button() & QtCore.Qt.MiddleButton:
            state = self._driver.get_state()
            if state.get_state(cell) != game.CellState.OPENED:
                return

            if self._driver.get_neighbors(cell) != state.neighbor_flags(cell):
                return

            for delta in itertools.product((-1, 0, 1), repeat=2):
                if any(delta) and is_active(self._driver):
                    self._driver.open_cell(tuple(map(sum, zip(cell, delta))),
                                           self._window.autocomplete())

        elif event.button() & QtCore.Qt.LeftButton:
            self._driver.open_cell(cell, self._window.autocomplete())
        elif event.button() & QtCore.Qt.RightButton:
            self._driver.invert_flag(cell)

    def paintEvent(self, event):
        with temp_painter(self) as p:
            p.drawImage(0, 0, self._canvas)


class StartGameWindow(QtWidgets.QDialog):
    """Окно выбора параметров игры"""
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config

        self._sel_layout = QtWidgets.QVBoxLayout()
        for _ in config.default_games:
            self._sel_layout.addWidget(QtWidgets.QRadioButton())

        self._other = QtWidgets.QRadioButton()
        self._other.toggled.connect(self._click_other)
        self._sel_layout.addWidget(self._other)

        self._sel_layout.itemAt(0).widget().setChecked(True)

        self._selector = QtWidgets.QGroupBox()
        self._selector.setLayout(self._sel_layout)

        self._inputs = QtWidgets.QHBoxLayout()
        validator = QtGui.QIntValidator()
        validator.setBottom(0)

        for _ in range(3):
            inp = QtWidgets.QLineEdit()
            inp.setValidator(validator)
            self._inputs.addWidget(inp)

        self._hide_inputs()

        self._buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._selector)
        layout.addLayout(self._inputs)
        layout.addWidget(self._buttons)
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        self.setLayout(layout)
        self.reinit_strings()

    def _click_other(self, show):
        self._hide_inputs(not show)
        if show:
            inp = self._inputs.itemAt(0).widget()
            QtCore.QTimer.singleShot(
                0, lambda: inp.setFocus(QtCore.Qt.OtherFocusReason))

    def _hide_inputs(self, value=True):
        for idx in range(self._inputs.count()):
            self._inputs.itemAt(idx).widget().setVisible(not value)

        self.resize(self.width(), self.minimumSizeHint().height())

    def reinit_strings(self):
        """Инициализация текстовых строк с учётом локализации"""
        self.setWindowTitle(self._config.string('t_new'))
        self._selector.setTitle(self._config.string('game_params'))

        self._params = []
        for (idx, info) in enumerate(self._config.default_games):
            self._sel_layout.itemAt(idx).widget().setText(
                self._config.string('game_info').format(info[0], *info[1]))
            self._params.append(info[1])

        self._other.setText(self._config.string('game_other'))

        for (idx, name) in enumerate(('l_width', 'l_height', 'l_mines')):
            self._inputs.itemAt(idx).widget().setPlaceholderText(
                self._config.string(name))

    def params(self):
        """Выбранные параметры игры"""
        def convert(params):
            *size, bombs = params
            return (size, bombs)

        if self._other.isChecked():
            return convert([self._inputs.itemAt(i).widget().text()
                            for i in range(3)])

        for i in range(self._sel_layout.count()):
            if self._sel_layout.itemAt(i).widget().isChecked():
                return convert(list(self._params[i]))


class HiScoresWindow(QtWidgets.QDialog):
    """Окно «рекорды»"""
    _TEMPLATE = """<html>
    <head>
        <style>
            table {{
                border: 3px double black;
                width: 100%;
            }}

            td.place {{ text-align: center; }}
            td.name {{ }}
            td.score {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1 align='center'>{}</h1>
        <table>{}</table>
    </body>
</html>"""

    _ROW_TEMPLATE = """<tr>
<td class='place'>{}</td>
<td class='name'>{}</td>
<td class='score'>{}</td>
</tr>"""

    def __init__(self, config, scoreboard, parent=None):
        super().__init__(parent)
        self._scores = scoreboard
        self._config = config

        self._viewer = QtWebKitWidgets.QWebView()

        self._btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        self._btns.accepted.connect(self.close)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._viewer)
        layout.addWidget(self._btns)

        self.setLayout(layout)
        self.reinit_strings()

    def reinit_strings(self):
        """Инициализация текстовых строк с учётом локализации"""
        self.setWindowTitle(self._config.string('title'))

    @staticmethod
    def _make_row(place, name, score):
        return HiScoresWindow._ROW_TEMPLATE.format(
            place, name, time_to_str(score))

    def prepare(self, game_driver):
        """Подготовка и отображение данных"""
        scores = self._scores.get_scores(
            game_driver.size(), game_driver.bombs())

        table = ''.join(
            HiScoresWindow._make_row(place + 1, name, score)
            for (place, (name, score)) in enumerate(scores))

        self._viewer.setHtml(HiScoresWindow._TEMPLATE.format(
            self._config.string('hiscores'), table))


class MinesweeperWindow(QtWidgets.QMainWindow):
    """Главное окно приложения"""
    def __init__(self, config, scoreboard, game_driver, parent=None):
        super().__init__(parent)
        self._config = config
        self._scoreboard = scoreboard
        self._driver = game_driver

        self._init_ui()
        self._init_strings()
        self._init_driver()
        QtCore.QTimer.singleShot(0, lambda: self._start_game())

    def _init_ui(self):
        # Dialogs init

        self._new_game_dialog = StartGameWindow(self._config, self)
        self._new_game_dialog.setModal(True)
        self._new_game_dialog.accepted.connect(self._start_game)
        self._new_game_dialog.rejected.connect(self._cmd_exit)

        self._scores_wnd = HiScoresWindow(self._config, self._scoreboard, self)
        self._scores_wnd.setModal(True)

        # Main menu init

        menu = self.menuBar()

        self._new_game = QtWidgets.QAction(self)
        self._new_game.setShortcut('Ctrl+N')
        self._new_game.triggered.connect(self._cmd_new_game)

        self._again = QtWidgets.QAction(self)
        self._again.setShortcut('Ctrl+R')
        self._again.triggered.connect(self._cmd_again)

        self._open_game = QtWidgets.QAction(self)
        self._open_game.setShortcut('Ctrl+O')
        self._open_game.triggered.connect(self._cmd_open)

        self._save_game = QtWidgets.QAction(self)
        self._save_game.setShortcut('Ctrl+S')
        self._save_game.triggered.connect(self._cmd_save)

        self._exit = QtWidgets.QAction(self)
        self._exit.setShortcut('Ctrl+X')
        self._exit.triggered.connect(self._cmd_exit)

        self._m_game = menu.addMenu('')
        self._m_game.addAction(self._new_game)
        self._m_game.addAction(self._again)
        self._m_game.addAction(self._open_game)
        self._m_game.addAction(self._save_game)
        self._m_game.addSeparator()
        self._m_game.addAction(self._exit)

        self._undo = QtWidgets.QAction(self)
        self._undo.setShortcut('Ctrl+Z')
        self._undo.triggered.connect(self._cmd_undo)

        self._redo = QtWidgets.QAction(self)
        self._redo.setShortcut('Ctrl+Y')
        self._redo.triggered.connect(self._cmd_redo)

        if self._scoreboard is not None:
            self._scores = QtWidgets.QAction(self)
            self._scores.setShortcut('Alt+S')
            self._scores.triggered.connect(self._cmd_scores)

        self._autocomplete = QtWidgets.QAction(self)
        self._autocomplete.setCheckable(True)
        self._autocomplete.setShortcut('Alt+C')

        self._m_act = menu.addMenu('')
        self._m_act.addAction(self._undo)
        self._m_act.addAction(self._redo)
        self._m_act.addSeparator()
        if self._scoreboard is not None:
            self._m_act.addAction(self._scores)
        self._m_act.addAction(self._autocomplete)

        self._m_langs = menu.addMenu('')
        self._langs = QtWidgets.QActionGroup(self)
        for (name, descr) in self._config.langs.items():
            lang = QtWidgets.QAction('{} ({})'.format(name, descr), self)
            lang.setCheckable(True)
            if name == self._config.language:
                lang.setChecked(True)

            lang.triggered.connect(
                (lambda l=name: lambda *args: self._cmd_lang(l))())

            self._langs.addAction(lang)
            self._m_langs.addAction(lang)

        self._about = QtWidgets.QAction(self)
        self._about.setShortcut('Shift+F1')
        self._about.triggered.connect(self._cmd_about)

        self._m_help = menu.addMenu('')
        self._m_help.addAction(self._about)

        # Main widget init

        self._info = QtWidgets.QLabel(self)
        self._time = QtWidgets.QLabel(time_to_str(0), self)

        if self._scoreboard is not None:
            self._hiscore_label = QtWidgets.QLabel(self)
            self._hiscore = QtWidgets.QLabel(self)

        self._info.setFont(QtGui.QFont('Monospace', 28, QtGui.QFont.Bold))
        self._time.setFont(QtGui.QFont('Monospace', 18, QtGui.QFont.Bold))
        self._time.setAlignment(QtCore.Qt.AlignRight)

        if self._scoreboard is not None:
            self._hiscore_label.setFont(QtGui.QFont('System', 10))
            self._hiscore.setFont(
                QtGui.QFont('Monospace', 10, QtGui.QFont.Bold))

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        self._scroller = QtWidgets.QScrollArea(self)
        self._scroller.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self._field = GuiField(self, self._config, self._driver,
                               self._scroller)
        self._field.setFrameStyle(QtWidgets.QFrame.Box)
        self._field.setLineWidth(2)

        self._scroller.setWidget(self._field)

        scores_layout = QtWidgets.QVBoxLayout()
        scores_layout.addWidget(self._time)

        if self._scoreboard is not None:
            self._best = None
            hiscore_layout = QtWidgets.QHBoxLayout()
            hiscore_layout.addWidget(self._hiscore_label, QtCore.Qt.AlignRight)
            hiscore_layout.addWidget(self._hiscore, QtCore.Qt.AlignRight)
            scores_layout.addLayout(hiscore_layout)

        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addWidget(self._info, QtCore.Qt.AlignLeft)
        top_layout.addWidget(QtWidgets.QWidget(self), QtCore.Qt.AlignJustify)
        top_layout.addLayout(scores_layout)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self._scroller, QtCore.Qt.AlignJustify)

        window = QtWidgets.QWidget(self)
        window.setLayout(layout)
        self.setCentralWidget(window)

    def _init_strings(self):
        self.setWindowTitle(self._config.string('title'))

        self._m_game.setTitle(self._config.string('m1_game'))
        self._new_game.setText(self._config.string('m1_new'))
        self._again.setText(self._config.string('m1_again'))
        self._open_game.setText(self._config.string('m1_open'))
        self._save_game.setText(self._config.string('m1_save'))
        self._exit.setText(self._config.string('m1_exit'))

        self._m_act.setTitle(self._config.string('m2_actions'))
        self._undo.setText(self._config.string('m2_undo'))
        self._redo.setText(self._config.string('m2_redo'))
        if self._scoreboard is not None:
            self._scores.setText(self._config.string('m2_scores'))
            self._hiscore_label.setText(self._config.string('l_hiscore'))
            if self._best is None:
                self._hiscore.setText(self._config.string('na_score'))
        self._autocomplete.setText(self._config.string('m2_compl'))

        self._m_langs.setTitle(self._config.string('m3_langs'))
        self._m_help.setTitle(self._config.string('m4_help'))
        self._about.setText(self._config.string('m4_about'))

        self._new_game_dialog.reinit_strings()
        self._scores_wnd.reinit_strings()

    def _init_driver(self):
        @self._driver.event_handler(driver.EventTypes.PLAYER_WIN)
        def win_handler(field):
            if self._scoreboard is None:
                QtWidgets.QMessageBox.information(
                    self, self._config.string('title'),
                    self._config.string('win'),
                    QtWidgets.QMessageBox.Ok)
                return

            if not self._driver.get_time():
                return

            player_name = QtWidgets.QInputDialog.getText(
                self, self._config.string('win'),
                self._config.string('prompt_name'),
                text=self._config.string('anon'))
            if player_name[1]:
                self._scoreboard.add_score(field, player_name[0],
                                           self._driver.get_time())

        @self._driver.event_handler(driver.EventTypes.PLAYER_LOSE)
        def lose_handler(field, cell):
            QtWidgets.QMessageBox.information(
                self, self._config.string('title'),
                self._config.string('lose'), QtWidgets.QMessageBox.Ok)

        @self._driver.event_handler(driver.EventTypes.NEW_GAME)
        def new_handler(size, bombs):
            self._info.setText(str(self._driver.bombs()))

            if self._scoreboard is not None:
                hi_score = utils.first_or_default(
                    self._scoreboard.get_scores(
                        self._driver.size(), self._driver.bombs()))

                if hi_score is not None:
                    self._best = hi_score[1]
                    self._hiscore.setText(time_to_str(self._best))
                    self._hiscore.setToolTip(hi_score[0])
                else:
                    self._best = None
                    self._hiscore.setText(self._config.string('na_score'))
                    self._hiscore.setToolTip('')

        @self._driver.event_handler(driver.EventTypes.END_CHANGE)
        def end_handler():
            QtCore.QTimer.singleShot(
                0, lambda: self._info.setText(
                    str(self._driver.bombs() - self._driver.flags())))
            self._undo.setEnabled(self._driver.can_undo())
            self._redo.setEnabled(self._driver.can_redo())

    def _start_game(self):
        try:
            self._driver.new_game(*self._new_game_dialog.params())
        except Exception as e:
            LOGGER.error('Error while start game: %s', e)
            QtWidgets.QMessageBox.critical(
                self, self._config.string('title'),
                self._config.string('start_game_error'),
                QtWidgets.QMessageBox.Ok)

    def autocomplete(self):
        return self._autocomplete.isChecked()

    def _check_saved(self):
        if self._driver.saved():
            return True

        answer = QtWidgets.QMessageBox.question(
            self, self._config.string('title'),
            self._config.string('prompt_save'),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
            QtWidgets.QMessageBox.Cancel)

        if answer & QtWidgets.QMessageBox.Cancel:
            return False

        if answer & QtWidgets.QMessageBox.Yes:
            self._cmd_save()

        return True

    def _cmd_new_game(self):
        if self._check_saved():
            self._new_game_dialog.open()

    def _cmd_again(self):
        if self._check_saved():
            self._driver.again()

    def _cmd_open(self):
        if not self._check_saved():
            return

        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, self._config.string('t_load'), self._config.savedir)

        if filename:
            try:
                self._driver.load_game(filename)
            except driver.LoadError as e:
                LOGGER.error('Error while loading game: "%s"', e)
                QtWidgets.QMessageBox.critical(
                    self, self._config.string('title'),
                    self._config.string('load_game_error'),
                    QtWidgets.QMessageBox.Ok)

    def _cmd_save(self):
        if not is_active(self._driver):
            return

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self._config.string('t_save'), self._config.savedir)

        if filename:
            try:
                self._driver.save_game(filename)
            except driver.SaveError as e:
                LOGGER.error('Error while saving game: "%s"', e)
                QtWidgets.QMessageBox.critical(
                    self, self._config.string('title'),
                    self._config.string('save_game_error'),
                    QtWidgets.QMessageBox.Ok)

    def _cmd_undo(self):
        self._driver.undo()

    def _cmd_redo(self):
        self._driver.redo()

    def _cmd_scores(self):
        self._scores_wnd.prepare(self._driver)
        self._scores_wnd.show()

    def _cmd_exit(self):
        self._check_saved()
        QtCore.QCoreApplication.exit()

    def _cmd_about(self):
        QtWidgets.QMessageBox.information(
            self, self._config.string('title'),
            self._config.string('about').format(
                __version__, '{} <{}>'.format(__author__, __email__)),
            QtWidgets.QMessageBox.Ok)

    def _cmd_lang(self, lang):
        self._config.language = lang
        self._init_strings()

    def _tick(self):
        time = self._driver.get_time()

        color = QtCore.Qt.black
        if self._scoreboard is not None:
            if self._best is not None and self._best <= time:
                color = QtCore.Qt.red
            else:
                color = QtCore.Qt.darkGreen

        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.WindowText, color)
        self._time.setText(time_to_str(time))
        self._time.setPalette(pal)


def run(config, scoreboard, game_driver):
    """Запуск логики «Сапёра»"""
    app = QtWidgets.QApplication([])

    wnd = MinesweeperWindow(config, scoreboard, game_driver)
    center = app.desktop().availableGeometry().center()
    wnd.move(center.x() - wnd.width() // 2, center.y() - wnd.height() // 2)
    wnd.show()

    return app.exec_()


def parse_args():
    """Разбор аргуметов запуска"""
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTIONS]',
        description='Minesweeper game. GUI version {}'.format(__version__),
        epilog='Author: {} <{}>'.format(__author__, __email__))

    parser.add_argument(
        '-c', '--config', type=str,
        metavar='FILENAME', default='settings.ini', help='configuration file')
    arg_group = parser.add_mutually_exclusive_group()
    arg_group.add_argument(
        '-l', '--log', type=str,
        metavar='FILENAME', default='mines.log', help='log filename')
    arg_group.add_argument(
        '--no-log',
        action='store_true', help='no log')

    return parser.parse_args()


class NullStream:
    """Ничегонеделающий context manager"""
    def __getattr__(self, name):
        self.name = lambda *args: None
        return self.name

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def main():
    """Точка входа в приложение"""
    args = parse_args()

    if not args.no_log:
        try:
            stream = open(args.log, 'a')
        except Exception:
            stream = sys.stderr
    else:
        stream = NullStream()

    with stream:
        log = logging.StreamHandler(stream)
        log.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s <%(name)s>] %(message)s'))

        for module in (sys.modules[__name__], settings, driver):
            logger = logging.getLogger(module.LOGGER_NAME)
            logger.setLevel(logging.DEBUG if args.log else logging.ERROR)
            logger.addHandler(log)

        LOGGER.info('GUI Application started')
        try:
            config = settings.Settings(args.config)
        except Exception as e:
            print('Error while reading settings file\n{}'.format(e),
                  file=sys.stderr)
            sys.exit(ERROR_WRONG_SETTINGS)
        else:
            LOGGER.info('Settings OK')

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
            sys.exit(run(config, scoreboard, game_driver))
        except SystemExit:
            LOGGER.info('Exiting')
        except BaseException as e:
            import traceback
            LOGGER.error('Error: %s\n%s', e,
                         ''.join(traceback.format_tb(sys.exc_info()[-1])))
            print(e, file=sys.stderr)
            sys.exit(ERROR_EXCEPTION)


if __name__ == '__main__':
    main()
