import json
from collections import namedtuple

from odoo import fields
from odoo.exceptions import UserError


class FitSaltEdgeCustomer:
    def __init__(self, settings):
        self.settings = settings
        self.customer_id = ''

    def validate_customer(self):
        self.customer_id = self.settings.settings_customer_id
        if not self.customer_id:
            self.create_customer()
        else:
            if self.is_customer_available(self.customer_id):
                self.settings.settings_status += '\n' + str(fields.Datetime.now()) + ' Customer is available'
            else:
                self.create_customer()

        return True

    def create_customer(self):
        payload = json.dumps({"data": {"identifier": "" + self.settings.settings_customer_identifier + ""}})
        response = self.settings.app.post('https://www.saltedge.com/api/v4/customers/', payload)
        if response.status_code == 200:
            print 'create customer success: ' + str(response.content)
            json_data = json.loads(response.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
            self.settings.settings_status += '\n' + str(fields.Datetime.now()) + ' Customer created, save identifier and secret'
            self.settings.settings_customer_id = json_data.data.id
            # self.settings.settings_customer_identifier = json_data.data.identifier
            self.settings.settings_customer_secret = json_data.data.secret
        else:
            raise UserError(
                'Fout tijdens het aanmaken van een nieuwe : \n\nCode: ' + str(response.status_code) + '\nError: ' + str(
                    response.text))

    def is_customer_available(self, customer_id):
        response = self.settings.app.get('https://www.saltedge.com/api/v4/customers/' + customer_id)
        if response.status_code == 200:
            print 'call customer info success: ' + str(response.content)
            json_data = json.loads(response.content, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
            self.settings.settings_status += '\n' + str(fields.Datetime.now()) + ' Customer information is correct'
            # self.settings.settings_customer_identifier = json_data.data.identifier
            self.settings.settings_customer_id = json_data.data.id
            self.settings.settings_customer_secret = json_data.data.secret
            self.settings.settings_customer_identifier = json_data.data.identifier
            return True

        self.settings.settings_status += '\n' + str(fields.Datetime.now()) + ' No Customer information available'
        return False
