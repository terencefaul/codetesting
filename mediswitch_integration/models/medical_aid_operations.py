
from odoo import fields, models, api , _
from suds.wsse import Security, UsernameToken
from suds.client import Client
from datetime import datetime,date
from odoo.http import request
from odoo.exceptions import MissingError , Warning
import xml.etree.ElementTree as ET
import time
import json
import requests

class MediswitchSubmitClaim(models.Model):
    _name = "mediswitch.submit.claim"
    _rec_name = 'name'

    name = fields.Char(string="Name")
    response_payload_date = fields.Datetime(string="Date")
    destination_code = fields.Char(string="Destination Code")
    user_reference = fields.Integer(string="User Reference")
    generated_payload = fields.Text(string="Payload")
    status = fields.Char(string="Status")
    switch_reference = fields.Char(string="Switch Reference")
    retry = fields.Integer(string="Retry")
    response_payload = fields.Text(string="Response Payload")
    force=fields.Integer(string="Force")
    invoice_id = fields.Many2one("account.invoice",string="Invoice Ref",readonly="1")
    fetch_claim_id=fields.One2many("mediswitch.fetch.claim",'claim_ref_id')
    status_morefiles = fields.Char(string="Status Of MoreFiles",invisible="1")
    response_error = fields.Text(string="Response Error")

    @api.multi
    def fetch_operations(self):
        if self.env.context.get('fetch_response'):
            invoice_ids = self.invoice_id
        else:
            invoice_ids = self.env['account.invoice'].search([('claim_level_mediswitch_status', 'in', ['01', '02'])])
        if self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.for_what') == 'test':
            username = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.user_name_test')
            password = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.password_test')
            package = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.package_test')
            url = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.test_url')
        else:
            username = self.env['ir.config_parameter'].sudo().get_param(
                'mediswitch_integration.user_name_production')
            password = self.env['ir.config_parameter'].sudo().get_param(
                'mediswitch_integration.password_production')
            package = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.package_production')
            url = self.env['ir.config_parameter'].sudo().get_param('mediswitch_integration.production_url')
        for invoice in invoice_ids:
            xml = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v2="http://gateway.switchonline.co.za/MediswitchGateway/v2">
                           <soapenv:Header/>
                           <soapenv:Body>
                              <v2:fetchOperation>
                                 <user>%s</user>
                                 <passwd>%s</passwd>
                                 <package>%s</package>
                                 <txType>302</txType>
                                 <swref>%s</swref>
                                 <force>%s</force>
                              </v2:fetchOperation>
                           </soapenv:Body>
                        </soapenv:Envelope>""" % (
                username, password, package, invoice.user_ref, 0)
            headers = {'Content-Type': 'text/xml', 'charset': 'utf-8'}
            response = requests.post(url, headers=headers, data=xml.encode('utf-8'))
            response_string = ET.fromstring(response.content)
            data_dict = {}
            responsepayload = False

            for node in response_string.iter():
                if node.tag == 'originalSwref':
                    data_dict.update({'origial_swref': node.text})
                elif node.tag == 'responsePayload':
                    data_dict.update({'response_payload': node.text})
                elif node.tag == 'feedbackType':
                    data_dict.update({'feedback_type': node.text})
                elif node.tag == 'feedbackVersion':
                    data_dict.update({'feedback_version': node.text})
                elif node.tag == 'moreFiles':
                    data_dict.update({'morefiles': int(node.text)})
                elif node.tag == 'originalUserRef':
                    data_dict.update({'original_userref': node.text})
                elif node.tag == 'originalDataSetId':
                    if node.text:
                        data_dict.update({'original_dataset_id': int(node.text)})
                elif node.tag == 'fileName':
                    data_dict.update({'filename': node.text})
                elif node.tag == 'fileDate':
                    data_dict.update({'filedate': node.text or date.today()})
                elif node.tag == 'message':
                    raise Warning(_(node.text))
                else:
                    data_dict.update({str(node.tag): node.text})
            claim_id = self.env['mediswitch.submit.claim'].search([('switch_reference', '=', invoice.user_ref)],
                                                                  limit=1)
            data_dict.update(
                {'claim_ref_id': claim_id.id})
            fetch_id = self.env['mediswitch.fetch.claim'].create(data_dict)
            if responsepayload:
                claim_status_lines = []
                lines = responsepayload.split("\n")
                strings = ("Invalid Missing", "Invalid")
                if any(s in lines[0] for s in strings):
                    raise Warning(_(lines[0]))
                if lines and lines[0] and lines[0].startswith('H'):
                    flag = 1
                    treatment_line = 0
                    balance_price = 0
                    approved_price = 0
                    total_approved_price = 0
                    list1 = []
                    number = 0
                    message = ''
                    for line in lines:
                        split_line = line.split("|")
                        if line.startswith('S'):
                            if int(line.split("|")[5]) > 0:
                                flag = 1
                        if line.startswith('R') and flag == 1:
                            rejection_count = split_line[2] + ' - ' + split_line[1]
                            fetch_id.response_error = rejection_count
                        if line.startswith('FR') and flag == 1:
                            rejection_count = split_line[1]
                            fetch_id.response_error = rejection_count
                        if line.startswith('P') and flag == 1:
                            message11, message2, message3 = self.claim_messages(split_line[13], split_line[14],
                                                                                split_line[15])
                            message = message3 + ' - ' + message11 + ', from ' + message2 + '\n'
                            invoice.claim_level_mediswitch_status = split_line[13]
                        if line.startswith('T') and flag == 1:
                            treatment_line += 1
                            message1, message2, message3 = self.claim_messages(split_line[14], split_line[15],
                                                                               split_line[16])
                            claim_status_lines.append(message1)
                        if line.startswith('Z'):
                            if split_line[18]:
                                approved_price = int(split_line[18]) / 100
                                total_approved_price += approved_price
                            if split_line[16]:
                                balance_price = int(split_line[16]) / 100
                            list1.append({'approve': approved_price, 'balance': balance_price})
                    if total_approved_price:
                        invoice.action_invoice_open()
                        vals = {}
                        accquire_id = self.env['payment.acquirer'].search([('name', '=', 'Mediswitch Payment Gateway')])
                        vals.update({
                            'amount': total_approved_price,
                            'currency_id': self.env.user.company_id.currency_id.id,
                            'partner_id': invoice.partner_id.id,
                            'invoice_ids': [(6, 0, invoice.ids)],
                            'state': 'done',
                        })
                        vals['acquirer_id'] = accquire_id.id
                        vals['reference'] = invoice.name
                        transaction = self.env['payment.transaction'].create(vals)
                        journal_id = request.env['account.journal'].sudo().search(
                            [('type', '=', 'bank')], limit=1)
                        payment_method_id = self.env['account.payment.method'].search(
                            [('name', '=', 'Manual'), ('payment_type', '=', 'outbound')], limit=1)
                        payments = {
                            'payment_type': 'inbound',
                            'partner_type': 'customer',
                            'partner_id': invoice.partner_id.id,
                            'amount': total_approved_price,
                            'journal_id': journal_id.id,
                            'payment_date': date.today(),
                            'communication': invoice.number,
                            'payment_method_id': payment_method_id.id,
                            'invoice_ids': [(4, invoice.id)],
                            'payment_transaction_id': transaction.id,
                        }
                        payment_id = self.env['account.payment'].create(payments)
                        payment_id.post()

                    for each in invoice.invoice_line_ids:
                        each.approved_amount = list1[number].get('approve')
                        each.balance_amount = list1[number].get('balance')
                        each.claim_status = claim_status_lines[number]
                        number += 1

    @api.model
    def create(self, vals):
        res = super(MediswitchSubmitClaim, self).create(vals)
        name = self.env['ir.sequence'].next_by_code('claim_sequence')
        if res.invoice_id and res.invoice_id.sequence_number_next and res.invoice_id.sequence_number_next_prefix:
            res.name = name + '-' + res.invoice_id.sequence_number_next_prefix + res.invoice_id.sequence_number_next
        else:
            res.name = name
        return res

class MediswitchFetchClaim(models.Model):
    _name="mediswitch.fetch.claim"
    _rec_name="origial_swref"

    claim_ref_id=fields.Many2one("mediswitch.submit.claim",string="Claim Ref",readonly="1")
    status=fields.Char(string="Fetch Status")
    feedback_type=fields.Char(string="Feedback Type")
    feedback_version=fields.Char(string="FeedBack Version")
    morefiles=fields.Integer(string="More Files")
    origial_swref=fields.Char(string="Switch Reference")
    original_userref=fields.Char(string="User Reference")
    original_dataset_id=fields.Integer(string="DataSet Id")
    filename=fields.Char(string="File Name")
    filedate=fields.Date(string="File Date")
    response_payload=fields.Text(string="Response Payload")
    response_error = fields.Text(string="Response Error")

class MarkToMsv(models.Model):
    _name = "mark.msv"

    name = fields.Char(readonly=1)

    def mark_to_msv(self):
        for id in self.env.context.get('active_ids'):
            id = self.env['res.partner'].browse(id)
            if not id.msv_later_button:
                id.msv_later_button = True
class BulkMsv(models.Model):
    _name = 'bulk.msv'

    name = fields.Char(readonly=1)

    def bulk_for_msv(self):
        for id in self.env.context.get('active_ids'):
            id = self.env['res.partner'].browse(id)
            if id.msv_later_button:
                id.msv_later_button = False