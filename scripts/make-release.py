#!/usr/bin/env python
"""
    make-release
    ~~~~~~~~~~~~

    Helper script that performs a release.  Does pretty much everything
    automatically for us.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import argparse
import os
import re
import sys
from datetime import date, datetime
from subprocess import PIPE, Popen

_date_clean_re = re.compile(r"(\d+)(st|nd|rd|th)")


def parse_changelog():
    with open("CHANGES") as f:
        lineiter = iter(f)
        for line in lineiter:
            match = re.search(r"^Version\s+(.*)", line.strip())
            if match is None:
                continue
            version = match.group(1).strip()
            if lineiter.next().count("-") != len(match.group(0)):
                continue
            while 1:
                change_info = lineiter.next().strip()
                if change_info:
                    break

            match = re.search(
                r"released on (\w+\s+\d+\w+\s+\d+)" r"(?:, codename (.*))?(?i)",
                change_info,
            )
            if match is None:
                continue

            datestr, codename = match.groups()
            return version, parse_date(datestr), codename


def bump_version(version):
    try:
        parts = map(int, version.split("."))
    except ValueError:
        fail("Current version is not numeric")
    parts[-1] += 1
    return ".".join(map(str, parts))


def parse_date(string):
    string = _date_clean_re.sub(r"\1", string)
    return datetime.strptime(string, "%B %d %Y")


def set_filename_version(filename, version_number, pattern):
    changed = []

    def inject_version(match):
        before, old, after = match.groups()
        changed.append(True)
        return before + version_number + after

    with open(filename) as f:
        contents = re.sub(
            r"^(\s*%s\s*=\s*')(.+?)(')(?sm)" % pattern, inject_version, f.read()
        )

    if not changed:
        fail("Could not find %s in %s", pattern, filename)

    with open(filename, "w") as f:
        f.write(contents)


def set_version(version):
    info("Setting version to %s", version)
    with open("logbook/__version__.py", "w") as f:
        f.write(f"__version__ = {version!r}")


def fail(message, *args):
    print >> sys.stderr, "Error:", message % args
    sys.exit(1)


def info(message, *args):
    print >> sys.stderr, message % args


def get_git_tags():
    return set(Popen(["git", "tag"], stdout=PIPE).communicate()[0].splitlines())


def git_is_clean():
    return Popen(["git", "diff", "--quiet"]).wait() == 0


def make_git_commit(message, *args):
    message = message % args
    Popen(["git", "commit", "-am", message]).wait()


def make_git_tag(tag):
    info('Tagging "%s"', tag)
    Popen(["git", "tag", tag]).wait()


parser = argparse.ArgumentParser("%prog [options]")
parser.add_argument("--no-upload", dest="upload", action="store_false", default=True)


def main():
    args = parser.parse_args()

    os.chdir(os.path.join(os.path.dirname(__file__), ".."))

    rv = parse_changelog()
    if rv is None:
        fail("Could not parse changelog")

    version, release_date, codename = rv
    dev_version = bump_version(version) + "-dev"

    info(
        "Releasing %s (codename %s, release date %s)",
        version,
        codename,
        release_date.strftime("%d/%m/%Y"),
    )
    tags = get_git_tags()

    if version in tags:
        fail('Version "%s" is already tagged', version)
    if release_date.date() != date.today():
        fail(
            "Release date is not today ({} != {})".format(
                release_date.date(), date.today()
            )
        )

    if not git_is_clean():
        fail("You have uncommitted changes in git")

    set_version(version)
    make_git_commit("Bump version number to %s", version)
    make_git_tag(version)
    set_version(dev_version)
    make_git_commit("Bump version number to %s", dev_version)


if __name__ == "__main__":
    main()
