"""
seed.py — 从 ai-learning-roadmap.html 解析数据导入 PostgreSQL
================================================================
用法: python seed.py

需要:
1. PostgreSQL 已启动 + 配置在 config.py
2. pip install -r requirements.txt
3. Node.js 可用 (node --version)
"""
import json, subprocess, sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from database import sync_engine, SyncSessionLocal, Base
from models import Phase, Week, Day, Tip
from sqlalchemy import text

HTML_PATH = os.path.join(os.path.dirname(__file__), "static", "ai-learning-roadmap-original.html")


def extract_via_node(html: str) -> list[dict]:
    """用 Node.js 解析 JS 数组，比正则更可靠"""
    # 找到 const D = ... ]; 边界
    lines = html.split("\n")
    start = next(i for i, l in enumerate(lines) if l.strip() == "const D = [")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "];")
    inner = "\n".join(lines[start + 1: end])  # 只取括号内的数据，不包括 ]; 行
    js = f"[{inner}]"

    script = "const D = " + js + ";\nconsole.log(JSON.stringify(D));"
    tmp = os.path.join(os.path.dirname(__file__), "_seed_tmp.js")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(script)

    try:
        r = subprocess.run(["node", tmp], capture_output=True, text=True, timeout=30, encoding="utf-8")
        os.unlink(tmp)
        if r.returncode != 0:
            sys.exit(f"Node error:\n{r.stderr}")
        return json.loads(r.stdout)
    except FileNotFoundError:
        sys.exit("ERROR: 需要 Node.js (https://nodejs.org)")


def seed():
    if not os.path.exists(HTML_PATH):
        sys.exit(f"ERROR: {HTML_PATH} 不存在——先确保 HTML 文件在 static/ 目录下")

    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    print("🔍 用 Node.js 解析 JS 数据...")
    phases = extract_via_node(html)
    print(f"   ✅ 解析到 {len(phases)} 个阶段")

    # 建表 + 清旧数据
    print("📦 创建数据库表...")
    Base.metadata.create_all(bind=sync_engine)

    with SyncSessionLocal() as db:
        db.execute(text("DELETE FROM days"))
        db.execute(text("DELETE FROM weeks"))
        db.execute(text("DELETE FROM tips"))
        db.execute(text("DELETE FROM phases"))
        db.commit()

    total_days, week_num = 0, 0

    with SyncSessionLocal() as db:
        for pi, pd in enumerate(phases):
            phase = Phase(
                title=pd["title"], period=pd.get("period", ""),
                desc=pd.get("desc", ""), color=pd.get("color", ""),
                sort_order=pi,
            )
            db.add(phase)
            db.flush()

            # Tips
            for ti, tip_text in enumerate(pd.get("tips", [])):
                db.add(Tip(phase_id=phase.id, text=tip_text, sort_order=ti))

            # Weeks + Days
            for wi, wd in enumerate(pd.get("weeks", [])):
                week_num += 1
                week = Week(
                    phase_id=phase.id, title=wd["title"],
                    week_num=week_num, sort_order=wi,
                )
                db.add(week)
                db.flush()

                for di, dd in enumerate(wd.get("days", [])):
                    db.add(Day(
                        week_id=week.id, topic=dd["topic"],
                        hours=dd.get("hours", 3), resource=dd.get("resource", ""),
                        detail=dd.get("detail", ""), sort_order=di,
                    ))
                    total_days += 1

            db.commit()
            print(f"   ✅ {phase.title}: {len(pd.get('weeks',[]))}周")

    print(f"\n🎉 导入完成! {len(phases)} 阶段, {total_days} 天学习内容")


if __name__ == "__main__":
    seed()
