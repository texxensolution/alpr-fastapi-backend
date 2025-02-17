from src.core.auth import create_access_token, TokenUser
import asyncio


async def main():
    token_credentials = TokenUser(
        user_id="on_e7497b844beef6e47a915f67361c8c66",
        user_type="internal"
    )
    generated_token = await create_access_token(token_credentials)
    print(f"✨ generated token: {generated_token}")


asyncio.run(main())