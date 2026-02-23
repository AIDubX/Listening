import pathlib
import os
import json
from app.utils.character_recognition import CharacterRecognition
from app.model.api import Params
from pathlib import Path

class Listening:
    def __init__(self):
        self._data_dir = Path("configs/listening")
        self._tags_data = {"dialogue": {"defaultRole": [{"id": "默认对话", "value": "dialogue"}],
                                        "defaultFlag": [{"id": "默认对话", "value": True}],
                                        "role": []}, "narration": {}}
        self._id = None
        self._config = {}
        self.c: CharacterRecognition = None
        self._file_mtime = None
        self._current_file = None
        self.load_data()

    @property
    def tags_data(self):
        return self._tags_data

    @tags_data.setter
    def tags_data(self, value):
        self._tags_data = value
        self.c = CharacterRecognition(self._tags_data)
        # Callback can be added here if needed
        # self._on_tags_data_changed(value)

    def get_config(self):
        d = []
        for f in pathlib.Path(self._data_dir).glob("*.json"):
            d.append(f.stem)
        return d

    def load_data(self, id="default"):
        if self._id == id:
            # Check if file has been modified
            file_path = os.path.join(self._data_dir, f"{id}.json")
            if self._current_file == file_path:
                current_mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else None
                if current_mtime == self._file_mtime:
                    return

        self._id = id
        file_path = os.path.join(self._data_dir, f"{id}.json")
        self._current_file = file_path
        
        if os.path.exists(file_path):
            self._file_mtime = os.path.getmtime(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        
        tags_data = {"dialogue": {"defaultRole": [{"id": "默认对话", "value": "dialogue"}],
                                  "defaultFlag": [{"id": "默认对话", "value": True}],
                                  "role": []}, "narration": {}}
        
        for k, v in self._config.items():
            if k == "旁白" or k == "默认对话":
                continue
            tags_data["dialogue"]["defaultRole"].append(
                {"id": k, "value": v.get("tag", 'dialogue')})
            tags_data["dialogue"]["defaultFlag"].append({"id": k, "value": False})
            tags_data["dialogue"]["role"].append({"id": k, "value": v.get("regex", k)})
        self.tags_data = tags_data

    def text_to_params(self, text, id):
        self.load_data(id)
        data = []
        for handle_text in self.c.handle_text(text):
            if handle_text['tag'] == "narration":
                role = "旁白"
            elif handle_text['tag'] == "dialogue" and not handle_text.get("id"):
                role = "默认对话"
            else:
                role = handle_text["id"]
            params = Params(text=handle_text['text'], **self._config.get(role, {})) 
            data.append((params,role))
        return data