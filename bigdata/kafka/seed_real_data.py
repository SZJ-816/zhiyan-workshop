#!/usr/bin/env python3
"""
种子数据生成器 — 为禅道平台生成真实项目/任务/Bug数据
直接通过 pymysql 写入 MySQL，绕过 ORM 以避免模型兼容性问题
"""
import pymysql
import random
import hashlib
from datetime import datetime, timedelta

# MySQL连接
conn = pymysql.connect(
    host='zentao-mysql',
    port=3306,
    user='zentao',
    password='zentao123',
    database='zentao',
    charset='utf8mb4'
)
cur = conn.cursor()

# ==================== 数据定义 ====================

# 15个用户 (account, realname, role, dept_id)
USERS = [
    ("admin", "系统管理员", "admin", 1),
    ("zhangsan", "张三", "pm", 2),
    ("lisi", "李四", "pm", 2),
    ("wangwu", "王五", "dev", 1),
    ("zhaoliu", "赵六", "dev", 1),
    ("sunqi", "孙七", "dev", 1),
    ("zhouba", "周八", "dev", 1),
    ("wujiu", "吴九", "qa", 3),
    ("zhengshi", "郑十", "qa", 3),
    ("liuyi", "刘一", "qa", 3),
    ("chener", "陈二", "po", 2),
    ("yangsan", "杨三", "po", 2),
    ("huangsi", "黄四", "dev", 1),
    ("linwu", "林五", "dev", 1),
    ("heliu", "何六", "po", 2),
]

# 10个项目 (name, code, description, status, pm_id)
PROJECTS = [
    ("企业ERP管理系统", "ERP-V3", "企业资源计划管理系统第三代重构，涵盖财务、人力、供应链、生产制造等核心模块的全面升级", "doing", 2),
    ("SOP V2.0 协同增强迭代", "SOP-V2", "标准操作流程管理平台协同功能增强，支持多人实时协作编辑、审批流程引擎、版本对比与回滚、智能任务分配", "doing", 3),
    ("移动办公APP", "MOA-V1", "移动办公应用第一版开发，包含即时通讯、任务管理、审批流程、考勤打卡、日报周报等功能", "doing", 2),
    ("数据可视化大屏平台", "DASH-01", "实时数据可视化监控大屏，集成多数据源实时图表展示，支持自定义仪表盘布局与告警规则配置", "waiting", 3),
    ("智能客服AI系统", "AI-CS-01", "基于大语言模型的智能客服系统，涵盖意图识别、多轮对话管理、知识库检索增强、人机协作切换等功能", "doing", 2),
    ("用户中心微服务重构", "UC-MS-01", "将单体用户中心拆分为微服务架构：认证服务、权限服务、用户画像服务、消息通知服务", "doing", 3),
    ("API网关与流量治理", "GW-01", "统一API网关建设，涵盖路由转发、限流熔断、协议转换、灰度发布、全链路追踪等治理能力", "waiting", 2),
    ("电商订单履约系统", "OMS-V2", "订单履约系统第二版，集成多仓库库存调度、第三方物流对接、异常订单自动处理、履约时效监控", "doing", 3),
    ("DevOps持续交付平台", "CICD-01", "企业内部DevOps持续交付平台建设，涵盖代码扫描、自动化测试、容器化部署、环境一键拉起", "doing", 2),
    ("内容安全管理后台", "CMS-ADMIN", "内容安全管理后台，支持图文视频内容审核、敏感词过滤、用户举报处理、数据安全审计日志", "waiting", 3),
]

# 产品线（每个项目至少一个产品）
PRODUCTS = [
    ("ERP系统", "erp", "企业资源计划管理系统产品线", 2),
    ("SOP协同平台", "sop", "标准操作流程管理平台产品线", 3),
    ("移动办公", "moa", "移动办公应用产品线", 2),
    ("数据大屏", "dashboard", "数据可视化监控大屏产品线", 3),
    ("AI客服", "ai-cs", "智能客服AI系统产品线", 2),
    ("微服务中间件", "microservice", "微服务基础设施产品线", 3),
    ("API网关", "api-gw", "API网关与流量治理产品线", 2),
    ("电商后台", "oms", "电商订单履约管理后台产品线", 3),
    ("DevOps平台", "devops", "持续交付与运维平台产品线", 2),
    ("内容安全", "cms", "内容安全管理平台产品线", 3),
]

