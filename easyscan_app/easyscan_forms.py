# -*- coding: utf-8 -*-

from django import forms


class CitationForm( forms.Form ):
    article_chapter_title = forms.CharField( label=u'Article/Chapter title...', max_length=500 )
    page_range = forms.CharField(
        label=u'Page range...', max_length=500, widget=forms.Textarea( attrs={'rows':2, 'cols':50} )
        )
