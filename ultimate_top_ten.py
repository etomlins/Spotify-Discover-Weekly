# import necessary modules
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect
from dotenv import load_dotenv
import os

load_dotenv()

my_client_id = os.getenv("CLIENT_ID")
my_client_secret = os.getenv("CLIENT_SECRET")

# initialize Flask app
app = Flask(__name__)

# set the name of the session cookie
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# set a random secret key to sign the cookie
app.secret_key = my_client_secret

# set the key for the token info in the session dictionary
TOKEN_INFO = 'token_info'

# route to handle logging in
@app.route('/')
def login():
    # create a SpotifyOAuth instance and get the authorization URL
    auth_url = create_spotify_oauth().get_authorize_url()
    # redirect the user to the authorization URL
    return redirect(auth_url)

# route to handle the redirect URI after authorization
@app.route('/redirect')
def redirect_page():
    # clear the session
    session.clear()
    # get the authorization code from the request parameters
    code = request.args.get('code')
    # exchange the authorization code for an access token and refresh token
    token_info = create_spotify_oauth().get_access_token(code)
    # save the token info in the session
    session[TOKEN_INFO] = token_info
    # redirect the user to the save_discover_weekly route
    return redirect(url_for('save_ultimate_top_ten',_external=True))

# route to save the Discover Weekly songs to a playlist
@app.route('/saveUltimateTopTen')
def save_ultimate_top_ten():
    try: 
        # get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')
        return redirect("/")

    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])

    # find user's top ten tracks of all time
    top_tracks = sp.current_user_top_tracks(limit=10, offset=0, time_range='long_term')['items']
    song_uris = []
    for song in top_tracks:
        song_uri = song['id']
        song_uris.append(song_uri)
    
    # find user
    user_id = sp.current_user()['id']
    user_display_name = sp.current_user()['display_name']
    playlist_name = f"{user_display_name}'s Ultimate Top Ten Songs"
    desc = f"{user_display_name} is a music legend. Here's the songs loved most by yours truly."

    # actually make playlist
    ultimate_playlist = sp.user_playlist_create(user_id, 
    playlist_name, 
    public=True, 
    collaborative=False, 
    description=desc)
    sp.user_playlist_add_tracks(user_id,ultimate_playlist['id'],song_uris)

    # return a success message
    return ('IT WORKED!')

# function to get the token info from the session
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        redirect(url_for('login', _external=False))
    
    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = my_client_id,
        client_secret = my_client_secret,
        redirect_uri = url_for('redirect_page', _external=True),
        scope='user-top-read playlist-modify-public playlist-modify-private user-read-private user-read-email'
    )


app.run(debug=True)