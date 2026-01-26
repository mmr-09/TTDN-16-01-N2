# -*- coding: utf-8 -*-
from datetime import date
import calendar
from odoo import models, fields, api


class BangTinhLuong(models.Model):
    _name = 'bang_tinh_luong'
    _description = 'Bảng tính lương'
    _rec_name = 'name'
    _order = 'nam desc, thang desc, employee_id'

    name = fields.Char(string="Tên bảng lương", compute='_compute_name', store=True)
    employee_id = fields.Many2one('hr.employee', string="Nhân viên", required=True)
    thang = fields.Selection([(str(i), f'Tháng {i}') for i in range(1, 13)], string="Tháng", required=True)
    nam = fields.Char(string="Năm", required=True)

    ngay_bat_dau = fields.Date(string="Ngày bắt đầu", compute='_compute_ngay', store=True)
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc", compute='_compute_ngay', store=True)

    cong_chuan = fields.Integer(string="Công chuẩn", default=26)
    muc_phat_moi_phut = fields.Monetary(string="Mức phạt mỗi phút", default=5000, currency_field='currency_id')

    # Cấu hình làm tròn theo giờ làm
    gio_mot_cong = fields.Float(string="Giờ/1 công", default=8.0)
    buoc_lam_tron_phut = fields.Integer(string="Bước làm tròn (phút)", default=30,
                                        help="Làm tròn tổng phút làm việc theo bội số phút này")
    kieu_lam_tron = fields.Selection([
        ('nearest', 'Gần nhất'),
        ('floor', 'Xuống'),
        ('ceil', 'Lên'),
    ], string="Kiểu làm tròn", default='nearest')

    luong_co_ban = fields.Monetary(string="Lương cơ bản", compute='_compute_thong_tin_luong', store=True, currency_field='currency_id')
    phu_cap_co_dinh = fields.Monetary(string="Phụ cấp cố định", compute='_compute_thong_tin_luong', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string="Tiền tệ", default=lambda self: self.env.company.currency_id.id)

    so_gio_cong = fields.Float(string="Số giờ công (đã làm tròn)", compute='_compute_thong_ke_cong', store=True)
    so_ngay_cong = fields.Float(string="Số ngày công", compute='_compute_thong_ke_cong', store=True)
    so_ngay_vang_khong_phep = fields.Float(string="Vắng không phép", compute='_compute_thong_ke_cong', store=True)
    so_ngay_vang_co_phep = fields.Float(string="Vắng có phép", compute='_compute_thong_ke_cong', store=True)
    tong_phut_di_muon = fields.Float(string="Tổng phút đi muộn", compute='_compute_thong_ke_cong', store=True)
    tong_phut_ve_som = fields.Float(string="Tổng phút về sớm", compute='_compute_thong_ke_cong', store=True)

    don_gia_cong = fields.Monetary(string="Đơn giá công", compute='_compute_tien_luong', store=True, currency_field='currency_id')
    tien_cong = fields.Monetary(string="Tiền công", compute='_compute_tien_luong', store=True, currency_field='currency_id')
    tien_phat = fields.Monetary(string="Tiền phạt", compute='_compute_tien_luong', store=True, currency_field='currency_id')
    luong_thuc_nhan = fields.Monetary(string="Lương thực nhận", compute='_compute_tien_luong', store=True, currency_field='currency_id')

    _sql_constraints = [
        ('unique_bang_luong', 'unique(employee_id, thang, nam)', 'Mỗi nhân viên chỉ có một bảng lương cho một tháng.'),
    ]

    @api.depends('employee_id', 'thang', 'nam')
    def _compute_name(self):
        for record in self:
            if record.employee_id and record.thang and record.nam:
                record.name = f"Lương {record.employee_id.name} {record.thang}/{record.nam}"
            else:
                record.name = False

    @api.depends('thang', 'nam')
    def _compute_ngay(self):
        for record in self:
            if record.thang and record.nam:
                thang = int(record.thang)
                nam = int(record.nam)
                ngay_dau = date(nam, thang, 1)
                ngay_cuoi = date(nam, thang, calendar.monthrange(nam, thang)[1])
                record.ngay_bat_dau = ngay_dau
                record.ngay_ket_thuc = ngay_cuoi
            else:
                record.ngay_bat_dau = False
                record.ngay_ket_thuc = False

    @api.depends('employee_id')
    def _compute_thong_tin_luong(self):
        for record in self:
            record.luong_co_ban = record.employee_id.luong_co_ban
            record.phu_cap_co_dinh = record.employee_id.phu_cap_co_dinh

    @api.depends('employee_id', 'ngay_bat_dau', 'ngay_ket_thuc', 'buoc_lam_tron_phut', 'kieu_lam_tron', 'gio_mot_cong')
    def _compute_thong_ke_cong(self):
        BangChamCong = self.env['bang_cham_cong']
        for record in self:
            record.so_gio_cong = 0
            record.so_ngay_cong = 0
            record.so_ngay_vang_khong_phep = 0
            record.so_ngay_vang_co_phep = 0
            record.tong_phut_di_muon = 0
            record.tong_phut_ve_som = 0

            if not record.employee_id or not record.ngay_bat_dau or not record.ngay_ket_thuc:
                continue

            # Lấy dữ liệu chấm công từ module cham_cong
            domain = [
                ('employee_id', '=', record.employee_id.id),
                ('ngay_cham_cong', '>=', record.ngay_bat_dau),
                ('ngay_cham_cong', '<=', record.ngay_ket_thuc),
            ]
            cham_congs = BangChamCong.search(domain)

            if not cham_congs:
                continue

            # Thống kê chi tiết từ bảng chấm công
            ngay_di_lam = 0
            ngay_vang_khong_phep = 0
            ngay_vang_co_phep = 0
            tong_phut_muon = 0
            tong_phut_som = 0
            tong_phut_lam = 0

            def round_minutes(total_minutes, step, mode):
                if step <= 0:
                    return total_minutes
                if mode == 'floor':
                    return (total_minutes // step) * step
                if mode == 'ceil':
                    return ((total_minutes + step - 1) // step) * step
                # nearest
                return int((total_minutes + step / 2) // step) * step

            for cc in cham_congs:
                # Tính ngày công dựa trên ca làm
                if cc.ca_lam == 'Cả ngày':
                    ngay_di_lam += 1
                elif cc.ca_lam in ['Sáng', 'Chiều']:
                    ngay_di_lam += 0.5
                
                # Thống kê vắng mặt
                if cc.trang_thai == 'vang_mat':
                    if cc.ca_lam == 'Cả ngày':
                        ngay_vang_khong_phep += 1
                    elif cc.ca_lam in ['Sáng', 'Chiều']:
                        ngay_vang_khong_phep += 0.5
                elif cc.trang_thai == 'vang_mat_co_phep':
                    if cc.ca_lam == 'Cả ngày':
                        ngay_vang_co_phep += 1
                    elif cc.ca_lam in ['Sáng', 'Chiều']:
                        ngay_vang_co_phep += 0.5
                
                # Tổng hợp phút đi muộn và về sớm
                tong_phut_muon += cc.phut_di_muon
                tong_phut_som += cc.phut_ve_som

                # Tổng phút làm việc theo giờ vào/ra, áp dụng làm tròn
                if cc.gio_vao and cc.gio_ra:
                    delta_min = int((cc.gio_ra - cc.gio_vao).total_seconds() / 60)
                    delta_min = max(0, delta_min)
                    tong_phut_lam += round_minutes(delta_min, record.buoc_lam_tron_phut, record.kieu_lam_tron)

            record.so_ngay_cong = ngay_di_lam
            record.so_gio_cong = tong_phut_lam / 60.0
            record.so_ngay_vang_khong_phep = ngay_vang_khong_phep
            record.so_ngay_vang_co_phep = ngay_vang_co_phep
            record.tong_phut_di_muon = tong_phut_muon
            record.tong_phut_ve_som = tong_phut_som

            # Quy đổi giờ công đã làm tròn thành ngày công theo cấu hình
            if record.gio_mot_cong and record.gio_mot_cong > 0:
                record.so_ngay_cong = record.so_gio_cong / record.gio_mot_cong

    @api.depends(
        'luong_co_ban',
        'phu_cap_co_dinh',
        'cong_chuan',
        'so_ngay_cong',
        'tong_phut_di_muon',
        'tong_phut_ve_som',
        'muc_phat_moi_phut',
    )
    def _compute_tien_luong(self):
        for record in self:
            if record.cong_chuan and record.cong_chuan > 0:
                record.don_gia_cong = record.luong_co_ban / record.cong_chuan
            else:
                record.don_gia_cong = 0

            record.tien_cong = record.don_gia_cong * record.so_ngay_cong
            tong_phut_phat = record.tong_phut_di_muon + record.tong_phut_ve_som
            record.tien_phat = record.muc_phat_moi_phut * tong_phut_phat
            record.luong_thuc_nhan = record.tien_cong + record.phu_cap_co_dinh - record.tien_phat
