# -*- coding: utf-8 -*-
from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('kotti_rdbt')

def kotti_configure(settings):

    settings['pyramid.includes'] += ' kotti_rdbt kotti_rdbt.views'
    settings['kotti.available_types'] += ' kotti_rdbt.resources.RDBTable kotti_rdbt.resources.RDBTableColumn'


def includeme(config):
    pass
    #config.add_translation_dirs('kotti_rdbt:locale')
