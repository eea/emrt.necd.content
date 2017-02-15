from Products.CMFCore.utils import getToolByName
from Products.ATVocabularyManager.config import SORT_METHOD_FOLDER_ORDER
from emrt.necd.content.constants import LDAP_SECTOREXP
from emrt.necd.content.constants import LDAP_SECRETARIAT


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


LDAP_SETTINGS = {
    'id': 'ldap-plugin',
    'title': 'LDAP',
    'login_attr': 'uid',
    'uid_attr': 'uid',
    'users_base': 'ou=Users,o=EIONET,l=Europe',
    'users_scope': 2,
    'roles': 'Authenticated',
    'groups_base': (
        'cn=extranet-necd-review,'
        'cn=extranet-necd,'
        'cn=extranet,'
        'ou=Roles,o=EIONET,l=Europe'
    ),
    'groups_scope': 2,
    'binduid': '',
    'bindpwd': '',
    'binduid_usage': 0,
    'LDAP_server': 'ldap3.eionet.europa.eu',
    'rdn_attr': 'uid',
    'local_groups': 0,
    'read_only': True,
}


LDAP_ROLE_MAPPING = {
    LDAP_SECTOREXP: 'SectorExpert',
    LDAP_SECRETARIAT: 'Manager',
}


MEMCACHED_ID = 'memcached'


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


def setup_memcached(portal):
    if 'memcached' not in portal.keys():
        try:
            oid = portal.manage_addProduct[
                'MemcachedManager'].manage_addMemcachedManager(MEMCACHED_ID)
        except Exception, err:
            logger.exception(err)
        else:
            cache = portal[MEMCACHED_ID]
            cache._settings['servers'] = ('127.0.0.1:11211', )
            cache._p_changed = True


def setup_ldap(portal):
    acl = portal['acl_users']
    acl.manage_addProduct['PloneLDAP'].manage_addPloneLDAPMultiPlugin(
        **LDAP_SETTINGS)
    ldap_plugin = acl[LDAP_SETTINGS['id']]
    ldap_acl = ldap_plugin._getLDAPUserFolder()
    for ldap_group, plone_role in LDAP_ROLE_MAPPING.items():
        ldap_acl.manage_addGroupMapping(ldap_group, plone_role)

    # enable memcache
    ldap_plugin.ZCacheable_setManagerId(manager_id=MEMCACHED_ID)


def setupVarious(context):
    """ various import steps for emrt.necd.content """
    portal = context.getSite()

    if context.readDataFile('emrt.necd.content_various.txt') is None:
        return

    prepareVocabularies(portal, context)
    enable_atd_spellchecker(portal)
    setup_memcached(portal)
    setup_ldap(portal)
