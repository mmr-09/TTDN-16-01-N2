# TECHNICAL SPECIFICATION: HR - CHAM_CONG - TINH_LUONG

---

## 📋 SPECIFICATIONS BY MODULE

### MODULE 1: HR (addons/hr/)

#### Database Structure

**Model: `hr.employee` (Extended in tinh_luong)**

Fields from base HR module:
```
- id                              : Integer (Primary Key)
- name                            : Char (employee name)
- resource_id                     : Many2one('resource.resource')
- user_id                         : Many2one('res.users')
- active                          : Boolean (default: True)
- company_id                      : Many2one('res.company') - REQUIRED
- department_id                   : Many2one('hr.department')
- job_id                          : Many2one('hr.job')
- address_home_id                 : Many2one('res.partner')
- work_email                      : Char
- phone                           : Char
- mobile_phone                    : Char
- barcode                         : Char (unique per company)
- pin                             : Char (PIN for attendance)
- birthday                        : Date
- gender                          : Selection (male, female, other)
- marital                         : Selection (single, married, etc.)
- passport_id                     : Char
- bank_account_id                 : Many2one('res.partner.bank')
```

Extensions from tinh_luong module:
```
- luong_co_ban                    : Monetary (basic salary)
- phu_cap_co_dinh                 : Monetary (fixed allowance)
- currency_id                     : Many2one('res.currency')
```

**Related Models:**
- `hr.department` - phòng ban
- `hr.job` - chức vụ
- `res.company` - công ty
- `res.users` - tài khoản người dùng

**Access Control:**
- Module: `hr`
- Security group: `hr.group_hr_user` (read), `hr.group_hr_manager` (write)

#### Key Methods

```python
def create(self, vals):
    """
    Tạo nhân viên mới
    - Đồng bộ thông tin từ user (email, timezone, avatar)
    - Subscribe địa chỉ cá nhân vào mail channel
    - Launch onboarding plans
    """

def _sync_user(self, user, employee_has_image=False):
    """
    Đồng bộ thông tin từ user account
    Returns: dict với fields cần update
    """

@api.constrains('pin')
def _verify_pin(self):
    """
    Validate PIN là dãy số
    Raises: ValidationError nếu PIN không hợp lệ
    """
```

---

### MODULE 2: CHAM_CONG (addons/cham_cong/)

#### Database Structure

**Model: `bang_cham_cong` (Bảng Chấm Công)**

```
Trường (Field)           Type          Mô tả
───────────────────────────────────────────────────────
employee_id              Many2one      Nhân viên (FK → hr.employee) [REQUIRED]
ngay_cham_cong           Date          Ngày chấm công [REQUIRED]
ca_lam                   Selection     Ca làm (Sáng/Chiều/Cả ngày) [DEFAULT: ""]

gio_vao_ca               Datetime      Giờ vào ca theo quy định [COMPUTED]
gio_ra_ca                Datetime      Giờ ra ca theo quy định [COMPUTED]

gio_vao                  Datetime      Giờ vào thực tế (từ check-in)
gio_ra                   Datetime      Giờ ra thực tế (từ check-out)

phut_di_muon_goc         Float         Phút đi muộn gốc [COMPUTED]
phut_di_muon             Float         Phút đi muộn thực tế [COMPUTED]

phut_ve_som_goc          Float         Phút về sớm gốc [COMPUTED]
phut_ve_som              Float         Phút về sớm thực tế [COMPUTED]

trang_thai               Selection     Trạng thái [COMPUTED]
                                       - 'di_lam': Đi làm bình thường
                                       - 'di_muon': Đi muộn
                                       - 've_som': Về sớm
                                       - 'di_muon_ve_som': Đi muộn và về sớm
                                       - 'vang_mat': Vắng mặt
                                       - 'vang_mat_co_phep': Vắng mặt có phép

Id_BCC                   Char          ID tự động {TênNV}_{YYYY-MM-DD} [COMPUTED]
```

**Default Shift Times:**
```
ca_lam = "Sáng":
  gio_vao_ca = 07:30
  gio_ra_ca  = 11:30
  Tổng: 4 giờ

ca_lam = "Chiều":
  gio_vao_ca = 13:30
  gio_ra_ca  = 17:30
  Tổng: 4 giờ

ca_lam = "Cả ngày":
  gio_vao_ca = 07:30
  gio_ra_ca  = 17:30
  Tổng: 10 giờ (- 1 giờ nghỉ trưa = 9 giờ công, tương đương 8h theo chuẩn)
```

