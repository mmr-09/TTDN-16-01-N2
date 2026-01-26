# -*- coding: utf-8 -*-
from datetime import time

from odoo import fields, models, api
from pytz import timezone, UTC


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    bang_cham_cong_id = fields.Many2one(
        'bang_cham_cong',
        string="Bảng chấm công liên kết",
        ondelete='set null',
        readonly=True,
    )

    @api.model
    def create(self, vals):
        attendance = super(HrAttendance, self).create(vals)
        attendance._sync_to_bang_cham_cong()
        return attendance

    def write(self, vals):
        result = super(HrAttendance, self).write(vals)
        for attendance in self:
            attendance._sync_to_bang_cham_cong()
        return result

    def _sync_to_bang_cham_cong(self):
        """Đồng bộ dữ liệu từ hr.attendance sang bang_cham_cong (không ghi đè ngày)."""
        BangChamCong = self.env['bang_cham_cong']

        for attendance in self:
            if not attendance.employee_id or not attendance.check_in:
                continue

            user_tz = self.env.user.tz or 'UTC'
            tz = timezone(user_tz)

            check_in_local = UTC.localize(attendance.check_in).astimezone(tz)
            ngay_cham_cong = check_in_local.date()
            gio_check_in = check_in_local.time()

            # Tính số giờ làm (nếu có check_out)
            so_gio = None
            if attendance.check_out:
                so_gio = (attendance.check_out - attendance.check_in).total_seconds() / 3600.0

            ca_lam = self._xac_dinh_ca_lam(gio_check_in, so_gio)

            vals = {
                'employee_id': attendance.employee_id.id,
                'ngay_cham_cong': ngay_cham_cong,
                'ca_lam': ca_lam,
                'gio_vao': attendance.check_in,
                'gio_ra': attendance.check_out or False,
            }

            if attendance.bang_cham_cong_id:
                attendance.bang_cham_cong_id.write(vals)
            else:
                bang_cc = BangChamCong.create(vals)
                attendance.bang_cham_cong_id = bang_cc.id

    def _xac_dinh_ca_lam(self, gio_check_in, so_gio):
        """Xác định ca làm dựa trên giờ check-in và tổng số giờ làm (nếu có)."""
        if so_gio is not None and so_gio >= 7:
            return 'Cả ngày'
        if gio_check_in < time(12, 0):
            return 'Sáng'
        return 'Chiều'
