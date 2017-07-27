# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, pprint
# from easyscan_app.models import LasDataMaker, ScanRequest, StatsBuilder
from django.http import QueryDict
from django.test import TestCase
from easyscan_app.lib.data_prepper import LasDataMaker
from easyscan_app.lib.magic_bus import Prepper
from easyscan_app.lib.spacer import Spacer
from easyscan_app.models import ScanRequest, StatsBuilder


# maker = LasDataMaker()
prepper = Prepper()
statsbuilder = StatsBuilder()


class LasDataMakerTest( TestCase ):
    """ Tests models.LasDataMaker() """

    def setUp(self):
        self.maker = LasDataMaker()
        self.maxDiff = None

    def test__utf8list_to_utf8csv__str( self ):
        """ Tests good utf8 strings (required by csv module). """
        utf8_list = [ b'foo', b'bar', b'“iñtërnâtiônàlĭzætiøn”' ]
        result = self.maker.utf8list_to_utf8csv( utf8_list )
        self.assertEqual(
            b'"foo","bar","\xe2\x80\x9ci\xc3\xb1t\xc3\xabrn\xc3\xa2ti\xc3\xb4n\xc3\xa0l\xc4\xadz\xc3\xa6ti\xc3\xb8n\xe2\x80\x9d"\r\n',
            result )
        self.assertEqual(
            str,
            type(result) )

    def test__utf8list_to_utf8csv__unicode( self ):
        """ Tests bad unicode strings. """
        unicode_list = [ u'foo', u'bar', u'“iñtërnâtiônàlĭzætiøn”' ]
        result = u'init'
        try:
            self.maker.utf8list_to_utf8csv( unicode_list )
        except Exception as e:
            result = unicode(e)
        self.assertEqual(
            u"entry `u'foo'` not of type str",
            result )

    def test__make_date_string( self ):
        """ Tests conversion of datetime object to string required by LAS. """
        dt = datetime.datetime( 2014, 12, 8, 12, 40, 59 )
        self.assertEqual(
            u'Mon Dec 08 2014',
            self.maker.make_date_string( dt )
            )

    def test__strip_stuff( self ):
        """ Tests removal of double-quotes and new-lines. """
        self.assertEqual(
            u"The title was 'Zen', I think.",
            self.maker.strip_stuff(u'The title was "Zen", I think.') )
        self.assertEqual(
            u'first line - second line',
            self.maker.strip_stuff(u'first line\nsecond line') )
        self.assertEqual(
            u'first line - second line',
            self.maker.strip_stuff(u'first line\rsecond line') )
        self.assertEqual(
            u"The title was 'Zen', I think.",
            self.maker.strip_stuff(u'The title was `Zen`, I think.') )

    # def test__add_email( self ):
    #     """ Checks for space before and after actual email line. """
    #     email = 'a@a.edu'
    #     expected_lst = [
    #         'PATRON_EMAIL...                                   ',  # 50 characters
    #         '                                                  ',
    #         'a@a.edu | A@A.EDU                                 ',
    #         '                                                  '
    #         ]
    #     self.assertEqual(
    #         ''.join( expected_lst ),
    #         self.maker.add_email( email )
    #         )

    def test__add_email( self ):
        """ Checks for space before and after actual email line. """
        email = 'a@a.edu'
        expected_lst = [
            'email: a@a.edu                                    ',  # 50 characters
            'EMAIL: A@A.EDU                                    '
            ]
        self.assertEqual(
            ''.join( expected_lst ),
            self.maker.add_email( email )
            )

    def test__add_article_chapter_title( self ):
        """ Checks for space before and after article-chapter-title line. """
        initial_data = 'foo bar                                           '  # 50 characters
        article_chapter_title = 'Ultrastructural analysis of the effect of ethane dimethanesulphonate on the testis of the rat, guinea pig, hamster and mouse.'
        expected_lst = [
            'foo bar                                           ',  # 50 characters
            'ARTICLE-CHAPTER-TITLE...                          ',
            '                                                  ',
            'Ultrastructural analysis of the effect of ethane  ',
            'dimethanesulphonate on the testis of the rat,     ',
            'guinea pig, hamster and mouse.                    ',
            '                                                  '
            ]
        self.assertEqual(
            ''.join( expected_lst ),
            self.maker.add_article_chapter_title( initial_data, article_chapter_title )
            )

    # def test__make_notes_field( self ):
    #     """ Checks for proper spacing. """
    #     patron_email = 'a@a.edu'
    #     item_chap_vol_title = 'test-article-title'
    #     item_page_range_other = 'test-range'
    #     item_other = 'test-other'
    #     expected_lst = [
    #         'PATRON_EMAIL...                                   ',  # 50 characters
    #         '                                                  ',
    #         'a@a.edu | A@A.EDU                                 ',
    #         '                                                  ',
    #         'ARTICLE-CHAPTER-TITLE...                          ',
    #         '                                                  ',
    #         'test-article-title                                ',
    #         '                                                  ',
    #         'PAGE-RANGE: test-range                            ',
    #         'PAGE-OTHER: test-other                            ',
    #         ]
    #     self.assertEqual(
    #         ''.join( expected_lst ),
    #         self.maker.make_notes_field( patron_email, item_chap_vol_title, item_page_range_other, item_other )
    #         )

    def test__make_notes_field( self ):
        """ Checks for proper spacing. """
        patron_email = 'a@a.edu'
        item_chap_vol_title = 'test-article-title'
        item_page_range_other = 'test-range'
        item_other = 'test-other'
        expected_lst = [
            'email: a@a.edu                                    ',  # 50 characters
            'EMAIL: A@A.EDU                                    ',
            '                                                  ',
            'ARTICLE-CHAPTER-TITLE...                          ',
            '                                                  ',
            'test-article-title                                ',
            '                                                  ',
            'PAGE-RANGE: test-range                            ',
            'PAGE-OTHER: test-other                            ',
            ]
        self.assertEqual(
            ''.join( expected_lst ),
            self.maker.make_notes_field( patron_email, item_chap_vol_title, item_page_range_other, item_other )
            )

    # end class class LasDataMakerTest


