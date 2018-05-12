import json
import logging
from collections import namedtuple

from ..classes.c_saltedge import SaltEdge
from odoo import fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FitSaltedgeProviderFieldOptionsModel(models.TransientModel):
    _name = 'fit.saltedge.provider.field.option'
    _description = 'Provider Field Option'
    _rec_name = 'provider_field_option_local_name'

    provider_field = fields.Char('Provider Field')
    provider_field_option_name = fields.Char('Name')
    provider_field_option_english_name = fields.Char('English name')
    provider_field_option_local_name = fields.Char('Localized name')
    provider_field_option_value = fields.Char('Value')


class FitSaltedgeProviderFieldModel(models.TransientModel):
    _name = 'fit.saltedge.provider.field'
    _description = 'Provider Field'
    _rec_name = 'provider_field_name'
    # _inherits = {'fit.saltedge.provider.field.option': 'provider_field_options'}

    provider = fields.Integer('Provider')
    provider_field_type = fields.Char('Type')
    provider_field_name = fields.Char('Name')
    provider_field_english_name = fields.Char('English name')
    provider_field_local_name = fields.Char('Localized name')
    provider_field_nature = fields.Char('Nature')
    provider_field_position = fields.Integer('Position')
    provider_field_optional = fields.Integer('Optional')
    provider_field_options = fields.One2many('fit.saltedge.provider.field.option', 'provider_field_option_name',
                                             'Field options', ondelete="cascade")


class FitSaltEdgeProviderModel(models.TransientModel):
    _name = 'fit.saltedge.provider'
    _description = 'Provider'
    _rec_name = 'provider_name'
    _order = 'provider_name'
    # _inherits = {'fit.saltedge.provider.field': 'provider_fields'}

    provider_id = fields.Integer('ID')
    provider_code = fields.Char('Code')
    provider_name = fields.Char('Name')
    provider_mode = fields.Char('Mode')
    provider_country_code = fields.Char('Country')
    provider_status = fields.Char('Status')
    provider_fields = fields.One2many('fit.saltedge.provider.field', 'provider_field_name',
                                      'Fields', ondelete="cascade")


