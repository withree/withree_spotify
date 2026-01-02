import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

#--------------CONFIG-----------------------
EXCEL_FILE = "albums.xlsx"
PLAYLIST_NAME = "My Album Collection"
PLAYLIST_DESCRIPTION = "Automatically generated from Excel file"
SCOPE = "playlist-modify-public playlist-modify-private"
#-------------------------------------------
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(scope=SCOPE)
)

user_id = sp.me()["id"]

#Get or create playlist
def get_or_create_playlist(name):
    playlists = sp.current_user_playlists(limit=50)

    while playlists:
        for playlist in playlists["items"]:
            if playlist["name"].lower() == name.lower():
                print(f"Using existing playlist: {playlist['name']}")
                return playlist["id"]

        playlists = sp.next(playlists) if playlists["next"] else None

    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        description=PLAYLIST_DESCRIPTION,
        public=True
    )

    print(f"Created new playlist: {name}")
    return playlist["id"]


def get_existing_tracks(playlist_id):
    existing_tracks = set()
    results = sp.playlist_items(playlist_id, limit=100)

    while results:
        for item in results["items"]:
            if item["track"]:
                existing_tracks.add(item["track"]["uri"])
        results = sp.next(results) if results["next"] else None

    return existing_tracks


def get_album_tracks(artist, album):
    query = f"album:{album} artist:{artist}"
    results = sp.search(q=query, type="album", limit=1)

    if not results["albums"]["items"]:
        print(f"Album not found: {artist} - {album}")
        return []

    track_uris = []
    album_id = results["albums"]["items"][0]["id"]
    tracks = sp.album_tracks(album_id, limit=50)

    while tracks:
        for track in tracks["items"]:
            track_uris.append(track["uri"])

        tracks = sp.next(tracks) if tracks["next"] else None

    return track_uris


def main():
    df = pd.read_excel(EXCEL_FILE)
    required_columns = {"Artist", "Album"}
    if not required_columns.issubset(df.columns):
        raise ValueError("Excel file must contain 'Artist' and 'Album' columns")

    playlist_id = get_or_create_playlist(PLAYLIST_NAME)
    existing_track_uris = get_existing_tracks(playlist_id)    

    tracks_to_add = []

    for _, row in df.iterrows():
        artist = str(row["Artist"]).strip()
        album = str(row["Album"]).strip()

        print(f"Processing: {artist} - {album}")
        album_tracks = get_album_tracks(artist, album)

        for track_uri in album_tracks:
            if track_uri not in existing_track_uris:
                tracks_to_add.append(track_uri)
                existing_track_uris.add(track_uri)

    if tracks_to_add:
        for i in range(0, len(track_uris), 50):
            sp.playlist_add_items(playlist_id, track_uris[i:i + batch_size])
            print(f"Added {len(tracks_to_add)} new tracks")
    else:
        print("No new tracks to add")


if __name__ == "__main__":
    main()

