#!/usr/bin/env python

# Copyright (c) 2011 Martin Vilcans
# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license.php

import sys
import codecs
from optparse import OptionParser

from screenplain.parsers import fountain, fdx

output_formats = (
    'fdx', 'html', 'pdf'
)

input_formats = (
    'fdx', 'fountain'
)

usage = """Usage: %prog [options] [input-file [output-file]]

If a file name parameter is missing or a dash (-), input will be read
from standard input and output will be written to standard output.

Screenplain will try to auto-detect the output format if
an output-file is given. Otherwise use the --output-format option."""


def invalid_format(parser, message):
    parser.error(
        '%s\nUse --format with one of the following formats: %s' %
        (message, ' '.join(output_formats))
    )


def main(args):
    parser = OptionParser(usage=usage)
    parser.add_option(
        '-o', '--output-format', dest='output_format',
        metavar='FORMAT',
        help=(
            'Set what kind of file to create. FORMAT can be one of ' +
            ', '.join(output_formats)
        )
    )
    parser.add_option(
        '-i', '--input-format', dest='input_format',
        metavar='FORMAT',
        help=(
            'Set what kind of file to read. FORMAT can be one of ' +
            ', '.join(input_formats)
        )
    )
    parser.add_option(
        '--bare',
        action='store_true',
        dest='bare',
        help=(
            'For HTML output, only output the actual screenplay, '
            'not a complete HTML document.'
        )
    )
    parser.add_option(
        '--css',
        metavar='FILE',
        help=(
            'For HTML output, inline the given CSS file in the HTML document '
            'instead of the default.'
        )
    )
    parser.add_option(
        '--strong',
        action='store_true',
        dest='strong',
        help=(
            'For PDF output, scene headings will appear '
            'Bold and Underlined.'
        )
    )
    options, args = parser.parse_args(args)
    if len(args) >= 3:
        parser.error('Too many arguments')
    input_file = (len(args) > 0 and args[0] != '-') and args[0] or None
    output_file = (len(args) > 1 and args[1] != '-') and args[1] or None

    input_format = options.input_format
    if input_format is None and input_file:
        if input_file.endswith('.fdx'):
            input_format = 'fdx'
        elif input_file.endswith('.fountain'):
            input_format = 'fountain'
        else:
            invalid_format(
                parser,
                'Could not detect input format from file name ' + input_format
            )

    if input_format not in input_formats:
        invalid_format(
            parser, 'Unsupported input format: "%s".' % input_format
        )

    output_format = options.output_format
    if output_format is None and output_file:
        if output_file.endswith('.fdx'):
            output_format = 'fdx'
        elif output_file.endswith('.html'):
            output_format = 'html'
        elif output_file.endswith('.pdf'):
            output_format = 'pdf'
        else:
            invalid_format(
                parser,
                'Could not detect output format from file name ' + output_file
            )

    if output_format not in output_formats:
        invalid_format(
            parser, 'Unsupported output format: "%s".' % output_format
        )

    if input_file:
        # TODO: handle exception on file readings.
        input = codecs.open(input_file, 'r', 'utf-8-sig')
    else:
        input = codecs.getreader('utf-8')(sys.stdin.buffer)

    if input_format == 'fdx':
        screenplay = fdx.parse(input)
    else:
        screenplay = fountain.parse(input)

    if output_format == 'pdf':
        output_encoding = None
    else:
        output_encoding = 'utf-8'

    if output_file:
        if output_encoding:
            output = codecs.open(output_file, 'w', output_encoding)
        else:
            output = open(output_file, 'wb')
    else:
        if output_encoding:
            output = codecs.getwriter(output_encoding)(sys.stdout.buffer)
        else:
            output = sys.stdout.buffer

    try:
        if output_format == 'text':
            from screenplain.export.text import to_text
            to_text(screenplay, output)
        elif output_format == 'fdx':
            from screenplain.export.fdx import to_fdx
            to_fdx(screenplay, output)
        elif output_format == 'html':
            from screenplain.export.html import convert
            convert(
                screenplay, output,
                css_file=options.css, bare=options.bare
            )
        elif output_format == 'pdf':
            from screenplain.export.pdf import to_pdf
            to_pdf(screenplay, output, is_strong=options.strong)
    finally:
        if output_file:
            output.close()


def cli():
    """setup.py entry point for console scripts."""
    main(sys.argv[1:])


if __name__ == '__main__':
    main(sys.argv[1:])
