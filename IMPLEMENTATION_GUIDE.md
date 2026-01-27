# IMPLEMENTATION GUIDE & VISUAL DIAGRAMS

---

## 📐 VISUAL DATABASE SCHEMA

### Entity Relationship Diagram (ERD)

```
┌────────────────────────────────────┐
│         HR.EMPLOYEE                │
├────────────────────────────────────┤
│ id (PK)                            │
│ name                               │
│ company_id (FK)                    │
│ department_id (FK)                 │
│ job_id (FK)                        │
│ luong_co_ban ◄─────┐               │
│ phu_cap_co_dinh ◄──┤─────┐         │
│ currency_id        │     │         │
└────────────────────────────────────┘
         ▲                │           │
         │                │           │
         │                ▼           ▼
         │           ┌────────────────────────────┐
         │           │  BANG_TINH_LUONG           │
         │           ├────────────────────────────┤
         │           │ id (PK)                    │
         │           │ employee_id (FK) ──────────┼──→ [hr.employee]
         │           │ thang                      │
         │           │ nam                        │
         │           │ [Computed Fields]          │
         │           │ • so_ngay_cong             │
         │           │ • tien_cong                │
         │           │ • tien_phat                │
         │           │ • luong_thuc_nhan          │
         │           └────────────────────────────┘
         │                   ▲
         │                   │ (Tổng hợp từ)
         │                   │
         │           ┌────────────────────────────┐
         │           │  BANG_CHAM_CONG            │
         │           ├────────────────────────────┤
         │           │ id (PK)                    │
         │           │ employee_id (FK) ──────────┼──→ [hr.employee]
         │           │ ngay_cham_cong             │
         │           │ ca_lam                     │
         │           │ gio_vao                    │
         │           │ gio_ra                     │
         │           │ phut_di_muon               │
         │           │ phut_ve_som                │
         │           │ trang_thai                 │
         │           └────────────────────────────┘
         │                   ▲
         │                   │ (Sync từ)
         │                   │
         └───────────────────┴──────────────────────┐
                         │
                         │
         ┌───────────────────────────────────────────┐
         │      HR.ATTENDANCE                        │
         ├───────────────────────────────────────────┤
         │ id (PK)                                   │
         │ employee_id (FK)                          │
         │ check_in                                  │
         │ check_out                                 │
         │ bang_cham_cong_id (FK) ──────────────────→│
         └───────────────────────────────────────────┘
```

### Data Flow Sequence Diagram

```
Timeline: Một ngày chấm công

┌───────────────┬──────────────┬──────────────┬──────────────┐
│ Thời điểm     │ Hành động     │ Module       │ Kết quả      │
├───────────────┼──────────────┼──────────────┼──────────────┤
│ 09:00 sáng    │ Check-in     │ HR.ATT       │ record tạo   │
└───────────────┴──────────────┴──────────────┴──────────────┘
                              │
                              │ [TRIGGER: create()]
                              ▼
                ┌──────────────────────────────┐
                │ _sync_to_bang_cham_cong()    │
                │ (cham_cong module)           │
                │                              │
                │ 1. Lấy check_in              │
                │ 2. Xác định ca làm           │
                │ 3. Tạo/cập nhật              │
                │    bang_cham_cong            │
                └──────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ BANG_CHAM_CONG  │
                    │ • ca_lam        │
                    │ • gio_vao = 09h │
                    │ • phut_di_muon  │
                    └─────────────────┘
                              │
┌───────────────┬──────────────┼──────────────┬──────────────┐
│ 17:00 chiều   │ Check-out    │ HR.ATT       │ record cập   │
└───────────────┴──────────────┴──────────────┴──────────────┘
                              │
                              │ [TRIGGER: write()]
                              ▼
                ┌──────────────────────────────┐
                │ _sync_to_bang_cham_cong()    │
                │ (cham_cong module)           │
                │                              │
                │ 1. Lấy check_out             │
                │ 2. Tính phut_ve_som          │
                │ 3. Cập nhật bang_cham_cong   │
                └──────────────────────────────┘
                              │
                              ▼
                ┌──────────────────────────────┐
                │ _cap_nhat_bang_luong()       │
                │ (cham_cong module)           │
                │                              │
                │ Tạo/cập nhật:                │
                │ bang_tinh_luong (1/2024)     │
                └──────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ BANG_TINH_LUONG │
                    │ • so_ngay_cong  │
                    │ • tien_cong     │
                    │ • tien_phat     │
                    │ • luong_thuc... │
                    └─────────────────┘
```

---

## 🚀 IMPLEMENTATION WORKFLOW

### Step-by-Step Implementation

#### **Phase 1: Setup HR Module** (Base)
```
Status: ✓ Done (Odoo Standard)

Structure:
  addons/hr/
  ├── models/
  │   ├── hr_employee.py (main model)
  │   ├── hr_department.py
  │   ├── hr_job.py
  │   └── ...
  ├── views/
  │   ├── hr_employee_views.xml
  │   └── ...
  └── security/
      └── ir.model.access.csv

Key Actions:
  1. Create employees with:
     - luong_co_ban (Lương cơ bản)
     - phu_cap_co_dinh (Phụ cấp cố định)
     - company_id
     - department_id
     - job_id
```

