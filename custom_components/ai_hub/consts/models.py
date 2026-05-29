"""Model lists for AI Hub providers."""

from __future__ import annotations

from typing import Final

AI_HUB_CHAT_MODELS: Final = [
    "Qwen/Qwen3.5-4B",
    "Qwen/Qwen3-8B",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
    "Qwen/Qwen2.5-32B-Instruct",
    "Qwen/Qwen2.5-14B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2-VL-72B-Instruct",
    "Qwen/Qwen2-VL-7B-Instruct",
    "deepseek-ai/DeepSeek-V3",
    "deepseek-ai/DeepSeek-R1",
    "deepseek-ai/DeepSeek-V2.5",
    "meta-llama/Llama-3.1-8B-Instruct",
    "meta-llama/Llama-3.1-70B-Instruct",
    "01-ai/Yi-1.5-34B-Chat",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "THUDM/glm-4-9b-chat",
]

AI_HUB_IMAGE_MODELS: Final = [
    "Kwai-Kolors/Kolors",
    "black-forest-labs/FLUX.1-schnell",
    "black-forest-labs/FLUX.1-dev",
    "black-forest-labs/FLUX-pro",
    "stabilityai/stable-diffusion-3-5-large",
    "stabilityai/stable-diffusion-3-medium",
]

VISION_MODELS: Final = [
    "Qwen/Qwen3.5-4B",
]

IMAGE_SIZES: Final = [
    "1024x1024",
    "768x1344",
    "864x1152",
    "1344x768",
    "1152x864",
    "1440x720",
    "720x1440",
]

SILICONFLOW_STT_MODELS: Final = [
    "TeleAI/TeleSpeechASR",
    "FunAudioLLM/SenseVoiceSmall",
]

SILICONFLOW_STT_AUDIO_FORMATS: Final = ["mp3", "wav", "flac", "m4a", "ogg", "webm"]
