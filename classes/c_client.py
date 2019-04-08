import json
from collections import namedtuple

from odoo import fields
from odoo.exceptions import UserError


class FitSaltEdgeClient:
    def __init__(self, settings):
        self.settings = settings

    def validate_client(self):
        client_id = self.settings.settings_client_id
        if not client_id:
            return False
        return self.call_client_info()

    def call_client_info(self):
        response = self.settings.app.get('https://www.saltedge.com/api/v4/client/info')
        if response.status_code == 200:
            print 'call client info success: ' + str(response.content)
            json_data = json.loads(response.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
            self.settings.settings_status += '\n' + str(fields.Datetime.now()) + ' Client informatie is correct'
            logins = json_data.data.logins.total
            self.settings.settings_status += '\n' + str(fields.Datetime.now()) + ' Totaal aantal logins aanwezig: ' + str(logins)
            return True
        else:
            raise UserError(_('Error while validating the client information: \n\nCode: '
                              '' + str(response.status_code) + '\nError: ' + str(response.text)))
