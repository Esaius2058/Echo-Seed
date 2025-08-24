import json
import builtins
from ..ai.playlist_generator import PlaylistGenerator
from ..ui.cli import PlaylistCLI
from spotipy import Spotify
from unittest.mock import MagicMock
from openai import OpenAI

sp_client = MagicMock(spec=Spotify)
ai_client = MagicMock(spec=OpenAI)
generator = PlaylistGenerator(sp_client, "Mellow")

def test_get_clusters_for_mood_returns_correct_ids(tmp_path, monkeypatch):
    fake_mood_labels_file = tmp_path / "cluster_mood_map.json"
    fake_data = {"0": "Happy", "1": "Sad", "2": "Hype", "3": "Mellow"}
    fake_mood_labels_file.write_text(json.dumps(fake_data))

    monkeypatch.setattr("echoseed.ui.cli.mood_labels_file", fake_mood_labels_file)

    mood = generator.get_clusters_for_mood()

    assert mood == ["3"]

def test_get_playlist_name_returns_string(monkeypatch):
    class FakeResponse:
        class FakeChoice:
            class FakeMessage:
                content = "Sunset Vibes\nLate Night Drive\nMood Booster"
            message = FakeMessage()
        choices = [FakeChoice()]

    def fake_create(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(generator.ai_client.chat.completions, "create", fake_create)

    name = generator.get_playlist_name()

    assert name in ["Sunset Vibes", "Late Night Drive", "Mood Booster"]

def test_get_artists_from_playlist_extracts_unique_names(monkeypatch):
    sp_client.user_playlists.return_value = {
        "items": [
            {"id": "playlist1"},
            {"id": "playlist2"},
            {"id": "playlist3"},
        ]
    }

    def fake_playlist_items(playlist_id):
        if playlist_id == "playlist1":
            return {
                "items": [
                    {"track": {"artists": [{"name": "Drake"}, {"name": "Rihanna"}]}},
                    {"track": {"artists": [{"name": "Kanye West"}]}},
                ],
                "next": None,
            }
        if playlist_id == "playlist2":
            return {
                "items": [
                    {"track": {"artists": [{"name": "Drake"}]}},
                    {"track": {"artists": [{"name": "Adele"}]}},
                ],
                "next": None,
            }

    sp_client.playlist_items.side_effect = fake_playlist_items
    sp_client.next.side_effect = lambda _: None

    artists = generator.get_artists_from_playlists()

    assert set(artists) == {"Drake", "Rihanna", "Kanye West", "Adele"}

def test_get_recommended_tracks_returns_list(monkeypatch):
    class FakeResponse:
        class FakeChoice:
            class FakeMessage:
                content = ("1.Kendrick Lamar - Alright\n"
                           "2.J Cole - Middle Child\n"
                           "3.SZA - Broken Clocks\n"
                           "4.Jay Rock - OSOM\n"
                           "5.J Cole - Apparently")
            message = FakeMessage()
        choices = [FakeChoice()]

    def fake_create(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(generator.ai_client.chat.completions, "create", fake_create)

    recommended_tracks = generator.get_recommended_tracks(limit=5)

    assert recommended_tracks == ["Kendrick Lamar - Alright",
                                  "J Cole - Middle Child",
                                  "SZA - Broken Clocks",
                                  "Jay Rock - OSOM",
                                  "J Cole - Apparently"]

def test_generate_playlist_creates_and_adds(monkeypatch):
    sp_client.me.return_value = {"id": "fake_user"}
    sp_client.user_playlist_create.return_value = {"id": "playlist123"}

    class FakeNameResponse:
        class FakeChoice:
            class FakeMessage:
                content = "Sunset Vibes\nLate Night Drive\nMood Booster"
            message = FakeMessage()
        choices = [FakeChoice()]

    class FakeRecResponse:
        class FakeChoice:
            class FakeMessage:
                content = ("1.Kendrick Lamar - Alright\n"
                           "2.J Cole - Middle Child\n"
                           "3.SZA - Broken Clocks\n"
                           "4.Jay Rock - OSOM\n"
                           "5.J Cole - Apparently")
            message = FakeMessage()
        choices = [FakeChoice()]

    def fake_create_name(*args, **kwargs):
        return FakeNameResponse()

    def fake_create_recs(*args, **kwargs):
        return FakeRecResponse()

    monkeypatch.setattr(sp_client, "search", lambda q, type, limit: {
        "tracks": {"items": [{"uri": f"spotify:track:{q.replace(' ', '_')}"}]}
    })

    # Patch name and rec calls separately
    monkeypatch.setattr(generator.ai_client.chat.completions, "create", fake_create_name)
    # Patch get_recommended_tracks to directly use FakeRecResponse
    monkeypatch.setattr(generator, "get_recommended_tracks", lambda limit=25: [
        "Drake - Hotline Bling",
        "Kanye West - Stronger"
    ])

    generator.generate_playlist(limit=2)

    # We don't care about the exact URIs order, just that playlist_add_items was called
    args, kwargs = sp_client.playlist_add_items.call_args
    playlist_id, track_uris = args
    assert playlist_id == "playlist123"
    assert all(uri.startswith("spotify:track:") for uri in track_uris)
    assert "Hotline_Bling" in track_uris[0] or "Stronger" in track_uris[0]

def test_cli_to_generator_integration(monkeypatch, tmp_path):
    fake_mood_file = tmp_path / "cluster_mood_map.json"
    fake_data = {"0": "happy", "1": "hype", "2": "sad", "3": "mellow"}
    fake_mood_file.write_text(json.dumps(fake_data))

    fake_clustered_file = tmp_path / "clustered_tracks.csv"
    fake_clustered_file.write_text("track_id,cluster\nfoo,0\nbar,1\n")

    # Patch globals in cli.py
    monkeypatch.setattr("echoseed.ui.cli.mood_labels_file", fake_mood_file)
    monkeypatch.setattr("echoseed.ui.cli.clustered_tracks_file", fake_clustered_file)

    monkeypatch.setattr(builtins, "input", lambda _: "2")

    # Fake spotify client
    sp_client = MagicMock()
    sp_client.me.return_value = {"id": "fake_user"}
    sp_client.user_playlist_create.return_value = {"id": "playlist123"}

    # Run CLI
    cli = PlaylistCLI(sp_client)
    mood = cli.display_menu()
    generator = PlaylistGenerator(sp_client, mood)

    class FakeNameResponse:
        class FakeChoice:
            class FakeMessage:
                content = "Sunset Vibes\nLate Night Drive\nMood Booster"
            message = FakeMessage()
        choices = [FakeChoice()]

    class FakeRecResponse:
        class FakeChoice:
            class FakeMessage:
                content = ("1.Kendrick Lamar - Alright\n"
                           "2.J Cole - Middle Child\n"
                           "3.SZA - Broken Clocks\n"
                           "4.Jay Rock - OSOM\n"
                           "5.J Cole - Apparently")
            message = FakeMessage()
        choices = [FakeChoice()]

    def fake_create_name(*args, **kwargs):
        return FakeNameResponse()

    def fake_create_recs(*args, **kwargs):
        return FakeRecResponse()

    monkeypatch.setattr(sp_client, "search", lambda q, type, limit:{
        "tracks": {"items": [{"uri": f"spotify:track:{q.replace(' ', '_')}"}]}
    })
    monkeypatch.setattr(generator.ai_client.chat.completions, "create", fake_create_name)
    monkeypatch.setattr(generator, "get_recommended_tracks", lambda limit=25: [
        "J Cole -  Apparently",
        "Kanye West - Stronger",
        "Earl Sweatshirt - Sunday"
    ])

    generator.generate_playlist(limit=3)

    args, kwargs = sp_client.playlist_add_items.call_args
    playlist_id, track_uris = args
    assert mood == "hype"
    assert all(uri.startswith("spotify:track:") for uri in track_uris)
    assert "Apparently" in track_uris[0] or "Sunday" in track_uris[0]
