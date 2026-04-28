#rename.py
import os
from pathlib import Path

# ==================== 配置区域 ====================
SUBTITLE_DIR = Path(r"E:\projects_2026\BiliScribe\download\【从0到1学人工智能】")
# =================================================

def batch_rename_subtitles(directory: Path):
    """批量重命名字幕文件，保留 PXX_标题 部分"""
    if not directory.exists():
        print(f"目录不存在: {directory}")
        return
    
    srt_files = list(directory.glob("*.srt"))
    if not srt_files:
        print("未找到 .srt 文件")
        return
    
    print(f"找到 {len(srt_files)} 个字幕文件")
    print("-" * 50)
    
    rename_plan = []
    
    for file_path in srt_files:
        original_name = file_path.stem  # 不含扩展名
        suffix = file_path.suffix       # .srt
        
        # 按 _ 分割
        parts = original_name.split('_')
        
        if len(parts) < 3:
            print(f"跳过（格式不符）: {file_path.name}")
            continue
        
        # 删除第一个元素（开头长标题）和最后一个元素（BV号）
        # 保留中间部分: P01 + 标题
        new_name = '_'.join(parts[1:-1]) + suffix
        
        # 清理可能的重复空格
        new_name = ' '.join(new_name.split())
        
        old_path = file_path
        new_path = directory / new_name
        
        rename_plan.append((old_path, new_path, file_path.name, new_name))
        print(f"{file_path.name}")
        print(f"  -> {new_name}")
        print()
    
    if not rename_plan:
        print("没有符合重命名条件的文件")
        return
    
    print("-" * 50)
    confirm = input(f"确认重命名以上 {len(rename_plan)} 个文件？(yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("已取消")
        return
    
    success_count = 0
    for old_path, new_path, old_name, new_name in rename_plan:
        try:
            if new_path.exists():
                print(f"跳过（目标已存在）: {new_name}")
                continue
            
            old_path.rename(new_path)
            success_count += 1
            print(f"已重命名: {old_name}")
            
        except Exception as e:
            print(f"重命名失败 {old_name}: {e}")
    
    print("-" * 50)
    print(f"完成: {success_count}/{len(rename_plan)} 个文件已重命名")

if __name__ == "__main__":
    batch_rename_subtitles(SUBTITLE_DIR)