# 任务模板 — 按项目类型分组
TASK_TEMPLATES = {
    "erp": [
        ("用户权限模块RBAC设计", 16, "high"),
        ("财务总账接口对接银行API", 24, "high"),
        ("HR组织架构树递归查询优化", 8, "medium"),
        ("采购订单审批工作流引擎", 20, "high"),
        ("库存盘点差异自动对账", 12, "medium"),
        ("生产排产甘特图可视化", 16, "medium"),
        ("应收应付账龄分析报表", 8, "low"),
        ("多币种汇率自动转换", 6, "low"),
        ("物料清单BOM递归展开", 10, "medium"),
        ("数据权限按组织层级隔离", 18, "high"),
        ("凭证自动生成引擎优化", 14, "medium"),
        ("月结任务调度框架", 22, "high"),
    ],
    "sop": [
        ("多人实时协作编辑器同步冲突解决", 20, "high"),
        ("Flowable审批流引擎集成", 16, "high"),
        ("SOP文档版本差异对比算法", 12, "medium"),
        ("智能任务分配推荐引擎", 18, "high"),
        ("操作日志审计追踪链", 8, "medium"),
        ("拖拽式流程编辑器Canvas渲染", 24, "high"),
        ("文档模板市场预览与管理", 10, "medium"),
        ("附件批量上传与在线预览", 14, "medium"),
        ("审批催办自动提醒机制", 6, "low"),
        ("流程执行数据统计看板", 12, "medium"),
        ("跨部门协作空间权限模型", 16, "high"),
        ("文档变更通知WebSocket推送", 8, "low"),
    ],
    "moa": [
        ("即时通讯WebSocket长连接管理", 20, "high"),
        ("任务看板拖拽排序与状态流转", 12, "medium"),
        ("考勤打卡GPS定位与围栏", 16, "high"),
        ("日报周报AI摘要生成", 10, "medium"),
        ("审批表单动态渲染引擎", 14, "high"),
        ("消息推送FCM/APNs双通道", 8, "medium"),
        ("离线数据同步冲突解决", 16, "high"),
        ("会议预定与日程冲突检测", 10, "medium"),
        ("文件共享与权限控制", 12, "medium"),
        ("组织架构树懒加载优化", 8, "low"),
        ("IM消息已读未读状态同步", 6, "medium"),
    ],
    "dashboard": [
        ("ECharts多图表联动交互", 16, "high"),
        ("WebSocket实时数据推送管道", 12, "high"),
        ("拖拽式仪表盘布局Grid引擎", 20, "high"),
        ("告警规则DSL解析器", 14, "medium"),
        ("数据源连接池与缓存层", 18, "high"),
        ("图表组件插件市场架构", 24, "high"),
        ("大屏自适应分辨率方案", 10, "medium"),
        ("定时刷新与数据快照", 8, "low"),
        ("数据下钻与联动筛选", 12, "medium"),
        ("颜色主题与暗色模式切换", 6, "low"),
    ],
    "ai": [
        ("意图识别NLU模型训练与部署", 24, "high"),
        ("多轮对话上下文管理", 16, "high"),
        ("向量知识库Milvus检索增强", 20, "high"),
        ("人机协作切换决策引擎", 14, "medium"),
        ("客服对话质量自动评分", 12, "medium"),
        ("FAQ冷启动词库构建", 8, "low"),
        ("情感分析模型微调fine-tune", 18, "high"),
        ("流式输出SSE响应优化", 10, "medium"),
        ("多语言翻译中间件集成", 12, "medium"),
        ("会话数据脱敏与隐私保护", 8, "low"),
        ("模型评测Benchmark平台", 16, "medium"),
        ("Prompt模板管理与AB测试", 14, "medium"),
    ],
    "uc": [
        ("OAuth2.0授权码模式实现", 16, "high"),
        ("JWT Token刷新与黑名单", 10, "medium"),
        ("RBAC权限模型数据设计", 12, "high"),
        ("用户画像标签体系构建", 18, "high"),
        ("短信邮件验证码服务", 8, "medium"),
        ("单点登录SSO CAS协议集成", 14, "high"),
        ("多租户数据隔离方案", 20, "high"),
        ("用户行为埋点数据采集", 12, "medium"),
        ("第三方登录微信/钉钉", 10, "medium"),
        ("密码强度策略与定期更新", 6, "low"),
        ("账号异常登录检测与锁定", 14, "high"),
    ],
    "gw": [
        ("动态路由配置热更新", 16, "high"),
        ("Sentinel限流规则动态下发", 14, "high"),
        ("灰度发布流量染色与路由", 20, "high"),
        ("全链路追踪TraceID透传", 12, "medium"),
        ("协议转换HTTP->gRPC网关", 18, "high"),
        ("API文档Swagger自动聚合", 10, "medium"),
        ("熔断降级Hystrix集成", 8, "medium"),
        ("请求日志ES存储与分析", 12, "medium"),
        ("认证鉴权插件化架构", 16, "high"),
        ("服务健康检查与自动摘除", 8, "low"),
    ],
    "oms": [
        ("多仓库存实时调度算法", 20, "high"),
        ("第三方物流API抽象适配层", 16, "high"),
        ("异常订单自动处理规则引擎", 14, "medium"),
        ("物流轨迹实时追踪WebSocket", 12, "medium"),
        ("履约时效SLA监控看板", 10, "medium"),
        ("退货退款流程状态机", 16, "high"),
        ("库存预占与释放事务管理", 14, "high"),
        ("电子面单批量打印", 8, "low"),
        ("发票管理电子发票开具", 10, "medium"),
        ("订单拆分与合并策略", 18, "high"),
        ("运费模板动态计算", 12, "medium"),
    ],
    "devops": [
        ("Jenkins Pipeline共享库", 16, "high"),
        ("K8s Helm Chart模板管理", 20, "high"),
        ("自动化测试全量/增量调度", 14, "high"),
        ("环境隔离与一键拉起", 18, "high"),
        ("制品管理Nexus集成", 10, "medium"),
        ("代码质量SonarQube集成", 12, "medium"),
        ("部署审批与变更窗口管理", 8, "medium"),
        ("发布回滚一键操作", 6, "low"),
        ("日志采集Filebeat配置", 8, "low"),
        ("监控报警Prometheus规则", 12, "medium"),
        ("配置中心Apollo集成", 14, "medium"),
    ],
    "cms": [
        ("图文内容AI敏感词检测", 18, "high"),
        ("视频内容抽帧审核工作流", 16, "high"),
        ("用户举报分类与优先级排序", 12, "medium"),
        ("数据安全审计日志ELK", 14, "medium"),
        ("内容分级标签体系设计", 10, "medium"),
        ("违规内容自动下架机制", 8, "low"),
        ("审核人员工作量统计", 8, "low"),
        ("内容推荐算法黑名单过滤", 14, "high"),
        ("多级审核流程配置化", 12, "medium"),
        ("审核时效SLA报警", 6, "low"),
    ],
}