**Constraints:**
```sql
UNIQUE (employee_id, ngay_cham_cong) -- Một record/ngày/nhân viên
```

**Related Models:**
- `hr.employee` - nhân viên
- `bang_tinh_luong` - bảng tính lương

#### Key Methods

**Computed Fields Dependencies:**

```python
@api.depends('ca_lam', 'ngay_cham_cong')
def _compute_gio_ca(self):
    """
    Tính giờ vào/ra ca theo quy định dựa trên ca_lam
    - Chuyển timezone từ user → UTC
    - Gán gio_vao_ca, gio_ra_ca
    """

@api.depends('gio_vao', 'gio_vao_ca')
def _compute_phut_di_muon_goc(self):
    """
    phut_di_muon_goc = max(0, (gio_vao - gio_vao_ca) in minutes)
    """

@api.depends('gio_ra', 'gio_ra_ca')
def _compute_phut_ve_som_goc(self):
    """
    phut_ve_som_goc = max(0, (gio_ra_ca - gio_ra) in minutes)
    """

@api.depends('phut_di_muon', 'phut_ve_som', 'gio_vao', 'gio_ra')
def _compute_trang_thai(self):
    """
    Logic:
    if not gio_vao and not gio_ra:
        trang_thai = 'vang_mat'
    elif phut_di_muon > 0 and phut_ve_som > 0:
        trang_thai = 'di_muon_ve_som'
    elif phut_di_muon > 0:
        trang_thai = 'di_muon'
    elif phut_ve_som > 0:
        trang_thai = 've_som'
    else:
        trang_thai = 'di_lam'
    """
```

**Lifecycle Methods:**

```python
@api.model
def create(self, vals):
    """
    1. Tạo record bang_cham_cong
    2. Trigger: _cap_nhat_bang_luong()
       → Tạo/cập nhật bang_tinh_luong
    """

def write(self, vals):
    """
    1. Cập nhật record bang_cham_cong
    2. Trigger: _cap_nhat_bang_luong()
       → Cập nhật bang_tinh_luong
    """

def _cap_nhat_bang_luong(self):
    """
    Tự động tạo/cập nhật bảng lương
    - Trích xuất thang, nam từ ngay_cham_cong
    - Search bang_tinh_luong(employee_id, thang, nam)
    - If not found: Create
    - If found: Trigger recompute (_compute_thong_ke_cong)
    """
```

---

**Extension: `hr.attendance` (Mở rộng từ module hr_attendance)**

```
Trường mới:
───────────────────────────────────────────────────────
bang_cham_cong_id      Many2one      Liên kết tới bang_cham_cong
                                     (ondelete='set null')

Lifecycle:
───────────────────────────────────────────────────────
create()    → Tạo hr.attendance → _sync_to_bang_cham_cong()
write()     → Cập nhật hr.attendance → _sync_to_bang_cham_cong()
```

**Key Method:**

```python
def _sync_to_bang_cham_cong(self):
    """
    Đồng bộ dữ liệu từ hr.attendance → bang_cham_cong
    
    Quy trình:
    1. Lấy check_in → chuyển timezone → lấy ngay_cham_cong
    2. Tính so_gio = (check_out - check_in) / 3600
    3. Gọi _xac_dinh_ca_lam(gio_check_in, so_gio)
    4. Tạo/cập nhật bang_cham_cong với:
       - employee_id
       - ngay_cham_cong
       - ca_lam
       - gio_vao = check_in
       - gio_ra = check_out
    5. Trigger: _cap_nhat_bang_luong()
    """

def _xac_dinh_ca_lam(self, gio_check_in, so_gio):
    """
    Xác định ca làm dựa trên giờ check-in và tổng số giờ
    
    Logic:
    - if so_gio >= 7: return 'Cả ngày'
    - elif gio_check_in < 12:00: return 'Sáng'
    - else: return 'Chiều'
    """
```

#### Database Relationships

