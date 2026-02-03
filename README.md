 <h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    🎓 Faculty of Information Technology (DaiNam University)
    </a>
</h2>
<h2 align="center">
   Hệ thống quản lý nhân sự, chấm công và tính lương trên nền tảng Odoo 15
</h2>
<div align="center">
    <p align="center">
        <img src="images/aiotlab_logo.png" alt="AIoTLab Logo" width="170"/>
        <img src="images/fitdnu_logo.png" alt="AIoTLab Logo" width="180"/>
        <img src="images/dnu_logo.png" alt="DaiNam University Logo" width="200"/>
    </p>

[![AIoTLab](https://img.shields.io/badge/AIoTLab-green?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)
</div>

## 1. Tổng quan về hệ thống

Hệ thống được xây dựng trên nền tảng Odoo 15 nhằm hỗ trợ doanh nghiệp quản lý tập trung các nghiệp vụ cốt lõi, bao gồm quản lý nhân sự, quản lý chấm công và quản lý tính lương. Hệ thống được thiết kế theo mô hình ERP module hóa, cho phép các chức năng liên kết chặt chẽ với nhau, đồng thời đảm bảo tính linh hoạt, dễ mở rộng và phù hợp với nhu cầu quản lý thực tế của doanh nghiệp.

Trong hệ thống, mỗi nghiệp vụ được triển khai dưới dạng một module độc lập nhưng có khả năng tích hợp và chia sẻ dữ liệu. Nhờ đó, thông tin được quản lý đồng bộ, giúp nâng cao hiệu quả vận hành, giảm thao tác thủ công và hỗ trợ nhà quản lý trong quá trình theo dõi, đánh giá và ra quyết định.

Bên cạnh các chức năng quản lý cơ bản, hệ thống còn tích hợp chatbot nội quy hỗ trợ tra cứu quy định công ty nhằm góp phần nâng cao trải nghiệm người dùng và tiệm cận hơn với nhu cầu thực tế của doanh nghiệp hiện nay.

## 2. Các chức năng chính

Hệ thống cung cấp các chức năng quản lý nghiệp vụ cốt lõi của doanh nghiệp, được triển khai dưới dạng các module độc lập nhưng có khả năng liên kết và chia sẻ dữ liệu với nhau.

### 2.1. Quản lý nhân sự
- Quản lý thông tin nhân viên, phòng ban và chức vụ.
- Phân quyền người dùng theo vai trò.
- Liên kết nhân viên với công việc và khách hàng phụ trách.

### 2.2. Quản lý chấm công
- Quản lý chấm công hàng ngày
- Quản lý giờ giấc vào ca, tan làm
- Theo dõi đi muộn và về sớm

### 2.3. Quản lý tính lương
- Tính toán lương tháng của từng thành viên trong công ty
- Phân tích - tính toán đầy đủ lương cơ bản - phụ cấp - thưởng phạt
- Tổng hợp công, tính phạt và lương thực nhận
- Tạo báo cáo chấm công và bảng lương
- Tự động tính lương và in danh sách bản lương

### 2.4. Chatbot nội quy
- Hỗ trợ tra cứu nội quy và quy định công ty.
- Chatbot sử dụng Groq API để xử lý câu hỏi.
- Trả lời dựa trên dữ liệu nội quy được cấu hình sẵn trong hệ thống.

## 3. Công nghệ sử dụng

![OS](https://img.shields.io/badge/OS-Ubuntu-orange?logo=ubuntu&logoColor=white)
![ERP](https://img.shields.io/badge/ERP-Odoo%2015-purple)
[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org/)
![Database](https://img.shields.io/badge/Database-PostgreSQL-blue?logo=postgresql&logoColor=white)
![Container](https://img.shields.io/badge/Container-Docker-blue?logo=docker&logoColor=white)
![Repository](https://img.shields.io/badge/Repository-GitHub-black?logo=github&logoColor=white)

Hệ thống được triển khai trên hệ điều hành Ubuntu, sử dụng nền tảng Odoo 15 làm lõi ERP.  
Python 3.10 được sử dụng để phát triển các module nghiệp vụ, kết hợp với PostgreSQL để lưu trữ dữ liệu.  
Docker hỗ trợ triển khai cơ sở dữ liệu, trong khi GitHub được dùng để quản lý mã nguồn.  

## 4. Cài đặt công cụ, môi trường và các thư viện cần thiết

### 4.1. Clone project.
```
git clone https://github.com/FIT-DNU/Business-Internship.git

git clone https://github.com/mmr-09/TTDN-16-01-N2

git checkout 
```
### 4.2. cài đặt các thư viện cần thiết

Người sử dụng thực thi các lệnh sau đề cài đặt các thư viện cần thiết

```
sudo apt-get install libxml2-dev libxslt-dev libldap2-dev libsasl2-dev libssl-dev python3.10-distutils python3.10-dev build-essential libssl-dev libffi-dev zlib1g-dev python3.10-venv libpq-dev
```
### 4.3. khởi tạo môi trường ảo.

`python3.10 -m venv ./venv`
Thay đổi trình thông dịch sang môi trường ảo và chạy requirements.txt để cài đặt tiếp các thư viện được yêu cầu

```
source venv/bin/activate
pip3 install -r requirements.txt
```

### 4.4. Setup database

Khởi tạo database trên docker bằng việc thực thi file dockercompose.yml.

`docker-compose up -d`

### 4.5. Setup tham số chạy cho hệ thống
#### Khởi tạo odoo.conf
Tạo tệp **odoo.conf** có nội dung như sau:

```
[options]
addons_path = addons
db_host = localhost
db_password = odoo
db_user = odoo
db_port = 5431
xmlrpc_port = 8069
```
Có thể kế thừa từ **odoo.conf.template**

Ngoài ra có thể thêm mổ số parameters như:

```
-c _<đường dẫn đến tệp odoo.conf>_
-u _<tên addons>_ giúp cập nhật addons đó trước khi khởi chạy
-d _<tên database>_ giúp chỉ rõ tên database được sử dụng
--dev=all giúp bật chế độ nhà phát triển 
```

### 4.7. Chạy hệ thống và cài đặt các ứng dụng cần thiết

Người sử dụng truy cập theo đường dẫn _http://localhost:8069/_ để đăng nhập vào hệ thống.

##  5. Poster

<img width="562" height="806" alt="image" src="https://github.com/user-attachments/assets/417584be-4e2a-42d4-8e4c-dafd694f005a" />

## 6. Liên hệ
- 👨‍🎓 **Sinh viên thực hiện**: Nguyễn Tiến Thái - Nguyễn Việt Đức - Lù Ngọc Tân
- 🎓 **Khoa**: Công nghệ thông tin – Đại học Đại Nam
- 📧 **Email**: tienthai0915@gmail.com / nguyenvietduc71221@gmail.com
