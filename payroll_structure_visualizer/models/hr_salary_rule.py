from odoo import api, fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    struct_count = fields.Integer(compute='_compute_struct_count', string='# Structures', store=True,
        help='Number of salary structures using this rule')
    is_shared = fields.Boolean(compute='_compute_struct_count', string='Shared', store=True,
        help='True when this rule is used by more than one salary structure')

    @api.depends('struct_ids')
    def _compute_struct_count(self):
        for rule in self:
            rule.struct_count = len(rule.struct_ids)
            rule.is_shared = rule.struct_count > 1
