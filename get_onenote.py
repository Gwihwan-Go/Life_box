import msal
from msal import PublicClientApplication
import requests
import json
from onenote_export_utils import *
from requests_oauthlib import OAuth2Session

CLIENT_SECRET='G2I8Q~dAEVI_UoHLF1tiBrHA.pf7QXl~egaEQbKj' # This is the secret key for the app registration
APPLICATION_ID='2d90ba13-6c4d-4625-a652-f48d1614c27a' # This is the ID of the app registration
base_url = 'https://graph.microsoft.com/v1.0/' # Microsoft Graph API endpoint
endpoint = base_url + 'me/onenote/notebooks' #/sections/pages 
scopes = ['Notes.Read', 'Notes.Read.All', 'User.Read'] # Add other scopes/permissions as needed.
authority_url = 'https://login.microsoftonline.com/organizations' #consumers - personal account, organizations - work/school account

def main() :

    selected_notebooks = ['Diary'] # Notebook Name where your notes are stored
    onenote_result = {}
    target_days = 10 

    client_instance = msal.PublicClientApplication( # Create a public client application
        client_id=APPLICATION_ID, # The client ID of the app registration
        authority=authority_url # The authority URL for Microsoft Graph API
    )

    flow = client_instance.initiate_device_flow(scopes=scopes) # Initiate the device flow`
    print(flow['message']) # Print the message from the response`

    access_result = client_instance.acquire_token_by_device_flow(flow) # Acquire the token by device flow
    if "access_token" in access_result:
        print("successfully got access token")
    else:
        print(access_result.get("error"))
        print(access_result.get("error_description"))
        print(access_result.get("correlation_id"))

    # if there is no target_days ? then all the pages in selected notebook will be looked at
    graph_client = OAuth2Session(token=access_result)

    notebooks = get_json(graph_client, f'{graph_url}/me/onenote/notebooks')
    notebooks, select = filter_items(notebooks, selected_notebooks, 'notebooks', 0)

    for nb in notebooks :
        indent_print(0, nb["displayName"]) # Print the name of the notebook
        onenote_result[nb["displayName"]] = {} # Create a dictionary for the notebook
        sections = get_json(graph_client, nb['sectionsUrl']) # Get the sections of the notebook
        sections, select = filter_items(sections, select, 'sections', 1) # Filter the sections
        # Pop the latest pages from the sections
        onenote_result[nb["displayName"]] = pop_latest_pages(graph_client, sections, select, target_days) 
    
    return onenote_result


if __name__ == "__main__":

    main()