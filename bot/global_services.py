from notion.client import NotionClient

_notion_client = None

def start_client(notion_token: str):
   global notion_client
   # , monitor=True, start_monitoring=True
   notion_client = NotionClient(notion_token)

def get_notion_client() -> NotionClient:
    return notion_client 


