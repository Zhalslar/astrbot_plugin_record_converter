from datetime import datetime
import os
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, StarTools, register
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.message.components import File, Record
from astrbot.api import logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from .utils import (
    download_file,
    get_nickname,
    get_reply_chain,
    get_replyer_id,
    guess_audio_ext,
    upload_file,
)


@register(
    "astrbot_plugin_record_converter",
    "Zhalslar",
    "QQ语音转化插件，包括语音转文件，文件转语音，克服了QQ语音无法转发的问题",
    "v1.0.0",
)
class RecordConverterPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.format = config.get("format", "mp3")
        self.send_private = config.get("send_private", False)
        self.plugin_data_dir = StarTools.get_data_dir("astrbot_plugin_record_converter")

    async def get_file_name(
        self, event: AiocqhttpMessageEvent, file: bytes | None = None
    ) -> str:
        """生成文件名"""
        replyer_id = get_replyer_id(event) or 0
        nickname = await get_nickname(event, user_id=replyer_id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = guess_audio_ext(file) if file else self.format
        return f"{nickname}_{timestamp}.{ext}"

    @filter.command("转文件")
    async def record_to_file(self, event: AiocqhttpMessageEvent):
        """将语音消息转为文件"""
        reply_chain = get_reply_chain(event)
        file = (
            reply_chain[0].file
            if reply_chain and isinstance(reply_chain[0], Record)
            else None
        )
        if not file:
            yield event.plain_result("请同时引用一条语音消息")
            return
        result = await event.bot.get_record(file=file, out_format=self.format)
        file_name = await self.get_file_name(event)
        await upload_file(
            event, path=result["file"], name=file_name, send_private=self.send_private
        )
        if not event.is_private_chat() and self.send_private:
            yield event.plain_result("私发给你了")
        logger.info(f"成功转化语音文件: {file} -> {file_name}")
        event.stop_event()

    @filter.command("转语音")
    async def file_to_record(self, event: AiocqhttpMessageEvent):
        """将文件转为语音消息"""
        reply_chain = get_reply_chain(event)
        url = (
            reply_chain[0].url
            if reply_chain and isinstance(reply_chain[0], File)
            else None
        )
        if not reply_chain or not url:
            yield event.plain_result("请同时引用一条文件消息")
            return
        file: bytes | None = await download_file(url)
        if not file:
            yield event.plain_result("文件下载失败")
            return
        file_name = await self.get_file_name(event, file)
        save_path = os.path.join(self.plugin_data_dir, file_name)
        try:
            with open(save_path, "wb") as f:
                f.write(file)
        except Exception as e:
            yield event.plain_result(f"保存文件时出错: {e}")
            return
        yield event.chain_result([Record(file=save_path)])
