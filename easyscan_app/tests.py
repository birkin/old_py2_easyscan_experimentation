# -*- coding: utf-8 -*-

import datetime, pprint
from django.http import QueryDict
from django.test import TestCase
from easyscan_app.models import LasDataMaker, ScanRequest, StatsBuilder
from easyscan_app.lib.magic_bus import Prepper
from easyscan_app.lib.spacer import Spacer


# maker = LasDataMaker()
prepper = Prepper()
statsbuilder = StatsBuilder()


class LasDataMakerTest( TestCase ):
    """ Tests models.LasDataMaker() """

    def setUp(self):
        self.maker = LasDataMaker()

    def test__utf8list_to_utf8csv__str( self ):
        """ Tests good utf8 strings (required by csv module). """
        utf8_list = [ b'foo', b'bar', b'“iñtërnâtiônàlĭzætiøn”' ]
        result = self.maker.utf8list_to_utf8csv( utf8_list )
        self.assertEqual(
            '"foo","bar","\xe2\x80\x9ci\xc3\xb1t\xc3\xabrn\xc3\xa2ti\xc3\xb4n\xc3\xa0l\xc4\xadz\xc3\xa6ti\xc3\xb8n\xe2\x80\x9d"\r\n',
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

    def test__add_spacer_small_string( self ):
        """ Tests filler in no-wrap situation. """
        self.maker.notes_line_length = 10
        self.maker.spacer_character = '|'
        self.assertEqual(
            'abc ||||| ',
            self.maker.add_spacer( 'abc' )
            )

    def test__add_spacer_big_string( self ):
        """ Tests filler when wrapping. """
        self.maker.notes_line_length = 10
        self.maker.spacer_character = '|'
        fifteen_characters = 'x' * 15
        self.assertEqual(
            'xxxxxxxxxxxxxxx ||| ',
            self.maker.add_spacer( fifteen_characters )
            )

    def test__add_spacer_big_string2( self ):
        """ Tests filler when wrapping will hit on a break. """
        self.maker.notes_line_length = 50
        self.maker.spacer_character = '|'
        long_text = '''A really long article title. A really long article title. A really long article title.'''
        self.assertEqual(
            'A really long article title. A really long |||||| article title. A really long article title. ||||| ',
            self.maker.add_spacer( long_text )
            )

    def test__add_spacer_big_string3( self ):
        """ Tests filler wrapping will hit on a break2. """
        self.maker.notes_line_length = 50
        self.maker.spacer_character = '|'
        long_text = '''First line will break after (46th letter) THIS aanndd then continue.'''
        self.assertEqual(
            'First line will break after (46th letter) THIS || aanndd then continue. ||||||||||||||||||||||||||| ',
            self.maker.add_spacer( long_text )
            )

    def test__add_spacer_big_string4( self ):
        """ Tests filler wrapping will hit on end-of-word.
            (Ends up breaking on the previous word.) """
        self.maker.notes_line_length = 50
        self.maker.spacer_character = '|'
        long_text = '''First line will break afterrrrr (50th letter) THIS and then continue.'''
        self.assertEqual(
            'First line will break afterrrrr (50th letter) ||| THIS and then continue. ||||||||||||||||||||||||| ',
            self.maker.add_spacer( long_text )
            )

    def test__add_spacer_full_length_string( self ):
        """ Checks that full-string gets a full extra string added (ending in a space). """
        self.maker.notes_line_length = 10
        self.maker.spacer_character = '|'
        ten_characters = 'x' * 10
        self.assertEqual(
            'xxxxxxxxxx |||||||| ',
            self.maker.add_spacer( ten_characters )
            )

    def test__add_spacer_full_length_string_using_spaces( self ):
        """ Checks that full-string gets a full extra string added (ending in a space) when using expected spacer character of ' '. """
        self.maker.notes_line_length = 10
        self.maker.spacer_character = ' '
        ten_characters = 'x' * 10
        self.assertEqual(
            'xxxxxxxxxx          ',
            self.maker.add_spacer( ten_characters )
            )

    def test__add_email( self ):
        """ Checks for space before and after actual email line. """
        self.maker.notes_line_length = 20
        self.maker.spacer_character = '|'
        email = 'a@a.edu'
        expected_lst = [
            'PATRON_EMAIL... ||| ',
            ' |||||||||||||||||| ',
            'a@a.edu | A@A.EDU | ',
            ' |||||||||||||||||| '
            ]
        self.assertEqual(
            ''.join( expected_lst ),
            self.maker.add_email( email )
            )


    # end class class LasDataMakerTest


class SpacerTest( TestCase ):
    """ Checks spacer.py Spacer() """

    def setUp(self):
        self.spcr = Spacer()

    def test__convert_string_to_lines__short(self):
        self.spcr.notes_line_length = 10
        self.assertEqual(
            [ 'abc' ],
            self.spcr.convert_string_to_lines( 'abc' )
            )

    def test__convert_string_to_lines__full(self):
        self.spcr.notes_line_length = 10
        self.assertEqual(
            ['1234567890', ''],
            self.spcr.convert_string_to_lines( '1234567890' )
            )

    def test__convert_string_to_lines__single_bigger(self):
        self.spcr.notes_line_length = 10
        self.assertEqual(
            ['foo', ''],
            self.spcr.convert_string_to_lines( '123456789012' )
            )

    def test__convert_string_to_lines__single_bigger_plus_more_words(self):
        self.spcr.notes_line_length = 10
        self.assertEqual(
            ['foo', ''],
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

    # def test__add_spacer_small_string( self ):
    #     """ Tests filler in no-wrap situation. """
    #     self.spcr.notes_line_length = 10
    #     self.spcr.spacer_character = '|'
    #     expected_lst = [
    #         'abc ||||| '
    #         ]
    #     self.assertEqual(
    #         ''.join( expected_lst ),
    #         self.spcr.add_spacer( 'abc' )
    #         )

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


