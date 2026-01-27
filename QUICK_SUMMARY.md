# TÓMT NGẮN GỌN: Ba Module HR - CHAM_CONG - TINH_LUONG

## 🎯 MỤC ĐÍCH TỪNG MODULE

### 1️⃣ HR Module (Nhân Sự)
- **Nhiệm vụ**: Quản lý thông tin nhân viên
- **Dữ liệu chính**:
  - `hr.employee` → Hồ sơ nhân viên
  - `luong_co_ban` (Lương cơ bản)
  - `phu_cap_co_dinh` (Phụ cấp cố định)
- **Nguồn dữ liệu** cho 2 module sau

### 2️⃣ CHAM_CONG Module (Chấm Công)
- **Nhiệm vụ**: Ghi nhận & tính toán chi tiết chấm công hàng ngày
- **Mô hình**: `bang_cham_cong` (1 record = 1 ngày/1 nhân viên)
- **Tính toán**:
  - Xác định ca làm (Sáng/Chiều/Cả ngày)
  - Phút đi muộn (`phut_di_muon`)
  - Phút về sớm (`phut_ve_som`)
  - Trạng thái (`trang_thai`: di_lam, di_muon, ve_som, vang_mat, ...)
- **Tự động cập nhật** bảng lương khi chấm công thay đổi

### 3️⃣ TINH_LUONG Module (Tính Lương)
- **Nhiệm vụ**: Tổng hợp & tính lương hàng tháng
- **Mô hình**: `bang_tinh_luong` (1 record = 1 tháng/1 nhân viên)
- **Tính toán**:
  - **Tổng hợp công**: so_ngay_cong (từ bang_cham_cong)
  - **Tính lương**: 
    - don_gia_cong = luong_co_ban / cong_chuan
    - tien_cong = don_gia_cong × so_ngay_cong
    - tien_phat = (phut_muon + phut_som) × muc_phat/phut
    - **luong_thuc_nhan** = tien_cong + phu_cap - tien_phat

---

## 🔄 WORKFLOW CHÍNH

```
┌─────────────────────────────────────────────────────────────────┐
│ NGÀY LÀM VIỆC: Nhân viên Check-in/Check-out                    │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
        ┌──────────────────────────────────┐
        │ HR.ATTENDANCE tạo/cập nhật       │
        │ check_in, check_out              │
        └──────────┬───────────────────────┘
                   │ [TRIGGER]
                   ↓
        ┌──────────────────────────────────┐
        │ CHAM_CONG tự động:               │
        │ _sync_to_bang_cham_cong()        │
        │                                  │
        │ 1. Lấy giờ check-in/check-out    │
        │ 2. Xác định ca làm               │
        │ 3. Tính phut_di_muon             │
        │ 4. Tính phut_ve_som              │
        │ 5. Gán trang_thai                │
        └──────────┬───────────────────────┘
                   │ [TRIGGER]
                   ↓
        ┌──────────────────────────────────┐
        │ TINH_LUONG tự động:              │
        │ _cap_nhat_bang_luong()           │
        │                                  │
        │ Tạo/cập nhật bang_tinh_luong:   │
        │ • _compute_thong_ke_cong()       │
        │ • _compute_tien_luong()          │
        └──────────┬───────────────────────┘
                   ↓
        ┌──────────────────────────────────┐
        │ BANG_TINH_LUONG (Lương Tháng)    │
        │ ✓ so_ngay_cong                   │
        │ ✓ tien_cong                      │
        │ ✓ tien_phat                      │
        │ ✓ luong_thuc_nhan                │
        └──────────────────────────────────┘
```

---

## 📌 BẢNG TÓMT QUAN HỆ DỮ LIỆU

| Module | Model | Trường chính | Lấy từ | Tính toán |
|--------|-------|--------------|--------|----------|
| **HR** | hr.employee | id, name, luong_co_ban, phu_cap_co_dinh | - | - |
| **CHAM_CONG** | bang_cham_cong | employee_id, ngay_cham_cong, ca_lam, gio_vao, gio_ra | hr.attendance | phut_di_muon, phut_ve_som, trang_thai |
| **TINH_LUONG** | bang_tinh_luong | employee_id, thang, nam | hr.employee | so_ngay_cong, tien_cong, tien_phat, **luong_thuc_nhan** |

---

## 🔗 LUỒNG DỮ LIỆU CHÍNH

