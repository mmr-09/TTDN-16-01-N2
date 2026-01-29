# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class HRAssistantController(http.Controller):
    
    @http.route('/hr_assistant/send_message', type='json', auth='user', methods=['POST'])
    def send_message(self, message, **kwargs):
        """API endpoint để gửi tin nhắn"""
        chat_message = request.env['hr.chat.message']
        result = chat_message.send_message(message)
        return {'success': True, 'data': result}
    
    @http.route('/hr_assistant/get_history', type='json', auth='user', methods=['GET'])
    def get_history(self, limit=50, **kwargs):
        """Lấy lịch sử chat"""
        chat_message = request.env['hr.chat.message']
        messages = chat_message.get_chat_history(limit)
        return {'success': True, 'messages': messages}
    
    @http.route('/hr_assistant/clear_history', type='json', auth='user', methods=['POST'])
    def clear_history(self, **kwargs):
        """Xóa lịch sử chat"""
        chat_message = request.env['hr.chat.message']
        chat_message.clear_chat_history()
        return {'success': True}