#### **Phase 2: Setup CHAM_CONG Module** (Custom)
```
Status: ✓ Done (Installed)

Structure:
  addons/cham_cong/
  ├── models/
  │   ├── bang_cham_cong.py (main model)
  │   ├── hr_attendance.py (extend hr.attendance)
  │   └── ...
  ├── views/
  │   └── bang_cham_cong.xml
  ├── security/
  │   └── ir.model.access.csv
  └── __manifest__.py

Key Objects:
  - TrangThaiChamCong (status master)
  - BangChamCong (attendance records)
  - Extended HR.Attendance

Flow:
  HR.Attendance.create() 
    → _sync_to_bang_cham_cong()
    → BangChamCong created/updated
    → Computed fields calculated
    → _cap_nhat_bang_luong() triggered
```

#### **Phase 3: Setup TINH_LUONG Module** (Custom)
```
Status: ✓ Done (Installed)

Structure:
  addons/tinh_luong/
  ├── models/
  │   ├── bang_tinh_luong.py (main model)
  │   ├── nhan_vien.py (extend hr.employee)
  │   └── ...
  ├── views/
  │   ├── bang_tinh_luong.xml
  │   └── ...
  ├── security/
  │   └── ir.model.access.csv
  └── __manifest__.py

Key Objects:
  - BangTinhLuong (payroll records)
  - Extended HR.Employee

Flow:
  BangTinhLuong.create()
    → _compute_thong_ke_cong() (tính công từ bang_cham_cong)
    → _compute_tien_luong() (tính tiền lương)
    → Kết quả: luong_thuc_nhan
```

---

## 📋 DATA OPERATION EXAMPLES

### Example 1: Create Employee

```python
# Tạo nhân viên
employee = self.env['hr.employee'].create({
    'name': 'Nguyễn Văn A',
    'company_id': 1,
    'department_id': 1,
    'job_id': 1,
    'luong_co_ban': 10000000,  # 10 triệu VND
    'phu_cap_co_dinh': 2000000,  # 2 triệu VND
    'currency_id': 1,
})
# Kết quả: Nhân viên được tạo với ID = employee.id
```

### Example 2: Check-in/Check-out

```python
# Nhân viên check-in vào 09:00
attendance = self.env['hr.attendance'].create({
    'employee_id': employee.id,
    'check_in': datetime(2024, 1, 2, 9, 0, 0),
})
# [TRIGGER] _sync_to_bang_cham_cong()
# Result: BangChamCong record created
#   - ca_lam = 'Sáng' (check-in trước 12:00)
#   - phut_di_muon = 30 (07:30 → 09:00)

# Nhân viên check-out vào 17:30
attendance.write({
    'check_out': datetime(2024, 1, 2, 17, 30, 0),
})
# [TRIGGER] _sync_to_bang_cham_cong()
# Result: BangChamCong updated
#   - ca_lam = 'Cả ngày' (so_gio >= 7)
#   - phut_ve_som = 0 (17:30 = 17:30, không về sớm)
#   - trang_thai = 'di_muon'

# [TRIGGER] _cap_nhat_bang_luong()
# Result: BangTinhLuong (1/2024) created/updated
```

### Example 3: Calculate Payroll

```python
# Tạo bảng lương cho tháng 1/2024
payroll = self.env['bang_tinh_luong'].create({
    'employee_id': employee.id,
    'thang': '1',
    'nam': '2024',
})

# [AUTO-COMPUTE] _compute_thong_ke_cong()
# Query BangChamCong từ 2024-01-01 đến 2024-01-31
# Kết quả:
payroll.so_ngay_cong  # = 22 (ngày công đã làm)
payroll.so_gio_cong   # = 176 (giờ công)
payroll.tong_phut_di_muon  # = 90 phút
payroll.tong_phut_ve_som   # = 30 phút

# [AUTO-COMPUTE] _compute_tien_luong()
payroll.don_gia_cong  # = 10,000,000 / 26 = 384,615 VND/công
payroll.tien_cong     # = 384,615 × 22 = 8,461,530 VND
payroll.tien_phat     # = (90 + 30) × 5,000 = 600,000 VND
payroll.luong_thuc_nhan  # = 8,461,530 + 2,000,000 - 600,000
                         # = 9,861,530 VND
```

---

## 🔍 DEBUGGING CHECKLIST

### If Payroll Calculation is Wrong

```
┌─ Check Employee Data
│  └─ luong_co_ban set?
│  └─ phu_cap_co_dinh set?
│
├─ Check Attendance Data
│  └─ check_in/check_out exist?
│  └─ Correct employee_id?
│
├─ Check BangChamCong
│  └─ Records created for the month?
│  └─ trang_thai calculated?
│  └─ phut_di_muon, phut_ve_som correct?
│
├─ Check BangTinhLuong
│  └─ Record exists for month?
│  └─ so_ngay_cong calculated?
│  └─ tien_cong formula correct?
│  └─ tien_phat formula correct?
│
└─ Check Configuration
   └─ cong_chuan = 26?
   └─ gio_mot_cong = 8.0?
   └─ muc_phat_moi_phut = 5000?
   └─ buoc_lam_tron_phut = 30?
```

