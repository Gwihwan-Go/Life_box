import gistyc
import os

##For github actions##
try :
    if os.environ['GITHUB_ACTIONS'] :
        auth_token = os.environ['auth_token']
        gist_id = os.environ['gist_id']
##For github actions##
except :
    import yaml
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
    f.close()
    auth_token = config['auth_token']
    gist_id = config['gist_id']

file_to_upload_path="./results/Overview my life"
# Initiate the GISTyc class with the auth token
gist_api = gistyc.GISTyc(auth_token=auth_token)

# Update the GIST based on the GISTs ID
response_update_data = gist_api.update_gist(file_name=file_to_upload_path,
                                            gist_id=gist_id)
print(f"gist has successfully updated to {response_update_data['url']}")