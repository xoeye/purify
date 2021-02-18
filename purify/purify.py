"""Make Pythonic single-argument mutator transforms into properly pure functions"""
import copy
import inspect
from typing import Callable, Dict, TypeVar, Union, cast, overload

F = TypeVar("F", bound=Callable)


def _purify_by_name_or_pos(purify_strategy: Callable, pos: int, name: str, f: F) -> F:
    def purified(*args, **kwargs):
        if name in kwargs:
            kwargs = {**kwargs, name: purify_strategy(kwargs[name])}
        elif pos >= 0 and len(args) > pos:
            args = (*args[:pos], purify_strategy(args[pos]), *args[pos + 1 :])
        return f(*args, **kwargs)

    return cast(F, purified)


def _find_argument_pos(f: Callable, name: str) -> int:
    argspec = inspect.getfullargspec(f)
    for i, pos_name in enumerate(argspec.args):
        if pos_name == name:
            return i
    raise ValueError(f"{name} not found in function {f}")


def _find_last_pos_arg_name(f: Callable) -> str:
    return inspect.getfullargspec(f).args[-1]


@overload
def purify(arg: F) -> F:
    ...


@overload
def purify(arg: str = "", *, deep: bool = False) -> Callable[[F], F]:
    ...


def purify(
    arg: Union[str, F] = "", *, deep: bool = False
) -> Union[F, Callable[[F], F]]:
    """Makes a Python mutator transform into a shallowly or deeply pure
    mutator of a single argument, chosen by name or automatically.

    Shallow may be 3 orders of magnitude faster, so that is the
    default, but if you really don't want to split your transforms by
    level, you can use deep instead.

    Called with only the function as its argument, it will assume that
    the last positional argument is the one you want to purify.

    """
    copy_strategy: Dict[bool, Callable] = {True: copy.deepcopy}
    purify_name_or_f = arg

    if isinstance(purify_name_or_f, str):
        purify_name = purify_name_or_f
    else:
        purify_name = ""

    def decorator(f: F) -> F:
        nonlocal purify_name
        if not purify_name:
            # autopurify the last argument
            purify_name = _find_last_pos_arg_name(f)
        return _purify_by_name_or_pos(
            copy_strategy.get(deep, copy.copy),
            _find_argument_pos(f, purify_name),
            purify_name,
            f,
        )

    if isinstance(purify_name_or_f, str):
        return decorator

    return decorator(purify_name_or_f)
