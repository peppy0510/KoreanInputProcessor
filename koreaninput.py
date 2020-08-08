# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com

requirements:

description:

reference:

'''


import os
import sys

from copy import deepcopy


for k, env in os.environ.items():
    if not isinstance(env, str):
        continue
    for path in [path for path in env.split(';') if 'python' in path.lower()]:
        parts = [v for v in path.strip().split(os.path.sep) if v]
        if not parts[-1].lower().startswith('python'):
            continue
        python_path = os.path.sep.join(parts)
        package_path = os.path.join(python_path, 'Lib', 'site-packages')
        if python_path not in sys.path:
            sys.path += [python_path]
        if package_path not in sys.path:
            sys.path += [package_path]


try:
    import hgtk
except ImportError as error:
    print(error)


class KoreanInputProcessor:

    def __init__(self):
        letters = list(hgtk.letter.CHO) + list(hgtk.letter.JOONG) + list(hgtk.letter.JONG)
        self.letters = set([v for v in letters if v])

    def is_cho(self, char):
        return char in hgtk.letter.CHO

    def is_joong(self, char):
        return char in hgtk.letter.JOONG

    def is_jong(self, char):
        return char in hgtk.letter.JONG

    def compose(self, a, b, c=''):
        try:
            composed = hgtk.letter.compose(a, b, c)
        except hgtk.exception.NotHangulException:
            composed = None
        except hgtk.exception.NotLetterException:
            composed = None
        return composed

    def decompose(self, char):
        try:
            decomposed = hgtk.letter.decompose(char)
        except hgtk.exception.NotHangulException:
            decomposed = []
        except hgtk.exception.NotLetterException:
            decomposed = []
        return [v for v in decomposed if v]

    def combine_joong(self, a, b):
        return {
            ('ㅗ', 'ㅏ'): 'ㅘ',
            ('ㅗ', 'ㅐ'): 'ㅙ',
            ('ㅗ', 'ㅣ'): 'ㅚ',
            ('ㅜ', 'ㅓ'): 'ㅝ',
            ('ㅜ', 'ㅔ'): 'ㅞ',
            ('ㅜ', 'ㅣ'): 'ㅟ',
            ('ㅡ', 'ㅣ'): 'ㅢ',
        }.get((a, b))

    def combine_jong(self, a, b):
        return {
            ('ㄱ', 'ㅅ'): 'ㄳ',
            ('ㄴ', 'ㅈ'): 'ㄵ',
            ('ㄴ', 'ㅎ'): 'ㄶ',
            ('ㄹ', 'ㄱ'): 'ㄺ',
            ('ㄹ', 'ㅁ'): 'ㄻ',
            ('ㄹ', 'ㅂ'): 'ㄼ',
            ('ㄹ', 'ㅅ'): 'ㄽ',
            ('ㄹ', 'ㅌ'): 'ㄾ',
            ('ㄹ', 'ㅍ'): 'ㄿ',
            ('ㄹ', 'ㅎ'): 'ㅀ',
            ('ㅂ', 'ㅅ'): 'ㅄ',
        }.get((a, b))

    def decombine_joong(self, joong):
        return {
            'ㅘ': ('ㅗ', 'ㅏ'),
            'ㅙ': ('ㅗ', 'ㅐ'),
            'ㅚ': ('ㅗ', 'ㅣ'),
            'ㅝ': ('ㅜ', 'ㅓ'),
            'ㅞ': ('ㅜ', 'ㅔ'),
            'ㅟ': ('ㅜ', 'ㅣ'),
            'ㅢ': ('ㅡ', 'ㅣ'),
        }.get(joong)

    def decombine_jong(self, jong):
        return {
            'ㄳ': ('ㄱ', 'ㅅ'),
            'ㄵ': ('ㄴ', 'ㅈ'),
            'ㄶ': ('ㄴ', 'ㅎ'),
            'ㄺ': ('ㄹ', 'ㄱ'),
            'ㄻ': ('ㄹ', 'ㅁ'),
            'ㄼ': ('ㄹ', 'ㅂ'),
            'ㄽ': ('ㄹ', 'ㅅ'),
            'ㄾ': ('ㄹ', 'ㅌ'),
            'ㄿ': ('ㄹ', 'ㅍ'),
            'ㅀ': ('ㄹ', 'ㅎ'),
            'ㅄ': ('ㅂ', 'ㅅ'),
        }.get(jong)

    def decompose_letter(self, letter):
        decomposed = self.decompose(letter)

        if len(decomposed) == 1:
            a = decomposed[0]
            decombined_joong = self.decombine_joong(a)
            decombined_jong = self.decombine_jong(a)

            if decombined_joong:
                return decombined_joong
            elif decombined_jong:
                return decombined_jong
            else:
                return decomposed

        elif len(decomposed) == 2:
            a, b = decomposed
            decombined = self.decombine_joong(b)

            if not decombined:
                return decomposed
            else:
                b, c = decombined
                return [a, b, c]

        elif len(decomposed) == 3:
            a, b, d = decomposed
            decombined_joong = self.decombine_joong(b)
            decombined_jong = self.decombine_jong(d)

            if not decombined_joong and not decombined_jong:
                return decomposed

            elif not decombined_jong:
                b, c = decombined_joong
                return [a, b, c, d]

            elif not decombined_joong:
                d, e = decombined_jong
                return [a, b, d, e]
            else:
                b, c = decombined_joong
                d, e = decombined_jong
                return [a, b, c, d, e]

        return decomposed

    def decomposed_char_length(self, char):
        decomposed = self.decompose(char)
        length = len(decomposed)
        if len(decomposed) == 1:
            a = decomposed[0]
            if self.decombine_joong(a):
                length += 1
            elif self.decombine_jong(a):
                length += 1

        elif len(decomposed) == 2:
            a, b = decomposed
            if self.decombine_joong(b):
                length += 1

        elif len(decomposed) == 3:
            a, b, c = decomposed
            if self.decombine_joong(b):
                length += 1
            if self.decombine_jong(c):
                length += 1

        return length

    def compose_collection(self, collection):
        collection = deepcopy(collection)[::-1]
        collection = self.__compose_collection(collection)
        collection = self.__compose_collection(collection)
        return collection[::-1]

    def __compose_collection(self, collection):
        '''
        ('ㅗ', 'ㅏ'): ('ㅘ')
        '''
        for i in range(len(collection) - 2, -1, -1):
            a = collection[i + 1]
            b = collection[i]
            combined = self.combine_joong(a, b)
            if combined:
                collection.pop(i)
                collection[i] = combined

        '''
        ('ㄱ', 'ㅅ') ('ㄳ')
        '''
        for i in range(len(collection) - 2, -1, -1):
            a = collection[i + 1]
            b = collection[i]
            combined = self.combine_jong(a, b)
            if combined:
                collection.pop(i)
                collection[i] = combined

        '''
        ('ㅇ', 'ㅏ', 'ㄴ'): ('안')
        '''
        delta = 0
        for i in range(len(collection) - 3, -1, -1):
            i -= delta
            if i < 0:
                break

            a = collection[i + 2]
            if not self.is_cho(a):
                continue

            b = collection[i + 1]
            if not self.is_joong(b):
                continue

            c = collection[i]
            if not self.is_jong(c):
                continue

            composed = self.compose(a, b, c)
            if not composed:
                continue

            collection.pop(i)
            collection.pop(i)
            collection[i] = composed
            delta += 1

        '''
        ('아', 'ㄴ'): ('안')
        '''
        for i in range(len(collection) - 2, -1, -1):
            a = collection[i + 1]
            c = collection[i]
            if not self.is_jong(c):
                continue

            decomposed = self.decompose(a)
            if len(decomposed) != 2:
                continue

            a, b = decomposed

            composed = self.compose(a, b, c)
            if not composed:
                continue

            collection.pop(i)
            collection[i] = composed

        '''
        ('ㅇ', 'ㅏ'): ('아')
        '''
        for i in range(len(collection) - 2, -1, -1):
            a = collection[i + 1]
            if not self.is_cho(a):
                continue

            b = collection[i]
            if not self.is_joong(b):
                continue

            composed = self.compose(a, b)
            if not composed:
                continue

            collection.pop(i)
            collection[i] = composed

        '''
        ('핫', 'ㅔ'): ('하', '세')
        '''
        for i in range(len(collection) - 2, -1, -1):
            a = collection[i + 1]
            d = collection[i]
            if not self.is_joong(d):
                continue

            decomposed = self.decompose(a)
            if len(decomposed) != 3:
                continue

            a, b, c = decomposed
            if not self.is_cho(c):
                continue

            ab_composed = self.compose(a, b)
            if not ab_composed:
                continue

            cd_composed = self.compose(c, d)
            if not cd_composed:
                continue

            collection[i + 1] = ab_composed
            collection[i] = cd_composed

        '''
        ('호', 'ㅣ'): ('회')
        '''
        for i in range(len(collection) - 2, -1, -1):
            a = collection[i + 1]
            c = collection[i]
            if not self.is_joong(c):
                continue

            decomposed = self.decompose(a)
            if len(decomposed) != 2:
                continue

            a, b = decomposed

            bc_combined = self.combine_joong(b, c)
            if not bc_combined:
                continue

            composed = self.compose(a, bc_combined)
            if not composed:
                continue

            collection.pop(i)
            collection[i] = composed

        '''
        ('발', 'ㄱ'): ('밝')
        '''
        for i in range(len(collection) - 2, -1, -1):
            a = collection[i + 1]
            d = collection[i]
            if not self.is_jong(d):
                continue

            decomposed = self.decompose(a)
            if len(decomposed) != 3:
                continue

            a, b, c = decomposed

            cd_combined = self.combine_jong(c, d)
            if not cd_combined:
                continue

            try:
                composed = hgtk.letter.compose(a, b, cd_combined)
            except hgtk.exception.NotHangulException:
                continue

            collection.pop(i)
            collection[i] = composed

        '''
        ('밝', 'ㅣ'): ('발', '기')
        '''
        for i in range(len(collection) - 2, -1, -1):
            a = collection[i + 1]
            e = collection[i]

            if not self.is_joong(e):
                continue

            decomposed = self.decompose(a)
            if len(decomposed) != 3:
                continue

            a, b, c = decomposed

            decombined = self.decombine_jong(c)
            if not decombined:
                continue

            c, d = decombined

            abc_composed = self.compose(a, b, c)
            if not abc_composed:
                continue

            de_composed = self.compose(d, e)
            if not de_composed:
                continue

            collection[i + 1] = abc_composed
            collection[i] = de_composed

        return collection
