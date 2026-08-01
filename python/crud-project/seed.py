"""
seed.py — 从 ai-learning-roadmap.html 解析数据导入 PostgreSQL
================================================================
用法: python seed.py

需要:
1. PostgreSQL 已启动 + 配置在 config.py
2. pip install -r requirements.txt
3. Node.js 可用 (node --version)
"""
# 导入 JSON、子进程、系统退出、路径处理和文本流相关标准库。
import json, subprocess, sys, os, io
# 重新包装标准输出，强制使用 UTF-8，并在遇到无法编码字符时进行替换。
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
# 导入同步引擎、同步 Session 工厂和 ORM 元数据基类。
from database import sync_engine, SyncSessionLocal, Base
# 导入 seed 脚本需要创建的四种业务模型。
from models import Phase, Week, Day, Tip
# text 把原始 SQL 字符串包装成 SQLAlchemy 可执行语句。
from sqlalchemy import text

# 根据当前脚本目录拼出数据源 HTML 的绝对路径。
HTML_PATH = os.path.join(os.path.dirname(__file__), "static", "ai-learning-roadmap-original.html")


# 参数和返回值类型标注说明：输入 HTML 字符串，返回字典列表。
def extract_via_node(html: str) -> list[dict]:
    """用 Node.js 解析 JS 数组，比正则更可靠"""
    # 找到 const D = ... ]; 边界
    # 按换行符切分，后续可以逐行定位 JavaScript 数组边界。
    lines = html.split("\n")
    # next 取得第一行内容严格等于 const D = [ 的下标；找不到会抛 StopIteration。
    start = next(i for i, l in enumerate(lines) if l.strip() == "const D = [")
    # 从起始行之后查找第一个只包含 ]; 的结束行。
    end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "];")
    # 切片取起止位置中间的数组元素，再重新拼成多行字符串。
    inner = "\n".join(lines[start + 1: end])  # 只取括号内的数据，不包括 ]; 行
    # 给数组元素补回方括号，形成可执行的 JavaScript 数组表达式。
    js = f"[{inner}]"

    # 构造最小 Node.js 脚本，把数组序列化为标准 JSON 输出。
    script = "const D = " + js + ";\nconsole.log(JSON.stringify(D));"
    # 临时脚本与 seed.py 放在同一目录，便于 Node 直接执行。
    tmp = os.path.join(os.path.dirname(__file__), "_seed_tmp.js")
    # 以 UTF-8 文本写模式创建临时 JavaScript 文件。
    with open(tmp, "w", encoding="utf-8") as f:
        # 将刚刚拼出的脚本内容写入文件。
        f.write(script)

    # 捕获 Node 不存在等可预期异常。
    try:
        # 启动 node 子进程，捕获输出，设置 UTF-8 和 30 秒超时。
        r = subprocess.run(["node", tmp], capture_output=True, text=True, timeout=30, encoding="utf-8")
        # Node 执行完成后删除临时脚本。
        os.unlink(tmp)
        # 非零返回码表示 JavaScript 执行失败。
        if r.returncode != 0:
            # sys.exit 终止脚本，并把 Node 的错误输出展示给使用者。
            sys.exit(f"Node error:\n{r.stderr}")
        # 将 Node 输出的 JSON 字符串解析回 Python 列表和字典。
        return json.loads(r.stdout)
    # 系统找不到 node 命令时，subprocess 会抛 FileNotFoundError。
    except FileNotFoundError:
        # 给出明确依赖提示后终止 seed。
        sys.exit("ERROR: 需要 Node.js (https://nodejs.org)")


