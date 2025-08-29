from __future__ import annotations

from collections.abc import Collection, Iterable, Iterator, Sequence
from typing import Any, Callable, Generic, Self, SupportsIndex, TypeVar, cast, overload

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
KeyT = TypeVar("KeyT")
ValueT = TypeVar("ValueT")
T1 = TypeVar("T1")
T2 = TypeVar("T2")


class cached_property(Generic[T, ValueT]):
    __slots__ = "__doc__", "func", "slot"

    def __init__(self, func: Callable[[T], ValueT], *, slot: str | None = None) -> None:
        self.func = func
        self.slot = slot
        self.__doc__ = getattr(func, "__doc__")

    @overload
    def __get__(self, instance: None, owner: type[T]) -> cached_property[T, ValueT]: ...

    @overload
    def __get__(self, instance: T, owner: type[T]) -> ValueT: ...

    def __get__(self, instance: T | None, owner: type[T]) -> Any:
        if instance is None:
            return self

        if self.slot is None:
            value = self.func(instance)
            setattr(instance, self.func.__name__, value)
            return value

        try:
            return getattr(instance, self.slot)
        except AttributeError:
            value = self.func(instance)
            setattr(instance, self.slot, value)
            return value


class SequenceProxy(Sequence[T_co]):
    def __init__(self, proxied: Collection[T_co], *, sorted: bool = False) -> None:
        self.__proxied: Collection[T_co] = proxied
        self.__sorted: bool = sorted

    @cached_property
    def __copied(self) -> list[T_co]:
        if self.__sorted:
            self.__proxied = cast("list[T_co]", sorted(self.__proxied))  # pyright: ignore[reportArgumentType]
        else:
            self.__proxied = list(self.__proxied)
        return self.__proxied

    def __repr__(self) -> str:
        return f"SequenceProxy({self.__proxied!r})"

    @overload
    def __getitem__(self, idx: SupportsIndex) -> T_co: ...

    @overload
    def __getitem__(self, idx: slice) -> list[T_co]: ...

    def __getitem__(self, idx: SupportsIndex | slice) -> T_co | list[T_co]:
        return self.__copied[idx]

    def __len__(self) -> int:
        return len(self.__proxied)

    def __contains__(self, item: Any) -> bool:
        return item in self.__copied

    def __iter__(self) -> Iterator[T_co]:
        return iter(self.__copied)

    def __reversed__(self) -> Iterator[T_co]:
        return reversed(self.__copied)

    def index(self, value: Any, *args: Any, **kwargs: Any) -> int:
        return self.__copied.index(value, *args, **kwargs)

    def count(self, value: Any) -> int:
        return self.__copied.count(value)


