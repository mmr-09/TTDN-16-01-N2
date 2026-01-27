# Phân Tích Workflow Ba Module: HR, CHAM_CONG, TINH_LUONG

---

## 📋 PHẦN 1: PHÂN TÍCH CÁC MODULE

### 1. MODULE HR (Nhân Sự)
**Đường dẫn:** `addons/hr/`

#### Mục đích/Mô tả:
- Module cốt lõi của hệ thống quản lý nhân sự Odoo
- Quản lý thông tin nhân viên, phòng ban, chức vụ
- Lưu trữ hồ sơ cá nhân chi tiết của từng nhân viên

#### Model chính: `hr.employee`
**Các trường quan trọng (từ tinh_luong module):**
- `id` - ID nhân viên (liên kết với các module khác)
- `name` - Tên nhân viên
- `resource_id` - Liên kết tới tài nguyên
- `user_id` - Liên kết tới user account
- `company_id` - Công ty nhân viên làm việc
- `department_id` - Phòng ban
- `job_id` - Chức vụ
- `address_home_id` - Địa chỉ cá nhân
- **`luong_co_ban`** - Lương cơ bản (được extend bởi tinh_luong)
- **`phu_cap_co_dinh`** - Phụ cấp cố định (được extend bởi tinh_luong)

#### Các model phụ:
- `hr.department` - Phòng ban
- `hr.job` - Chức vụ/vị trí công việc
- `hr.employee.category` - Phân loại nhân viên
- `hr.employee.public` - Thông tin nhân viên công khai
- `hr.departure.reason` - Lý do rời công ty

#### Dependencies:
```
- base_setup
- mail
- resource
- web
```

#### Key Functions/Methods:
- `create()` - Tạo nhân viên mới (đồng bộ thông tin từ user account)
- `_sync_user()` - Đồng bộ thông tin từ user (email, tz, avatar)
- `_cron_check_work_permit_validity()` - Kiểm tra hiệu lực giấy phép làm việc
- `name_get()`, `read()`, `_search()` - Xử lý quyền truy cập

---

### 2. MODULE CHAM_CONG (Chấm Công/Attendance)
**Đường dẫn:** `addons/cham_cong/`

#### Mục đích/Mô tả:
- Quản lý chấm công hàng ngày của nhân viên
- Ghi nhận giờ vào, giờ ra từ hệ thống hr.attendance
- Tính toán các vi phạm (đi muộn, về sớm, vắng mặt)
- Tự động cập nhật bảng lương khi có thay đổi chấm công

#### Model 1: `bang_cham_cong` (Bảng Chấm Công)
**Các trường:**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `employee_id` | Many2one(hr.employee) | Nhân viên |
| `ngay_cham_cong` | Date | Ngày chấm công |
| `ca_lam` | Selection | Ca làm: Sáng/Chiều/Cả ngày |
| `gio_vao_ca` | Datetime (Computed) | Giờ vào ca theo quy định |
| `gio_ra_ca` | Datetime (Computed) | Giờ ra ca theo quy định |
| `gio_vao` | Datetime | Giờ vào thực tế (từ check-in) |
| `gio_ra` | Datetime | Giờ ra thực tế (từ check-out) |
| `phut_di_muon` | Float (Computed) | Số phút đi muộn (phút) |
| `phut_ve_som` | Float (Computed) | Số phút về sớm (phút) |
| `trang_thai` | Selection (Computed) | Trạng thái: di_lam, di_muon, ve_som, vang_mat, vang_mat_co_phep |
| `Id_BCC` | Char (Computed) | ID tự động: "TênNV_YYYY-MM-DD" |

**Định nghĩa ca làm:**
```
- Ca Sáng:    07:30 - 11:30 (4 giờ)
- Ca Chiều:   13:30 - 17:30 (4 giờ)
- Cả ngày:    07:30 - 17:30 (8 giờ, có 1 giờ nghỉ trưa)
```

**Các trạng thái trang_thai:**
```
- 'di_lam'               → Đi làm bình thường (không muộn, không về sớm)
- 'di_muon'              → Đi muộn (phut_di_muon > 0)
- 've_som'               → Về sớm (phut_ve_som > 0)
- 'di_muon_ve_som'       → Đi muộn và về sớm
- 'vang_mat'             → Vắng mặt (không có gio_vao và gio_ra)
- 'vang_mat_co_phep'     → Vắng mặt có phép
```

