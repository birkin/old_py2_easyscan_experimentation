# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import csv, logging, pprint, StringIO
from easyscan_app.lib.spacer import Spacer


log = logging.getLogger(__name__)
spcr = Spacer()


class LasDataMaker( object ):
    """ Contains code to make comma-delimited las string.
        Called by models.ScanRequest.save() """

    def __init__( self ):
        pass

    def make_csv_string(
        self, date_string, patron_name, patron_barcode, patron_email, item_title, item_barcode, item_chap_vol_title, item_page_range_other, item_other ):
        """ Makes and returns csv string from database data.
            Called by models.ScanRequest.save() """
        modified_date_string = self.make_date_string( date_string )
        utf8_data_list = self.make_utf8_data_list(
            modified_date_string, item_barcode, self.strip_stuff(patron_name), patron_barcode, self.strip_stuff(item_title), patron_email, self.strip_stuff(item_chap_vol_title), self.strip_stuff(item_page_range_other), self.strip_stuff(item_other)
            )
        log.debug( 'LasDataMaker(); utf8_data_list, ```{0}```'.format(pprint.pformat(utf8_data_list)) )
        utf8_csv_string = self.utf8list_to_utf8csv( utf8_data_list )
        csv_unicode_string = utf8_csv_string.decode( 'utf-8' )
        return csv_unicode_string

    def make_date_string( self, datetime_object ):
        """ Will convert datetime_object to date format required by LAS.
            Example returned format, `Mon Dec 05 2014`.
            Called by make_csv_string() """
        utf8_date_string = datetime_object.strftime( '%a %b %d %Y' )
        date_string = utf8_date_string.decode( 'utf-8' )
        return date_string

    def strip_stuff( self, var ):
        """ Replaces various characters from field.
            Called by make_csv_string() """
        updated_var = var.replace( '"', "'" )
        updated_var = updated_var.replace( '\n', ' - ' )
        updated_var = updated_var.replace( '\r', ' - ' )
        updated_var = updated_var.replace( '`', "'" )
        return updated_var

    def make_utf8_data_list( self, modified_date_string, item_barcode, patron_name, patron_barcode, item_title, patron_email, item_chap_vol_title, item_page_range_other, item_other ):
        """ Assembles data elements in order required by LAS.
            Called by make_csv_string() """
        utf8_data_list = [
            'item_id_not_applicable'.encode( 'utf-8' ),
            item_barcode.encode( 'utf-8', 'replace' ),
            'ED'.encode( 'utf-8' ),
            'QS'.encode( 'utf-8' ),
            patron_name.encode( 'utf-8', 'replace' ),
            patron_barcode.encode( 'utf-8', 'replace' ),
            item_title.encode( 'utf-8', 'replace' ),
            modified_date_string.encode( 'utf-8', 'replace' ),
            self.make_notes_field( patron_email, item_chap_vol_title, item_page_range_other, item_other ).encode( 'utf-8', 'replace' )
            ]
        return utf8_data_list

    def make_notes_field( self, patron_email, item_chap_vol_title, item_page_range_other, item_other ):
        """ Assembles notes field.
            Called by make_utf8_data_list() """
        data = self.add_email( patron_email )
        data = self.add_article_chapter_title( data, item_chap_vol_title )
        data = self.add_page_range( data, item_page_range_other )
        data = self.add_other( data, item_other )
        log.debug( 'LasDataMaker(); data, ```{0}```'.format(data) )
        return data

    def add_email( self, patron_email ):
        """ Adds email.
            Called by make_utf8_notes_field() """
        line_1_start = 'PATRON_EMAIL...'
        line_1 = spcr.add_spacer( line_1_start )
        line_2_start = ' '
        line_2 = spcr.add_spacer( line_2_start )
        line_3_start = '{nrml} | {uppr}'.format( nrml=patron_email, uppr=patron_email.upper() )
        line_3 = spcr.add_spacer( line_3_start )
        line_4_start = ' '
        line_4 = spcr.add_spacer( line_4_start )
        data = line_1 + line_2 + line_3 + line_4
        log.debug( 'data, ```{0}```'.format(data) )
        return data

    def add_article_chapter_title( self, data, item_chap_vol_title ):
        """ Adds email.
            Called by make_utf8_notes_field() """
        line_1_start = 'ARTICLE-CHAPTER-TITLE...'
        line_1 = spcr.add_spacer( line_1_start )
        line_2_start = ' '
        line_2 = spcr.add_spacer( line_2_start )
        line_3_start = '{0}'.format( item_chap_vol_title )
        line_3 = spcr.add_spacer( line_3_start )
        line_4_start = ' '
        line_4 = spcr.add_spacer( line_4_start )
        data = data + line_1 + line_2 + line_3 + line_4
        log.debug( 'data, ```{0}```'.format(data) )
        return data

    def add_page_range( self, data, item_page_range_other ):
        """ Adds page-range.
            Called by make_utf8_notes_field() """
        line_start = 'PAGE-RANGE: {0}'.format(item_page_range_other)
        line = spcr.add_spacer( line_start )
        data = data + line
        log.debug( 'data, ```{0}```'.format(data) )
        return data

    def add_other( self, data, item_other ):
        """ Adds other info.
            Called by make_utf8_notes_field() """
        line_start = 'PAGE-OTHER: {0}'.format(item_other)
        line = spcr.add_spacer( line_start )
        data = data + line
        log.debug( 'data, ```{0}```'.format(data) )
        return data

    def utf8list_to_utf8csv( self, utf8_data_list ):
        """ Converts list into utf8 string.
            Called by make_csv_string()
            Note; this python2 csv module requires utf-8 strings. """
        log.debug( 'utf8_data_list, ```{0}```'.format(pprint.pformat(utf8_data_list)) )
        for entry in utf8_data_list:
            if not type(entry) == str:
                raise Exception( 'entry `%s` not of type str' % unicode(repr(entry)) )
        io = StringIO.StringIO()
        writer = csv.writer( io, delimiter=','.encode('utf-8'), quoting=csv.QUOTE_ALL )
        writer.writerow( utf8_data_list )
        csv_string = io.getvalue()  # csv_string is a byte-string
        log.debug( 'type(csv_string), `{0}'.format( type(csv_string) ) )
        log.debug( 'csv_string, ```{0}```'.format( csv_string.decode('utf-8') ) )
        io.close()
        return csv_string

    # end class LasDataMaker()
