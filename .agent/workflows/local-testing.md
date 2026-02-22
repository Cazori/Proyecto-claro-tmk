---
description: How to test Cleo AI localy before committing
---
To test changes without affecting the production version:

1. **Start the Backend**
   - Open a terminal.
   - `cd backend`
   - `python main.py`
   - Verify you see: "Uvicorn running on http://0.0.0.0:8000"

2. **Start the Frontend**
   - Open a SEPARATE terminal.
   - `cd frontend`
   - `npm run dev`
   - Open the URL shown (usually http://localhost:5173).

3. **Verify Changes**
   - Once both are running, go to the chat.
   - Search for "tv43".
   - If it doesn't crash, the fix is working!

4. **Commit Only When Ready**
   - Only run `git add` and `git commit` once you are happy with the local results.
