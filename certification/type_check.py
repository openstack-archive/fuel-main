import functools


def match_base_type(tp, val):
    return type(val) is tp


def any_matcher(_):
    return True


def none_or(next_matcher, val):
    if val is not None:
        return next_matcher(val)
    return True


def match_list(inner_matcher, val):
    if not isinstance(val, (list, tuple)):
        return False

    for element in val:
        if not inner_matcher(element):
            return False

    return True


def match_set(inner_matcher, val):
    if not isinstance(val, set):
        return False

    for element in val:
        if not inner_matcher(element):
            return False

    return True


def match_dict(key_matcher, val_matcher, val):
    if not isinstance(val, dict):
        return False

    for k, v in val.items():
        if not (key_matcher(k) and val_matcher(v)):
            return False

    return True


class Any(object):
    pass


class NoneOr(object):
    def __init__(self, inner):
        self.inner = inner

type_map = {}

for _tp in (int, str, unicode, bool, float):
    type_map[_tp] = functools.partial(match_base_type, _tp)


type_map[Any] = any_matcher


def descr2matcher(descr):
    if descr is NoneOr:
        return functools.partial(none_or, descr.inner)
    elif isinstance(descr, (list, tuple)):
        if len(descr) != 1:
            raise ValueError("List in type description should be len 1")
        return functools.partial(match_list, descr2matcher(descr[0]))
    elif isinstance(descr, set):
        if len(descr) != 1:
            raise ValueError("Set in type description should be len 1")
        return functools.partial(match_set, descr2matcher(list(descr)[0]))
    elif isinstance(descr, dict):
        if len(descr) != 1:
            raise ValueError("Dict in type description should be len 1")
        k, v = descr.items()[0]
        return functools.partial(match_dict,
                                 descr2matcher(k),
                                 descr2matcher(v))
    elif descr in type_map:
        return type_map[descr]
    else:
        msg = "Unknown value in type description : {!r}".format(descr)
        raise ValueError(msg)


def check(descr, val):
    assert descr2matcher(descr)(val)


def test():
    assert descr2matcher(int)(1)
    assert not descr2matcher(int)("1")
    assert descr2matcher(str)("1")
    assert descr2matcher(bool)(True)
    assert descr2matcher(float)(1.1)
    assert descr2matcher([int])([1])
    assert descr2matcher([int])([1, 2])
    assert not descr2matcher([int])([1, []])
    assert descr2matcher([int])((1, ))
    assert descr2matcher({int: str})({1: "2"})
    assert not descr2matcher({int: str})({1: "2", 3: 4})
    assert not descr2matcher({int: str})({1: "2", 3: [4]})
    assert descr2matcher({int: [str]})({1: ["2", "4"]})
    assert descr2matcher({int: [str]})({1: []})
    assert not descr2matcher({int: [str]})({"1": []})

if __name__ == "__main__":
    test()
    print "All tests pass OK"
