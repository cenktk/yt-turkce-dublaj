# Setup guide for Claude

The user gave you this repo to set up a Turkish dub for English YouTube videos. Reply to the user in their language (usually Turkish). Do every step you can with your own tools. Only two steps belong to the user: the API key and loading the Chrome extension.

## 1. Clone

If the repo is not on disk yet, clone it into the user's home folder:

```bash
git clone https://github.com/cenktk/yt-turkce-dublaj.git ~/yt-turkce-dublaj
```

All later commands run from the repo folder.

## 2. Install the tools

- Python 3.9 or newer (`python3 --version`).
- `yt-dlp` and `ffmpeg`. On macOS: `brew install yt-dlp ffmpeg`. On Windows: `winget install yt-dlp.yt-dlp Gyan.FFmpeg`, and use `python` instead of `python3`.
- Claude Code must be installed and logged in (`claude --version`). The translation step runs `claude -p` and uses the user's own Claude quota.

## 3. API key (user step)

Copy `.env.example` to `.env`. Then ask the user to paste their own Alania v2 TTS key into `.env` as `PATIENTDESK_API_KEY=...`. A user without a key gets one at https://speech.patientdesk.ai/tr.

- Do not ask the user to paste the key into the chat. The key would stay in the chat log.
- Check only that the value is not empty, for example: `awk -F= '/^PATIENTDESK_API_KEY=/{print length($2)}' .env`. Do not print the key.

## 4. Self-test and server

```bash
python3 hazirla.py --selftest
```

Start the server in the background and leave it running. The extension talks only to `localhost:8790`.

```bash
python3 hazirla.py serve --port 8790
```

Check it: `curl -s -X POST -H 'X-Dublaj: 1' http://localhost:8790/durum/dQw4w9WgXcQ` must return JSON with `"calisiyor"`.

## 5. Chrome extension (user step)

Give the user the absolute path of the `eklenti` folder in this repo (for example `/Users/<name>/yt-turkce-dublaj/eklenti`). Then give them these steps:

1. Open `chrome://extensions`.
2. Turn on **Developer mode** (top right).
3. Click **Load unpacked**.
4. Select the `eklenti` folder.
5. Open an English YouTube video and refresh the page.

If an older copy of the extension is installed, the user must remove it first. Chrome runs the copy it loaded, not this repo's copy.

## 6. Use

- The box at the top right of the player shows a voice list and a **Türkçe dublaj hazırla** button. The server prepares the first 90 seconds first, then the whole video.
- On a video that already has a dub, a voice that is not made yet shows as "(hazırla)". Choosing it makes that voice too.
- Cost: the **Ücretsiz (Antalia Mini)** voice is free (0 characters billed); the key is still required. Nisa and Oncel cost about one character per character of speech, per voice. A 15-minute video is about 16k characters per voice.
- Videos without subtitles do not work.

## Troubleshooting

- No box on the video: check that the server runs, then refresh the page. The server log shows a `GET /<videoId>/manifest.json` line for each video the extension checks.
- After a reboot the server is not running. Start step 4 again.
- Job logs: `dublaj/<videoId>.log`.
