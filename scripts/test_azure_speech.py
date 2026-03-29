#!/usr/bin/env python3
"""
Azure Speech 发音评估测试脚本

用法:
1. 先设置环境变量:
   export SPEECH_ASSESSOR=azure
   export AZURE_SPEECH_KEY=your-key
   export AZURE_SPEECH_REGION=eastasia

2. 运行测试:
   python scripts/test_azure_speech.py
"""

import os
import sys
import asyncio
import wave
import io

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def generate_test_wav(text: str = "Hello world") -> bytes:
    """生成一个简单的测试 WAV 音频文件。

    注意：这是一个合成音频（正弦波），不是真实语音。
    仅用于测试 Azure API 连接，不会有有效的语音识别结果。
    """
    # 音频参数
    sample_rate = 16000
    duration = 2  # 2秒
    frequency = 440  # A4 音调

    # 生成正弦波音频数据
    import math
    samples = []
    for i in range(int(sample_rate * duration)):
        # 生成正弦波样本 (16-bit PCM)
        sample = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
        samples.append(sample)

    # 创建 WAV 文件
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav_file:
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # 将样本转换为字节
        import struct
        audio_data = struct.pack('<' + 'h' * len(samples), *samples)
        wav_file.writeframes(audio_data)

    return output.getvalue()


async def test_azure_speech():
    """测试 Azure Speech 评估器。"""
    print("=" * 60)
    print("Azure Speech 发音评估测试")
    print("=" * 60)

    # 检查环境变量
    assessor_type = os.environ.get("SPEECH_ASSESSOR", "mock")
    azure_key = os.environ.get("AZURE_SPEECH_KEY", "")
    azure_region = os.environ.get("AZURE_SPEECH_REGION", "")

    print(f"\n环境配置:")
    print(f"  SPEECH_ASSESSOR={assessor_type}")
    print(f"  AZURE_SPEECH_KEY={'*' * 10 if azure_key else '未设置'}")
    print(f"  AZURE_SPEECH_REGION={azure_region or '未设置'}")

    if not azure_key or not azure_region:
        print("\n⚠️  警告: AZURE_SPEECH_KEY 和 AZURE_SPEECH_REGION 未设置")
        print("  将使用 Mock 评估器进行测试（无需 Azure 账户）")
        print("\n如需使用真实 Azure 服务，请设置:")
        print("  export SPEECH_ASSESSOR=azure")
        print("  export AZURE_SPEECH_KEY=your-key-here")
        print("  export AZURE_SPEECH_REGION=eastasia")
        print("\n继续 Mock 测试...\n")
        has_azure_key = False
    else:
        has_azure_key = True

    # 导入评估器
    try:
        from app.services.speech_assessment import get_assessor
        try:
            from app.services.speech_assessment import AzureSpeechAssessor
        except ImportError:
            AzureSpeechAssessor = None
    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        return 1

    # 获取评估器
    print(f"\n获取评估器 (SPEECH_ASSESSOR={assessor_type})...")
    assessor = get_assessor()
    print(f"  ✓ 评估器类型: {type(assessor).__name__}")

    if has_azure_key and AzureSpeechAssessor and not isinstance(assessor, AzureSpeechAssessor):
        print(f"\n⚠️  警告: 当前使用的是 {type(assessor).__name__}，不是 AzureSpeechAssessor")
        print("  设置 SPEECH_ASSESSOR=azure 以使用 Azure 评估器")

    # 生成测试音频
    test_text = "Hello world"
    print(f"\n生成测试音频...")
    print(f"  参考文本: \"{test_text}\"")
    audio_bytes = generate_test_wav(test_text)
    print(f"  ✓ 音频大小: {len(audio_bytes)} bytes")

    # 测试评估
    print(f"\n调用 Azure Speech API...")
    print("  (注意：使用合成音频，预期不会有有效识别结果)")
    print("-" * 60)

    try:
        result = await assessor.assess(audio_bytes, test_text)

        print(f"\n✅ 评估成功!")
        print(f"\n结果:")
        print(f"  总分: {result.score}")
        print(f"  等级: {result.level}")
        print(f"  反馈: {result.feedback}")
        print(f"  单词评分:")
        for ws in result.word_scores:
            status_emoji = "✓" if ws.status == "good" else "✗"
            print(f"    {status_emoji} {ws.word}: {ws.score} ({ws.status})")

    except ValueError as e:
        print(f"\n❌ 验证错误: {e}")
        return 1
    except RuntimeError as e:
        print(f"\n❌ API 错误: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 意外错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_azure_speech())
    sys.exit(exit_code)
