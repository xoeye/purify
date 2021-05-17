# purify

Pythonic object-mutator transforms as pure functions.

## Rationale

This solves a longstanding complaint that I have about Python -
there's no Pythonic way to write a pure function that is supposed to
return a transformed version of an input instance of a class.

Specifically, Python heavily incentivizes (via its syntax and via
utilities such as `mypy`) doing the following:

```
def rename_tree(name: str, tree: Tree) -> Tree:
    tree.name = name
    return tree
```

because the pure alternatives are either expensive:

```
def pure_rename_tree(name: str, tree: Tree) -> Tree:
    tree = deepcopy(tree)
    tree.name = name
    return tree
```

or not Pythonic and not type checkable:

```
def pure_rename_treedict(name: str, tree: dict) -> dict:
    return dict(tree, name=name)
```

This library is a result of noticing that the first option above is
extremely common in our codebases at XOi and enough of a convention to
be a best practice.  While this usually works as long as we compose
these "object transforms" as a linear pipeline where no function ever
needs to read the pre-transformed object, it is nevertheless a
convention which trades off actual purity for efficiency and
readability.

A new decorator, `@purify`, can be applied to any function where a
single one of the arguments will be modified, and by performing a
behind-the-scenes shallow copy of that object, allows the object
transform to become pure without further ado.

```
@purify
def rename_tree(name: str, tree: Tree) -> Tree:
    tree.name = tree
    return tree

tree = Tree('Felicity')
dtree = rename_tree('Daniella', tree)

print(tree.name) # 'Felicity'
print(dtree.name) # 'Daniella'
```

### Shallow copy vs deepcopy

In rudimentary tests with objects of size < 400 KB, `deepcopy` was
found to be, not surprisingly, 3 orders or magnitude slower than a
shallow copy. Additionally, equality tests on deep-copied and _not_
modified objects are 1-2 orders of magnitude slower than shallow
copies, presumably because the shallow copy allows the comparison to
do far more `id` equality checks.

So, `deepcopy` is expensive. But it's the only way to be sure that
your function is actually pure. `purify` defaults to shallow
copy. Why?

Because, as it turns out, it's frequently pretty simple to split
mutating functions into 'levels' based on the actual object that they
modify, and then decorate each level independently. In most cases,
this will mean far fewer Python objects need actual copying, and it
also gives you more reusable functions than you would have had if all
the levels were present together.

Given:

```
class Nest:
    num_eggs: int

class Tree:
    # ... (lots of other attributes)
    nests: List[Nest]
```

This expensive deepcopy approach:

```
@purify(deep=True)
def lay_in_all_nests(add: int, tree: Tree) -> Tree:
    for nest in tree.nests:
        nest.num_eggs += add
    return tree
```

Could be replaced with the equally pure, and less copy-expensive:

```
@purify
def lay_in_nest(lay: int, nest: Nest) -> Nest:
    nest.num_eggs += add
    return nest

@purify
def lay_in_all_nests(lay: int, tree: Tree) -> Tree:
    tree.nests = [lay_in_nest(lay, nest) for nest in tree.nests]
    return tree
```

#### How to visually parse shallowly pure functions

Some effort is required to use shallow-copy functions properly,
whereas `deepcopy` makes your function trivially pure. How to focus
that effort?

A good rule of thumb is that the object being purified must only ever
be referenced with a single dot (`.`), e.g. `tree.nests`, and usage of
that dotted name must either be read-only or direct assignment to that
name.  E.g., `tree.nests[i] = foo` is a no-no, because the
left-hand-side of the statement is not the bare name `nests`, but
something that directs its activity into the list itself.


## Advanced Usage:

### Argument name

It's highly recommended to follow a convention where the object that
you're mutating is the last positional argument to your function. This
is generally better for the composition of many partially-applied
functions transforming the same object.

That said, if you have a desire to specify which argument is to be
shallow-copied, you may do so by calling the decorator with the first
positional argument being the name of the function argument you want
purified.

### Deepcopy

As above, if you have a need for deepcopying, you need only to pass
`deep=True` to the decorator.
