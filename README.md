# Dormitricity

Real-time monitoring of your dormitory's remaining electricity balance

实时监测您宿舍的剩余电费

## 这是什么？

Dormitricity 是由 Python 构建的爬虫，运行在 GitHub Actions 上。它以固定的时间间隔查询宿舍剩余电量，生成历史剩余电量和用电功率的图表，并预测电费将在何时耗尽。

你可以在本仓库的 `logs` 分支看到当前监测宿舍的用电情况。

## 如何使用？

1. Star [本仓库](https://github.com/KeithCoreDumped/Dormitricity)
2. Fork [本仓库](https://github.com/KeithCoreDumped/Dormitricity)，仅复制 `master` 分支即可
3. 获取cookies（以 Microsoft Edge 为例）

   - 使用浏览器登陆[电费查询页面](https://app.bupt.edu.cn/buptdf/wap/default/chong)，确保您的宿舍电费查询结果正确
   - 在浏览器中点击网址左侧的🔒图标查看站点信息
   - 单击 `Cookie 和站点数据` -> `Cookie(正在使用 1 个 Cookie)`
   - 然后依次展开 `网址/Cookie` 得到 `UUkey` 和 `eai-sess` 两个 Cookies

   也可参阅 [在 Microsoft Edge 中查看 Cookie - Microsoft 支持](https://support.microsoft.com/zh-cn/microsoft-edge/%E5%9C%A8-microsoft-edge-%E4%B8%AD%E6%9F%A5%E7%9C%8B-cookie-a7d95376-f2cd-8e4a-25dc-1de753474879)
4. 获取查询字符串，用于指定查询的宿舍

   - 查询字符串主要包含校区、公寓、楼层、宿舍四部分信息，其写法基本和电费查询页面上显示的一致
   - 一个合法的查询字符串看起来像这样：

     ```txt
     西土城.学五楼.3.5-312-节能蓝天@学五-312宿舍
     ```

     或者这样：

     ```txt
     沙河.沙河校区雁北园A楼.1层.A楼102@沙河A102宿舍
     ```

     > 注意两个校区的楼层写法不同且有别于查询网站。这是由于学校接口返回数据的不一致性
     >

     查询字符串的@符号后面的是宿舍标识符，用于加密和邮件提醒。参阅？？
   - 可以同时查询多个宿舍，不同宿舍的查询字符串用半角逗号 `,` 分隔
5. 准备自定义的 `passphrase`

   - `passphrase` 用于加密，更换不同的 `passphrase` 会生成不同的文件名和密文，导致读取失败或历史记录丢失。建议仅设置一次 `passphrase`
   - 可以使用在线随机密码生成器，建议不包含特殊字符 $"`\\
6. 在 Secrets 中设置以上信息
   在 GitHub 仓库设置 -> `Secrets and variables` -> `Actions` -> `Repository secrets` 中添加下列三个 Secrets

   - `QUERY_STR`，例如

     ```txt
     西土城.学五楼.3.5-312-节能蓝天@学五-312宿舍,沙河.沙河校区雁北园A楼.1层.A楼102@沙河A102宿舍
     ```
   - `COOKIES`，例如

     ```txt
     UUkey=kj0xexrgphqg7mpoflwvw9npmwkjkrkj&eai-sess=1odrcuq6kbi4u2y46ck7ak5q06
     ```
   - `PASSPHRASE`，按上述要求生成的随机字符串

## 会因此被开盒吗？