```
hr.attendance (1) ──→ (1) bang_cham_cong
                        ↓ (employee_id)
                    (1) hr.employee
```

---

### MODULE 3: TINH_LUONG (addons/tinh_luong/)

#### Database Structure

**Model: `bang_tinh_luong` (Bảng Tính Lương)**

```
Trường (Field)              Type           Mô tả
──────────────────────────────────────────────────────
employee_id                 Many2one       Nhân viên (FK → hr.employee) [REQUIRED]
thang                       Selection      Tháng (1-12) [REQUIRED]
nam                         Char           Năm [REQUIRED]

name                        Char           Tên: "Lương [TênNV] [Tháng]/[Năm]" [COMPUTED]
ngay_bat_dau                Date           Ngày 1 của tháng [COMPUTED]
ngay_ket_thuc               Date           Ngày cuối cùng của tháng [COMPUTED]

cong_chuan                  Integer        Công chuẩn (default: 26) [DEFAULT: 26]
gio_mot_cong                Float          Giờ/1 công (default: 8.0) [DEFAULT: 8.0]
buoc_lam_tron_phut          Integer        Bước làm tròn (phút) [DEFAULT: 30]
kieu_lam_tron               Selection      Kiểu làm tròn (nearest/floor/ceil) [DEFAULT: 'nearest']
muc_phat_moi_phut           Monetary       Mức phạt/phút (default: 5000) [DEFAULT: 5000]

luong_co_ban                Monetary       Lương cơ bản (từ hr.employee) [COMPUTED]
phu_cap_co_dinh             Monetary       Phụ cấp cố định (từ hr.employee) [COMPUTED]
currency_id                 Many2one       Tiền tệ [DEFAULT: company currency]

so_ngay_cong                Float          Số ngày công đã làm [COMPUTED]
so_gio_cong                 Float          Tổng giờ công (đã làm tròn) [COMPUTED]
so_ngay_vang_khong_phep     Float          Vắng không phép (ngày) [COMPUTED]
so_ngay_vang_co_phep        Float          Vắng có phép (ngày) [COMPUTED]
tong_phut_di_muon           Float          Tổng phút đi muộn [COMPUTED]
tong_phut_ve_som            Float          Tổng phút về sớm [COMPUTED]

don_gia_cong                Monetary       Đơn giá công [COMPUTED]
tien_cong                   Monetary       Tiền công [COMPUTED]
tien_phat                   Monetary       Tiền phạt [COMPUTED]
luong_thuc_nhan             Monetary       Lương thực nhận [COMPUTED]
```

**Constraints:**
```sql
UNIQUE (employee_id, thang, nam) -- Một record/tháng/nhân viên
```

**Related Models:**
- `hr.employee` - nhân viên (liên kết để lấy lương_co_ban, phu_cap)
- `bang_cham_cong` - bảng chấm công (source dữ liệu tính lương)
- `res.currency` - tiền tệ

#### Key Computed Fields & Formulas

**1. Thống kê công từ bang_cham_cong:**

```python
@api.depends('employee_id', 'ngay_bat_dau', 'ngay_ket_thuc', 
             'buoc_lam_tron_phut', 'kieu_lam_tron', 'gio_mot_cong')
def _compute_thong_ke_cong(self):
    """
    Lấy tất cả bang_cham_cong của nhân viên trong tháng
    Thống kê:
    
    so_ngay_cong:
    - Ca Cả ngày = 1 công
    - Ca Sáng/Chiều = 0.5 công
    
    so_gio_cong:
    - Tính từ (gio_ra - gio_vao) mỗi ngày
    - Làm tròn theo buoc_lam_tron_phut
    - Mode: nearest (mặc định), floor, hoặc ceil
    - Chia cho gio_mot_cong để quy về ngày
    
    so_ngay_vang_khong_phep:
    - Đếm trang_thai = 'vang_mat'
    
    so_ngay_vang_co_phep:
    - Đếm trang_thai = 'vang_mat_co_phep'
    
    tong_phut_di_muon:
    - Tổng của phut_di_muon từ các ngày
    
    tong_phut_ve_som:
    - Tổng của phut_ve_som từ các ngày
    """
```

