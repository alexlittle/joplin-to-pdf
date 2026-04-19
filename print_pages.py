print("Remember: Reverse side goes face down!")
TOTAL_PAGES = 130
BLOCK_SIZE = 36 # Should be divisible by 4!



def print_pages(
    side: str,
    total_pages: int,
    block_size: int,
    start_page: int,
) -> str:
    if side not in {"front", "back"}:
        raise ValueError("side must be 'front' or 'back'")

    ranges = []
    step = 4
    offset = 0 if side == "front" else 2

    last_page = min(start_page + block_size - 1, total_pages)

    for base in range(start_page, last_page + 1, step):
        p1 = base + offset
        p2 = p1 + 1

        if p1 > last_page:
            break

        if p2 > last_page:
            ranges.append(str(p1))
        else:
            ranges.append(f"{p1}-{p2}")

    return ",".join(ranges)

for start in range(1, TOTAL_PAGES + 1, BLOCK_SIZE):
    print(f"\nPages {start}-{min(start + BLOCK_SIZE - 1, TOTAL_PAGES)}")

    for side in ("front", "back"):
        print(f"{side.capitalize()}:",
              print_pages(side, TOTAL_PAGES, BLOCK_SIZE, start))




