import plone.api as api


def run(_):
    vocab_tool = api.portal.get_tool('portal_vocabularies')
    vocabs = tuple([vocab_tool[name] for name in ('pollutants', 'fuel')])
    api.content.delete(objects=vocabs)
