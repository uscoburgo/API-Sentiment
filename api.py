from src.config import PORT
from src.app import app
import src.Controllers.chats
import src.Controllers.sentiment

app.run("0.0.0.0", PORT, debug=True)