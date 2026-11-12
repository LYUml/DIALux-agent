# DIALux-agent

用 AI 或命令行操作 DIALux evo，完成建模、布灯、计算、保存和报告导出。

- CLI 是命令行入口。
- MCP 让 AI 客户端调用工具。
- [Skill](skills/dialux-agent/SKILL.md) 是给 AI 的操作说明。

## 安装

需要 Windows、Python 3.12 和 DIALux evo。已测试 DIALux evo 14.1。桌面操作需要交互式 Windows 会话，可能占用前台焦点。CAD 原生转换和打印另需 AutoCAD Core Console，默认使用 AutoCAD 2027。

在 PowerShell 中运行：

~~~powershell
git clone https://github.com/LYUml/DIALux-agent.git
cd DIALux-agent
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m src.dialux_agent --help
~~~

## CLI

启动并查看 DIALux 状态：

~~~powershell
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-launch
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-status
~~~

创建和检查示例房间：

~~~powershell
.\.venv\Scripts\python.exe -m src.dialux_agent room-create --spec examples/validation-room.json --output local/demo-room.stf
.\.venv\Scripts\python.exe -m src.dialux_agent stf-inspect --path local/demo-room.stf
~~~

对已打开的工程计算、保存和导出，将路径替换为自己的工程：

~~~powershell
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-calculate --expected-project C:/Projects/demo.evo
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-save --expected-project C:/Projects/demo.evo
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-export-pdf --expected-project C:/Projects/demo.evo --path C:/Projects/report.pdf
~~~

命令返回 JSON，各子命令支持 --help。冷启动可能需要数分钟。输出请选择新路径，工程和报告建议存放在 Git 忽略的 local/ 目录。一次运行一个桌面任务。超时后先检查工程状态，再决定是否重试。

## MCP

在 AI 客户端中添加以下配置，将 C:/path/to/DIALux-agent 替换为实际克隆路径，然后重新连接客户端：

~~~json
{
  "mcpServers": {
    "dialux": {
      "command": "C:/path/to/DIALux-agent/.venv/Scripts/python.exe",
      "args": ["C:/path/to/DIALux-agent/src/server.py"]
    }
  }
}
~~~

可调用 desktop_status、create_room、desktop_calculate 等工具。CLI 与 MCP 共用后端。Skill 可按客户端支持的方式加载。

## 使用范围

支持 STF 房间、ULD 灯具、阵列控制、真实计算、PDF 报告及独立 CAD 工具。香港规则放在可替换的 profiles/ 中，使用时需要确认适用范围。

报告解析以英文 DIALux 输出为主。复杂工程的布灯和恢复能力有适用边界，详见 [验收与限制](docs/current-acceptance.md)。

## 参考

- [桌面操作](docs/standalone-desktop.md)
- [布灯与核对](docs/grid-application.md)
- [CAD 示例](docs/framed-cad-quickstart.md)
- [香港规则来源](docs/hk-source-register.md)
- [上游来源](docs/upstream-review.md)

开发测试：

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q
~~~

STF 读写复用 MIT 许可的 MCP_Dialux，许可证保留在 vendor/MCP_Dialux/LICENSE。
