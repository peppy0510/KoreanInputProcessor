# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com

requirements:

description:

reference:

'''


import ctypes
import os
import sublime
import sublime_plugin
import threading
import time


try:
    from koreaninput import KoreanInputProcessor
except ImportError:
    from .koreaninput import KoreanInputProcessor


kip = KoreanInputProcessor()


UPDATE_THREAD_CHECK_TIMEOUT = 0.1
UPDATE_THREAD_CHECK_INTERVAL = 0.002


LINE_SPLIT_CODE = 10
START_OR_END_OF_PAGE_CODE = 0


class ArrowPositionHandler:

    def __init__(self):
        self.pending_arrow_position = 0

    def __press_key(self, code):
        ctypes.windll.user32.keybd_event(code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(code, 0, 0x0002, 0)

    def press_vkey_left(self):
        self.__press_key(0x25)

    def press_vkey_right(self):
        self.__press_key(0x27)

    def press_vkey_up(self):
        self.__press_key(0x26)

    def press_vkey_down(self):
        self.__press_key(0x28)

    def press_vkey_pageup(self):
        self.__press_key(0x21)

    def press_vkey_pagedown(self):
        self.__press_key(0x22)

    def press_vkey_home(self):
        self.__press_key(0x24)

    def press_vkey_end(self):
        self.__press_key(0x23)

    def press_vkey_return(self):
        self.__press_key(0x0D)

    def press_vkey_spacebar(self):
        self.__press_key(0x20)

    def press_vkey_backspace(self):
        self.__press_key(0x08)

    def set_arrow_position(self):
        self.pending_arrow_position = 0
        if not self.updated:
            a = self.view.sel()[0].a
            b = self.view.sel()[0].b
            self.prefix = self.view.substr(a - 1)
            self.suffix = self.view.substr(b)
        self.press_vkey_backspace()


class ViewEventHandler:

    def __init__(self):
        self.events = []

    def init_event(self):
        self.events = []

    def pop_event(self):
        if self.events:
            return self.events.pop()

    def push_event(self, event):
        self.events += [event]


class UpdateThread(threading.Thread):

    def __init__(
            self, parent, commands,
            check_interval=UPDATE_THREAD_CHECK_INTERVAL,
            check_timeout=UPDATE_THREAD_CHECK_TIMEOUT):
        self.parent = parent
        self.commands = commands
        self.check_timeout = check_timeout
        self.check_interval = check_interval
        threading.Thread.__init__(self)
        self.__stop = threading.Event()
        self.start()

    def stop(self):
        self.__stop.set()

    def stopped(self):
        return self.__stop.is_set()

    def run(self):
        timeout_count = self.check_timeout / self.check_interval

        while (not self.stopped() and self.parent.activated and timeout_count > 0):
            time.sleep(self.check_interval)

            if not self.parent.pending_arrow_position:
                self.parent.view.run_command(
                    'korean_input_renderer', {'commands': self.commands})
                break

            timeout_count -= 1

        self.stop()


class KoreanInputRendererCommand(sublime_plugin.TextCommand):

    def __init__(self, view):
        sublime_plugin.TextCommand.__init__(self, view)

    def run(self, edit, commands):

        for command in commands:

            method = command['method']
            kwargs = command['kwargs']

            if method == 'cursor':
                self.view.sel().clear()
                self.view.sel().add(sublime.Region(**kwargs['region']))

            elif method == 'insert':
                self.view.insert(
                    edit, kwargs['offset'], kwargs['string'])

            elif method == 'replace':
                self.view.replace(
                    edit, sublime.Region(**kwargs['region']), kwargs['string'])

            elif method == 'erase':
                self.view.insert(
                    edit, sublime.Region(**kwargs['region']), kwargs['string'])


class LetterHandler:

    def init_letter(self):
        self.letters = []

    def pop_letter(self):
        if self.letters:
            return self.letters.pop()

    def compose_letters(self):
        self.update()

    def decompose_letters(self):
        self.pending_decompose = 1
        self.pop_letter()
        composed = kip.compose_collection(self.letters)
        string = ''.join(composed)
        if not string:
            self.init_event()
            self.init_letter()
            self.prefix = ''
            self.suffix = ''
            self.updated = False
            self.pending_decompose = 0
            self.pending_arrow_position = 0
            return

        a = self.view.sel()[0].a
        b = self.view.sel()[0].b

        UpdateThread(self, [
            {'method': 'replace', 'kwargs': {'region': {'a': a - 1, 'b': b - 1}, 'string': string}},
            {'method': 'cursor', 'kwargs': {'region': {'a': a, 'b': b}}},
        ])

    def update(self):
        if not self.letters:
            return

        prefix = self.prefix
        self.prefix = ''

        suffix = self.suffix
        self.suffix = ''

        composed = kip.compose_collection(self.letters)

        string = ''.join(composed)
        a = self.view.sel()[0].a
        b = self.view.sel()[0].b

        splitter = 0
        if len(composed) > 1:
            decomposed = kip.decompose_letter(composed[0])
            splitter = len(decomposed)
        splitted = self.letters[splitter:] != self.letters
        self.letters = self.letters[splitter:]

        prefix_is_special = prefix and ord(prefix) in (START_OR_END_OF_PAGE_CODE, LINE_SPLIT_CODE,)
        suffix_is_special = prefix and ord(suffix) in (START_OR_END_OF_PAGE_CODE, LINE_SPLIT_CODE,)
        prefix = '' if prefix_is_special else prefix
        suffix = '' if suffix_is_special else suffix

        string = prefix + string + suffix

        if not self.updated:
            if prefix_is_special and not suffix_is_special:
                UpdateThread(self, [
                    {'method': 'replace', 'kwargs': {'region': {
                        'a': a, 'b': a + len(string) - 1}, 'string': string}},
                    {'method': 'cursor', 'kwargs': {'region': {'a': b, 'b': b}}},
                ])
            elif suffix_is_special and not prefix_is_special:
                UpdateThread(self, [
                    {'method': 'replace', 'kwargs': {'region': {'a': b - len(string), 'b': b - 1}, 'string': string}},
                    {'method': 'cursor', 'kwargs': {'region': {'a': b, 'b': b}}},
                ])
            elif suffix_is_special and prefix_is_special:
                UpdateThread(self, [
                    {'method': 'insert', 'kwargs': {'offset': b - 1, 'string': string}},
                    {'method': 'cursor', 'kwargs': {'region': {'a': b, 'b': b}}},
                ])
            else:
                UpdateThread(self, [
                    {'method': 'replace', 'kwargs': {'region': {'a': a - 1, 'b': a + 1}, 'string': string}},
                    {'method': 'cursor', 'kwargs': {'region': {'a': b, 'b': b}}},
                ])
        elif not splitted:
            UpdateThread(self, [
                {'method': 'replace', 'kwargs': {'region': {'a': b - len(string) - 1, 'b': b - 1}, 'string': string}},
                {'method': 'cursor', 'kwargs': {'region': {'a': a, 'b': b - 1}}},
            ])
        else:
            UpdateThread(self, [
                {'method': 'replace', 'kwargs': {'region': {'a': b - len(string), 'b': b - 1}, 'string': string}},
                {'method': 'cursor', 'kwargs': {'region': {'a': b, 'b': b}}},
            ])

        self.updated = True

    def finalize(self, set_cursor=True):
        if not self.letters:
            return

        self.init_event()
        self.init_letter()
        self.prefix = ''
        self.suffix = ''
        self.updated = False
        self.pending_decompose = 0
        self.pending_arrow_position = 0


class KoreanInputEventListener(sublime_plugin.ViewEventListener, LetterHandler, ViewEventHandler, ArrowPositionHandler):

    def __init__(self, view):
        self.letters = []
        self.prefix = ''
        self.suffix = ''
        self.updated = False
        self.activated = False
        self.pending_decompose = 0
        self.pending_arrow_position = 0
        LetterHandler.__init__(self)
        ViewEventHandler.__init__(self)
        ArrowPositionHandler.__init__(self)
        sublime_plugin.ViewEventListener.__init__(self, view)

    def on_activated(self):
        # print('view.{}.on_activated()'.format(self.view.id()))
        self.init_event()
        self.init_letter()
        self.prefix = ''
        self.suffix = ''
        self.updated = False
        self.activated = True
        self.pending_decompose = 0
        self.pending_arrow_position = 0

    def on_deactivated(self):
        # print('view.{}.on_deactivated()'.format(self.view.id()))
        self.init_event()
        self.init_letter()
        self.prefix = ''
        self.suffix = ''
        self.updated = False
        self.activated = False
        self.pending_decompose = 0
        self.pending_arrow_position = 0

    def on_pre_save(self):
        filename = os.path.split(self.view.file_name())[-1]
        if filename == 'imesupportplugin.py':
            self.on_deactivated()

    def on_pre_close(self):
        self.on_deactivated()

    def on_query_completions(self, prefix, locations):
        self.push_event('query_completions')

    def on_modified(self):
        if self.pending_decompose:
            self.pending_decompose -= 1
            if self.pending_decompose < 0:
                self.pending_decompose = 0
            return

        a = self.view.sel()[0].a
        b = self.view.sel()[0].b
        # letter = self.view.substr(a - 1)
        # letter == ' ' and
        # print(self.events)

        if (b - a == 0 and self.events[-2:] == ['modified', 'selection_modified']):
            self.finalize()
            return

        self.push_event('modified')

    def on_selection_modified(self):
        if (len(self.events) < 2 or
                self.events[-2] != 'modified' or
                self.events[-1] != 'selection_modified'):
            self.push_event('selection_modified')
            return

        self.init_event()
        region = self.view.sel()[0]
        letter = self.view.substr(region.a)

        if letter not in kip.letters:
            return

        self.letters += [letter]
        self.set_arrow_position()
        self.compose_letters()
        # if len(self.letters) > 0:

    def on_text_command(self, command_name, args):
        # print('text_command: {}: {}: {}'.format(command_name, args, self.pending_arrow_position))
        if self.pending_arrow_position:
            self.pending_arrow_position -= 1
            if self.pending_arrow_position < 0:
                self.pending_arrow_position = 0
            return

        self.push_event('text_command')

        if command_name == 'left_delete' and self.letters:
            self.decompose_letters()
            return

        self.finalize()
