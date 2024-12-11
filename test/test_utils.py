'''
Test the functions in the utils module.
'''


from itertools import islice

from pplt.utils import dict_join, dict_split, take, skip, unzip


def test_take():
    assert take(3, iter([1, 2, 3, 4, 5])) == [1, 2, 3]
    assert take(3, iter([1, 2])) == [1, 2]

def test_skip():
    it = iter([1, 2, 3, 4, 5, 6])
    skip(3, it)
    assert list(it) == [4, 5, 6]


def test_dict_join():
    dj = dict_join({'a': [1, 2, 3], 'b': [4, 5, 6]})
    assert next(dj) == {'a': 1, 'b': 4}
    assert next(dj) == {'a': 2, 'b': 5}


def test_dict_join_islice():
    dj = dict_join({'a': [1, 2, 3], 'b': [4, 5, 6]})
    assert list(islice(dj, 3)) == [
        {'a': 1, 'b': 4},
        {'a': 2, 'b': 5},
        {'a': 3, 'b': 6}
    ]

def test_dict_split():
    ds = dict_split(dict_join({'a': [1, 2, 3], 'b': [4, 5, 6]}))
    assert list(ds['a']) == [1, 2, 3]
    assert list(ds['b']) == [4, 5, 6]


def test_unzip():
    zipped = zip((1, 2, 3), ('a', 'b', 'c'))
    z1, z2 = unzip(zipped)
    assert list(z1) == [1, 2, 3]
    assert list(z2) == ['a', 'b', 'c']