#### Model 2: `trang_thai_cham_cong` (Trạng thái Chấm Công)
- Model đơn giản lưu danh sách các trạng thái có thể dùng

#### Extension của Module: `hr.attendance`
**Mối quan hệ:**
- Extends model `hr.attendance` từ module hr_attendance
- Thêm trường: `bang_cham_cong_id` - tham chiếu tới bang_cham_cong

**Key Method:**
- `create()` - Tạo attendance → tự động gọi `_sync_to_bang_cham_cong()`
- `write()` - Cập nhật attendance → tự động đồng bộ
- `_sync_to_bang_cham_cong()` - Đồng bộ dữ liệu từ hr.attendance → bang_cham_cong
  - Lấy giờ check-in từ attendance
  - Xác định ca làm dựa trên giờ check-in và tổng số giờ làm
  - Tạo hoặc cập nhật record bang_cham_cong
  - **TỰ ĐỘNG TRIGGER cập nhật bảng lương**
- `_xac_dinh_ca_lam()` - Xác định ca làm:
  - Nếu tổng số giờ ≥ 7 giờ → Cả ngày
  - Nếu check-in trước 12:00 → Ca Sáng
  - Nếu check-in từ 12:00 → Ca Chiều

#### Dependencies:
```
- base
- hr
- hr_attendance
```

#### Workflow tạo dữ liệu:
1. Nhân viên check-in/check-out trong `hr.attendance`
2. Tự động tạo/cập nhật `bang_cham_cong`
3. Tính toán trạng thái, phút muộn, phút sớm
4. **Tự động cập nhật `bang_tinh_luong`** thông qua `_cap_nhat_bang_luong()`

---

### 3. MODULE TINH_LUONG (Tính Lương)
**Đường dẫn:** `addons/tinh_luong/`

#### Mục đích/Mô tả:
- Tự động tính toán lương hàng tháng dựa trên chấm công
- Tổng hợp thông tin công việc từ bảng chấm công
- Tính toán các khoản trừ (đi muộn, về sớm)
- Tổng hợp lương thực nhận

#### Extension của HR: `hr.employee`
**Các trường mở rộng:**
```python
luong_co_ban          # Lương cơ bản (VND)
phu_cap_co_dinh       # Phụ cấp cố định (VND)
currency_id           # Tiền tệ (liên kết tới res.currency)
```

#### Model: `bang_tinh_luong` (Bảng Tính Lương)
**Các trường cơ bản:**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `name` | Char (Computed) | Tên: "Lương [TênNV] [Tháng]/[Năm]" |
| `employee_id` | Many2one(hr.employee) | Nhân viên |
| `thang` | Selection | Tháng (1-12) |
| `nam` | Char | Năm |
| `ngay_bat_dau` | Date (Computed) | Ngày 1 của tháng |
| `ngay_ket_thuc` | Date (Computed) | Ngày cuối cùng của tháng |

**Cấu hình:**

| Trường | Giá trị mặc định | Mô tả |
|--------|-----------------|-------|
| `cong_chuan` | 26 | Số công chuẩn/tháng |
| `gio_mot_cong` | 8.0 | Giờ/1 công (giờ) |
| `buoc_lam_tron_phut` | 30 | Bước làm tròn (phút) |
| `kieu_lam_tron` | 'nearest' | Kiểu làm tròn: nearest/floor/ceil |
| `muc_phat_moi_phut` | 5000 | Mức phạt mỗi phút (VND) |

**Thông tin lương:**

| Trường | Kiểu | Mô tả | Công thức |
|--------|------|-------|-----------|
| `luong_co_ban` | Monetary | Lương cơ bản | Từ hr.employee |
| `phu_cap_co_dinh` | Monetary | Phụ cấp cố định | Từ hr.employee |
| `don_gia_cong` | Monetary (Computed) | Đơn giá công | luong_co_ban / cong_chuan |
| `currency_id` | Many2one | Tiền tệ | Mặc định công ty |

**Thống kê công việc (từ bang_cham_cong):**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `so_ngay_cong` | Float (Computed) | Số ngày công đã làm |
| `so_gio_cong` | Float (Computed) | Tổng giờ công (đã làm tròn) |
| `so_ngay_vang_khong_phep` | Float (Computed) | Vắng không phép (ngày) |
| `so_ngay_vang_co_phep` | Float (Computed) | Vắng có phép (ngày) |
| `tong_phut_di_muon` | Float (Computed) | Tổng phút đi muộn |
| `tong_phut_ve_som` | Float (Computed) | Tổng phút về sớm |

