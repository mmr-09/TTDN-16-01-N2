# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CauHinhLuong(models.Model):
    _name = 'cau_hinh_luong'
    _description = 'Cấu hình lương và bảo hiểm'
    _rec_name = 'employee_id'
    _order = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string="Nhân viên", required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string="Công ty", default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string="Tiền tệ", related='company_id.currency_id', readonly=True)
    
    # Thông tin lương
    luong_co_ban = fields.Monetary(string="Lương cơ bản", currency_field='currency_id', required=True)
    phu_cap_co_dinh = fields.Monetary(string="Phụ cấp cố định", currency_field='currency_id', default=0)
    
    # Cấu hình bảo hiểm
    ap_dung_bao_hiem = fields.Boolean(string="Áp dụng bảo hiểm", default=True, 
                                       help="Tích vào nếu nhân viên có tham gia bảo hiểm")
    luong_dong_bao_hiem = fields.Monetary(
        string="Lương đóng bảo hiểm",
        currency_field='currency_id',
        help="Lương làm căn cứ đóng bảo hiểm. Nếu để trống sẽ lấy bằng lương cơ bản"
    )
    
    # Tỷ lệ bảo hiểm nhân viên đóng
    ty_le_bhxh_nv = fields.Float(string="Tỷ lệ BHXH (NV)", default=8.0, 
                                  help="Tỷ lệ % bảo hiểm xã hội nhân viên đóng")
    ty_le_bhyt_nv = fields.Float(string="Tỷ lệ BHYT (NV)", default=1.5, 
                                  help="Tỷ lệ % bảo hiểm y tế nhân viên đóng")
    ty_le_bhtn_nv = fields.Float(string="Tỷ lệ BHTN (NV)", default=1.0, 
                                  help="Tỷ lệ % bảo hiểm thất nghiệp nhân viên đóng")
    
    # Tỷ lệ bảo hiểm công ty đóng
    ty_le_bhxh_cty = fields.Float(string="Tỷ lệ BHXH (CTY)", default=17.5, 
                                   help="Tỷ lệ % bảo hiểm xã hội công ty đóng")
    ty_le_bhyt_cty = fields.Float(string="Tỷ lệ BHYT (CTY)", default=3.0, 
                                   help="Tỷ lệ % bảo hiểm y tế công ty đóng")
    ty_le_bhtn_cty = fields.Float(string="Tỷ lệ BHTN (CTY)", default=1.0, 
                                   help="Tỷ lệ % bảo hiểm thất nghiệp công ty đóng")
    
    # Ghi chú
    note = fields.Text(string="Ghi chú")
    
    _sql_constraints = [
        ('unique_employee', 'unique(employee_id)', 'Mỗi nhân viên chỉ có một cấu hình lương!'),
    ]
    
    @api.onchange('luong_co_ban', 'luong_dong_bao_hiem')
    def _onchange_luong_dong_bao_hiem(self):
        """Tự động điền lương đóng bảo hiểm bằng lương cơ bản nếu để trống"""
        if not self.luong_dong_bao_hiem and self.luong_co_ban:
            self.luong_dong_bao_hiem = self.luong_co_ban
    
    @api.model
    def get_cau_hinh_by_employee(self, employee_id):
        """Lấy cấu hình lương của nhân viên"""
        return self.search([('employee_id', '=', employee_id)], limit=1)
