# -*- coding: utf-8 -*-

from django.contrib import admin
from easyscan_app.models import ScanRequest


class ScanRequestAdmin( admin.ModelAdmin ):
    date_hierarchy = u'create_datetime'
    ordering = [ u'id' ]
    list_display = [
        u'id', u'create_datetime',
        u'item_title', u'item_barcode', u'item_callnumber', u'item_volume_year', u'item_chap_vol_title', u'item_source_url', u'item_page_range_other', u'item_other',
        u'patron_name', u'patron_barcode', u'patron_email',
        u'las_conversion' ]
    # list_filter = [ u'patron_barcode' ]
    search_fields = [
        u'id', u'create_datetime',
        u'item_title', u'item_barcode', u'item_callnumber', u'item_volume_year', u'item_chap_vol_title', u'item_source_url', u'item_page_range_other', u'item_other',
        u'patron_name', u'patron_barcode', u'patron_email',
        u'las_conversion' ]
    readonly_fields = [
        u'id', u'create_datetime',
        u'item_title', u'item_barcode', u'item_callnumber', u'item_volume_year', u'item_chap_vol_title', u'item_source_url', u'item_page_range_other', u'item_other',
        u'patron_name', u'patron_barcode', u'patron_email',
        u'las_conversion' ]


admin.site.register( ScanRequest, ScanRequestAdmin )