class SpacerTest( TestCase ):
    """ Checks spacer.py Spacer() """

    def setUp(self):
        self.spcr = Spacer()

    ## convert_string_to_lines() ##

    def test__convert_string_to_lines__short_blank(self):
        self.spcr.notes_line_length = 4
        self.assertEqual(
            [ '' ],
            self.spcr.convert_string_to_lines( ' ' )
            )

    def test__convert_string_to_lines__short(self):
        self.spcr.notes_line_length = 10
        self.assertEqual(
            [ 'abc' ],
            self.spcr.convert_string_to_lines( 'abc' )
            )

    def test__convert_string_to_lines__full(self):
        self.spcr.notes_line_length = 10
        self.assertEqual(
            ['1234567890'],
            self.spcr.convert_string_to_lines( '1234567890' )
            )

    def test__convert_string_to_lines__single_bigger(self):
        self.spcr.notes_line_length = 10
        self.assertEqual(
            [u'123456789012'],
            self.spcr.convert_string_to_lines( '123456789012' )
            )

    def test__convert_string_to_lines__single_bigger_plus_more_words(self):
        self.spcr.notes_line_length = 10
        self.assertEqual(
            ['123456789012', 'aaa'],
            self.spcr.convert_string_to_lines( '123456789012 aaa' )
            )

    def test__convert_string_to_lines__bigger_even_break(self):
        self.spcr.notes_line_length = 10
        self.assertEqual(
            ['1234567890', '123'],
            self.spcr.convert_string_to_lines( '1234567890 123' )
            )

    def test__convert_string_to_lines__bigger_uneven_break(self):
        self.spcr.notes_line_length = 10
        self.assertEqual(
            ['12345678', '012'],
            self.spcr.convert_string_to_lines( '12345678 012' )
            )

    def test__convert_string_to_lines__bigger_miscellaneous(self):
        self.spcr.notes_line_length = 50
        self.assertEqual( [
            'A surprisingly long TEST article-title, because',  # 47, would be 50
            'of the repetition of the surprisingly long',  # 42, would be 50
            'article title.'
            ],
            self.spcr.convert_string_to_lines( 'A surprisingly long TEST article-title, because of the repetition of the surprisingly long article title.' )
            )

    ## add_spacer() ##

    def test__add_spacer_small_string( self ):
        """ Tests filler in no-wrap situation. """
        self.spcr.notes_line_length = 10
        self.spcr.spacer_character = '|'
        self.assertEqual(
            'abc ||||| ',
            self.spcr.add_spacer( 'abc' )
            )

    def test__add_spacer_full_length_string( self ):
        """ Checks that full-string gets a full extra string added (ending in a space). """
        self.spcr.notes_line_length = 10
        self.spcr.spacer_character = '|'
        ten_characters = 'x' * 10
        expected_lst = [
            'xxxxxxxxxx',
            ' |||||||| '
            ]
        self.assertEqual(
            ''.join( expected_lst ),
            self.spcr.add_spacer( ten_characters )
            )

    def test__add_spacer_full_length_string_using_spaces( self ):
        """ Checks that full-string gets a full extra string added (ending in a space) when using expected spacer character of ' '. """
        self.spcr.notes_line_length = 10
        self.spcr.spacer_character = ' '
        ten_characters = 'x' * 10
        expected_lst = [
            'xxxxxxxxxx',
            '          '
            ]
        self.assertEqual(
            ''.join( expected_lst ),
            self.spcr.add_spacer( ten_characters )
            )

    def test__add_spacer_big_string( self ):
        """ Tests filler when wrapping. """
        self.spcr.notes_line_length = 10
        self.spcr.spacer_character = '|'
        fifteen_characters = 'x' * 15
        expected_lst = [
            'xxxxxxxxxx',
            'xxxxx ||| '
            ]
        self.assertEqual(
            ''.join( expected_lst ),
            self.spcr.add_spacer( fifteen_characters )
            )

    def test__add_spacer_big_string2( self ):
        """ Tests filler when wrapping will hit on a break. """
        self.spcr.notes_line_length = 50
        self.spcr.spacer_character = '|'
        long_text = '''A really long article title. A really long article title. A really long article title.'''
        expected_lst = [
            'A really long article title. A really long |||||| ',
            'article title. A really long article title. ||||| '
            ]
        self.assertEqual(
            ''.join( expected_lst ),
            self.spcr.add_spacer( long_text )
            )

    def test__add_spacer_big_string3( self ):
        """ Tests filler when wrapping will hit on a break2. """
        self.spcr.notes_line_length = 50
        self.spcr.spacer_character = '|'
        long_text = '''First line will break after (46th letter) THIS aanndd then continue.'''
        expected_lst = [
            'First line will break after (46th letter) THIS || ',
            'aanndd then continue. ||||||||||||||||||||||||||| '
            ]
        self.assertEqual(
            ''.join( expected_lst ),
            self.spcr.add_spacer( long_text )
            )

    def test__add_spacer_big_string4( self ):
        """ Tests filler when wrapping will hit on end-of-word.
            (Should breaking on the previous word.) """
        self.spcr.notes_line_length = 50
        self.spcr.spacer_character = '|'
        long_text = '''First line will break afterrrrr (50th letter) THIS and then continue.'''
        expected_lst = [
            'First line will break afterrrrr (50th letter) ||| ',
            'THIS and then continue. ||||||||||||||||||||||||| '
            ]
        self.assertEqual(
            ''.join( expected_lst ),
            self.spcr.add_spacer( long_text )
            )

    def test__add_spacer_big_string5( self ):
        """ Tests filler when wrapping will hit on end-of-word2.
            (Should breaking on the previous word.)
            For some reason the above passed and this initially didn't """
        self.spcr.notes_line_length = 50
        self.spcr.spacer_character = '|'
        long_text = 'A surprisingly long TEST article-title, because of the repetition of the surprisingly long article title.'
        expected_lst = [
            'A surprisingly long TEST article-title, because | ',
            'of the repetition of the surprisingly long |||||| '
            'article title. |||||||||||||||||||||||||||||||||| '
            ]
        self.assertEqual(
            ''.join( expected_lst ),
            self.spcr.add_spacer( long_text )
            )

    # end class SpacerTest()


