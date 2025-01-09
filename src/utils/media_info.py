from typing import Dict, List
from pymediainfo import MediaInfo


def get_media_info(file_path: str) -> Dict[str, str]:
    """
    Gets codec, audio, and subtitles from the file using pymediainfo.

    :param file_path: Full path of the file
    :return: Dictionary with video, audio, and subtitle details
    """
    media_info = MediaInfo.parse(file_path)
    video_info: List[str] = []
    audio_info: List[str] = []
    subtitle_info: List[str] = []

    for track in media_info.tracks:
        if track.track_type == "Video":
            codec = track.other_format[0] if track.other_format else "Unknown"
            quality = f"{track.height}p {codec}"
            video_info.append(quality)
        elif track.track_type == "Audio":
            channels = (
                "5.1"
                if track.channel_s == 6
                else f"{track.channel_s}.0"
                if track.channel_s
                else "Unknown"
            )
            audio_format = (
                track.other_format[0].split()[0] if track.other_format else "Unknown"
            )
            audio_name = track.title if track.title else "Unknown"
            # audio_language = (
            #    track.other_language[0] if track.other_language else "Unknown"
            # )
            audio_info.append(f"{audio_name} ({audio_format} {channels})")
        elif track.track_type == "Text":
            subtitle_format = (
                track.other_format[0].upper() if track.other_format else "Unknown"
            )
            if subtitle_format == "UTF-8":
                subtitle_format = "SRT"
            subtitle_name = track.title if track.title else "Unknown"
            # subtitle_language = (
            #    track.other_language[0] if track.other_language else "Unknown"
            # )
            subtitle_info.append(f"{subtitle_name} ({subtitle_format})")

    return {
        "video": ", ".join(video_info),
        "audio": ", ".join(audio_info),
        "subtitles": ", ".join(subtitle_info),
    }
