import logging

from ..classes.c_client import FitSaltEdgeClient
from ..classes.c_customer import FitSaltEdgeCustomer
from ..classes.c_login import FitSaltEdgeLogin
from ..classes.c_saltedge import SaltEdge
from ..models.m_account import FitSaltEdgeAccount
from ..models.m_provider import FitSaltEdgeProvider
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FitSaltedgeSettingsModel(models.Model):
    _name = 'fit.saltedge.settings'
    _description = _('Settings')
    _rec_name = 'settings_customer_id'

    settings_username = fields.Char('Username')
    settings_password = fields.Char('Password')
    settings_identifier = fields.Char('Identifier')
    settings_service_secret = fields.Char('Service secret')
    settings_client_id = fields.Char('Client ID')
    settings_customer_id = fields.Char('Customer ID')
    settings_customer_identifier = fields.Char('Customer identifier')
    settings_customer_secret = fields.Char('Customer secret')
    settings_environment_url = fields.Char('Environment URL')
    settings_sync_from_date = fields.Date('Sync from', default=fields.Date.today())
    settings_status = fields.Text('Status', default='')
    settings_debug = fields.Boolean('Debug enabled?', default=False)

    def get_app(self):
        self._get_app()

    def _get_app(self):
        try:
            self.app = SaltEdge(self.settings_client_id, self.settings_service_secret)
        except BaseException as e:
            error = ''
            if hasattr(e, 'strerror'):
                error = e.strerror
            else:
                if hasattr(e, 'message'):
                    error = e.message

            raise UserError(_('Error while creating connection object: \nError: ' + str(error)))

    @api.multi
    def validate_settings(self):
        self.settings_status = str(fields.Datetime.now()) + ' Settings validation started'
        self._get_app()
        try:
            _c_saltedge_client = FitSaltEdgeClient(self)
            if _c_saltedge_client.validate_client():
                _c_saltedge_customer = FitSaltEdgeCustomer(self)
                if _c_saltedge_customer.validate_customer():
                    _logger.info('Successfully validated settings')
                    self.settings_status += '\n' + str(fields.Datetime.now()) + ' Successfully validated settings'
        except BaseException as e:
            raise

    @api.multi
    def validate_logins(self):
        self.settings_status = str(fields.Datetime.now()) + ' Login validation started'
        self._get_app()
        try:
            _c_saltedge_account = FitSaltEdgeAccount(self)
            _c_saltedge_login = FitSaltEdgeLogin(self, _c_saltedge_account)
            _c_saltedge_login.refresh_logins(self.settings_customer_id)
        except:
            raise
        self.env['bus.bus'].sendone('auto_refresh', 'ir.ui.menu')

    @api.multi
    def delete_accounts(self):
        _account_model = self.env['fit.saltedge.account']
        _accounts = _account_model.search([])
        for _account in _accounts:
            _logger.info('Deleting account: "' + str(_account.account_name) + '" with ID: ' + str(_account.account_id))
            print 'Deleting account: ' + str(_account.account_name) + '" with ID: ' + str(_account.account_id)
            self.settings_status += '\n' + str(fields.Datetime.now()) + ' Deleted account "' + str(_account.account_name) + '" with ID: ' + str(
                _account.account_id)
            _account.unlink()
        self.settings_status += '\n' + str(fields.Datetime.now()) + ' Accounts deleted'

    @api.multi
    def delete_logins(self):
        self.settings_status = str(fields.Datetime.now()) + ' Bank registration delete started'
        _login_model = self.env['fit.saltedge.login']
        _logins = _login_model.search([])
        for _login in _logins:
            _logger.info('Deleting login: "' + str(_login.login_name) + '" with ID: ' + str(_login.login_id))
            print 'Deleting login: ' + str(_login.login_name) + '" with ID: ' + str(_login.login_id)
            _login.unlink()

        self.settings_status += '\n' + str(fields.Datetime.now()) + ' Bank registration(s) deleted, start account delete'
        self.delete_accounts()
        self.env['bus.bus'].sendone('auto_refresh', 'ir.ui.menu')

    @api.multi
    def update_providers(self):
        self._get_app()
        self.settings_status = str(fields.Datetime.now()) + ' Start Bank Institution update'
        self._c_provider = FitSaltEdgeProvider(self)
        self._c_provider.create_update_providers()
        self.settings_status += '\n' + str(fields.Datetime.now()) + ' Bank Institution updated'

    # @api.one
    @api.onchange('settings_customer_identifier', 'settings_customer_id')
    def __check_group(self):
        if not self.user_has_groups('base.group_system'):
            raise UserError(_('You don\'t have the appropriate rights to update these settings'))

# @api.multi
    # def write(self, vals):
    #     if self.user_has_groups('base.group_system'):
    #         return super(FitSaltedgeSettingsModel, self).write(vals)
    #     else:
    #         raise UserError(_('You don\'t have the appropiate rights to update the settings'))


class FitSaltEdgeSettings:
    def __init__(self, env):
        self.env = env

    def get_settings(self):
        settings_model = self.env['fit.saltedge.settings']
        settings_result = settings_model.search([], limit=1)
        for settings in settings_result:
            return settings
