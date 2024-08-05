import typing

T = typing.TypeVar("T")

class Foo(typing.Generic[T]):

    mylist: typing.List[T] = list()

    def get_elem(self) -> typing.Optional[T]:
        if self.mylist:
            return self.mylist[0]
        else:
            return None

class IntFoo(Foo[int]):

    def addfive(self) -> int:
        if self.get_elem():
            return self.get_elem() + 5
        return 5

a = IntFoo()
a.mylist.append(7)
print(a.addfive())