# seed 封装完整的数据源检查、解析、建表、清表和写入流程。
def seed():
    # 先检查配置的数据源 HTML 是否真实存在。
    if not os.path.exists(HTML_PATH):
        # 文件缺失时立即终止，避免后面出现难理解的 open 错误。
        sys.exit(f"ERROR: {HTML_PATH} 不存在——先确保 HTML 文件在 static/ 目录下")

    # 以 UTF-8 只读方式打开路线图 HTML。
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        # 一次性读取完整文件内容。
        html = f.read()

    # 输出当前执行阶段，方便命令行观察进度。
    print("🔍 用 Node.js 解析 JS 数据...")
    # 调用上面的解析函数，得到阶段字典列表。
    phases = extract_via_node(html)
    # 显示解析出的阶段数量。
    print(f"   ✅ 解析到 {len(phases)} 个阶段")

    # 建表 + 清旧数据
    # 输出当前阶段，然后根据 Base 收集的元数据创建尚不存在的表。
    print("📦 创建数据库表...")
    # bind 指定使用同步引擎执行建表语句。
    Base.metadata.create_all(bind=sync_engine)

    # with 结束时自动关闭同步 Session。
    with SyncSessionLocal() as db:
        # 按现有脚本顺序清空学习日数据。
        db.execute(text("DELETE FROM days"))
        # 清空周数据。
        db.execute(text("DELETE FROM weeks"))
        # 清空阶段建议数据。
        db.execute(text("DELETE FROM tips"))
        # 最后清空阶段数据。
        db.execute(text("DELETE FROM phases"))
        # 提交四条 DELETE，使清理结果真正写入数据库。
        db.commit()

    # total_days 统计导入天数，week_num 维护跨阶段的全局周序号。
    total_days, week_num = 0, 0

    # 创建新的同步 Session，开始写入解析后的路线数据。
    with SyncSessionLocal() as db:
        # enumerate 同时提供阶段下标 pi 和阶段字典 pd。
        for pi, pd in enumerate(phases):
            # 根据 HTML 字典创建阶段 ORM 对象。
            phase = Phase(
                # title 必填，其余字段使用 get 提供空字符串默认值。
                title=pd["title"], period=pd.get("period", ""),
                desc=pd.get("desc", ""), color=pd.get("color", ""),
                # 原始列表下标直接作为展示顺序。
                sort_order=pi,
            )
            # 将阶段对象加入当前事务。
            db.add(phase)
            # flush 先执行 INSERT，以便在提交前取得数据库生成的 phase.id。
            db.flush()

            # Tips
            # 遍历当前阶段的建议文本；没有 tips 时使用空列表。
            for ti, tip_text in enumerate(pd.get("tips", [])):
                # 使用刚生成的 phase.id 建立外键，并保存建议顺序。
                db.add(Tip(phase_id=phase.id, text=tip_text, sort_order=ti))

            # Weeks + Days
            # 遍历当前阶段中的所有周。
            for wi, wd in enumerate(pd.get("weeks", [])):
                # 全局周序号每处理一周就加一。
                week_num += 1
                # 创建周 ORM 对象并关联当前阶段。
                week = Week(
                    phase_id=phase.id, title=wd["title"],
                    # week_num 是跨阶段序号，wi 是当前阶段内排序下标。
                    week_num=week_num, sort_order=wi,
                )
                # 将周加入事务。
                db.add(week)
                # flush 取得 week.id，供随后创建 Day 外键。
                db.flush()

                # 遍历当前周中的所有学习日。
                for di, dd in enumerate(wd.get("days", [])):
                    # 创建 Day 并直接加入 Session。
                    db.add(Day(
                        # 关联当前周并读取必填主题。
                        week_id=week.id, topic=dd["topic"],
                        # 可选字段通过 get 提供默认值。
                        hours=dd.get("hours", 3), resource=dd.get("resource", ""),
                        detail=dd.get("detail", ""), sort_order=di,
                    ))
                    # 累加本次导入的学习日数量。
                    total_days += 1

            # 每个阶段及其子数据处理完后提交一次，缩小单次事务范围。
            db.commit()
            # 在命令行显示当前阶段和导入周数。
            print(f"   ✅ {phase.title}: {len(pd.get('weeks',[]))}周")

    # 所有阶段处理完后输出总计。
    print(f"\n🎉 导入完成! {len(phases)} 阶段, {total_days} 天学习内容")


# 只有直接运行 python seed.py 时才执行 seed；被其他模块导入时不会自动清库。
if __name__ == "__main__":
    # 调用完整导入流程。
    seed()