**Ví dụ tính so_ngay_cong:**
```
Giả sử tháng 1 có:
- 18 ngày cả ngày = 18 × 1 = 18 công
- 8 ca sáng/chiều = 4 × 0.5 = 4 công
→ so_ngay_cong = 22 công

Hoặc tính từ giờ:
- Tổng 176 giờ (22 × 8)
- so_gio_cong = 176 / 8 = 22 ngày
```

**2. Tính lương:**

```python
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
    """
    don_gia_cong = luong_co_ban / cong_chuan
    
    tien_cong = don_gia_cong × so_ngay_cong
    
    tong_phut_phat = tong_phut_di_muon + tong_phut_ve_som
    tien_phat = tong_phut_phat × muc_phat_moi_phut
    
    luong_thuc_nhan = tien_cong + phu_cap_co_dinh - tien_phat
    """
```

#### Formulas in Detail

**Công Thức 1: Đơn giá công**
```
don_gia_cong = luong_co_ban / cong_chuan

Ví dụ:
- luong_co_ban = 10,000,000 VND
- cong_chuan = 26
→ don_gia_cong = 10,000,000 / 26 = 384,615 VND/công
```

**Công Thức 2: Tiền công**
```
tien_cong = don_gia_cong × so_ngay_cong

Ví dụ:
- don_gia_cong = 384,615
- so_ngay_cong = 22
→ tien_cong = 384,615 × 22 = 8,461,530 VND
```

**Công Thức 3: Tiền phạt**
```
tong_phut_phat = tong_phut_di_muon + tong_phut_ve_som
tien_phat = tong_phut_phat × muc_phat_moi_phut

Ví dụ:
- tong_phut_di_muon = 90 phút
- tong_phut_ve_som = 30 phút
- muc_phat_moi_phut = 5,000 VND
- tong_phut_phat = 90 + 30 = 120 phút
→ tien_phat = 120 × 5,000 = 600,000 VND
```

**Công Thức 4: Lương Thực Nhận**
```
luong_thuc_nhan = tien_cong + phu_cap_co_dinh - tien_phat

Ví dụ:
- tien_cong = 8,461,530
- phu_cap_co_dinh = 2,000,000
- tien_phat = 600,000
→ luong_thuc_nhan = 8,461,530 + 2,000,000 - 600,000
                  = 9,861,530 VND
```

#### Key Methods

```python
@api.depends('employee_id', 'thang', 'nam')
def _compute_name(self):
    """
    name = f"Lương {employee_id.name} {thang}/{nam}"
    """

@api.depends('thang', 'nam')
def _compute_ngay(self):
    """
    Tính ngày bắt đầu và kết thúc của tháng
    - ngay_bat_dau = date(nam, thang, 1)
    - ngay_ket_thuc = date(nam, thang, last_day)
    """

@api.depends('employee_id')
def _compute_thong_tin_luong(self):
    """
    Lấy luong_co_ban, phu_cap_co_dinh từ hr.employee
    """
```

---

## 🔄 INTEGRATION & DATA FLOW

### Data Flow Diagram

```
┌──────────────────────┐
│  HR.EMPLOYEE         │ ← Employee Info
│  • name              │
│  • luong_co_ban      │
│  • phu_cap_co_dinh   │
└──────┬───────────────┘
       │
       ├─────────────────────────────────┐
       │                                 │
       ↓                                 ↓
┌──────────────────────┐      ┌──────────────────────┐
│ HR.ATTENDANCE        │      │  BANG_TINH_LUONG     │
│ • check_in           │      │  (Khởi tạo với      │
│ • check_out          │      │   luong_co_ban,      │
└──────┬───────────────┘      │   phu_cap_co_dinh)   │
       │                      └──────┬───────────────┘
       │ [TRIGGER]                   │
       │ _sync_to_bang_cham_cong()   │
       ↓                             │
┌──────────────────────┐             │
│ BANG_CHAM_CONG       │             │
│ • ca_lam             │             │
│ • phut_di_muon       │             │
│ • phut_ve_som        │             │
│ • trang_thai         │             │
└──────┬───────────────┘             │
       │                             │
       │ [TRIGGER]                   │
       │ _cap_nhat_bang_luong()      │
       └────────┬────────────────────┘
                │
                ↓
        ┌──────────────────────┐
        │ BANG_TINH_LUONG      │
        │ (Cập nhật)           │
        │ • so_ngay_cong       │
        │ • tong_phut_muon     │
        │ • tong_phut_som      │
        └──────┬───────────────┘
               │ [COMPUTED]
               │ _compute_thong_ke_cong()
               │ _compute_tien_luong()
               ↓
        ┌──────────────────────┐
        │ RESULT:              │
        │ • don_gia_cong       │
        │ • tien_cong          │
        │ • tien_phat          │
        │ • luong_thuc_nhan ✓  │
        └──────────────────────┘
```

