import asyncio
from app.dialogue import Session


async def main():
    s = Session()
    print("AGENT:", s.greeting())
    while s.state != "saved":
        text = input("YOU: ").strip()
        if not text:
            continue
        reply = await s.handle(text)
        print("AGENT:", reply)
        print("   [record]", s.record)
    print("SAVED:", s.saved_records)

asyncio.run(main())