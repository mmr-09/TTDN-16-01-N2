# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import re
import json
import logging

_logger = logging.getLogger(__name__)


class HrAIAssistant(models.Model):
    _name = 'hr.ai.assistant'
    _description = 'HR AI Assistant'
    _order = 'create_date desc'
    
    user_id = fields.Many2one('res.users', string="Người hỏi", default=lambda self: self.env.user)
    question = fields.Text(string="Câu hỏi", required=True)
    answer = fields.Html(string="Câu trả lời")
    employee_id = fields.Many2one('hr.employee', string="Nhân viên liên quan")
    query_time = fields.Datetime(string="Thời gian hỏi", default=fields.Datetime.now)
    
    def action_ask_ai(self):
        """Button action để hỏi AI"""
        _logger.info("="*50)
        _logger.info("action_ask_ai called!")
        
        self.ensure_one()
        
        if not self.question:
            _logger.warning("No question provided")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '⚠️ Chưa có câu hỏi',
                    'message': 'Vui lòng nhập câu hỏi trước',
                    'type': 'warning',
                }
            }
        
        try:
            _logger.info(f"Question: {self.question}")
            
            # Phân tích câu hỏi
            intent, employee, params = self._analyze_question(self.question)
            _logger.info(f"Intent: {intent}, Employee: {employee}, Params: {params}")
            
            # Lấy câu trả lời
            answer = self._get_answer(intent, employee, params)
            _logger.info(f"Answer length: {len(answer)}")
            _logger.info(f"Answer preview: {answer[:200]}...")
            
            # Lưu kết quả
            answer_html = answer.replace('\n', '<br/>')
            self.write({
                'answer': answer_html,
                'employee_id': employee.id if employee else False,
            })
            
            _logger.info("Answer saved successfully!")
            
            # Reload form để hiển thị answer
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'hr.ai.assistant',
                'res_id': self.id,
                'view_mode': 'form',
                'view_id': self.env.ref('hr_ai_assistant.view_hr_ai_assistant_form').id,
                'target': 'current',
            }
            
        except Exception as e:
            _logger.exception("Error in action_ask_ai")
            self.answer = f"<p style='color: red;'>❌ Lỗi: {str(e)}</p>"
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '❌ Lỗi',
                    'message': str(e),
                    'type': 'danger',
                }
            }
    
    @api.model
    def ask_question(self, question):
        """
        Hàm chính: Nhận câu hỏi, phân tích và trả lời
        
        Ví dụ câu hỏi:
        - "Thông tin nhân viên Nguyễn Văn A"
        - "Lương tháng này của NV001"
        - "Số ngày nghỉ của Trần Thị B tháng 1"
        - "Nhân viên nào đi muộn nhiều nhất"
        """
        try:
            # Bước 1: Phân tích câu hỏi
            intent, employee, params = self._analyze_question(question)
            
            # Bước 2: Lấy thông tin từ database
            answer = self._get_answer(intent, employee, params)
            
            # Bước 3: Lưu lịch sử
            record = self.create({
                'question': question,
                'answer': answer,
                'employee_id': employee.id if employee else False,
            })
            
            return {
                'success': True,
                'answer': answer,
                'employee_id': employee.id if employee else False,
                'employee_name': employee.name if employee else '',
            }
            
        except Exception as e:
            return {
                'success': False,
                'answer': f"❌ Xin lỗi, tôi không hiểu câu hỏi này. Lỗi: {str(e)}"
            }
    
    def _analyze_question(self, question):
        """
        Phân tích câu hỏi để xác định:
        - Intent: Hỏi về gì? (lương/công/nghỉ/thông tin chung)
        - Employee: Nhân viên nào?
        - Params: Tham số thêm (tháng, năm, khoảng thời gian)
        """
        question_lower = question.lower()
        
        # Xác định intent
        intent = None
        if any(keyword in question_lower for keyword in ['lương', 'luong', 'tiền', 'thu nhập']):
            intent = 'salary'
        elif any(keyword in question_lower for keyword in ['công', 'cong', 'chấm công', 'cham cong', 'giờ làm', 'gio lam']):
            intent = 'attendance'
        elif any(keyword in question_lower for keyword in ['nghỉ', 'nghi', 'vắng', 'vang', 'phép']):
            intent = 'leave'
        elif any(keyword in question_lower for keyword in ['bảo hiểm', 'bao hiem', 'bhxh', 'bhyt']):
            intent = 'insurance'
        elif any(keyword in question_lower for keyword in ['đi muộn', 'di muon', 'về sớm', 've som']):
            intent = 'late_early'
        elif any(keyword in question_lower for keyword in ['thông tin', 'thong tin', 'hồ sơ', 'ho so']):
            intent = 'info'
        elif any(keyword in question_lower for keyword in ['tất cả', 'tat ca', 'toàn bộ', 'toan bo', 'danh sách', 'danh sach']):
            intent = 'list'
        else:
            intent = 'info'  # Mặc định
        
        # Tìm nhân viên được nhắc đến
        employee = self._find_employee_from_text(question)
        
        # Tìm tháng/năm
        params = self._extract_time_params(question)
        
        return intent, employee, params
    
    def _find_employee_from_text(self, text):
        """Tìm nhân viên từ tên hoặc mã trong câu hỏi"""
        # Tìm theo mã nhân viên (NV001, NV002, ...)
        match = re.search(r'NV\d+', text, re.IGNORECASE)
        if match:
            code = match.group(0).upper()
            employee = self.env['hr.employee'].search([
                ('barcode', '=', code)
            ], limit=1)
            if employee:
                return employee
        
        # Tìm theo tên (tìm tất cả nhân viên và match tên)
        employees = self.env['hr.employee'].search([])
        for emp in employees:
            if emp.name.lower() in text.lower():
                return emp
        
        return None
    
    def _extract_time_params(self, question):
        """Trích xuất thời gian từ câu hỏi"""
        params = {
            'thang': None,
            'nam': None,
        }
        
        # Tìm tháng (tháng 1, tháng 12, T1, T12)
        match = re.search(r'tháng\s*(\d+)', question, re.IGNORECASE)
        if not match:
            match = re.search(r'T(\d+)', question)
        if match:
            params['thang'] = match.group(1)
        else:
            # Mặc định tháng hiện tại
            params['thang'] = str(date.today().month)
        
        # Tìm năm
        match = re.search(r'năm\s*(\d{4})', question, re.IGNORECASE)
        if match:
            params['nam'] = match.group(1)
        else:
            # Mặc định năm hiện tại
            params['nam'] = str(date.today().year)
        
        return params
    
    def _get_answer(self, intent, employee, params):
        """Lấy câu trả lời dựa trên intent"""
        
        if not employee and intent not in ['list']:
            return "❓ Vui lòng cho biết tên hoặc mã nhân viên cần tra cứu."
        
        if intent == 'salary':
            return self._get_salary_info(employee, params)
        elif intent == 'attendance':
            return self._get_attendance_info(employee, params)
        elif intent == 'leave':
            return self._get_leave_info(employee, params)
        elif intent == 'insurance':
            return self._get_insurance_info(employee, params)
        elif intent == 'late_early':
            return self._get_late_early_info(employee, params)
        elif intent == 'info':
            return self._get_employee_info(employee)
        elif intent == 'list':
            return self._get_list_employees()
        else:
            return self._get_full_report(employee, params)
    
    def _get_salary_info(self, employee, params):
        """Trả lời về lương"""
        BangTinhLuong = self.env['bang_tinh_luong']
        
        bang_luong = BangTinhLuong.search([
            ('employee_id', '=', employee.id),
            ('thang', '=', params['thang']),
            ('nam', '=', params['nam']),
        ], limit=1)
        
        if not bang_luong:
            return f"❌ Chưa có bảng lương tháng {params['thang']}/{params['nam']} của {employee.name}"
        
        answer = f"""
💰 **THÔNG TIN LƯƠNG - {employee.name}**
📅 Tháng: {params['thang']}/{params['nam']}

💵 Lương cơ bản: {bang_luong.luong_co_ban:,.0f} VNĐ
📊 Công chuẩn: {bang_luong.cong_chuan} ngày
✅ Số công thực tế: {bang_luong.so_ngay_cong:.1f} ngày
⏰ Số giờ làm: {bang_luong.so_gio_cong:.1f} giờ

💸 Tiền công: {bang_luong.tien_cong:,.0f} VNĐ
🎁 Phụ cấp: {bang_luong.phu_cap_co_dinh:,.0f} VNĐ
⚠️ Tiền phạt: {bang_luong.tien_phat:,.0f} VNĐ
🏥 Bảo hiểm NV đóng: {bang_luong.tong_bh_nv:,.0f} VNĐ

💰 **LƯƠNG THỰC NHẬN: {bang_luong.luong_thuc_nhan:,.0f} VNĐ**
"""
        return answer
    
    def _get_attendance_info(self, employee, params):
        """Trả lời về chấm công"""
        BangChamCong = self.env['bang_cham_cong']
        
        # Tính ngày đầu và cuối tháng
        thang = int(params['thang'])
        nam = int(params['nam'])
        from calendar import monthrange
        ngay_dau = date(nam, thang, 1)
        ngay_cuoi = date(nam, thang, monthrange(nam, thang)[1])
        
        cham_congs = BangChamCong.search([
            ('employee_id', '=', employee.id),
            ('ngay_cham_cong', '>=', ngay_dau),
            ('ngay_cham_cong', '<=', ngay_cuoi),
        ])
        
        # Thống kê
        tong_ngay = len(cham_congs)
        di_lam = len(cham_congs.filtered(lambda x: x.trang_thai == 'di_lam'))
        di_muon = len(cham_congs.filtered(lambda x: 'di_muon' in x.trang_thai))
        ve_som = len(cham_congs.filtered(lambda x: 've_som' in x.trang_thai))
        vang_mat = len(cham_congs.filtered(lambda x: 'vang_mat' in x.trang_thai))
        
        tong_phut_muon = sum(cham_congs.mapped('phut_di_muon'))
        tong_phut_som = sum(cham_congs.mapped('phut_ve_som'))
        
        answer = f"""
📊 **THÔNG TIN CHẤM CÔNG - {employee.name}**
📅 Tháng: {params['thang']}/{params['nam']}

📈 Tổng số bản ghi: {tong_ngay} ngày
✅ Đi làm đúng giờ: {di_lam} lần
⏰ Đi muộn: {di_muon} lần (Tổng: {tong_phut_muon:.0f} phút)
🏃 Về sớm: {ve_som} lần (Tổng: {tong_phut_som:.0f} phút)
❌ Vắng mặt: {vang_mat} lần
"""
        
        # Hiển thị 5 ngày gần nhất
        recent = cham_congs.sorted(lambda x: x.ngay_cham_cong, reverse=True)[:5]
        if recent:
            answer += "\n📋 **5 ngày gần nhất:**\n"
            for cc in recent:
                status_icon = {
                    'di_lam': '✅',
                    'di_muon': '⏰',
                    've_som': '🏃',
                    'di_muon_ve_som': '⚠️',
                    'vang_mat': '❌',
                    'vang_mat_co_phep': '📝',
                }.get(cc.trang_thai, '❓')
                
                answer += f"  {status_icon} {cc.ngay_cham_cong.strftime('%d/%m/%Y')} - {cc.ca_lam} - {cc.trang_thai}\n"
        
        return answer
    
    def _get_leave_info(self, employee, params):
        """Trả lời về nghỉ phép"""
        BangChamCong = self.env['bang_cham_cong']
        
        thang = int(params['thang'])
        nam = int(params['nam'])
        from calendar import monthrange
        ngay_dau = date(nam, thang, 1)
        ngay_cuoi = date(nam, thang, monthrange(nam, thang)[1])
        
        # Nghỉ có phép
        nghi_co_phep = BangChamCong.search_count([
            ('employee_id', '=', employee.id),
            ('ngay_cham_cong', '>=', ngay_dau),
            ('ngay_cham_cong', '<=', ngay_cuoi),
            ('trang_thai', '=', 'vang_mat_co_phep'),
        ])
        
        # Nghỉ không phép
        nghi_khong_phep = BangChamCong.search_count([
            ('employee_id', '=', employee.id),
            ('ngay_cham_cong', '>=', ngay_dau),
            ('ngay_cham_cong', '<=', ngay_cuoi),
            ('trang_thai', '=', 'vang_mat'),
        ])
        
        answer = f"""
📝 **THÔNG TIN NGHỈ PHÉP - {employee.name}**
📅 Tháng: {params['thang']}/{params['nam']}

✅ Nghỉ có phép: {nghi_co_phep} ngày
❌ Nghỉ không phép: {nghi_khong_phep} ngày
📊 Tổng nghỉ: {nghi_co_phep + nghi_khong_phep} ngày
"""
        return answer
    
    def _get_insurance_info(self, employee, params):
        """Trả lời về bảo hiểm"""
        BangTinhLuong = self.env['bang_tinh_luong']
        
        bang_luong = BangTinhLuong.search([
            ('employee_id', '=', employee.id),
            ('thang', '=', params['thang']),
            ('nam', '=', params['nam']),
        ], limit=1)
        
        if not bang_luong:
            # Lấy thông tin từ employee
            answer = f"""
🏥 **THÔNG TIN BẢO HIỂM - {employee.name}**

📊 Lương đóng BH: {employee.luong_dong_bao_hiem:,.0f} VNĐ
✅ Áp dụng BH: {'Có' if employee.ap_dung_bao_hiem else 'Không'}

💼 Tỷ lệ NV đóng:
   - BHXH: {employee.ty_le_bhxh_nv}%
   - BHYT: {employee.ty_le_bhyt_nv}%
   - BHTN: {employee.ty_le_bhtn_nv}%

🏢 Tỷ lệ Công ty đóng:
   - BHXH: {employee.ty_le_bhxh_cty}%
   - BHYT: {employee.ty_le_bhyt_cty}%
   - BHTN: {employee.ty_le_bhtn_cty}%
"""
        else:
            answer = f"""
🏥 **THÔNG TIN BẢO HIỂM - {employee.name}**
📅 Tháng: {params['thang']}/{params['nam']}

📊 Lương đóng BH: {bang_luong.luong_dong_bao_hiem:,.0f} VNĐ

💰 Nhân viên đóng:
   - BHXH: {bang_luong.bhxh_nv:,.0f} VNĐ
   - BHYT: {bang_luong.bhyt_nv:,.0f} VNĐ
   - BHTN: {bang_luong.bhtn_nv:,.0f} VNĐ
   - **Tổng: {bang_luong.tong_bh_nv:,.0f} VNĐ**

🏢 Công ty đóng:
   - BHXH: {bang_luong.bhxh_cty:,.0f} VNĐ
   - BHYT: {bang_luong.bhyt_cty:,.0f} VNĐ
   - BHTN: {bang_luong.bhtn_cty:,.0f} VNĐ
   - **Tổng: {bang_luong.tong_bh_cty:,.0f} VNĐ**
"""
        return answer
    
    def _get_late_early_info(self, employee, params):
        """Thông tin đi muộn về sớm"""
        BangChamCong = self.env['bang_cham_cong']
        
        thang = int(params['thang'])
        nam = int(params['nam'])
        from calendar import monthrange
        ngay_dau = date(nam, thang, 1)
        ngay_cuoi = date(nam, thang, monthrange(nam, thang)[1])
        
        cham_congs = BangChamCong.search([
            ('employee_id', '=', employee.id),
            ('ngay_cham_cong', '>=', ngay_dau),
            ('ngay_cham_cong', '<=', ngay_cuoi),
        ])
        
        di_muon_records = cham_congs.filtered(lambda x: x.phut_di_muon > 0)
        ve_som_records = cham_congs.filtered(lambda x: x.phut_ve_som > 0)
        
        answer = f"""
⏰ **THÔNG TIN ĐI MUỘN VỀ SỚM - {employee.name}**
📅 Tháng: {params['thang']}/{params['nam']}

⏰ Đi muộn:
   - Số lần: {len(di_muon_records)} lần
   - Tổng phút: {sum(di_muon_records.mapped('phut_di_muon')):.0f} phút
   - Trung bình: {sum(di_muon_records.mapped('phut_di_muon'))/len(di_muon_records):.0f} phút/lần

🏃 Về sớm:
   - Số lần: {len(ve_som_records)} lần
   - Tổng phút: {sum(ve_som_records.mapped('phut_ve_som')):.0f} phút
   - Trung bình: {sum(ve_som_records.mapped('phut_ve_som'))/len(ve_som_records):.0f} phút/lần
""" if di_muon_records or ve_som_records else f"✅ {employee.name} không có lần nào đi muộn hoặc về sớm tháng {params['thang']}/{params['nam']}"
        
        return answer
    
    def _get_employee_info(self, employee):
        """Thông tin cơ bản nhân viên"""
        answer = f"""
👤 **THÔNG TIN NHÂN VIÊN**

📛 Họ tên: {employee.name}
🔢 Mã NV: {employee.barcode or 'Chưa có'}
📧 Email: {employee.work_email or 'Chưa có'}
📱 Điện thoại: {employee.mobile_phone or 'Chưa có'}
🏢 Phòng ban: {employee.department_id.name if employee.department_id else 'Chưa có'}
💼 Chức vụ: {employee.job_title or 'Chưa có'}

💰 Lương cơ bản: {employee.luong_co_ban:,.0f} VNĐ
🎁 Phụ cấp: {employee.phu_cap_co_dinh:,.0f} VNĐ
🏥 Bảo hiểm: {'Có' if employee.ap_dung_bao_hiem else 'Không'}
"""
        return answer
    
    def _get_list_employees(self):
        """Danh sách nhân viên"""
        employees = self.env['hr.employee'].search([], limit=20)
        
        answer = "👥 **DANH SÁCH NHÂN VIÊN**\n\n"
        for emp in employees:
            answer += f"• {emp.name} ({emp.barcode or 'N/A'}) - {emp.job_title or 'N/A'}\n"
        
        if len(employees) == 20:
            answer += "\n(Chỉ hiển thị 20 nhân viên đầu tiên)"
        
        return answer
    
    def _get_full_report(self, employee, params):
        """Báo cáo tổng hợp đầy đủ"""
        answer = "📊 **BÁO CÁO TỔNG HỢP**\n\n"
        answer += self._get_employee_info(employee) + "\n\n"
        answer += self._get_salary_info(employee, params) + "\n\n"
        answer += self._get_attendance_info(employee, params)
        return answer
