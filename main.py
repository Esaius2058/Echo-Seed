import os
import logging
from dotenv import load_dotenv
from echoseed.api.auth import SpotifyAuthService
from echoseed.security.token_manager import TokenManager
from echoseed.security.network_monitor import NetworkMonitor
from echoseed.ai.playlist_generator import PlaylistGenerator
from echoseed.ui.cli import PlaylistCLI

load_dotenv()
logger = logging.getLogger("echoseed.main")
secret_key = os.getenv("SECRET_KEY").encode()

def main():
    try:
        auth_service = SpotifyAuthService()
        auth_service.authenticate()
        spotify_client = auth_service.get_spotify_client()
        access_token = auth_service.get_access_token()
        token_manager = TokenManager(secret_key)
        logger.info("[EchoSeed] Saving Access Token")
        token_manager.save_token(access_token)

        network_monitor = NetworkMonitor(refresh_callback=auth_service.refresh_access_token)
        network_monitor.run()

        cli = PlaylistCLI(spotify_client)
        logger.info("[EchoSeed] UI")
        selected_mood = cli.display_menu()

        generator = PlaylistGenerator(spotify_client, selected_mood)
        logger.info("[EchoSeed] PlaylistGenerator generating playlist")
        playlist = generator.generate_playlist()
    except Exception as e:
        logger.error("Application failed: %s", str(e))
        logger.error(f"Error generating playlist {e}")
        exit(1)

if __name__ == "__main__":
    main()
