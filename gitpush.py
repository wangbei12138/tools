#!/usr/bin/python
import sys,getopt
import re
import os
import shutil
import matplotlib.pyplot as plt

class AutoPush(object):
    def __init__(self, source, target, manifest_url, branch_name):
        self.source = source
        self.target = target
        self.manifest_url = manifest_url
        ## project_info[0]中保存项目在git 仓库的名称
        ## project_info[1]中保存项目相对路径
        self.project_info = ([],[])
        self.branch_name = branch_name

    def get_manifest(self):
        is_exists = os.path.exists(self.target)
        if not is_exists:
            os.makedirs(self.target)
        os.chdir(self.target)

        os.system("git clone %s" %(self.manifest_url))
        self.file_name = self.target + "/manifest/pbx.xml"

    def get_remote_git(self) :
        with open(self.file_name, "r", errors='ignore') as f:
            project = re.compile("project[ ]?name=(.+)?")
            fetch = re.compile("remote[ ]?fetch=(.+)?")
            while True:
                line = f.readline()
                if line == "":
                    break
                project_line = project.search(line)
                fetch_line = fetch.search(line)

                if project_line:
                    substrs = project_line.group().split(" ")

                    name_str = substrs[1]
                    path_str = substrs[2]
                    name_value = name_str.split("=")
                    path_value = path_str.split("=")
                    project_name = eval(name_value[1])
                    project_path = eval(path_value[1])

                    ## 不推送根目录
                    if project_path == "./" :
                        continue

                    self.project_info[0].append(project_name)
                    self.project_info[1].append(project_path)
                if fetch_line:
                    substrs = fetch_line.group().split(" ")
                    fetch_str = substrs[1]
                    fetch_value = fetch_str.split("=")
                    ## 保存仓库的url，如http://git.zhkj-rd.cn:8010
                    self.fetch_info = fetch_value[1]

    def do_push(self) :
        is_exists = os.path.exists(self.target)
        if not is_exists :
            os.makedirs(self.target)
        os.chdir(self.source)
        for i in range(len(self.project_info[0])) :
            path = self.project_info[1][i]
            git_lab_path = self.project_info[0][i]
            source_path = self.source + "/" + path
            git_path = self.fetch_info + "/" + git_lab_path
            str1 = git_lab_path.split(".git")
            str2 = str1[0].split("/")
            git_lab_name = str2[1]
            target_path = self.target + "/" + git_lab_name

            ## 判断源代码地址是否存在
            if not os.path.exists(source_path) :
                print("source path not exists: ", source_path)
                return False
            ## 判断本地分支是否存在
            ret = os.system("git rev-parse --verify -q %s" %(path))
            if ret != 0:
                ## 路径名称作为分支名称，将提交记录分离
                os.system("git subtree split -P %s -b %s" %(path, path))

            ## 判断本地子项目git仓库文件夹是否存在
            is_exists = os.path.exists(target_path)
            if not is_exists :
                os.makedirs(target_path)
                os.chdir(target_path)

            ## 初始化git仓库，并将对应分支拉到本地git
            os.chdir(target_path)
            os.system("git init")
            os.system("git pull %s %s" %(self.source, path))

            ## 检测远程仓库是否存在，如果不存在，则结束本分支相关操作
            ## 根据manifest文件提供的url判断
            ret = os.system("git ls-remote --exit-code -h %s" %(git_path))
            if ret != 0 :
                os.chdir(self.source)
                continue

            # 绑定远程git仓库
            os.system("git remote add origin %s" %(git_path))
            os.system("git branch --set-upstream-to=origin/%s"%(self.branch_name))

            ## push
            #os.system("git push --set-upstream origin %s" %(self.branch_name))

            os.chdir(self.source)
            # 删除分支
            #os.system("git branch -D %s" %(path))
        return True

if __name__ == '__main__':
    '''
    此脚本默认放在pbx项目的根目录下，因此默认根目录为当前执行目录，也可以通过参数手动指定根目录:-s
    目的文件夹的根目录默认为git目录，可通过参数指定:-t
    支持传递branch:-b
    '''
    source_path = os.getcwd()
    target_path = source_path + "/git"
    branch_name = "5.2-new"
    ## 此处使用的是http网址，需要本地配置全局用户名和密码git config --global credential.helper store
    ## 也可通过-f 手动指定地址，如-f git@git.zhkj-rd.cn:ucs5.1/manifest.git
    manifest_git_url = "http://git.zhkj-rd.cn:8010/ucs5.1/manifest.git"

    key1 = 's:t:b:f:'
    opts, args = getopt.getopt(sys.argv[1:], key1)
    for key,value in opts:
        if key == '-s':
            source_path = value
            target_path = source_path + "/git"
        elif key == '-t':
            target_path = value
        elif key == '-b':
            branch_name = value
        elif key == "-f":
            manifest_git_url = value

    a = AutoPush(source_path, target_path, manifest_git_url, branch_name)
    a.get_manifest()
    a.get_remote_git()
    a.do_push()


