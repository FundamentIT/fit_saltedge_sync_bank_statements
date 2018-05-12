# -*- coding: utf-8 -*-

import ast
# import datetime
import logging
import time
from datetime import datetime
from ..classes.c_transactions import FitSaltEdgeTransactions
from ..models.m_settings import FitSaltEdgeSettings
from odoo import models, fields, api, _
from odoo.addons.base.res.res_bank import sanitize_account_number
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FitSaltedgeSynchroniseModel(models.TransientModel):
    _name = 'fit.saltedge.synchronise'
    _description = 'Synchronise'
    _rec_name = 'id'
    _inherit = 'account.bank.statement.import'

    data_file = fields.Binary(string='Bank Statement File', required=False,
                              help='Get you bank statements in electronic format from your bank and select them here.')
    synchronise_account = fields.Many2one('fit.saltedge.account')
    synchronise_account_id = fields.Char('Account ID')
    synchronise_account_name = fields.Char('Account')
    synchronise_id = fields.Char('ID')
    synchronise_client_id = fields.Char('Client ID')
    synchronise_connect = fields.Html('Connect')
    synchronise_customer_id = fields.Char('Customer ID')
    synchronise_error = fields.Char('')
    synchronise_interactive_fields = fields.One2many('fit.saltedge.interactive.field', 'interactive_field_id', 'Interactive fields')
    synchronise_last_update = fields.Char('Last Update')
    synchronise_login_id = fields.Char('Login ID')
    synchronise_name = fields.Char('Name')
    synchronise_saltedge_stage = fields.Char('Stage')
    synchronise_state_check = fields.Char(compute='_compute_state')
    synchronise_state = fields.Many2one('fit.saltedge.synchronise.stage', group_expand='_get_synchronise_states',
                                        default=lambda self: self._get_stage_id_default())
    synchronise_status = fields.Text('Status', default='')
    synchronise_journal_fail = fields.Boolean(defualt=False)
    synchronise_statements_ids = fields.Text()
    synchronise_notifications = fields.Text()

    @api.multi
    @api.depends('synchronise_state')
    def _compute_state(self):
        state = self.env['fit.saltedge.synchronise.stage'].browse(self.synchronise_state.id)
        self.synchronise_state_check = str(state.display_name)
        print 'updated state check to: ' + str(state.display_name)

    @api.model
    def create(self, vals):
        _stage_initial = self._get_stage_id_default()
        _initial_sync_item = self.search([('synchronise_state','=',_stage_initial.id)], limit=1)
        if _initial_sync_item:
            return _initial_sync_item
        else:
            return super(FitSaltedgeSynchroniseModel, self).create(vals)

    def __update_account_last_sync_date(self):
        self.synchronise_account.account_latest_sync = datetime.today().date()

    @api.constrains('synchronise_saltedge_stage')
    def _check_state_finished(self):
        if self.synchronise_saltedge_stage == 'finish':
            print 'updated state check = finish, update state to success and start transaction update'
            self.write({'synchronise_state': self._get_stage_id_success().id})
            _c_saltedge_settings = FitSaltEdgeSettings(self.env).get_settings()
            _c_saltedge_transactions = FitSaltEdgeTransactions(self, _c_saltedge_settings)
            _c_saltedge_transactions.retrieve_transactions()
            self.__update_account_last_sync_date()
            self.write({'synchronise_saltedge_stage': 'transactions update'})

    @api.model
    def _get_stage_id_default(self):
        _stage = self.env['fit.saltedge.synchronise.stage'].search([('synchronise_stage_id', '=', 'initial')], limit=1)
        return _stage

    @api.model
    def _get_stage_id_start(self):
        _stage = self.env['fit.saltedge.synchronise.stage'].search([('synchronise_stage_id', '=', 'start')], limit=1)
        return _stage

    @api.model
    def _get_stage_id_success(self):
        _stage = self.env['fit.saltedge.synchronise.stage'].search([('synchronise_stage_id', '=', 'success')], limit=1)
        return _stage

    @api.model
    def _get_synchronise_states(self, stages, domain, order):
        _states = stages._search([], order=order, access_rights_uid=1)
        return stages.browse(_states)

    @api.multi
    def write(self, vals):
        st = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        vals['synchronise_last_update'] = st
        super(FitSaltedgeSynchroniseModel, self).write(vals)
        return True

    @api.multi
    def start_synchronization(self):
        try:
            # self.start_synchronization()
            self.synchronise_state = self._get_stage_id_start()
            # self.write({'synchronise_saltedge_stage': 'start'},)
            _c_saltedge_settings = FitSaltEdgeSettings(self.env).get_settings()
            _c_saltedge_transactions = FitSaltEdgeTransactions(self, _c_saltedge_settings)
            _c_saltedge_transactions.initialize_refresh()
        except:
            raise
        return True

    @api.multi
    def validate_synchronization(self):
        try:
            _c_saltedge_settings = FitSaltEdgeSettings(self.env).get_settings()
            _c_saltedge_transactions = FitSaltEdgeTransactions(self, _c_saltedge_settings)
            _c_saltedge_transactions.validate_credentials()
        except:
            raise

        return True

    @api.multi
    def retrieve_transactions(self):
        try:
            _c_saltedge_settings = FitSaltEdgeSettings(self.env).get_settings()
            _c_saltedge_transactions = FitSaltEdgeTransactions(self, _c_saltedge_settings)
            self.__update_account_last_sync_date()
            self.write({'synchronise_saltedge_stage': 'transactions update'})
            return _c_saltedge_transactions.retrieve_transactions()
        except:
            raise
            # return True

    @api.multi
    def retrieve_available_transactions(self):
        try:
            _c_saltedge_settings = FitSaltEdgeSettings(self.env).get_settings()
            _c_saltedge_transactions = FitSaltEdgeTransactions(self, _c_saltedge_settings)
            self.write({'synchronise_saltedge_stage': 'transactions update'})
            return _c_saltedge_transactions.retrieve_transactions()
        except:
            raise

    @api.multi
    def view_reconciliation(self):
        if self.synchronise_statements_ids:
            statement_ids = ast.literal_eval(self.synchronise_statements_ids)
            notifications = ast.literal_eval(self.synchronise_notifications)
            action = self.env.ref('account.action_bank_reconcile_bank_statements')
            return {
                'name': action.name,
                'tag': action.tag,
                'context': {
                    'statement_ids': statement_ids,
                    'notifications': notifications
                },
                'type': 'ir.actions.client',
            }

    @api.multi
    def create_journal(self):
        print '_c_saltedge_transactions'
        account_number = sanitize_account_number(self.synchronise_account_name)
        """ Calls a wizard that allows the user to carry on with journal creation """
        return {
            'name': 'Journal Creation',
            'type': 'ir.actions.act_window',
            # 'res_model': 'account.bank.statement.import.journal.creation',
            'res_model': 'account.journal',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                # 'statement_import_transient_id': self.ids[0],
                'default_bank_acc_number': account_number,
                'default_name': 'Bank' + ' ' + account_number,
                'default_currency_id': False,
                'default_type': 'bank',
            }
        }

    def _create_bank_statements(self, stmts_vals):
        """ Create new bank statements from imported values, filtering out already imported transactions, and returns data used by the reconciliation widget """
        BankStatement = self.env['account.bank.statement']
        BankStatementLine = self.env['account.bank.statement.line']

        # Filter out already imported transactions and create statements
        statement_ids = []
        ignored_statement_lines_import_ids = []
        for st_vals in stmts_vals:
            filtered_st_lines = []
            for line_vals in st_vals['transactions']:
                if 'unique_import_id' not in line_vals \
                        or not line_vals['unique_import_id'] \
                        or not bool(BankStatementLine.sudo().search([('unique_import_id', '=', line_vals['unique_import_id'])], limit=1)):
                    if line_vals['amount'] != 0:
                        # Some banks, like ING, create a line for free charges.
                        # We just skip those lines as there's a 'non-zero' constraint
                        # on the amount of account.bank.statement.line
                        filtered_st_lines.append(line_vals)
                else:
                    ignored_statement_lines_import_ids.append(line_vals['unique_import_id'])
                    # if 'balance_start' in st_vals:
                    #     st_vals['balance_start'] += float(line_vals['amount'])

            if len(filtered_st_lines) > 0:
                # Remove values that won't be used to create records
                st_vals.pop('transactions', None)
                for line_vals in filtered_st_lines:
                    line_vals.pop('account_number', None)
                # Create the satement
                st_vals['line_ids'] = [[0, False, line] for line in filtered_st_lines]
                statement_ids.append(BankStatement.create(st_vals).id)
        if len(statement_ids) == 0:
            raise UserError(_('All transactions already processed, nothing to do.'))

        # Prepare import feedback
        notifications = []
        num_ignored = len(ignored_statement_lines_import_ids)
        if num_ignored > 0:
            notifications += [{
                'type': 'warning',
                'message': _("%d transactions had already been imported and were ignored.") % num_ignored if num_ignored > 1 else _(
                    "1 transaction had already been imported and was ignored."),
                'details': {
                    'name': _('Already imported items'),
                    'model': 'account.bank.statement.line',
                    'ids': BankStatementLine.search([('unique_import_id', 'in', ignored_statement_lines_import_ids)]).ids
                }
            }]
        return statement_ids, notifications
