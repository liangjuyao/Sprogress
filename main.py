import requests
import pymysql
import ddddocr
from fake_useragent import UserAgent
import base64
import time
from PIL import Image
import io


def get_verify_code(sess):
    # 获取验证码图片的URL
    verify_url = 'http://jwgl.gzist.edu.cn/yzm?d=' + str(int(time.time() * 1000))
    try:
        response = sess.get(verify_url)
        response.raise_for_status()
        image_data = response.content
        try:
            # 尝试打开图像，以确保它是有效的
            img = Image.open(io.BytesIO(image_data))
        except Exception as e:
            print(f"验证码图片无效: {e}")
            return None
        ocr = ddddocr.DdddOcr()
        verify_code = ocr.classification(image_data)
        print(f"验证码: {verify_code}")
        return verify_code
    except requests.RequestException as e:
        print(f"获取验证码失败: {e}")
        return None

def encode_password(password):
    encoded_password = base64.b64encode(password.encode()).decode()
    return encoded_password

def login(sess, login_url, username, password):
    verify_code = get_verify_code(sess)
    if not verify_code:
        return False

    encoded_password = encode_password(password)
    login_data = {
        'account': username,
        'pwd': encoded_password,
        'verifycode': verify_code
    }

    try:
        response = sess.post(login_url, data=login_data)
        print(response.text)  # 输出响应内容进行调试
        response_json = response.json()
        if response_json.get("status") == "y":
            print('登录成功')
            return True
        else:
            print('登录失败')
            return False
    except requests.RequestException as e:
        print(f"登录请求失败: {e}")
        return False
    except ValueError as e:
        print(f"解析响应失败: {e}")
        return False

def fetch_data_and_store(sess, headers, cursor, conn):
    a = 1
    for j in range(17):
        url = f'http://jwgl.gzist.edu.cn/xsgrkbcx!getKbRq.action?xnxqdm=202302&zc={a}'
        try:
            response = sess.get(url=url, headers=headers).json()
            text = response[0]
            print(response)
            for i in range(49):
                try:
                    # 课程
                    name = text[i]['kcmc']
                except IndexError:
                    break
                # 老师
                teacher = text[i]['teaxms']
                # 地点
                room = text[i]['jxcdmc']
                # 星期几
                day = text[i]['xq']
                # 周次
                attend = text[i]['zc']
                # 节次
                nums_list = str(text[i]['jcdm2']).split(',')
                # 节次-开始
                nums = nums_list[0]
                # 节次-结束
                enum = nums_list[1]
                sql = '''insert into kebiao(name,teacher,room,day,attend,nums,enums) values (%s,%s,%s,%s,%s,%s,%s) ;'''
                cursor.execute(sql, [name, teacher, room, day, attend, nums, enum])
                conn.commit()
            a += 1
        except requests.RequestException as e:
            print(f"获取数据失败: {e}")
            continue

def main():
    # 数据库连接
    conn = pymysql.connect(host='127.0.0.1', user='root', password='798lhh', database='progress', charset='utf8mb4')
    cursor = conn.cursor()

    # 登录信息
    username = '20210407430347'
    password = '271589'

    # 初始化会话
    sess = requests.Session()

    # URL 信息
    base_url = 'http://jwgl.gzist.edu.cn'
    login_url = f'{base_url}/login!doLogin.action'
    headers = {
        'User-Agent': UserAgent().random,
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'http://jwgl.gzist.edu.cn/'
    }

    # 登录
    while True:
        if login(sess, login_url, username, password):
            break
        else:
            print("尝试重新登录...")

    # 获取数据并存储
    fetch_data_and_store(sess, headers, cursor, conn)
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