class IndexableDict(Generic[KeyT, ValueT]):
    def __init__(self, *data: tuple[KeyT, ValueT]) -> None:
        self.__keys: list[KeyT] = [key for key, _ in data]
        self.__values: list[ValueT] = [val for _, val in data]

    def copy(self) -> dict[KeyT, ValueT]: ...

    @property
    def keys(self) -> SequenceProxy[KeyT]:
        return SequenceProxy(self.__keys)

    @property
    def values(self) -> SequenceProxy[ValueT]:
        return SequenceProxy(self.__values)

    def items(self) -> Iterator[tuple[KeyT, ValueT]]:
        yield from zip(self.__keys, self.__values)

    def index(self, key: KeyT, /) -> int:
        return self.__keys.index(key)

    def add(self, key: KeyT, value: ValueT) -> None:
        self.__keys.append(key)
        self.__values.append(value)

    @overload
    def get(self, key: KeyT, default: None = None, /) -> ValueT | None: ...
    @overload
    def get(self, key: KeyT, default: ValueT, /) -> ValueT: ...
    @overload
    def get(self, key: KeyT, default: T, /) -> ValueT | T: ...
    @overload
    def get(self, key: int, default: None = None, /) -> tuple[KeyT, ValueT] | None: ...
    @overload
    def get(self, key: int, default: T, /) -> tuple[KeyT, ValueT] | T: ...
    def get(self, key: int | KeyT, default: Any = None, /) -> Any:
        try:
            return self[key]
        except IndexError:
            return default

    @overload
    def pop(self, key: KeyT, /) -> ValueT: ...
    @overload
    def pop(self, key: KeyT, default: ValueT, /) -> ValueT: ...
    @overload
    def pop(self, key: KeyT, default: T, /) -> ValueT | T: ...
    @overload
    def pop(self, key: int, /) -> tuple[KeyT, ValueT]: ...
    @overload
    def pop(self, key: int, default: T, /) -> tuple[KeyT, ValueT] | T: ...
    def pop(self, key: KeyT | int, default: Any = None, /) -> Any:
        try:
            val = self[key]
            del self[key]
            return val
        except IndexError | KeyError:
            return default

    def __len__(self) -> int:
        return len(self.__keys)

    @overload
    def __getitem__(self, key: KeyT, /) -> ValueT: ...
    @overload
    def __getitem__(self, key: int, /) -> tuple[KeyT, ValueT]: ...
    def __getitem__(self, key: KeyT | int, /) -> ValueT | tuple[KeyT, ValueT]:
        if isinstance(key, int):
            try:
                return self.__keys[key], self.__values[key]
            except IndexError:
                raise IndexError("index out of range") from None
        else:
            try:
                return self.__values[self.__keys.index(key)]
            except ValueError:
                raise KeyError(key) from None

    @overload
    def __setitem__(self, key: KeyT, value: ValueT, /) -> None: ...
    @overload
    def __setitem__(self, key: int, value: tuple[KeyT, ValueT], /) -> None: ...
    def __setitem__(self, key: KeyT | int, value: Any, /) -> None:
        if isinstance(key, int):
            try:
                self.__keys[key] = value[0]
                self.__values[key] = value[1]
            except IndexError:
                raise IndexError("out of index") from None
        else:
            self.__keys.append(key)
            self.__values.append(value)

    def __delitem__(self, key: KeyT | int, /) -> None:
        idx = key if isinstance(key, int) else self.__keys.index(key)

        self.__keys.pop(idx)
        self.__values.pop(idx)

    def __iter__(self) -> Iterator[KeyT]:
        yield from self.__keys

    def __eq__(self, other: object, /) -> bool:
        return isinstance(other, IndexableDict) and hash(self) == hash(other)  # pyright: ignore[reportUnknownArgumentType]

    def __hash__(self) -> int:
        return hash((IndexableDict, self.__keys, self.__values))

    @overload
    def __or__(
        self, value: IndexableDict[KeyT, ValueT], /
    ) -> IndexableDict[KeyT, ValueT]: ...
    @overload
    def __or__(
        self, value: IndexableDict[T1, T2], /
    ) -> IndexableDict[KeyT | T1, ValueT | T2]: ...
    def __or__(
        self, other: IndexableDict[T1, T2], /
    ) -> IndexableDict[KeyT | T1, ValueT | T2]:
        return IndexableDict(*self.items(), *other.items())

    @overload
    def __ror__(
        self, value: IndexableDict[KeyT, ValueT], /
    ) -> IndexableDict[KeyT, ValueT]: ...
    @overload
    def __ror__(
        self, value: IndexableDict[T1, T2], /
    ) -> IndexableDict[KeyT | T1, ValueT | T2]: ...
    def __ror__(
        self, other: IndexableDict[T1, T2], /
    ) -> IndexableDict[KeyT | T1, ValueT | T2]:
        return IndexableDict(*other.items(), *self.items())

    @overload
    def __ior__(self, other: IndexableDict[KeyT, ValueT], /) -> Self: ...
    @overload
    def __ior__(self, other: Iterable[tuple[KeyT, ValueT]], /) -> Self: ...
    def __ior__(
        self, other: IndexableDict[KeyT, ValueT] | Iterable[tuple[KeyT, ValueT]], /
    ) -> Self:
        if isinstance(other, IndexableDict):
            self.__keys.extend(cast("SequenceProxy[KeyT]", other.keys))
            self.__values.extend(cast("SequenceProxy[ValueT]", other.values))  # pyright: ignore[reportUnknownMemberType]
        else:
            for key, value in other:
                self[key] = value

        return self

    def __repr__(self) -> str:
        return (
            "{"
            + ", ".join(
                f"{key!r}: {val!r}" for key, val in zip(self.__keys, self.__values)
            )
            + "}"
        )
