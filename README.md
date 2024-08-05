# Reciperr2Trakt

A no-nonsense program to import Reciperr JSON list (StevenLu List) to your Trakt List. 

See https://dsync89.com/guides/homelab/virtual-live-tv/export-reciperr-list-to-trakt/ for complete tutorial to setting this up.

Make sure to generate API token from your Trakt account.

Replace the following variables:
- CLIENT_ID
- CLIENT_SECRET
- USERNAME
- LIST_NAME
- LIST_DESCRIPTION
- MOVIES_URL

Then run,

```
python3 app.py
```

## How `reciperr2trakt` Work

**Trakt VIP account is required to create Trakt personal list and adding items to the list. See https://trakt.docs.apiary.io/introduction/vip-methods for more details.**

1. Get [Device Code from Trakt (OAuth)](https://trakt.docs.apiary.io/reference/authentication-devices) to authenticate your device running the script. 
    - If this is the first time, you will need to authenticate your PC running the script by entering the code shown in the script via https://trakt.tv/activate when asked to. 
    - The access code is then save it to a local `access_code.json` file so that it won't ask again the next time. 
    - You only need to authenticate and authorzie again if the code expired or the `access_code.json` is not found. 
2. [Get all your Personal Lists from your Trakt account](https://trakt.docs.apiary.io/reference/lists/list/get-list), and check if the list you wanted to create exist.
    - [Create the list](https://trakt.docs.apiary.io/reference/users/lists/create-personal-list) if it doesn't exist, and get the created list `slug_id`.
    - If the list already exist, then get the list `slug_id`
3. Parse Reciperr movie list JSON and format it according to Trakt expected `movie` JSON structure.
4. [Add the Trakt formatted `movie` JSON structure array to the user list](https://trakt.docs.apiary.io/reference/users/add-list-items/add-items-to-personal-list).
5. Profit!
