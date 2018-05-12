# -*- coding: utf-8 -*-
{
    'name': "FIT Synchronize Bank Information",

    'summary': """
Synchronize financial information through a service provider.
    """,

    'description': """
Module which provides connectivity to banking API.""",


    'author': "Fundament IT",
    'website': "https://www.fundament.it",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    #'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account_bank_statement_import',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/d_account_stages.xml',
        'data/d_login_stages.xml',
        'data/d_synchronise_stages.xml',
        'views/v_saltedge_account.xml',
        'views/v_saltedge_login.xml',
        'views/v_saltedge_login_wizard.xml',
        'views/v_saltedge_menu.xml',
        'views/v_saltedge_settings.xml',
        'views/v_saltedge_synchronise.xml',
        # 'views/v_saltedge_templates.xml',
    ],
    'qweb':['static/src/xml/*.xml'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "application": True,
    "installable": True,
}