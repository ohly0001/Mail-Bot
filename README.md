# Installation
## .env File
1. Create a local .env file in the project directory
2. Copy the contents of [env-template.txt](env-template.txt) to the .env
3. Substite the placeholder values (`Example...`) as directed with your personal configuration and authentication details.

## MySQL
1. Install MySQL Server, Manager, and other services as needed. Installation left to reader's discretion and personal system requirements.
2. Import or copy [db-setup.sql](db-setup.sql) into your SQL manager or terminal and execute it. If the database already exists, take a backup of the data and drop the database to ensure a clean but reversible reinstallation occurs.

## Model
1. Download the .gguf from [HF TheBloke/Mistral-7B-Instruct-v0.1-GGUF](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/blob/main/mistral-7b-instruct-v0.1.Q4_0.gguf) to your local [model/](./model/)