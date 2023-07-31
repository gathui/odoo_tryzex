# -*- coding: utf-8 -*-
{
    'name': "Employment",

    'summary': """
        Employment Related Modules""",

    'description': """
        Employment Related Modules including Minimum Wage Calculation
    """,

    'author': "Odoo Marine",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['case_file'],

    # always loaded
    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/minimum_wage.xml',
        'views/menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