**Tính toán lương:**

| Trường | Công thức | Mô tả |
|--------|-----------|-------|
| `tien_cong` | don_gia_cong × so_ngay_cong | Tiền công (tính theo công đã làm) |
| `tien_phat` | (tong_phut_di_muon + tong_phut_ve_som) × muc_phat_moi_phut | Tiền phạt |
| `luong_thuc_nhan` | tien_cong + phu_cap_co_dinh - tien_phat | **Lương thực nhận** |

#### Key Methods:

**`_compute_thong_ke_cong()`** - Tổng hợp công từ bang_cham_cong:
```
1. Truy vấn tất cả bang_cham_cong của nhân viên trong khoảng ngày tháng
2. Thống kê:
   - so_ngay_cong (số ngày công):
     * Ca Cả ngày = 1 công
     * Ca Sáng/Chiều = 0.5 công
   - so_gio_cong: Tổng (gio_ra - gio_vao), làm tròn theo buoc_lam_tron_phut
   - so_ngay_vang_khong_phep: Từ trang_thai = 'vang_mat'
   - so_ngay_vang_co_phep: Từ trang_thai = 'vang_mat_co_phep'
   - tong_phut_di_muon: Tổng phut_di_muon
   - tong_phut_ve_som: Tổng phut_ve_som
3. Quy đổi giờ → ngày: so_ngay_cong = so_gio_cong / gio_mot_cong
```

**`_compute_tien_luong()`** - Tính toán tiền lương:
```
1. don_gia_cong = luong_co_ban / cong_chuan
2. tien_cong = don_gia_cong × so_ngay_cong
3. tien_phat = (tong_phut_di_muon + tong_phut_ve_som) × muc_phat_moi_phut
4. luong_thuc_nhan = tien_cong + phu_cap_co_dinh - tien_phat
```

#### Dependencies:
```
- base
- hr (để kế thừa hr.employee)
- hr_attendance (để liên kết với cham_cong)
- cham_cong (để truy vấn bang_cham_cong)
```

---

## 🔄 PHẦN 2: WORKFLOW TỔNG THỂ & LUỒNG DỮ LIỆU

### Quy trình hoạt động từng bước:

#### **Bước 1: Quản lý nhân sự (HR Module)**
```
┌─────────────────────────────────────┐
│ Module HR (hr.employee)             │
├─────────────────────────────────────┤
│ • Tạo/cập nhật hồ sơ nhân viên      │
│ • Ghi nhận:                         │
│   - Tên, phòng ban, chức vụ         │
│   - Lương cơ bản                    │
│   - Phụ cấp cố định                 │
│   - Thông tin cá nhân               │
└─────────────────────────────────────┘
           ↓
    Lưu trữ thông tin
           ↓
┌─────────────────────────────────────┐
│ Dữ liệu sẵn dùng:                   │
│ • id (nhân viên)                    │
│ • name                              │
│ • luong_co_ban                      │
│ • phu_cap_co_dinh                   │
│ • company_id                        │
└─────────────────────────────────────┘
```

#### **Bước 2: Chấm công hàng ngày (CHAM_CONG Module)**
```
┌──────────────────────────────────────┐
│ Quá trình chấm công:                 │
│                                      │
│ 09:00 sáng: Check-in                │
│ → hr.attendance.create()             │
│                                      │
│ 17:00 chiều: Check-out              │
│ → hr.attendance.write()              │
└──────────────────────────────────────┘
           ↓ Tự động (Trigger)
┌──────────────────────────────────────┐
│ CHAM_CONG: _sync_to_bang_cham_cong() │
│                                      │
│ 1. Lấy check_in/check_out            │
│ 2. Xác định ca làm:                 │
│    - Sáng (07:30-11:30)             │
│    - Chiều (13:30-17:30)            │
│    - Cả ngày (07:30-17:30)          │
│ 3. Tạo/cập nhật bang_cham_cong      │
│ 4. Tính toán trạng thái             │
│    - phut_di_muon                   │
│    - phut_ve_som                    │
│    - trang_thai                     │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ BANG_CHAM_CONG Record:               │
│                                      │
│ employee_id = "Nguyễn Văn A"        │
│ ngay_cham_cong = "2024-01-15"       │
│ ca_lam = "Cả ngày"                  │
│ gio_vao = "09:05" (muộn 35 phút)    │
│ gio_ra = "17:15" (về sớm -45 phút)  │
│ phut_di_muon = 35                    │
│ phut_ve_som = 0                      │
│ trang_thai = "di_muon"              │
└──────────────────────────────────────┘
           ↓ Tự động (Trigger)
      _cap_nhat_bang_luong()
           ↓
   (Sẽ chi tiết ở Bước 3)
```

