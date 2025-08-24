import builtins
import json
from echoseed.ui.cli import PlaylistCLI
from unittest.mock import MagicMock
from spotipy import Spotify
import sys

sys.modules["__main__"] = object()

def test_display_menu_shows_all_moods(monkeypatch, capsys, tmp_path):
    fake_mood_file = tmp_path / "cluster_mood_map.json"
    fake_data = {"0": "Happy", "1": "Sad"}
    fake_mood_file.write_text(json.dumps(fake_data))

    fake_clustered_file = tmp_path / "clustered_tracks.csv"
    fake_clustered_file.write_text("track_id,cluster\nfoo,0\nbar,1\n")

    monkeypatch.setattr("echoseed.ui.cli.mood_labels_file", fake_mood_file)
    monkeypatch.setattr("echoseed.ui.cli.clustered_tracks_file", fake_clustered_file)

    monkeypatch.setattr(builtins, "input", lambda _: "1")

    sp_client = MagicMock(spec=Spotify)
    cli = PlaylistCLI(sp_client)

    selected = cli.display_menu()
    captured = capsys.readouterr()

    assert "Happy" in captured.out
    assert "Sad" in captured.out
    assert selected == "Happy"

def test_display_menu_valid_choice(monkeypatch, tmp_path):
    fake_mood_file = tmp_path / "cluster_mood_map.json"
    fake_data = {"0": "happy", "1": "hype", "2": "sad", "3": "mellow"}
    fake_mood_file.write_text(json.dumps(fake_data))

    fake_clustered_file = tmp_path / "clustered_tracks.csv"
    fake_clustered_file.write_text("track_id,cluster\nfoo,0\nbar,1\n")

    monkeypatch.setattr("echoseed.ui.cli.mood_labels_file", fake_mood_file)
    monkeypatch.setattr("echoseed.ui.cli.clustered_tracks_file", fake_clustered_file)

    monkeypatch.setattr(builtins, "input", lambda _:"3")

    sp_client = MagicMock(spec=Spotify)
    cli = PlaylistCLI(sp_client)

    selected = cli.display_menu()

    assert selected == "sad"


def test_display_menu_invalid_choice(monkeypatch, tmp_path, capsys):
    fake_mood_file = tmp_path / "cluster_mood_map.json"
    fake_data = {"0": "happy", "1": "hype", "2": "sad", "3": "mellow"}
    fake_mood_file.write_text(json.dumps(fake_data))

    fake_clustered_file = tmp_path / "clustered_tracks.csv"
    fake_clustered_file.write_text("track_id,cluster\nfoo,0\nbar,1\n")

    monkeypatch.setattr("echoseed.ui.cli.mood_labels_file", fake_mood_file)
    monkeypatch.setattr("echoseed.ui.cli.clustered_tracks_file", fake_clustered_file)

    inputs = iter(["99", "2"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    sp_client = MagicMock(spec=Spotify)
    cli = PlaylistCLI(sp_client)

    selected = cli.display_menu()
    captured = capsys.readouterr()

    assert "Please enter a number between 1 and 4." in captured.out
    assert selected == "hype"

def test_display_menu_non_numeric_input(monkeypatch, capsys, tmp_path):
    fake_mood_file = tmp_path / "cluster_mood_map.json"
    fake_data = {"0": "happy", "1": "hype", "2": "sad", "3": "mellow"}
    fake_mood_file.write_text(json.dumps(fake_data))

    fake_clustered_file = tmp_path / "clustered_tracks.csv"
    fake_clustered_file.write_text("track_id,cluster\nfoo,0\nbar,1\n")

    monkeypatch.setattr("echoseed.ui.cli.mood_labels_file", fake_mood_file)
    monkeypatch.setattr("echoseed.ui.cli.clustered_tracks_file", fake_clustered_file)

    inputs = iter(["abc", "2"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    sp_client = MagicMock(spec=Spotify)
    cli = PlaylistCLI(sp_client)
    selected = cli.display_menu()
    captured = capsys.readouterr()

    assert "Invalid input. Please enter a number." in captured.out
    assert selected == "hype"