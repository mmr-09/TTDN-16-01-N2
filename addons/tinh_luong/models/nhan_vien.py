# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    luong_co_ban = fields.Monetary(string="Lương cơ bản", currency_field='currency_id')
    phu_cap_co_dinh = fields.Monetary(string="Phụ cấp cố định", currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        string="Tiền tệ",
        default=lambda self: self.env.company.currency_id.id,
    )
