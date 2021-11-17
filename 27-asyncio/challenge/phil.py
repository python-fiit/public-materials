#!/usr/bin/env python3

import re
import sys
from collections import defaultdict
from urllib.request import urlopen
from urllib.parse import quote, unquote
from urllib.error import URLError, HTTPError


CONTENT_START = re.compile(r'<div.*?mw-content-text', re.IGNORECASE)
DIV_TAG = re.compile(r'<(/?div)', re.IGNORECASE)
HREF_TAG = re.compile('<a\\s+href=["\']/wiki/([^:#]*?)["\']', re.IGNORECASE)


def get_content(name):
    try:
        with urlopen(f'http://ru.wikipedia.org/wiki/{quote(name)}') as page:
            return page.read().decode('utf-8', errors='ignore')
    except (URLError, HTTPError):
        return None


def extract_content(page):
    begin = CONTENT_START.search(page)
    if not begin:
        return (0, 0)

    tags = 1
    pos = begin.start() + 1
    while tags:
        tag = DIV_TAG.search(page, pos)
        if not tag:
            return (begin.end(), len(page))

        pos = tag.start() + 1
        if tag.group(1).startswith('</'):
            tags -= 1
        else:
            tags += 1

    return (begin.end(), pos)


def remove_duplicates(iterator):
    seen = set()

    for item in iterator:
        if item not in seen:
            yield item
            seen.add(item)


def extract_links(page, begin, end):
    yield from remove_duplicates(
        unquote(link.group(1))
        for link in HREF_TAG.finditer(page, begin, end)
    )


def build_node(frontier):
    for name in frontier:
        page = get_content(name)
        for link in extract_links(page, *extract_content(page)):
            yield (name, link)


def build_graph(start, finish):
    graph = defaultdict(set)

    visited = set()
    frontier = [start]

    cf_finish = finish.casefold()
    while cf_finish not in (visited | set(frontier)):
        new_front = []

        for (name, link) in build_node(frontier):
            visited.add(name.casefold())

            graph[name].add(link)
            if link.casefold() not in visited:
                new_front.append(link)

            if link.casefold() == cf_finish:
                return graph

        frontier = list(remove_duplicates(new_front))

    return graph


def _get_track(start, finish, backtrack):
    track = [finish]
    pointer = finish

    while pointer != start:
        pointer = backtrack.get(pointer, start)
        track.append(pointer)

    return track[::-1]


def find_chain(graph, start, finish):
    visited = set()
    backtrack = {}
    queue = [start]

    while queue:
        top = queue.pop(0)

        for item in graph[top]:
            if item in visited:
                continue

            visited.add(item)
            backtrack[item] = top
            queue.append(item)

            if item == finish:
                return _get_track(start, finish, backtrack)


def main():
    if len(sys.argv) < 2:
        sys.exit("Start word is not specified")

    params = (sys.argv[1], 'Философия')

    graph = build_graph(*params)
    chain = find_chain(graph, *params)
    if chain:
        print('\n'.join(chain))
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
