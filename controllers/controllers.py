# -*- coding: utf-8 -*-
import logging

import requests
from pip._vendor.requests.packages.urllib3 import request

from ..classes.c_saltedge import SaltEdge
from odoo import http, fields, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class FitSaltEdgeController(http.Controller):
    def __get_stage(self, request, stage):
        stage_search = request.env['fit.saltedge.synchronise.stage'].sudo(). \
            search([('synchronise_stage_id', '=', str(stage))], limit=1)
        return stage_search.id

    def __create_login_registration_item(self, login_wizard_item, request):
        login_item = request.env['fit.saltedge.login'].sudo().search([('login_id', '=', int(login_wizard_item.login_wizard_id))])
        if len(login_item.ids) == 0:
            try:
                _logger.info(
                    'State finished, creating new bank/login registration for login wizard (id: ' + str(login_wizard_item.login_wizard_id) + ')')
                record = request.env['fit.saltedge.login'].sudo().create(
                    {'login_id': int(login_wizard_item.login_wizard_id),
                     'login_name': login_wizard_item.login_wizard_provider.provider_name,
                     'login_provider': login_wizard_item.login_wizard_provider.id,
                     }
                )
            except BaseException as e:
                error = e.strerror if hasattr(e, 'strerror') else False
                if not error:
                    error = e.message if hasattr(e, 'message') else None
                    if not error:
                        error = str(e)
                # error = ''
                # if hasattr(e, 'strerror'):
                #     error = e.strerror
                # else:
                #     if hasattr(e, 'message'):
                #         error = e.message
                _logger.error('Error while creating login registration: ' + str(error))

            try:
                record.test()
                record.update_accounts()
                _logger.info('Accounts updated from login record (id: ' + str(login_wizard_item.login_wizard_id) + ')')
            except BaseException as e:
                error = e.strerror if hasattr(e, 'strerror') else False
                if not error:
                    error = e.message if hasattr(e, 'message') else None
                    if not error:
                        error = str(e)
                _logger.error('Error while updating accounts: ' + str(error))

        else:
            _logger.info('State finished, login wizard item already exists (id: ' + str(login_item.id) + ')')

    def __get_reroute_url(self, request, type):
        _base_url = request.jsonrequest[u'data'][u'custom_fields'][u'fit_env']
        _full_url = _base_url + '/saltedge/' + type
        return _full_url

    @http.route('/fit_bank_import/route/success', auth='public', type='json', csrf=False)
    def route_success_traffic(self, request, **kw):
        if u'fit_env' in request.jsonrequest[u'data'][u'custom_fields']:
            _reroute_url = self.__get_reroute_url(request, 'success')
            requests.post(_reroute_url, None, request.jsonrequest, **kw)
        else:
            _logger.error('Success route callback, unable to determine target environment for request: ' + str(request.jsonrequest))

    @http.route('/fit_bank_import/route/interactive', auth='public', type='json', csrf=False)
    def route_interactive_traffic(self, request, **kw):
        if u'fit_env' in request.jsonrequest[u'data'][u'custom_fields']:
            _reroute_url = self.__get_reroute_url(request, 'interactive')
            requests.post(_reroute_url, None, request.jsonrequest, **kw)
        else:
            _logger.error('Interactive route callback, unable to determine target environment for request: ' + str(request.jsonrequest))

    @http.route('/fit_bank_import/route/fail', auth='public', type='json', csrf=False)
    def route_fail_traffic(self, request, **kw):
        if u'fit_env' in request.jsonrequest[u'data'][u'custom_fields']:
            _reroute_url = self.__get_reroute_url(request, 'fail')
            requests.post(_reroute_url, None, request.jsonrequest, **kw)
        else:
            _logger.error('Fail route callback, unable to determine target environment for request: ' + str(request.jsonrequest))

    @http.route('/fit_bank_import/route/notify', auth='public', type='json', csrf=False)
    def route_notify_traffic(self, request, **kw):
        if u'fit_env' in request.jsonrequest[u'data'][u'custom_fields']:
            _reroute_url = self.__get_reroute_url(request, 'notify')
            requests.post(_reroute_url, None, request.jsonrequest, **kw)
        else:
            _logger.error('Notify route callback, unable to determine target environment for request: ' + str(request.jsonrequest))

    @http.route('/fit_bank_import/route/service', auth='public', type='json', csrf=False)
    def route_service_traffic(self, request, **kw):
        if u'fit_env' in request.jsonrequest[u'data'][u'custom_fields']:
            _reroute_url = self.__get_reroute_url(request, 'service')
            requests.post(_reroute_url, None, request.jsonrequest, **kw)
        else:
            _logger.error('Service route callback, unable to determine target environment for request: ' + str(request.jsonrequest))

    @http.route('/fit_bank_import/route/destroy', auth='public', type='json', csrf=False)
    def route_destroy_traffic(self, request, **kw):
        if u'fit_env' in request.jsonrequest[u'data'][u'custom_fields']:
            _reroute_url = self.__get_reroute_url(request, 'destroy')
            requests.post(_reroute_url, None, request.jsonrequest, **kw)
        else:
            _logger.error('Destroy route callback, unable to determine target environment for request: ' + str(request.jsonrequest))

    @http.route('/fit_bank_import/start_sync', type='json', auth='user', methods=['POST'])
    def start_sync_synchronization(self, **post):
        sync_id = post[u'id']
        _logger.info('Retrieved synchronization start for item with ID: ' + str(sync_id))
        sync_item = request.env['fit.saltedge.synchronise'].sudo().browse(sync_id)
        sync_item.start_synchronization()
        request.env['bus.bus'].sendone('auto_refresh', 'fit.saltedge.synchronise')

    @http.route('/fit_bank_import/start_login', type='json', auth='user', methods=['POST'])
    def start_login_synchronization(self, **post):
        login_id = post[u'id']
        _logger.info('Retrieved login wizard start for item with ID: ' + str(login_id))
        login_wizard_item = request.env['fit.saltedge.login.wizard'].sudo().browse(login_id)
        # sync_item.start_synchronization()
        request.env['bus.bus'].sendone('auto_refresh', 'fit.saltedge.login.wizard')

    @http.route('/saltedge/notify', auth='public', type='json', csrf=False)
    def saltedge_notify(self, request, **kw):
        try:
            _logger.info("Received SaltEdge Notify callback: " + str(request.jsonrequest))
            if u'sync_id' in request.jsonrequest[u'data'][u'custom_fields']:
                sync_id = request.jsonrequest[u'data'][u'custom_fields'][u'sync_id']
                self._process_notify_sync_item(sync_id, request)
            elif u'login_id' in request.jsonrequest[u'data'][u'custom_fields']:
                login_id = request.jsonrequest[u'data'][u'custom_fields'][u'login_id']
                self._process_notify_login_wizard_item(login_id, request)

        except Exception as e:
            print 'notify callback error: ' + str(e)
            # print 'retry....'
            # self.saltedge_notify(request, **kw)

    @http.route('/saltedge/interactive', auth='public', type='json', csrf=False)
    def saltedge_interactive(self, request, **kw):
        try:
            _logger.info("Received SaltEdge Interactive callback: " + str(request.jsonrequest))
            if u'sync_id' in request.jsonrequest[u'data'][u'custom_fields']:
                sync_id = request.jsonrequest[u'data'][u'custom_fields'][u'sync_id']
                self._process_interactive_sync_item(sync_id, request)
            elif u'login_id' in request.jsonrequest[u'data'][u'custom_fields']:
                login_id = request.jsonrequest[u'data'][u'custom_fields'][u'login_id']
                self._process_interactive_login_wizard_item(login_id, request)
        except Exception as e:
            print 'interactive callback error: ' + str(e)

    @http.route('/saltedge/success', auth='public', type='json', csrf=False)
    def saltedge_success(self, request, **kw):
        try:
            _logger.info("Received SaltEdge Success callback: " + str(request.jsonrequest))
            if u'sync_id' in request.jsonrequest[u'data'][u'custom_fields']:
                sync_id = request.jsonrequest[u'data'][u'custom_fields'][u'sync_id']
                self._process_success_sync_item(sync_id, request)
            elif u'login_id' in request.jsonrequest[u'data'][u'custom_fields']:
                login_id = request.jsonrequest[u'data'][u'custom_fields'][u'login_id']
                self._process_success_login_wizard_item(login_id, request)

        except Exception as e:
            print 'success callback error: ' + str(e)

    @http.route('/saltedge/fail', auth='public', type='json', csrf=False)
    def saltedge_fail(self, request, **kw):
        try:
            _logger.info("Received SaltEdge Fail callback: " + str(request.jsonrequest))
            if u'sync_id' in request.jsonrequest[u'data'][u'custom_fields']:
                sync_id = request.jsonrequest[u'data'][u'custom_fields'][u'sync_id']
                self._process_fail_sync_item(sync_id, request)
            elif u'login_id' in request.jsonrequest[u'data'][u'custom_fields']:
                login_id = request.jsonrequest[u'data'][u'custom_fields'][u'login_id']
                self._process_fail_login_wizard_item(login_id, request)
        except Exception as e:
            print 'fail callback fail: ' + str(e)

    @http.route('/saltedge/service', auth='public', type='json', csrf=False)
    def saltedge_service(self, request, **kw):
        try:
            _logger.info("Received SaltEdge Service callback: " + str(request.jsonrequest))
            print 'saltedge service callback'
        except Exception as e:
            print 'service callback error: ' + str(e)

    @http.route('/saltedge/destroy', auth='public', type='json', csrf=False)
    def saltedge_destory(self, request, **kw):
        try:
            _logger.info("Received SaltEdge Destroy callback: " + str(request.jsonrequest))
            print 'saltedge destroy callback'
        except Exception as e:
            print 'destroy callback error: ' + str(e)

    def _process_notify_login_wizard_item(self, login_id, request):
        stage = request.jsonrequest[u'data'][u'stage']
        sa_login_id = request.jsonrequest[u'data'][u'login_id']
        login_wizard_item = request.env['fit.saltedge.login.wizard'].sudo().browse(login_id)

        if login_wizard_item:
            current_login_wizard_state = login_wizard_item.login_wizard_state
            if current_login_wizard_state != stage:
                login_wizard_status = str(login_wizard_item.login_wizard_status)
                login_wizard_status += '\n' + str(fields.Datetime.now()) + ' Received notification, new state: ' + stage + ', please wait.'
                login_wizard_item.write({'login_wizard_status': login_wizard_status,
                                         'login_wizard_id': sa_login_id,
                                         'login_wizard_state': stage})
                if stage == 'finish':
                    self.__create_login_registration_item(login_wizard_item, request)
                    login_wizard_status = str(login_wizard_item.login_wizard_status)
                    login_wizard_status += '\n' + str(fields.Datetime.now()) + ' Bank registration completed, accounts added, proces completed.'

                # request.env['bus.bus'].sendone('auto_refresh', 'ir.ui.menu')
                request.env['bus.bus'].sendone('auto_refresh', 'fit.saltedge.login.wizard')

    def _process_notify_sync_item(self, sync_id, request):
        stage = request.jsonrequest[u'data'][u'stage']
        update_stage = False
        if stage == 'connect':
            update_stage = True
        elif stage == 'interactive':
            print 'interactive return!'
            return
            # update_stage = True

        synchronise_item = request.env['fit.saltedge.synchronise'].sudo().browse(sync_id)

        if synchronise_item:
            synchronise_status = str(synchronise_item.synchronise_status)
            synchronise_status += '\n' + str(fields.Datetime.now()) + ' Received notification, new state: ' + stage + ', please wait.'
            if update_stage:
                synchronise_item.write({'synchronise_status': synchronise_status,
                                        'synchronise_saltedge_stage': stage,
                                        'synchronise_state': self.__get_stage(request, stage)})
            else:
                synchronise_item.write({'synchronise_status': synchronise_status,
                                        'synchronise_saltedge_stage': stage})

            request.env['bus.bus'].sendone('auto_refresh', 'fit.saltedge.synchronise')

    def _process_interactive_login_wizard_item(self, login_id, request):
        stage = request.jsonrequest[u'data'][u'stage']
        sa_login_id = request.jsonrequest[u'data'][u'login_id']
        interactive_html = request.jsonrequest[u'data'][u'html']
        interactive_fields_names = request.jsonrequest[u'data'][u'interactive_fields_names']
        login_wizard_item = request.env['fit.saltedge.login.wizard'].sudo().browse(login_id)

        if login_wizard_item:
            if interactive_html:
                connect_data = '<div id=\'interactive_top\'>' + interactive_html + '</div>'
            else:
                connect_data = ''

            login_wizard_item.login_wizard_interactive_fields.unlink()
            login_wizard_item.write({
                'login_wizard_id': sa_login_id,
                'login_wizard_connect': connect_data})

            print 'interactive connect update:' + connect_data

            for interactive_fields_name in interactive_fields_names:
                print 'interactive_fields_name: ' + interactive_fields_name
                login_wizard_item.write({
                    'login_wizard_interactive_fields': [(0, 0, {
                        'interactive_field_name': interactive_fields_name,
                        'interactive_field_field': interactive_fields_name,
                    })]
                })

            request.env['bus.bus'].sendone('auto_refresh', 'fit.saltedge.login.wizard')

    def _process_interactive_sync_item(self, sync_id, request):
        stage = request.jsonrequest[u'data'][u'stage']
        interactive_html = request.jsonrequest[u'data'][u'html']
        interactive_fields_names = request.jsonrequest[u'data'][u'interactive_fields_names']
        synchronise_item = request.env['fit.saltedge.synchronise'].sudo().browse(sync_id)

        if synchronise_item:
            synchronise_status = str(synchronise_item.synchronise_status)
            synchronise_status += '\n' + str(
                fields.Datetime.now()) + ' Received interactive request, new state: ' + stage + '.'
            if interactive_html:
                connect_data = '<div id=\'interactive_top\'>' + interactive_html + '</div>'
            else:
                connect_data = ''

            synchronise_item.synchronise_interactive_fields.unlink()
            synchronise_item.write({
                'synchronise_state': self.__get_stage(request, stage),
                'synchronise_status': synchronise_status,
                'synchronise_saltedge_stage': stage,
                'synchronise_connect': connect_data})

            print 'interactive connect update:' + connect_data

            for interactive_fields_name in interactive_fields_names:
                print 'interactive_fields_name: ' + interactive_fields_name
                synchronise_item.write({
                    'synchronise_interactive_fields': [(0, 0, {
                        'interactive_field_name': interactive_fields_name,
                        'interactive_field_field': interactive_fields_name,
                    })]
                })

            request.env['bus.bus'].sendone('auto_refresh', 'fit.saltedge.synchronise')

    def _process_fail_login_wizard_item(self, login_id, request):
        error = str(request.jsonrequest[u'data'][u'error_message'])
        error_class = str(request.jsonrequest[u'data'][u'error_class'])
        if error_class == 'InvalidInteractiveCredentials':
            stage = 'interactive'
        else:
            stage = 'error'

        login_wizard_item = request.env['fit.saltedge.login.wizard'].sudo().browse(login_id)
        if login_wizard_item:
            login_wizard_id = login_wizard_item.login_wizard_id
            login_wizard_status = str(login_wizard_item.login_wizard_status)
            login_wizard_status += '\n' + str(fields.Datetime.now()) + ' Received error, new state: ' + stage + '.'
            login_wizard_item.write({
                'login_wizard_state': stage,
                'login_wizard_status': login_wizard_status,
                'login_wizard_error': _(error)})

            _c_saltedge_settings = request.env['fit.saltedge.settings'].sudo().search([], limit=1)
            app = SaltEdge(_c_saltedge_settings.settings_client_id, _c_saltedge_settings.settings_app_id, _c_saltedge_settings.settings_service_secret)
            delete = app.delete('https://www.saltedge.com/api/v4/logins/' + str(login_wizard_id))

            request.env['bus.bus'].sendone('auto_refresh', 'fit.saltedge.login.wizard')

    def _process_fail_sync_item(self, sync_id, request):
        error = str(request.jsonrequest[u'data'][u'error_message'])
        error_class = str(request.jsonrequest[u'data'][u'error_class'])
        if error_class == 'InvalidInteractiveCredentials':
            stage = 'interactive'
        else:
            stage = 'error'

        synchronise_item = request.env['fit.saltedge.synchronise'].sudo().browse(sync_id)
        if synchronise_item:
            synchronise_status = str(synchronise_item.synchronise_status)
            synchronise_status += '\n' + str(fields.Datetime.now()) + ' Received error, new state: ' + stage + '.'
            synchronise_item.write({
                'synchronise_state': self.__get_stage(request, stage),
                'synchronise_status': synchronise_status,
                'synchronise_error': _(error)})

            request.env['bus.bus'].sendone('auto_refresh', 'fit.saltedge.synchronise')

    def _process_success_login_wizard_item(self, login_id, request):
        login_wizard_item = request.env['fit.saltedge.login.wizard'].sudo().browse(login_id)
        if login_wizard_item:
            print 'success callback stage: ' + login_wizard_item.login_wizard_state
            if login_wizard_item.login_wizard_state == 'finish':
                print 'FOUND FINISHED LOGIN'
                _logger.info('Successful login, create registration item')

                # with Environment.manage():  # class function
                #     env = Environment(cr, uid, context)

                # self.__create_login_registration_item(login_wizard_item, request)

                # request.env['bus.bus'].sendone('auto_refresh', 'fit.saltedge.login.wizard')

    def _process_success_sync_item(self, sync_id, request):
        synchronise_item = request.env['fit.saltedge.synchronise'].sudo().browse(sync_id)

        if synchronise_item:
            print 'success callback stage: ' + str(synchronise_item.synchronise_saltedge_stage)
            if synchronise_item.synchronise_saltedge_stage == 'finish':
                print 'FOUND FINISHED REFRESH, START TRANSACTION UPDATE'
                _logger.info('Successful refresh, set state to \'transactions update\'')

            request.env['bus.bus'].sendone('auto_refresh', 'fit.saltedge.synchronise')
