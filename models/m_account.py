import json
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

from collections import namedtuple


class FitSaltedgeAccountModel(models.Model):
    _name = 'fit.saltedge.account'
    _description = 'Account'
    _rec_name = 'account_id'
    _inherit = ['ir.needaction_mixin']

    account_currency_id = fields.Many2one('res.currency', string='Currency')
    account_id = fields.Integer(0)
    account_login_id = fields.Integer(0)
    account_name = fields.Char('Name')
    account_balance = fields.Monetary('Balance', currency_field='account_currency_id', )
    account_nr_transactions = fields.Integer(0)
    account_latest_sync = fields.Date('Latest sync')
    account_latest_sync_id = fields.Integer('Latest sync ID')
    account_nature = fields.Char('Type')
    account_active = fields.Boolean('Active?', default=False)
    account_status = fields.Char('Status', default='Inactive')

    # @api.model
    # def _needaction_domain_get(self):
    #     count = int(self.search_count([]))
    #     return [('account_id', '!=', '0')]

    @api.model
    def _needaction_count(self, domain=None):
        count = int(self.search_count([]))
        return count

    @api.multi
    def fit_account_activate(self):
        for account in self:
            account.account_active = not account.account_active
            if account.account_active:
                account.account_status = 'Active'
            else:
                account.account_status = 'Inactive'
        return {
            'name': 'Account Overview',
            'view_type': 'form',
            'view_mode': 'kanban,form',
            'res_model': 'fit.saltedge.account',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'nodestroy': True
        }

    @api.multi
    def write(self, vals):
        active = True if vals.get('account_status') == 'Active' else False
        if active:
            count = int(self.search_count([('account_status', '=', 'Active')]))
            if count > 0:
                raise UserError(_('Error while activating account, only one active account allowed.'))

        vals['account_active'] = active
        super(FitSaltedgeAccountModel, self).write(vals)

    def unlink(self):
        try:
            super(FitSaltedgeAccountModel, self).unlink()
            self.env['bus.bus'].sendone('auto_refresh', 'ir.ui.menu')
        except BaseException as e:
            print 'error: '+str(e)
        # def refresh_accounts(self, saltedge_customer):
    #     response = self.settings.app.get(
    #         'https://www.saltedge.com/api/v4/accounts?customer_id=' + str(saltedge_customer.customer_id))
    #
    #     if response.status_code == 200:
    #         json_data = json.loads(response.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
    #
    #         if len(json_data.data) == 0:
    #             self.settings.settings_status += '\n' + str(fields.Datetime.now()) + ' No accounts found'
    #         else:
    #             self.settings.settings_status += '\n' + str(
    #                 fields.Datetime.now()) + ' Accounts retrieved, start update'
    #             for account in json_data.data:
    #                 self.refresh_account(account)
    #
    # def refresh_account(self, account):
    #     existing_account = self.settings.env['fit.saltedge.account'].search([['account_id', '=', account.id]])
    #     if len(existing_account.ids) > 0:
    #         self.update_account(account, existing_account)
    #         print 'existing_account: '
    #     else:
    #         self.create_account(account)
    #
    #     print account.login_id
    #     print account.id
    #
    # def create_account(self, account):
    #     self.settings.env['fit.saltedge.account'].create(
    #         {'account_id': account.id,
    #          'account_login_id': account.login_id,
    #          'account_name': account.name,
    #          'account_balance': account.balance,
    #          'account_nr_transactions': account.extra.transactions_count.posted,
    #          'account_nature': account.nature
    #          }
    #     )
    #     self.settings.settings_status += '\n' + str(fields.Datetime.now()) + ' New account created, id: ' + str(
    #         account.id)
    #
    # def update_account(self, account, existing_account):
    #     existing_account.write(
    #         {'account_id': account.id,
    #          'account_login_id': account.login_id,
    #          'account_name': account.name,
    #          'account_balance': account.balance,
    #          'account_nr_transactions': account.extra.transactions_count.posted,
    #          'account_nature': account.nature
    #          }
    #     )
    #     self.settings.settings_status += '\n' + str(fields.Datetime.now()) + ' Account updated, id: ' + str(
    #         account.id)


class FitSaltEdgeAccount:
    def __init__(self, settings):
        self.settings = settings

    def refresh_accounts(self):

        response = self.settings.app.get(
            'https://www.saltedge.com/api/v4/accounts?customer_id=' + str(self.settings.settings_customer_id))

        if response.status_code == 200:
            json_data = json.loads(response.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))

            if len(json_data.data) == 0:
                self.settings.settings_status += '\n' + str(fields.Datetime.now()) + ' No accounts found'
            else:
                self.settings.settings_status += '\n' + str(
                    fields.Datetime.now()) + ' Accounts retrieved, start update'
                for account in json_data.data:
                    self._refresh_account(account)

    def _refresh_account(self, account):
        existing_account = self.settings.env['fit.saltedge.account'].search([['account_id', '=', account.id]])
        if len(existing_account.ids) > 0:
            self._update_account(account, existing_account)
        else:
            self._create_account(account)

        print account.login_id
        print account.id

    def _create_account(self, account):
        self.settings.env['fit.saltedge.account'].create(
            {'account_id': account.id,
             'account_login_id': account.login_id,
             'account_name': account.name,
             'account_balance': account.balance,
             'account_nr_transactions': account.extra.transactions_count.posted,
             'account_nature': account.nature
             }
        )
        self.settings.settings_status += '\n' + str(fields.Datetime.now()) + ' New account created, id: ' + str(
            account.id)

    def _update_account(self, account, existing_account):
        existing_account.write(
            {'account_id': account.id,
             'account_login_id': account.login_id,
             'account_name': account.name,
             'account_balance': account.balance,
             'account_nr_transactions': account.extra.transactions_count.posted,
             'account_nature': account.nature
             }
        )
        self.settings.settings_status += '\n' + str(fields.Datetime.now()) + ' Account updated, id: ' + str(
            account.id)
