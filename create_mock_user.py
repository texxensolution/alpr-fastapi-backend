from src.core.auth import create_access_token, TokenUser
import asyncio


async def main():
    token_credentials = TokenUser(
        user_id="on_0021290c15f126423b3e5c406e719b7b",
        user_type="internal"
    )
    generated_token = await create_access_token(token_credentials)
    print(f"✨ generated token: {generated_token}")


asyncio.run(main())