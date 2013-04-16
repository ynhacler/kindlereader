# Kindlereader

一个定时将Google reader发送至kindle的工具
其中NoGR分支由[WilliamGates](https://github.com/williamgateszhao)开发

* [master](https://github.com/jiedan/kindlereader/) 分支为单用户版(基于python), 运行于 Linux, Mac OSX, Windows
* [gae](https://github.com/jiedan/kindlereader/tree/gae) 分支为运行于 Google app engine 的多用户版, demo: [http://www.mydogear.com](http://www.mydogear.com)
* [NoGR](https://github.com/williamgateszhao/kindlereader/tree/NoGR) 分支为单用户版(基于python), 不依赖于Google Reader的API，从config.ini文件读取Feed地址并获取数据，运行于 Linux, Mac OSX, Windows


## 使用说明

* 详细使用说明请看[这里](http://blog.williamgates.net/2013/04/kindle-reader-without-google-reader/)

## 简要使用说明（Master/NoGR分支）
* 安装 Python (建议版本2.7), 大多Liunx和OSX已内置Python
* (NoGR版本特有）安装 Python 的 feedparser 库
* 修改 config.sample.ini 为 config.ini 并按说明修改其中内容
* 下载并拷贝 kindlegen 到 kindlereader.py 所在目录，并添加可执行权限
* 在终端或命令符内运行 ```python kindlereader.py```

## 对Windows用户的特别说明（Master/NoGR分支）
* kindlereader.exe 运行不需要安装 Python 环境, 将 kindlereader.exe 和 kindlegen.exe 及 config.ini 放在同一目录内，运行 kindlereader.exe 即可

## 参考

* python: [http://www.python.org/](http://www.python.org/)
* py2exe: [http://www.py2exe.org/](http://www.py2exe.org/)
* Kindlegen下载地址: [KindleGen](http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211)

## 许可

Kindlereader is Licensed under the MIT license: [http://www.opensource.org/licenses/mit-license.php](http://www.opensource.org/licenses/mit-license.php)

## NoGR分支版本历史

* 0.4.4 引入[Kindlestrip](http://www.mobileread.com/forums/showthread.php?t=96903)，大幅度压缩了生成mobi文件的大小（一般小于原先的50%）;打包了exe文件，使得NoGR分支可以在windows不依赖Python环境运行，对普通用户更加友好
* 0.4.3 修复了不会自动退出的BUG;修复了对"/"结尾Feed地址处理的BUG
* 0.4.2 修复了某些feed地址必须以"/"结尾或反之所导致的问题，对feed是否读取成功进行判断
* 0.4.1 增加限制最旧文章时间的功能;修改了日期格式
* 0.4.0 it works

## 待开发

* 解决图片url中含有非ASCII字符时的下载错误
