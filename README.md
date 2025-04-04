# 🧠 AI - Table Column Data Catalog Assistant

This is a Streamlit-based application that allows users to interact with the OpenAI API and a PostgreSQL database to document and catalog database tables.

The app guides the user through a step-by-step interactive process:
1. Select a table from the database.
2. Retrieve the table structure and existing column comments.
3. Automatically generate missing descriptions using OpenAI.
4. Allow the user to edit or validate comments.
5. Generate and execute SQL `COMMENT ON COLUMN` statements.
6. Export final documentation in Markdown format.

---

## 🚀 Features

- PostgreSQL schema inspection
- Automatic comment generation via OpenAI
- Editable interface for column descriptions
- SQL execution with confirmation
- Markdown export with preview and download
- Logging panel to trace all interactions
- Environment variable support

---

## 📦 Requirements

For local execution:

- Python 3.10 or higher
- pipenv (recommended)
- PostgreSQL database accessible over network
- OpenAI API key

---

## 🔧 Environment Variables

These are used to configure the app:

| Variable           | Description                      |
|--------------------|----------------------------------|
| `OPENAI_API_KEY`   | Your OpenAI API key              |
| `DB_HOST`          | PostgreSQL host                  |
| `DB_PORT`          | PostgreSQL port (default: 5432)  |
| `DB_NAME`          | Database name                    |
| `DB_USER`          | Username                         |
| `DB_PASSWORD`      | Password                         |

You can define them via:

- A `.env` file
- The shell environment
- `docker-compose.yml`

---

## 💻 Local Development

```bash
# Install dependencies
pipenv install --dev

# Run the app
pipenv run streamlit run streamlit_app.py
```
Ensure your .env file is in the root folder and contains the required variables.

---

## 🐳 Run with Docker

Step 1: Build the Docker image
```bash
docker build -t catalog-assistant .
```
Step 2: Run the Docker container (with .env)
```bash
docker run --rm -p 8501:8501 --env-file .env catalog-assistant
``` 
Or pass environment variables directly:
```bash
docker run --rm -p 8501:8501 \
  -e OPENAI_API_KEY=sk-... \
  -e DB_HOST=db.example.com \
  -e DB_PORT=5432 \
  -e DB_NAME=my_db \
  -e DB_USER=user \
  -e DB_PASSWORD=pass \
  catalog-assistant
```
---
## 🐳 Run with Docker Compose

Use the provided docker-compose.yml for convenience:
```bash
docker compose up --build
```
You can define your variables either:
	•	Inside the docker-compose.yml under environment:
	•	Or in a .env file in the project root

## 📝 Output Example

## Table: `table_name`

**Description:** Show the last host name record for each device.

| Column       | Data Type     | Description                            |
|--------------|---------------|----------------------------------------|
| device_sn    | text          | Unique serial number of the device.    |
| host_name    | text          | Last host name seen per device.        |
| updated_at   | timestamptz   | Timestamp of the latest update.        |

---
## 🧩 Folder Structure
```
project-root/
├── Dockerfile
├── docker-compose.yml
├── .env (optional)
├── streamlit_app.py
├── utils/
│   └── utils.py
├── Pipfile
├── Pipfile.lock
```

---

## 🧠 About the Logs

You can enable a sidebar panel to view real-time debug logs including:
-	LLM requests and responses
-	SQL execution tracking
-	User interaction steps

---

## 📤 Roadmap Ideas
- Multi-table batch documentation
- Support for other databases (MySQL, SQLite)
- Export to HTML, PDF
- Authentication

---
## 👤 Author

Developed by Horacio E. Suarez  
Feel free to reach out for feedback or contributions.

GitHub: [https://github.com/Hacho55](https://github.com/Hacho55)  
Email: horacioesuarez@gmail.com

---
## 📄 License

MIT License. Use freely, modify, contribute!