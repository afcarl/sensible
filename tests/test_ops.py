from sensible.util import ops


def test_merge_n_lists():

    a = [[1, 2, 3, 4, 5],
         ['a', 'b', 'c'],
         ['i', 'j', 'k', 'l', 'm', 'n', 'o', 'p']]
    expected_out = [1, 'a', 'i', 2, 'b', 'j', 3, 'c', 'k', 4, 'l', 5, 'm', 'n', 'o', 'p']

    out = ops.merge_n_lists(a)

    assert out == expected_out

    b = [1, 2, 3, 4, 5]

    out2 = ops.merge_n_lists(b)

    assert b == out2
