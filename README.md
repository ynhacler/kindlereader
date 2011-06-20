# Kindlereader

一个定时将Google reader发送至kindle的工具

* [master](https://github.com/jiedan/kindlereader/) 分支为单用户版(基于python), 运行于 Linux, Mac OSX, Windows
* [gae](https://github.com/jiedan/kindlereader/tree/gae) 分支为运行于 Google app engine 的多用户版, demo: [http://reader.dogear.mobi](http://reader.dogear.mobi)

## 单用户版使用说明

* 安装 python ( 2.5-2.7, 2.4和3.0未测试), 大多liunx和osx已内置
* 修改 config.sample.ini 为 config.ini 并按说明修改其中内容
* 下载并拷贝 kindlegen 到 kindlereader.py 所在目录，并添加可执行权限
* 在终端或命令符内运行 python kindlereader.py
* Windows用户可以安装 py2exe 然执行 python build_exe.py 生成kindlereader.exe

## 参考

* python: [http://www.python.org/](http://www.python.org/)
* py2exe: [http://www.py2exe.org/](http://www.py2exe.org/)
* Kindlegen下载地址: [http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000234621](http://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000234621)

## 许可

Kindlereader is Licensed under the MIT license: [http://www.opensource.org/licenses/mit-license.php](http://www.opensource.org/licenses/mit-license.php)