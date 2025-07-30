import instaloader

# === Instaloader session-based Instagram media fetcher ===
SESSION_FILE = "session-asteriasmoons"  # The filename you just restored in main.py
USERNAME = "asteriasmoons"  # Your IG username


def get_instagram_media_links(shortcode):
    """
    Downloads Instagram media links and caption for a given post shortcode
    using instaloader and your saved session.
    Returns (media_links, caption)
    - media_links: List of dicts with 'type' ('image' or 'video') and 'url'
    - caption: string (the post caption)
    """
    L = instaloader.Instaloader()
    try:
        # Load your saved IG session file
        L.load_session_from_file(USERNAME, SESSION_FILE)
    except Exception as e:
        print(f"[DEBUG] Failed to load session file: {e}")
        return [], None

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
    except Exception as e:
        print(f"[ERROR] Could not fetch post for shortcode {shortcode}: {e}")
        return [], None

    media_links = []
    caption = post.caption or ""

    # Handle multiple images/videos (sidecar)
    if post.typename == "GraphSidecar":
        for node in post.get_sidecar_nodes():
            if node.is_video:
                media_links.append({"type": "video", "url": node.video_url})
            else:
                media_links.append({"type": "image", "url": node.display_url})
    # Single video
    elif post.is_video:
        media_links.append({"type": "video", "url": post.video_url})
    # Single image
    else:
        media_links.append({"type": "image", "url": post.url})

    # Debug logging
    print(f"[DEBUG] Media links for {shortcode}: {media_links}")
    print(f"[DEBUG] Caption: {caption[:100]}...")  # First 100 chars

    return media_links, caption
