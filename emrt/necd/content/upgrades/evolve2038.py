import plone.api as api


VOCABS = (
    'pollutants',
    'highlight',
)

def run(_):
    vocab_tool = api.portal.get_tool('portal_vocabularies')
    vocabs = tuple([vocab_tool[name] for name in VOCABS])
    api.content.delete(objects=vocabs)
