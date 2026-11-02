
import httpx

from app.core.config import settings


async def exchange_code_for_token(code: str) -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_CALLBACK_URL,
            },
        )

        response.raise_for_status()
        data = response.json()

        if "access_token" not in data:
            raise ValueError("GitHub did not return an access token")

        return data["access_token"]


async def get_github_user(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
            },
        )

        response.raise_for_status()
        user = response.json()

        if not isinstance(user.get("id"), int):
            raise ValueError("Invalid GitHub user response")

        return user
