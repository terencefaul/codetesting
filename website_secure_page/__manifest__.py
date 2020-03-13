# -*- coding: utf-8 -*-
#################################################################################
# Author      : Humint Business Information Systems (<www.humint.co.za>)
# Copyright(c): 2019 Humint Business Information Systems
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

{
    'name': 'Website Secure Page',
    'summary': 'Website Secure Page',
    'version': '1.0',
    'description': """Website Secure Page""",
    'author': 'Humint Business Information Systems',
    'category': 'Website',
    'website': "http://www.humint.co.za",
    'depends': ['base','website'],
    'data': [
'views/assets.xml',
        'views/templates.xml',
    ],
    'qweb': ['static/src/xml/website_page.xml'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
