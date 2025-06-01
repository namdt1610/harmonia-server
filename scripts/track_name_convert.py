import os
import re

# Thư mục chứa các file mp3
folder_path = './your_folder_path_here'  # chỉnh lại đường dẫn nhé

def get_base_name(filename):
    """
    Lấy tên file gốc trước phần suffix.
    Ví dụ:
    - 1000_Anh_Mat.mp3 -> 1000_Anh_Mat
    - 1000_Anh_Mat_5zIOw9p.mp3 -> 1000_Anh_Mat
    """
    # loại bỏ phần _suffix (nếu có) trước .mp3
    # tìm phần trước _suffix nếu _suffix là chuỗi ký tự không phải chữ số hay chữ cái
    # để đơn giản: lấy phần đầu tên đến lần xuất hiện cuối của dấu '_'
    
    # pattern: tách phần tên gốc trước suffix (bỏ phần sau dấu gạch dưới cuối)
    # nếu file có nhiều dấu _ thì lấy hết trừ phần cuối cùng sau dấu _
    # Ví dụ: 1000_Anh_Mat_5zIOw9p -> 1000_Anh_Mat
    
    name_part = filename[:-4]  # bỏ .mp3
    if '_' in name_part:
        parts = name_part.rsplit('_', 1)
        # Kiểm tra phần suffix có phải là kiểu ngẫu nhiên (kí tự + số)
        suffix = parts[1]
        # Nếu suffix chứa ký tự đặc biệt hoặc là mã random (có chữ số + chữ cái),
        # thì bỏ suffix, giữ phần trước
        # Nếu suffix là chữ số hay chữ cái dài > 3 (để tránh bỏ nhầm tên chuẩn)
        if re.match(r'^[a-zA-Z0-9]{4,}$', suffix):
            return parts[0]
    return name_part

def main():
    files = [f for f in os.listdir(folder_path) if f.endswith('.mp3')]

    base_names = {}
    for f in files:
        base = get_base_name(f)
        # Lưu lại file gốc duy nhất
        # Nếu chưa có base này, hoặc file tên ngắn hơn (để ưu tiên file gốc)
        if base not in base_names or len(f) < len(base_names[base]):
            base_names[base] = f

    print("Danh sach file giu lai:")
    for f in base_names.values():
        print(f)

    # Nếu muốn xóa file không giữ lại, uncomment đoạn dưới:
    # for f in files:
    #     if f not in base_names.values():
    #         os.remove(os.path.join(folder_path, f))
    #         print(f"Da xoa: {f}")

if __name__ == '__main__':
    main()