#### **Bước 3: Tính lương hàng tháng (TINH_LUONG Module)**

**Giai đoạn 1: Tạo bảng lương**
```
Khi tới cuối tháng hoặc khi chấm công được tạo:

┌───────────────────────────────────────┐
│ BangTinhLuong.create()                │
│                                       │
│ • employee_id = "Nguyễn Văn A"        │
│ • thang = "1" (Tháng 1)               │
│ • nam = "2024"                        │
│ • ngay_bat_dau = "2024-01-01"         │
│ • ngay_ket_thuc = "2024-01-31"        │
│                                       │
│ Lấy dữ liệu từ hr.employee:           │
│ • luong_co_ban = 10,000,000 VND       │
│ • phu_cap_co_dinh = 2,000,000 VND     │
└───────────────────────────────────────┘
```

**Giai đoạn 2: Thống kê công (từ bang_cham_cong)**
```
SELECT bang_cham_cong
WHERE employee_id = "Nguyễn Văn A"
  AND ngay_cham_cong BETWEEN "2024-01-01" AND "2024-01-31"

Kết quả thống kê (ví dụ):
┌──────────────────────────────────────┐
│ Tháng 1/2024:                        │
│                                      │
│ Tổng cộng 22 ngày làm việc:         │
│ • 18 ngày cả ngày = 18 công         │
│ • 8 ca sáng/chiều = 4 công          │
│ → so_ngay_cong = 22 công            │
│                                      │
│ Tổng số giờ = 176 giờ               │
│ Làm tròn: 176/8 = 22 ngày           │
│ → so_gio_cong = 176 giờ             │
│                                      │
│ Đi muộn:                             │
│ • 3 ngày muộn × 30 phút = 90 phút    │
│ → tong_phut_di_muon = 90 phút       │
│                                      │
│ Về sớm:                              │
│ • 2 ngày sớm × 15 phút = 30 phút     │
│ → tong_phut_ve_som = 30 phút        │
│                                      │
│ Vắng mặt:                            │
│ • Vắng không phép = 2 ngày           │
│ • Vắng có phép = 0 ngày              │
└──────────────────────────────────────┘
```

**Giai đoạn 3: Tính lương**
```
┌──────────────────────────────────────────────┐
│ Công thức tính lương:                        │
├──────────────────────────────────────────────┤
│ 1. Đơn giá công:                             │
│    don_gia_cong = luong_co_ban / cong_chuan │
│    = 10,000,000 / 26 = 384,615 VND/công     │
│                                              │
│ 2. Tiền công:                                │
│    tien_cong = don_gia_cong × so_ngay_cong  │
│    = 384,615 × 22 = 8,461,530 VND           │
│                                              │
│ 3. Tiền phạt:                                │
│    tong_phut_phat = 90 + 30 = 120 phút       │
│    tien_phat = 120 × 5,000 = 600,000 VND    │
│                                              │
│ 4. LƯƠNG THỰC NHẬN:                          │
│    = tien_cong + phu_cap_co_dinh - tien_phat│
│    = 8,461,530 + 2,000,000 - 600,000        │
│    = 9,861,530 VND                          │
└──────────────────────────────────────────────┘
```

---

## 🔗 PHẦN 3: QUAN HỆ VÀ LIÊN KẾT GIỮA CÁC MODULE

### Sơ đồ Mối Quan Hệ:

