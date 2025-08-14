import asyncio
from datetime import datetime
import os
import random

import aiofiles
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, StarTools, register
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.message.components import File, Plain, Record, Video
from astrbot.api import logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from .utils import (
    download_file,
    extract_audio,
    get_nickname,
    get_reply_chain,
    get_replyer_id,
    guess_audio_ext,
    upload_file,
)


@register(
    "astrbot_plugin_record_converter",
    "Zhalslar",
    "QQ语音转化插件",
    "v1.0.1",
)
class RecordConverterPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.format = config.get("format", "mp3")
        self.send_private = config.get("send_private", False)
        self.plugin_data_dir = str(
            StarTools.get_data_dir("astrbot_plugin_record_converter")
        )
        self.manager_group_id = config.get("manager_group_id", "")

        auto_config: dict = config.get("auto_config", {})
        self.default_character = auto_config.get("default_character", "")
        self.send_record_probability: float = auto_config.get(
            "send_record_probability", 0.15
        )
        self.max_resp_text_len: int = auto_config.get("max_resp_text_len", 50)
        self.character_id = None

    async def get_file_name(
        self, event: AiocqhttpMessageEvent, file: bytes | None = None
    ) -> str:
        """生成文件名"""
        replyer_id = get_replyer_id(event) or 0
        nickname = await get_nickname(event, user_id=replyer_id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = guess_audio_ext(file) if file else self.format
        return f"{nickname}_{timestamp}.{ext}"

    @staticmethod
    async def get_character_id(
        event: AiocqhttpMessageEvent, character: str = "温柔妹妹"
    ):
        """获取AI角色ID"""
        group_id = event.get_group_id()
        data = await event.bot.get_ai_characters(group_id=int(group_id))
        for category in data:
            for ch in category["characters"]:
                if ch["character_name"] == character:
                    return ch["character_id"]

    async def qq_tts(self, event: AiocqhttpMessageEvent, text: str):
        """调用QQ声聊合成语音并发送"""
        if not self.character_id:
            self.character_id = await self.get_character_id(
                event, character=self.default_character
            )
        group_id = self.manager_group_id or event.get_group_id()
        audio_path = await event.bot.get_ai_record(
            character=self.character_id, group_id=int(group_id), text=text
        )
        return audio_path

    @filter.command("转语音")
    async def to_record(self, event: AiocqhttpMessageEvent, arg: str | int = ""):
        """文件、文本 -> 语音"""
        reply_chain = get_reply_chain(event)
        seg = reply_chain[0] if reply_chain else None
        msg = event.message_str.removeprefix("转语音").strip()
        text = seg.text if (isinstance(seg, Plain) and seg.text) else msg

        # 文件 -> 语音
        if isinstance(seg, File) and seg.url:
            record_file = await download_file(seg.url)
            if not record_file:
                yield event.plain_result("文件下载失败")
                return

            file_name = await self.get_file_name(event, record_file)
            audio_path = os.path.join(self.plugin_data_dir, file_name)

            try:
                with open(audio_path, "wb") as f:
                    f.write(record_file)
            except Exception as e:
                yield event.plain_result(f"保存文件时出错: {e}")
                return

            yield event.chain_result([Record(audio_path)])
            return

        # 视频 -> 语音
        elif isinstance(seg, Video) and seg.file:
            path = await seg.convert_to_file_path()  # 实测该方法暂时无效，等待框架修复
            out_path = asyncio.run(extract_audio(path, self.plugin_data_dir))
            file_name = await self.get_file_name(event)
            await upload_file(
                event, path=out_path, name=file_name, send_private=self.send_private
            )
            return

        # 文本 -> 语音
        elif text:
            # 使用astrbot的tts
            if tts := self.context.get_using_tts_provider():
                if audio_path := await tts.get_audio(text):
                    yield event.chain_result([Record(audio_path)])
                    return
            # 使用qq的tts
            audio_path = await self.qq_tts(event, text)
            if self.manager_group_id:
                yield event.chain_result([Record(audio_path)])
            event.stop_event()

    @filter.command("转文件")
    async def to_file(self, event: AiocqhttpMessageEvent):
        """语音 -> 文件"""
        reply_chain = get_reply_chain(event)
        if not reply_chain:
            yield event.plain_result("需引用语音")
            return

        seg = reply_chain[0]

        # 语音 -> 文件
        if isinstance(seg, Record) and seg.url:
            file_name = await self.get_file_name(event)
            audio_path = os.path.join(self.plugin_data_dir, file_name)
            if file := await download_file(seg.url):
                async with aiofiles.open(audio_path, "wb") as fp:
                    await fp.write(file)
            await upload_file(
                event,
                path=audio_path,
                name=file_name,
                send_private=self.send_private,
            )
            if not event.is_private_chat() and self.send_private:
                yield event.plain_result("私发给你了")
            logger.info(f"成功转化语音文件: {seg.file} -> {file_name}")
            event.stop_event()
            return

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AiocqhttpMessageEvent):
        """将文本按概率生成语音并发送"""
        # 概率控制
        if random.random() > self.send_record_probability:
            return
        chain = event.get_result().chain
        seg = chain[0]

        # 纯短文本
        if (
            len(chain) == 1
            and isinstance(seg, Plain)
            and len(seg.text) < self.max_resp_text_len
        ):
            audio_path = await self.qq_tts(event, seg.text)
            if self.manager_group_id:
                chain.clear()
                chain.append(Record.fromURL(audio_path))
