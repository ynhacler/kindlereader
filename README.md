# Kindlereader

一个定时将RSS/ATOM feed发送至kindle的工具
其中master分支自改为不再依赖Google Reader以来，由[WilliamGates](https://github.com/williamgateszhao)协助开发

**2013年7月1日Google Reader关闭服务之后GR和gae分支版本将无法使用**

* [master](https://github.com/williamgateszhao/kindlereader/tree/NoGR) 分支为单用户版(基于python), 不依赖于Google Reader的API，从config.ini文件读取Feed地址并获取数据，运行于 Linux, Mac OSX, Windows
* [GR](https://github.com/jiedan/kindlereader/tree/GR) 分支为单用户版(基于python), 运行于 Linux, Mac OSX, Windows，从Google reader获取Rss更新
* [gae](https://github.com/jiedan/kindlereader/tree/gae) 分支为运行于 Google app engine 的多用户版，从Google reader获取Rss更新, demo: [http://www.mydogear.com](http://www.mydogear.com)


## 使用说明

* 详细使用说明请看[这里](http://blog.williamgates.net/2013/04/kindle-reader-without-google-reader/)

## 简要使用说明（Master/GR分支）
* 安装 Python (建议版本2.7), 大多Liunx和OSX已内置Python
* (Master分支特有）安装 Python 的 feedparser 库
* 修改 config.sample.ini 为 config.ini 并按说明修改其中内容
* 下载并拷贝 kindlegen 到 kindlereader.py 所在目录，并添加可执行权限
* 在终端或命令符内运行 ```python kindlereader.py```

## 对Windows用户的特别说明（Master/GR分支）
* kindlereader.exe 运行不需要安装 Python 环境, 将 kindlereader.exe 和 kindlegen.exe 及 config.ini 放在同一目录内，运行 kindlereader.exe 即可
* 暂时仅测试了Win7平台，不能保证支持WinXP及更早版本
* WinXP用户如尝试使用，请确保你的C:\Windows\system32\中有以下文件且版本正确﻿：OLEAUT32.dll,USER32.dll,SHELL32.dll,KERNEL32.dll,ADVAPI32.dll,WS2_32.dll,GDI32.dll,ole32.dll

## 参考

* python: [http://www.python.org/](http://www.python.org/)
* py2exe: [http://www.py2exe.org/](http://www.py2exe.org/)
* Kindlegen下载地址: [KindleGen](http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211)

## 许可

Kindlereader is Licensed under the MIT license: [http://www.opensource.org/licenses/mit-license.php](http://www.opensource.org/licenses/mit-license.php)

## Master分支改为不依赖Google Reader（即原来的NoGR分支）以来更新历史

* 0.4.6 修复了对图片URL中含有非ASCII字符的支持，并加强了下载图片的效率和适应性
* 0.4.5 修复了对不提供author或content节点的RSS格式支持
* 0.4.4 引入[Kindlestrip](http://www.mobileread.com/forums/showthread.php?t=96903)，大幅度压缩了生成mobi文件的大小（一般小于原先的50%）;打包了exe文件，使得NoGR分支可以在windows不依赖Python环境运行，对普通用户更加友好
* 0.4.3 修复了不会自动退出的BUG;修复了对"/"结尾Feed地址处理的BUG
* 0.4.2 修复了某些feed地址必须以"/"结尾或反之所导致的问题，对feed是否读取成功进行判断
* 0.4.1 增加限制最旧文章时间的功能;修改了日期格式
* 0.4.0 it works
