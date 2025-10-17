# TDS Proj1 - Minimal App Generator

This project hosts an API endpoint that accepts a JSON POST request, generates a minimal application, creates a GitHub repository, and pushes the app to it.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/TDS_proj1.git
    cd TDS_proj1
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create a `.env` file** by copying the example and add your environment variables:
    ```bash
    cp .env.example .env
    ```
    Now, edit the `.env` file with your credentials:
    ```
    SHARED_SECRET=your_shared_secret
    GITHUB_TOKEN=your_github_personal_access_token
    EVALUATION_URL=https://your_evaluation_url.com
    GITHUB_USERNAME=your_github_username
    ```

## Usage

1.  **Start the Flask server:**
    ```bash
    python app.py
    ```

2.  **Send a POST request** to the `/api-endpoint`:
    ```bash
    curl -X POST http://127.0.0.1:5001/api-endpoint \
    -H "Content-Type: application/json" \
    -H "X-Secret: your_shared_secret" \
    -d '{
        "brief": "A brief description of the app.",
        "email": "user@example.com",
        "task": "captcha-solver-42",
        "round": 1,
        "nonce": "ab12-..."
    }'
    ```

## Code Explanation

-   **`app.py`**: The main application file. It contains the Flask web server, the API endpoint, and the logic for creating the GitHub repository and sending the notification.
-   **`requirements.txt`**: The list of Python dependencies.
-   **`.env`**: The file for storing environment variables.

## License

This project is licensed under the MIT License.