### SQL Queries for Verification

```sql
-- Check employee data
SELECT id, name, luong_co_ban, phu_cap_co_dinh 
FROM hr_employee 
WHERE name LIKE 'Nguyễn%';

-- Check attendance records
SELECT id, employee_id, check_in, check_out 
FROM hr_attendance 
WHERE employee_id = X;

-- Check bang_cham_cong records
SELECT id, employee_id, ngay_cham_cong, ca_lam, 
       phut_di_muon, phut_ve_som, trang_thai 
FROM bang_cham_cong 
WHERE employee_id = X AND MONTH(ngay_cham_cong) = 1;

-- Check payroll
SELECT id, employee_id, thang, nam, 
       so_ngay_cong, tien_cong, tien_phat, luong_thuc_nhan 
FROM bang_tinh_luong 
WHERE employee_id = X AND thang = '1' AND nam = '2024';
```

---

## 🛠️ COMMON CUSTOMIZATIONS

### Customization 1: Change Shift Times

**File:** `addons/cham_cong/models/bang_cham_cong.py`

```python
@api.depends('ca_lam', 'ngay_cham_cong')
def _compute_gio_ca(self):
    for record in self:
        if record.ca_lam == "Sáng":
            gio_vao = time(8, 0)   # Thay từ 7:30 → 8:00
            gio_ra = time(12, 0)   # Thay từ 11:30 → 12:00
        elif record.ca_lam == "Chiều":
            gio_vao = time(14, 0)  # Thay từ 13:30 → 14:00
            gio_ra = time(18, 0)   # Thay từ 17:30 → 18:00
        # ...
```

### Customization 2: Change Penalty Calculation

**File:** `addons/tinh_luong/models/bang_tinh_luong.py`

```python
def _compute_tien_luong(self):
    for record in self:
        # Phạt chỉ tính cho đi muộn, không tính về sớm
        tong_phut_phat = record.tong_phut_di_muon  # Bỏ tong_phut_ve_som
        record.tien_phat = record.muc_phat_moi_phut * tong_phut_phat
```

### Customization 3: Add Bonus for Good Attendance

**File:** `addons/tinh_luong/models/bang_tinh_luong.py`

```python
def _compute_tien_luong(self):
    for record in self:
        # ... existing code ...
        
        # Add bonus if no late/early
        tien_thuong = 0
        if record.tong_phut_di_muon == 0 and record.tong_phut_ve_som == 0:
            tien_thuong = 500000  # 500k bonus
        
        record.luong_thuc_nhan = (record.tien_cong + 
                                  record.phu_cap_co_dinh + 
                                  tien_thuong - 
                                  record.tien_phat)
```

---

## 📊 SAMPLE DATA VALIDATION

### Validation Case 1: Full Month

```
Employee: Nguyễn Văn A
Month: 1/2024 (22 working days)
Shift: Cả ngày (07:30-17:30)

Attendance Record:
┌─────────┬──────────┬──────────┬──────────┐
│ Date    │ Check-in │ Check-out│ Result   │
├─────────┼──────────┼──────────┼──────────┤
│ 2024-01-02│ 07:30 │ 17:30   │ di_lam   │
│ 2024-01-03│ 08:00 │ 17:30   │ di_muon  │
│ 2024-01-04│ 07:30 │ 17:00   │ ve_som   │
│ ... (19 more days all normal) ...      │
└─────────┴──────────┴──────────┴──────────┘

Total:
- so_ngay_cong = 22
- tong_phut_di_muon = 30 phút (1 ngày muộn × 30 phút)
- tong_phut_ve_som = 30 phút (1 ngày về sớm × 30 phút)

Payroll Calculation:
- don_gia_cong = 10,000,000 / 26 = 384,615
- tien_cong = 384,615 × 22 = 8,461,530
- tien_phat = (30 + 30) × 5,000 = 300,000
- luong_thuc_nhan = 8,461,530 + 2,000,000 - 300,000 = 10,161,530 VND ✓
```

---

## 🎓 BEST PRACTICES

### 1. Data Integrity
```
✓ Always set luong_co_ban and phu_cap_co_dinh before month-end
✓ Ensure employee belongs to correct company
✓ Validate timezone settings in system configuration
✓ Monitor for duplicate bang_cham_cong records
```

### 2. Performance
```
✓ Archive old bang_tinh_luong records (older than 1 year)
✓ Index on (employee_id, ngay_cham_cong) in bang_cham_cong
✓ Index on (employee_id, thang, nam) in bang_tinh_luong
✓ Use cron jobs to batch process payroll
```

### 3. Testing
```
✓ Test with various shift times (Morning, Afternoon, Full)
✓ Test with edge cases (Absence, Late, Early)
✓ Test mid-month salary changes
✓ Test timezone conversions
```

### 4. Reporting
```
✓ Generate monthly payroll report
✓ Audit trail for salary changes
✓ Attendance variance report
✓ Penalty breakdown report
```

