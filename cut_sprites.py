import os
from PIL import Image

def cut_sprite_sheet(image_path, output_dir, rows, cols, frame_data):
    """
    切割精灵表并按动作类别重命名存储。
    """
    # 1. 加载图片
    try:
        sheet = Image.open(image_path).convert("RGBA")
    except FileNotFoundError:
        print(f"错误: 找不到文件 {image_path}")
        return

    sheet_width, sheet_height = sheet.size

    # 2. 计算单个帧的大小
    frame_width = sheet_width // cols
    frame_height = sheet_height // rows

    print(f"精灵表大小: {sheet_width}x{sheet_height}")
    print(f"单个帧大小: {frame_width}x{frame_height}")
    print(f"预计切割: {rows * cols} 帧")

    # 3. 背景处理：灰色背景变透明
    arr = np.array(sheet)
    bg1 = np.array([195, 195, 195])
    bg2 = np.array([147, 147, 147])
    TOL = 18

    r, g, b = arr[:,:,0].astype(int), arr[:,:,1].astype(int), arr[:,:,2].astype(int)
    is_bg1 = (np.abs(r - bg1[0]) < TOL) & (np.abs(g - bg1[1]) < TOL) & (np.abs(b - bg1[2]) < TOL)
    is_bg2 = (np.abs(r - bg2[0]) < TOL) & (np.abs(g - bg2[1]) < TOL) & (np.abs(b - bg2[2]) < TOL)
    is_bg = is_bg1 | is_bg2

    arr[:,:,3] = np.where(is_bg, 0, 255)
    sheet = Image.fromarray(arr, "RGBA")

    # 4. 创建输出根目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 5. 创建按类别命名的子目录
    category_dirs = {}
    for category in frame_data.keys():
        cat_dir = os.path.join(output_dir, category)
        if not os.path.exists(cat_dir):
            os.makedirs(cat_dir)
        category_dirs[category] = cat_dir

    # 6. 开始切割
    frame_count = 0
    for row in range(rows):
        for col in range(cols):
            left = col * frame_width
            top = row * frame_height
            right = left + frame_width
            bottom = top + frame_height

            frame = sheet.crop((left, top, right, bottom))

            frame_index = (row * cols) + col
            category_found = False

            for category, indices in frame_data.items():
                if frame_index in indices:
                    idx_in_category = list(indices).index(frame_index)
                    filename = f"{category}_{idx_in_category:03d}.png"
                    save_path = os.path.join(category_dirs[category], filename)
                    frame.save(save_path)
                    category_found = True
                    break

            if not category_found:
                uncat_dir = os.path.join(output_dir, "uncategorized")
                if not os.path.exists(uncat_dir):
                    os.makedirs(uncat_dir)
                filename = f"frame_{frame_index:03d}.png"
                save_path = os.path.join(uncat_dir, filename)
                frame.save(save_path)

            frame_count += 1

    print(f"切割完成！共生成 {frame_count} 个帧文件")


if __name__ == "__main__":
    import numpy as np

    # 3.jpeg 是 9行 x 8列
    IMAGE_FILE = "/Users/sevik/Desktop/ip/3.jpeg"
    OUTPUT_FOLDER = "/Users/sevik/Desktop/ip/sprites_cut"

    ROWS = 9
    COLS = 8

    # 根据 3.jpeg 的实际内容定义动作类别
    FRAME_ACTIONS = {
        "idle_front": list(range(0, 8)),      # Row 1: 正面idle，眨眼
        "walk_right": list(range(8, 16)),     # Row 2: 向右走
        "walk_left": list(range(16, 24)),     # Row 3: 向左走
        "walk_front": list(range(24, 32)),    # Row 4: 向前(下)走
        "cheer": list(range(32, 40)),         # Row 5: 挥手/欢呼
        "jump": list(range(40, 47)),           # Row 6: 跳（7帧）
        "slide": list(range(47, 55)),         # Row 7: 滑步/拿刀（8帧）
        "run": list(range(55, 63)),           # Row 8: 跑步（8帧）
        "work_sleep": list(range(63, 72)),    # Row 9: 坐电脑(5帧)+睡觉(4帧)
    }

    cut_sprite_sheet(IMAGE_FILE, OUTPUT_FOLDER, ROWS, COLS, FRAME_ACTIONS)