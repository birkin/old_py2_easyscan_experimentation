# -*- coding: utf-8 -*-

import datetime, pprint
from django.http import QueryDict
from django.test import TestCase
from easyscan_app.models import LasDataMaker, ScanRequest, StatsBuilder
from easyscan_app.lib.magic_bus import Prepper


maker = LasDataMaker()
prepper = Prepper()
statsbuilder = StatsBuilder()


class LasDataMakerTest( TestCase ):
    """ Tests models.LasDataMaker() """

    def test__utf8list_to_utf8csv__str( self ):
        """ Tests good utf8 strings (required by csv module). """
        utf8_list = [ 'foo', 'bar', '“iñtërnâtiônàlĭzætiøn”' ]
        result = maker.utf8list_to_utf8csv( utf8_list )
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
            maker.utf8list_to_utf8csv( unicode_list )
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
            maker.make_date_string( dt )
            )

    def test__strip_stuff( self ):
        """ Tests removal of double-quotes and new-lines. """
        self.assertEqual(
            u"The title was 'Zen', I think.",
            maker.strip_stuff(u'The title was "Zen", I think.') )
        self.assertEqual(
            u'first line - second line',
            maker.strip_stuff(u'first line\nsecond line') )
        self.assertEqual(
            u'first line - second line',
            maker.strip_stuff(u'first line\rsecond line') )
        self.assertEqual(
            u"The title was 'Zen', I think.",
            maker.strip_stuff(u'The title was `Zen`, I think.') )

    # end class class LasDataMakerTest


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


