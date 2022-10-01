from os import access
from flask import Flask, render_template, request, session, redirect
from urllib import parse
from zenora import APIClient
from flask import Flask, render_template, request
import hurry.filesize, secrets, json, os
from os.path import splitext
from PIL import Image
from datetime import date
import json
import random
import datetime
from datetime import datetime

now = datetime.now()
today = date.today()

TOKEN = "OTk3MjI4NjI2NDU2MTAwOTQ0.GYLBzI.Ejpc-XM3HGmF39oaP6cD8k8-qCZ0X3kL-v0VcY"
CLIENT_SECRET = "oT7ofudW6WEzM79WsaORQLc4_fa1s84l"
REDIRECT_URI = "http://localhost:80/callback"
OAUTH_URL = f"https://discord.com/api/oauth2/authorize?client_id=997228626456100944&redirect_uri={parse.quote(REDIRECT_URI)}&response_type=code&scope=identify"

app = Flask(__name__)
app.config['SECRET_KEY'] = "secret"
client = APIClient(TOKEN, client_secret=CLIENT_SECRET)

author_name = 'neksio'
api_key = 'Flz9lEmSHvavfCPkFHSF'
storage_folder = 'static/screenshots/images'
website_url = 'http://localhost:80/'

whitelist = [
    "987337901182418954"
]

@app.route("/")
def home():
    whitelisted = len(whitelist)
    dir_path = r'static/screenshots/images/'
    count = 0
    for path in os.listdir(dir_path):
        if os.path.isfile(os.path.join(dir_path, path)):
            count += 1
    
    def get_dir_size(path='.'):
        total = 0
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_dir_size(entry.path)
        return total

    def get_size(path='.'):
        if os.path.isfile(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            return get_dir_size(path)

    sizef = str(round(get_size(f'static/screenshots/images/')/(1024*1024), 2))
    if 'token' in session:
        bearer_client = APIClient(session.get('token'), bearer=True)
        current_user = bearer_client.users.get_current_user()
        print(current_user)
        if str(current_user.id) in whitelist:
            return render_template("index.html", current_user=current_user, key =api_key, count=count, size=sizef, whitelisted=whitelisted)
        else:
            session.clear()
            return redirect("/")
    return render_template("index.html", oauth_url=OAUTH_URL, count=count, size=sizef, whitelisted=whitelisted)

@app.route("/callback")
def callback():
    code = request.args['code']
    access_token = client.oauth.get_access_token(code, REDIRECT_URI).access_token
    session['token'] = access_token
    return redirect("/")

@app.route('/<page>')
def screenshoturl(page):
    if f'{page}.png' not in os.listdir(storage_folder):
        return render_template('404.html', URL=website_url)

    try:
        with open(f'static/screenshots/json/{page}.json') as f:
            uploader = json.load(f)["author_name"]
    except Exception as e:
        print(e)
        pass
    return render_template('image.html',
                           ss_location=f'{website_url}/static/screenshots/images/{page}.png',
                           json_location=f'{website_url}/static/screenshots/json/{page}.json',
                           ss_thumbnail=f'{page}.png',
                           date = today.strftime("%d/%m/%Y"),
                           hour = now.strftime("%H:%M:%S"),
                           answer = str(round(os.path.getsize(f'static/screenshots/images/{page}.png')/1024, 2)),
                           cur_url=page)

@app.route('/upload', methods=['POST'])
def upload():
    if not request.method == 'POST':
        return {"error": "Method Not Allowed"}, 405
    used_api_key = request.form.to_dict(flat=False)['secret_key'][0]

    if used_api_key == api_key:
        file = request.files['image']
        extension = splitext(file.filename)[1]
        file.flush()
        size = os.fstat(file.fileno()).st_size
        if extension != '.png':
            return 'File type is not supported', 415

        elif size > 6000000:
            return 'File size too large', 400

        else:
            image = Image.open(file)
            data = list(image.getdata())
            file_without_exif = Image.new(image.mode, image.size)
            file_without_exif.putdata(data)
            filename = secrets.token_urlsafe(8)
            file_without_exif.save(os.path.join(storage_folder, filename + extension))

            image_json = {"title": filename + '.png',
                          "author_name": author_name,
                          "author_url": website_url,
                          "provider_name": hurry.filesize.size(size, system=hurry.filesize.alternative)}

            with open(f'static/screenshots/json/{filename}.json', 'w+') as f:
                json.dump(image_json, f, indent=4)
            return json.dumps({"filename": filename, "extension": extension}), 200
    else:
        return 'Unauthorized use', 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(port="80", debug=True)