# 模板key到项目index的映射
TEMPLATE_TO_PROJECT = [
    "erp", "sop", "moa", "dashboard", "ai",
    "uc", "gw", "oms", "devops", "cms",
]

# Bug描述模板（每个项目3-4个bug）
BUG_TEMPLATES = [
    # project 0 - ERP
    ("ERP系统登录页面在Edge浏览器输入密码后页面卡死3秒", "critical", "active"),
    ("财务总账报表导出Excel时数值精度丢失，小数位四舍五入错误", "major", "active"),
    ("HR组织架构拖拽排序后刷新页面顺序还原", "normal", "resolved"),
    ("采购订单审批超时后未自动转交下一审批人", "major", "active"),
    # project 1 - SOP
    ("SOP协同编辑时两人同时修改同一段落内容丢失", "critical", "active"),
    ("审批流引擎偶发跳过指定审批节点直接完成", "major", "resolved"),
    ("SOP文档版本对比时大文档diff计算超时导致页面无响应", "major", "active"),
    # project 2 - MOA
    ("移动端IM消息推送延迟超过30秒，iOS设备尤为明显", "major", "active"),
    ("考勤打卡GPS定位偏移超500米导致无法打卡", "critical", "active"),
    ("日报提交后列表刷新仍显示草稿状态", "normal", "resolved"),
    # project 3 - DASH
    ("数据大屏长时间运行后内存泄漏导致浏览器卡死", "critical", "active"),
    ("自定义图表拖拽调整大小时图表渲染异常", "normal", "active"),
    ("告警规则配置'连续3次超过阈值'时触发不准确", "major", "resolved"),
    # project 4 - AI
    ("智能客服对话超过20轮后上下文丢失回答质量严重下降", "major", "active"),
    ("向量检索偶发返回完全不相关文档影响回答准确性", "critical", "active"),
    ("人机切换后历史对话记录丢失", "normal", "active"),
    # project 5 - UC
    ("OAuth2.0授权回调地址被CSRF攻击利用", "critical", "active"),
    ("JWT Token过期后刷新接口偶发返回500错误", "major", "resolved"),
    ("多租户场景下用户画像数据交叉污染", "critical", "active"),
    # project 6 - GW
    ("灰度发布流量染色配置热更新后旧Pod未及时摘除", "major", "active"),
    ("API网关在高并发下偶发返回502，后端服务实际正常", "critical", "active"),
    ("全链路追踪TraceID在跨线程场景下丢失", "major", "resolved"),
    # project 7 - OMS
    ("多仓库库存调度算法在特定场景下死循环导致CPU 100%", "critical", "active"),
    ("电子面单打印批量操作时第23张开始错位", "normal", "active"),
    ("退货退款状态机关闭退款后仍可发起退款", "major", "resolved"),
    ("物流轨迹更新延迟导致用户看到已签收实际未送达", "major", "active"),
    # project 8 - DevOps
    ("Jenkins Pipeline执行到部署阶段偶发卡死超时", "major", "active"),
    ("K8s Helm部署时ConfigMap更新未触发Pod重启", "major", "active"),
    ("自动化测试增量模式误判跳过关键测试用例", "critical", "resolved"),
    # project 9 - CMS
    ("AI敏感词检测对同音替换词识别率为零", "major", "active"),
    ("视频抽帧审核在处理4K视频时内存溢出", "critical", "active"),
    ("举报处理完成后用户再次举报同一内容可绕过审核", "major", "resolved"),
]

