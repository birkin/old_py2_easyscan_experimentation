# -*- coding: utf-8 -*-

from django.test import TestCase
from easyscan_app.models import LasDataMaker


class LasDataMakerTest( TestCase ):
    """ Tests models.LasDataMaker(). """

    def test__utf8list_to_utf8csv__str( self ):
        """ Tests good utf8 strings (required by csv module). """
        maker = LasDataMaker()
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
        maker = LasDataMaker()
        unicode_list = [ u'foo', u'bar', u'“iñtërnâtiônàlĭzætiøn”' ]
        result = u'init'
        try:
            maker.utf8list_to_utf8csv( unicode_list )
        except Exception as e:
            result = unicode(e)
        self.assertEqual(
            u"entry `u'foo'` not of type str",
            result )