```
                        ┌─────────────────┐
                        │   HR Module     │
                        │   hr.employee   │
                        ├─────────────────┤
                        │ • id            │
                        │ • name          │
                        │ • luong_co_ban  │
                        │ • phu_cap_etc   │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    ↓                         ↓
          ┌──────────────────┐      ┌──────────────────┐
          │ hr_attendance    │      │  cham_cong       │
          │ (Odoo core)      │      │  (Custom)        │
          └────────┬─────────┘      └──────────────────┘
                   │                        ↑
                   │  check_in/             │ Links via
                   │  check_out             │ bang_cham_cong_id
                   │                        │
                   └────────────┬───────────┘
                                ↓
                        ┌──────────────────────┐
                        │  CHAM_CONG Module    │
                        │  bang_cham_cong      │
                        ├──────────────────────┤
                        │ • employee_id (FK)   │
                        │ • ngay_cham_cong     │
                        │ • ca_lam             │
                        │ • phut_di_muon       │
                        │ • phut_ve_som        │
                        │ • trang_thai         │
                        └──────────┬───────────┘
                                   │
                          Tự động trigger
                   _cap_nhat_bang_luong()
                                   │
                                   ↓
                        ┌──────────────────────┐
                        │ TINH_LUONG Module    │
                        │ bang_tinh_luong      │
                        ├──────────────────────┤
                        │ • employee_id (FK)   │
                        │ • thang, nam         │
                        │ • so_ngay_cong       │
                        │ • tong_phut_muon     │
                        │ • tong_phut_som      │
                        │                      │
                        │ • luong_thuc_nhan ✓  │
                        └──────────────────────┘
```

### Chi tiết Quan Hệ:

#### **HR ↔ CHAM_CONG:**
```
hr.employee (1)  ──────→ (N) bang_cham_cong
  • employee_id là Foreign Key
  • 1 nhân viên có nhiều ngày chấm công
  • Ví dụ: Nguyễn Văn A có 22 records bang_cham_cong cho tháng 1
```

#### **CHAM_CONG ↔ TINH_LUONG:**
```
bang_cham_cong (N) ──→ (1) bang_tinh_luong
  • Mối quan hệ: Nhiều records chấm công được tổng hợp trong 1 bảng lương
  • Ngoại lệ không có FK trực tiếp, nhưng có liên kết logic:
    - Cùng employee_id
    - Cùng khoảng ngày (ngay_bat_dau → ngay_ket_thuc)
```

#### **HR ↔ TINH_LUONG:**
```
hr.employee (1) ──────→ (N) bang_tinh_luong
  • employee_id là Foreign Key
  • 1 nhân viên có 1 bảng lương/tháng
  • Inheritance: tinh_luong extends hr.employee
    - Thêm luong_co_ban
    - Thêm phu_cap_co_dinh
```

---

## 📊 PHẦN 4: CÁC MỘT FLOW HOÀN CHỈNH

### Scenario: Tính lương tháng 1/2024 cho nhân viên Nguyễn Văn A

#### **Timeline Hoạt Động:**

**Ngày 1-31 Tháng 1:**
```
2024-01-02 (Thứ 2):
  08:50 → 17:15: Check-in/Check-out → hr.attendance
         ↓ (Trigger) _sync_to_bang_cham_cong
         → bang_cham_cong: Ca Sáng (08:50-11:30)
         → phut_di_muon = 20
         → trang_thai = 'di_muon'
         ↓ (Trigger) _cap_nhat_bang_luong
         → bang_tinh_luong (1/2024) được tạo/cập nhật
           _compute_thong_ke_cong() chạy lại

2024-01-03 (Thứ 3):
  07:30 → 17:30: Check-in/Check-out → hr.attendance
         ↓ (Trigger) _sync_to_bang_cham_cong
         → bang_cham_cong: Cả ngày
         → phut_di_muon = 0
         → phut_ve_som = 0
         → trang_thai = 'di_lam'
         ↓ (Trigger) _cap_nhat_bang_luong
         → bang_tinh_luong (1/2024) được cập nhật
           so_ngay_cong += 1

... (Lặp lại cho 22 ngày làm việc) ...

2024-01-08 (Ngày vắng):
  (Không có check-in/check-out)
         ↓
         → bang_cham_cong trang_thai = 'vang_mat'
         → bang_tinh_luong: so_ngay_vang_khong_phep += 1

2024-02-01 (Cuối tháng):
  → Bảng lương 1/2024 đã đầy đủ
  → so_ngay_cong = 22 công
  → tong_phut_di_muon = 90 phút
  → tong_phut_ve_som = 30 phút
  → TINH TOÁN LƯƠNG:
     • don_gia_cong = 10,000,000 / 26 = 384,615 VND/công
     • tien_cong = 384,615 × 22 = 8,461,530 VND
     • tien_phat = (90 + 30) × 5,000 = 600,000 VND
     • luong_thuc_nhan = 8,461,530 + 2,000,000 - 600,000
                      = 9,861,530 VND ✓
```

