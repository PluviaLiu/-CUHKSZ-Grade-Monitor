import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ================= 🔧 配置区域 (GitHub 部署版) =================

# 1. 优先从系统环境变量获取 (适合 GitHub Actions/服务器部署)
# 如果本地运行，可以在下方 else 里填入你的默认值
MY_USERNAME = os.getenv("STU_ID", "124090381")  # 默认值留给本地测试
MY_PASSWORD = os.getenv("STU_PWD", "你的密码")  # 上传 GitHub 前记得把这里的密码删掉！

# 2. 通知密钥 (二选一，不用的留空)
# 【Bark (iPhone推荐)】
BARK_KEY = os.getenv("BARK_KEY", "")
# 【PushPlus (微信通用)】
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "")

# 3. 网址配置
LOGIN_URL = "https://sts.cuhk.edu.cn/adfs/oauth2/authorize?response_type=code&client_id=3f09a73c-33cf-49b8-8f0c-b79ea2f3e83b&redirect_uri=https://sis.cuhk.edu.cn/sso/dologin.html"
SCORE_URL = "https://sis.cuhk.edu.cn/psp/csprd/EMPLOYEE/HRMS/c/SA_LEARNER_SERVICES_2.SSS_MY_CRSEHIST.GBL?PORTALPARAM_PTCNAV=HC_SSS_MY_CRSEHIST_GBL2&EOPP.SCNode=HRMS&EOPP.SCPortal=EMPLOYEE&EOPP.SCName=PT_PTPP_PORTAL_ROOT&EOPP.SCLabel=Academic%20Planning&EOPP.SCFName=ADMN_F201601191916357876084613&EOPP.SCSecondary=true&EOPP.SCPTfname=ADMN_F201601191916357876084613&FolderPath=PORTAL_ROOT_OBJECT.PORTAL_BASE_DATA.CO_NAVIGATION_COLLECTIONS.PT_PTPP_PORTAL_ROOT.ADMN_F201512291342098588791689.ADMN_F201601191916357876084613.ADMN_S201601191923197932645635&IsFolder=false"

# 4. 关键元素 ID
ID_ACCOUNT_BOX = "userNameInput"
ID_PASSWORD_BOX = "passwordInput"


# ============================================================

def send_notification(title, content):
    """
    发送通知的通用函数
    支持 Bark (iOS) 和 PushPlus (微信)
    """
    print(f"🔔 准备发送通知: {title}")

    # 1. 发送 Bark 通知
    if BARK_KEY:
        try:
            url = f"https://api.day.app/{BARK_KEY}/{title}/{content}"
            requests.get(url)
            print("✅ Bark 推送成功")
        except Exception as e:
            print(f"❌ Bark 推送失败: {e}")

    # 2. 发送 PushPlus 微信通知
    if PUSHPLUS_TOKEN:
        try:
            url = "http://www.pushplus.plus/send"
            data = {"token": PUSHPLUS_TOKEN, "title": title, "content": content}
            requests.post(url, json=data)
            print("✅ 微信推送成功")
        except Exception as e:
            print(f"❌ 微信推送失败: {e}")


def start_monitoring():
    print("🛡️ 查分监控启动...")

    # 配置 Chrome 选项
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # 💡 如果部署在服务器/GitHub Actions，请取消这行的注释
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # --- 登录模块 ---
        print("➡️  登录中...")
        driver.get(LOGIN_URL)
        time.sleep(3)

        driver.find_element(By.ID, ID_ACCOUNT_BOX).send_keys(MY_USERNAME + Keys.ENTER)
        time.sleep(3)
        driver.find_element(By.ID, ID_PASSWORD_BOX).send_keys(MY_PASSWORD + Keys.ENTER)

        # --- 查分初始化 ---
        print("⏳ 跳转查分页面...")
        time.sleep(8)  # 等待登录完成
        driver.get(SCORE_URL)
        time.sleep(8)  # 等待成绩单加载

        # 锁定基准
        initial_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"✅ 基准已锁定 (字数: {len(initial_text)})")

        # 发送一条测试通知，确认手机能收到
        send_notification("查分脚本已启动", "目前一切正常，有变化我会通知你。")

        # --- 循环监控 ---
        count = 0
        while True:
            time.sleep(60)  # 1分钟一次
            count += 1
            print(f"[{time.strftime('%H:%M')}] 检查 #{count}...", end="")

            try:
                driver.refresh()
                time.sleep(8)
                current_text = driver.find_element(By.TAG_NAME, "body").text

                # 防误报：如果网页加载失败变短了，忽略
                if len(current_text) < len(initial_text) * 0.5:
                    print("⚠️ 页面加载不全，跳过")
                    continue

                if current_text != initial_text:
                    print("\n🚨 变化检测！")
                    # 触发手机通知！
                    send_notification("出分啦！！！", "检测到教务系统成绩单发生变化，快去看看！")
                    break
                else:
                    print(" 无变化")

            except Exception as e:
                print(f"重试...{e}")
                continue

    except Exception as e:
        print(f"❌ 运行出错: {e}")
        send_notification("脚本报错停止", str(e))
    finally:
        driver.quit()


if __name__ == "__main__":
    start_monitoring()