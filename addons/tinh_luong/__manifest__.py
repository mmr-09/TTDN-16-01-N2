# -*- coding: utf-8 -*-
{
    'name': "tinh_luong",
    'summary': "Tính lương dựa trên chấm công và thông tin nhân sự",
    'description': "Tự động tổng hợp công và tính lương theo tháng từ bảng chấm công và hồ sơ nhân sự.",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Human Resources',
    'version': '0.1',
    'depends': [
        'base',
        'hr',
        'hr_attendance',
        'cham_cong',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/nhan_vien.xml',
        'views/bang_tinh_luong.xml',
        'views/menu.xml',
    ],
    'demo': [],
}