```
HR (Nhân sự)
├─ luong_co_ban = 10,000,000
├─ phu_cap_co_dinh = 2,000,000
└─ id = "Nguyễn Văn A"
        ↓
CHAM_CONG (Chấm công hàng ngày)
├─ 2024-01-02: check-in 08:50 → 17:15 → di_muon 20 phut
├─ 2024-01-03: check-in 07:30 → 17:30 → di_lam (đúng giờ)
├─ 2024-01-04: check-in 08:00 → 12:30 → ca_sang, di_muon 30 phut
├─ 2024-01-05: (vang) → trang_thai = vang_mat
└─ ... (22 ngày công tổng cộng)
        ↓
TINH_LUONG (Lương tháng 1)
├─ so_ngay_cong = 22
├─ don_gia_cong = 10,000,000 / 26 = 384,615
├─ tien_cong = 384,615 × 22 = 8,461,530
├─ tien_phat = (90 + 30) × 5,000 = 600,000
└─ luong_thuc_nhan = 8,461,530 + 2,000,000 - 600,000 = 9,861,530 ✓
```

---

## ⚡ KEY FEATURES

### ✅ Tự Động
- Chấm công → Tự động tạo bang_cham_cong
- Chấm công thay đổi → Tự động cập nhật bang_tinh_luong
- Công việc không cần nhập liệu thủ công

### ✅ Linh Hoạt
- Cấu hình ca làm: Sáng (07:30-11:30), Chiều (13:30-17:30), Cả ngày
- Cấu hình mức phạt: /phút
- Cấu hình làm tròn: gần nhất/xuống/lên
- Cấu hình công chuẩn: 26 công/tháng (thay đổi được)

### ✅ Chính Xác
- Dựa trên dữ liệu thực tế check-in/check-out
- Tính toán tự động, không sai số
- Có truy vết lịch sử chấm công

### ✅ Quản Trị
- Có thể điều chỉnh lương thủ công (cong_chuan, muc_phat, kiểu_lam_tron)
- Có thể xem chi tiết từng ngày chấm công
- Có thể theo dõi lương từng tháng

---

## 📊 VÍ DỤ TÍNH LƯƠNG THỰC TẾ

**Nhân viên: Nguyễn Văn A**  
**Tháng: 1/2024**

### Thống kê Chấm Công:
- Tổng ngày công: **22 ngày**
- Tổng giờ làm: **176 giờ** (22 × 8)
- Đi muộn tổng: **90 phút**
- Về sớm tổng: **30 phút**
- Vắng không phép: **2 ngày**

### Tính Lương:
```
Lương cơ bản:        10,000,000 VND
Phụ cấp cố định:     2,000,000 VND
Công chuẩn:          26 công

① Đơn giá công:
   = 10,000,000 ÷ 26
   = 384,615 VND/công

② Tiền công:
   = 384,615 × 22
   = 8,461,530 VND

③ Tiền phạt:
   = (90 + 30) phút × 5,000 VND/phút
   = 120 × 5,000
   = 600,000 VND

④ LƯƠNG THỰC NHẬN:
   = 8,461,530 + 2,000,000 - 600,000
   = 9,861,530 VND
```

---

## 🎓 QUAN HỆ GIỮA 3 MODULE

```
                         HR
                         ↑
                (luong_co_ban, phu_cap)
                         │
              ┌──────────┴───────────┐
              ↓                      ↓
         CHAM_CONG         ← ← ← TINH_LUONG
      (Chấm công)         (Tổng hợp)
              │
              │ (bang_cham_cong
              │  records)
              │
              └─→ TINH_LUONG
                  _compute_thong_ke_cong()
```

### Mối Quan Hệ:
1. **HR → CHAM_CONG**: 1 nhân viên → nhiều ngày chấm công
2. **CHAM_CONG → TINH_LUONG**: Nhiều ngày chấm công → 1 lương tháng (tổng hợp)
3. **HR → TINH_LUONG**: 1 nhân viên → 1 lương/tháng

---

## 📌 CÔNG THỨC CHÍNH

```
don_gia_cong = luong_co_ban / cong_chuan

tien_cong = don_gia_cong × so_ngay_cong

tien_phat = (tong_phut_di_muon + tong_phut_ve_som) × muc_phat_moi_phut

luong_thuc_nhan = tien_cong + phu_cap_co_dinh - tien_phat
```

---

## 🔍 TÓM TẮT ĐIỂM CHÍNH

| Điểm | Giải thích |
|------|-----------|
| **Nhập liệu** | Check-in/check-out trong HR.ATTENDANCE |
| **Xử lý 1** | CHAM_CONG tính chi tiết từng ngày |
| **Xử lý 2** | TINH_LUONG tổng hợp & tính lương tháng |
| **Kết quả** | Lương thực nhận (luong_thuc_nhan) |
| **Tự động** | Trigger tự động giữa các bước |
| **Linh hoạt** | Có thể cấu hình ca làm, phạt, làm tròn |

