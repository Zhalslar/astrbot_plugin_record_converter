import asyncio
import os
import aiohttp
from astrbot.core.message.components import Reply
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.api import logger



def get_replyer_id(event: AiocqhttpMessageEvent) -> str | None:
    """获取被引用消息者的id"""
    for seg in event.get_messages():
        if isinstance(seg, Reply):
            return str(seg.sender_id)


async def get_nickname(event: AiocqhttpMessageEvent, user_id: int | str) -> str:
    """获取指定群友的群昵称或Q名"""
    client = event.bot
    group_id = event.get_group_id()
    all_info = await client.get_group_member_info(
        group_id=int(group_id), user_id=int(user_id)
    )
    return all_info.get("card") or all_info.get("nickname")


def get_reply_chain(event: AiocqhttpMessageEvent):
    """获取回复链"""
    chain = event.message_obj.message
    reply_chain = chain[0].chain if chain and isinstance(chain[0], Reply) else None
    return reply_chain


async def download_file(url: str) -> bytes | None:
    """下载图片"""
    url = url.replace("https://", "http://")
    try:
        async with aiohttp.ClientSession() as client:
            response = await client.get(url)
            img_bytes = await response.read()
            return img_bytes
    except Exception as e:
        logger.error(f"图片下载失败: {e}")


def guess_audio_ext(file_bytes: bytes) -> str:
    """根据文件头猜测常见音频扩展名（无依赖版）"""
    header = file_bytes[:16]

    magic_map = [
        (b"ID3", ".mp3"),  # MP3 - ID3 标签
        (b"\xff\xfb", ".mp3"),  # MP3 - 帧同步
        (b"RIFF", ".wav"),  # WAV - RIFF chunk
        (b"OggS", ".ogg"),  # OGG
        (b"fLaC", ".flac"),  # FLAC
        (b"\xff\xf1", ".aac"),  # AAC - ADTS sync word
        (b"\xff\xf9", ".aac"),  # AAC - ADTS sync word
    ]

    for magic, ext in magic_map:
        if header.startswith(magic):
            # WAV 需要额外确认是 WAVE 格式
            if ext == ".wav" and header[8:12] != b"WAVE":
                continue
            return ext

    return ".dat"  # 未识别


async def upload_file(
    event: AiocqhttpMessageEvent,
    path: str,
    name: str | None = None,
    send_private: bool = False,
):
    """上传文件"""
    client = event.bot
    group_id = event.get_group_id()
    name = name or os.path.basename(path)
    if not send_private and group_id:
        await client.upload_group_file(
            group_id=int(group_id),
            file=str(path),
            name=name,
        )
    else:
        await client.upload_private_file(
            user_id=int(event.get_sender_id()),
            file=str(path),
            name=name,
        )


async def extract_audio(video_path: str, out_path: str) -> str:
    cmd = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "copy",
        "-y",
        out_path,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    if proc.stdout is None:
        raise RuntimeError("无法获取 ffmpeg 的 stdout")

    async for line in proc.stdout:
        print(line.decode(), end="")

    await proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg 执行失败")

    return out_path
