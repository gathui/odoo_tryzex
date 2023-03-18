# -*- coding: utf-8 -*-
{
    'name': "mpesa_base",

    'summary': """
       Hold Base Functionality for MPesa""",

    'description': """
        Implement functionality for the various Paybill Accounts in the Organisation
    """,

    'author': "James Nguyo",
    'website': "http://www.sanergy.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/rules.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron.xml',
        'views/settings.xml',
        'views/mpesa.xml',
        'views/mpesa_reconcile.xml',
        'views/menus.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
