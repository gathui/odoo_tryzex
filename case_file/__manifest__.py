# -*- coding: utf-8 -*-
{
    'name': "Case File",

    'summary': """
        Store details on Case Files""",

    'description': """
        Long description of module's purpose
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
    'depends': ['mail', 'account','hr_expense'],

    # always loaded
    'data': [
        'data/ir_sequence.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/court.xml',
        'views/case_contact.xml',
        'views/case_file.xml',
        'views/case_document.xml',
        'views/hr_expense.xml',
        'views/account_move.xml',
        'views/case_act.xml',
        'views/menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