class FitSaltEdgeProvider:
    def __init__(self, _m_settings):
        self._m_settings = _m_settings

    def create_update_providers(self):
        # delete all existing providers
        # self.__delete_current_providers()
        # retrieve json data containing provider information
        providers = self.__retrieve_providers('NL')
        # create new providers and return result
        for provider in providers:
            _m_provider = self.__create_update_provider(provider)
            _provider_details = self.__retrieve_provider_details(provider)
            self.__create_update_provider_details(_m_provider, _provider_details)

        if self._m_settings.settings_debug:
            providers = self.__retrieve_providers('XF')
            # create new providers and return result
            for provider in providers:
                _m_provider = self.__create_update_provider(provider)
                _provider_details = self.__retrieve_provider_details(provider)
                self.__create_update_provider_details(_m_provider, _provider_details)

    def __create_update_provider(self, provider):
        # check if provider available; then update; otherwise create
        _providers_found = self._m_settings.env['fit.saltedge.provider'].search([('provider_id', '=', provider.id)])
        if len(_providers_found) > 0:
            for _provider_found in _providers_found:
                _provider_found.write({
                    'provider_id': provider.id,
                    'provider_code': provider.code,
                    'provider_name': provider.name,
                    'provider_mode': provider.mode,
                    'provider_country_code': provider.country_code,
                    'provider_status': provider.status
                })
                _logger.info('Provider updated, id: ' + str(provider.id))
                _m_provider = _provider_found
        else:
            _m_provider = self._m_settings.env['fit.saltedge.provider'].create(
                {'provider_id': provider.id,
                 'provider_code': provider.code,
                 'provider_name': provider.name,
                 'provider_mode': provider.mode,
                 'provider_country_code': provider.country_code,
                 'provider_status': provider.status
                 }
            )
            _logger.info('Provider created, id: ' + str(provider.id))
        return _m_provider

    def __create_update_provider_details(self, _m_provider, provider_details):
        #loop required field details
        for required_field in provider_details.required_fields:
            #search existing required fields
            _fields_found = self._m_settings.env['fit.saltedge.provider.field'].search([
                ('provider', '=', _m_provider.id),
                ('provider_field_name', '=', required_field.name)])
            if len(_fields_found.ids) > 0:
                for _field_found in _fields_found:
                    _provider_field = _field_found
                    _field_found.write(
                        {'provider': _m_provider.id,
                         'provider_field_english_name': required_field.english_name,
                         'provider_field_local_name': required_field.localized_name,
                         'provider_field_name': required_field.name,
                         'provider_field_nature': required_field.nature,
                         'provider_field_optional': required_field.optional,
                         'provider_field_position': required_field.position,
                         'provider_field_type': 'required',
                         }
                    )
                    _logger.info('Updated required field: "' + str(required_field.name) + '" for provider ' + provider_details.code)
            else:
                _provider_field = self._m_settings.env['fit.saltedge.provider.field'].create(
                    {'provider': _m_provider.id,
                     'provider_field_english_name': required_field.english_name,
                     'provider_field_local_name': required_field.localized_name,
                     'provider_field_name': required_field.name,
                     'provider_field_nature': required_field.nature,
                     'provider_field_optional': required_field.optional,
                     'provider_field_position': required_field.position,
                     'provider_field_type': 'required',
                     }
                )
                _logger.info('Created new required field: "' + str(required_field.name) + '" for provider ' + provider_details.code)

            #check field options
            if hasattr(required_field, 'field_options'):
                _field_options_found = self._m_settings.env['fit.saltedge.provider.field.option'].search(
                    [('provider_field','=', str(_provider_field.id))])
                if len(_field_options_found.ids) > 0:
                    for _field_option_found in _field_options_found:
                        _field_option_found.unlink()

                for _field_option in required_field.field_options:
                    _provider_field.write({
                        'provider_field_options': [(0, 0, {'provider_field': str(_provider_field.id),
                                                           'provider_field_option_english_name': _field_option.english_name,
                                                           'provider_field_option_local_name': _field_option.localized_name,
                                                           'provider_field_option_name': _field_option.name,
                                                           'provider_field_option_value': _field_option.option_value,
                                                           })]
                    })
                    _logger.info('Created new required field option: ' + str(_field_option.name) + ' for provider ' + provider_details.code)

        if hasattr(provider_details, 'interactive_fields'):

            for _interactive_field in provider_details.interactive_fields:
                _fields_found = self._m_settings.env['fit.saltedge.provider.field'].search([
                    ('provider', '=', _m_provider.id),
                    ('provider_field_name', '=', _interactive_field.name)])
                if len(_fields_found.ids) > 0:
                    for _field_found in _fields_found:
                        _field_found.write(
                            {'provider': _m_provider.id,
                             'provider_field_english_name': _interactive_field.english_name,
                             'provider_field_local_name': _interactive_field.localized_name,
                             'provider_field_name': _interactive_field.name,
                             'provider_field_nature': _interactive_field.nature,
                             'provider_field_optional': _interactive_field.optional,
                             'provider_field_position': _interactive_field.position,
                             'provider_field_type': 'interactive',
                             }
                        )
                        _logger.info('Updated Interactive field: "' + str(_interactive_field.name) + '" for provider ' + provider_details.code)
                else:
                    _provider_field = self._m_settings.env['fit.saltedge.provider.field'].create(
                        {'provider': _m_provider.id,
                         'provider_field_english_name': _interactive_field.english_name,
                         'provider_field_local_name': _interactive_field.localized_name,
                         'provider_field_name': _interactive_field.name,
                         'provider_field_nature': _interactive_field.nature,
                         'provider_field_optional': _interactive_field.optional,
                         'provider_field_position': _interactive_field.position,
                         'provider_field_type': 'interactive',
                         }
                    )
                    _logger.info('Created Interactive field: ' + str(_interactive_field.name) + ' for provider ' + provider_details.code)


    def __delete_current_providers(self):
        _m_provider = self._m_settings.env['fit.saltedge.provider']
        providers = _m_provider.search([])
        for provider in providers:
            _logger.info('Deleting existing (old) provider: ' + provider.provider_name + ' (code: ' + provider.provider_code + ')')
            provider.unlink()

    def __retrieve_providers(self, _code):
        # start retrieving providers
        app = SaltEdge(self._m_settings.settings_client_id, self._m_settings.settings_service_secret)
        response = app.get('https://www.saltedge.com/api/v3/providers?country_code=' + _code + '&mode=web')

        if response.status_code == 200:
            # parse result
            json_data = json.loads(response.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
            return json_data.data
        else:
            raise UserError(_('Error while retrieving banking institutions (providers): \n\nCode: ' + str(response.status_code) + '\nError: ' +
                              str(response.text)))

    def __retrieve_provider_details(self, provider):
        app = SaltEdge(self._m_settings.settings_client_id, self._m_settings.settings_service_secret)
        # delete existing and create new provider details
        if provider.code:
            # start retrieving provider details
            response = app.get('https://www.saltedge.com/api/v3/providers/' + str(provider.code))
            if response.status_code == 200:
                # parse result
                json_data = json.loads(response.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
                return json_data.data
            else:
                raise UserError(
                    _('Error while retrieving banking institution details (provider details): \n\nCode: ' + str(response.status_code) +
                      '\nError: ' + str(response.text)))
