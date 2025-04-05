# Teams Interpreter Bot

## Overview

Teams Interpreter Bot provides real-time translation and text-to-speech capabilities for Microsoft Teams. This bot can translate messages between languages (currently supporting English, Spanish, and Russian) and generate speech from translated text.

## Repository Structure

This repository contains the Python components of the bot that will be deployed to Replit:
/
├── app.py (Flask web server)
├── teams_bot.py (Teams bot logic)
├── calling_handler.py (Call handling code)
├── requirements.txt (Python dependencies)
├── .env.example (Sample environment variables - rename to .env)
└── src/
├── init.py (Empty file)
├── tts/
│ ├── init.py (Empty file)
│ └── simple_tts.py (TTS implementation)
└── translation/
├── init.py (Empty file)
└── simple_translator.py (Translator implementation)


## Setup Instructions

### 1. Replit Setup (Python Backend)

1. **Create a Replit account** at [replit.com](https://replit.com) (free tier)

2. **Import this repository**
   - Click "Create Repl" > "Import from GitHub"
   - Paste this repository URL
   - Choose "Python" as the language

3. **Set up environment variables**
   - In your Repl, click the lock icon (🔒) on the left sidebar
   - Add these secrets:
     - `MICROSOFT_APP_ID`: Your Bot's App ID
     - `MICROSOFT_APP_PASSWORD`: Your Bot's App Password 
     - `PORT`: 8000

4. **Install dependencies**
   - Replit should automatically install dependencies from requirements.txt
   - If not, run this in the Replit Shell: `pip install -r requirements.txt`

5. **Run the project**
   - Click the "Run" button
   - Note your Replit URL (e.g., https://teams-interpreter-bot.yourusername.repl.co)

### 2. Hostinger Setup (PHP Proxy)

Create the following files on your Hostinger web hosting:

1. **Directory structure**
   ```
   /teams-bot/
   ├── api_messages.php
   ├── api_calls.php
   ├── index.php
   └── static/
       ├── manifest.json
       ├── color.png
       └── outline.png
   ```

2. **api_messages.php**
   ```php
   <?php
   // Forward Teams messages to your Python hosting on Replit
   header('Content-Type: application/json');

   // Your Replit app URL - REPLACE WITH YOUR ACTUAL URL
   $python_app_url = 'https://teams-interpreter-bot.yourusername.repl.co/api/messages';

   // Get the request method
   $method = $_SERVER['REQUEST_METHOD'];

   // Get headers
   $headers = getallheaders();
   $forward_headers = array();
   foreach ($headers as $header => $value) {
       if ($header != 'Host') {
           $forward_headers[] = "$header: $value";
       }
   }

   // Get request body
   $request_body = file_get_contents('php://input');

   // Initialize cURL session
   $ch = curl_init($python_app_url);

   // Set cURL options
   curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
   curl_setopt($ch, CURLOPT_POSTFIELDS, $request_body);
   curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
   curl_setopt($ch, CURLOPT_HTTPHEADER, $forward_headers);
   curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);

   // Execute the request
   $response = curl_exec($ch);
   $status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);

   // Close cURL
   curl_close($ch);

   // Return the response with status code
   http_response_code($status_code);
   echo $response;
   ```

3. **api_calls.php**
   ```php
   <?php
   // Forward Teams calling webhooks to your Python hosting on Replit
   header('Content-Type: application/json');

   // Your Replit app URL - REPLACE WITH YOUR ACTUAL URL
   $python_app_url = 'https://teams-interpreter-bot.yourusername.repl.co/api/calls';

   // Get the request method
   $method = $_SERVER['REQUEST_METHOD'];

   // Get headers
   $headers = getallheaders();
   $forward_headers = array();
   foreach ($headers as $header => $value) {
       if ($header != 'Host') {
           $forward_headers[] = "$header: $value";
       }
   }

   // Get request body
   $request_body = file_get_contents('php://input');

   // Initialize cURL session
   $ch = curl_init($python_app_url);

   // Set cURL options
   curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
   curl_setopt($ch, CURLOPT_POSTFIELDS, $request_body);
   curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
   curl_setopt($ch, CURLOPT_HTTPHEADER, $forward_headers);
   curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);

   // Execute the request
   $response = curl_exec($ch);
   $status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);

   // Close cURL
   curl_close($ch);

   // Return the response with status code
   http_response_code($status_code);
   echo $response;
   ```

4. **index.php**
   ```php
   <?php
   echo "Teams Interpreter Bot Proxy is running!";
   ```

5. **static/manifest.json**
   ```json
   {
       "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.11/MicrosoftTeams.schema.json",
       "manifestVersion": "1.11",
       "version": "1.0.0",
       "id": "YOUR_BOT_ID_HERE",
       "packageName": "com.yourcompany.teamsinterpreterbot",
       "developer": {
           "name": "Your Company",
           "websiteUrl": "https://yourdomain.com",
           "privacyUrl": "https://yourdomain.com/privacy",
           "termsOfUseUrl": "https://yourdomain.com/terms"
       },
       "icons": {
           "color": "color.png",
           "outline": "outline.png"
       },
       "name": {
           "short": "Interpreter Bot",
           "full": "Teams Interpreter Bot"
       },
       "description": {
           "short": "Bot for real-time translation and speech synthesis",
           "full": "This bot provides real-time translation between languages and can convert text to speech during meetings."
       },
       "accentColor": "#FFFFFF",
       "bots": [
           {
               "botId": "YOUR_BOT_ID_HERE",
               "scopes": ["personal", "team", "groupchat"],
               "supportsFiles": false,
               "isNotificationOnly": false,
               "supportsCalling": true,
               "supportsVideo": true,
               "commandLists": [
                   {
                       "scopes": ["personal", "team", "groupchat"],
                       "commands": [
                           {
                               "title": "help",
                               "description": "Shows help information"
                           },
                           {
                               "title": "languages",
                               "description": "Shows supported languages"
                           },
                           {
                               "title": "translate",
                               "description": "Translates text to another language"
                           },
                           {
                               "title": "speak",
                               "description": "Converts text to speech"
                           }
                       ]
                   }
               ]
           }
       ],
       "permissions": [
           "identity",
           "messageTeamMembers",
           "calling"
       ],
       "validDomains": [
           "yourdomain.com",
           "*.yourdomain.com",
           "teams-interpreter-bot.yourusername.repl.co"
       ]
   }
   ```

### 3. Azure Bot Registration

1. **Update Messaging Endpoint**
   - In Azure Portal, find your Bot Channels Registration
   - Set Messaging endpoint to: `https://yourdomain.com/teams-bot/api_messages.php`

2. **Update Calling Webhook**
   - In Channels > Microsoft Teams, enable Calling
   - Set Calling webhook to: `https://yourdomain.com/teams-bot/api_calls.php`

### 4. Teams App Package

1. **Update manifest.json**
   - Replace `YOUR_BOT_ID_HERE` with your actual Bot ID
   - Update URLs to use your actual domain

2. **Create app package**
   - Zip together: manifest.json, color.png, outline.png
   - Upload to Teams through "Apps" > "Manage your apps" > "Upload a custom app"

## Functionality

- **Translation**: Works between English, Spanish, and Russian
- **Text-to-Speech**: Converts translated text to speech
- **Bot Commands**:
  - `/help` - Show help information
  - `/languages` - Show supported languages
  - `/translate <text>` - Translate specific text
  - `/speak <text>` - Convert text to speech
  - `/call <meeting-link>` - Join a meeting (Coming soon)

## Troubleshooting

- **Check Replit Logs**: If your bot isn't responding, check the Replit console for errors
- **Check PHP Logs**: Look for errors in your Hostinger error logs
- **Verify Endpoints**: Make sure your proxy URLs are correct in Azure Bot Registration
- **Test Connectivity**: Try visiting https://yourdomain.com/teams-bot/ to see if the proxy is running

## License

MIT License

## Credits

Created by Your Name / Your Company.