BUG_SEVERITIES = ["critical", "major", "normal", "minor"]
BUG_STATUSES = ["active", "resolved", "closed"]
TASK_STATUSES = ["todo", "doing", "done", "closed"]
PROJECT_STATUSES = ["waiting", "doing", "done", "suspended"]
ROLES = ["admin", "pm", "dev", "qa", "po"]


def hash_pwd(pwd):
    """简单的密码哈希（与之前系统兼容）"""
    import bcrypt
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()


def generate():
    print("=" * 60)
    print("  禅道平台真实数据生成器")
    print("=" * 60)

    # 1. 清空所有表
    tables = ["zt_activity", "zt_bug", "zt_task", "zt_story",
              "zt_project", "zt_product", "zt_user", "zt_department"]
    for t in tables:
        cur.execute(f"DELETE FROM {t}")
    conn.commit()
    for t in tables:
        cur.execute(f"ALTER TABLE {t} AUTO_INCREMENT = 1")
    conn.commit()
    print("[1/7] 已清空所有数据表")

    # 2. 创建部门
    depts = [
        (1, "技术研发部", None, 1),
        (2, "产品管理部", None, 2),
        (3, "质量保障部", None, 3),
        (4, "运营管理部", None, 4),
        (5, "UED设计部", None, 5),
    ]
    for d in depts:
        cur.execute("INSERT INTO zt_department (id,name,parent_id,sort) VALUES (%s,%s,%s,%s)", d)
    conn.commit()
    print(f"[2/7] 创建 {len(depts)} 个部门")

    # 3. 创建用户
    import bcrypt
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_ids = []
    colors = ["#4A90D9", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6",
              "#1ABC9C", "#E67E22", "#3498DB", "#E91E63", "#00BCD4",
              "#FF5722", "#673AB7", "#009688", "#795548", "#607D8B"]
    for i, (acc, rn, role, dept_id) in enumerate(USERS):
        pwd = bcrypt.hashpw("123456".encode(), bcrypt.gensalt()).decode()
        cur.execute(
            "INSERT INTO zt_user (account,realname,password,role,email,phone,department_id,avatar_color,created_at,last_login) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (acc, rn, pwd, role, f"{acc}@worknest.com", f"1380000{i:04d}", dept_id, colors[i], now, now)
        )
        user_ids.append(cur.lastrowid if cur.lastrowid else i + 1)
    conn.commit()
    print(f"[3/7] 创建 {len(user_ids)} 个用户")

    # 4. 创建产品线
    product_ids = []
    for i, (name, code, desc, created_by) in enumerate(PRODUCTS):
        cur.execute(
            "INSERT INTO zt_product (name,code,description,status,created_by,created_at,updated_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (name, code, desc, "normal", user_ids[created_by - 1], now, now)
        )
        product_ids.append(cur.lastrowid if cur.lastrowid else i + 1)
    conn.commit()
    print(f"[4/7] 创建 {len(product_ids)} 个产品线")

    # 5. 创建项目
    project_ids = []
    dev_ids = [uid for i, uid in enumerate(user_ids) if USERS[i][2] == "dev"]
    qa_ids = [uid for i, uid in enumerate(user_ids) if USERS[i][2] == "qa"]
    po_ids = [uid for i, uid in enumerate(user_ids) if USERS[i][2] == "po"]
    pm_ids = [uid for i, uid in enumerate(user_ids) if USERS[i][2] == "pm"]

    for i, (name, code, desc, status, pm_idx) in enumerate(PROJECTS):
        start = datetime.now() - timedelta(days=random.randint(30, 180))
        end = start + timedelta(days=random.randint(60, 200))
        cur.execute(
            "INSERT INTO zt_project (name,code,description,start_date,end_date,status,pm_id,product_id,progress,created_at,updated_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (name, code, desc,
             start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"),
             status, user_ids[pm_idx - 1], product_ids[i],
             round(random.uniform(20, 85), 1), now, now)
        )
        project_ids.append(cur.lastrowid if cur.lastrowid else i + 1)
    conn.commit()
    print(f"[5/7] 创建 {len(project_ids)} 个项目")

    # 6. 创建任务
    task_count = 0
    for proj_idx, tpl_key in enumerate(TEMPLATE_TO_PROJECT):
        tasks = TASK_TEMPLATES[tpl_key]
        project_id = project_ids[proj_idx]
        for j, (tname, estimate, priority) in enumerate(tasks):
            # 随机分配状态
            status = random.choices(TASK_STATUSES, weights=[20, 35, 35, 10])[0]
            assigned_to = random.choice(dev_ids) if status != "todo" else None
            consumed = round(random.uniform(0, estimate * 1.2), 1) if status == "done" else 0

            deadline = datetime.now() + timedelta(days=random.randint(1, 30))
            finished = None
            if status == "done":
                finished = (datetime.now() - timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d %H:%M:%S")

            cur.execute(
                "INSERT INTO zt_task (name,description,project_id,assigned_to,status,priority,estimate,consumed,"
                "start_date,deadline,finished_date,created_at,updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (tname, f"任务描述：{tname}\n\n需求来源：产品经理PRD\n技术方案：待定",
                 project_id, assigned_to, status, priority,
                 estimate, consumed,
                 datetime.now().strftime("%Y-%m-%d"),
                 deadline.strftime("%Y-%m-%d"),
                 finished, now, now)
            )
            task_count += 1
    conn.commit()
    print(f"[6/7] 创建 {task_count} 个任务")

    # 7. 创建 Bug
    bug_count = 0
    for title, severity, status in BUG_TEMPLATES:
        project_idx = bug_count // random.randint(3, 4)
        if project_idx >= len(project_ids):
            project_idx = project_idx % len(project_ids)
        project_id = project_ids[project_idx]

        created_by = random.choice(dev_ids + qa_ids + po_ids)
        assigned_to = random.choice(dev_ids)

        resolved_at = None
        if status == "resolved":
            resolved_at = (datetime.now() - timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            "INSERT INTO zt_bug (title,description,product_id,project_id,severity,status,assigned_to,created_by,"
            "created_at,resolved_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (title, f"【Bug详情】\n{title}\n\n复现步骤：\n1. 登录系统\n2. 执行相关操作\n3. 观察现象",
             product_ids[project_idx], project_id, severity, status,
             assigned_to, created_by,
             now, resolved_at)
        )
        bug_count += 1
    conn.commit()
    print(f"[7/7] 创建 {bug_count} 个 Bug")

    # 统计
    cur.execute("SELECT COUNT(*) FROM zt_user")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM zt_project")
    total_projects = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM zt_task")
    total_tasks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM zt_bug")
    total_bugs = cur.fetchone()[0]

    print("\n" + "=" * 60)
    print("  ✅ 数据生成完成！")
    print(f"  用户: {total_users} | 项目: {total_projects}")
    print(f"  任务: {total_tasks} | Bug: {total_bugs}")
    print("=" * 60)

    cur.close()
    conn.close()


if __name__ == "__main__":
    generate()
