import base64
import werkzeug
import odoo
import time
from odoo import http, _, tools
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv.expression import OR
import pprint
import random
import string
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from random import randint
import logging
from odoo.addons.web.controllers.main import Home, ensure_db
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.sale.controllers.portal import CustomerPortal as SaleCustomerPortal
from odoo.addons.account.controllers.portal import PortalAccount as AccountCustomerPortal

_logger = logging.getLogger(__name__)


class WebsiteCustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(WebsiteCustomerPortal, self)._prepare_portal_layout_values()
        download_count = request.env['ir.attachment'].sudo().search_count([
            ('is_portal_visible', '=', True)
        ])
        values.update({
            'download_count': download_count,
        })
        return values

    @http.route(['/my/downloads', '/my/downloads/page/<int:page>'], type='http', auth='user', website=True,
                sitemap=False)
    def my_downloads(self, page=1, filter_id=0, **kw):
        attachments = request.env['ir.attachment']
        domain = [
            ('is_portal_visible', '=', True)
        ]

        order_count = attachments.sudo().search_count(domain)
        pager = portal_pager(
            url="/my/downloads",
            url_args={},
            total=order_count,
            page=page,
            step=25
        )
        attachments = attachments.sudo().search(domain, limit=25, offset=pager['offset'])
        request.session['my_downloads_history'] = attachments.ids[:100]
        values = {
            'attachments': attachments,
            'pager': pager,
            'default_url': '/my/downloads',
            'page_display_name': 'Downloads',
            'page_name': "download",
            'filter_id': filter_id,
            'download_count': order_count,
        }
        return request.render('website_download_attachments.download', values)
