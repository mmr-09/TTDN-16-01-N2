# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class HrChatMessage(models.Model):
    _name = 'hr.chat.message'
    _description = 'HR Chat Message'
    _order = 'create_date asc'
    
    user_id = fields.Many2one('res.users', string="Người dùng", default=lambda self: self.env.user, required=True)
    message = fields.Text(string="Tin nhắn", required=True)
    is_bot = fields.Boolean(string="Là bot", default=False)
    employee_id = fields.Many2one('hr.employee', string="Nhân viên liên quan")
    
    def send_message(self, message_text):
        """Gửi tin nhắn và nhận phản hồi từ AI"""
        # Tạo tin nhắn của user
        user_msg = self.create({
            'message': message_text,
            'is_bot': False,
        })
        
        # Xử lý câu hỏi
        try:
            assistant = self.env['hr.ai.assistant']
            intent, employee, params = assistant._analyze_question(message_text)
            answer = assistant._get_answer(intent, employee, params)
            
            # Tạo tin nhắn phản hồi của bot
            bot_msg = self.create({
                'message': answer,
                'is_bot': True,
                'employee_id': employee.id if employee else False,
            })
            
            return {
                'user_message': {
                    'id': user_msg.id,
                    'message': user_msg.message,
                    'is_bot': False,
                    'time': user_msg.create_date.strftime('%H:%M'),
                },
                'bot_message': {
                    'id': bot_msg.id,
                    'message': bot_msg.message,
                    'is_bot': True,
                    'time': bot_msg.create_date.strftime('%H:%M'),
                    'employee_name': employee.name if employee else '',
                }
            }
        except Exception as e:
            _logger.exception("Error in send_message")
            bot_msg = self.create({
                'message': f"❌ Xin lỗi, có lỗi xảy ra: {str(e)}",
                'is_bot': True,
            })
            return {
                'user_message': {
                    'id': user_msg.id,
                    'message': user_msg.message,
                    'is_bot': False,
                    'time': user_msg.create_date.strftime('%H:%M'),
                },
                'bot_message': {
                    'id': bot_msg.id,
                    'message': bot_msg.message,
                    'is_bot': True,
                    'time': bot_msg.create_date.strftime('%H:%M'),
                }
            }
    
    @api.model
    def get_chat_history(self, limit=50):
        """Lấy lịch sử chat"""
        messages = self.search([
            ('user_id', '=', self.env.user.id)
        ], limit=limit, order='create_date asc')
        
        return [{
            'id': msg.id,
            'message': msg.message,
            'is_bot': msg.is_bot,
            'time': msg.create_date.strftime('%H:%M'),
            'employee_name': msg.employee_id.name if msg.employee_id else '',
        } for msg in messages]
    
    @api.model
    def clear_chat_history(self):
        """Xóa lịch sử chat"""
        self.search([('user_id', '=', self.env.user.id)]).unlink()
        return True
