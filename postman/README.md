# Harmonia API Testing Guide

This guide will help you test the Harmonia API endpoints using Postman without needing the UI.

## Prerequisites

1. Install [Postman](https://www.postman.com/downloads/)
2. Make sure the Harmonia server is running locally (`python manage.py runserver`)

## Setup

1. Import the `harmonia_api_test.postman_collection.json` file into Postman
2. Create a new environment in Postman and set the following variables:
   - `base_url`: http://localhost:8000
   - `access_token`: (leave empty for now)
   - `track_id`: (leave empty for now)

## Testing Flow

### 1. Authentication

1. First, use the "Register" request to create a new user
2. Then use the "Login" request to get an access token
3. Copy the access token from the response and set it as the `access_token` environment variable

### 2. Tracks

1. Use "Get All Tracks" to see existing tracks
2. Use "Create Track" to create a new track
3. Copy the track ID from the response and set it as the `track_id` environment variable
4. Use "Get Track Detail" to verify the track was created correctly

### 3. Media

1. Use "Upload Track Audio" to upload an audio file for the track
   - Select an audio file from your computer
   - The track_id will be automatically included from the environment variable
2. Use "Get Track Audio" to verify the audio file was uploaded correctly

## Tips

- Use the "Tests" tab in Postman to write automated tests
- Use the "Console" in Postman to debug requests
- Save responses as examples for future reference
- Use environment variables to switch between different environments (development, staging, production)

## Common Issues

1. If you get a 401 Unauthorized error:
   - Check if your access token is valid
   - Try logging in again to get a new token

2. If you get a 400 Bad Request error:
   - Check the request body format
   - Make sure all required fields are included

3. If you get a 404 Not Found error:
   - Check if the URL is correct
   - Make sure the resource exists

## Additional Resources

- [Postman Documentation](https://learning.postman.com/docs/getting-started/introduction/)
- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [JWT Authentication Documentation](https://django-rest-framework-simplejwt.readthedocs.io/) 