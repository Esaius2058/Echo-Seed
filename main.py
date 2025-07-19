import logging
from echoseed.api.auth import SpotifyAuthService
from echoseed.api.playlist_service import SpotifyPlaylistService

logger = logging.getLogger("echoseed.main")
logging.basicConfig(level=logging.INFO)

def get_track_ids(tracks):
    return [track.id for track in tracks]

def start_playlist_generator_with_authentication():
    try:
        auth_service = SpotifyAuthService()
        auth_service.authenticate()

        spotify = auth_service.get_spotify_client()
        playlist_service = SpotifyPlaylistService(spotify)

        playlists = playlist_service.get_user_playlists()
        logger.info("Retrieved %d playlists", len(playlists))

        if playlists:
            selected = playlists[0]
            tracks = playlist_service.get_playlist_tracks(selected.id)
            logger.info("Retrieved %d tracks from playlist '%s'", len(tracks), selected.name)

            track_ids = get_track_ids(tracks)

            # Placeholder for next step (e.g. clustering, analysis)
            logger.info("Fetched %d track IDs for analysis", len(track_ids))

    except Exception as e:
        logger.error("Application failed: %s", str(e))
        exit(1)

if __name__ == "__main__":
    logger.info("Starting EchoSeed...")
    start_playlist_generator_with_authentication()
