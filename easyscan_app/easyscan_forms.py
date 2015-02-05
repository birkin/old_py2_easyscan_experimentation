# -*- coding: utf-8 -*-

from django import forms


class CitationForm( forms.Form ):
    article_chapter_title = forms.CharField(
        label=u'Article/Chapter title (required)', max_length=500, widget=forms.Textarea( attrs={'rows':2, 'cols':50} )
        )
    page_range = forms.CharField(
        label=u'Page range (required)', max_length=500, widget=forms.Textarea( attrs={'rows':2, 'cols':50} )
        )
    other = forms.CharField(
        label=u'Other (optional)', required=False, max_length=500, widget=forms.Textarea( attrs={'rows':2, 'cols':50} )
        )
