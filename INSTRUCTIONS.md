## How To Get DipVis Running 
### For Software Developers and Admins

You can set up and test out the system as follows:

1. Install Python 3 
e.g. `winget install -e --id Python.Python.3.9 --scope machine` or `choco install python`

2. Install other requirements (e.g. Django)
    - `pip install -r requirements.txt`

3. Run migrations
   `cd .\visualiser\`
   `python manage.py makemigrations`
   `python manage.py makemigrations`
4. Create a SQLite database - Credit to https://www.tutorialspoint.com/sqlite/sqlite_installation.htm for the following few steps:
− Go to the [SQLite download page](https://www.sqlite.org/download.html), and download precompiled binaries from Windows section.

− Download **BOTH** the sqlite-shell-win32-*.zip and sqlite-dll-win32-*.zip zipped files.

− Create a folder `C:\sqlite` and unzip above two zipped files in this folder, which will give you sqlite3.def, sqlite3.dll and sqlite3.exe files.

− Add `C:\sqlite` to your PATH environment variable
- Open a fresh command prompt and run `sqlite3 dipvis.db` to create a database called dipvis.db

------------TODO: set up tables here-----------

5.
   `python manage.py loaddata players`
   `python manage.py loaddata game_sets`
   It will be auto-populated with Great Powers and a few known players.
5. Create an admin account -- `python manage.py createsuperuser`
6. Run the test server - "python manage.py runserver`
7. Open the URL `http://127.0.0.1:8000/admin/tournament/player/` in
   a web broswer and add players by filling in the fields.
8. Open the URL `http://127.0.0.1:8000/admin/tournament/tournament/` in
   a web browser and add a tournament by filling in the fields. Optionally
   add players to the tournament. Note that adding a player to a tournament
   can take a while because the system copies information from the WDD to
   its own database. This can be avoided by not providing WDD Ids for
   TournamentPlayers.
9. Open the tournament's page `http://127.0.0.1:8000/tournaments/1/` in a
   web browser and try out some of the links.
10. Open the Registered Players URL `http://127.0.0.1:8000/tournaments/1/players/`
   in a web browser and add players to one or more rounds.
11. Go to the roll call page for the first round at
   `http://127.0.0.1:8000/tournaments/1/roll_call/` and identify at least
   seven players as playing in the round (for simplicity, you probably want
   to pick a multiple of seven to start with, although the system can
   deal with other numbers).
12. You'll be taken to the page to create a game for the round. Go ahead and
   do that.
   # When I create a game, I get an error message, but it does populate
   # the game into the tournament. I think it's trying to send emails to
   # the players in the test game and doesn't like that it doesn't have
   # emails for them.
