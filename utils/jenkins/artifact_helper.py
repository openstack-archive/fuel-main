#!/usr/bin/env python

import argparse
import logging
import re
import sys


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

art_id = {
    (None, 'img'): 'img',
    (None, 'iso'): 'iso',
    ('upgrade', 'tar'): 'upgrade',
    ('upgrade', 'tar.lrzip'): 'upgrade-lrzip',
    ('patching', 'tar'): 'patching',
}


class NamingException(Exception):
    pass


def parsed_name_to_str(parsed_name, fmt_string):
    """Print dictionary using specified fmt string"""
    if not fmt_string:
        fmt_string = ("fullname: {fullname}\n"
                      "version: {version}\n"
                      "ci_id: {ci_id}\n"
                      "art_type: {art_type}\n"
                      "art_ext: {art_ext}\n"
                      "art_id: {art_id}\n"
                      "build_number: {build_number}\n"
                      "timestamp: {timestamp}")
    return fmt_string.format(**parsed_name)


def parse_name(name):
    """Parse artifact name according to schema:

    fuel
    [-<ci_id>]
    [-<version>]
    [-<art_type>]
    [-<build_number>]
    [-<timestamp>]
    .<art_ext>
    """

    parsed_name = {'fullname': name}

    # Check if artifact name should follow the scheme
    if not name.startswith("fuel-"):
        raise NamingException("Wrong name")

    match_string = (
        "fuel"
        "(-(?P<ci_id>(gerrit)|(community)))?"
        "(-(?P<version>(\d\.\d)|(master)))?"
        "(-(?P<art_type>(upgrade)|(patching)))?"
        "(-(?P<build_number>\d*))?"
        "(-(?P<timestamp>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}))?"
        "(\.(?P<art_ext>[a-z\.]*))\Z"
    )

    matched = re.match(match_string, name)

    if not matched:
        raise NamingException(
            "Name %s does not match string: %s" % (name, match_string)
        )

    parsed_name.update(matched.groupdict())

    # Add art_id - the unique id combined from art_type and art_ext

    parsed_name['art_id'] = art_id[
        (parsed_name['art_type'], parsed_name['art_ext'])
    ]

    return parsed_name


def run_command(command, args):
    """Runs subcommand according to parsed data"""

    if command == 'parse':
        parsed_name = parse_name(args.artifact_name)
        print parsed_name_to_str(parsed_name, args.fmt)
    elif command == 'test':
        try:
            parse_name(args.artifact_name)
        except NamingException:
            sys.exit(-1)
    else:
        logger.warning("Nothing to do for command %s" % command)


def main():

    parser = argparse.ArgumentParser(description='Artifacts helper')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        default=False,
                        help='show debug output')

    subparsers = parser.add_subparsers(
        title='Subcommands',
        description='Run %(prog)s <subcommand> -h for subcommand help.',
        dest='command')

    parser_test = subparsers.add_parser(
        'test',
        help=(
            'Test if artifact name follows naming schema. '
            'Return error code -1 if not.'
        )
    )

    parser_test.add_argument('artifact_name', help='artifact name')

    parser_parse = subparsers.add_parser(
        'parse',
        help=(
            'Parse artifact name according to naming schema'
            'and print formatted output'
        )
    )

    parser_parse.add_argument('artifact_name', help='artifact name')
    parser_parse.add_argument('--fmt', default=None,
                              help='output format string')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(level=logging.DEBUG)

    logger.debug("Args: %s" % args)

    run_command(args.command, args)


if __name__ == '__main__':
    main()
