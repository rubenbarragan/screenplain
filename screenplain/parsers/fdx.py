from lxml import etree

from screenplain.types import (
    Slug, Action, Dialog, Transition,
    Screenplay
)
from screenplain.richstring import parse_emphasis


def _sequence_to_rich(lines):
    """Converts a sequence of strings into a list of RichString."""
    return [parse_emphasis(line) for line in lines]


def _string_to_rich(line):
    """Converts a single string into a RichString.
    """
    return parse_emphasis(line)


# TODO: Possibly, assign exclusively to FDX parser
# or factor out.
# TODO: Although the parser asumes the file is well-formated,
# handle errors here for visibility.
class InputParagraph(object):
    def __init__(self, lines_type, lines):
        self.lines = lines
        self.lines_type = lines_type

    def update_list(self, previous_paragraphs):
        """Inserts this paragraph into a list.
        Modifies the `previous_paragraphs` list.
        """
        (
            self.append_slug(previous_paragraphs) or
            self.append_character(previous_paragraphs) or
            self.append_dialog(previous_paragraphs) or
            self.append_transition(previous_paragraphs) or
            self.append_action(previous_paragraphs)
        )

    # TODO: Confirm that FDX (XML) format does not support
    # scene numbers
    def append_slug(self, paragraphs):
        """Shots scenes are treated as scene headings.
        """
        if len(self.lines) != 1:
            return False

        if self.lines_type not in ['Scene Heading', 'Shot']:
            return False

        text = self.lines[0]
        paragraphs.append(Slug(_string_to_rich(text.upper())))
        return True

    def _create_dialog(self, character):
        return Dialog(
            parse_emphasis(character.strip()),
            _sequence_to_rich(line.strip() for line in self.lines)
        )

    def append_character(self, paragraphs):
        """When characters type comes, it appends a Dialog object so that
        used when the actual dialog text comes.
        """
        if len(self.lines) != 1:
            return False

        if self.lines_type != 'Character':
            return False

        character = self.lines[0]
        paragraphs.append(Dialog(parse_emphasis(character.strip().upper())))
        return True

    def append_dialog(self, paragraphs):
        """Parentheticals will always come after a character based Final Draft
        official documentation:
        https://blog.finaldraft.com/lets-talk-about-parentheticals.
        Therefore, Parenthetical types will be handled here as if it was
        part of the dialog. The Dialog class is in charge of making the
        distinction between dialogs and parentheticals.
        """
        if len(self.lines) < 1:
            return False

        if self.lines_type not in ['Dialogue', 'Parenthetical']:
            return False

        if not paragraphs or not isinstance(paragraphs[-1], Dialog):
            return False

        # In the case the last element is a character, it will take it
        # and also an empty text.
        # In the case the last element is a dialoge or parenthical,
        # it will take the character as well and the text assigned +
        # the current text.
        previous = paragraphs.pop()
        current_lines = []
        for is_parenthetical, text in previous.blocks:
            current_lines.append(text)
        current_lines += self.lines

        paragraphs.append(Dialog(
            parse_emphasis(str(previous.character).strip()),
            _sequence_to_rich(str(line).strip() for line in current_lines)
        ))
        return True

    def append_transition(self, paragraphs):
        if len(self.lines) != 1:
            return False

        if self.lines_type != 'Transition':
            return False

        text = self.lines[0]
        paragraphs.append(Transition(_string_to_rich(text.upper())))
        return True

    def append_action(self, paragraphs):
        paragraphs.append(
            Action(_sequence_to_rich(line.rstrip() for line in self.lines))
        )
        return True


def _preprocess_line(raw_line):
    r"""Replaces tabs with spaces and removes trailing end of line markers.

    >>> _preprocess_line('foo \r\n\n')
    'foo '

    """
    return raw_line.expandtabs(4).rstrip('\r\n')


def _is_blank(line):
    return line == '' or line == ' '


def parse(stream):
    """Parses Final Draft source. The parser's behavior is
    parsing every component known and ignore everything
    else, such as errors and unknown paragraph types.

    Parser trusts the types and texts are well assigned.

    Returns a Screenplay object.
    """
    return parse_xml(stream)


# TODO: Parse title of the document.
def parse_xml(source):
    """Parses the xml file provided.

    Returns a Screenplay object.
    """
    root = etree.parse(source)
    return Screenplay('UNTITLED DOCUMENT', parse_body(root))


# TODO: Handle exceptions.
def parse_body(root):
    """Reads lines of the main screenplay and generates paragraph objects."""

    paragraphs = []
    for para in root.xpath("Content//Paragraph")[1:]:
        para_type = para.get("Type")

        line = ""
        for text in para.xpath("Text"):
            if text.text:
                line += text.text

        paragraph = InputParagraph(para_type, line.split('\n'))
        paragraph.update_list(paragraphs)

    return paragraphs
