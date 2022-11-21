# Run code instructions


This repository refered [Onenote_export Repo](!https://github.com/Danmou/onenote_export), [gistyc Repo](!https://github.com/ThomasAlbin/gistyc), and[Productive-box Repo](!https://github.com/GwiHwan-Go/productive-box).


1. Resister your app on Azure


   1-1. Go to https://aad.portal.azure.com/ and log in with your Microsoft account.


   1-2. Select "Azure Active Directory" and then "App registrations" under "Manage".


   1-3. Select "New registration". Choose any name, set "Supported account types" to "Accounts in any 
      organizational directory and personal Microsoft accounts" and under "Redirect URI", select Web 
      and enter `http://localhost:5000/getToken`. Register.


   1-4. Copy "Application (client) ID" and paste it as `client_id` in `config.yaml`.


   1-5. Select "Certificates & secrets" under "Manage". Press "New client secret", choose a name and confirm.


   1-6. Copy the client secret and paste it as `secret` in `config.yaml`.


   1-7. Select "API permissions" under "Manage". Press "Add a permission", scroll down and select OneNote, choose "Delegated permissions" and check "Notes.Read" and "Notes.Read.All". Press "Add permissions".


2. install dependencies.
```bash
pip install -r requirements.txt
```


3. Make 'config.yaml' file, and config 4 variables
   - client_id
   - secret
   - username(Azure id)(!optional)
   - password(Azure pwd)(!optional)


3. run the ```python main.py```

```

8. Make sure you have Python 3.8 (or newer)

This Python script exports all the OneNote notebooks linked to your Microsoft account to HTML files.
