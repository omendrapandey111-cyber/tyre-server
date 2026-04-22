def parse_position(position: str) -> dict:
    axle_type = "Front" if position[0] == "F" else "Rear"
    axle_number = int(position[1])
    side = "Left" if position[2] == "L" else "Right"

    placement = None
    if len(position) > 3:
        placement = "Inner" if position[3] == "I" else "Outer"

    name = f"{axle_type} Axle {axle_number} {side}"
    if placement:
        name += f" {placement}"

    return {
        "position": position,
        "name": name,
        "axle_type": axle_type,
        "axle_number": axle_number,
        "side": side,
        "placement": placement,
    }