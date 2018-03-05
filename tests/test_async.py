#!/usr/bin/python
# -*-coding: utf-8 -*-

import asyncio


async def searching_stuff_1():
    # searching
    yield 1
    await asyncio.sleep(1)
    # and searching
    yield 2
    yield 3


async def searching_stuff_2():
    await asyncio.sleep(5)
    yield 4
    yield 5


async def gen():
    # async for i in searching_stuff_1():
    #     yield i
    # async for i in searching_stuff_2():
    #     yield i
    l = [searching_stuff_1, searching_stuff_2]
    for g in l:
        async for g1 in g():
            yield g1


async def gen_all():
    async for i in gen():
        print(i)

if __name__ == "__main__":
    result = asyncio.get_event_loop().run_until_complete(gen_all())
    # print(result)