### Trigger Chain

```
HR.ATTENDANCE.create() or .write()
    ↓
    _sync_to_bang_cham_cong() [hr.attendance extended method]
        Creates/Updates: BANG_CHAM_CONG
        Computes: ca_lam, phut_di_muon, phut_ve_som, trang_thai
    ↓
    _cap_nhat_bang_luong() [bang_cham_cong.create/write method]
        Creates/Updates: BANG_TINH_LUONG
        Triggers: _compute_thong_ke_cong(), _compute_tien_luong()
    ↓
    BANG_TINH_LUONG computed fields are updated automatically
        so_ngay_cong, tien_cong, tien_phat, luong_thuc_nhan
```

---

## 📊 COMPUTED FIELD DEPENDENCIES

### CHAM_CONG Dependencies

```
ca_lam → gio_vao_ca, gio_ra_ca
↓
gio_vao, gio_ra → phut_di_muon_goc, phut_ve_som_goc
↓
phut_di_muon_goc, phut_ve_som_goc → phut_di_muon, phut_ve_som
↓
phut_di_muon, phut_ve_som, gio_vao, gio_ra → trang_thai
```

### TINH_LUONG Dependencies

```
employee_id → luong_co_ban, phu_cap_co_dinh
↓
thang, nam → ngay_bat_dau, ngay_ket_thuc
↓
ngay_bat_dau, ngay_ket_thuc, employee_id → [Query BANG_CHAM_CONG]
↓
[BANG_CHAM_CONG data] → so_ngay_cong, so_gio_cong, tong_phut_*
↓
luong_co_ban, cong_chuan → don_gia_cong
↓
don_gia_cong, so_ngay_cong → tien_cong
↓
tong_phut_*, muc_phat_moi_phut → tien_phat
↓
tien_cong, phu_cap_co_dinh, tien_phat → luong_thuc_nhan
```

---

## 🔒 Security & Access Control

### Access Rules (ACLs)

| Module | Model | Read | Write | Create | Delete |
|--------|-------|------|-------|--------|--------|
| HR | hr.employee | hr.group_hr_user | hr.group_hr_manager | hr.group_hr_manager | hr.group_hr_manager |
| CHAM_CONG | bang_cham_cong | All authenticated | hr.group_hr_manager | All authenticated | hr.group_hr_manager |
| TINH_LUONG | bang_tinh_luong | hr.group_hr_user | hr.group_hr_manager | All authenticated | hr.group_hr_manager |

---

## 🧪 TESTING SCENARIOS

### Scenario 1: Normal Day
```
Employee: Nguyễn Văn A
Date: 2024-01-02

→ Check-in: 07:30
→ Check-out: 17:30
→ Expected: trang_thai = 'di_lam', phut_di_muon = 0, phut_ve_som = 0
```

### Scenario 2: Late
```
Employee: Nguyễn Văn A
Date: 2024-01-03

→ Check-in: 08:00 (muộn 30 phút)
→ Check-out: 17:30
→ Expected: trang_thai = 'di_muon', phut_di_muon = 30
```

### Scenario 3: Absence
```
Employee: Nguyễn Văn A
Date: 2024-01-04

→ No check-in/check-out
→ Expected: trang_thai = 'vang_mat'
```

### Scenario 4: Monthly Payroll
```
Employee: Nguyễn Văn A
Month: 1/2024

Expected Results:
- so_ngay_cong = 22
- don_gia_cong = 10,000,000 / 26 = 384,615 VND/công
- tien_cong = 384,615 × 22 = 8,461,530 VND
- tien_phat = 120 × 5,000 = 600,000 VND
- luong_thuc_nhan = 8,461,530 + 2,000,000 - 600,000 = 9,861,530 VND
```

