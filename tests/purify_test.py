from typing import Sequence

import pytest

from purify import purify


class Nest:
    def __init__(self, num_eggs: int):
        self.num_eggs = num_eggs


class Tree:
    def __init__(self, name: str, nests: Sequence[Nest] = ()):
        self.name = name
        self.nests = list(nests)


def _rename_tree(new_name: str, tree: Tree, *, double: bool = False) -> Tree:
    if double:
        new_name = new_name + new_name
    tree.name = new_name
    return tree


rename_tree = purify("tree")(_rename_tree)


def test_shallow_purify_works_with_top_level_attrs():
    tree = Tree("Ralph")

    mutated_tree = rename_tree("Felicity", tree)
    assert tree.name == "Ralph"
    assert mutated_tree.name == "Felicity"

    mutated_tree = rename_tree("Felicity", double=True, tree=tree)
    assert tree.name == "Ralph"
    assert mutated_tree.name == "FelicityFelicity"


def increment_nests(add: int, tree: Tree) -> Tree:
    for nest in tree.nests:
        nest.num_eggs += add
    return tree


def test_shallow_purify_does_not_deepcopy():
    shallow_increment_nests = purify("tree")(increment_nests)

    tree = Tree("Steve", nests=[Nest(2), Nest(3)])

    mutated_tree = shallow_increment_nests(10, tree)
    mutated_tree.name = "Bob"

    assert mutated_tree is not tree
    assert mutated_tree.nests is tree.nests
    assert mutated_tree.nests == tree.nests
    assert tree.nests[0].num_eggs == 12
    assert tree.name == "Steve"  # still doing shallow copy though


def test_deep_purify_does_deepcopy():
    deep_increment_nests = purify("tree", deep=True)(increment_nests)

    tree = Tree("Steve", nests=[Nest(2), Nest(3)])

    mutated_tree = rename_tree("George", deep_increment_nests(10, tree))

    assert mutated_tree is not tree
    assert mutated_tree.nests != tree.nests
    assert tree.nests[0].num_eggs == 2
    assert mutated_tree.nests[0].num_eggs == 12
    assert tree.name == "Steve"  # still doing shallow copy though


@purify("nest")
def increment_nest(add: int, nest: Nest) -> Nest:
    nest.num_eggs += add
    return nest


def test_purify_leveled():
    """Demonstrates the preferred leveled approach that makes shallow copy viable"""
    tree = Tree("Tim", nests=[Nest(4), Nest(5)])

    @purify("tree")
    def increment_nests(add: int, tree: Tree) -> Tree:
        tree.nests = [increment_nest(add, nest) for nest in tree.nests]
        return tree

    new_tree = increment_nests(3, tree)
    assert new_tree != tree
    assert tree.nests[0].num_eggs == 4
    assert new_tree.nests[0].num_eggs == 7


def test_autopurify():
    tree = Tree("Josh")

    rename_tree = purify(_rename_tree)

    mtree = rename_tree("Jeff", tree)
    assert mtree.name == "Jeff"
    assert tree.name == "Josh"


@purify
def awkward(name: str, age: int, size: int, empty: bool = False) -> str:
    if empty:
        return ""
    return f"{name} {age} {size}"


def test_awkward():
    assert "peter 10 13" == awkward("peter", 10, 13)

    with pytest.raises(TypeError):
        # make sure meaningful Python errors are raised for bad calls
        awkward("peter", 13, age=10)  # type: ignore
        # this one is illegal in standard python

    assert "peter 10 13" == awkward("peter", size=13, age=10)

    assert "" == awkward("peter", 8, 3, empty=True)
    assert "" == awkward("peter", 8, 3, True)


def test_autopurify_deep():
    """Pick the last positional argument but still allow deep=True to be provided"""
    rename_tree = purify(deep=True)(_rename_tree)
    assert rename_tree("Peter", Tree("Steve")).name == "Peter"


def test_value_error():

    with pytest.raises(ValueError):

        @purify("bar")
        def f(foo: str) -> str:
            return foo
