import asyncio
from datetime import datetime
import os
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, StarTools, register
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.message.components import File, Record, Video
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
    "v1.0.0",
)
class RecordConverterPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.format = config.get("format", "mp3")
        self.send_private = config.get("send_private", False)
        self.plugin_data_dir = str(StarTools.get_data_dir("astrbot_plugin_record_converter"))

    async def get_file_name(
        self, event: AiocqhttpMessageEvent, file: bytes | None = None
    ) -> str:
        """生成文件名"""
        replyer_id = get_replyer_id(event) or 0
        nickname = await get_nickname(event, user_id=replyer_id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = guess_audio_ext(file) if file else self.format
        return f"{nickname}_{timestamp}.{ext}"

    @filter.command("转格式")
    async def file_to_record(self, event: AiocqhttpMessageEvent):
        """将音频文件、语音消息相互转化"""
        reply_chain = get_reply_chain(event)
        if not reply_chain:
            yield event.plain_result("需引用音频文件/语音消息")
            return

        seg = reply_chain[0]

        # 文件 -> 语音
        if isinstance(seg, File) and seg.url:
            record_file = await download_file(seg.url)
            if not record_file:
                yield event.plain_result("文件下载失败")
                return

            file_name = await self.get_file_name(event, record_file)
            save_path = os.path.join(self.plugin_data_dir, file_name)

            try:
                with open(save_path, "wb") as f:
                    f.write(record_file)
            except Exception as e:
                yield event.plain_result(f"保存文件时出错: {e}")
                return

            yield event.chain_result([Record(file=save_path)])
            return

        # 语音 -> 文件
        if isinstance(seg, Record) and seg.file:
            result = await event.bot.get_record(file=seg.file, out_format=self.format)
            file_name = await self.get_file_name(event)
            await upload_file(
                event, path=result["file"], name=file_name, send_private=self.send_private
            )
            if not event.is_private_chat() and self.send_private:
                yield event.plain_result("私发给你了")
            logger.info(f"成功转化语音文件: {seg.file} -> {file_name}")
            event.stop_event()
            return

        # 视频 -> 音频
        if isinstance(seg, Video) and seg.file:
            path = await seg.convert_to_file_path() # 实测该方法暂时无效，等待框架修复
            out_path = asyncio.run(extract_audio(path, self.plugin_data_dir))
            file_name = await self.get_file_name(event)
            await upload_file(
                event, path=out_path, name=file_name, send_private=self.send_private
            )
            return

        yield event.plain_result("需引用音频文件/语音消息")

