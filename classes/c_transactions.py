import json
import logging
from collections import namedtuple
from datetime import datetime
from time import strftime

from dateutil.relativedelta import relativedelta
from flask import json

from c_saltedge import SaltEdge
from odoo import fields, _
from odoo.addons.base.res.res_bank import sanitize_account_number
from odoo.exceptions import UserError, RedirectWarning
from schwifty import IBAN
from schwifty import BIC

_logger = logging.getLogger(__name__)


class FitSaltEdgeTransactions:
    def __init__(self, synchronise_item, settings):
        self.synchronise_item = synchronise_item
        self.settings = settings
        self.currency_code = 'EUR'
        self.account_number = None
        self.account_balance = None

    def _add_from_and_to_date(self, payload, _m_active_account):
        _current_latest_sync_date = _m_active_account.account_latest_sync
        payload = json.loads(payload)
        if not _current_latest_sync_date:
            _past_date = datetime.today().date() + relativedelta(months=-2) + relativedelta(days=+2)
            _tomorrow_date = datetime.today().date() + relativedelta(days=+1)
            from_date = {u'from_date': str(_past_date)}
            to_date = {u'to_date': str(_tomorrow_date)}
            payload[u'data'].update(from_date)
            payload[u'data'].update(to_date)
        else:
            _current_latest_sync_date = datetime.strptime(_current_latest_sync_date, '%Y-%m-%d')
            _maximum_date = _current_latest_sync_date + relativedelta(months=+2) + relativedelta(days=+1)
            _tomorrow_date = datetime.today().date() + relativedelta(days=+1)
            _is_valid_date = _tomorrow_date < _maximum_date.date()
            if _is_valid_date:
                from_date = {u'from_date': str(_current_latest_sync_date.date())}
                to_date = {u'to_date': str(_tomorrow_date)}
                payload[u'data'].update(from_date)
                payload[u'data'].update(to_date)
        return json.dumps(payload)

    def __add_unique_id(self, payload, environment_url):
        payload = json.loads(payload)
        sync_id = {u'sync_id': self.synchronise_item.id, u'fit_env': environment_url}
        custom_fields = {u'custom_fields': sync_id}
        payload[u'data'].update(custom_fields)
        return json.dumps(payload)

    def __is_valid_iban(self, account_nr):
        try:
            IBAN(account_nr)
            print 'VALID IBAN: ' + account_nr
            return True
        except ValueError as e:
            print 'INVALID IBAN: ' + str(e)
            return False

    def __get_compact_iban(self, account_nr):
        _iban = IBAN(account_nr)
        return _iban.compact

    def _generate_unique_name(self):
        return strftime('%Y%m%d%H%M%S_FIT_BANK_STATEMENT')

    def _get_inactive_accounts(self):
        inactive_accounts = self.synchronise_item.env['fit.saltedge.account'].search([['account_status', '=', 'Inactive']])
        inactive_accounts_result = list()
        for inactive_account in inactive_accounts:
            inactive_accounts_result.append(inactive_account.account_id)
        return inactive_accounts_result

    def initialize_refresh(self):
        try:
            self.synchronise_item.write({'synchronise_error': ''})
            app = SaltEdge(self.settings.settings_client_id, self.settings.settings_app_id, self.settings.settings_service_secret)
            inactive_accounts = self._get_inactive_accounts()
            payload = json.dumps({'data': {"fetch_scopes": ["accounts","transactions"], "exclude_accounts": inactive_accounts}})
            payload = self.__add_unique_id(payload, self.settings.settings_environment_url)

            active_accounts = self.synchronise_item.env['fit.saltedge.account'].search([['account_status', '=', 'Active']], limit=1)
            if len(active_accounts) == 0:
                stage = self.synchronise_item.env['fit.saltedge.synchronise.stage'].sudo().search(
                    [('synchronise_stage_id', '=', 'done')], limit=1)
                self.synchronise_item.write({
                    'synchronise_status': 'No active accounts',
                    'synchronise_state': stage.id})
            else:
                _m_active_account = active_accounts[0]
                print _m_active_account.account_name
                print _m_active_account.account_status
                print _m_active_account.account_id
                print _m_active_account.account_login_id
                print _m_active_account.account_latest_sync
                synchronise_status = str(fields.Datetime.now()) + ' Initializing account refresh, please wait.'
                self.synchronise_item.write({'synchronise_account_name': _m_active_account.account_name,
                                             'synchronise_account_id': _m_active_account.account_id,
                                             'synchronise_account': _m_active_account.id,
                                             'synchronise_client_id': self.settings.settings_client_id,
                                             'synchronise_customer_id': self.settings.settings_customer_id,
                                             'synchronise_login_id': _m_active_account.account_login_id,
                                             'synchronise_status': synchronise_status})

                _account_number = sanitize_account_number(_m_active_account.account_name)
                currency, journal = self.synchronise_item._find_additional_data(self.currency_code, _account_number)
                if not journal:
                    self.synchronise_item.write({'synchronise_journal_fail': True,
                                                 'synchronise_error': _('Journal for bank account: %s not available, please create journal '
                                                                        'first.') % (_account_number)})
                    return False

                payload = self._add_from_and_to_date(payload, _m_active_account)
                response = app.put(
                    'https://www.saltedge.com/api/v4/logins/' + str(_m_active_account.account_login_id) + '/refresh', payload)

                synchronise_status = str(self.synchronise_item.synchronise_status)
                synchronise_status += '\n' + str(fields.Datetime.now())

                if response.status_code == 200:
                    _logger.info('Login refresh success: ' + str(response.content))
                    synchronise_status += ' Successfully initialized refresh, waiting for response from bank.'
                    self.synchronise_item.write({'synchronise_status': synchronise_status})
                else:
                    synchronise_status += ' Error while initializing refresh.'
                    synchronise_error = 'ERROR:  \n'
                    synchronise_error += json.loads(response.text)[u'error_message']

                    stage = self.synchronise_item.env['fit.saltedge.synchronise.stage'].sudo().search(
                        [('synchronise_stage_id', '=', 'error')],
                        limit=1)
                    self.synchronise_item.write({
                        'synchronise_status': synchronise_status,
                        'synchronise_state': stage.id,
                        'synchronise_error': synchronise_error})
        except UserError as e:
            raise e
        except Exception as e:
            self._handle_error(e)

    def validate_credentials(self):
        try:
            self.synchronise_item.write({'synchronise_error': ''})
            app = SaltEdge(self.settings.settings_client_id, self.settings.settings_app_id, self.settings.settings_service_secret)
            payload = '{"data": {"credentials": {'
            count = 0
            for synchronise_interactive_field in self.synchronise_item.synchronise_interactive_fields:
                print synchronise_interactive_field.interactive_field_field
                print synchronise_interactive_field.interactive_field_value
                if count > 0:
                    payload += ','
                payload += '"' + synchronise_interactive_field.interactive_field_field + '":"' + \
                           synchronise_interactive_field.interactive_field_value + '"'
                count += 1

            payload += '}}}'
            payload = json.dumps(json.loads(payload))
            payload = self.__add_unique_id(payload, self.settings.settings_environment_url)

            response = app.put('https://www.saltedge.com/api/v4/logins/' + str(self.synchronise_item.synchronise_login_id) + '/interactive',
                               payload)

            synchronise_status = str(self.synchronise_item.synchronise_status)
            synchronise_status += '\n' + str(fields.Datetime.now())

            if response.status_code == 200:
                _logger.info('Login interactive success: ' + str(response.content))
                json_data = json.loads(response.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
                synchronise_status += ' Successfully validated interactive response, waiting for next step.'
                stage = self.synchronise_item.env['fit.saltedge.synchronise.stage'].sudo().search([('synchronise_stage_id', '=', 'connect')],
                                                                                                  limit=1)
                self.synchronise_item.write({
                    'synchronise_status': synchronise_status,
                    'synchronise_state': stage.id})
                print json_data

            else:
                synchronise_status += ' Error while validating interactive response: \n'
                synchronise_status += response.text
                synchronise_error = 'ERROR:  \n'
                synchronise_error += json.loads(response.text)[u'error_message']
                stage = self.synchronise_item.env['fit.saltedge.synchronise.stage'].sudo().search([('synchronise_stage_id', '=', 'error')],
                                                                                                  limit=1)
                self.synchronise_item.write({
                    'synchronise_status': synchronise_status,
                    'synchronise_state': stage.id,
                    'synchronise_error': synchronise_error})
        except UserError:
            raise
        except Exception as e:
            self._handle_error(e)

    def retrieve_transactions(self, next_id=None):
        try:
            self.synchronise_item.write({'synchronise_error': ''})
            app = SaltEdge(self.settings.settings_client_id, self.settings.settings_app_id, self.settings.settings_service_secret)
            if next_id:
                response = app.get('https://www.saltedge.com/api/v4/transactions?account_id=' + self.synchronise_item.synchronise_account_id +
                                   '&from_id=' + str(next_id))
            else:
                response = app.get('https://www.saltedge.com/api/v4/transactions?account_id=' + self.synchronise_item.synchronise_account_id)

            synchronise_status = str(self.synchronise_item.synchronise_status)
            synchronise_status += '\n' + str(fields.Datetime.now())

            if response.status_code == 200:
                _logger.info('Received transactions batch successful: ' + str(response.content))
                # json_data = json.loads(response.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
                json_data = json.loads(response.content)
                synchronise_status += ' Successfully retrieved transaction batch, please wait.'
                synchronise_status += '\n' + str(fields.Datetime.now())
                synchronise_status += ' Handling transactions, please wait.'

                result, statement_ids, notifications, max_unique_id = self._handle_transactions(json_data, next_id)
                if result:
                    if max_unique_id > 0:
                        _account = self.synchronise_item.synchronise_account
                        _account.write({'account_latest_sync_id': max_unique_id})
                    synchronise_status += '\n' + str(fields.Datetime.now())
                    synchronise_status += ' Successfully handled transactions, process done!'
                    stage = self.synchronise_item.env['fit.saltedge.synchronise.stage'].sudo().search([('synchronise_stage_id', '=', 'done')],
                                                                                                      limit=1)
                    self.synchronise_item.write({
                        'synchronise_status': synchronise_status,
                        'synchronise_state': stage.id,
                        'synchronise_error': '',
                        'synchronise_journal_fail': False,
                        'synchronise_statements_ids': statement_ids,
                        'synchronise_notifications': notifications})
                return True
            else:
                synchronise_status += ' Error while retrieving transactions: \n'
                synchronise_status += response.text
                synchronise_error = 'ERROR:  \n'
                synchronise_error += json.loads(response.text)[u'error_message']
                stage = self.synchronise_item.env['fit.saltedge.synchronise.stage'].sudo().search([('synchronise_stage_id', '=', 'error')],
                                                                                                  limit=1)
                self.synchronise_item.write({
                    'synchronise_status': synchronise_status,
                    'synchronise_state': stage.id,
                    'synchronise_error': synchronise_error})

        except UserError:
            raise
        except RedirectWarning:
            raise
        except Exception as e:
            self._handle_error(e)

    def _handle_error(self, e):
        error = ''
        if hasattr(e, 'strerror'):
            error = e.strerror
        else:
            if hasattr(e, 'message'):
                error = e.message

        raise UserError(
            'An unknown error occurred. \nError: ' + str(error))

    def _handle_transactions(self, json_data, current_id):
        _logger.info('Start handling of transactions')

        if not current_id:
            self.transactions = json_data[u'data']
        else:
            self.transactions.extend(json_data[u'data'])

        if json_data[u'meta'][u'next_id']:
            self.retrieve_transactions(json_data[u'meta'][u'next_id'])
        else:
            print 'retrieved all transactions, # total: ' + str(len(self.transactions))
            result_transactions = []
            for transaction in self.transactions:
                if str(transaction[u'account_id']) == str(self.synchronise_item.synchronise_account_id):
                    print 'transaction details: ' + str(transaction)
                    if self.account_number is None:
                        self.account_number = sanitize_account_number(self.synchronise_item.synchronise_account_name)
                    self.account_balance = transaction[u'extra'][u'account_balance_snapshot']

                    result_transaction = {}
                    result_transaction['partner_name'] = transaction[u'description']
                    result_transaction['name'] = transaction[u'description']
                    # created_date = strptime(transaction.made_on, "%Y%m%dT%H:%M:%SZ").date()
                    result_transaction['date'] = transaction[u'made_on']
                    result_transaction['amount'] = transaction[u'amount']
                    result_transaction['unique_import_id'] = str(transaction[u'id'])
                    result_transaction['note'] = transaction[u'description']

                    if u'information' in transaction[u'extra']:
                        if self.__is_valid_iban(transaction[u'extra'][u'information']):
                            result_transaction['account_number'] = self.__get_compact_iban(transaction[u'extra'][u'information'])
                        else:
                            result_transaction['name'] = transaction[u'extra'][u'information']
                            # result_transaction['account_number'] = transaction[u'extra'][u'information'].replace(" ", "")
                    if u'payee' in transaction[u'extra']:
                        if self.__is_valid_iban(transaction[u'extra'][u'payee']):
                            result_transaction['account_number'] = self.__get_compact_iban(transaction[u'extra'][u'payee'])
                        else:
                            result_transaction['name'] = transaction[u'extra'][u'payee']
                            # result_transaction['account_number'] = transaction[u'extra'][u'payee']
                    # if u'payee' in transaction[u'extra']:
                    #     result_transaction['partner_name'] = transaction[u'extra'][u'payee']
                    if u'record_number' in transaction:
                        result_transaction['ref'] = transaction[u'record_number']
                    if u'additional' in transaction[u'extra']:
                        result_transaction['name'] = transaction[u'extra'][u'additional']
                    print 'result transaction: ' + str(result_transaction)
                    result_transactions.append(result_transaction)

            data = [{'name': self._generate_unique_name(), 'date': strftime('%Y-%m-%d'), 'balance_end_real': self.account_balance,
                     'transactions': result_transactions}]

            currency, journal = self.synchronise_item._find_additional_data(self.currency_code, self.account_number)
            if not journal:
                self.synchronise_item.write({'synchronise_journal_fail': True,
                                             'synchronise_error': _('Journal for bank account: %s not available, please create journal '
                                                                    'first.') % (self.account_number,)})
                return False, '', '', 0
            if not journal.default_debit_account_id or not journal.default_credit_account_id:
                self.synchronise_item.write({'synchronise_journal_fail': True,
                                             'synchronise_error': _(
                                                 'You have to set a Default Debit Account and a Default Credit Account for the journal: %s') % (
                                                                      journal.name,)})
                return False, '', '', 0

            try:
                last_bnk_stmt = self.synchronise_item.env['account.bank.statement'].search([('journal_id', '=', journal.id)], limit=1)
                data[0]['balance_start'] = last_bnk_stmt.balance_end_real
                # if last_bnk_stmt:
                # return last_bnk_stmt.balance_end

                # Prepare statement data to be used for bank statements creation
                _max_unique_id = max([x['unique_import_id'] for x in data[0]['transactions']])
                stmts_vals = self.synchronise_item._complete_stmts_vals(data, journal, self.account_number)
                # _max_unique_id = max([x['unique_import_id'] for x in stmts_vals[0]['transactions']])

                # Create the bank statements
                statement_ids, notifications = self.synchronise_item._create_bank_statements(stmts_vals)

                # Now that the import worked out, set it as the bank_statements_source of the journal
                journal.bank_statements_source = 'file_import'

                return True, statement_ids, notifications, _max_unique_id
            except UserError as e:
                # if e[0] == u'U hebt dit bestand reeds ge\xefmporteerd.':
                #     stage = self.synchronise_item.env['fit.saltedge.synchronise.stage'].sudo().search([('synchronise_stage_id', '=', 'done')],
                #                                                                                       limit=1)
                #     self.synchronise_item.write({'synchronise_journal_fail': False,
                #                                  'synchronise_state': stage.id,
                #                                  'synchronise_error': _('All transactions already processed, nothing to do.')})
                # else:
                stage = self.synchronise_item.env['fit.saltedge.synchronise.stage'].sudo().search([('synchronise_stage_id', '=', 'error')],
                                                                                                  limit=1)
                self.synchronise_item.write({'synchronise_journal_fail': False,
                                             'synchronise_state': stage.id,
                                             'synchronise_error': _(e[0])})
                return False, '', '', 0
            except BaseException as e:
                stage = self.synchronise_item.env['fit.saltedge.synchronise.stage'].sudo().search([('synchronise_stage_id', '=', 'error')],
                                                                                                  limit=1)
                self.synchronise_item.write({'synchronise_journal_fail': False,
                                             'synchronise_state': stage.id,
                                             'synchronise_error': _(e)})
                return False, '', '', 0
