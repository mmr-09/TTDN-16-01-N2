# -*- coding: utf-8 -*-
{
    'name': "HR AI Assistant",
    'summary': "AI trợ lý tra cứu thông tin nhân viên thông minh",
    'description': """
        HR hỏi thông tin về nhân viên, AI sẽ trả lời:
        - Giờ làm việc, chấm công
        - Lương, bảo hiểm
        - Số ngày nghỉ, số giờ làm
        - Thống kê tổng hợp
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Human Resources',
    'version': '1.0',
    'depends': [
        'base',
        'hr',
        'hr_attendance',
        'cham_cong',
        'tinh_luong',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/delete_old_action.xml',
        'views/hr_ai_assistant_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_ai_assistant/static/src/xml/hr_ai_chat.xml',
            'hr_ai_assistant/static/src/js/hr_ai_chat.js',
            'hr_ai_assistant/static/src/css/hr_ai_chat.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