---

## 🔍 PHẦN 5: ĐIỂM CHÍNH & QUY TRÌNH TÓMT

### Quy trình cốt lõi:

| Bước | Hành động | Module | Kết quả |
|------|-----------|--------|---------|
| 1 | Nhân viên check-in/check-out | HR Attendance | `hr.attendance` record tạo/cập nhật |
| 2 | Trigger `_sync_to_bang_cham_cong()` | CHAM_CONG | `bang_cham_cong` tạo/cập nhật với ca làm, giờ vào/ra |
| 3 | Tính toán trạng thái | CHAM_CONG | Tính phut_di_muon, phut_ve_som, trang_thai |
| 4 | Trigger `_cap_nhat_bang_luong()` | CHAM_CONG | Tạo/cập nhật `bang_tinh_luong` |
| 5 | Tổng hợp công tháng | TINH_LUONG | `_compute_thong_ke_cong()` đếm công, giờ, vắng |
| 6 | Tính tiền lương | TINH_LUONG | `_compute_tien_luong()` tính don_gia, tien_cong, tien_phat |
| 7 | Kết quả cuối | TINH_LUONG | `luong_thuc_nhan` = tien_cong + phu_cap - tien_phat |

### Luồng Dữ Liệu:

```
HR.EMPLOYEE (Thông tin nhân viên)
    ↓
    ├─ Lương cơ bản
    ├─ Phụ cấp cố định
    └─ ID nhân viên
         ↓
HR.ATTENDANCE (Check-in/Check-out)
    ↓
BANG_CHAM_CONG (Tính toán chi tiết chấm công)
    ├─ Xác định ca làm
    ├─ Tính phút đi muộn/về sớm
    ├─ Gán trạng thái
    └─ [TRIGGER] Cập nhật bảng lương
         ↓
BANG_TINH_LUONG (Tổng hợp lương tháng)
    ├─ Thống kê công (từ bang_cham_cong)
    ├─ Tính đơn giá công (lương_co_ban / cong_chuan)
    ├─ Tính tiền công (don_gia × so_ngay_cong)
    ├─ Tính tiền phạt (phut_phat × muc_phat)
    └─ KẾT QUẢ: Lương thực nhận
```

### Automation & Triggers:

| Trigger | Khi nào | Hành động | Kết quả |
|---------|---------|----------|---------|
| `hr.attendance.create()` | Tạo check-in/check-out | Gọi `_sync_to_bang_cham_cong()` | Đồng bộ sang `bang_cham_cong` |
| `hr.attendance.write()` | Cập nhật check-in/check-out | Gọi `_sync_to_bang_cham_cong()` | Cập nhật `bang_cham_cong` |
| `bang_cham_cong.create()` | Tạo record chấm công | Gọi `_cap_nhat_bang_luong()` | Tạo/cập nhật `bang_tinh_luong` |
| `bang_cham_cong.write()` | Cập nhật chấm công | Gọi `_cap_nhat_bang_luong()` | Cập nhật `bang_tinh_luong` |
| `bang_tinh_luong` computed fields | Mỗi khi employee_id/thang/nam/dates thay đổi | `_compute_thong_ke_cong()`, `_compute_tien_luong()` | Tính toán lương |

---

## 💡 KẾT LUẬN

### Mục đích chung:
Hệ thống này tự động hóa toàn bộ quy trình từ **chấm công → tính lương**, giảm thiểu nhập liệu thủ công và đảm bảo tính toán lương chính xác dựa trên thực tế.

### Lợi ích:
1. ✓ **Tự động**: Trigger tự động khi check-in/check-out
2. ✓ **Chính xác**: Tính toán dựa trên dữ liệu thực tế
3. ✓ **Linh hoạt**: Cấu hình ca làm, phạt, làm tròn dễ dàng
4. ✓ **Truy vết**: Lịch sử chấm công rõ ràng, có thể kiểm toán

### Mô hình dữ liệu:
```
HR (Nhân sự) → CHAM_CONG (Chấm công) → TINH_LUONG (Lương)
               ↑                          ↑
               └─── Tự động trigger ─────┘
```
