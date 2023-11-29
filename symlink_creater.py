import os
import threading
import time
import queue
import logging
import sys

class SymlinkCreator:
    def __init__(self, source_folder, target_folder, num_threads=8):
        self.source_folder = source_folder
        self.target_folder = target_folder
        self.num_threads = num_threads
        self.allowed_extensions = (".mkv", ".iso", ".ts", ".mp4", ".avi", ".rmvb", ".wmv", ".m2ts", ".mpg", ".flv", ".rm", ".mov")
        self.created_links = 0
        self.existing_links = 0
        self.file_queue = queue.Queue()

    def create_symlink(self, src, dst, thread_name):
        try:
            if os.path.exists(dst):
                self.existing_links += 1
                print(f"线程 {thread_name}: 软链接已存在，跳过:{dst} \n")
                return
            os.symlink(src, dst)
            self.created_links += 1
            print(f"线程 {thread_name}: {src} => {dst} \n")
            logging.info(f"线程 {thread_name}: {src} => {dst} \n")
        except Exception as e:
            pass

    def create_and_print_link(self, thread_name):
        while True:
            source_file = self.file_queue.get()
            if source_file is None:
                break
            relative_path = os.path.relpath(source_file, self.source_folder)
            target_file = os.path.join(self.target_folder, relative_path)
            # 确保目标文件夹存在，如果不存在则创建
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            self.create_symlink(source_file, target_file, thread_name)
            self.file_queue.task_done()

    def get_source_files(self):
        for dp, dn, filenames in os.walk(self.source_folder):
            for f in filenames:
                source_file = os.path.join(dp, f)
                if source_file.endswith(self.allowed_extensions):
                    yield source_file

    def run(self):
        start_time = time.time()
        print(f"开始更新软链接...")
        logging.info(f"开始更新软链接...")
        threads = []

        for i in range(self.num_threads):
            thread_name = f"Thread-{i + 1}"
            thread = threading.Thread(target=self.create_and_print_link, args=(thread_name,))
            threads.append(thread)
            thread.start()

        for source_file in self.get_source_files():
            self.file_queue.put(source_file)

        # 添加停止任务
        for i in range(self.num_threads):
            self.file_queue.put(None)

        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time
        message = f"总耗时: {total_time:.2f} 秒, 共处理软链接数：{self.created_links + self.existing_links}个，共创建软链接数：{self.created_links}，共跳过软链接数：{self.existing_links}"
        print(message)
        logging.info(message)
        return message

if __name__ == "__main__":
    # 配置日志
    log_path = 'symlink_creater.log'
    logging.basicConfig(filename=log_path, level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

    # 记录程序运行时间
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logging.info(f"程序运行开始时间: {current_time}")

    # 优先从命令行参数获取源文件夹和链接文件夹路径
    if len(sys.argv) == 3:
        source_folder = sys.argv[1]
        target_folder = sys.argv[2]
    else:
        # 否则从config.txt中读取路径
        dir_dict = {}
        with open('config.txt', 'r') as file:
            for line in file:
                key, value = line.strip().split("=")
                dir_dict[key.strip()] = value.strip()
        source_folder = dir_dict.get('media_dir', '')
        target_folder = dir_dict.get('symlink_dir', '')

    # 如果路径为空则打印错误信息
    if not source_folder or not target_folder:
        print("Error: Please provide source folder and target folder paths.")
    else:
        num_threads = 8
        symlink_creator = SymlinkCreator(source_folder, target_folder, num_threads)
        symlink_creator.run()
