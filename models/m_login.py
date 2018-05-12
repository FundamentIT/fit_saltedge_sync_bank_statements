import json
import logging
from collections import namedtuple

from ..classes.c_login import FitSaltEdgeLogin
from ..classes.c_saltedge import SaltEdge
from ..models.m_account import FitSaltEdgeAccount
from ..models.m_provider import FitSaltEdgeProvider
from ..models.m_settings import FitSaltEdgeSettings
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FitSaltedgeLoginWizardModel(models.TransientModel):
    _name = 'fit.saltedge.login.wizard'
    _description = 'Login Wizard'
    _rec_name = 'login_wizard_id'

    def __init__(self, pool, cr):
        super(FitSaltedgeLoginWizardModel, self).__init__(pool, cr)

    def _get_providers(self):
        # ceate initial settings and connection app
        self._c_saltedge_settings = FitSaltEdgeSettings(self.env).get_settings()
        self._c_saltedge_settings.get_app()

        self._c_provider = FitSaltEdgeProvider(self._c_saltedge_settings)
        self._c_provider.create_update_providers()

    login_wizard_id = fields.Integer()
    login_wizard_connect = fields.Html('Connect')
    login_wizard_country_id = fields.Char('Country')
    login_wizard_error = fields.Char('Error', default='')
    login_wizard_interactive = fields.Boolean('', default=False)
    login_wizard_interactive_fields = fields.One2many('fit.saltedge.interactive.field', 'interactive_field_id', 'Interactive fields')
    login_wizard_state = fields.Char('State', default='confirm')
    login_wizard_status_label = fields.Char('Status', default='Status')
    login_wizard_status = fields.Text('Status', default='Status will automatically update.')
    login_wizard_saltedge_connect = fields.Html('<p>test</p>')


    # login_wizard_provider_id = fields.Integer(default=_get_providers)
    login_wizard_provider_id = fields.Integer()
    login_wizard_provider = fields.Many2one('fit.saltedge.provider', string='Provider')

    login_wizard_char_fld_1_id = fields.Char()
    login_wizard_char_fld_1_label = fields.Char()
    login_wizard_char_fld_1_value = fields.Char(default='username')
    login_wizard_char_fld_1_visible = fields.Boolean()

    login_wizard_char_fld_2_id = fields.Char()
    login_wizard_char_fld_2_label = fields.Char()
    login_wizard_char_fld_2_value = fields.Char()
    login_wizard_char_fld_2_visible = fields.Boolean()

    login_wizard_pwd_fld_1_id = fields.Char()
    login_wizard_pwd_fld_1_label = fields.Char()
    login_wizard_pwd_fld_1_value = fields.Char()
    login_wizard_pwd_fld_1_visible = fields.Boolean()

    login_wizard_selection_fld_1_id = fields.Char('label')
    login_wizard_selection_fld_1_label = fields.Char()
    login_wizard_selection_fld_1_field = fields.Char('Provider Field')
    login_wizard_selection_fld_1_value = fields.Many2one('fit.saltedge.provider.field.option')
    login_wizard_selection_fld_1_visible = fields.Boolean()

    # @api.multi
    @api.onchange('login_wizard_provider')
    def _get_provider_details(self):
        # self.login_wizard_id = self.login_wizard_id + 10
        self.login_wizard_char_fld_1_visible = False
        self.login_wizard_char_fld_2_visible = False
        self.login_wizard_pwd_fld_1_visible = False
        self.login_wizard_selection_fld_1_visible = False

        self.login_wizard_provider_id = self.login_wizard_provider
        self.login_wizard_country_id = self.login_wizard_provider.provider_country_code
        contains_selection, domain = self.__create_gui_interactive_fields()
        if contains_selection:
            return domain
            # if self.login_wizard_selection_fld_1_field:
            #     res = {}
            #     res['domain'] = {'login_wizard_selection_fld_1_value': [('provider_field', '=', str(self.login_wizard_selection_fld_1_field))]}
            #     return res

    # def write(self, vals):
    #     print 'update'
    #     super(FitSaltedgeLoginWizardModel, self).write(vals)

    def _check_visible_state(self):
        if self.login_wizard_state:
            if self.login_wizard_state == 'initial':
                return False
            else:
                return True
        else:
            return False

    def __create_gui_interactive_fields(self):
        domain = {}
        contains_selection = False
        if self.login_wizard_provider.id:
            # retrieve provider fields
            _fields = self.env['fit.saltedge.provider.field'].search([('provider', '=', self.login_wizard_provider.id)])
            _nr_txt_fields = 0
            _nr_pwd_fields = 0
            _nr_select_fields = 0
            # loop fields
            for _field in _fields:
                # handle field is required and not optional
                if str(_field.provider_field_type) == 'required' and not bool(_field.provider_field_optional):

                    print 'required_field: ' + _field.provider_field_local_name
                    _field_name = str('')
                    # determine field type and enale dynamic field accordingly
                    if _field.provider_field_nature == 'text':
                        _nr_txt_fields = _nr_txt_fields + 1
                        _field_name = 'login_wizard_char_fld_' + str(_nr_txt_fields)
                    elif _field.provider_field_nature == 'password':
                        _nr_pwd_fields = _nr_pwd_fields + 1
                        _field_name = 'login_wizard_pwd_fld_' + str(_nr_pwd_fields)
                    elif _field.provider_field_nature == 'select':
                        _nr_select_fields = _nr_select_fields + 1
                        _field_name = 'login_wizard_selection_fld_' + str(_nr_select_fields)
                        for _field_option in _field.provider_field_options:
                            self.login_wizard_selection_fld_1_field = _field.id
                        domain['domain'] = {_field_name + '_value': [('provider_field', '=', str(_field.id))]}
                        contains_selection = True

                    if _field_name == 'login_wizard_char_fld_1':
                        self.login_wizard_char_fld_1_visible = True
                        self.login_wizard_char_fld_1_label = _field.provider_field_local_name
                        self.login_wizard_char_fld_1_id = _field.id
                        self.login_wizard_char_fld_1_value = False
                    elif _field_name == 'login_wizard_char_fld_2':
                        self.login_wizard_char_fld_2_visible = True
                        self.login_wizard_char_fld_2_label = _field.provider_field_local_name
                        self.login_wizard_char_fld_2_id = _field.id
                        self.login_wizard_char_fld_2_value = False
                    elif _field_name == 'login_wizard_pwd_fld_1':
                        self.login_wizard_pwd_fld_1_visible = True
                        self.login_wizard_pwd_fld_1_label = _field.provider_field_local_name
                        self.login_wizard_pwd_fld_1_id = _field.id
                        self.login_wizard_pwd_fld_1_value = False
                    elif _field_name == 'login_wizard_selection_fld_1':
                        self.login_wizard_selection_fld_1_visible = True
                        self.login_wizard_selection_fld_1_label = _field.provider_field_local_name
                        self.login_wizard_selection_fld_1_id = _field.id
                        self.login_wizard_selection_fld_1_value = False
                        # self.__setattr__(_field_name + '_visible', True)

        return contains_selection, domain

    def __create_selection_field(self, field_option):
        self.env['fit.saltedge.login.wizard.selection'].create(
            {'selection_id': field_option.name,
             'selection_name': field_option.localized_name,
             'selection_option_value': field_option.option_value,
             })
        _logger.info('New selection field created, name: ' + str(field_option.name))
        # return str(field_option.name)

    def __delete_current_selection_fields(self):
        _m_selection_fields = self.env['fit.saltedge.login.wizard.selection']
        _selection_fields = _m_selection_fields.search([])
        for _selection_field in _selection_fields:
            _logger.info('Deleting existing (old) selection fields: ' + _selection_field.selection_name)
            _selection_field.unlink()

    def __add_credentials(self, payload):
        payload = json.loads(payload)
        credentials_details = {}
        fields = self.env['fit.saltedge.provider.field'].search([('provider', '=', self.login_wizard_provider.id)])
        nr_txt_fields = 0
        nr_pwd_fields = 0
        nr_selection_fields = 0
        for field in fields:
            # handle field is required and not optional
            if str(field.provider_field_type) == 'required' and not bool(field.provider_field_optional):
                if field.provider_field_nature == 'text':
                    nr_txt_fields = nr_txt_fields + 1
                    if nr_txt_fields == 1:
                        credentials_details[unicode(field.provider_field_name)] = unicode(self.login_wizard_char_fld_1_value)
                    elif nr_txt_fields == 2:
                        credentials_details[unicode(field.provider_field_name)] = unicode(self.login_wizard_char_fld_2_value)
                elif field.provider_field_nature == 'password':
                    nr_pwd_fields = nr_pwd_fields + 1
                    if nr_pwd_fields == 1:
                        credentials_details[unicode(field.provider_field_name)] = unicode(self.login_wizard_pwd_fld_1_value)
                elif field.provider_field_nature == 'select':
                    nr_selection_fields = nr_selection_fields + 1
                    if nr_selection_fields == 1:
                        credentials_details[
                            unicode(field.provider_field_name)] = self.login_wizard_selection_fld_1_value.provider_field_option_value

        credentials = {u'credentials': credentials_details}
        payload[u'data'].update(credentials)
        return json.dumps(payload)

    def __add_interactive_credentials(self, payload):
        payload = json.loads(payload)
        credentials_details = {}
        # fields = self.env['fit.saltedge.provider.field'].search([('provider', '=', self.login_wizard_provider.id)])
        # nr_txt_fields = 0
        # nr_pwd_fields = 0
        # nr_selection_fields = 0
        # for field in fields:
        #     # handle field is required and not optional
        #     if str(field.provider_field_type) == 'required' and not bool(field.provider_field_optional):
        #         if field.provider_field_nature == 'text':
        #             nr_txt_fields = nr_txt_fields + 1
        #             if nr_txt_fields == 1:
        #                 credentials_details[unicode(field.provider_field_name)] = unicode(self.login_wizard_char_fld_1_value)
        #             elif nr_txt_fields == 2:
        #                 credentials_details[unicode(field.provider_field_name)] = unicode(self.login_wizard_char_fld_2_value)
        #         elif field.provider_field_nature == 'password':
        #             nr_pwd_fields = nr_pwd_fields + 1
        #             if nr_pwd_fields == 1:
        #                 credentials_details[unicode(field.provider_field_name)] = unicode(self.login_wizard_pwd_fld_1_value)
        #         elif field.provider_field_nature == 'select':
        #             nr_selection_fields = nr_selection_fields + 1
        #             if nr_selection_fields == 1:
        #                 credentials_details[unicode(field.provider_field_name)] = self.login_wizard_selection_fld_1_value.provider_field_option_value

        for interactive_field in self.login_wizard_interactive_fields:
            # if str(field.provider_field_type) == 'interactive' and not bool(field.provider_field_optional):
            print interactive_field.interactive_field_name
            print interactive_field.interactive_field_value
            credentials_details[unicode(interactive_field.interactive_field_name)] = unicode(interactive_field.interactive_field_value)

        credentials = {u'credentials': credentials_details}
        payload[u'data'].update(credentials)
        return json.dumps(payload)

    def __add_unique_id(self, payload, environment_url):
        payload = json.loads(payload)
        login_id = {u'login_id': self.id, u'fit_env': environment_url}
        custom_fields = {u'custom_fields': login_id}
        payload[u'data'].update(custom_fields)
        return json.dumps(payload)

    def register_login(self):
        _logger.info('Register new login for provider: ' + str(self.login_wizard_provider.provider_name))
        try:
            _c_saltedge_settings = FitSaltEdgeSettings(self.env).get_settings()
            app = SaltEdge(_c_saltedge_settings.settings_client_id, _c_saltedge_settings.settings_service_secret)
            payload = json.dumps({"data":
                {
                    "customer_id": int(_c_saltedge_settings.settings_customer_id),
                    "country_code": str(self.login_wizard_provider.provider_country_code),
                    "provider_code": str(self.login_wizard_provider.provider_code),
                    "fetch_type": "recent"
                }
            })
            payload = self.__add_credentials(payload)
            payload = self.__add_unique_id(payload, _c_saltedge_settings.settings_environment_url)
            response = app.post('https://www.saltedge.com/api/v3/logins/', payload)
            if response.status_code == 200:
                _logger.info('Login registration successful: ' + str(response.content))
                self.login_wizard_status += '\n' + str(fields.Datetime.now()) + ' Started new registration, please wait.'
                self.login_wizard_state = 'registration'
                json_data = json.loads(response.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
                print json_data
            else:
                print 'error: ' + str(response.status_code) + ', details: ' + str(response.content)
                delete = app.delete('https://www.saltedge.com/api/v3/logins/' + str(self.login_wizard_id))
                raise UserError(_('Error: ' + str(response.status_code) + '\nDetails: ' + json.loads(response.content)[u'error_message']))
        except UserError:
            raise
        except BaseException as e:
            print 'error: ' + str(e)

    def start_login(self):
        self._get_providers()
        self.login_wizard_state = 'initial'
        _logger.info(_('Start registration, retrieve providers.'))


    def validate_data(self):
        _logger.info('Validating data login for provider: ' + str(self.login_wizard_provider.provider_name))
        try:
            _c_saltedge_settings = FitSaltEdgeSettings(self.env).get_settings()
            app = SaltEdge(_c_saltedge_settings.settings_client_id, _c_saltedge_settings.settings_service_secret)
            payload = json.dumps({"data":
                {
                    "customer_id": int(_c_saltedge_settings.settings_customer_id),
                    "country_code": str(self.login_wizard_provider.provider_country_code),
                    "provider_code": str(self.login_wizard_provider.provider_code),
                    "fetch_type": "recent"
                }
            })
            payload = self.__add_interactive_credentials(payload)
            payload = self.__add_unique_id(payload, _c_saltedge_settings.settings_environment_url)
            response = app.put('https://www.saltedge.com/api/v3/logins/' + str(self.login_wizard_id) + '/interactive', payload)
            if response.status_code == 200:
                _logger.info('Login registration successful: ' + str(response.content))
                self.login_wizard_status += '\n' + str(fields.Datetime.now()) + ' Successfully validated interactive request, please wait.'
                json_data = json.loads(response.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
                print json_data
            else:
                print 'error: ' + str(response.status_code) + ', details: ' + str(response.content)
                print 'posting delete for login: ' + str(self.login_wizard_id)
                delete = app.delete('https://www.saltedge.com/api/v3/logins/' + str(self.login_wizard_id))

                raise UserError(_('Error: ' + str(response.status_code) + '\nDetails: ' + json.loads(response.content)[u'error_message']))
        except UserError:
            raise
        except BaseException as e:
            print 'error: ' + str(e)

    def view_registrations(self):
        return {
            'name': _('Bank Overview'),
            'view_type': 'form',
            'view_mode': 'kanban,form',
            'res_model': 'fit.saltedge.login',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'nodestroy': True
        }


class FitSaltedgeLoginModel(models.Model):
    _name = 'fit.saltedge.login'
    _description = 'Login'
    _rec_name = 'login_id'
    _inherit = ['ir.needaction_mixin']

    login_id = fields.Integer(0)
    login_wizard_id = fields.Integer(0)
    login_name = fields.Char('Name')
    login_nr_accounts = fields.Integer(0)
    login_provider = fields.Integer(0)
    login_status = fields.Char('Status', default='Active')

    @api.model
    def _needaction_count(self, domain=None):
        count = int(self.search_count([]))
        return count

    @api.multi
    def test(self):
        print 'LOGIN TEST!'

    @api.multi
    def update_accounts(self):
        _c_saltedge_settings = FitSaltEdgeSettings(self.env).get_settings()
        if not hasattr(_c_saltedge_settings, 'app'):
            _c_saltedge_settings.get_app()
        _c_saltedge_account = FitSaltEdgeAccount(_c_saltedge_settings)
        _c_saltedge_account.refresh_accounts()

    @api.model
    def _default_stage_id(self):
        _stage_initial = self.env['fit.saltedge.login.stage'].search([('login_stage_id', '=', 'inactive')], limit=1)
        return _stage_initial

    @api.model
    def _get_login_states(self, stages, domain, order):
        _states = stages._search([], order=order, access_rights_uid=1)
        return stages.browse(_states)

    @api.multi
    def fit_login_activate(self):
        for login in self:
            login.login_active = not login.login_active
            if login.login_active:
                login.login_status = 'Active'
            else:
                login.login_status = 'Inactive'
        return {
            'name': 'Login Overview',
            'view_type': 'form',
            'view_mode': 'kanban,form',
            'res_model': 'fit.saltedge.login',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'nodestroy': True
        }

    @api.multi
    def write(self, vals):
        active = True if vals.get('login_status') == 'Active' else False
        if active:
            count = int(self.search_count([('login_status', '=', 'Active')]))
            if count > 0:
                raise UserError(_('Error while activating bank registration, only one active registration allowed.'))

        vals['login_active'] = active
        super(FitSaltedgeLoginModel, self).write(vals)

    @api.multi
    def unlink(self):
        try:
            _c_saltedge_settings = FitSaltEdgeSettings(self.env).get_settings()
            _app = SaltEdge(_c_saltedge_settings.settings_client_id, _c_saltedge_settings.settings_service_secret)
            _response = _app.delete('https://www.saltedge.com/api/v3/logins/' + str(self.login_id))
            if _response.status_code == 200:
                _logger.info('Successfully initialized delete for login with id: ' + str(self.login_id))
                _c_saltedge_settings.delete_accounts()
                _c_saltedge_settings.validate_logins()
        except:
            pass

        super(FitSaltedgeLoginModel, self).unlink()
        self.env['bus.bus'].sendone('auto_refresh', 'ir.ui.menu')
