import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth

#---------------CONFIG-----------------
PLAYLIST_NAME = "Popularity based playlist"
PLAYLIST_DESCRIPTION = "Random songs filtered by popularity range"
MIN_POPULARITY = 30     # 0–100
MAX_POPULARITY = 35
TRACK_LIMIT = 100        # number of NEW songs to add per run
#--------------------------------------

scope = "playlist-modify-public playlist-modify-private"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(scope=scope)
)

# Create or find playlist in an account
def get_or_create_playlist(user_id, name, description):
    playlists = sp.current_user_playlists(limit=50)
    for playlist in playlists["items"]:
        if playlist["name"].lower() == name.lower():
            return playlist["id"]

    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=True,
        description=description
    )
    return playlist["id"]

# Get tracks from playlist
def get_existing_tracks(playlist_id):
    existing_tracks = set()
    results = sp.playlist_items(playlist_id, additional_types=["track"])

    while results:
        for item in results["items"]:
            if item["track"]:
                existing_tracks.add(item["track"]["uri"])
        results = sp.next(results) if results["next"] else None

    return existing_tracks

# Find random tracks based on a year, 10 attempts
def find_random_tracks(min_pop, max_pop, limit, exclude_uris):
    new_tracks = set()
    attempts = 0

    while len(new_tracks) < limit and attempts < 50:
        attempts += 1
        year = random.randint(1940,2026)
        offset = random.randint(0, 100000)

        results = sp.search(
            q=f"year:{year}",
            type="track",
            limit=50,
            offset=offset
        )

        for item in results["tracks"]["items"]:
            uri = item["uri"]
            popularity = item["popularity"]

            if (
                min_pop <= popularity <= max_pop
                and uri not in exclude_uris
                and uri not in new_tracks
            ):
                new_tracks.add(uri)

                if len(new_tracks) >= limit:
                    break

    return list(new_tracks)

def add_tracks_to_playlist(playlist_id, track_uris):
    # Spotify allows max 100 tracks per request
    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(playlist_id, track_uris[i:i + 100])

def main():
    user = sp.current_user()
    playlist_id = get_or_create_playlist(
        user["id"],
        PLAYLIST_NAME,
        PLAYLIST_DESCRIPTION
    )

    existing_tracks = get_existing_tracks(playlist_id)

    new_tracks = find_random_tracks(
        MIN_POPULARITY,
        MAX_POPULARITY,
        TRACK_LIMIT,
        existing_tracks
    )

    if new_tracks:
        add_tracks_to_playlist(playlist_id, new_tracks)
        print(f"Added {len(new_tracks)} new tracks to '{PLAYLIST_NAME}'.")
    else:
        print("No new tracks found in the given popularity range.")

if __name__ == "__main__":
    main()
