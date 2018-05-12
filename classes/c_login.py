import json
from collections import namedtuple

from odoo import fields


class FitSaltEdgeLogin:
    def __init__(self, _m_settings, _c_account):
        self._m_settings = _m_settings
        self._c_account = _c_account

    def refresh_logins(self, customer_id):
        response = self._m_settings.app.get(
            'https://www.saltedge.com/api/v3/logins?customer_id=' + str(customer_id))

        if response.status_code == 200:
            json_data = json.loads(response.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))

            if len(json_data.data) == 0:
                self._m_settings.settings_status += '\n' + str(fields.Datetime.now()) + ' No logins found'
            else:
                self._m_settings.settings_status += '\n' + str(fields.Datetime.now()) + ' Logins retrieved, start update'
                for _login in json_data.data:
                    self._refresh_login(_login)
                    self._c_account.refresh_accounts()

    def _refresh_login(self, _login):
        _existing_login = self._m_settings.env['fit.saltedge.login'].search([['login_id', '=', _login.id]])
        if len(_existing_login.ids) > 0:
            self._update_login(_login, _existing_login)
        else:
            self._create_login(_login)

    def _create_login(self, _login):
        self._m_settings.env['fit.saltedge.login'].create(
            {'login_id': int(_login.id),
             'login_name': _login.provider_name,
             'login_provider': _login.provider_id,
             }
        )
        self._m_settings.settings_status += '\n' + str(fields.Datetime.now()) + ' New login created, id: ' + str(_login.id)

    def _update_login(self, _login, _existing_login):
        _existing_login.write(
            {'login_id': int(_login.id),
             'login_name': _login.provider_name,
             'login_provider': _login.provider_id,
             }
        )
        self._m_settings.settings_status += '\n' + str(fields.Datetime.now()) + ' Login updated, id: ' + str(_login.id)
