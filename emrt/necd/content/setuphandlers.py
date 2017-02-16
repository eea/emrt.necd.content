import logging

from zope.component.hooks import getSite

from Products.CMFCore.utils import getToolByName
from Products.ATVocabularyManager.config import SORT_METHOD_FOLDER_ORDER

from emrt.necd.content.constants import LDAP_SECTOREXP
from emrt.necd.content.constants import LDAP_SECRETARIAT


LOGGER = logging.getLogger('emrt.necd.content.setuphandlers')


VOCABULARIES = [
    {'id': 'eea_member_states',
     'title': 'EEA Member States',
     'filename': 'eea_member_states.csv',
    },
    {'id': 'ghg_source_category',
     'title': 'NFR category group',
     'filename': 'ghg_source_category.csv',
    },
    {'id': 'ghg_source_sectors',
     'title': 'NFR Sector',
     'filename': 'ghg_source_sectors.csv',
    },
    {'id': 'fuel',
     'title': 'Fuel',
     'filename': 'fuel.csv',
    },
    {'id': 'pollutants',
     'title': 'Pollutants',
     'filename': 'pollutants.csv',
    },
    {'id': 'highlight',
     'title': 'Highligt',
     'filename': 'highlight.csv',
    },
    {'id': 'parameter',
     'title': 'Parameter',
     'filename': 'parameter.csv',
    },
    {'id': 'conclusion_reasons',
     'title': 'Conclusion Reasons',
     'filename': 'conclusion_reasons.csv',
    },
]


LDAP_ROLE_MAPPING = {
    LDAP_SECTOREXP: 'SectorExpert',
    LDAP_SECRETARIAT: 'Manager',
}


def create_vocabulary(
        context, vocabname, vocabtitle, importfilename=None, profile=None):
    _ = context.invokeFactory(
        id=vocabname, title=vocabtitle, type_name='SimpleVocabulary')

    vocabulary = context.getVocabularyByName(vocabname)
    vocabulary.setSortMethod(SORT_METHOD_FOLDER_ORDER)
    wtool = getToolByName(context, 'portal_workflow')
    wtool.doActionFor(vocabulary, 'publish')
    from logging import getLogger
    log = getLogger('create_vocabulary')
    log.info('Created %s vocabulary' % vocabname)
    if importfilename is not None:
        data = profile.readDataFile(importfilename, subdir='necdvocabularies')
        vocabulary.importCSV(data)

    for term in vocabulary.values():
        wtool.doActionFor(term, 'publish')

    log.info('done')


def prepareVocabularies(context, profile):
    """ initial population of vocabularies """

    atvm = getToolByName(context, 'portal_vocabularies')

    for vocabulary in VOCABULARIES:
        vocab = atvm.getVocabularyByName(vocabulary.get('id'))
        if vocab is None:
            create_vocabulary(
                atvm,
                vocabulary.get('id'),
                vocabulary.get('title'),
                vocabulary.get('filename', None),
                profile
            )


def enable_atd_spellchecker(portal):
    tinymce = getToolByName(portal, 'portal_tinymce')
    tinymce.libraries_spellchecker_choice = u'AtD'
    tinymce.libraries_atd_service_url = u'service.afterthedeadline.com'


def setup_memcached(portal, memcached_id):
    if memcached_id not in portal.keys():
        try:
            _ = portal.manage_addProduct[
                'MemcachedManager'].manage_addMemcachedManager(memcached_id)
        except Exception, err:
            LOGGER.exception(err)
        else:
            cache = portal[memcached_id]
            cache._settings['servers'] = ('127.0.0.1:11211', )
            cache._p_changed = True


def setup_ldap(portal, ldap_id, memcached_id):
    acl = portal['acl_users']
    ldap_plugin = acl[ldap_id]

    # map LDAP roles to Plone roles
    ldap_acl = ldap_plugin._getLDAPUserFolder()
    for ldap_group, plone_role in LDAP_ROLE_MAPPING.items():
        ldap_acl.manage_addGroupMapping(ldap_group, plone_role)

    # enable memcached
    ldap_plugin.ZCacheable_setManagerId(manager_id=memcached_id)

    # disable unnecessary PAS LDAP plugins
    enabled_interfaces = (
        'IUserEnumerationPlugin',
        'IGroupsPlugin',
        'IGroupEnumerationPlugin',
        'IRoleEnumerationPlugin',
        'IAuthenticationPlugin',
        'IPropertiesPlugin',
        'IRolesPlugin',
        'IGroupIntrospection',
        # Commenting out disabled plugins for reference.
        # 'ICredentialsResetPlugin',
        # 'IGroupManagement',
        # 'IUserAdderPlugin',
        # 'IUserManagement',
    )

    # activate selected plugins
    ldap_plugin.manage_activateInterfaces(enabled_interfaces)

    # move LDAP Properties plugin to top
    plugins = acl['plugins']
    active_plugins = plugins.getAllPlugins('IPropertiesPlugin')['active']
    interface = plugins._getInterfaceFromName('IPropertiesPlugin')

    for _ in range(len(active_plugins) - 1):
        # need to move it one position at a time
        plugins.movePluginsUp(interface, [ldap_id])


def post_install(context):
    memcached_id = 'memcached'
    portal = getSite()
    setup_memcached(portal, memcached_id)
    setup_ldap(portal, 'ldap-plugin', memcached_id)


def setupVarious(context):
    """ various import steps for emrt.necd.content """
    portal = context.getSite()

    if context.readDataFile('emrt.necd.content_various.txt') is None:
        return

    prepareVocabularies(portal, context)
    enable_atd_spellchecker(portal)
