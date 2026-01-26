from odoo import models, fields, api
from datetime import datetime, time
from odoo.exceptions import ValidationError
from pytz import timezone, UTC

class TrangThaiChamCong(models.Model):
    _name = 'trang_thai_cham_cong'
    _description = 'Trạng thái chấm công'

    name = fields.Char(string="Tên trạng thái", required=True)


class BangChamCong(models.Model):
    _name = 'bang_cham_cong'
    _description = "Bảng chấm công"
    _rec_name = 'Id_BCC'

    # Basic fields
    employee_id = fields.Many2one('hr.employee', string="Nhân viên", required=True)
    ngay_cham_cong = fields.Date("Ngày chấm công", required=True)
    
    ca_lam = fields.Selection([
        ("", ""),
        ("Sáng", "Sáng"),
        ("Chiều", "Chiều"),
        ("Cả ngày", "Cả Ngày"),
    ], string="Ca làm", default="")
    
    gio_vao_ca = fields.Datetime("Giờ vào ca", compute='_compute_gio_ca', store=True)
    gio_ra_ca = fields.Datetime("Giờ ra ca", compute='_compute_gio_ca', store=True)

    Id_BCC = fields.Char(string="ID BCC", compute="_compute_Id_BCC", store=True)

    @api.depends('employee_id', 'ngay_cham_cong')
    def _compute_Id_BCC(self):
        for record in self:
            if record.employee_id and record.ngay_cham_cong:
                record.Id_BCC = f"{record.employee_id.name}_{record.ngay_cham_cong.strftime('%Y-%m-%d')}"
            else:
                record.Id_BCC = ""
    
    @api.depends('ca_lam', 'ngay_cham_cong')
    def _compute_gio_ca(self):
        for record in self:
            if not record.ngay_cham_cong or not record.ca_lam:
                record.gio_vao_ca = False
                record.gio_ra_ca = False
                continue

            user_tz = self.env.user.tz or 'UTC'
            tz = timezone(user_tz)

            if record.ca_lam == "Sáng":
                gio_vao = time(7, 30)  # 7:30 AM
                gio_ra = time(11, 30)  # 11:30 AM
            elif record.ca_lam == "Chiều":
                gio_vao = time(13, 30)  # 1:30 PM
                gio_ra = time(17, 30)  # 5:30 PM
            elif record.ca_lam == "Cả ngày":
                gio_vao = time(7, 30)  # 7:30 AM
                gio_ra = time(17, 30)  # 5:30 PM
            else:
                record.gio_vao_ca = False
                record.gio_ra_ca = False
                continue

            # Convert to datetime in user's timezone
            thoi_gian_vao = datetime.combine(record.ngay_cham_cong, gio_vao)
            thoi_gian_ra = datetime.combine(record.ngay_cham_cong, gio_ra)
            
            # Store in UTC
            record.gio_vao_ca = tz.localize(thoi_gian_vao).astimezone(UTC).replace(tzinfo=None)
            record.gio_ra_ca = tz.localize(thoi_gian_ra).astimezone(UTC).replace(tzinfo=None)

    gio_vao = fields.Datetime("Giờ vào thực tế")
    gio_ra = fields.Datetime("Giờ ra thực tế")

    # Tính toán đi muộn
    phut_di_muon_goc = fields.Float("Số phút đi muộn gốc", compute="_compute_phut_di_muon_goc", store=True)
    phut_di_muon = fields.Float("Số phút đi muộn thực tế", compute="_compute_phut_di_muon", store=True)
    
    @api.depends('gio_vao', 'gio_vao_ca')
    def _compute_phut_di_muon_goc(self):
        for record in self:
            if record.gio_vao and record.gio_vao_ca:
                delta = record.gio_vao - record.gio_vao_ca
                record.phut_di_muon_goc = max(0, delta.total_seconds() / 60)
            else:
                record.phut_di_muon_goc = 0

    @api.depends('phut_di_muon_goc')
    def _compute_phut_di_muon(self):
        for record in self:
            record.phut_di_muon = record.phut_di_muon_goc

    # Tính toán về sớm
    phut_ve_som_goc = fields.Float("Số phút về sớm gốc", compute="_compute_phut_ve_som_goc", store=True)
    phut_ve_som = fields.Float("Số phút về sớm thực tế", compute="_compute_phut_ve_som", store=True)
    
    @api.depends('gio_ra', 'gio_ra_ca')
    def _compute_phut_ve_som_goc(self):
        for record in self:
            if record.gio_ra and record.gio_ra_ca:
                delta = record.gio_ra_ca - record.gio_ra
                record.phut_ve_som_goc = max(0, delta.total_seconds() / 60)
            else:
                record.phut_ve_som_goc = 0

    @api.depends('phut_ve_som_goc')
    def _compute_phut_ve_som(self):
        for record in self:
            record.phut_ve_som = record.phut_ve_som_goc
                

    # Trạng thái chấm công
    trang_thai = fields.Selection([
        ('di_lam', 'Đi làm'),
        ('di_muon', 'Đi muộn'),
        ('di_muon_ve_som', 'Đi muộn và về sớm'),
        ('ve_som', 'Về sớm'),
        ('vang_mat', 'Vắng mặt'),
        ('vang_mat_co_phep', 'Vắng mặt có phép'),
    ], string="Trạng thái", compute="_compute_trang_thai", store=True)
    
    @api.depends('phut_di_muon', 'phut_ve_som', 'gio_vao', 'gio_ra')
    def _compute_trang_thai(self):
        for record in self:
            if not record.gio_vao and not record.gio_ra:
                record.trang_thai = 'vang_mat'
            elif record.phut_di_muon > 0 and record.phut_ve_som > 0:
                record.trang_thai = 'di_muon_ve_som'
            elif record.phut_di_muon > 0:
                record.trang_thai = 'di_muon'
            elif record.phut_ve_som > 0:
                record.trang_thai = 've_som'
            else:
                record.trang_thai = 'di_lam'

    @api.model
    def create(self, vals):
        record = super(BangChamCong, self).create(vals)
        record._cap_nhat_bang_luong()
        return record

    def write(self, vals):
        result = super(BangChamCong, self).write(vals)
        self._cap_nhat_bang_luong()
        return result

    def _cap_nhat_bang_luong(self):
        """Tự động tạo hoặc cập nhật bảng lương khi có chấm công"""
        BangTinhLuong = self.env['bang_tinh_luong']
        
        for record in self:
            if not record.employee_id or not record.ngay_cham_cong:
                continue
            
            thang = str(record.ngay_cham_cong.month)
            nam = str(record.ngay_cham_cong.year)
            
            # Tìm hoặc tạo bảng lương cho nhân viên/tháng/năm
            bang_luong = BangTinhLuong.search([
                ('employee_id', '=', record.employee_id.id),
                ('thang', '=', thang),
                ('nam', '=', nam),
            ], limit=1)
            
            if not bang_luong:
                # Tạo mới bảng lương
                BangTinhLuong.create({
                    'employee_id': record.employee_id.id,
                    'thang': thang,
                    'nam': nam,
                })
            else:
                # Trigger recompute các field computed bằng cách chạm vào record
                bang_luong._compute_thong_ke_cong()

    