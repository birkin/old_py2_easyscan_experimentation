# -*- coding: utf-8 -*-

""" Transports scan-request files to LAS location. """

import os


class Prepper( object ):
    """ Container for sender code. """

    def __init__( self ):
        self.source_transfer_dir_path = unicode( os.environ[u'EZSCAN__SOURCE_TRANSFER_DIR_PATH'] )
        self.filename_prefix = u'REQ-PARSED'
        self.data_file_suffix = u'.dat'
        self.count_file_suffix = u'.cnt'

    def make_data_files( self, datetime_object, data_string ):
        """ Creates data files that will be transferred to remote server.
            Job triggered by (we'll see). """
        self.ensure_empty_dir()
        filename_datestring = self.make_filename_datestring( datetime_object )
        self.save_data_file( filename_datestring, data_string )
        self.save_count_file( filename_datestring )
        return

    def ensure_empty_dir( self ):
        """ Raises exception if directory is not empty.
            Called by make_data_files() """
        if not os.listdir( self.source_transfer_dir_path ) == []:
            raise Exception( u'Source path `%s` must be empty.' % self.source_transfer_dir_path )

    def make_filename_datestring( self, datetime_object ):
        """ Returns formatted date string.
            Example returned format, `2014-12-08T15:40:59`.
            Called by make_data_files() """
        utf8_date_string = datetime_object.strftime( u'%Y-%m-%dT%H:%M:%S' )  # temp: REQ-PARSED_2014-09-29T13:10:02.dat
        date_string = utf8_date_string.decode( u'utf-8' )
        return date_string

    def save_data_file( self, filename_datestring, data_string ):
        """ Saves data file.
            Called by make_data_files() """
        filename = u'%s_%s%s' % ( self.filename_prefix, filename_datestring, self.data_file_suffix )
        filepath = u'%s/%s' % ( self.source_transfer_dir_path, filename )
        buffer1 = data_string.strip()
        buffer2 = buffer1 + u'\n'
        utf8_data_string = buffer2.encode( u'utf-8', u'replace' )
        with open( filepath, u'w' ) as f:
            f.write( utf8_data_string )
        return

    def save_count_file( self, filename_datestring ):
        """ Saves count file.
            Called by make_data_files() """
        filename = u'%s_%s%s' % ( self.filename_prefix, filename_datestring, self.count_file_suffix )
        filepath = u'%s/%s' % ( self.source_transfer_dir_path, filename )
        with open( filepath, u'w' ) as f:
            f.write( '1\n' )
        return

