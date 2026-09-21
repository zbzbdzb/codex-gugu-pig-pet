# 测试记录

测试环境：Windows，Codex 26.915.4065.0 的宠物图集格式。

| 范围 | 结果 |
| --- | --- |
| 图集规格、73 个有效帧、透明空白格、边界留白、WebP 无损解码 | 通过 |
| 原始 GIF 八帧用于右移、左移逐帧镜像 | 通过 |
| 鼻子、尾巴、眼睛尺寸、受限的局部动作修改 | 通过 |
| 预览脚本的九类动作、播放/暂停/逐帧、16 个方向、主题切换 | 通过 |
| 本地浏览器加载与动画视觉检查 | 通过 |
| 首次安装、重复安装、模拟更新、旧文件备份、兼容版安装 | 通过 |
| DryRun 不写文件、不同宠物 ID 拒绝覆盖 | 通过 |
| 真实本地安装文件与发布资源的 SHA-256 一致性 | 通过 |
| 发布 ZIP 完整性及文件清单 | 通过 |

原生 Codex 宠物窗口的自动状态触发没有进行 UI 自动化验证；浏览器预览循环播放选中动作，不能代替应用自身的状态调度测试。

## 复现

在 Windows 上安装 Python 3.10+ 和 Node.js，然后在项目根目录运行：

```powershell
python -m pip install -r requirements.txt
python scripts/build_pet.py
python scripts/make_preview.py
node scripts/verify_preview.cjs
python scripts/verify_installation.py
python scripts/package_release.py
```

安装测试使用项目下的独立 `.test-output/` 目录，不会更改实际使用中的宠物。构建预览的中文标签使用 Windows 自带的微软雅黑字体。

机器可读结果保存在 `validation.json`、`validation-pixels.json` 和 `validation-installation.json`。
