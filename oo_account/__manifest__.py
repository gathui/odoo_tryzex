# -*- coding: utf-8 -*-
{
    'name': "Journal Entry Import Template",

    'summary': """
        Adds Journal Entry Import Template.""",

    'description': """
        - Adds Journal Entry Import Template
    """,

    'author': "Teclea Limited",
    'category': 'Accounting',
    'version': '0.1',

    'depends': ['account',],

    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
    ],

    'installable': True,
}
