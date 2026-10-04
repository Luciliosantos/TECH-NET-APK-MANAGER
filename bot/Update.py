import os
import json
import requests

def edit_paste(paste_id, token, file_path, new_title=None, new_visibility=None):
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    
    with open(file_path, "r", encoding="utf-8") as f:
        new_content = f.read()

    url = f"https://pastefy.app/api/v2/paste/{paste_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {"content": new_content}
    if new_title:
        payload["title"] = new_title
    if new_visibility:
        payload["visibility"] = new_visibility.upper()

    response = requests.put(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        data = response.json()
        
        paste_data = data.get("paste", data)
        paste_id_final = paste_data.get("id") or paste_id
        paste_title = paste_data.get("title", "No title")
        paste_visibility = paste_data.get("visibility", "UNKNOWN")
        paste_url = f"https://pastefy.app/{paste_id_final}/raw"

        print("✅ Paste updated successfully!")
        print("📄 Title:", paste_title)
        print("🌐 Visibility:", paste_visibility)
        print("🔗 Final URL:", paste_url)
    else:
        print(f"❌ Failed to update ({response.status_code}):\n{response.text}")



if __name__ == "__main__":
    my_token = "my_token"
    my_paste_id = "myid"

    file_name = "update.txt"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, file_name)

    edit_paste(my_paste_id, my_token, file_path, new_title="Updated from File", new_visibility="UNLISTED")