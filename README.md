# Teams Interpreter Bot

A bot for Microsoft Teams that provides real-time translation and text-to-speech capabilities.

## Features

- Translate messages between languages (English, Spanish, Russian)
- Convert text to speech using Windows TTS voices
- Bot commands for easy interaction
- Simple API for external integrations

## Setup Instructions

### Prerequisites

- Python 3.9+ installed
- Microsoft Azure account for Bot Registration
- Microsoft Teams account with permissions to add custom apps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Register a Bot in Azure

1. Go to the [Azure Portal](https://portal.azure.com)
2. Create a new "Bot Channels Registration" resource
3. Fill in the required details:
   - Name: TeamsInterpreterBot
   - Messaging endpoint: The public URL where your bot will be hosted (we'll use ngrok for testing)
   - Create a Microsoft App ID and password
4. Save the App ID and password

### 3. Configure Environment Variables

1. Open the `.env` file in the project root
2. Add your Microsoft App ID and password:
   ```
   MICROSOFT_APP_ID=your-app-id
   MICROSOFT_APP_PASSWORD=your-app-password
   ```

### 4. Start the Translation Server

```bash
python translation_tts_server.py
```

This starts the translation and TTS service on port 8080.

### 5. Create a Public Endpoint (for development)

To expose your local bot to Microsoft Teams, you can use ngrok:

```bash
ngrok http 3978
```

This will create a public URL like `https://abc123.ngrok.io` that forwards to your local server.

### 6. Update the Messaging Endpoint

1. Go back to your Bot registration in Azure
2. Update the Messaging endpoint with your ngrok URL + `/api/messages`
   (e.g., `https://abc123.ngrok.io/api/messages`)

### 7. Update the Teams Manifest

1. Open `static/manifest.json`
2. Replace `YOUR_BOT_ID_HERE` with your Microsoft App ID
3. Update `validDomains` to include your ngrok domain

### 8. Start the Bot Server

```bash
python app.py
```

This starts the bot server on port 3978.

### 9. Package and Upload to Teams

1. Create a zip file containing:
   - `manifest.json` (from the static folder)
   - `color.png` and `outline.png` icons (you can use placeholder images for testing)
2. In Microsoft Teams, go to "Apps" > "Manage your apps" > "Upload a custom app"
3. Upload the zip file

## Bot Commands

- `/help` - Show help information
- `/languages` - Show supported languages
- `/translate <text>` - Translate text to another language
- `/speak <text>` - Convert text to speech
- `/call <meeting-link>` - Join a meeting (Coming soon)

## Architecture

The system consists of three main components:

1. **Translation and TTS Server** - A Python HTTP server that handles translation and text-to-speech requests.
2. **Teams Bot** - A Bot Framework application that integrates with Microsoft Teams for messaging.
3. **Calling Handler** - Manages real-time media sessions for meeting interpretation.

### Calling Features

The bot now supports joining Teams meetings to provide real-time interpretation. This requires:

1. The calling webhook configured in your bot registration
2. Additional Graph API permissions for calling
3. Proper Teams manifest settings with `supportsCalling` and `supportsVideo` enabled

For full calling functionality, you'll need to:

1. Configure your Bot Channel Registration with call capabilities
2. Add `calls.accessMedia.all` and `calls.joinGroupCalls.all` permissions to your app registration
3. Make sure your web server has the necessary endpoints to handle call events

## Development

### Running the Bot Locally

1. Start the translation server:
   ```
   python translation_tts_server.py
   ```

2. In a separate terminal, start the bot server:
   ```
   python app.py
   ```

3. Use ngrok to create a public URL:
   ```
   ngrok http 3978
   ```

### Troubleshooting

- If the bot doesn't respond, check that your App ID and password are correct in the `.env` file.
- If translations are not working, ensure the translation server is running on port 8080.
- For TTS issues, ensure your Windows system has speech voices installed.

## License

[MIT License](LICENSE)

## Credits

Created by Your Name / Your Company. 