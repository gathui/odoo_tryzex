# -*- coding: utf-8 -*-
{
    'name': "CRM Custom",

    'summary': """
        Custom Modules for the CRM Modules""",

    'description': """
        Custom Modules for the CRM Modules.
    """,

    'author': "Odoo Marine",
    'website': "https://www.yourcompany.com",
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['crm'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/ke_county.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
