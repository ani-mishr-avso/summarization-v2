import json

from collections import defaultdict

from app.transcript_parser.models import TurnEntry, Speaker

def _turn_entry(id_counter: int, words: list[dict], speaker_id: int) -> TurnEntry:
    """
    Create a turn entry from a list of words and a speaker.

    Args:
        id_counter (int): The id of the turn.
        words (list[dict]): A list of words from the transcript.
        speaker (int): The speaker of the words.

    Returns:
        TurnEntry: A turn entry.
    """
    start_time = words[0]["start"]
    end_time = words[-1]["end"]
    duration = end_time - start_time
    text = " ".join(w["punctuated_word"] for w in words)
    speaker_label = "spk_" + str(speaker_id)
    return TurnEntry(
        id=id_counter,
        start_time=round(start_time, 2),
        end_time=round(end_time, 2),
        duration=round(duration, 2),
        text=text,
    speaker_label=speaker_label
    )


def parse_transcript(json_file_path: str) -> list[TurnEntry]:
    """
    Parse a transcript from a JSON file.
    Convert the transcript into a list of turn entries.
    Args:
        json_file_path (str): The path to the JSON file.

    Returns:
        list[TurnEntry]: A list of speaker turn entries.
    """
    with open(json_file_path, 'r') as f:
        data = json.load(f)

    channels = data['results']['channels']
    turns = []
    id_counter = 0
    for channel in channels:
        words = channel['alternatives'][0]['words']
        current_speaker = None
        turn_words = []
        for word in words:
            if current_speaker is not None and current_speaker != word["speaker"]:
                turns.append(_turn_entry(id_counter, turn_words, current_speaker))
                id_counter += 1
                turn_words = []
            turn_words.append(word)
            current_speaker = word["speaker"]
        if turn_words:
            turns.append(_turn_entry(id_counter, turn_words, current_speaker))
            id_counter += 1

    return turns


def is_short_transcript(parsed_transcript: list[TurnEntry], min_duration: float = 180.0) -> bool:
    """
    Check if a transcript is short.
    
    Args:
        parsed_transcript (list[dict]): The parsed transcript.
        min_duration (float): The minimum duration of the transcript in seconds.
    Returns:
        bool: True if the transcript is short, False otherwise.
    """
    start_time = float(parsed_transcript[0]['start_time'])
    end_time = float(parsed_transcript[-1]['end_time'])
    return end_time - start_time < min_duration


def format_transcript(parsed_transcript: list[TurnEntry], label_map: dict) -> str:
    """
    Format a transcript from a JSON file as a string.
    
    Args:
        parsed_transcript (list[TurnEntry]): The parsed transcript.
        label_map (dict): The Speaker-to-Name label map.
    Returns:
        str: The formatted transcript.
    """

    formatted_transcript = ""
    for turn in parsed_transcript:
        speaker = label_map.get(turn['speaker_label'], turn['speaker_label'])
        utterance = turn['sentence']
        formatted_transcript += f"{speaker}: {utterance}\n"

    return formatted_transcript


def get_duration_mins(transcript: list[dict]) -> int:
    """
    Get the duration of a transcript in minutes.
    
    Args:
        transcript (list[TurnEntry]): The parsed transcript.
    Returns:
        int: The duration of the transcript in minutes.
    """
    start_time = transcript[0]['start_time']
    end_time = transcript[-1]['end_time']
    duration_mins = int(round((end_time - start_time) / 60))
    return duration_mins
