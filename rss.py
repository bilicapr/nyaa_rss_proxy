import os
import requests
import time
import threading
import xml.etree.ElementTree as ET
from http.server import SimpleHTTPRequestHandler
import socketserver

# 配置信息
rss_sources = [
    {
        "query": "我和班上最討厭的女生結婚了",
        "filename": "whwbsztydnsjhl.xml",
        "folder": "downloads"
    },
    {
        "query": "2",
        "filename": "2.xml",
        "folder": "downloads"
    }
]

SERVER_PORT = 45670
UPDATE_INTERVAL = 300  # 5分钟

def create_folder(path):
    """确保目录存在"""
    try:
        os.makedirs(path, exist_ok=True)
        print(f"目录已创建: {path}")
    except Exception as e:
        print(f"目录创建失败: {e}")

def process_rss(source):
    """处理单个RSS源"""
    try:
        # 解析XML
        tree = ET.parse(source['filename'])
        root = tree.getroot()

        # 准备下载目录
        download_dir = os.path.join(source['folder'], source['query'])
        create_folder(download_dir)

        # 遍历所有条目
        for item in root.findall('.//item'):
            link = item.find('link')
            if link is None:
                continue

            torrent_url = link.text.strip()
            if not torrent_url.endswith('.torrent'):
                continue

            # 下载种子文件
            torrent_name = os.path.basename(torrent_url)
            save_path = os.path.join(download_dir, torrent_name)
            
            try:
                response = requests.get(torrent_url, timeout=10)
                response.raise_for_status()
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"下载成功: {torrent_name}")
            except Exception as e:
                print(f"下载失败: {e}")
                continue

            # 更新链接地址
            encoded_path = requests.utils.quote(f"{source['folder']}/{source['query']}/{torrent_name}")
            new_link = f"http://156.229.166.30:{SERVER_PORT}/{encoded_path}"
            link.text = new_link
            print(f"链接已更新: {new_link}")

        # 保存修改后的XML
        tree.write(source['filename'], encoding='utf-8', xml_declaration=True)
        print(f"文件已保存: {source['filename']}")

    except Exception as e:
        print(f"处理错误: {e}")

def update_feeds():
    """更新所有RSS源"""
    for source in rss_sources:
        try:
            # 下载原始RSS
            url = f"https://nyaa.si/?page=rss&q={source['query']}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            with open(source['filename'], 'wb') as f:
                f.write(response.content)
            
            print(f"RSS下载成功: {source['filename']}")
            process_rss(source)

        except Exception as e:
            print(f"更新失败: {e}")

def start_server():
    """启动HTTP服务器"""
    # 设置静态文件目录
    handler = SimpleHTTPRequestHandler
    handler.extensions_map.update({
        '.xml': 'application/xml',
        '.torrent': 'application/x-bittorrent',
    })

    try:
        with socketserver.TCPServer(("", SERVER_PORT), handler) as httpd:
            print(f"服务运行中: http://localhost:{SERVER_PORT}")
            httpd.serve_forever()
    except OSError as e:
        print(f"服务器启动失败: {e}")

if __name__ == "__main__":
    # 首次更新
    update_feeds()

    # 启动服务器线程
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    # 定时任务
    while True:
        time.sleep(UPDATE_INTERVAL)
        update_feeds()