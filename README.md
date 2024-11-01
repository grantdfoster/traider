# Hello

## Setup Instructions

1. **Clone the repository:**

   ```sh
   git clone <repository_url>
   cd <repository_name>
   ```

2. **Create a virtual environment:**

   ```sh
   python -m venv venv
   ```

3. **Activate the virtual environment:**

   - On Windows:
     ```sh
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```sh
     source venv/bin/activate
     ```

4. **Install the required packages using pip:**

   ```sh
   pip install -r requirements.txt
   ```

5. **Set up environment variables:**

   - Create a `.env` file in the root directory of the project.
   - Copy the contents from `.env.example` (if available) or refer to the `.env` section in the context provided.

6. **Run the main script:**

   ```sh
   python main.py
   ```

   - If this is the first time running the script, a new wallet will be created and saved to `wallet.json`.
   - If `wallet.json` already exists, the wallet will be loaded from the file.

## Additional Information

- Ensure you have Python 3.6 or higher installed.
- If you encounter any issues, please refer to the documentation or raise an issue in the repository.
