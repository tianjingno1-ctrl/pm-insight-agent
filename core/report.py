from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("output")


def save_legacy_report(content: str) -> Path:
    """
    保存旧版单次分析报告到 output/pm_insight_report_{timestamp}.md。
    自动创建 output 目录。
    返回保存路径。
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = OUTPUT_DIR / f"pm_insight_report_{timestamp}.md"
    filepath.write_text(content, encoding="utf-8")
    return filepath
