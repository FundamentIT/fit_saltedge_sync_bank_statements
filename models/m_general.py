from odoo import models, fields, _


class FitSaltEdgeAccountStage(models.Model):
    _name = 'fit.saltedge.account.stage'
    _description = 'Account Stage'
    _rec_name = 'account_stage_name'
    account_stage_sequence = fields.Integer('Sequence')
    account_stage_name = fields.Char('Name')
    account_stage_id = fields.Char('ID')


class FitSaltEdgeInteractiveFieldModel(models.Model):
    _name = 'fit.saltedge.interactive.field'
    _description = 'Interactive Field'
    _rec_name = 'interactive_field_name'
    interactive_field_id = fields.Char('ID')
    interactive_field_name = fields.Char('Name')
    interactive_field_value = fields.Char('Value')
    interactive_field_field = fields.Char('Field', default='Field')


class FitSaltEdgeLoginStage(models.Model):
    _name = 'fit.saltedge.login.stage'
    _description = 'Login Stage'
    _rec_name = 'login_stage_name'
    login_stage_sequence = fields.Integer('Sequence')
    login_stage_name = fields.Char('Name')
    login_stage_id = fields.Char('ID')


class FitSaltEdgeSynchroniseStage(models.Model):
    _name = 'fit.saltedge.synchronise.stage'
    _description = 'Synchronise Stage'
    _rec_name = 'synchronise_stage_name'
    synchronise_stage_sequence = fields.Integer('Sequence')
    synchronise_stage_name = fields.Char('Name')
    synchronise_stage_id = fields.Char('ID')


