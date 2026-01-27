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

    # Cấu hình bảo hiểm
    luong_dong_bao_hiem = fields.Monetary(
        string="Lương đóng bảo hiểm",
        currency_field='currency_id',
        help="Lương làm căn cứ đóng bảo hiểm. Nếu để trống sẽ lấy bằng lương cơ bản"
    )
    ty_le_bhxh_nv = fields.Float(string="Tỷ lệ BHXH (NV)", default=8.0, help="Tỷ lệ % bảo hiểm xã hội nhân viên đóng")
    ty_le_bhyt_nv = fields.Float(string="Tỷ lệ BHYT (NV)", default=1.5, help="Tỷ lệ % bảo hiểm y tế nhân viên đóng")
    ty_le_bhtn_nv = fields.Float(string="Tỷ lệ BHTN (NV)", default=1.0, help="Tỷ lệ % bảo hiểm thất nghiệp nhân viên đóng")
    
    ty_le_bhxh_cty = fields.Float(string="Tỷ lệ BHXH (CTY)", default=17.5, help="Tỷ lệ % bảo hiểm xã hội công ty đóng")
    ty_le_bhyt_cty = fields.Float(string="Tỷ lệ BHYT (CTY)", default=3.0, help="Tỷ lệ % bảo hiểm y tế công ty đóng")
    ty_le_bhtn_cty = fields.Float(string="Tỷ lệ BHTN (CTY)", default=1.0, help="Tỷ lệ % bảo hiểm thất nghiệp công ty đóng")
    
    ap_dung_bao_hiem = fields.Boolean(string="Áp dụng bảo hiểm", default=True, help="Tích vào nếu nhân viên có tham gia bảo hiểm")
