# AI听书

AI听书因为个人没精力再维护，但是很多人还在使用，在这里我就把基于IndexTTS-VLLM版本的代码全放出来了，以AGPL协议开源。其他引擎的代码可以参考app.service中的代码。

## 功能：

- [x] 统一的音色管理模块。
- [x] 完善的在线API接口
- [x] 提供基于basic-auth的认证机制。
- [x] 不捆绑任何TTS引擎，可方便更换任何TTS
- [x] 小说多角色多人物识别
- [x] 支持一键导入开源阅读，多小说配置，方便同时听多本小说
- [x] 支持gradio内网传统，部署在家用电脑上外出也能听书
- [x] 支持长篇小说一键合成，自动画本等功能。

# 使用方法

- [ ] 需要python3.11及以上版本 
- [ ] vllm 0.10.2版本

## 以IndexTTS-VLLM为例

1. 克隆indextts-vllm项目代码

```
git clone https://cnb.cool/ai_dub/indextts-vllm
cd indextts-vllm
pip install -r requirements.txt
```

2. [下载AI听书代码](https://github.com/AIDubX/Listening/archive/refs/heads/main.zip)

3. 解压代码到indextts-vllm目录下

4. 运行
```
python listening.py
```


