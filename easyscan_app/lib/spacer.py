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
        """ Manages spacer code.
            Called by x() """
        lines = self.convert_string_to_lines( start_string.strip() )
        full_line = ''
        for line in lines:
            spaced_line = self.make_spaced_line( line )
            full_line = full_line + spaced_line
        log.debug( 'full_line, ```{0}```'.format(full_line) )
        return full_line

        return lines

    def convert_string_to_lines( self, start_string ):
        """ Converts full-string to separate lines of words, trying to keep each line's length less-than-or-equal-to the line-length limit.
              (Goal not possible if word-length exceeds line-length limit.)
            Called by add_spacer() """
        ( lines, words, line ) = ( [], start_string.split(), '' )
        for word in words:
            ( line, lines ) = self.apply_word_logic( word, line, lines )
        if len(lines) == 0:
            lines.append( line.strip() )
        elif lines[-1] != line:
            if len(line) > 0:
                lines.append( line.strip() )
        log.debug( 'lines, ```{0}```'.format(lines) )
        return lines

    def apply_word_logic( self, word, line, lines ):
        """ Builds a line word-by-word. Just before the line-length would exceed the maximum limit,
              adds the line to lines, and starts with a fresh empty line.
            Called by convert_string_to_lines() """
        if len(word) >= self.notes_line_length:
            lines.append( word )
            line = ''
        elif ( len(word) + len(line) + len(' ') <= self.notes_line_length ):
            line = line + ' ' + word
        elif ( len(word) + len(line) + len(' ') > self.notes_line_length ):
            lines.append( line.strip() )
            line = word
        else:
            raise Exception( 'condition not handled' )
        return ( line, lines )

    def make_spaced_line( self, line ):
        spacers_needed = self.calc_spacers_needed( line )
        line_spacer = self.assemble_spacer( spacers_needed )
        spaced_line = line + line_spacer
        log.debug( 'spaced_line, ```{0}```'.format(spaced_line) )
        return spaced_line

    def calc_spacers_needed( self, line ):
        line_len = len( line )
        if line_len <= self.notes_line_length:
            spacers_needed = self.notes_line_length - line_len
        else:
            spacers_needed = self.notes_line_length - ( line_len % self.notes_line_length )
        log.debug( 'spacers_needed, ```{0}```'.format(spacers_needed) )
        return spacers_needed

    def assemble_spacer( self, spaces_needed ):
        """ Calculates and returns spacer.
            Called by add_spacer() """
        if spaces_needed == 0:  # add a whole other line of spacers
            temp_spacer = self.spacer_character * self.notes_line_length
            line_spacer = ' ' + temp_spacer[0:-2] + ' '
        elif spaces_needed == 1 or spaces_needed == 2:
            line_spacer = ' ' * spaces_needed
        elif spaces_needed > 2:
            temp_spacer = self.spacer_character * spaces_needed
            line_spacer = ' ' + temp_spacer[0:-2] + ' '
        log.debug( 'line_spacer, ```{0}```'.format(line_spacer) )
        return line_spacer

    # def convert_str
