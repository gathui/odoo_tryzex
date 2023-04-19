# -*- coding: utf-8 -*-
{
    'name': "Case File",

    'summary': """
        Store details on Case Files""",

    'description': """
        Long description of module's purpose
    """,

    'author': "odooMarine",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail'],

    # always loaded
    'data': [
        'data/ir_sequence.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/case_file.xml',
        'views/menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
