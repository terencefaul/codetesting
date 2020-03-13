from odoo import models, fields, api

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    is_portal_visible = fields.Boolean(string="Visible in Portal")