class MagicBusPrepperTest( TestCase ):
    """ Tests magic_bus.py Prepper() """

    def test__make_filename_datestring( self ):
        """ Tests conversion of datetime object to string for filename. """
        dt = datetime.datetime( 2014, 12, 8, 15, 40, 59 )
        self.assertEqual(
            u'2014-12-08T15:40:59',
            prepper.make_filename_datestring( dt )
            )

    # end class MagicBusPrepperTest


class StatsBuilderTest( TestCase ):
    """ Tests models.py StatsBuilder() """

    def test__check_params( self ):
        """ Tests keys. """
        ## bad params
        qdict = QueryDict( u'', mutable=True ); qdict.update( {u'start': u'a', u'end': u'b'} )
        self.assertEqual( False, statsbuilder.check_params(qdict, u'server_name') )
        ## good params
        qdict = QueryDict( u'', mutable=True ); qdict.update( {u'start_date': 'a', u'end_date': 'b'} )
        self.assertEqual( True, statsbuilder.check_params(qdict, u'server_name') )

    def test__run_query( self ):
        """ Tests that scanrequest is found and returned. """
        sr = ScanRequest( item_title=u'foo' )
        sr.save()
        qdict = QueryDict( u'', mutable=True ); qdict.update( {u'start_date': datetime.date.today(), u'end_date': datetime.date.today()} )
        statsbuilder.check_params( qdict, u'server_name' )
        results = statsbuilder.run_query()
        self.assertEqual( 1, len(results) )


