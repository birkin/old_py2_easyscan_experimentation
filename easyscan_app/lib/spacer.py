# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging


log = logging.getLogger(__name__)


class Spacer( object ):

    """ Manages left-justified spacer code. """

    def __init__( self ):
        self.notes_line_length = 50
        self.spacer_character = ' '

    def add_spacer( self, start_string ):
        lines = self.convert_string_to_lines( start_string.strip() )
        return lines

    def convert_string_to_lines( self, start_string ):
        """ Converts string to separate lines.
            Called by add_spacer() """
        log.debug( 'start_string, ```{0}```'.format(start_string) )
        lines = []  # need to convert the string to individual lines for calculation, because lines will auto-break on spaces
        words = start_string.split()
        line = ''
        for word in words:
            log.debug( 'word, ```{0}```'.format(word) )
            if len(word) == self.notes_line_length:
                line = word
                lines.append( line.strip() )
                line = ''
            elif ( len(word) <= self.notes_line_length ) and ( len(line) + len(' ') + len(word) <= self.notes_line_length ):
                line = line + ' ' + word
            elif ( len(word) + len(line) + len(' ') >= self.notes_line_length ):
                lines.append( line.strip() )
                line = word
            else:
                log.debug( 'oops condition' )
        if len(lines) == 0:
            lines.append( line.strip() )
        elif lines[-1] != line:
            lines.append( line.strip() )
        log.debug( 'lines, ```{0}```'.format(lines) )
        return lines
