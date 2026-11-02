
import re
import httpx

from fastapi import HTTPException

GITHUB_REPO_PATTERN = re.compile(
    r"^[A-Za-z0-9-]{1,39}/[A-Za-z0-9_.-]{1,100}$"
)


async def verify_repository_ownership(
    repo_name: str,
    github_user_id: int,
) -> dict:
    if not GITHUB_REPO_PATTERN.fullmatch(repo_name):
        raise HTTPException(
            status_code=422,
            detail="Expected GitHub repository as owner/name",
        )

    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=False,
    ) as client:
        try:
            response = await client.get(
                f"https://api.github.com/repos/{repo_name}",
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "OpenSourceFundingHackathon",
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail="Repository not found",
                )
            raise HTTPException(
                status_code=502,
                detail="Unable to verify GitHub repository",
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=502,
                detail="GitHub API unavailable",
            )

    repo = response.json()

    if repo.get("private") is not False:
        raise HTTPException(
            status_code=403,
            detail="Only public repositories are supported",
        )

    owner = repo.get("owner") or {}

    if owner.get("id") != github_user_id:
        raise HTTPException(
            status_code=403,
            detail="You must own this repository",
        )

    if not isinstance(repo.get("id"), int):
        raise HTTPException(
            status_code=502,
            detail="Invalid GitHub repository response",
        )

    return {
        "id": repo["id"],
        "url": repo["html_url"],
    }
