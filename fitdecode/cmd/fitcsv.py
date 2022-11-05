#!/usr/bin/env python3
# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import argparse
import csv
import sys
import traceback

import fitdecode


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description='Dump a FIT file to JSON format',
        epilog=f'fitdecode version {fitdecode.__version__}',
        allow_abbrev=False)

    parser.add_argument(
        '--output', '-o', type=argparse.FileType(mode='wt', encoding='utf-8'),
        default='-',
        help='File to output data into (defaults to stdout)')

    parser.add_argument(
        '--nocrc', action='store_const',
        const=fitdecode.CrcCheck.DISABLED,
        default=fitdecode.CrcCheck.WARN,
        help='Some devices seem to write invalid CRC\'s, ignore these.')

    parser.add_argument(
        '--field-names', '-f', nargs='+',
        default=('timestamp',),
        help='Names of fields to include (=columns of the CSV file).')

    parser.add_argument(
        'infile', metavar='FITFILE', type=argparse.FileType(mode='rb'),
        help='Input .FIT file (use - for stdin)')

    options = parser.parse_args(args)

    return options


def main(args=None):
    options = parse_args(args)

    try:
        with fitdecode.FitReader(
                options.infile,
                processor=fitdecode.StandardUnitsDataProcessor(),
                check_crc=options.nocrc,
                keep_raw_chunks=True) as fit:

            writer = csv.writer(options.output)
            writer.writerow(options.field_names)

            for frame in fit:
                if frame.frame_type == fitdecode.FIT_FRAME_DEFINITION:
                    continue

                if frame.frame_type in (
                            fitdecode.FIT_FRAME_DEFINITION,
                            fitdecode.FIT_FRAME_DATA) and frame.mesg_type is None:
                    continue

                if frame.frame_type == fitdecode.FIT_FRAME_DATA:
                    frame_data = {}
                    for field in frame.fields:
                        if field.name in options.field_names and field.value is not None:
                            frame_data[field.name] = field.value

                    row = [frame_data.get(field_name, "-") for field_name in options.field_names]
                    writer.writerow(row)

    except Exception:
        print(
            'WARNING: the following error occurred while parsing FIT file. '
            'Output file might be incomplete or corrupted.',
            file=sys.stderr)
        print('', file=sys.stderr)
        traceback.print_exc()

    return 0


if __name__ == '__main__':
    sys.exit(main())
