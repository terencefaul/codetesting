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
    'name': 'Website Attachments Download',
    'summary': 'Website Attachments Download',
    'version': '1.0',
    'description': """Website Attachments Download""",
    'author': 'Humint Business Information Systems',
    'category': 'Website',
    'website': "http://www.humint.co.za",
    'depends': ['base', 'website','portal'],
    'data': [
        'views/attachment.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
