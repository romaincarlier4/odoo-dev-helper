from odoo import api, fields, models


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    rule_count = fields.Integer(compute='_compute_rule_stats', string='Rules', store=True)
    shared_rule_count = fields.Integer(compute='_compute_rule_stats', string='Shared Rules', store=True,
        help='Number of rules that are also used by at least one other salary structure')

    @api.depends('rule_ids', 'rule_ids.struct_ids')
    def _compute_rule_stats(self):
        for struct in self:
            rules = struct.rule_ids
            struct.rule_count = len(rules)
            struct.shared_rule_count = sum(1 for r in rules if len(r.struct_ids) > 1)
